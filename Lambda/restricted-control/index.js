require('helper.js')();


exports.handler = async (event) => {
    console.log(event);

    let display_name, access_token, user_id, chan;
    let validation_result = await validation(event);
    if (validation_result.statusCode != 200) {return validation_result;}
    
    display_name = validation_result.body.display_name;
    access_token = validation_result.body.access_token;
    user_id = validation_result.body.user_id;
    
    if (event.queryStringParameters != null) {
        chan = event.queryStringParameters.channel;
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
            if (chan == "annaagtapp" || chan == "mike_hu_0_0") {
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
        else {
            return forbidden();
        }
        let payload = {
            route: "sendmessage",
            action: "modaction",
            channel: chan,
            category: "json",
            coordinates: body
        };
        let result = await websocketAPI(payload);
        if (result) {
            console.log(body);
            console.log(JSON.stringify({'images': body.images}));
            return success(JSON.stringify({'images': body.images}));
        }
        else {
            return forbidden();
        }
    }
    else {
        return forbidden();
    }
};
