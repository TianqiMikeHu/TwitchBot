const AWS = require('aws-sdk');
const ssm = new AWS.SSM({ region: 'us-west-2' });
const ddb = new AWS.DynamoDB.DocumentClient();
const axios = require('axios');

const cache = {};

const loadParameter = async (key, WithDecryption = false) => {
    const { Parameter } = await ssm.getParameter({ Name: key, WithDecryption: WithDecryption }).promise();
    return Parameter.Value;
};

const policyString = JSON.stringify({
    'Statement': [{
        'Resource': `https://apoorlywrittenbot.cc/restricted/*`,
        'Condition': {
            'DateLessThan': { 'AWS:EpochTime': getExpiryTime() }
        }
    }]
});

function getSignedCookie(publicKey, privateKey) {
    const cloudFront = new AWS.CloudFront.Signer(publicKey, privateKey);
    const options = { policy: policyString };
    return cloudFront.getSignedCookie(options);
}

function getExpirationTime() {
    const date = new Date();
    return new Date(date.getFullYear(), date.getMonth(), date.getDate()+14, date.getHours(), date.getMinutes(), date.getSeconds());
}

function getExpiryTime() {
    return Math.floor(getExpirationTime().getTime() / 1000);
}

async function getDisplayName(login) {
    let access_token;
    try {
        let result = await ddb
            .get({
                TableName: 'CF-Cookies',
                Key: {
                    CookieHash: '160025583'
                }
            })
            .promise();
        access_token = result["Item"]["AccessToken"];
    } catch (err) {
        return null;
    }
    
    let header = {
        "Client-ID": "6yz6w1tnl13svb5ligch31aa5hf4ty",
        "Authorization": `Bearer ${access_token}`,
        "Content-Type": "application/json"
    };

    try {
        let response = await axios.get(`https://api.twitch.tv/helix/users?login=${login}`, {
            headers: header
        });
        return response.data.data[0]["display_name"];
    }
    catch (error) {
        console.log(error);
        return null;
    }
}

function getEmotesLambda (params) {
    const lambda = new AWS.Lambda();
    return new Promise((res, rej) => {
        lambda.invoke(params, function(err, data) {
            if (err) {
              return rej(err);
            }
            return res(data);
        });
    });
}

function forbidden() {
    return {
        isBase64Encoded: false,
        statusCode: '403',
        body: ''
    };
}

exports.handler = async (event, context) => {
    if (event.httpMethod != "GET"){
        return forbidden();
    }
    if (event.headers == null) {
        return forbidden();
    }
    if (event.headers["cf-env"] != process.env.CF_ENV) {
        return forbidden();
    }
    if (event.queryStringParameters["code"] == null) {
        return forbidden();
    }

    let token_request = `https://id.twitch.tv/oauth2/token?client_id=6yz6w1tnl13svb5ligch31aa5hf4ty&client_secret=${process.env.CLIENT_SECRET}&grant_type=authorization_code&code=${event.queryStringParameters["code"]}&redirect_uri=https://apoorlywrittenbot.cc`;
    let access_token, refresh_token, login, user_id;

    await axios.post(token_request)
        .then(function (response) {
            access_token = response.data.access_token;
            refresh_token = response.data.refresh_token;
        })
        .catch(function (error) {
            return forbidden();
        });
    await axios.get("https://id.twitch.tv/oauth2/validate", {
        headers: {
            Authorization: 'Bearer ' + access_token
        }
    })
        .then(function (response) {
            login = response.data.login;
            user_id = response.data.user_id;
        })
        .catch(function (error) {
            return forbidden();
        });


    let display_name = await getDisplayName(login);
    console.log(`display name is ${display_name}`);
    if (display_name == null) {
        display_name = login;
    }

    let pushover = {
        'token': process.env.PUSHOVER_APP_TOKEN,
        'user': process.env.PUSHOVER_USER_TOKEN,
        'device': 'mike-iphone',
        'title': 'LOGIN',
        'message': `${display_name}`
    };
    await axios.post('https://api.pushover.net/1/messages.json', pushover);

    if (cache.publicKey == null) cache.publicKey = await loadParameter('CF-PUBLIC-KEY-ID');
    if (cache.privateKey == null) cache.privateKey = await loadParameter('CF-PRIVATE-KEY', true);

    const { publicKey, privateKey } = cache;

    const signedCookie = getSignedCookie(publicKey, privateKey);

    const { createHash } = require('crypto');
    try {
        await ddb
            .put({
                TableName: process.env.table,
                Item: {
                    CookieHash: createHash('sha256').update(signedCookie['CloudFront-Signature']).digest('hex'),
                    AccessToken: access_token,
                    RefreshToken: refresh_token,
                    TTL: getExpiryTime(),
                    DisplayName: display_name
                },
            })
            .promise();
    } catch (err) {
        return {
            statusCode: 500,
        };
    }
    
    let payload = {'access_token': access_token, 'user_id': user_id};
    var params = {
      FunctionName: 'GetEmotes',
      InvocationType: 'Event',
      Payload: JSON.stringify(payload),
    };
    await getEmotesLambda(params);

    return {
        isBase64Encoded: false,
        statusCode: '302',
        headers: {
            "Location": "https://apoorlywrittenbot.cc/restricted/search.html",
            "Cache-Control": "no-cache, no-store, must-revalidate"
        },
        multiValueHeaders: {
            "Set-Cookie": [
                `CloudFront-Policy=${signedCookie['CloudFront-Policy']};Domain=apoorlywrittenbot.cc;Path=/;Expires=${getExpirationTime().toUTCString()};Secure;HttpOnly;SameSite=Lax`,
                `CloudFront-Key-Pair-Id=${signedCookie['CloudFront-Key-Pair-Id']};Domain=apoorlywrittenbot.cc;Path=/;Expires=${getExpirationTime().toUTCString()};Secure;HttpOnly;SameSite=Lax`,
                `CloudFront-Signature=${signedCookie['CloudFront-Signature']};Domain=apoorlywrittenbot.cc;Path=/;Expires=${getExpirationTime().toUTCString()};Secure;HttpOnly;SameSite=Lax`
            ]
        },
        body: ''
    };
};
