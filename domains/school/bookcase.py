from debug import dbg
from thing import Thing
from action import Action

class Bookcase(Thing):
    def __init__(self, ID, path, hidden_room):
        Thing.__init__(self, ID, path)
        self.set_description('bookcase full of books', \
        'This bookcase is a hodgepodge of books; some are newer, but a lot of old ones are scattered around them.')
        # we want this to trigger if they type, for example, "take old book"
        self.add_names("book")
        self.add_adjectives("old", "new")
        self.fix_in_place("The bookcase appears to be fixed to the wall.")
        self.actions.append(Action(self.handle_book, ["take", "get", "pull"], True, False))
        self.hidden_room = hidden_room

    def handle_book(self, p, cons, oDO, oIDO):
        (sV, sDO, sPrep, sIDO) = p.diagram_sentence(p.words)
        if sDO in ['tattered book', 'old book']:
            cons.write('You pull on a book. ')
            self.emit("&nD%s does something to the bookcase." % cons.user.id)
            self.emit('The bookcase shakes, and swings open, revealing a secret staircase leading down.')
            self.location.add_exit('down', self.hidden_room)
            self.set_description('a bookcase door wide open to a secret staircase', 'This door is cleverly disguised as a bookcase. It is open, revealing a secret staircase leading down.')
            return True
        else:
            return "Did you mean to get a particular book?"

