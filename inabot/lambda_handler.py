import random
import json
import boto3

def lambda_handler(event, context):
    print('queryStringParameters:', json.dumps(event['queryStringParameters']))
    
    command = event['queryStringParameters'].get('command').lower()
    content = event['queryStringParameters'].get('content')
    
    result = 'Bad request'
    
    if len(command) == 0:
        return  {
            'statusCode': 200,
            'body': result
        }
    
    if command == '!fierce':
        client = boto3.client('s3', region_name='us-west-2')
        obj = client.get_object(Bucket='inabot', Key='fierce.txt')
        obj_bytes = obj['Body'].read()
        text = obj_bytes.decode("utf-8")
        text = text.split("\r\n")

        result = f"Fierce hates {random.choice(text)} inaboxMRDR"
        
    elif command == '!fierce+' and len(content)>0:
        client = boto3.client('s3')
        obj = client.get_object(Bucket='inabot', Key='fierce.txt')
        text = obj['Body'].read().decode("utf-8")
        text+=f'\r\n{content}'
        
        client = boto3.client('s3', region_name='us-west-2')
    
        response = client.put_object(
            ACL='bucket-owner-full-control',
            Body=text.encode("utf-8"),
            Bucket='inabot',
            ContentType='text/plain',
            Key='fierce.txt'
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            result = f'\"{content}\" added to the !fierce list.'
        else:
            result = 'An error occurred @Mike_Hu_0_0'

    return  {
        'statusCode': 200,
        'body': result
    }