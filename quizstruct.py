import nltk
import re

SEPARATE = '*SEP*'

class Quiz():

    def __init__(self):
        self.quiz_state = 0
                    # 0: Halt
                    # 1: Awaiting answer 1
                    # 2: Answer 1 ruled incorrect
                    # 3: Awaiting answer 2
                    # 4: Answer 2 ruled incorrect
                    # 5: Awaiting answer 3
                    # 6: Answer 3 ruled incorrect
        self.parts = None
        self.answers = None
        self.player = ''
        self.score = 0

    def get_state(self):
        return self.quiz_state
    
    def get_score(self):
        return self.score

    def get_player(self):
        return self.player

    def get_parts(self, index):
        return self.parts[index]

    def get_answers(self, index):
        return self.answers[index]

    def set_parts(self, parts):
        self.parts = parts

    def set_answers(self, answers):
        self.answers = answers

    def set_player(self, player):
        self.player = player


    # input has white space removed and changed to lower case, answer is only changed to lower case
    def grader_helper(self, input, answer):
        accept = answer.split('do not')
        args = accept[0].split(' ')
        noWhiteSpace = accept[0].replace(' ', '')
        if len(input)>1 and input in noWhiteSpace:
            return True
        for a in args:
            distance = nltk.edit_distance(input, a)
            if distance<2:
                return True
        args2 = re.split(r'[\[<]', noWhiteSpace)
        length = len(args2[0])
        distance = nltk.edit_distance(input, args2[0])
        if distance<(length/2):
            return True
        return False


    # return values: reply, update/not update score
    def grader(self, input):

        if self.quiz_state==0:
            self.quiz_state = 1
            return None, None
     
        if self.quiz_state==1:
            input = input.lower().replace(' ', '')
            answer = self.answers[0].lower()
            if len(input)<1:
                correct = False
            else:
                correct = self.grader_helper(input, answer)

            if correct:
                self.score+=10
                self.quiz_state = 3
                return ("BlobYes CORRECT! The answerline is:" +
                        SEPARATE +
                        self.answers[0] +
                        SEPARATE +
                        "Part 2:" +
                        SEPARATE +
                        self.parts[2]), False
            else:
                self.quiz_state = 2
                return ("BlobNo Incorrect. The answerline is:" +
                        SEPARATE +
                        self.answers[0] +
                        SEPARATE +
                        "Were you correct? [y/n]"), False
        elif self.quiz_state==3:
            input = input.lower().replace(' ', '')
            answer = self.answers[1].lower()
            if len(input)<1:
                correct = False
            else:
                correct = self.grader_helper(input, answer)

            if correct:
                self.score+=10
                self.quiz_state = 5
                return ("BlobYes CORRECT! The answerline is:" +
                        SEPARATE +
                        self.answers[1] +
                        SEPARATE +
                        "Part 3:" +
                        SEPARATE +
                        self.parts[3]), False
            else:
                self.quiz_state = 4
                return ("BlobNo Incorrect. The answerline is:" +
                        SEPARATE +
                        self.answers[1] +
                        SEPARATE +
                        "Were you correct? [y/n]"), False
        elif self.quiz_state==5:
            input = input.lower().replace(' ', '')
            answer = self.answers[2].lower()
            if len(input)<1:
                correct = False
            else:
                correct = self.grader_helper(input, answer)

            if correct:
                self.score+=10
                self.quiz_state = 0
                return ("BlobYes CORRECT! The answerline is:" +
                        SEPARATE +
                        self.answers[2] +
                        SEPARATE +
                        "You have scored {0} / 30 points.".format(self.score)), True
            else:
                self.quiz_state = 6
                return ("BlobNo Incorrect. The answerline is:" +
                        SEPARATE +
                        self.answers[2] +
                        SEPARATE +
                        "Were you correct? [y/n]"), False
        else:
            return None, None


    def no_helper(self):
        if self.quiz_state==2:
            self.quiz_state = 3
            return "Part 2:"+SEPARATE+self.parts[2], False
        elif self.quiz_state==4:
            self.quiz_state = 5
            return "Part 3:"+SEPARATE+self.parts[3], False
        elif self.quiz_state==6:
            self.quiz_state = 0
            return "You have scored {0} / 30 points.".format(self.score), True
        else:
            return None, None


    def yes_helper(self):
        if self.quiz_state==2:
            self.score+=10
            self.quiz_state = 3
            return "Points awarded. Part 2:"+SEPARATE+self.parts[2], False
        elif self.quiz_state==4:
            self.score+=10
            self.quiz_state = 5
            return "Points awarded. Part 3:"+SEPARATE+self.parts[3], False
        elif self.quiz_state==6:
            self.score+=10
            self.quiz_state = 0
            return "Points awarded. You have scored {0} / 30 points.".format(self.score), True
        else:
            return None, None   


    def reset(self):
        self.parts = ['' for i in range(4)]
        self.answers = ['' for i in range(4)]
        self.player = ''
        self.score = 0
        self.quiz_state = 0