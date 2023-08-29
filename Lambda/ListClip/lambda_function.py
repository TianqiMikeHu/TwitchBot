import socket
import json
import urllib
import API

HOST = 'irc.chat.twitch.tv'
NICK = 'a_poorly_written_bot'
PORT = 6667
CHAN = '#mike_hu_0_0'


def lambda_handler(event, context):
    # print('event:', json.dumps(event))
    # print('queryStringParameters:', json.dumps(event['queryStringParameters']))
    
    user = event['queryStringParameters'].get('user')
    override = event['queryStringParameters'].get('override')
    max = event['queryStringParameters'].get('max')
    
    if user is None:
        return  {
            'statusCode': 200,
            'body': 'Usage: !listclip [user]'
        }
    if len(user)==0:
        return  {
            'statusCode': 200,
            'body': 'Usage: !listclip [user]'
        }
        
    user = urllib.parse.unquote_plus(user)
    
    result = API.listclip(user, override, max)

    return  {
        'statusCode': 200,
        'body': result
    }