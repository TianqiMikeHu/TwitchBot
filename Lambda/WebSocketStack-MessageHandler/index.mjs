import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, UpdateCommand, ScanCommand } from "@aws-sdk/lib-dynamodb";
import { ApiGatewayManagementApiClient, PostToConnectionCommand } from "@aws-sdk/client-apigatewaymanagementapi";
import crypto from 'crypto';

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

async function broadcast(endpoint, connections, body_channel, payload){
    const callbackAPI = new ApiGatewayManagementApiClient({
  		apiVersion: "2018-11-29",
  		endpoint: endpoint
  	});
  	let input, command;
    await Promise.all(connections.Items.map(async ({ connectionID, channel }) => {
        input = { 
          Data: JSON.stringify(payload),
          ConnectionId: connectionID,
        };
        command = new PostToConnectionCommand(input);
        if (channel == body_channel) {
            try {
                await callbackAPI.send(command);
            } catch (err) {
                console.log(err);
                return {statusCode: 500};
            }
        }
    }));
    return { 
        statusCode: 200
    };
}

export const handler = async (event) => {
  let command, connections;
  
  command = new ScanCommand({
    TableName: process.env.TABLE,
  });
  
  try {
    connections = await docClient.send(command);
  }
  catch (err){
    console.log(err);
    return {statusCode: 500};
  }
	
	const body = JSON.parse(event.body);
  if (body.action == 'joinchannel') {
      if (body.channel == null) {
          return { statusCode: 400 };
      }
      command = new UpdateCommand({
        TableName: process.env.TABLE,
        Key: {
            connectionID : event.requestContext.connectionId
        },
        UpdateExpression: "set channel = :x",
        ExpressionAttributeValues: {
          ":x": body.channel
        },
      });
      
      try {
          await docClient.send(command);
      } 
      catch (err) {
          console.log(err);
          return {statusCode: 500};
      }
      return {statusCode: 200};
  }
  else if (body.action == 'newclip' || body.action == 'modaction') {
      console.log(event.body);
      let signature = body['signature'];
      delete body['signature'];

      const hash = crypto
          .createHmac('sha256', Buffer.from(process.env.SECRET, 'utf-8'))
          .update(JSON.stringify(body), "utf8")
          .digest('hex');

      if (signature != hash) {
          console.log(`403: ${hash}`);
          return { statusCode: 403 };
      }
      return await broadcast(`https://${event.requestContext.domainName}/${event.requestContext.stage}`, connections, body.channel, body);
  }


  return { statusCode: 200 };
};
