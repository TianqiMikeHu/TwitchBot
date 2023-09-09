from websocket import create_connection
import hmac
import json
import os
import hashlib

def lambda_handler(event, context):
    payload = event
    
    ws = create_connection("wss://2bd6aqqafb.execute-api.us-west-2.amazonaws.com/dev")
    payload_string = json.dumps(payload, separators=(',', ':'), ensure_ascii=False)

    secret = os.getenv('SECRET')
    signature = hmac.new(secret.encode('utf-8'), msg=payload_string.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

    payload['signature'] = signature
    print(f"Sending payload_string: {payload_string}")

    ws.send(json.dumps(payload))
    ws.close()
    return ""
