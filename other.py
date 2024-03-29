from tools import *
import API
import os
import random

################################################    Other functions
def lurk(attributes):
    return f"Thanks for the lurk, {attributes['author']}! Let us know if you find anything interesting."


def unlurk(attributes):
    return f"Welcome back {attributes['author']}, hope you had fun!"


def updatedeath(attributes):
    if len(attributes['args'])<2:
        return "Usage: !updatedeath [link]"
    myquery = 'call bot.updatedeath(%s)'
    query(attributes['pool'], myquery, True, (attributes['args'][1],))
    return "Done"


def updatepb(attributes):
    if len(attributes['args'])<2:
        return "Usage: !updatepb [link]"
    myquery = 'call bot.updatepb(%s)'
    query(attributes['pool'], myquery, True, (attributes['args'][1],))
    return "Done"


def manifest(attributes):
    return ' '.join(attributes['args'][1:])


def se(attributes):
    if len(attributes['args'])<3:
        return "Usage: !se [streamer] ![command]"
    return attributes['scrapper'].se_handler(attributes['args'][1], attributes['args'][2], attributes['author'], attributes['args'][2:])


def se_alias(attributes):
    if len(attributes['args'])<2:
        return None
    if attributes['args'][0][0]==COMMAND and attributes['args'][1][0]==COMMAND:
        if not os.path.isfile(f'SE_Cache/{attributes["args"][0][1:]}.txt'):
            return '[INFO]: If you meant to get a StreamElements command, it\'s not currently cached locally. Please use \'!se [streamer] ![command]\' first.'
        else:
            return attributes['scrapper'].se_handler(attributes['args'][0][1:], attributes['args'][1], attributes['author'], attributes['args'][1:])
    else:
        return None


def se_clear(attributes):
    if len(attributes['args'])<2:
        return "Usage: !se_clear [streamer]"
    return attributes['scrapper'].se_clear(attributes['args'][1])


def blame(attributes):
    return f'Blame {random.choice(BLAME_LIST)}'


def blame2(attributes):
    chatters = API.ls_chatters(ME)
    return f'Blame {random.choice(chatters)}'


stipulation = None
STIPULATION_LIST = ['Melee+Bricks/Bottles Only', 'No Melee', 'Kill All', 'No Throwables', 'Whoa%', 'No Guns Kill All']

def next(attributes):
    global stipulation
    stipulation = random.choice(STIPULATION_LIST)
    return f'Next Stipulation: {stipulation}'

def current(attributes):
    global stipulation
    return f'Current Stipulation: {stipulation}' 