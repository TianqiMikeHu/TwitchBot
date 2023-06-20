const AWS = require('aws-sdk');
const axios = require('axios');
const { createHash } = require('crypto');
const ddb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();
const parameterStore = new AWS.SSM();

const SIGNATURE = "CloudFront-Signature=";

function forbidden() {
    return {
        isBase64Encoded: false,
        statusCode: '403',
        body: ''
    };
}

function success() {
    return {
        isBase64Encoded: false,
        statusCode: '200',
        body: JSON.stringify({})
    };
}

async function getS3File(bucket, key) {
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
}


const putParam = (param, value) => {
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

const getEmotesLambda = (params) => {
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

async function validation(event) {
    if (event.headers == null) {
        return forbidden();
    }
    if (event.headers["cf-env"] != process.env.CF_ENV || event.headers["Cookie"] == null) {
        return forbidden();
    }

    let cookie = event.headers['Cookie'];
    let index = cookie.indexOf(SIGNATURE);

    if (index == -1) {
        return forbidden();
    }

    let cf_signature = cookie.substring(index + SIGNATURE.length);

    var ddbParams = {
        Key: {
            "CookieHash": createHash('sha256').update(cf_signature).digest('hex')
        },
        TableName: process.env.table
    };

    let access_token, display_name;
    try {
        let result = await ddb.get(ddbParams).promise();
        if (result["Item"] == null) {
            access_token = null;
        }
        else {
            access_token = result["Item"]["AccessToken"];
            display_name = result["Item"]["DisplayName"];
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
        return forbidden();
    }

    let result, user_id;
    await axios.get("https://id.twitch.tv/oauth2/validate", {
        headers: {
            Authorization: 'Bearer ' + access_token
        }
    })
        .then(function (response) {
            result = true;
            user_id = response.data.user_id;
        })
        .catch(function (error) {
            result = false;
        });
    if (result) {
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
        return forbidden();
    }
}


exports.handler = async (event) => {

    console.log(event);

    let display_name, access_token, user_id;
    let validation_result = await validation(event);

    if (validation_result.statusCode != 200) {
        return validation_result;
    }
    display_name = validation_result.body.display_name;
    access_token = validation_result.body.access_token;
    user_id = validation_result.body.user_id;

    if (event.httpMethod == "GET") {
        if (event.path == "/restricted/search.html") {
            return await getS3File("a-poorly-written-bot", "restricted/search.html");
        }
        else if (event.path == "/restricted/username") {
            return {
                isBase64Encoded: false,
                statusCode: '200',
                body: JSON.stringify({ username: display_name })
            };
        }
        else if (event.path == "/restricted/emote-loader") {
            let payload = {'access_token': access_token, 'user_id': user_id};
            var params = {
              FunctionName: 'GetEmotes',
              InvocationType: 'Event',
              Payload: JSON.stringify(payload),
            };
            await getEmotesLambda(params);
            return success();
        }
        else if (event.path == "/restricted/moderator") {
            if (event.queryStringParameters == null) {
                return forbidden();
            }
            let chan = event.queryStringParameters.channel;
            if (chan == null) {
                return forbidden();
            }


            let mods = require("./modList.js");
            if (chan == "annaagtapp") {
                if (mods.modListAnnaAgtapp.includes(display_name.toLowerCase())) {
                    // Approved
                    return await getS3File("a-poorly-written-bot", "restricted/moderator-AnnaAgtapp.html");
                }
                else {
                    return forbidden();
                }
            }
            else if(chan == "mike_hu_0_0"){
                if (mods.modListMike_Hu_0_0.includes(display_name.toLowerCase())) {
                    // Approved
                    return await getS3File("a-poorly-written-bot", "restricted/moderator-Mike_Hu_0_0.html");
                }
                else {
                    return forbidden();
                }
            }
            else {
                return forbidden();
            }
        }
        else {
            return forbidden();
        }
    }
    else if (event.httpMethod == "POST") {
        let mods = require("./modList.js");
        let body = JSON.parse(event.body);
        let payload;

        if (event.path == "/restricted/mike_hu_0_0/json") {
            if (mods.modListMike_Hu_0_0.includes(display_name.toLowerCase())==false){
                return forbidden();
            }
            payload = {
                route: "sendmessage",
                action: "modaction",
                channel: "mike_hu_0_0",
                category: "json",
                coordinates: body
            };
            await putParam('JSON_MIKE_HU_0_0', event.body);
        }
        else if (event.path == "/restricted/annaagtapp/json") {
            if (mods.modListAnnaAgtapp.includes(display_name.toLowerCase())==false){
                return forbidden();
            }
            payload = {
                route: "sendmessage",
                action: "modaction",
                channel: "annaagtapp",
                category: "json",
                coordinates: body
            };
            await putParam('JSON_ANNAAGTAPP', event.body);
        }
        else {
            return forbidden();
        }
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
        if (result) {
            return success();
        }
        else {
            return forbidden();
        }
    }
    else {
        return forbidden();
    }
};
