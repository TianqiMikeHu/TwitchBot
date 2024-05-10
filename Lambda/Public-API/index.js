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
    else if (event.path == "/public/reset-cookie"){
        return {
            isBase64Encoded: false,
            statusCode: '200',
            headers: {
                "Cache-Control": "no-cache, no-store, must-revalidate"
            },
            multiValueHeaders: {
                "Set-Cookie": [
                    `CloudFront-Policy=a;Domain=apoorlywrittenbot.cc;Path=/;Expires=Thu, 01 Jan 1970 00:00:01 GMT`,
                    `CloudFront-Key-Pair-Id=b;Domain=apoorlywrittenbot.cc;Path=/;Expires=Thu, 01 Jan 1970 00:00:01 GMT`,
                    `CloudFront-Signature=c;Domain=apoorlywrittenbot.cc;Path=/;Expires=Thu, 01 Jan 1970 00:00:01 GMT`
                ]
            },
            body: ''
        };
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
