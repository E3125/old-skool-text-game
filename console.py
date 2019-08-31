import asyncio
import connections_websock
import os.path

from debug import dbg
from parse import Parser
from player import Player
import gametools

class Console:
    default_width = 80
    measurement_systems = ['IMP', 'SI']
    default_measurement_system = 'IMP'
    prompt = "--> "
    help_msg = """Your goal is to explore the world around you, solve puzzles,
               fight monsters, complete quests, and eventually become a
               Sorcerer capable of changing and adding to the very fabric 
               of the world itself.\n\n
               Useful commands include 'look' to examine your surroundings 
               or an object, 'take' to pick something up, 'inventory' to see 
               what you are carrying, 'go' to move a particular direction. 
               You can use prepositions to create more complex commands and
               adjectives to specify particular objects; articles are 
               optional. Here are some examples of valid commands:\n\n
               \t'look'\n
               \t'go north'\n
               \t'take sword'\n
               \t'take the rusty sword'\n
               \t'drink potion from tall flask'\n
               \t'put the gold coin in the leather bag'\n
               \t'move vines'\n\n
               You can create shortcuts to reduce typing; type 'alias' for 
               more details. Type 'width' to change the console's text width. 
               Type 'quit' to save your progress and leave 
               the game."""

    def __init__(self, net_conn, game = None):
        self.game = game
        self.user = None
        self.username = None
        self.raw_input = ''
        self.raw_output = ''
        self.change_players = False
        self.connection = net_conn
        self.input_redirect = None
        self.width = Console.default_width
        self.measurement_system = Console.default_measurement_system
        self.changing_passwords = False
        self.alias_map = {'n':       'go north',
                          's':       'go south',
                          'e':       'go east', 
                          'w':       'go west', 
                          'nw':      'go northwest',
                          'sw':      'go southwest',
                          'ne':      'go northeast',
                          'se':      'go southeast',
                          'u':       'go up',
                          'd':       'go down',
                          'i':       'inventory',
                          'l':       'look',
                          'x':       'execute'
                          }
        self.legal_tags = {'span':     ['style'],
                           'div':      ['style'],
                           'b':        ['style'],
                           'br':       ['style'],
                           'code':     ['code'],
                           'dl':       ['style'],
                           'dd':       ['style'],
                           'dt':       ['style'],
                           'del':      ['style'],
                           'em':       ['style'],
                           'h1':       ['style'],
                           'h2':       ['style'],
                           'h3':       ['style'],
                           'h4':       ['style'],
                           'h5':       ['style'],
                           'h6':       ['style'],
                           'hr':       ['style'],
                           'i':        ['style'],
                           'ins':      ['style'],
                           'li':       ['style', 'value'],
                           'mark':     ['style'],
                           'meter':    ['style', 'high', 'low', 'max', 'min', 'optimum', 'value'],
                           'ol':       ['style', 'start', 'reversed', 'type'],
                           'p':        ['style'],
                           'pre':      ['style'],
                           'progress': ['style', 'max', 'value'],
                           'q':        ['style'],
                           's':        ['style'],
                           'kbd':      ['style'],
                           'samp':     ['style'],
                           'small':    ['style'],
                           'strong':   ['style'],
                           'sub':      ['style'],
                           'sup':      ['style'],
                           'u':        ['style'],
                           'ul':       ['style']}
        self.empty_elements = ['br', 'hr']

    def detach(self, user):
        if self.user == user:
            self.user = None

    def set_width(self, w):
        self.width = w
    
    def get_width(self):
        return self.width
    
    def _add_alias(self, cmd):
        instructions = 'To create a new alias, type:\n    alias [a] [text]\n' \
                        'where [a] is the new alias and [text] is what will replace the alias.'
         
        if len(self.words) == 1:
            # print a list of current aliases & instructions for adding
            self.write('Current aliases:')
            for a in sorted(self.alias_map, key=self.alias_map.get):
                self.write('%s = %s' % (a.rjust(12), self.alias_map[a]))
            self.write(instructions)
            return 
        alias = self.words[1]
        if len(self.words) == 2:
            # print the particular alias if it exists
            if (alias in self.alias_map):
                self.write("'%s' is currently aliased to '%s'" % (alias, self.alias_map[alias]))
            else:
                self.write("'%s' is not currently aliased to anything." % alias)
                self.write(instructions)
            return 
        # new alias specified, insert it into the alias_map
        if (alias in self.alias_map):
            self.write("'%s' is currently aliased to '%s'; changing." % (alias, self.alias_map[alias]))
        expansion = cmd.split(maxsplit=2)[2]    # split off first two words and keep the rest
        self.alias_map[alias] = expansion
        self.write("'%s' is now an alias for '%s'" % (alias, expansion))
        return
    
    def _change_units(self, cmd):
        cmd = cmd.split(' ')
        if len(cmd) == 2:
            if cmd[1].upper() in Console.measurement_systems:
                self.measurement_system = cmd[1].upper()
                self.write('Changed units to %s.' % self.measurement_system)
            else:
                self.write('Not an accepted measurement system. Accepted ones are:\n' + [x for x in Console.measurement_systems])
        else:
            self.write('Current units are: %s\nType units [system] to change them.' % self.measurement_system)

    def _replace_aliases(self):
        cmd = ""
        for t in self.words:
            if t in self.alias_map:
                cmd += self.alias_map[t] + " "
                dbg.debug("Replacing alias '%s' with expansion '%s'" % (t, self.alias_map[t]), 3)
            else:
                cmd += t + " "
        cmd = cmd[:-1]   # strip trailing space added above
        dbg.debug("User input with aliases resolved:\n    %s" % (cmd), 3)
        return cmd
    
    def _set_verbosity(self, level=-1):
        if level != -1:
            dbg.set_verbosity(level, self.user.id)
            return "Verbose debug output now %s, verbosity level %s." % ('on' if level else 'off', dbg.verbosity)
        if dbg.verbosity == 0:
            dbg.set_verbosity(1, self.user.id)
            return "Verbose debug output now on, verbosity level %s." % dbg.verbosity
        else:
            dbg.set_verbosity(0, self.user.id)
            return "Verbose debug output now off."

    def _handle_verbose(self):
        try:
            level = int(self.words[1])
        except IndexError:
            self.write(self._set_verbosity())
            return
        except ValueError:
            if self.words[1] == 'filter':
                try:
                    s = self.words[2:]
                    dbg.set_filter_strings(s, self.user.id)
                    self.write("Set verbose filter to '%s', debug strings containing '%s' will now be printed." % (s, s))                      
                except IndexError:
                    dbg.set_filter_strings(['&&&'], self.user.id)
                    self.write("Turned off verbose filter; debug messages will only print if they are below level %d." % dbg.verbosity)
                return
            self.write("Usage: verbose [level]\n    Toggles debug message verbosity on and off (level 1 or 0), or sets it to the optionally provided [level]")
            return
        self.write(self._set_verbosity(level))
    
    def _handle_console_commands(self):
        """Handle any commands internal to the console, returning True if the command string was handled."""
        if len(self.words) > 0:
            cmd = self.words[0]
            if cmd == 'alias':
                self._add_alias(self.command)
                return True
            
            if cmd == 'units':
                self._change_units(self.command)
                return True
            
            if cmd == 'help':
                self.write(self.help_msg)
                return True

            if cmd == 'debug':
                # check wizard privilages before allowing
                if self.user.wprivilages:
                    self.game.handle_exceptions = not self.game.handle_exceptions
                    self.write("Toggle debug exception handling to %s" % ("on" if self.game.handle_exceptions else "off"))
                    return True
                else:
                    self.write("You do not have permission to change the game's debug mode. If you would like to report a bug, type \"bug\" instead.")
                    return True
            
            if cmd == 'verbose':
                # check wizard privilages before allowing
                if self.user.wprivilages:
                    self._handle_verbose()
                    return True
                else:
                    self.write("Type \"terse\" to print short descriptions when entering a room.")
                    return True

            if cmd == "escape":
                if self.input_redirect != None:
                    self.input_redirect = None
                    self.write("Successfully escaped from the redirect. ")
                else:
                    self.write("You cannot escape from a redirect, as there is none.")
                return True

            if cmd == 'auto-attack':
                self.user.auto_attack = True if self.user.auto_attack == False else False
                self.write("Auto attack toggled to %s." % self.user.auto_attack)
                return True
            
            if cmd == 'change':
                if self.words[1] == 'password':
                    self.write("Please enter your new #password:")
                    self.input_redirect = self
                    self.changing_passwords = True
                    return True
            
            game_file_cmds = {'savegame':self.game.save_game,
                         'loadgame':self.game.load_game}
            if cmd in game_file_cmds:
                if (len(self.words) == 2):
                    filename = self.words[1]
                    game_file_cmds[cmd](filename)
                else:
                    self.write("Usage: %s [filename]" % cmd)
                return True
            if cmd == 'save':
                if (len(self.words) == 2):
                    filename = self.words[1]
                    self.game.save_player(filename, self.user)
                else:
                    self.write("Usage: save [filename]")
                return True
            if cmd == 'load':
                if (len(self.words) == 2):
                    filename = self.words[1]
                    try:
                        self.game.load_player(filename, self.user, self)
                    except gametools.PlayerLoadError:
                        self.write("Encountered an error trying to load from file.")
                else:
                    self.write("Usage: load [filename]")
                return True
            
            if cmd == 'quit':
                self.user.emit("&nD%s fades from view, as if by sorcery...you sense that &p%s is no longer of this world." % (self.user, self.user))
                self.game.save_player(os.path.join(gametools.PLAYER_DIR, self.user.names[0]), self.user)
                self.write("#quit")
                if self.words[1] == 'game' and self.user.wprivilages:
                    self.game.keep_going = False
                return "__quit__"

        return False

    def sanatizeHTML(self, html):
        html = html.replace('<', '(#*tag)(||istag)').replace('>', '(#*tag)')
        possible_tags = html.split('(#*tag)')
        tags = []
        nontags = []
        first = None
        for i in possible_tags:
            if i.startswith('(||istag)'):
                (head, sep, tail) = i.partition('(||istag)')
                tags.append(tail)
                if first == None:
                    first = 'tag'
            else:
                nontags.append(i)
                if first == None:
                    first = 'nontag'
        #dbg.debug('Output tags are:'+tags, 0)
        tag_lists = []
        for j in tags:
            tag_and_attributes = j.split(' ')
            if len(tag_and_attributes) > 1:
                item = [tag_and_attributes[0], tag_and_attributes[1:]]
            else:
                item = [tag_and_attributes[0], []]
            tag_lists.append(item)
        for l in range(0, len(tag_lists)):
            if (tag_lists[l][0] not in list(self.legal_tags)) and (tag_lists[l][0].partition('/')[2] not in list(self.legal_tags)):
                (head, sep, tail) = tag_lists[l][0].partition('/')
                if tail in self.empty_elements:
                    tag_lists[l] = ['br', []]
                elif tail not in list(self.legal_tags):
                    if sep == '':
                        tag_lists[l] = ['span', []]
                    else:
                        tag_lists[l] = ['/span', []]
            for m in range(0, len(tag_lists[l][1])):
                #if tag_lists[l][0].rfind('/') > -1:
                (head, sep, tail) = tag_lists[l][1][m].partition('=')
                if head not in self.legal_tags[tag_lists[l][0]]:
                    tag_lists[l][1][m] = ''
        
        full_tags = []
        for n in tag_lists:
             tag = '<'
             tag += n[0]
             for o in n[1]:
                tag += ' ' + o
             tag += '>'
             full_tags.append(tag)
        final_html = ''
        for p in range(0, len(full_tags)+len(nontags)):
            if p/2 == int(p/2):
                if first == 'tag':
                    final_html += full_tags[int(p/2)]
                elif first == 'nontag':
                    final_html += nontags[int(p/2)]
            else:
                if first == 'tag':
                    final_html += nontags[int(p/2)]
                elif first == 'nontag':
                    final_html += full_tags[int(p/2)]
        return final_html
    
    def choose_measurements(self, text):
        text = text.replace('[', '|[')
        text = text.replace(']', ']|')
        split_text = text.split('|')

        in_measurement = False
        correct_measurement = False
        to_continue = False

        new_text = ''

        for i in split_text:
            for j in Console.measurement_systems:
                if i == '['+j+']':
                    in_measurement = True
                    to_continue = True
                    if j == self.measurement_system:
                        correct_measurement = True
                    else:
                        correct_measurement = False
                elif i == '[/'+j+']':
                    in_measurement = False
                    to_continue = True
                    if j == self.measurement_system:
                        correct_measurement = True
                    else:
                        correct_measurement = False
            if to_continue:
                to_continue = False
                continue
            if (not in_measurement) or correct_measurement:
                new_text += i
        
        return new_text

    def write(self, text, indent=0):
        self.raw_output += str(text) + '<br>'
        self.raw_output = self.raw_output.replace('\n','<br>').replace('\t', '&nbsp&nbsp&nbsp&nbsp')
        self.raw_output = self.choose_measurements(self.raw_output)
        self.raw_output = self.sanatizeHTML(self.raw_output)
        asyncio.ensure_future(connections_websock.ws_send(self))

    '''
    def new_user(self):
        self.write("Create your new user.")
        user_default_name = input("User default name: ")    #TODO: Simplify and make text more user-friendly.
        user_short_description = input("User short description: ")
        user_long_description = input("User long description: ")
        new_user = Player(user_default_name, self)
        new_user.set_description(user_short_description, user_long_description)
        new_user.set_max_weight_carried(750000)
        new_user.set_max_volume_carried(2000)
        new_user.move_to(self.user.location)
        for i in self.user.contents:
            i.move_to(new_user)
        self.write("You are now %s!" % new_user.id)
        self.user.move_to(Thing.ID_dict['nulspace'])
        self.user.cons = None
        self.set_user(new_user)
        self.game.user = new_user
    '''
    def request_input(self, dest):
        self.input_redirect = dest
        dbg.debug("Input from console %s given to %s!" % (self, dest))
    
    def console_recv(self, command):
        """Temporarily recieve information as a two-part command, e.g. changing passwords."""
        if self.changing_passwords:
            self.user.password = command
            self.changing_passwords = False
            self.input_redirect = None

    def take_input(self):
        if (self.raw_input == ''):
            return None
        (self.command, sep, self.raw_input) = self.raw_input.partition('\n')
        self.words = self.command.split()
        # if user types a console command, handle it and start over unless the player that called this is deactive
        internal = self._handle_console_commands()
        if internal == "__quit__":
            return "__quit__"
        if internal:
            return "__noparse__"
        if self.input_redirect != None:
            try:
                self.input_redirect.console_recv(self.command)
                return "__noparse__"
            except AttributeError:
                dbg.debug('Error! Input redirect is not valid!')
                self.input_redirect = None
        # replace any aliases with their completed version
        self.final_command = self._replace_aliases()
        return self.final_command
