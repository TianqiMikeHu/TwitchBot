import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { PutCommand, DynamoDBDocumentClient } from "@aws-sdk/lib-dynamodb";

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

export const handler = async(event) => {
  const command = new PutCommand({
    TableName: process.env.TABLE,
    Item: {
        connectionID: event.requestContext.connectionId,
    },
  });

  try {
    await docClient.send(command);
    return {statusCode: 200};
  }
  catch (err){
    console.log(err);
    return {statusCode: 500};
  }
};