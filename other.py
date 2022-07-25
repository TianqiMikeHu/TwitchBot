from tools import *
import API
import os
import random

################################################    Other functions
def lurk(attributes):
    return f"Enjoy the lurk, {attributes['author']}!"


def unlurk(attributes):
    return f"Welcome back {attributes['author']}! Hope you had fun."


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
    return attributes['scrapper'].se_handler(attributes['args'][1], attributes['args'][2], attributes['author'], attributes['args'][2:], attributes['header'])


def se_alias(attributes):
    if len(attributes['args'])<2:
        return None
    if attributes['args'][0][0]==COMMAND and attributes['args'][1][0]==COMMAND:
        if not os.path.isfile(f'SE_Cache/{attributes["args"][0][1:]}.txt'):
            return '[INFO]: If you meant to get a StreamElements command, it\'s not currently cached locally. Please use \'!se [streamer] ![command]\' first.'
        else:
            return attributes['scrapper'].se_handler(attributes['args'][0][1:], attributes['args'][1], attributes['author'], attributes['args'][1:], attributes['header'])
    else:
        return None


def se_clear(attributes):
    if len(attributes['args'])<2:
        return "Usage: !se_clear [streamer]"
    return attributes['scrapper'].se_clear(attributes['args'][1])


def blame(attributes):
    return f'Blame {random.choice(BLAME_LIST)}'


def blame2(attributes):
    chatters = API.ls_chatters(ME, attributes['header'])
    return f'Blame {random.choice(chatters)}'