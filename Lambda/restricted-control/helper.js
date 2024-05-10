const SIGNATURE = "CloudFront-Signature=";
const AWS = require('aws-sdk');
const ddb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();
const parameterStore = new AWS.SSM();
const { createHash } = require('crypto');
const axios = require('axios');
const sqs = new AWS.SQS();
const sts = new AWS.STS();

module.exports = function(){
    this.forbidden = function() {
        return {
            isBase64Encoded: false,
            statusCode: '403',
            body: ''
        };
    };
    this.success = function(bodyText) {
        return {
            isBase64Encoded: false,
            statusCode: '200',
            body: bodyText
        };
    };
    this.timeout = function() {
        return {
            isBase64Encoded: false,
            statusCode: '504',
            body: ''
        };
    };
    this.getItem = function(params) {
      return new Promise((res, rej) => {
        ddb.get(params, (err, data) => {
            if (err) {
              return rej(err);
            }
            return res(data);
        });
      });
    };
    this.getVariable = async function(query) {
        let variable;
        switch (query) {
            case 'commands':
                variable = '_commands_json';
                break;
            case 'counters':
                variable = '_counters_json';
                break;
            case 'fierce':
                variable = 'quotes_!fierce';
                break;
            case 'kimexplains':
                variable = 'quotes_!kimexplains';
                break;
            default:
                return this.forbidden();
        }
        let params = {
          TableName : 'inabot-variables',
          Key: {
            var_name: variable,
            var_type: 'CUSTOM'
          }
        };
        const data = await this.getItem(params);
        if (Object.keys(data).length){
            return this.success(JSON.stringify({'value': data.Item.var_val}));
        } 
        else {return this.forbidden();}
    };
    this.getCommand = async function(query) {
        let params = {
          TableName : 'inabot-commands',
          Key: {
            command_name: query
          }
        };
        const data = await this.getItem(params);
        if (Object.keys(data).length){
            return this.success(JSON.stringify(data.Item));
        } 
        else {return this.forbidden();}
    };
    this.getCounter = async function(query) {
        let params = {
          TableName : 'inabot-variables',
          Key: {
            var_name: query,
            var_type: 'COUNTER'
          }
        };
        const data = await this.getItem(params);
        if (Object.keys(data).length){
            return this.success(JSON.stringify(data.Item));
        } 
        else {return this.forbidden();}
    };
    this.getKimexplain = async function(query) {
        let index = parseInt(query);
        if (!index){
            return this.forbidden();
        }
        let params = {
          TableName : 'inabot-quotes',
          Key: {
            quotes_name: '!kimexplains',
            quotes_index: index
          }
        };
        const data = await this.getItem(params);
        if (Object.keys(data).length){
            return this.success(JSON.stringify(data.Item));
        } 
        else {return this.forbidden();}
    };
    this.getFierce = async function(query) {
        let index = parseInt(query);
        if (!index){
            return this.forbidden();
        }
        let params = {
          TableName : 'inabot-quotes',
          Key: {
            quotes_name: '!fierce',
            quotes_index: index
          }
        };
        const data = await this.getItem(params);
        if (Object.keys(data).length){
            return this.success(JSON.stringify(data.Item));
        } 
        else {return this.forbidden();}
    };
    this.getS3File = async function(bucket, key) {
        let s3Params = {
            Bucket: bucket,
            Key: key
        };
        let objectData;
        try {
            const data = await s3.getObject(s3Params).promise();
            objectData = data.Body.toString('utf-8');
        }
        catch (e) {
            console.log(e.message);
        }
        return {
            isBase64Encoded: false,
            statusCode: '200',
            headers: {
                'Content-Type': 'text/html',
                'Cache-Control': 'no-cache, no-store, must-revalidate'
            },
            body: objectData
        };
    };
    this.uploadImage = async function(bucket, key, base64) {
        let objectData = Buffer.from(base64.replace(/^data:image\/\w+;base64,/, ""),'base64');
        let s3Params = {
            Bucket: bucket,
            Key: key,
            Body: objectData,
            ContentEncoding: 'base64',
            ContentType: 'image/jpeg'
        };
        try {
            await s3.putObject(s3Params).promise();
        }
        catch (e) {
            console.log(e.message);
        }
        return `https://apoorlywrittenbot.cc/${key}`;
    };
    this.putParam = (param, value) => {
      return new Promise((res, rej) => {
        parameterStore.putParameter({
          Name: param, Value: value, Overwrite: true
        }, (err, data) => {
            if (err) {
              return rej(err);
            }
            return res(data);
        });
      });
    };
    this.updateItem = (params) => {
      return new Promise((res, rej) => {
        ddb.update(params, (err, data) => {
            if (err) {
              return rej(err);
            }
            return res(data);
        });
      });
    };
    this.validation = async function(event) {
        if (event.headers == null) {
            return this.forbidden();
        }
        if (event.headers["cf-env"] != process.env.CF_ENV || event.headers["Cookie"] == null) {
            return this.forbidden();
        }
    
        let cookie = event.headers['Cookie'];
        let index = cookie.indexOf(SIGNATURE);
    
        if (index == -1) {
            return this.forbidden();
        }
    
        let cf_signature = cookie.substring(index + SIGNATURE.length);
        let CookieHash = createHash('sha256').update(cf_signature).digest('hex');
    
        var ddbParams = {
            Key: {
                "CookieHash": CookieHash
            },
            TableName: process.env.table
        };
    
        let access_token, display_name, user_id;
        try {
            let result = await ddb.get(ddbParams).promise();
            if (result["Item"] == null) {
                access_token = null;
            }
            else {
                access_token = result["Item"]["AccessToken"];
                display_name = result["Item"]["DisplayName"];
                user_id = result["Item"]["UserID"];
            }
        } catch (e) {
            console.log(e);
            return {
                isBase64Encoded: false,
                statusCode: '500',
                body: 'Query Error'
            };
        }
    
        if (access_token == null) {
            return this.forbidden();
        }
    
        return {
            isBase64Encoded: false,
            statusCode: '200',
            body: {
                'display_name': display_name,
                'access_token': access_token,
                'user_id': user_id
            }
        };
    };
    this.jsonPost = async function(chan, display_name, body){
        let mods = require("./modList.js");
        if (mods.modList[chan].includes(display_name.toLowerCase())==false){
            return this.forbidden();
        }
        for (let [key, value] of Object.entries(body.images)){
            if (value.startsWith('https://')){
                continue;
            }
            let url = await this.uploadImage('a-poorly-written-bot', `tmp/${key}.png`, value);
            body.images[key] = url;
        }
        let params = {
          TableName : 'Mod-Interface-JSON',
          Key: {
            channel: chan
          },
          UpdateExpression: 'set #j = :x',
          ExpressionAttributeNames: {'#j' : 'json'},
          ExpressionAttributeValues: {
            ':x' : JSON.stringify(body)
            }
        };
        await this.updateItem(params);
        return body;
    };
    this.cmdPost = async function(chan, display_name, command){
        let mods = require("./modList.js");
        if (mods.modList["inabox44"].includes(display_name.toLowerCase())==false){
            return this.forbidden();
        }
        command['display_name'] = display_name;
        console.log(JSON.stringify(command));
        await this.sqs_send('https://sqs.us-west-2.amazonaws.com/414556232085/inabot-queue', JSON.stringify(command));
        return await this.sqs_receive('https://sqs.us-west-2.amazonaws.com/414556232085/inabot-API-response', display_name);
    };
    this.sqs_send = async function (url, message){
        let params = {
            QueueUrl: url,
            MessageBody: message,
          };
        await sqs.sendMessage(params).promise();
    };
    this.sqs_receive = async function (url, display_name){
        const maxRetries = 3;
        let params = {
            QueueUrl: url,
            WaitTimeSeconds: 1,
            VisibilityTimeout: 0,
        };
        for (let i=0; i<maxRetries; i++){
            let response = await sqs.receiveMessage(params).promise();
            if (response.Messages) {
                for (var m of response.Messages){
                    let msg = JSON.parse(m.Body);
                    if (msg['display_name'] == display_name){   // Check if msg if intended for the right recipient
                        try {
                            let deleteParams = {
                              QueueUrl: url,
                              ReceiptHandle: m.ReceiptHandle
                            };
                            await sqs.deleteMessage(deleteParams).promise();
                        } catch (e) {}
                        return this.success(JSON.stringify(msg['feedbacks']));
                    }
                }
            }
        }
        return this.timeout();
    };
    this.wssLambda = async function (params) {
        const lambda = new AWS.Lambda();
        return new Promise((res, rej) => {
            lambda.invoke(params, function(err, data) {
                if (err) {
                  return rej(err);
                }
                return res(data);
            });
        });
    };
    this.websocketAPI = async function(payload){
        var params = {
          FunctionName: 'wss',
          InvocationType: 'Event',
          Payload: JSON.stringify(payload),
        };
        await this.wssLambda(params);
    };
    this.federateLogin = async function (roleName, display_name){
        let params = {
            RoleArn: `arn:aws:iam::414556232085:role/${roleName}`,
            RoleSessionName: display_name
        };
        let data = await sts.assumeRole(params).promise();
        let credentialsJson = `{"sessionId":"${data.Credentials.AccessKeyId}","sessionKey":"${data.Credentials.SecretAccessKey}","sessionToken":"${data.Credentials.SessionToken}"}`;
        let federationEndpoint = `https://ca-central-1.signin.aws.amazon.com/federation?Action=getSigninToken&Session=${encodeURIComponent(credentialsJson)}`;
        let response = await axios.get(federationEndpoint);
        let signinEngpoint = `https://ca-central-1.signin.aws.amazon.com/federation?Action=login&Issuer=https%3A%2F%2Fapoorlywrittenbot.cc%2Flogin.html&Destination=https%3A%2F%2Fca-central-1.console.aws.amazon.com%2Fscheduler%2Fhome%3Fregion%3Dca-central-1%23schedules&SigninToken=${response.data.SigninToken}`;
        console.log(response);
        
        let pushover = {
            'token': process.env.PUSHOVER_APP_TOKEN,
            'user': process.env.PUSHOVER_USER_TOKEN,
            'device': 'mike-iphone',
            'title': 'AWS_CONSOLE_LOGIN',
            'message': `${display_name}`
        };
        await axios.post('https://api.pushover.net/1/messages.json', pushover);
    
    
        return {
            isBase64Encoded: false,
            statusCode: '302',
            headers: {
                "Location": signinEngpoint,
                "Cache-Control": "no-cache, no-store, must-revalidate"
            },
            body: ''
        };
    };
};