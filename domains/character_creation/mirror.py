import thing
import gametools

class Mirror(thing.Thing):
    def __init__(self, what_you_see, exit_room, species='', gender='', adj1='', adj2=''):
        super().__init__('mirror', __file__)
        self.set_description('shimmering mirror', 'In this mirror you see %s.' % what_you_see)
        self.actions.append(thing.Action(self.enter, ['enter'],True, False))
        self.dest = exit_room
        self.species = species
        self.gender = gender
        self.adj1 = adj1
        self.adj2 = adj2

    def look_at(self, p, cons, oDO, oIDO):
        if self == oDO or self == oIDO:
            cons.user.perceive(self.long_desc)
            return True
        else:
            return "Not sure what you are trying to look at!"

    def enter(self, p, cons, oDO, oIDO):
        dest = gametools.load_room(self.dest)
        cons.user.move_to(dest)

        label = ""  # construct a label, e.g. "swarthy young male gnome"
        if self.adj1:
            label += self.adj1 + " "
            cons.user.add_adjectives(self.adj1)
        else:
            label = "nondescript" + " "
        if self.adj2:   
            label += self.adj2 + " "
            cons.user.add_adjectives(self.adj2)
        if self.gender:
            label += self.gender + " "
            cons.user.add_adjectives(self.gender)
            cons.user.gender = self.gender
        if self.species:
            label += self.species
            cons.user.species = self.species
            cons.user.add_names(self.species)
        cons.user.set_description(label, "A " + label)

        cons.user.perceive("As if in a dream, you approach the mirror and enter it, the glass parting like gauze "
            "to let you through. Somehow you feel more sharply defined, more real! You notice your surroundings "
            "have changed...\n")
        dest.report_arrival(cons.user)
        return True
