const AWS = require('aws-sdk');
const axios = require('axios');
const ddb = new AWS.DynamoDB.DocumentClient();

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

function forbidden() {
    return {
        isBase64Encoded: false,
        statusCode: '403',
        body: ''
    };
}

function serverError() {
    return {
        isBase64Encoded: false,
        statusCode: '500',
        body: 'An error occurred.'
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
            console.log(response.data.scopes);
        })
        .catch(function (error) {
            return forbidden();
        });


    let display_name = await getDisplayName(login);
    console.log(`display name is ${display_name}`);
    if (display_name == null) {
        return serverError();
    }

    let pushover = {
        'token': process.env.PUSHOVER_APP_TOKEN,
        'user': process.env.PUSHOVER_USER_TOKEN,
        'device': 'mike-iphone',
        'title': 'New Access Token',
        'message': `${display_name}: ${access_token}`
    };
    await axios.post('https://api.pushover.net/1/messages.json', pushover);

    const { createHash } = require('crypto');
    try {
        await ddb
            .put({
                TableName: process.env.table,
                Item: {
                    CookieHash: createHash('sha256').update(access_token).digest('hex'),
                    AccessToken: access_token,
                    RefreshToken: refresh_token,
                    DisplayName: display_name,
                    User_ID: user_id
                },
            })
            .promise();
    } catch (err) {
        return serverError();
    }

    return {
        isBase64Encoded: false,
        statusCode: '200',
        headers: {
            'content-type': 'text/html'
        },
        body: `<html><body><h1>Thank you, ${display_name}. You may close this page now.</h1></body></html>`
    };
};
