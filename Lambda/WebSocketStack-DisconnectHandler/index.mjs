import { DynamoDBClient } from "@aws-sdk/client-dynamodb";
import { DynamoDBDocumentClient, DeleteCommand } from "@aws-sdk/lib-dynamodb";

const client = new DynamoDBClient({});
const docClient = DynamoDBDocumentClient.from(client);

export const handler = async(event) => {
  const command = new DeleteCommand({
    TableName: process.env.TABLE,
    Key: {
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

