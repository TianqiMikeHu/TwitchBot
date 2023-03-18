require('dotenv').config();

const Discord = require('discord.js');
const client = new Discord.Client({
    intents: [
        Discord.GatewayIntentBits.DirectMessages,
        Discord.GatewayIntentBits.Guilds,
        Discord.GatewayIntentBits.GuildBans,
        Discord.GatewayIntentBits.GuildMessages,
        Discord.GatewayIntentBits.MessageContent,
    ],
    partials: [Discord.Partials.Channel],
  });

var index = 0;
var timestamp = 0;

client.once('ready', () => {
	console.log('Ready to connect to Discord');
    client.user.setActivity('Quiz Bowl');
});

client.login(process.env.DISCORD_TOKEN);

client.on('messageCreate', async message => {
	if (message.author.bot) return;

    switch (message.guild.id) {
        case '838919912168488984':  // My test server
            index = 0;
            break;
        case '927811251474677800':  // Anna
            index = 1;
            break;
        default: return;
    }

    var args = message.content.split(' ');
    var len = args.length;
    var command = args.shift().toLowerCase();
    var lower = message.content.toLowerCase();
    const user = message.author.tag;

    if (index==0 || index==1){
        if (lower.includes("wednesday") && !lower.includes("@")){
            var now = Math.floor(new Date().getTime() / 1000);
            var difference = now-timestamp;
            if (difference<180){
                console.log(`Throttled: ${difference.toString()}`);
                return;
            }
            timestamp = now;
            const regex = /Wednesday/ig;
            var response = message.content.replaceAll(regex, "hump day");
            message.reply({
                content: response,
                allowedMentions: {
                    repliedUser: false
                }
            });
        }
    }

});