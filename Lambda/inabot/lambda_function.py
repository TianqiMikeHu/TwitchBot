import uuid
import json
import boto3

def get_item(command):
    client = boto3.client('dynamodb')
    while 1:
        id = str(uuid.uuid4())
        response = client.query(
            KeyConditionExpression='command = :commandVal AND #U > :idVal',
            ExpressionAttributeNames={
                "#U":"UUID",
                "#R":"response"
            },
            ExpressionAttributeValues={
                ':commandVal': {
                    'S': command,
                },
                ':idVal': {
                    'S': id,
                }
            },
            ProjectionExpression='#R',
            TableName='inabot',
            Limit=1
        )
        if len(response['Items'])>0:
            return response['Items'][0]['response']['S']


def write_item(command, content):
    client = boto3.client('dynamodb')
    id = str(uuid.uuid4())
    response = client.put_item(
        Item={
            'command': {
                'S': command,
            },
            'UUID': {
                'S': id,
            },
            'response': {
                'S': content,
            },
        },
        TableName='inabot',
    )
    return response['ResponseMetadata']['HTTPStatusCode']
    

def lambda_handler(event, context):
    print('queryStringParameters:', json.dumps(event))
    
    command = event['queryStringParameters'].get('command').lower()
    content = event['queryStringParameters'].get('content')
    
    result = 'Bad Request'

    if command is None:
        return  {'statusCode': 200, 'body': result}

    if command == '!fierce':
        response = get_item('!fierce+')
        result = f"Fierce hates {response} inaboxMRDR"
        
    elif command == '!fierce+':
        if content is None:
            return  {'statusCode': 200, 'body': result}
        elif len(content)==0:
            return  {'statusCode': 200, 'body': result}
            
        statusCode = write_item(command, content)
        if statusCode == 200:
            result = f'\"{content}\" added to the !fierce list.'
        else:
            result = 'An error occurred @Mike_Hu_0_0'

    return  {
        'statusCode': 200,
        'body': result
    }