import pickle
import sys
import importlib

import gametools
from debug import dbg

from thing import Thing
from room import Room
from creature import Creature
from action import Action


class Player(Creature):
    def __init__(self, ID, path, console):
        """Initialize the Player object and attach a console"""
        Creature.__init__(self, ID, path)
        self.cons = console
        self.start_loc_id = None
        self.set_weight(175/2.2)
        self.set_volume(66)
        self.actions.append(Action(self.inventory, "inventory", False, True))
        self.actions.append(Action(self.toggle_terse, "terse", False, True))
        self.actions.append(Action(self.execute, "execute", True, True))
        self.actions.append(Action(self.fetch, "fetch", True, True))
        self.actions.append(Action(self.clone, "clone", True, True))
        self.actions.append(Action(self.apparate, "apparate", True, True))
        self.actions.append(Action(self.reload, "reload", True, True))
        self.actions.append(Action(self.say, ["say", "shout", "mutter", "whisper"], True, True))
        self.actions.append(Action(self.introduce, "introduce", True, True))
        self.actions.append(Action(self.engage, "engage", True, False))
        self.actions.append(Action(self.disengage, "disengage", False, True))
        self.aggressive = 1         #TODO: Specilized individual stats
        self.armor_class = 10
        self.combat_skill = 40
        self.strength = 20
        self.dexterity = 60
        self.attack_now = 0
        self.auto_attack = True
        self.wizardry_skill = 0
        self.wizardry_element = None
        self.attacking = False
        self.reading = False
        self.hitpoints = 20
        self.health = 20
        self.terse = False  # True -> show short description when entering room
        self.game.register_heartbeat(self)

    def __getstate__(self):
        """Custom pickling code for Player. 
        
        Avoids directly pickling the associated console (will eventually
        delete this for save-and-quit functionality in multiplayer; for 
        now just detach the console to support save-and-keep-playing). 
        """
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = super().__getstate__()
        state['set_start_loc'] = state['set_start_loc'].id
        del state['enemies'] #TODO: Make saving and loading of this attribute work
        # Remove the unpicklable entries.
        del state['cons']
        return state

    def __setstate__(self, state):
        """Custom unpickling code for Player

        Note 1: The function unpickling the Player must then attach it to
        a new console.
        
        Note 2: If the player is joining an ongoing game (as opposed to the
        entire game including players getting saved/restored) then the 
        function unpickling the player should restore the location field from
        an ID string to a direct reference, do the same for the objects in the
        contents field, and call move_to() to update the room."""
        super(Player, self).__setstate__(state) # updates Thing.ID_dict
        # Restore instance attributes
        self.enemies = [] #XXX fix problem with enemies

    def set_start_loc(self, startroom):
        self.start_loc_id = startroom.id

    def detach(self):
        self.cons.detach(self)
        self.cons = None
        Thing.game.deregister_heartbeat(self)

    def heartbeat(self):
        cmd = self.cons.take_input()
        if cmd:
            if cmd != '__noparse__':
                keep_going = Thing.game.parser.parse(self, self.cons, cmd)
                if not keep_going:
                    self.move_to(Thing.ID_dict['nulspace'])
                    self.detach()

        if self.auto_attack:            # TODO: Player Prefrences
            if self.attacking:
                if self.attacking == 'quit':
                    return
                else:
                    self.attack_enemy(self.attacking)
            for i in self.location.contents:
                if i in self.enemies:
                    self.cons.write('You attack your enemy %s.' % i.short_desc)
                    self.attacking = i
                    self.attack_enemy(i)
            

    def die(self, message):
        Creature.die(self, message)
        self.cons.write("You have died!\n\nFortunately you are reincarnated immediately...")
        self.health = self.hitpoints
        if (self.start_loc_id):
            room = Thing.ID_dict[self.start_loc_id]
            self.move_to(room)
            room.report_arrival(self)
        else:
            self.cons.write("Uh-oh! You don't have a starting location. You are in a great void...")

    def perceive(self, message):
        '''Parse a string passed to `emit()` and customize it for this
        player. Searches the string for special tags (indicated with the '&'
        symbol) and replaces the substring following that tag (up to a 
        whitespace character) with a customized substring. Currently supports
        the following tags, in which <id> is the ID attribute of an object O:

            tag      description
            -------  --------------------------------------------------------
            &nd<id>: 'name-definite': replace with the proper name of O, if O
                     has been introduced to this player, else the short
                     description of O preceeded by the definite article 'the'
            &nD<id>: 'name-capitalized-definite': replace with the proper name
                     of O, if O has been introduced to this player, else the
                     short description of O proceeded by the capitalized 
                     definite article 'The'
            &ni<id>: 'name-indefinite': replace with O.proper_name if O has 
                     been introduced, else O.short_desc preceeded by the 
                     indefinite article ('a' or 'an')
            &nI<id>: 'name-indefinite-capitalized': replace with O.proper_name
                     if O has been introduced, else 'A' or 'An' + O.short_desc
            &nn<id>: 'name-no-article': replace with O.proper_name if O has 
                     been introduced, else O.short_desc with no article.
        
        In general, a creature mentioned 'by name' in the message probably will 
        get a custom message and shouldn't get the default 'perceive' message.  
        So for convenience `perceive()` will silently return if this player is
        one of the creatures named using the &n semantics above, effectively 
        ignoring any creatures named in the `emit()` message.
        '''
        if not self.location.is_dark():
            # replace any & tags in the message 
            while True:
                # first, replace any occurrence of '&u' with the user's ID
                (m1, sep, m2) = message.partition('&u')  
                if not sep:    # partition() sets sep to '' if '&u' not found
                    break
                message = m1 + self.id + m2
            while True:
                (m1, sep, m2) = message.partition('&')  
                if not sep:    # partition() sets sep to '' if '&' not found
                    break
                tag = m2.split()[0]  # split() separates on whitespace
                subject = ""
                O = None
                try:
                    tag_type = tag[0:1]
                    idstr = tag[1:]
                    if tag_type in ('n', 'N'):  # some tag types use 2 letters
                        tag_type = tag[0:2]
                        idstr = tag[2:]
                    idstr = idstr.rstrip('.,!?;:\'"')  # remove any punctuation
                    O = Thing.ID_dict[idstr]
                except IndexError:
                    subject = "<error: can't parse tag &%s>" % tag
                except KeyError:
                    subject = "<error: can't find object %s>" % idstr
                if tag_type[0] == 'n':
                    if O == None:
                        subject = '[Error: no object matching idstr %s]' % idstr
                    if O == self: 
                        return      # ignore messages that mention self by name
                    else:
                        subject = O.get_short_desc(self)
                        if tag_type[1] in ('d','D'):
                            subject = O.get_short_desc(self, definite=True)
                        if tag_type[1] in ('i','I'):
                            subject = O.get_short_desc(self, indefinite=True)
                        if tag_type[1] in ('N','D','I', 'R'):
                            subject = subject[0].upper() + subject[1:]  # capitalize
                if tag_type[0] == 's':
                    subject = O.species
                if tag_type[0] == 'S':
                    subject = O.species[0].upper() + O.species[1:]
                m2 = subject + m2.partition(tag)[2]
                message = m1 + m2

            super().perceive(message)
            self.cons.write(message) 
                   
    def hold_object(self, obj):
        self.visible_inventory.append(obj)

    #
    # ACTION FUNCTIONS (verbs):
    # 
    def inventory(self, p, cons, oDO, oIDO):
        if cons.user != self:
            return "You can't look at another player's inventory!"
        cons.write("You are carrying:")
        if not self.contents:
            cons.write('\tnothing')
        for i in self.contents:
            if i == self.weapon_wielding or i == self.armor_worn: 
                continue
            cons.write("\ta " + i.short_desc)
        if self.weapon_wielding != self.default_weapon: 
            cons.write('You are wielding a %s.' % self.weapon_wielding.short_desc)
        if self.armor_worn != self.default_armor:
            cons.write('You are wearing a %s.' % self.armor_worn.short_desc)
        return True
    
    def toggle_terse(self, p, cons, oDO, oIDO):
        if cons.user != self:
            return "I don't quite get what you mean."
        try: 
            if p.words[1] == "on": 
                self.terse = True
            elif p.words[1] == "off": 
                self.terse = False
            else: 
                return """Usage: 'terse [on/off]'
                Use long descriptions (off) or short descriptions (on) when entering a place.
                With no specifier, 'terse' toggles between on and off."""
        except IndexError:
            self.terse = not self.terse
        cons.write("Terse mode %s. %s" % ("on" if self.terse else "off",
            "Short descriptions will be used when entering a place; type 'look' for full description" if self.terse else
            "Full descriptions will be used entering a place."))
        # TODO: a mode that prints long description only when first entering a room
        return True
    
    
    def execute(self, p, cons, oDO, oIDO):
        if cons.user != self:
            return "I don't quite get what you mean."
        cmd = ' '.join(p.words[1:])
        cons.write("Executing command: '%s'" % cmd)
        try: 
            exec(cmd)
        except Exception as inst:
            cons.write("Unexpected error: " + str(sys.exc_info()[0]) + "\n\t" + str(sys.exc_info()[1]))
            # cons.write(type(inst)+"\n"+inst)    # the exception instance
        return True

    def fetch(self, p, cons, oDO, oIDO):
        '''Find an in-game object by ID and bring it to the player.'''
        if cons.user != self:
            return "I don't quite get what you mean."
        if len(p.words) < 2: 
            cons.write("Usage: 'fetch <id>', where id is an entry in Thing.ID_dict[]")
            return True
        id = " ".join(p.words[1:])
        try:
            obj = Thing.ID_dict[id]
            if isinstance(obj, Creature) or obj.move_to(self) == False:
                if obj.move_to(self.location) == False:
                    cons.write("You attempt to fetch the %s but somehow cannot bring it to this place." % obj.names[0])
                else:
                    cons.write("You perform a magical incantation and bring the %s to this place!" % obj.names[0])
            else:
                cons.write("You perform a magical incantation and the %s appears in your hands!" % obj.names[0])
            self.emit("&nD%s performs a magical incantation, and you sense something has changed." % self.id, [self])
        except KeyError: 
            return "There seems to be no object with true name '%s'!" % id
        
        return True                    

    def clone(self, p, cons, oDO, oIDO):
        '''Clone a new copy of an object specified by ID or by module path, and bring it to the player.'''
        if cons.user != self:
            return "I don't quite get what you mean."
        if len(p.words) < 2: 
            cons.write("Usage:\n\t'clone <id>', where id is an entry in Thing.ID_dict[]"
                       "\n\t'clone <path>', where path is of the form 'domains.school.test_object'")
            return True
        id = " ".join(p.words[1:])
        try:
            current_obj = Thing.ID_dict[id]
            objpath = current_obj.path
        except KeyError: 
            objpath = id
        obj = gametools.clone(objpath)
        if obj == None:
            return "There seems to be no object with true name '%s'!" % id
        if isinstance(obj, Creature) or obj.move_to(self) == False:
            if obj.move_to(self.location) == False:
                cons.write("You attempt to clone the %s but somehow cannot bring it to this place." % obj.names[0])
            else:
                cons.write("You perform a magical incantation and bring the %s to this place!" % obj.names[0])
        else:
            cons.write("You perform a magical incantation and the %s appears in your hands!" % obj.names[0])
        self.emit("&nD%s performs a magical incantation. You sense something has changed." % self.id, [self])
        
        return True                    
    
    def reload(self, p, cons, oDO, oIDO):
        '''Reloads the specified room, or the room containing the player if none is given.
        First moves all objects out of the room into nulspace, then re-imports the room 
        module, calls `load()` in the new module, then finally moves any creatures including
        players back to the new room.'''
        room = None
        if len(p.words) < 2: 
            room = self.location
        elif len(p.words) == 2:
            room = gametools.load_room(p.words[1])
            if room == None: 
                return "Error, room '%s' doesn't seem to exist!" % p.words[1]
        else: 
            return "Usage: 'reload' [room path]\n\t<room path> is optional, if none is given will reload the current room."

        alive = [x for x in room.contents if isinstance(x, Creature)] # all Creatures incl NPCs & players
        if room.detach(room.path) == False:
            return "Error while detaching room %s!" % room.path
        mod = importlib.reload(room.mod)
        newroom = mod.load()  # TODO: store and re-use parameters of original load() call?
        newroom.mod = mod
        for c in alive: 
            c.move_to(newroom, force_move = True)
        cons.write('You make a magical gesture and scene around you suddenly changes.')
        self.emit('&nD%s makes a magical gesture, and you sense something has changed.' % self.id)
        del room  # XXX unclear if this will do anything
        return True

    def apparate(self, p, cons, oDO, oIDO):
        if cons.user != self:
            return "I don't quite get what you mean."
        if len(p.words) < 2: 
            cons.write("Usage: 'apparate <id>', where id is the entry of a Room in Thing.ID_dict[] or a path to it's module")
            return True
        id = " ".join(p.words[1:])
        try:
            room = Thing.ID_dict[id]
        except KeyError: 
            room = gametools.load_room(id)
        if room == None:
            return "There seems to be no place with id (or path) '%s'!" % id
        if isinstance(room, Room) == False:
                cons.write("You cannot apparate to %s; that is not a place!" % room.names[0])
                return True
        self.emit("&nD%s performs a magical incantation, and vanishes!" % self.id, [self])
        self.move_to(room)
        self.emit("&nD%s arrives suddenly, as if by magic!" % self.id, [self])
        self.perceive("You perform a magical incantation and are suddenly in a new place!")
        room.report_arrival(self, silent=True)
        return True

    def say(self, p, cons, oDO, oIDO):
        if cons.user != self:
            return "I don't quite get what you are trying to say."
        if len(p.words) < 2:
            return "What do you want to say?"
        self.emit("&nD%s %ss: %s" % (self.names[0], p.words[0], " ".join(p.words[1:])), ignore = [self])
        cons.write("You %s: %s" % (p.words[0], " ".join(p.words[1:])))
        return True
    
    def introduce(self, p, cons, oDO, oIDO):
        if cons.user != self:
            return "I'm not sure who's introducing whom."
        if len(p.words) < 2:
            return "Usage: 'introduce myself' or 'introduce <name>' with <name> of somebody present."
        if p.words[1] != 'myself':
            return "Introducing anybody other than 'myself' is not yet supported."
        self.emit("&nD%s introduces himself as '%s'." % (self, self.proper_name))
        self.perceive("You introduce yourself to all.")
        for obj in self.location.contents:
            if isinstance(obj, Creature) and obj != self:
                obj.introduced.add(self.id)
        return True

    def engage(self, p, cons, oDO, oIDO):
        if cons.user != self:
            return "I don't quite get what you mean."
        if not oDO:
            return "Who do you intend to engage in combat?"
        self.attacking = oDO
        self.weapon_and_armor_grab()
        return True

    def disengage(self, p, cons, oDO, oIDO):        #TODO: Finish up.
        if cons.user != self:
            return "I don't quite get what you mean."
        self.attacking = 'quit'
        return True

    def attack_enemy(self, enemy):
        if self.attacking in self.location.contents:
            self.attack(enemy)
        else:
            self.attacking = None