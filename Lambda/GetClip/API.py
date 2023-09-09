import requests
import boto3
import os
import random
import difflib

def get_header_user(user_id):
    client = boto3.client('dynamodb', region_name='us-west-2')
    response = client.get_item(
        Key={
            'CookieHash': {
                'S': user_id,
            }
        },
        TableName='CF-Cookies',
    )
    user_access_token =  response["Item"]['AccessToken']['S']
    
    header = {"Client-ID": os.getenv('CLIENTID'), 
                "Authorization":f"Bearer {user_access_token}", 
                "Content-Type":"application/json"}
    return header


def broadcaster_ID(name, header):
    r = requests.get(url=f"https://api.twitch.tv/helix/users?login={name}", headers=header)
    if r.status_code!=200:
        return None, f'[ERROR]: status code is {str(r.status_code)}'
    data = r.json()
    if len(data['data'])==0:
        return None, "[ERROR]: User not found"
    return data['data'][0], None
    

def getclip(user, key, header):
    # Get user ID from name
    user, error_message = broadcaster_ID(user, header)
    if not user:      # It's an error message
        return error_message
    id = user['id']

    # key = ' '.join(attributes['args'][2:])
    keyL = key.lower().split()
    limit = 20      # We're only gonna search 20*50 = 1000 clips

    # Get top clips
    r = requests.get(url=f"https://api.twitch.tv/helix/clips?broadcaster_id={id}&first=50", headers=header)
    while 1:
        if r.status_code!=200:
            print(r.status_code)
            return "[ERROR]: status code is not 200"
        data = r.json()

        # Put into a dictionary
        clips = {}
        for item in data.get('data'):
            title = item.get('title')
            link = item.get('url')
            if title is None or link is None:
                continue
            clips[title] = link


        # Check if the key words are all present
        for title in list(clips.keys()):
            titleL = title.lower()
            passed = True
            for k in keyL:
                if k not in titleL:
                    passed = False
                    break
            if passed:
                return f"Best match: {clips.get(title)}"

        
        # Use difflib if still inconclusive
        result = difflib.get_close_matches(key, list(clips.keys()), cutoff=0.7)

        if len(result)!=0:
            return f"Best match: {clips.get(result[0])}"

        limit-=1
        if limit==0:
            return "No result (limit reached)"

        pagination = data.get('pagination').get('cursor')
        if pagination is None or pagination=='':
            return "No result (end of pages)"
        # Continue from pagination index
        r = requests.get(url=f"https://api.twitch.tv/helix/clips?broadcaster_id={id}&first=50&after={pagination}", headers=header)
    
    return ""