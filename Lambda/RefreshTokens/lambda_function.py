import requests
import boto3
import os

def delete_token(key):
    client = boto3.client('dynamodb', region_name='us-west-2')
    response = client.delete_item(
        Key={
            'CookieHash': {
                'S': key,
            }
        },
        TableName='CF-Cookies',
    )


def validate(token):
    r = requests.get(url="https://id.twitch.tv/oauth2/validate", headers={"Authorization":f"Bearer {token}"})
    if r.status_code != 200:
        return 0
    else:
        return r.json().get('expires_in')


def refresh(key, refresh_token):
    refresh_token = requests.utils.quote(refresh_token, safe='')
    token_request = f"https://id.twitch.tv/oauth2/token?client_id={os.getenv('CLIENTID')}&client_secret={os.getenv('CLIENTSECRET')}&grant_type=refresh_token&refresh_token={refresh_token}"
    r = requests.post(url=token_request, headers={"Content-Type":"application/x-www-form-urlencoded"})
    
    if r.status_code != 200:
        if len(key)==64:
            delete_token(key)
        print(f"Failure refreshing {key}")
        return False
        
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
                'S': key,
            }
        },
        TableName='CF-Cookies',
        UpdateExpression='SET AccessToken = :a, RefreshToken = :r',
    )
    return True

def lambda_handler(event, context):
    
    # users_list = ['160025583', '681131749', '598261113', '687759326', '57184879']
    client = boto3.client('dynamodb', region_name='us-west-2')
    users_list = client.scan(TableName="CF-Cookies")
    
    alarm = False
    
    for user in users_list["Items"]:
        if user.get('RefreshToken'):
            if validate(user['AccessToken']['S'])<3600:
                print(f"Refreshing tokens for {user['CookieHash']['S']}...")
                success = refresh(user['CookieHash']['S'], user['RefreshToken']['S'])
                if not success:
                    alarm = True
                    print(user['CookieHash']['S'])
    
    if alarm:
        raise Exception("This should trigger CloudWatch alarm.")    
    
    return {
        'statusCode': 200,
        'body': ''
    }
