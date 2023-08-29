import requests
import boto3
import os


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


def lambda_handler(event, context):
    
    token, refresh = refresh_token()
    token, refresh = refresh_token(bot=True)
    token, refresh = refresh_token(user='AnnaAgtapp')
    
    return {
        'statusCode': 200,
        'body': ''
    }
