const mysql = require('mysql');
const ed = require('edit-distance');
require('dotenv').config();

const Discord = require('discord.js');
const client = new Discord.Client();

const SIZE = 2;

var index = 1000;
var quiz_state = [SIZE];
quiz_state[0] = 0;  // 0: Halt
                    // 1: Awaiting answer 1
                    // 2: Answer 1 ruled incorrect
                    // 3: Awaiting answer 2
                    // 4: Answer 2 ruled incorrect
                    // 5: Awaiting answer 3
                    // 6: Answer 3 ruled incorrect
var parts = [];
for(var i = 0; i < SIZE; i++){
    parts[i] = [];
    for(var j = 0; j < 4; j++){
        parts[i][j] = '';
    }
}

var answers = [];
for(var i = 0; i < SIZE; i++){
    answers[i] = [];
    for(var j = 0; j < 3; j++){
        answers[i][j] = '';
    }
}
var player = [SIZE];
for(var i=0; i<SIZE; i++){
    player[i] = '';
}
var score = [SIZE];
for(var i=0; i<SIZE; i++){
    score[i] = 0;
}

var insert, remove, update;
insert = remove = function(node) { return 1; };
update = function(stringA, stringB) { return stringA !== stringB ? 1 : 0; };

var con = mysql.createConnection({
  host: 'localhost',
  user: 'root',
  password: 'password',
  database: 'quizdb'
});

con.connect(function(err) {
  if (err){
      console.log(err);
      return;
  }
  console.log("Connected to MySQL!");
});

client.once('ready', () => {
	console.log('Ready to connect to Discord');
    client.user.setActivity('Quiz Bowl');
});

client.login(process.env.DISCORD_TOKEN);


client.on('message', message => {
	if (message.author.bot) return;

    switch (message.guild.name) {
        case 'Mike Hu\'s test server':
            index = 0;
            break;
        case 'EBHB1210':
            index = 1;
            break;
        default:;
    }

    var args = message.content.split(' ');
    var len = args.length;
    var command = args.shift().toLowerCase();
    const user = message.author.username;

    con.query('SELECT * FROM bot.chatters WHERE username = ?', user, (err,rows) => {
        if(err) throw err;

        if(rows.length == 0){
            con.query('INSERT INTO bot.chatters(username, points) VALUES(?, 0)', user, (err,rows1) => {
                if(err) throw err;
                console.log("Inserted a record");
            });
        }
    });

    if(command === '!points'){
        if(!message.mentions.users.size){
            if(len>1){
                var target = message.content.trim().slice(8).trim();
                con.query('SELECT * FROM bot.chatters WHERE username = ?', target, (err,rows) => {
                    if(err) throw err;
                    if(rows.length == 0){
                        message.channel.send(`User ${target} not found.`);
                    }
                    else{
                        message.channel.send(`User ${target} has ${rows[0].points} points`);
                    }
                });
            }
            else{
                con.query('SELECT * FROM bot.chatters WHERE username = ?', user, (err,rows) => {
                    if(err) throw err;
                    message.channel.send(`You have ${rows[0].points} points`);
                });
            }
            return;
        }
        const taggedUser = message.mentions.users.first().username;
        con.query('SELECT * FROM bot.chatters WHERE username = ?', taggedUser, (err,rows) => {
            if(err) throw err;
            if(rows.length == 0){
                message.channel.send(`User ${taggedUser} not found.`);
            }
            else{
                message.channel.send(`User ${taggedUser} has ${rows[0].points} points`);
            }
        });
        return;
    }

    if(command === '!quiz'){
        if(quiz_state[index] != 0){
            message.channel.send(`A quiz is currently running.`);
            return;
        }
        if(len<3){
            message.channel.send(`Incorrect number of arguments.`);
            return;
        }
        var category = args[0].toLowerCase();
        var catNum = 0;
        var difficulty = parseInt(args[1]);
        if(isNaN(difficulty)){
            message.channel.send(`Invalid difficulty.`);
            return;
        }
        if(category == "random"){
            var query = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from (bonus join (select * from tournaments where difficulty = ?) as b on bonus.tournament_id=b.id) order by rand() limit 1) as a on bonus_parts.bonus_id=a.id';
            con.query(query, difficulty, (err,rows) => {
                if(err) throw err;
                if(rows.length<3){
                    message.channel.send(`Sorry, something went wrong. Try again.`);
                    return;
                }
                parts[index][0] = rows[0].leadin;
                parts[index][1] = rows[0].text;
                parts[index][2] = rows[1].text;
                parts[index][3] = rows[2].text;
                answers[index][0] = rows[0].answer;
                answers[index][1] = rows[1].answer;
                answers[index][2] = rows[2].answer;
                message.channel.send(`${parts[index][0]}`);
                message.channel.send(`${parts[index][1]}`);
                quiz_state[index] = 1;
                player[index] = user;
            });
            return;
        }
        switch (category) {
          case 'mythology':
              catNum = 14;
              break;
          case 'literature':
              catNum = 15;
              break;
          case 'trash':
              catNum = 16;
              break;
          case 'science':
              catNum = 17;
              break;
          case 'history':
              catNum = 18;
              break;
          case 'religion':
              catNum = 19;
              break;
          case 'geography':
              catNum = 20;
              break;
          case 'fine_arts':
              catNum = 21;
              break;
          case 'social_science':
              catNum = 22;
              break;
          case 'philosophy':
              catNum = 25;
              break;
          case 'current_events':
              catNum = 26;
              break;
          default:
              message.channel.send(`Invalid category.`);
              return;
        }
        var query = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from (bonus join (select * from tournaments where difficulty = ?) as b on bonus.tournament_id=b.id) where category_id = ? order by rand() limit 1) as a on bonus_parts.bonus_id=a.id';
        con.query(query, [difficulty, catNum], (err,rows) => {
            if(err) throw err;
            if(rows.length<3){
                message.channel.send(`Sorry, something went wrong. Try again.`);
                return;
            }
            parts[index][0] = rows[0].leadin;
            parts[index][1] = rows[0].text;
            parts[index][2] = rows[1].text;
            parts[index][3] = rows[2].text;
            answers[index][0] = rows[0].answer;
            answers[index][1] = rows[1].answer;
            answers[index][2] = rows[2].answer;
            message.channel.send(`${parts[index][0]}`);
            message.channel.send(`>>> ${parts[index][1]}`);
            quiz_state[index] = 1;
            player[index] = user;
        });
        return;
    }

    if(message.content[0] == '-' && player[index] == user){
        switch (quiz_state[index]) {
          case 1:
              var correct;
              if(message.content.length<2){
                  correct = false;
              }
              else{
                  var input = message.content.slice(1).toLowerCase().replace(/\s/g, "");
                  var answer = answers[index][0].toLowerCase();
                  correct = grader(input, answer);
              }
              if(correct){
                  message.channel.send(`:white_check_mark: CORRECT! The answerline is:`);
                  message.channel.send(`**${answers[index][0]}**`);
                  message.channel.send(`Part 2:`);
                  message.channel.send(`>>> ${parts[index][2]}`);
                  score[index] += 10;
                  quiz_state[index] = 3;
              }
              else{
                  message.channel.send(`:x: Incorrect. The answerline is:`);
                  message.channel.send(`**${answers[index][0]}**`);
                  message.channel.send(`Were you correct? [y/n]`);
                  quiz_state[index] = 2;
              }
              break;
          case 3:
              var correct;
              if(message.content.length<2){
                  correct = false;
              }
              else{
                  var input = message.content.slice(1).toLowerCase().replace(/\s/g, "");
                  var answer = answers[index][1].toLowerCase();
                  correct = grader(input, answer);
              }
              if(correct){
                  message.channel.send(`:white_check_mark: CORRECT! The answerline is:`);
                  message.channel.send(`**${answers[index][1]}**`);
                  message.channel.send(`Part 3:`);
                  message.channel.send(`>>> ${parts[index][3]}`);
                  score[index] += 10;
                  quiz_state[index] = 5;
              }
              else{
                  message.channel.send(`:x: Incorrect. The answerline is:`);
                  message.channel.send(`**${answers[index][1]}**`);
                  message.channel.send(`Were you correct? [y/n]`);
                  quiz_state[index] = 4;
              }
              break;
          case 5:
              var correct;
              if(message.content.length<2){
                  correct = false;
              }
              else{
                  var input = message.content.slice(1).toLowerCase().replace(/\s/g, "");
                  var answer = answers[index][2].toLowerCase();
                  correct = grader(input, answer);
              }
              if(correct){
                  message.channel.send(`:white_check_mark: CORRECT! The answerline is:`);
                  message.channel.send(`**${answers[index][2]}**`);
                  score[index] += 10;
                  message.channel.send(`__You have scored ${score[index]} \/ 30 points.__`);
                  con.query('UPDATE bot.chatters SET points = points+? WHERE username = ?', [score[index], user], (err,rows2) => {
                      if(err) throw err;
                  });
                  score[index] = 0;
                  player[index] = '';
                  quiz_state[index] = 0;
              }
              else{
                  message.channel.send(`:x: Incorrect. The answerline is:`);
                  message.channel.send(`**${answers[index][2]}**`);
                  message.channel.send(`Were you correct? [y/n]`);
                  quiz_state[index] = 6;
              }
              break;
            default:;
        }
        return;
    }

    if((message.content[0] == 'y' || message.content[0] == 'n') && player[index] == user){
        switch (quiz_state[index]) {
            case 2:
                if(message.content[0] == 'y'){
                    score[index] += 10;
                    message.channel.send(`Points awarded. Part 2:`);
                }
                else{
                    message.channel.send(`Part 2:`);
                }
                message.channel.send(`>>> ${parts[index][2]}`);
                quiz_state[index] = 3;
                break;
          case 4:
              if(message.content[0] == 'y'){
                  score[index] += 10;
                  message.channel.send(`Points awarded. Part 3:`);
              }
              else{
                  message.channel.send(`Part 3:`);
              }
              message.channel.send(`>>> ${parts[index][3]}`);
              quiz_state[index] = 5;
              break;
          case 6:
              if(message.content[0] == 'y'){
                  score[index] += 10;
                  message.channel.send(`__Points awarded. You have scored ${score[index]} \/ 30 points.__`);
              }
              else{
                  message.channel.send(`__You have scored ${score[index]} \/ 30 points.__`);
              }
              con.query('UPDATE bot.chatters SET points = points+? WHERE username = ?', [score[index], user], (err,rows2) => {
                  if(err) throw err;
              });
              score[index] = 0;
              player[index] = '';
              quiz_state[index] = 0;
              break;
            default:;
        }
        return;
    }
});


function grader(input, answer){
    var args = answer.split(" ");
    noWhiteSpace = answer.replace(/\s/g, "");
    if(input.length>1 && noWhiteSpace.includes(input)){
        return true;
    }
    var lev;
    for(const arg of args){
        lev = ed.levenshtein(input, arg, insert, remove, update);
        if(lev.distance<3){
            return true;
        }
    }
    lev = ed.levenshtein(input, noWhiteSpace, insert, remove, update);
    if(lev.distance<5){
        return true;
    }
    return false;

}
