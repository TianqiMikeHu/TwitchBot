import requests
import boto3
import os
import random
import json
import time
import tools

def mike_poll_begin(event):
    title = event['title']
    broadcaster_user_login = event['broadcaster_user_login']
    choices = event['choices']
    if title is not None and choices is not None:
        message = f"PopCorn We have a new poll about...\"{title}\". The options are:"
        try:
            for i in range(len(choices)):
                option = choices[i].get("title")
                message = message + " " + str(i+1) + ") " + option
        except:
            raise Exception("Error assembling message")
        tools.send_twitchio(message)
        
def anna_poll_begin(event):
    title = event['title']
    broadcaster_user_login = event['broadcaster_user_login']
    choices = event['choices']
    if title is not None and choices is not None:
        message = "There is a new poll agtappDisco"
        tools.send_twitchio(message, "AnnaAgtapp")
        
def mike_online(event):
    username = event['broadcaster_user_name']
    tools.autoscale(username.lower(), 1)
    
def britt_online(event):
    username = event['broadcaster_user_name']
    response = "!funfact"
    tools.send_twitchio(response, username)
    tools.autoscale(username.lower(), 1)
    tools.pushover("ONLINE EVENT", "Britt is online", True)
    
def mikki_online(event):
    username = event['broadcaster_user_name']
    tools.autoscale(username.lower(), 1)
    
def anna_online(event):
    username = event['broadcaster_user_name']
    tools.autoscale(username.lower(), 1)
    
def mike_offline(event):
    username = event['broadcaster_user_name']
    offline_msg = "Stream is offline. Autoscaling in..."
    tools.pushover("AUTOSCALING", f"AutoScaling-{username.lower()} capacity set to 0")
    tools.send_twitchio(offline_msg, username)
    
def britt_offline(event):
    username = event['broadcaster_user_name']
    offline_msg = "Stream is offline. Autoscaling in..."
    tools.pushover("AUTOSCALING", f"AutoScaling-{username.lower()} capacity set to 0")
    tools.send_twitchio(offline_msg, username)
    
def mikki_offline(event):
    username = event['broadcaster_user_name']
    offline_msg = "Stream is offline. Autoscaling in..."
    tools.pushover("AUTOSCALING", f"AutoScaling-{username.lower()} capacity set to 0")
    tools.send_twitchio(offline_msg, username)
    
def anna_offline(event):
    username = event['broadcaster_user_name']
    offline_msg = "Stream is offline. Autoscaling in..."
    tools.pushover("AUTOSCALING", f"AutoScaling-{username.lower()} capacity set to 0")
    tools.send_twitchio(offline_msg, username)

def mike_follow(event):
    target = event['user_name']
    if target is not None:
        message = f"{target}, thank you so much for the follow! Welcome to the stream!"
        tools.send_twitchio(message)
        
def mike_prediction_begin(event):
    title = event['title']
    outcomes = event['outcomes']
    if title is not None and outcomes is not None:
        outcome_0 = outcomes[0]['title']
        outcome_1 = outcomes[1]['title']
        message = f"Prediction: \"{title}\" Waste your points between *{outcome_0}* and *{outcome_1}*, chat!"
        tools.send_twitchio(message)
        
def mike_subscribe(event):
    user_name = event['user_name']
    tier = event['tier']
    if user_name is not None and tier is not None:
        try:
            tier = int(tier) // 1000
            message = f"Whoa, {user_name} just subscribed at tier {str(tier)}! Thank you so much!"
        except:
            message = f"Whoa, {user_name} just subscribed! Thank you so much!"
        tools.send_twitchio(message)
        
def mike_subscription_message(event):
    user_name = event['user_name']
    tier = event['tier']
    cumulative_months = event['cumulative_months']
    if user_name is not None and tier is not None:
        try:
            tier = int(tier) // 1000
            if cumulative_months>1:
                cumulative_months = str(cumulative_months)
                message = f"Whoa, {user_name} just resubscribed at tier {str(tier)} for {cumulative_months} months! Thank you so much!"
        except:
            message = f"Whoa, {user_name} just resubscribed! Thank you so much!"
        tools.send_twitchio(message)
        
def mike_cheer(event):
    is_anonymous = event['is_anonymous']
    if not is_anonymous:
        user_name = event['user_name']
        bits = event['bits']
        if user_name is not None and bits is not None:
            try:
                bits = str(bits)
                message = f"PogChamp {user_name} just cheered for {bits} bits! I really appreaciate it :D"
                tools.send_twitchio(message)
            except:
                pass
            
def mike_raid(event):
    from_broadcaster_user_name = event['from_broadcaster_user_name']
    if from_broadcaster_user_name is not None:
        message = f"Welcome, raiders from {from_broadcaster_user_name}\'s channel!"
        tools.send_twitchio(message)
        
def anna_clips(event):
    secret = os.getenv('SECRET')
    broadcaster_user_login = event['broadcaster_user_login']
    link = event['user_input']
    
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
        tools.send_twitchio("[ERROR]: Could not interpret URL.", broadcaster_user_login)
    src = ''
    duration = 0
    
    r = requests.get(url=f"https://api.twitch.tv/helix/clips?id={id}", headers=tools.get_header_user('160025583'))
    if r.status_code!=200:
        tools.send_twitchio(f'[ERROR]: status code is {str(r.status_code)}', broadcaster_user_login)
        return
    
    data = r.json()
    if len(data['data'])==0:
        tools.send_twitchio("[ERROR]: Could not find this clip.", broadcaster_user_login)
        return
    else:
        src = f"https://clips.twitch.tv/embed?clip={id}&parent=apoorlywrittenbot.cc&autoplay=true&controls=false"
        duration = data['data'][0]['duration']*1000+300
        broadcaster_name = data['data'][0]['broadcaster_name']
        
    if broadcaster_name != "AnnaAgtapp":
        tools.send_twitchio("[ERROR]: Only Anna's clips are allowed.", broadcaster_user_login)
        return
    
    payload = {
        "route": "sendmessage",
        "action": "newclip",
        "channel": f"{broadcaster_user_login}-clip",
        "src": src,
        "duration": int(duration),
        "timestamp": str(time.time())
    }
    
    client = boto3.client('lambda')
    client.invoke(
        FunctionName='wss',
        InvocationType='Event',
        Payload=json.dumps(payload).encode('utf-8'),
    )
    message = "Request processed successfully."
    tools.send_twitchio(message, broadcaster_user_login)
    
def anna_create_poll(event):
    broadcaster_user_login = event['broadcaster_user_login']
    user_input = event['user_input']
    args = user_input.split(';')
    if len(args)<3:
        tools.send_twitchio("[ERROR]: Too few arguments", broadcaster_user_login)
        return
        
    title = args[0].strip()
    if len(title)>60:
        tools.send_twitchio("[ERROR]: Title may not be longer than 60 characters.", broadcaster_user_login)
        return
    
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
            tools.send_twitchio("[ERROR]: An option may not be longer than 25 characters.", broadcaster_user_login)
            return
        body["choices"].append({"title": option})
        
    r = requests.post(url="https://api.twitch.tv/helix/polls/", headers=tools.get_header_user('598261113'), json=body)

    if r.status_code!=200:
        message =  f'[ERROR]: status code is {str(r.status_code)}'
        tools.send_twitchio(message, broadcaster_user_login)
        
def mike_clips(event):
    secret = os.getenv('SECRET')
    broadcaster_user_login = event['broadcaster_user_login']
    link = event['user_input']
    
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
        tools.send_twitchio("[ERROR]: Could not interpret URL.")
        return
    src = ''
    duration = 0
    
    r = requests.get(url=f"https://api.twitch.tv/helix/clips?id={id}", headers=tools.get_header_user('160025583'))
    if r.status_code!=200:
        tools.send_twitchio(f'[ERROR]: status code is {str(r.status_code)}')
        return
    
    data = r.json()
    if len(data['data'])==0:
        tools.send_twitchio("[ERROR]: Could not find this clip.")
        return
    else:
        src = f"https://clips.twitch.tv/embed?clip={id}&parent=apoorlywrittenbot.cc&autoplay=true&controls=false"
        duration = data['data'][0]['duration']*1000+300
        broadcaster_name = data['data'][0]['broadcaster_name']

    payload = {
        "route": "sendmessage",
        "action": "newclip",
        "channel": f"{broadcaster_user_login}-clip",
        "src": src,
        "duration": int(duration),
        "timestamp": str(time.time())
    }
    
    client = boto3.client('lambda')
    client.invoke(
        FunctionName='wss',
        InvocationType='Event',
        Payload=json.dumps(payload).encode('utf-8'),
    )
    message = "Request processed successfully."
    tools.send_twitchio(message)
    
def mike_announcement(event):
    user_input = event['user_input']
    user_name = event['user_name']
    tools.announcement(f"{user_name}: {user_input}", '160025583', '681131749')
    
def mike_timeout(event):
    user_input = event['user_input']
    user_name = event['user_name']
    user_id = event['user_id']
    if not user_input.isnumeric():
        tools.send_twitchio("[ERROR]: the input was not a a valid number")
        return
    elif int(user_input)<1 or int(user_input)>1209600:
        tools.send_twitchio("[ERROR]: the input was not a a valid number")
        return
    
    request_body = {"data": {"user_id": user_id, "duration": int(user_input), "reason": "Timeout Redeem"}}
    r = requests.post(url="https://api.twitch.tv/helix/moderation/bans?broadcaster_id=160025583&moderator_id=681131749", headers=tools.get_header_user('681131749'), json=request_body)
    if r.status_code!=200:
        tools.send_twitchio(f'[ERROR]: status code is {str(r.status_code)}')
    else:
        tools.send_twitchio(f"{user_name} is timed out for {user_input} seconds.")
        
def mike_change_title(event):
    user_input = event['user_input']
    request_body = {"title": user_input}
    r = requests.patch(url="https://api.twitch.tv/helix/channels?broadcaster_id=160025583", headers=tools.get_header_user('160025583'), json=request_body)
    if r.status_code!=204:
        tools.send_twitchio(f'[ERROR]: status code is {str(r.status_code)}')
    else:
        tools.send_twitchio("Title updated successfully.")
