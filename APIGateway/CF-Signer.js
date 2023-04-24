const AWS = require('aws-sdk');
const ssm = new AWS.SSM({ region: 'us-west-2' });
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
    return new Date(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours() + 2, date.getMinutes(), date.getSeconds());
}

function getExpiryTime() {
    return Math.floor(getExpirationTime().getTime() / 1000);
}

async function new_access_token() {
    let app_accesstoken = null;

    try {
        let response = await axios.post(`https://id.twitch.tv/oauth2/token?client_id=6yz6w1tnl13svb5ligch31aa5hf4ty&client_secret=${process.env.CLIENT_SECRET}&grant_type=client_credentials`);
        console.log(response.data);
        app_accesstoken = response.data.access_token;
        await ssm.putParameter({
            Name: "APP_ACCESSTOKEN",
            Value: app_accesstoken,
            Type: 'SecureString',
            Overwrite: true,
            Tier: 'Standard',
            DataType: 'text'

        }).promise();
    }
    catch (error) {
        console.log(error);
    }
    return app_accesstoken;
}

async function getDisplayName(login) {
    const { Parameter } = await ssm.getParameter({ Name: "APP_ACCESSTOKEN", WithDecryption: true }).promise();
    let header = {
        "Client-ID": "6yz6w1tnl13svb5ligch31aa5hf4ty",
        "Authorization": `Bearer ${Parameter.Value}`,
        "Content-Type": "application/json"
    };

    try {
        let response = await axios.get(`https://api.twitch.tv/helix/users?login=${login}`, {
            headers: header
        });
        console.log(response.data.data[0]["display_name"]);
        return response.data.data[0]["display_name"];
    }
    catch (error) {
        console.log(error);
    }

    let app_accesstoken = new_access_token();

    header = {
        "Client-ID": "6yz6w1tnl13svb5ligch31aa5hf4ty",
        "Authorization": `Bearer ${app_accesstoken}`,
        "Content-Type": "application/json"
    };
    try {
        let response = await axios.get(`https://api.twitch.tv/helix/users?login=${login}`, {
            headers: header
        });
        console.log(response.data.data[0]["display_name"]);
        return response.data.data[0]["display_name"];
    }
    catch (error) {
        console.log(error);
        return null;
    }
}

exports.handler = async (event, context) => {

    if (event.headers == null) {
        return {
            isBase64Encoded: false,
            statusCode: '403',
            body: ''
        };
    }
    if (event.headers["cf-env"] != process.env.CF_ENV) {
        return {
            isBase64Encoded: false,
            statusCode: '403',
            body: ''
        };
    }
    if (event.queryStringParameters["code"] == null) {
        return {
            isBase64Encoded: false,
            statusCode: '400',
            body: ''
        };
    }

    let token_request = `https://id.twitch.tv/oauth2/token?client_id=6yz6w1tnl13svb5ligch31aa5hf4ty&client_secret=${process.env.CLIENT_SECRET}&grant_type=authorization_code&code=${event.queryStringParameters["code"]}&redirect_uri=https://apoorlywrittenbot.cc`;
    let access_token, login;

    await axios.post(token_request)
        .then(function (response) {
            access_token = response.data.access_token;
        })
        .catch(function (error) {
            return {
                isBase64Encoded: false,
                statusCode: '403',
                body: ''
            };
        });
    await axios.get("https://id.twitch.tv/oauth2/validate", {
        headers: {
            Authorization: 'Bearer ' + access_token
        }
    })
        .then(function (response) {
            login = response.data.login;
        })
        .catch(function (error) {
            return {
                isBase64Encoded: false,
                statusCode: '403',
                body: ''
            };
        });


    let display_name = await getDisplayName(login);
    console.log(`display name is ${display_name}`);
    if (display_name == null) {
        display_name = login;
    }


    if (cache.publicKey == null) cache.publicKey = await loadParameter('CF-PUBLIC-KEY-ID');
    if (cache.privateKey == null) cache.privateKey = await loadParameter('CF-PRIVATE-KEY', true);

    const { publicKey, privateKey } = cache;

    const signedCookie = getSignedCookie(publicKey, privateKey);

    const ddb = new AWS.DynamoDB.DocumentClient();
    const { createHash } = require('crypto');
    try {
        await ddb
            .put({
                TableName: process.env.table,
                Item: {
                    CookieHash: createHash('sha256').update(signedCookie['CloudFront-Signature']).digest('hex'),
                    AccessToken: access_token,
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
