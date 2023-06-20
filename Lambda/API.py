import requests
import boto3
import os
import random
from websocket import create_connection
import json
import hmac
import hashlib
import time
import allowlist_anna

def get_header_user(bot=False, user='Mike_Hu_0_0'):
    ssm = boto3.client('ssm', 'us-west-2')
    
    if bot:
        key = 'ACCESSTOKEN_BOT'
    elif user=='AnnaAgtapp':
        key = 'ACCESSTOKEN_ANNA'
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

def refresh_token(bot=False, user='Mike_Hu_0_0'):
    ssm = boto3.client('ssm', 'us-west-2')
    
    if bot:
        refresh_key = 'REFRESH_BOT'
        access_key = 'ACCESSTOKEN_BOT'
    elif user=='AnnaAgtapp':
        refresh_key = 'REFRESH_ANNA'
        access_key = 'ACCESSTOKEN_ANNA'
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
    print("User access token refreshed")
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
    r = requests.get(url="https://api.twitch.tv/helix/users?login={0}".format(name), headers=get_header())
    if r.status_code!=200:
        if r.status_code!=401:
            return f'[ERROR]: status code is {str(r.status_code)}', 2
        else:
            print("[ERROR]: status code is 401. Getting new access token...")
            token = new_access_token()
            # print(f'The new access token is: {token}')
            r = requests.get(url="https://api.twitch.tv/helix/users?login={0}".format(name), headers=get_header())
            if r.status_code!=200:
                return f'[ERROR]: status code is {str(r.status_code)}', 2
    data = r.json()
    if len(data.get('data'))==0:
        return "[ERROR]: User not found", 1
    id = data.get('data')[0].get('id')
    return id, 0

    
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

    
def pushover(title, message, critical=False):
    body = {
        'token': os.getenv('PUSHOVER_APP_TOKEN'),
        'user': os.getenv('PUSHOVER_USER_TOKEN'),
        'device': 'mike-iphone',
        'title': title,
        'message': message
    }
    
    if critical:
        body["priority"] = 2
        body["retry"] = 30
        body["expire"] = 300

    r = requests.post('https://api.pushover.net/1/messages.json', json=body)

    if r.status_code!=200:
        print(r.text)
    return

    
def start_ec2():
    client = boto3.client('ec2')
    
    response = client.start_instances(
        InstanceIds=[
            'i-061d8d9ee16d08713',
        ]
    )

    for instance in response['StartingInstances']:
        id = instance['InstanceId']
        state = instance['CurrentState']['Name']
        pushover("STARTING INSTANCE", f"Instance {id} is now {state}", True)
    return


def stop_ec2():
    client = boto3.client('ec2')
    
    response = client.stop_instances(
        InstanceIds=[
            'i-061d8d9ee16d08713',
        ]
    )
    
    for instance in response['StoppingInstances']:
        id = instance['InstanceId']
        state = instance['CurrentState']['Name']
        pushover("STOPPING INSTANCE", f"Instance {id} is now {state}")
    return

def autoscale(name, capacity):
    client = boto3.client('autoscaling')
    
    response = client.set_desired_capacity(
        AutoScalingGroupName=f'AutoScaling-{name}',
        DesiredCapacity=capacity,
        HonorCooldown=False
    )
    
    pushover("AUTOSCALING", f"AutoScaling-{name} capacity set to {capacity}")
    return


def redeem(body):
    user_id = body.get('event', {}).get("user_id")
    user_name = body.get('event', {}).get("user_name")
    user_input = body.get('event', {}).get("user_input")
    broadcaster_user_login = body.get('event', {}).get("broadcaster_user_login")
    reward = body.get('event', {}).get("reward")
    if reward is None:
        return "[Error] The reward body is empty"
    # else:
    #     print(reward)
    title = reward.get("title")
    reward_id = reward.get("id")
    if title is None:
        return "[Error] Required field missing"
    
    title = title.lower()
    if title == "change the title":
        request_body = {"title": user_input}
        r = requests.patch(url="https://api.twitch.tv/helix/channels?broadcaster_id=160025583", headers=get_header_user(), json=request_body)
        if r.status_code!=204:
            if r.status_code!=401:
                return f'[ERROR]: status code is {str(r.status_code)}'
            else:
                print("[ERROR]: status code is 401. Getting new access token...")
                token, refresh = refresh_token()
                # print(f'The new access token is: {token}')
                # print(f'The new refresh token is: {refresh}')
                r = requests.patch(url="https://api.twitch.tv/helix/channels?broadcaster_id=160025583", headers=get_header_user(), json=request_body)
                if r.status_code!=204:
                    return f'[ERROR]: status code is {str(r.status_code)}'
                else:
                    return "Title updated successfully."
        else:
            return "Title updated successfully."
            
    elif title == "timeout yourself":
        if not user_input.isnumeric():
            return "[ERROR]: the input was not a a valid number"
        elif int(user_input)<1 or int(user_input)>1209600:
            return "[ERROR]: the input was not a a valid number"
        
        request_body = {"data": {"user_id": user_id, "duration": int(user_input), "reason": "Timeout Redeem"}}
        r = requests.post(url="https://api.twitch.tv/helix/moderation/bans?broadcaster_id=160025583&moderator_id=160025583", headers=get_header_user(True), json=request_body)
        if r.status_code!=200:
            if r.status_code!=401:
                return f'[ERROR]: status code is {str(r.status_code)}'
            else:
                print("[ERROR]: status code is 401. Getting new access token...")
                token, refresh = refresh_token(True)
                # print(f'The new access token is: {token}')
                # print(f'The new refresh token is: {refresh}')
                r = requests.post(url="https://api.twitch.tv/helix/moderation/bans?broadcaster_id=160025583&moderator_id=681131749", headers=get_header_user(True), json=request_body)
                if r.status_code!=200:
                    return f'[ERROR]: status code is {str(r.status_code)}'
                else:
                    return f"{user_name} is timed out for {user_input} seconds."
        else:
            return f"{user_name} is timed out for {user_input} seconds."
    
    elif title == "make an announcement":
        return announcement(f"{user_name}: {user_input}")
        
    elif reward_id == "a2bcb4ff-7b78-41ec-ab20-d5f1c11e087a":
        args = user_input.split(';')
        if len(args)<3:
            return "[ERROR]: Too few arguments"
            
        title = args[0].strip()
        if len(title)>60:
            return "[ERROR]: Title may not be longer than 60 characters."
        
        body = {
            "broadcaster_id":"598261113", 
            "title":title, 
            "choices":[],
            "duration": 120
        }
        
        for i in range(1, len(args)):
            if i>5:
                break
            option = args[i].strip()
            if len(option)>25:
                return "[ERROR]: An option may not be longer than 25 characters."
            body["choices"].append({"title": option})
            
        r = requests.post(url="https://api.twitch.tv/helix/polls/", headers=get_header_user(user='AnnaAgtapp'), json=body)

        if r.status_code==401:
            print("[ERROR]: status code is 401. Getting new access token...")
            refresh_token(user='AnnaAgtapp')
            r = requests.post(url="https://api.twitch.tv/helix/polls/", headers=get_header_user(user='AnnaAgtapp'), json=body)
    
        if r.status_code!=200:
            return f'[ERROR]: status code is {str(r.status_code)}'
        else:
            return ""
        
        
    elif reward_id == "22ad9f2a-fbe5-42a5-9b96-1999a0ed5f86" or reward_id=="cf9e9e23-7a07-4e14-80d6-4f1072067818":
        secret = os.getenv('SECRET')
        link = user_input
        
        index1 = link.rfind('/')
        index2 = link.rfind('?')
        if index1==-1 and index2==-1:
            id = link
        elif index1!=-1 and index2!=-1:
            id = link[index1+1:index2]
        elif index2==-1:
            id = link[index1+1:]
        elif index1==-1:
            id = link[:index2]
        else:
            return "[ERROR]: Could not interpret URL."
        src = ''
        duration = 0
        
        r = requests.get(url=f"https://api.twitch.tv/helix/clips?id={id}", headers=get_header_user())
        if r.status_code!=200:
            if r.status_code!=401:
                return f'[ERROR]: status code is {str(r.status_code)}'
            else:
                print("[ERROR]: status code is 401. Getting new access token...")
                token, refresh = refresh_token()
                # print(f'The new access token is: {token}')
                # print(f'The new refresh token is: {refresh}')
                r = requests.get(url=f"https://api.twitch.tv/helix/clips?id={id}", headers=get_header_user())
                if r.status_code!=200:
                    return f'[ERROR]: status code is {str(r.status_code)}'
        
        data = r.json()
        if len(data['data'])==0:
            return "[ERROR]: Could not find this clip."
        else:
            src = f"https://clips.twitch.tv/embed?clip={id}&parent=apoorlywrittenbot.cc&autoplay=true&controls=false"
            duration = data['data'][0]['duration']*1000
            broadcaster_name = data['data'][0]['broadcaster_name']
            
        if reward_id=='cf9e9e23-7a07-4e14-80d6-4f1072067818' and broadcaster_name not in allowlist_anna.ALLOWLIST:
            return "[ERROR]: Please ask the mods which clips are allowed."
        
        ws = create_connection("wss://2bd6aqqafb.execute-api.us-west-2.amazonaws.com/dev")
        
        payload = {
            "route": "sendmessage",
            "action": "newclip",
            "channel": broadcaster_user_login,
            "src": src,
            "duration": int(duration),
            "timestamp": str(time.time())
        }
        
        payload_string = json.dumps(payload, separators=(',', ':'))

        signature = hmac.new(secret.encode('utf-8'), msg=payload_string.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

        payload['signature'] = signature
        
        ws.send(json.dumps(payload))
        ws.close()
        return "Request processed successfully."
    
    return ""
    
def restricted_control(payload):
    ws = create_connection("wss://2bd6aqqafb.execute-api.us-west-2.amazonaws.com/dev")
    payload_string = json.dumps(payload, separators=(',', ':'))

    secret = os.getenv('SECRET')
    signature = hmac.new(secret.encode('utf-8'), msg=payload_string.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

    payload['signature'] = signature

    ws.send(json.dumps(payload))
    ws.close()
    return ""