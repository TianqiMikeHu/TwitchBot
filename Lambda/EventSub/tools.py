import requests
import boto3
import os
import random
import json
import time
import socket
from twitchio.ext import commands

HOST = 'irc.chat.twitch.tv'
PORT = 6667
NICK = 'a_poorly_written_bot'

cold_start = True

def send_twitchio(message, chan="mike_hu_0_0"):
    global cold_start
    if not cold_start:
        send_socket(message, chan)
        return
    
    class Bot(commands.Bot):
        def __init__(self):
            channel = chan
            super().__init__(token=os.getenv('TWITCH_OAUTH_TOKEN'), prefix='!', initial_channels=[channel])
            self.channel = channel
    
        async def event_ready(self):
            chan = self.get_channel(self.channel)
            await chan.send(message)
            self.loop.stop()
            return
        
    bot = Bot()
    bot.run()
    cold_start = False
    
    try:
        client = boto3.client('lambda')
        response = client.update_function_configuration(
            FunctionName='EventSub',
            Description=f'Modified{str(time.time_ns())}'
        )
    except:
        pass
    
def send_socket(message, chan="mike_hu_0_0"):
    password = os.getenv('TWITCH_OAUTH_TOKEN')
    # print(password)
    channel =  chan
    try:
        s = socket.socket()
    except:
        raise Exception("Socket Creation")

    try:
        s.connect((HOST, PORT))
    except:
        s.close()
        raise Exception("Connect")

    try:
        s.sendall(f"PASS {password}\r\n".encode('utf-8'))
        s.sendall(f"NICK {NICK}\r\n".encode('utf-8'))
        s.sendall(f"JOIN #{channel}\r\n".encode('utf-8'))
        s.sendall(f"PRIVMSG #{channel} : {message}\r\n".encode('utf-8'))
        s.sendall(f"PART #{channel}\r\n".encode('utf-8'))
    except:
        raise Exception("Socket Error")
    finally:
        s.shutdown(socket.SHUT_RDWR)
        s.close()

def forbidden():
    return {
        'isBase64Encoded': False,
        'statusCode': '403',
        'body': ''
    }
    
def success(bodyText):
    return {
        'isBase64Encoded': False,
        'statusCode': '200',
        'body': bodyText
    }

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

def autoscale(name, capacity):
    client = boto3.client('autoscaling')
    
    response = client.set_desired_capacity(
        AutoScalingGroupName=f'AutoScaling-{name}',
        DesiredCapacity=capacity,
        HonorCooldown=False
    )
    
    pushover("AUTOSCALING", f"AutoScaling-{name} capacity set to {capacity}")
    return

def register_event(event_id, event_type, user_id):
    client = boto3.client('dynamodb')
    response = client.put_item(
        Item={
            'event_id': {
                'S': event_id,
            },
            'event_type': {
                'S': event_type,
            },
            'user_id': {
                'S': user_id,
            },
            'function': {
                'S': '',
            }
        },
        TableName='EventSub',
    )
    
def get_event(event_id):
    client = boto3.client('dynamodb')
    response = client.get_item(
        Key={
            'event_id': {
                'S': event_id,
            }
        },
        TableName='EventSub',
    )
    return response["Item"]
    
def announcement(message, broadcaster_id, moderator_id):
    colors = ["blue", "green", "orange", "purple", "primary"]
    body = {"message": message,"color": random.choice(colors)}
    r = requests.post(url=f"https://api.twitch.tv/helix/chat/announcements?broadcaster_id={broadcaster_id}&moderator_id={moderator_id}", headers=get_header_user('681131749'), json=body)
    if r.status_code!=204:
        send_twitchio(f'[ERROR]: status code is {str(r.status_code)}', broadcaster_id)
    return ""