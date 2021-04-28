const tmi = require('tmi.js');

require('dotenv').config();

// Define configuration options
const opts = {
  identity: {
    username: 'a_poorly_written_bot',
    password: process.env.TWITCH_OAUTH_TOKEN
  },
  channels: [
    'mike_hu_0_0'
  ]
};

const me = 'mike_hu_0_0';
var eb = false;

// Create a client with our options
const client = new tmi.client(opts);

// Register our event handlers (defined below)
client.on('message', onMessageHandler);
client.on('connected', onConnectedHandler);

// Connect to Twitch:
client.connect();

// Called every time a message comes in
function onMessageHandler (channel, context, message, self) {
  if (self) { return; } // Ignore messages from the bot

  var args = message.split(' ');
  var len = args.length;
  var command = args.shift().toLowerCase();
  const user = context.username;
  var temp = '';


  if(!eb &&  user === 'ebhb1210'){
      client.say(channel, 'BOVRIL');
      eb = true;
  }

  if (command === 'hello') {
      client.say(channel, `Hey, ${user}! VoHiYo`);
      return;
  }
  else if(command === '!rules'){
      client.say(channel, `I can only use melee attacks, bricks and bottles. Exceptions include Rat King and all scripted weapon usage.`);
      return;
  }
  else if(command === '!lastdeath'){
      client.say(channel, `This is also PB. \n https://www.twitch.tv/mike_hu_0_0/clip/SarcasticResilientTurtleMau5-JVoqTGBOTey3tUmq`);
      return;
  }
  if(message.includes('Wanna become famous?') && len>=7){
      client.say(channel, `/ban ${user}`);
      client.say(channel, `BOP BOP BOP`);
      return;
  }
  if(message.substring(0, 4).toLowerCase() === "nooo" || message.includes('D:')){
      client.say(channel, `D:`);
      return;
  }
}


// Called every time the bot connects to Twitch chat
function onConnectedHandler (addr, port) {
  console.log(`* Connected to ${addr}:${port}`);
}
