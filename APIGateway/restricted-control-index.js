const AWS = require('aws-sdk');
const axios = require('axios');
const { createHash } = require('crypto');
const ddb = new AWS.DynamoDB.DocumentClient();
const s3 = new AWS.S3();

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

    let result;
    await axios.get("https://id.twitch.tv/oauth2/validate", {
        headers: {
            Authorization: 'Bearer ' + access_token
        }
    })
        .then(function (response) {
            result = true;
        })
        .catch(function (error) {
            result = false;
        });
    if (result) {
        return {
            isBase64Encoded: false,
            statusCode: '200',
            body: display_name
        };
    }
    else {
        return forbidden();
    }
}


exports.handler = async (event) => {

    console.log(event);

    let display_name;
    let validation_result = await validation(event);

    if (validation_result.statusCode != 200) {
        return validation_result;
    }
    display_name = validation_result.body;

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
            else {
                return forbidden();
            }
        }
        else {
            return forbidden();
        }
    }
    else if (event.httpMethod == "POST") {
        let body = JSON.parse(event.body);
        let payload;
        if (event.path == "/restricted/annaagtapp/text") {
            payload = {
                route: "sendmessage",
                action: "modaction",
                channel: "annaagtapp",
                category: "text",
                content: body.content,
                color: body.color,
                size: body.size
            };
        }
        else if (event.path == "/restricted/annaagtapp/timer") {
            payload = {
                route: "sendmessage",
                action: "modaction",
                channel: "annaagtapp",
                category: "timer",
                content: body.content,
                duration: body.duration,
                color: body.color,
                size: body.size
            };
        }
        else if (event.path == "/restricted/annaagtapp/clearall") {
            payload = {
                route: "sendmessage",
                action: "modaction",
                channel: "annaagtapp",
                category: "clearAll",
            };
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
