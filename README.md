# TwitchBot

(Well, the title is kinda misleading since there is a file for Discord...)

Anyway, this is just my code for the chat bot I use for Twitch. Notables features are:
- Replies to basic commands
- A quiz bowl minigame (using the database from QuizDB.org), with a points system
- A joke feature where it can repeat a user's message but replace every adjective with a preset adjective, a verb with another verb, etc.
- Custom greetings for different viewers
- Tools that interact with Twitch API such as !getclip, !title, etc.
- A web scrapper that can fetch anyone's StreamElements commands. !se [streamer] [command]
- Wikipedia API
- EventSub notifications through an endpoint at Google Cloud

It also accepts any generic SQL queries, although only myself and a trusted mod are authorized to do that.
