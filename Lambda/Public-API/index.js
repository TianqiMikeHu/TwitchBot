require('helper.js')();

async function publicHandler(event){
    let chan;
    if (event.queryStringParameters != null) {
        chan = event.queryStringParameters.channel;
    }
    if (event.path == "/public/json"){
        return await getOverlay(chan);
    }
    else if (event.path == "/public/emote"){
        if (event.queryStringParameters == null) {
            return forbidden();
        }
        let name = event.queryStringParameters.name;
        return await getEmote(name);
    }
    else{
        return forbidden();
    }
}

exports.handler = async (event) => {
    if (event.httpMethod != "GET"){
        return forbidden();
    }
    if (event.path.startsWith("/public")){
        return await publicHandler(event);
    }
    return forbidden();
};
