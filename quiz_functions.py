from tools import *


#########################################################
# Quiz Bowl Game functions
def quiz_reset(attributes):
    if attributes['author'].lower()==attributes['quiz'].get_player() or attributes['author'].lower()==ME:
        attributes['quiz'].reset()
        return "Current bonus question ended."
    else:
        return "You are not the current player."

def quiz_start(attributes):
    if attributes['quiz'].get_state()!=0:
        return "A quiz is currently running. Please try !end"
    if len(attributes['args'])<3:
        return "Incorrect number of arguments."

    attributes['quiz'].reset()
    # Parse arguments
    category = attributes['args'][1].lower()
    catNum = 0
    difficulty = 0
    try:
        difficulty = int(attributes['args'][2])
    except ValueError:
        return "Difficulty must be an integer."
    if difficulty<1 or difficulty>9:
        return "Invalid difficulty."

    # Categories
    if category=='random':
        myquery = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from (bonus join (select * from tournaments where difficulty = %s) as b on bonus.tournament_id=b.id) order by rand() limit 1) as a on bonus_parts.bonus_id=a.id'
        result = query(attributes.get('pool'), myquery, False, (difficulty,))
        if len(result)<3:
            return "Sorry, something went wrong. Try again."
        attributes['quiz'] .set_parts([result[0][0], result[0][1], result[1][1], result[2][1]])
        attributes['quiz'].set_answers([result[0][2], result[1][2], result[2][2]])
        attributes['quiz'].grader(None)
        attributes['quiz'].set_player(attributes['author'].lower())
        return attributes['quiz'].get_parts(0) + SEPARATE + attributes['quiz'].get_parts(1)
    
    catNum = 0
    if category=='mythology':
        catNum = 14
    elif category=='literature':
        catNum = 15
    elif category=='trash':
        catNum = 16
    elif category=='science':
        catNum = 17
    elif category=='history':
        catNum = 18
    elif category=='religion':
        catNum = 19
    elif category=='geography':
        catNum = 20
    elif category=='fine_arts':
        catNum = 21
    elif category=='social_science':
        catNum = 22
    elif category=='philosophy':
        catNum = 25
    elif category=='current_events':
        catNum = 26
    elif category=='math':
        myquery = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from bonus where subcategory_id = 26 order by rand() limit 1) as a on bonus_parts.bonus_id=a.id'
        result = query(attributes['pool'], myquery, False, None)
        if len(result)<3:
            return "Sorry, something went wrong. Try again."
        attributes['quiz'].set_parts([result[0][0], result[0][1], result[1][1], result[2][1]])
        attributes['quiz'].set_answers([result[0][2], result[1][2], result[2][2]])
        attributes['quiz'].grader(None)
        attributes['quiz'].set_player(attributes['author'].lower())
        return attributes['quiz'].get_parts(0) + SEPARATE + attributes['quiz'].get_parts(1)
    elif category=='cs':
        myquery = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from bonus where subcategory_id = 23 order by rand() limit 1) as a on bonus_parts.bonus_id=a.id'
        result = query(attributes['pool'], myquery, False, None)
        if len(result)<3:
            return "Sorry, something went wrong. Try again."
        attributes['quiz'].set_parts([result[0][0], result[0][1], result[1][1], result[2][1]])
        attributes['quiz'].set_answers([result[0][2], result[1][2], result[2][2]])
        attributes['quiz'].grader(None)
        attributes['quiz'].set_player(attributes['author'].lower())
        return attributes['quiz'].get_parts(0) + SEPARATE + attributes['quiz'].get_parts(1)
    else:
        return "Invalid category."
    
    # Launch query
    myquery = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from (bonus join (select * from tournaments where difficulty = %s) as b on bonus.tournament_id=b.id) where category_id = %s order by rand() limit 1) as a on bonus_parts.bonus_id=a.id'
    result = query(attributes['pool'], myquery, False, (difficulty, catNum))
    if len(result)<3:
        return "Sorry, something went wrong. Try again."
    attributes['quiz'].set_parts([result[0][0], result[0][1], result[1][1], result[2][1]])
    attributes['quiz'].set_answers([result[0][2], result[1][2], result[2][2]])
    attributes['quiz'].grader(None)
    attributes['quiz'].set_player(attributes['author'].lower())
    return attributes['quiz'].get_parts(0) + SEPARATE + attributes['quiz'].get_parts(1)


def answer(attributes):
    if attributes['author'].lower()!=attributes['quiz'].player:
        return "You are not the current player, "+attributes['author']
    message = " ".join(attributes['args'][1:])
    reply, update = attributes['quiz'].grader(message)
    if update is not None:
        if update:
            myquery = 'UPDATE bot.viewers SET points = points+%s WHERE username = %s'
            query(attributes['pool'], myquery, True, (attributes['quiz'].get_score(), attributes['quiz'].player))
    return reply


def yes(attributes):
    if attributes['author'].lower()!=attributes['quiz'].player:
        return None
    reply, update = attributes['quiz'].yes_helper()
    if update is not None:
        if update:
            myquery = 'UPDATE bot.viewers SET points = points+%s WHERE username = %s'
            query(attributes['pool'], myquery, True, (attributes['quiz'].get_score(), attributes['quiz'].player))
    return reply


def no(attributes):
    if attributes['author'].lower()!=attributes['quiz'].player:
        return None
    reply, update = attributes['quiz'].no_helper()
    if update is not None:
        if update:
            myquery = 'UPDATE bot.viewers SET points = points+%s WHERE username = %s'
            query(attributes['pool'], myquery, True, (attributes['quiz'].get_score(), attributes['quiz'].player))
    return reply