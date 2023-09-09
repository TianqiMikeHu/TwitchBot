import socket
import json
import urllib
import API


def lambda_handler(event, context):
    print('event:', json.dumps(event))
    print('queryStringParameters:', json.dumps(event['queryStringParameters']))
    
    user = event['queryStringParameters'].get('user')
    key = event['queryStringParameters'].get('key')
    
    if user is None or key is None:
        return  {
            'statusCode': 200,
            'body': 'Usage: !getclip [user] [key words]'
        }
    if len(user)==0 or len(key)==0:
        return  {
            'statusCode': 200,
            'body': 'Usage: !getclip [user] [key words]'
        }
        
    user = urllib.parse.unquote_plus(user)
    key = urllib.parse.unquote_plus(key)
    
    result = API.getclip(user, key, API.get_header_user('160025583'))

    return  {
        'statusCode': 200,
        'body': result
    }
