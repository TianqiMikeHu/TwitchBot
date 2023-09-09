import requests
import boto3
import os

def get_user_tokens(user_id):
    client = boto3.client('dynamodb', region_name='us-west-2')
    response = client.get_item(
        Key={
            'CookieHash': {
                'S': user_id,
            }
        },
        TableName='CF-Cookies',
    )
    return response["Item"]


def validate(token):
    r = requests.get(url="https://id.twitch.tv/oauth2/validate", headers={"Authorization":f"Bearer {token}"})
    if r.status_code != 200:
        return 0
    else:
        return r.json().get('expires_in')


def refresh(user_id, refresh_token):
    refresh_token = requests.utils.quote(refresh_token, safe='')
    token_request = f"https://id.twitch.tv/oauth2/token?client_id={os.getenv('CLIENTID')}&client_secret={os.getenv('CLIENTSECRET')}&grant_type=refresh_token&refresh_token={refresh_token}"
    r = requests.post(url=token_request, headers={"Content-Type":"application/x-www-form-urlencoded"})
    access_token = r.json().get('access_token')
    refresh_token = r.json().get('refresh_token')
    client = boto3.client('dynamodb', region_name='us-west-2')
    response = client.update_item(
        ExpressionAttributeValues={
            ':a': {
                'S': access_token,
            },
            ':r': {
                'S': refresh_token,
            },
        },
        Key={
            'CookieHash': {
                'S': user_id,
            }
        },
        TableName='CF-Cookies',
        UpdateExpression='SET AccessToken = :a, RefreshToken = :r',
    )


def lambda_handler(event, context):
    
    users_list = ['160025583', '681131749', '598261113']
    
    for user_id in users_list:
        ddb_record = get_user_tokens(user_id)
        if validate(ddb_record['AccessToken']['S'])<3600:
            print(f"Refreshing tokens for {user_id}...")
            refresh(user_id, ddb_record['RefreshToken']['S'])
        
    
    return {
        'statusCode': 200,
        'body': ''
    }
