import requests
import boto3
import os
import random
import difflib

def get_header_user(bot=False):
    ssm = boto3.client('ssm', 'us-west-2')
    
    if bot:
        key = 'ACCESSTOKEN_BOT'
    else:
        key = 'ACCESSTOKEN'
    
    response = ssm.get_parameter(
        Name=key,WithDecryption=True
    )
    
    user_access_token = response['Parameter']['Value']
    
    header = {"Client-ID": os.getenv('CLIENTID'), 
                "Authorization":"Bearer {0}".format(user_access_token), 
                "Content-Type":"application/json"}
    return header

def refresh_token(bot=False):
    ssm = boto3.client('ssm', 'us-west-2')
    
    if bot:
        refresh_key = 'REFRESH_BOT'
        access_key = 'ACCESSTOKEN_BOT'
    else:
        refresh_key = 'REFRESH'
        access_key = 'ACCESSTOKEN'
    
    response = ssm.get_parameter(
        Name=refresh_key,WithDecryption=True
    )
    
    refresh_token = response['Parameter']['Value']
    
    refresh = requests.utils.quote(refresh_token, safe='')
    token_request = f"https://id.twitch.tv/oauth2/token?client_id={os.getenv('CLIENTID')}&client_secret={os.getenv('CLIENTSECRET')}&grant_type=refresh_token&refresh_token="+refresh_token
    r = requests.post(url=token_request, headers={"Content-Type":"application/x-www-form-urlencoded"})
    print(r.json())
    token = (r.json()).get('access_token')
    refresh = (r.json()).get('refresh_token')
    
    response = ssm.put_parameter(
        Name=access_key,
        Value=token,
        Type='SecureString',
        Overwrite=True,
        Tier='Standard',
        DataType='text'
    )
    
    response = ssm.put_parameter(
        Name=refresh_key,
        Value=refresh,
        Type='SecureString',
        Overwrite=True,
        Tier='Standard',
        DataType='text'
    )
    
    
    return token, refresh


## return values: message, status code
def broadcaster_ID(name):
    r = requests.get(url="https://api.twitch.tv/helix/users?login={0}".format(name), headers=get_header_user())
    if r.status_code!=200:
        if r.status_code!=401:
            return f'[ERROR]: status code is {str(r.status_code)}', 2
        else:
            print("[ERROR]: status code is 401. Getting new access token...")
            refresh_token()
            # print(f'The new access token is: {token}')
            r = requests.get(url="https://api.twitch.tv/helix/users?login={0}".format(name), headers=get_header_user())
            if r.status_code!=200:
                return f'[ERROR]: status code is {str(r.status_code)}', 2
    data = r.json()
    if len(data.get('data'))==0:
        return "[ERROR]: User not found", 1
    id = data.get('data')[0].get('id')
    return id, 0, data.get('data')[0].get('display_name'), data.get('data')[0].get('offline_image_url'), data.get('data')[0].get('description')

    
def announcement(message):
    colors = ["blue", "green", "orange", "purple", "primary"]
    body = {"message": message,"color": random.choice(colors)}
    r = requests.post(url="https://api.twitch.tv/helix/chat/announcements?broadcaster_id=160025583&moderator_id=681131749", headers=get_header_user(True), json=body)
    if r.status_code!=204:
        if r.status_code!=401:
            return f'[ERROR]: status code is {str(r.status_code)}'
        else:
            print("[ERROR]: status code is 401. Getting new access token...")
            token, refresh = refresh_token(True)
            # print(f'The new access token is: {token}')
            # print(f'The new refresh token is: {refresh}')
            r = requests.post(url="https://api.twitch.tv/helix/chat/announcements?broadcaster_id=160025583&moderator_id=681131749", headers=get_header_user(True), json=body)
            if r.status_code!=204:
                return f'[ERROR]: status code is {str(r.status_code)}'
    return ""
    

def getclip(user, key):
    # Get user ID from name
    id, status, display_name, img, about = broadcaster_ID(user)
    if status:      # It's an error message
        return id

    header = get_header_user()


    # key = ' '.join(attributes['args'][2:])
    keyL = key.lower().split()
    limit = 20      # We're only gonna search 20*50 = 1000 clips

    # Get top clips
    r = requests.get(url="https://api.twitch.tv/helix/clips?broadcaster_id={0}&first=50".format(id), headers=header)
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
                return "Best match: {0}".format(clips.get(title))

        
        # Use difflib if still inconclusive
        result = difflib.get_close_matches(key, list(clips.keys()), cutoff=0.7)

        if len(result)!=0:
            return "Best match: {0}".format(clips.get(result[0]))

        limit-=1
        if limit==0:
            return "No result (limit reached)"

        pagination = data.get('pagination').get('cursor')
        if pagination is None or pagination=='':
            return "No result (end of pages)"
        # Continue from pagination index
        r = requests.get(url="https://api.twitch.tv/helix/clips?broadcaster_id={0}&first=50&after={1}".format(id, pagination), headers=header)
    
    return ""