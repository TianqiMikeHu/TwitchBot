import json
import requests
import boto3
import os
import time

def lambda_handler(event, context):
    emotes_list = []
    broadcaster_list = event['broadcaster_list']
    
    customheader = {"Client-ID":"6yz6w1tnl13svb5ligch31aa5hf4ty", 
    "Authorization":f"Bearer {event['access_token']}", 
    "Content-Type":"application/json"}

    i = -1
    backoff = 1.25
    while i<len(broadcaster_list)-1:
        i+=1
        r = requests.get(url=f"https://api.twitch.tv/helix/chat/emotes?broadcaster_id={broadcaster_list[i]}", headers=customheader)
        if r.status_code == 429:
            time.sleep(backoff)
            backoff = backoff**1.5
            i-=1
            continue
        if r.status_code != 200:
            continue
        data = (r.json())["data"]
        for emote in data:
            emote_id = emote["id"]
            if "animated" in emote["format"]:
                emote_id+="/animated"
            else:
                emote_id+="/static"
            emotes_list.append((emote["name"], emote_id))
    
    client = boto3.client('dynamodb')
    emotes_list = [emotes_list[i:i+25] for i in range(0, len(emotes_list), 25)]
    for group in emotes_list:
        parameter = []
        for emote in group:
            parameter.append({'PutRequest': {
                                'Item': {
                                    'emote_name': {
                                        'S': emote[0],
                                    },
                                    'emote_id': {
                                        'S': emote[1],
                                    }
                                }
                            }})

        response = client.batch_write_item(
                RequestItems={
                    'Emotes': parameter
                }
            )
            
        while response['UnprocessedItems']:
            time.sleep(backoff)
            backoff = backoff**1.5
            response = client.batch_write_item(
                RequestItems={
                    'Emotes': response['UnprocessedItems']
                }
            )
    
    return {
        'statusCode': 200,
        'body': ''
    }
