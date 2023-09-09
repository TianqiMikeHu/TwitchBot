import socket
import json
import urllib
import API


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
    
    result = API.listclip(user, override, max, API.get_header_user('160025583'))

    return  {
        'statusCode': 200,
        'body': result
    }