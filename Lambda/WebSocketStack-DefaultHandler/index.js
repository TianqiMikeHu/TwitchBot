const AWS = require('aws-sdk');

exports.handler = async function (event, context) {
    return {
        statusCode: 200,
        body: "pong"
    };
};