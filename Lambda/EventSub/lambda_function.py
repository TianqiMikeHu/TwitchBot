import hmac
import hashlib
import os
import json
import helper
import tools
import boto3
import time
    


def lambda_handler(event, context):
    if event.get('headers') is None or event.get('body') is None:
        return tools.forbidden()
    if event['headers'].get('cf-env') !=os.getenv('CF_ENV'):
        return tools.forbidden()
    body = json.loads(event['body'])
    # print(body)
    if event['headers'].get('Twitch-Eventsub-Message-Type') =='webhook_callback_verification':
        challenge = body.get('challenge')
        print(f"Challenge is: {challenge}")
        if challenge is not None:
            event_id = body['subscription']['id']
            event_type = body['subscription']['type']
            user_id = body['subscription']['condition']['broadcaster_user_id']
            tools.register_event(event_id, event_type, user_id)
            return tools.success(challenge)
        else:
            return tools.forbidden()

    ID = event['headers']['Twitch-Eventsub-Message-Id']
    timestamp = event['headers']['Twitch-Eventsub-Message-Timestamp']
    signature = event['headers']['Twitch-Eventsub-Message-Signature']
    # print("JSON: ", data)

    concat = ID + timestamp + event['body']
    # print(concat)
    secret = os.getenv('SECRET')
    my_signature = hmac.new(secret.encode('utf-8'), msg=concat.encode('utf-8'), digestmod=hashlib.sha256).hexdigest().lower()
    my_signature = "sha256=" + my_signature

    if signature!=my_signature:
        tools.send_twitchio(f"signature mismatch: {signature}/{my_signature}")
        return tools.forbidden()

    event_id = body['subscription']['id']
    event_type = body['subscription']['type']
    ddb_record = tools.get_event(event_id)
    
    function = getattr(helper, ddb_record['function']['S'])
    function(body['event'])
    
    return tools.success('')
    
    ##############################

    
