import json
import requests
import boto3
import os
import time

def lambda_handler(event, context):
    
    customheader = {"Client-ID":"6yz6w1tnl13svb5ligch31aa5hf4ty", 
    "Authorization":f"Bearer {event['access_token']}", 
    "Content-Type":"application/json"}
    
    broadcaster_list = []
    broadcaster_list.append(event['user_id'])
    
    r = requests.get(url=f"https://api.twitch.tv/helix/channels/followed?user_id={event['user_id']}&first=100", headers=customheader)

    print((r.json())["total"])
    while 1:
        data = r.json()
        for user in data["data"]:
            broadcaster_list.append(user["broadcaster_id"])
        if not data["pagination"]:
            break
        cursor = data["pagination"]["cursor"]
        r = requests.get(url=f"https://api.twitch.tv/helix/channels/followed?user_id={event['user_id']}&first=100&after={cursor}", headers=customheader)
    
    broadcaster_list = [broadcaster_list[i:i+10] for i in range(0, len(broadcaster_list), 10)]
    
    client = boto3.client('lambda')
    
    for group in broadcaster_list:
        payload = {'access_token': event['access_token'], 'broadcaster_list': group}
        payload = json.dumps(payload).encode('utf-8')
        client.invoke(
            FunctionName='EmoteLoader',
            InvocationType='Event',
            Payload=payload,
        )
    
    return {
        'statusCode': 200,
        'body': ''
    }
