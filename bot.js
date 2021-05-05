const tmi = require('tmi.js');
const mysql = require('mysql');
const ed = require('edit-distance');
require('dotenv').config();


// Define configuration options
const opts = {
  identity: {
    username: 'a_poorly_written_bot',
    password: process.env.TWITCH_OAUTH_TOKEN,
  },
  channels: [
    'mike_hu_0_0'
  ]
};

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

const me = 'mike_hu_0_0';
var quiz_state = 0; // 0: Halt
                    // 1: Awaiting answer 1
                    // 2: Answer 1 ruled incorrect
                    // 3: Awaiting answer 2
                    // 4: Answer 2 ruled incorrect
                    // 5: Awaiting answer 3
                    // 6: Answer 3 ruled incorrect
var parts = [4];
var answers = [3];
var player = '';
var score = 0;

var insert, remove, update;
insert = remove = function(node) { return 1; };
update = function(stringA, stringB) { return stringA !== stringB ? 1 : 0; };

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


  if(!eb &&  user === 'ebhb1210'){
      client.say(channel, 'BOVRIL');
      eb = true;
  }
  if(message.includes('Wanna become famous?')){
      client.say(channel, `\/ban ${user}`);
      client.say(channel, `BOP BOP BOP`);
      return;
  }

  con.query('SELECT * FROM bot.viewers WHERE username = ?', user, (err,rows) => {
      if(err) throw err;

      if(rows.length == 0){
          con.query('INSERT INTO bot.viewers(username, messages, points) VALUES(?, 1, 0)', user, (err,rows1) => {
              if(err) throw err;
              console.log("Inserted a record");
          });
      }
      else{
          con.query('UPDATE bot.viewers SET messages = messages+1 WHERE username = ?', user, (err,rows2) => {
              if(err) throw err;
          });
      }
  });

  if(message.includes('nooo')  || message.includes('D:')){
      client.say(channel, `D:`);
      return;
  }

  if(command === '!sql'){
     if(user === me){
         var query = message.slice(5).toLowerCase();
         con.query(query, (err,rows) => {
             if(err){
                 client.say(channel, `An error occured.`);
                 console.log(err);
             }
             else{
                 client.say(channel, `Executed query.`);
                 var str = '';
                 for(const row of rows){
                     str = JSON.stringify(row);
                     client.say(channel, `${str}`);
                 }
             }
         });
     }
     else{
         client.say(channel, `You are not authorized to do this.`);
     }
     return;
  }

  if(command === '!messagecount'){
      if(len>1){
          var target = args[0].toLowerCase();
          if(target[0] === '@'){
              target = target.slice(1);
          }
          con.query('SELECT * FROM bot.viewers WHERE username = ?', target, (err,rows) => {
              if(err) throw err;
              if(rows.length == 0){
                  client.say(channel, `User ${target} not found.`);
              }
              else{
                  client.say(channel, `User ${target} has ${rows[0].messages} messages`);
              }
          });
      }
      else{
          con.query('SELECT * FROM bot.viewers WHERE username = ?', user, (err,rows) => {
              if(err) throw err;
              client.say(channel, `You have ${rows[0].messages} messages`);
          });
      }
      return;
  }

  if(command === '!points'){
      if(len>1){
          var target = args[0].toLowerCase();
          if(target[0] === '@'){
              target = target.slice(1);
          }
          con.query('SELECT * FROM bot.viewers WHERE username = ?', target, (err,rows) => {
              if(err) throw err;
              if(rows.length == 0){
                  client.say(channel, `User ${target} not found.`);
              }
              else{
                  client.say(channel, `User ${target} has ${rows[0].points} points`);
              }
          });
      }
      else{
          con.query('SELECT * FROM bot.viewers WHERE username = ?', user, (err,rows) => {
              if(err) throw err;
              client.say(channel, `You have ${rows[0].points} points`);
          });
      }
      return;
  }

  if(command === '!end' && user === me){
      quiz_state = 0;
      player = '';
      score = 0;
      client.say(channel, `Current bonus question ended.`);
      return;
  }


  if(command === '!quiz'){
      if(quiz_state != 0){
          client.say(channel, `A quiz is currently running.`);
          return;
      }
      if(len<3){
          client.say(channel, `Incorrect number of arguments.`);
          return;
      }
      var category = args[0].toLowerCase();
      var catNum = 0;
      var difficulty = parseInt(args[1]);
      if(isNaN(difficulty)){
          client.say(channel, `Invalid difficulty.`);
          return;
      }
      if(category == "random"){
          var query = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from (bonus join (select * from tournaments where difficulty = ?) as b on bonus.tournament_id=b.id) order by rand() limit 1) as a on bonus_parts.bonus_id=a.id';
          con.query(query, difficulty, (err,rows) => {
              if(err) throw err;
              if(rows.length<3){
                  client.say(channel, `Sorry, something went wrong. Try again.`);
                  return;
              }
              parts[0] = rows[0].leadin;
              parts[1] = rows[0].text;
              parts[2] = rows[1].text;
              parts[3] = rows[2].text;
              answers[0] = rows[0].answer;
              answers[1] = rows[1].answer;
              answers[2] = rows[2].answer;
              client.say(channel, `${parts[0]}`);
              client.say(channel, `${parts[1]}`);
              quiz_state = 1;
              player = user;
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
            client.say(channel, `Invalid category.`);
            return;
      }
      var query = 'select leadin, text, answer from bonus_parts join (select bonus.id, leadin from (bonus join (select * from tournaments where difficulty = ?) as b on bonus.tournament_id=b.id) where category_id = ? order by rand() limit 1) as a on bonus_parts.bonus_id=a.id';
      con.query(query, [difficulty, catNum], (err,rows) => {
          if(err) throw err;
          if(rows.length<3){
              client.say(channel, `Sorry, something went wrong. Try again.`);
              return;
          }
          parts[0] = rows[0].leadin;
          parts[1] = rows[0].text;
          parts[2] = rows[1].text;
          parts[3] = rows[2].text;
          answers[0] = rows[0].answer;
          answers[1] = rows[1].answer;
          answers[2] = rows[2].answer;
          client.say(channel, `${parts[0]}`);
          client.say(channel, `${parts[1]}`);
          quiz_state = 1;
          player = user;
      });
      return;
  }

  if(message[0] == '-' && player == user){
      switch (quiz_state) {
        case 1:
            var correct;
            if(message.length<2){
                correct = false;
            }
            else{
                var input = message.slice(1).toLowerCase().replace(/\s/g, "");
                var answer = answers[0].toLowerCase();
                correct = grader(input, answer);
            }
            if(correct){
                client.say(channel, `VoteYea CORRECT! The answerline is:`);
                client.say(channel, `${answers[0]}`);
                client.say(channel, `Part 2:`);
                client.say(channel, `${parts[2]}`);
                score += 10;
                quiz_state = 3;
            }
            else{
                client.say(channel, `VoteNay Incorrect. The answerline is:`);
                client.say(channel, `${answers[0]}`);
                client.say(channel, `Were you correct? [y/n]`);
                quiz_state = 2;
            }
            break;
        case 3:
            var correct;
            if(message.length<2){
                correct = false;
            }
            else{
                var input = message.slice(1).toLowerCase().replace(/\s/g, "");
                var answer = answers[1].toLowerCase();
                correct = grader(input, answer);
            }
            if(correct){
                client.say(channel, `VoteYea CORRECT! The answerline is:`);
                client.say(channel, `${answers[1]}`);
                client.say(channel, `Part 3:`);
                client.say(channel, `${parts[3]}`);
                score += 10;
                quiz_state = 5;
            }
            else{
                client.say(channel, `VoteNay Incorrect. The answerline is:`);
                client.say(channel, `${answers[1]}`);
                client.say(channel, `Were you correct? [y/n]`);
                quiz_state = 4;
            }
            break;
        case 5:
            var correct;
            if(message.length<2){
                correct = false;
            }
            else{
                var input = message.slice(1).toLowerCase().replace(/\s/g, "");
                var answer = answers[2].toLowerCase();
                correct = grader(input, answer);
            }
            if(correct){
                client.say(channel, `VoteYea CORRECT! The answerline is:`);
                client.say(channel, `${answers[2]}`);
                score += 10;
                client.say(channel, `You have scored ${score} \/ 30 points.`);
                con.query('UPDATE bot.viewers SET points = points+? WHERE username = ?', [score, user], (err,rows2) => {
                    if(err) throw err;
                });
                score = 0;
                player = '';
                quiz_state = 0;
            }
            else{
                client.say(channel, `VoteNay Incorrect. The answerline is:`);
                client.say(channel, `${answers[2]}`);
                client.say(channel, `Were you correct? [y/n]`);
                quiz_state = 6;
            }
            break;
          default:;
      }
      return;
  }

  if((message[0] == 'y' || message[0] == 'n') && player == user){
      switch (quiz_state) {
          case 2:
              if(message[0] == 'y'){
                  score += 10;
                  client.say(channel, `Points awarded. Part 2:`);
              }
              else{
                  client.say(channel, `Part 2:`);
              }
              client.say(channel, `${parts[2]}`);
              quiz_state = 3;
              break;
        case 4:
            if(message[0] == 'y'){
                score += 10;
                client.say(channel, `Points awarded. Part 3:`);
            }
            else{
                client.say(channel, `Part 3:`);
            }
            client.say(channel, `${parts[3]}`);
            quiz_state = 5;
            break;
        case 6:
            if(message[0] == 'y'){
                score += 10;
                client.say(channel, `Points awarded. You have scored ${score} \/ 30 points.`);
            }
            else{
                client.say(channel, `You have scored ${score} \/ 30 points.`);
            }
            con.query('UPDATE bot.viewers SET points = points+? WHERE username = ?', [score, user], (err,rows2) => {
                if(err) throw err;
            });
            score = 0;
            player = '';
            quiz_state = 0;
            break;
          default:;
      }
      return;
  }

  var regex = /^[a-z0-9]+$/i;
  if(message[0]!='!' && regex.test(message) == false){
      return;
  }

  con.query('SELECT * FROM bot.commands WHERE command_name = ?', command, (err,rows) => {
      if(err){
          console.log(err);
          client.say(channel, `@mike_hu_0_0 An error occured in a query. Take a look at logs.`);
          return;
      };
      rows.forEach( (row) => {
          var parse = row.response.split('PARSE');
          if(parse.length == 3){
              var answer = parse[0] + eval(parse[1]) + parse[2];
              client.say(channel, `${answer}`);
          }
          else{
              client.say(channel, `${row.response}`);
          }
      });
  });
}


// Called every time the bot connects to Twitch chat
function onConnectedHandler (addr, port) {
  console.log(`* Connected to ${addr}:${port}`);
}


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
