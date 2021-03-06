import random
import domains.school.school.library_book as library_book

title_formats = ['The {adjective1} {noun1}', '{noun1}, {noun2}, and the {adjective1} {noun3}', 
    'How the {noun1} {verb1}èd the {noun2}', 'A tale of {number1} {noun1}s', '{noun1} and {noun2}',
    'The {adjective1} {adjective2} {noun1}', 'A journey to the land of the {adjective1} {noun1}s',
    '{number1} {adjective1} {noun1}: A retrospective', 'On {verb1}ing {noun1}s', 'The {noun1} of {noun2}s']
nouns = ['city', 'plant', 'coffee', 'spell', 'dragon', 'tree', 'kingdom', 'knight', 'castle', 'land', 
'village', 'plain', 'forest', 'marsh', 'hut', 'portal', 'cave', 'mountain', 'empire', 'fire']
adjectives = ['strange', 'old', 'misty', 'crumbling', 'bright', 'dark', 'ancient', 'towering', 'brave', 
'endless', 'unseen', 'distant', 'new', 'dense', 'airy', 'dusty']
verbs = ['conquer', 'capture', 'destroy', 'create', 'perfect', 'combine', 'wash', 'vanquish', 'perfume', 'rescue']
numbers = ['two', 'three', 'fourty-two', 'thirteen', 'eighty-seven', 'fifty-five', 'two hundred fifty']

book_description_adjectives = ['old', 'worn', 'dusty', 'new', 'shiny', 'red', 'orange', 'yellow', 'green', 'blue', 
'violet', 'arcane', 'thin', 'thick', 'tall', 'short', 'yellowed', 'tiny', 'ancient', 'modern', 'strange']
book_messages = ['This page is in a language that you do not understand.', 'This page is mysteriously blank.', 
    'This page is too worn for you to make out the text.', 'This page has been blotted out by an ink spill.']
book_message_weights = [45, 8, 40, 7]

def clone():
    t_format = random.choice(title_formats)
    num_nouns = t_format.count('noun')
    num_adjectives = t_format.count('adjective')
    num_verbs = t_format.count('verb')
    num_numbers = t_format.count('number')

    arg_dict = {}
    for i in range(0, num_nouns):
        arg_dict['noun%s' % str(i+1)] = random.choice(nouns)
    for j in range(0, num_adjectives):
        arg_dict['adjective%s' % str(j+1)] = random.choice(adjectives)
    for k in range(0, num_verbs):
        arg_dict['verb%s' % str(k+1)] = random.choice(verbs)
    for l in range(0, num_numbers):
        arg_dict['number%s' % str(l+1)] = random.choice(numbers)

    book_title = t_format.format(**arg_dict).title()

    book_adjectives = [random.choice(book_description_adjectives), random.choice(book_description_adjectives)]
    book_s_desc = '%s %s book' % tuple(book_adjectives)
    book_l_desc = 'This is a ' + book_s_desc + ' titled ' + book_title + '.'

    number_pages = round(random.normalvariate(30, 15))

    page_msg = random.choices(book_messages, book_message_weights)[0]
    book_msg = """
\=============================================
%s
\=============================================""" % book_title
   
    for i in range(0, number_pages):
        book_msg += "\n#*\n" + page_msg
    
    random_book = library_book.LibraryBook('book', __file__, book_s_desc, book_l_desc)
    random_book.add_adjectives(*book_adjectives)
    random_book.set_message(book_msg)
    return random_book