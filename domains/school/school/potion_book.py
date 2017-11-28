import book
import gametools

def clone():
    potion_book = book.Book("leather book", __file__, "leather-bound tome", "This is an old leather-bound book titled \"Potion Recipes for the Beginning and Intermediate Sorcerer (First Edition).\"", pref_id="potion_book")
    potion_book.add_names("tome", "book")
    potion_book.add_adjectives("leather-bound", "leather")
    potion_book.set_message('''


Potion Recipes for the Beginning and Intermediate Sorcerer (First Edition)



#*
Table of Contents:

Invisibility Potion on page 3
Pink Potion on page 4
Strength Potion on page 5

#*
Invisibility Potion

The First Step: Gather thyself moss from a cave, water, truffles, a petal from a sunflower, and molasses.
The Second Step: Put the ingredients in thy cauldron and put the cauldron over a burner.
The Third Step: Drink thy potion, and turn thyself invisible.
The Fourth Step: Beware, because thou will not be invisible forever.
#*
Pink Potion

The First Step: Gather thyself water, molasses, and a seed from a poppy.
The Second Step: Put the ingredients in a cauldron and put the cauldron over a burner.
The Third Step: Drink thy potion, and turn thyself pink.
The Fourth Step: Beware, because thou will not be pink for long.
#*
Strength Potion

The First Step: Gather thyself moss from a cave, molasses, and a seed from a poppy
The Second Step: Put the ingredients in thy cauldron and put the cauldron over a burner.
The Third Step: Drink thy potion, and make thyself stronger.
The Fourth Step: Beware, because thou will not be stronger forever.
''')
    return potion_book
