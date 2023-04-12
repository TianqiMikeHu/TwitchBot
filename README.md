# TwitchBot

(Well, the title is kinda misleading since there is some stuff for Discord...)

Last Updated on April 11th, 2023

Anyway, this is just my code for the bot I use for Twitch. Notables features are:
- Basic commands system backed by MySQL
- A quiz bowl minigame (using the database from QuizDB.org), with a points system
- Custom greetings for different viewers
- Tools that interact with Twitch API such as !getclip, !title, etc.
- !listclip command that dynamically generates an html page of a Twitch user's top 1000 clips, and uploads to an S3 bucket.
- A web scrapper that can fetch anyone's StreamElements commands. !se [streamer] [command]
- Wikipedia API
- EventSub notifications through AWS Lambda. This includes notifications for a couple channel point rewards I set up for AnnaAgtapp's stream.
- A script for speech recognition. There's a separate workflow set up for AnnaAgtapp's stream where an EC2 instance running this script automatically starts and stops upon receiving channel status updates from Twitch.
- A Twitch clips player as an OBS overlay, connected to a websockets API Gateway to dynamically play clips based on a channel point reward.
- My mobile push notification script

The Discord bot has very little features at the moment, more work to be done.
