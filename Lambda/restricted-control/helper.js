const SIGNATURE = "CloudFront-Signature=";
const AWS = require('aws-sdk');
const ddb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();
const parameterStore = new AWS.SSM();
const axios = require('axios');
const { createHash } = require('crypto');

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
    
        let access_token, refresh_token, display_name;
        try {
            let result = await ddb.get(ddbParams).promise();
            if (result["Item"] == null) {
                access_token = null;
            }
            else {
                access_token = result["Item"]["AccessToken"];
                display_name = result["Item"]["DisplayName"];
                refresh_token = result["Item"]["RefreshToken"];
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
    
        let user_id = await this.TwitchValidation(access_token, refresh_token, CookieHash);
        if (user_id) {
            return {
                isBase64Encoded: false,
                statusCode: '200',
                body: {
                    'display_name': display_name,
                    'access_token': access_token,
                    'user_id': user_id
                }
            };
        }
        else {
            return this.forbidden();
        }
    };
    this.TwitchValidation = async function(access_token, refresh_token, CookieHash){
        let user_id;
        await axios.get("https://id.twitch.tv/oauth2/validate", {
            headers: {
                Authorization: 'Bearer ' + access_token
            }
        })
            .then(function (response) {
                user_id = response.data.user_id;
            })
            .catch(function (error) {
            });
        if (user_id){
            return user_id;
        }
        // Else try token refresh
        console.log("Attempting Token Refresh");
        let result;
        await axios.post(`https://id.twitch.tv/oauth2/token?grant_type=refresh_token&refresh_token=${refresh_token}&client_id=${process.env.CLIENT_ID}&client_secret=${process.env.CLIENT_SECRET}`,
            {},
            {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            })
            .then(function (response) {
                result = true;
                access_token = response.data.access_token;
                refresh_token = response.data.refresh_token;
            })
            .catch(function (error) {
                result = false;
            });
        if (result){
            let params = {
              TableName : process.env.table,
              Key: {
                "CookieHash": CookieHash
              },
              UpdateExpression: 'set AccessToken = :a, RefreshToken = :r',
              ExpressionAttributeValues: {
                ':a' : access_token,
                ':r' : refresh_token
              }
            };
            await this.updateItem(params);
        }
        else{
            console.log("Refresh Failed");
            return user_id;
        }
        // Validate Again
        await axios.get("https://id.twitch.tv/oauth2/validate", {
            headers: {
                Authorization: 'Bearer ' + access_token
            }
        })
            .then(function (response) {
                user_id = response.data.user_id;
            })
            .catch(function (error) {
            });
        return user_id;
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
    this.websocketAPI = async function(payload){
        let result;
        await axios.post("https://qjds6buo76x3n5b52dhkthqyey0lfnxm.lambda-url.us-west-2.on.aws/",
            payload,
            {
                headers: {
                    "invoke-eventsub": process.env.INVOKE_EVENTSUB
                }
            })
            .then(function (response) {
                result = true;
            })
            .catch(function (error) {
                result = false;
            });
        return result;
    };
};