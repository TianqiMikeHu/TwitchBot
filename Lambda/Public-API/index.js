const AWS = require('aws-sdk');
const ssm = new AWS.SSM({ region: 'us-west-2' });
const ddb = new AWS.DynamoDB.DocumentClient();

const getParam = (param, WithDecryption = false) => {
  return new Promise((res, rej) => {
    ssm.getParameter({
      Name: param, WithDecryption: WithDecryption
    }, (err, data) => {
        if (err) {
          return rej(err);
        }
        return res(data);
    });
  });
};

const getItem = (params) => {
  return new Promise((res, rej) => {
    ddb.get(params, (err, data) => {
        if (err) {
          return rej(err);
        }
        return res(data);
    });
  });
};

function forbidden() {
    return {
        isBase64Encoded: false,
        statusCode: '403',
        body: ''
    };
}

async function publicHandler(event){
    let chan;
    if (event.queryStringParameters != null) {
        chan = event.queryStringParameters.channel;
    }
    if (event.path == "/public/json"){
        if (chan == null) {return forbidden();}
        let params = {
          TableName : 'Mod-Interface-JSON',
          Key: {
            channel: chan
          }
        };
        const data = await getItem(params);
        if (Object.keys(data).length){
            return {
                isBase64Encoded: false,
                statusCode: '200',
                body: data.Item.json
            };
        }
        return forbidden();
    }
    else if (event.path == "/public/emote"){
        if (event.queryStringParameters == null) {
            return forbidden();
        }
        let name = event.queryStringParameters.name;
        if (name == null) {
            return forbidden();
        }
        let params = {
          TableName : 'Emotes',
          Key: {
            emote_name: name
          }
        };
        const data = await getItem(params);
        if (Object.keys(data).length){
            return {
                isBase64Encoded: false,
                statusCode: '200',
                body: JSON.stringify({id: data.Item.emote_id})
            };
        }
        else{
            return {
                isBase64Encoded: false,
                statusCode: '404',
                body: ''
            };
        }
    }
    else{
        return forbidden();
    }
}

exports.handler = async (event) => {
    if (event.httpMethod != "GET"){
        return forbidden();
    }
    if (event.path.startsWith("/public")){
        return await publicHandler(event);
    }
    return forbidden();
};
