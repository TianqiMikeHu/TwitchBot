import sys
from tools import *
import web_scrapper


def createcmd(attributes):
    if len(attributes['args'])<3:
        return "Usage: !createcmd [name] [response]"
    myquery = 'select * from bot.commands where command_name=%s'
    result = query(attributes['pool'], myquery, False, (attributes['args'][1].lower(),))
    if len(result)>0:
        return "This command already exists."
    myquery = 'call bot.createcmd(%s, %s)'
    query(attributes['pool'], myquery, True, (attributes['args'][1].lower(), ' '.join(attributes['args'][2:])))
    return "Done"



def editcmd(attributes):
    if len(attributes['args'])<3:
        return "Usage: !editcmd [name] [response]"
    myquery = 'select * from bot.commands where command_name=%s'
    result = query(attributes['pool'], myquery, False, (attributes['args'][1].lower(),))
    if len(result)==0:
        return "This command does not exist."
    myquery = 'call bot.editcmd(%s, %s)'
    query(attributes['pool'], myquery, True, (attributes['args'][1].lower(), ' '.join(attributes['args'][2:])))
    return "Done"



def deletecmd(attributes):
    if len(attributes['args'])<2:
        return "Usage: !deletecmd [name]"
    myquery = 'select * from bot.commands where command_name=%s'
    result = query(attributes['pool'], myquery, False, (attributes['args'][1].lower(),))
    if len(result)==0:
        return "This command does not exist."
    myquery = 'call bot.deletecmd(%s)'
    query(attributes['pool'], myquery, True, (attributes['args'][1].lower(),))
    return "Done"



def editaccess(attributes):
    if len(attributes['args'])<3:
        return "Usage: !editaccess [name] [access]"
    if attributes['args'][2] not in ['E', 'M']:
        return "Not a valid access level"
    myquery = 'select * from bot.commands where command_name=%s'
    result = query(attributes['pool'], myquery, False, (attributes['args'][1].lower(),))
    if len(result)==0:
           return "This command does not exist."
    myquery = 'call bot.editaccess(%s, %s)'
    query(attributes['pool'], myquery, True, (attributes['args'][1].lower(), attributes['args'][2]))
    return "Done"


def shutdown(attributes):
    web_scrapper.exit_event.set()
    sys.exit()