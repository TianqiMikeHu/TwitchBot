# TwitchBot

Last Updated on April 10th, 2024

This is a collection of everything relevant to the Twitch bots I have. Important things include:

My own chatbot (bot.py and other files referenced from that file):
- Basic commands system backed by MySQL
- A quiz bowl minigame (using the database from QuizDB.org), with a points system
- Custom greetings for different viewers
- Tools that interact with Twitch API such as !getclip, !title, etc.
- !listclip command that dynamically generates an html page of a Twitch user's top 1000 clips, and uploads to an S3 bucket.
- A web scrapper that can fetch anyone's StreamElements commands. !se [streamer] [command]
- Wikipedia API
- EventSub notifications through AWS Lambda. This includes notifications I have set up for a few other channels.
- A Twitch clips player as an OBS overlay, connected to a websockets API Gateway to dynamically play clips based on a channel point reward.
- My mobile push notification script

The chatbot for inabox44 (inabot). This is everything in the /inabot folder.
- Mostly a clone of what StreamElements can do.
- To ensure high availability (compared to my personal bot), this is being run on an EC2 isntance 24/7. Backed by DynamoDB instead of a local relational database.
- Easy to introduce new commands with very customized logic. New custom commands can take effect with 0 down time.
 
Web UI for inabot (Pretty much all the JS files here and the /restricted folder)
- Allows overlay manipulation (timers, images, etc.)
- Allows command management outside of Twitch chat
- Authentication done through Twitch (i.e. Users log in via Twitch credentials)

The /Lambda folder has copies of important Lambda functions I have that server as critical components of the web UI backend.
