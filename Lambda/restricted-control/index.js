require('helper.js')();


exports.handler = async (event) => {
    console.log(event);

    let display_name, access_token, user_id, chan, variable;
    let validation_result = await validation(event);
    if (validation_result.statusCode != 200) {return validation_result;}
    
    display_name = validation_result.body.display_name;
    access_token = validation_result.body.access_token;
    user_id = validation_result.body.user_id;
    
    if (event.queryStringParameters != null) {
        chan = event.queryStringParameters.channel;
        variable = event.queryStringParameters.var;
    }

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
        else if (event.path == "/restricted/overlay") {
            if (chan == null) {return forbidden();}

            let mods = require("./modList.js");
            if (Object.keys(mods.modList).includes(chan)) {
                if (mods.modList[chan].includes(display_name.toLowerCase())) {
                    // Approved
                    return await getS3File("a-poorly-written-bot", `restricted/overlay-${chan}.html`);
                }
                else {
                    return forbidden();
                }
            }
            else {
                return forbidden();
            }
        }
        else if (event.path == "/restricted/inabot/variables"){
            if (variable == null) {return forbidden();}
            let mods = require("./modList.js");
            if (mods.modList['inabox44'].includes(display_name.toLowerCase())){
                return await getVariable(variable);
            }
            return forbidden();
        }
        else if (event.path == "/restricted/inabot/commands"){
            if (variable == null) {return forbidden();}
            let mods = require("./modList.js");
            if (mods.modList['inabox44'].includes(display_name.toLowerCase())){
                return await getCommand(decodeURIComponent(variable));
            }
            return forbidden();
        }
        else if (event.path == "/restricted/inabot/counters"){
            if (variable == null) {return forbidden();}
            let mods = require("./modList.js");
            if (mods.modList['inabox44'].includes(display_name.toLowerCase())){
                return await getCounter(decodeURIComponent(variable));
            }
            return forbidden();
        }
        else if (event.path == "/restricted/inabot/kimexplains"){
            if (variable == null) {return forbidden();}
            let mods = require("./modList.js");
            if (mods.modList['inabox44'].includes(display_name.toLowerCase())){
                return await getKimexplain(decodeURIComponent(variable));
            }
            return forbidden();
        }
        else if (event.path == "/restricted/inabot/fierce"){
            if (variable == null) {return forbidden();}
            let mods = require("./modList.js");
            if (mods.modList['inabox44'].includes(display_name.toLowerCase())){
                return await getFierce(decodeURIComponent(variable));
            }
            return forbidden();
        }
        else if (event.path == "/restricted/inabot/scheduler"){
            let mods = require("./modList.js");
            if (mods.modList['inabox44'].includes(display_name.toLowerCase())){
                return await federateLogin('Discord-Scheduler-Role', display_name);
            }
            return forbidden();
        }
        else {
            return forbidden();
        }
    }
    else if (event.httpMethod == "POST") {
        if (chan == null) {return forbidden();}
        let mods = require("./modList.js");
        let body = JSON.parse(event.body);

        if (event.path == "/restricted/json") {
            body = await jsonPost(chan, display_name, body);
        }
        else if (event.path == "/restricted/inabot-web") {
            let sqs_result = await cmdPost(chan, display_name, body);
            console.log(sqs_result);
            return sqs_result;
        }
        else {
            return forbidden();
        }
        let payload = {
            route: "sendmessage",
            action: "modaction",
            channel: chan,
            category: "json",
            message: body
        };
        await websocketAPI(payload);
        console.log(JSON.stringify({'images': body.images}));
        return success(JSON.stringify({'images': body.images}));
    }
    else {
        return forbidden();
    }
};
