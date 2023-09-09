const AWS = require('aws-sdk');
const ssm = new AWS.SSM({ region: 'us-west-2' });
const ddb = new AWS.DynamoDB.DocumentClient();
const axios = require('axios');

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
    this.getOverlay = async function(chan) {
      if (chan == null) {return this.forbidden();}
        let params = {
          TableName : 'Mod-Interface-JSON',
          Key: {
            channel: chan
          }
        };
        const data = await this.getItem(params);
        if (Object.keys(data).length){
            return this.success(data.Item.json);
        }
        return this.forbidden();  
    };
    this.getEmote = async function(name){
        if (name == null) {
            return this.forbidden();
        }
        let params = {
          TableName : 'Emotes',
          Key: {
            emote_name: name
          }
        };
        const data = await this.getItem(params);
        if (Object.keys(data).length){
            return this.success(JSON.stringify({id: data.Item.emote_id}));
        }
        else{
            return {
                isBase64Encoded: false,
                statusCode: '404',
                body: ''
            };
        }
    };
};




