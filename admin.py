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


def start_listening(attributes):
    attributes['audio'].start_listening()
    return "Started listening..."

def stop_listening(attributes):
    attributes['audio'].stop_listening()
    return "Stopped listening..."

def add_audio_key(attributes):
    if len(attributes['args'])<3:
        return "[ERROR] Too few arguments"
    
    args = ' '.join(attributes['args'][1:])

    if ';' not in args:
        return "[ERROR] Incorrect format"

    args = args.split(';')

    myquery = 'INSERT INTO bot.audio_key(keyword,response,count,enabled) VALUES (%s, %s, 0, 1)'
    key = args[0].lower().strip()
    response = args[1].strip()
    
    if len(key)>20 or len(response)>80: # Table column limit
        return "[ERROR] Too many characters"

    print(f'key: {key} | response: {response}')

    query(attributes['pool'], myquery, True, (key, response))

    attributes['audio'].load_audio_keywords()

    return f"New key \"{key}\" added successfully."


def audio_debug(attributes):
    return attributes['audio'].toggle_debug()

def shutdown(attributes):
    web_scrapper.exit_event.set()
    # attributes['audio'].stop_listening()
    sys.exit()