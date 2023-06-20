const AWS = require('aws-sdk');
const crypto = require('crypto');
const ddb = new AWS.DynamoDB.DocumentClient();
var callbackAPI, connections;

async function broadcast(body_channel, payload){
    const sendMessages = connections.Items.map(async ({ connectionId, channel }) => {
        if (channel == body_channel) {
            try {
                await callbackAPI
                    .postToConnection({ ConnectionId: connectionId, Data: JSON.stringify(payload) })
                    .promise();
            } catch (e) {
                console.log(e);
            }
        }
    });

    try {
        await Promise.all(sendMessages);
    } catch (e) {
        console.log(e);
        return {
            statusCode: 500,
        };
    }
    console.log(payload);
    return { 
        statusCode: 200
    };
} 

exports.handler = async function (event, context) {
    try {
        connections = await ddb.scan({ TableName: process.env.table }).promise();
    } catch (err) {
        return {
            statusCode: 500,
        };
    }
    callbackAPI = new AWS.ApiGatewayManagementApi({
        apiVersion: '2018-11-29',
        endpoint:
            event.requestContext.domainName + '/' + event.requestContext.stage,
    });

    const body = JSON.parse(event.body);
    if (body.action == 'joinchannel') {
        if (body.channel == null) {
            return { statusCode: 400 };
        }
        let params = {
            TableName: process.env.table,
            Key: {
                "connectionId": event.requestContext.connectionId
            },
            UpdateExpression: "set channel = :x",
            ExpressionAttributeValues: {
                ":x": body.channel
            }
        };
        try {
            await ddb.update(params).promise();
        } catch (err) {
            console.log(err);
            return {
                statusCode: 500,
            };
        }
        return { 
            statusCode: 200
        };
    }
    else if (body.action == 'newclip' || body.action == 'modaction') {
        console.log(body);
        let signature = body['signature'];
        delete body['signature'];

        const hash = crypto
            .createHmac('sha256', process.env.SECRET)
            .update(JSON.stringify(body), "utf8")
            .digest('hex');

        if (signature != hash) {
            console.log(`403: ${hash}`);
            return { statusCode: 403 };
        }

        return await broadcast(body.channel, body);
    }
    else if (body.action == 'pollstart' || body.action == 'pollend') {
        let signature = body['signature'];
        delete body['signature'];

        const hash = crypto
            .createHmac('sha256', process.env.SECRET)
            .update(JSON.stringify(body), "utf8")
            .digest('hex');

        if (signature != hash) {
            return { statusCode: 403 };
        }

        return await broadcast(body.channel, body);
    }


    return { statusCode: 200 };
};