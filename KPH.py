from threading import Lock
import collections
import json
import datetime

class ErrorMessage(Exception):
    def __init__(self, message):
        self.message = message


class Question:
    def __init__(self, dictionary):
        self.name = ""
        self.question = ""
        self.answers = []
        self.hints = []
        self.__dict__ = dictionary
        if not (hasattr(self, "name") and
                hasattr(self, "question") and
                hasattr(self, "answers") and
                hasattr(self, "hints")):
            raise ValueError("Invalid question dictionary: %s"%(dictionary))
        # TODO: Check dictionary loaded right!

    def toJson(self):
        return json.dumps(self.__dict__, indent = 4)

    def displayQuestionToTeam(self):
        retStr = ""
        retStr += "Question: %s <br />"%(self.name)
        retStr += self.question + "<br />"
        return retStr

    def displayHintsToTeam(self, team, hintsRequested, allowRequest):
        if hintsRequested > len(self.hints) or hintsRequested < 0:
            raise ErrorMessage("Invalid number of requested hints: %d"%(hintsRequested))
        retStr = ""
        if hintsRequested:
            retStr += "Requested hints: <br />"
            for hintNum in range(hintsRequested):
                retStr += "Hint %d: %s<br />"%(hintNum, self.hints[hintNum])
        if allowRequest and hintsRequested < len(self.hints):
            retStr += "<button onclick='sendMessage(\"reqHint %s\")'>Request Hint</button><br />"%(self.name)
        return retStr

class QuestionList:
    def __init__(self, jsonFile):
        self.questionList = collections.OrderedDict()
        self.lock = Lock()
        with self.lock:
            with open(jsonFile, "r") as f:
                questionContent = json.load(f)
            for question in questionContent:
                print(question)
                q = Question(question)
                self.questionList[q.name] = q


class Team:
    def __init__(self, name):
        self.name = name
        self.questionAnswers = {}
        self.messages = []

    def notifyTeam(self, message, refresh = False):
        self.messages.append(message)
        for client in clients:
            if client.team == self:
                client.write_message(message)
                if refresh:
                    client.sendRefresh()

    def sendAllNotifications(self, client):
        for message in self.messages:
            client.write_message(message)

    def submitAnswer(self, question, answer):
        if question not in self.questionAnswers:
            self.questionAnswers[question] = Answer(question, self)
        answerItem = self.questionAnswers[question]
        answerItem.submitAnswer(answer)
        self.notifyTeam("Answer %s submitted for question %s"%(answer, question), refresh = True)

    def requestHint(self, question):
        if question not in self.questionAnswers:
            self.questionAnswers[question] = Answer(question, self)
        self.questionAnswers[question].requestHint()
        self.notifyTeam("Hint for question %s unlocked"%(question), refresh = True)

    def allowedToSubmitAnswer(self):
        for answer in answerQueue.answerList:
            if answer.team == self:
                return False
        return True

    def makeQuestionList(self):
        retStr = "<h1>Question List for %s</h1><br />"%(self.name)
        for question in questionList.questionList:
            if True: #Check that the team is allowed to see this question!
                if question not in self.questionAnswers:
                    self.questionAnswers[question] = Answer(question, self)
                retStr += self.questionAnswers[question].displayQuestion()
        return retStr

    def getScore(self):
        score = 0
        lastScoreTime = datetime.datetime.now()
        for answer in self.questionAnswers.values():
            thisScore = answer.score()
            if thisScore:
                score += thisScore
                if answer.answeredTime < lastScoreTime:
                    lastScoreTime = answer.answeredTime
        return lastScoreTime, score

    def getScoreHistory(self):
        answers = self.questionAnswers.values()
        answers = sorted(answers, key=lambda answer: answer.answeredTime)
        answerHistory = [(startTime, 0, datetimeToJsString(startTime))]
        curScore = 0
        for answer in answers:
            thisScore = answer.score()
            if thisScore:
                curScore += thisScore
                answerHistory.append((answer.answeredTime, curScore, datetimeToJsString(answer.answeredTime)))
        answerHistory.append((datetime.datetime.now(), curScore, datetimeToJsString(datetime.datetime.now())))
        return answerHistory

def datetimeToJsString(dt):
    return  str(tuple([i for i in dt.timetuple()][:6]))

class teamScore:
    def __init__(self, team):
        self.name = team.name
        self.time, self.score = team.getScore()

class TeamList:
    def __init__(self):
        self.lock = Lock()
        self.teamList = {}

    def createTeam(self, name):
        with self.lock:
            if name in self.teamList:
                raise ErrorMessage("A team of that name already exists")
            print("Creating new team: %s"%(name))
            newTeam = Team(name)
            self.teamList[name] = newTeam
            return newTeam

    def getTeam(self, name):
        with self.lock:
            if name in self.teamList:
                return self.teamList[name]
            else:
                raise ErrorMessage("Team %s doesn't exist!"%(name))

    def getScoreList(self):
        scores = [teamScore(team) for team in self.teamList.values()]
        dtnow = datetime.datetime.now()
        #Sorting is wrong!!!
        return sorted(scores, key=lambda teamS: (teamS.score, dtnow - teamS.time), reverse=True)

    def getScoreHistory(self):
        scoreHistory = collections.OrderedDict()
        for teamName in sorted(self.teamList.keys()):
            scoreHistory[teamName] = self.teamList[teamName].getScoreHistory()
        return scoreHistory

class Answer:
    INCORRECT = 0
    SUBMITTED = 1
    CORRECT = 2
    nextID = [0]
    idLock = Lock()

    def __init__(self, questionName = None, team = None):
        if questionName not in questionList.questionList:
            raise ErrorMessage("Question does not exist!")
        with self.idLock:
            self.id = self.nextID[0]
            self.nextID[0] += 1
        self.question = questionList.questionList[questionName]
        self.team = team
        self.status = self.INCORRECT
        self.previousAnswers = []
        self.hintCount = 0
        self.answer = ""
        self.answeredTime = datetime.datetime.now() 

    def submitAnswer(self, answer):
        if self.status != self.CORRECT:
            self.answer = answer
            answerQueue.queueAnswer(self)
            self.status = self.SUBMITTED
            self.answeredTime = datetime.datetime.now()
        else:
            raise ErrorMessage("Can't submit an answer to an already answered question!")

    def mark(self, mark):
        if mark:
            self.status = self.CORRECT
            self.team.notifyTeam("%s answer: CORRECT!"%(self.question.name), refresh = True)
        else:
            self.status = self.INCORRECT
            self.team.notifyTeam("%s answer: INCORRECT :("%(self.question.name), refresh = True)
            self.previousAnswers.append(self.answer)

    def displayQuestion(self):
        retStr = self.question.displayQuestionToTeam()
        if self.status == self.CORRECT:
            retStr += "Correct answer submitted: %s<br />"%(self.answer)
        retStr += self.question.displayHintsToTeam(self.team, self.hintCount, self.status==self.INCORRECT)
        if self.previousAnswers:
            retStr += "Previous incorrectly submitted answers: <br />"
            retStr += ", ".join(self.previousAnswers)
            retStr += "<br />"
        if self.status == self.SUBMITTED:
            retStr += "Submitted answer waiting marking: %s <br />"%(self.answer)
        if self.status == self.INCORRECT and self.team.allowedToSubmitAnswer():
            retStr += "<div id='%sErr'></div>Submit answer: <input id='%sAnswer' type='text' name='message' /><button onclick='submitAnswer(\"%s\")')>Submit answer</button><br />"%(self.question.name, self.question.name, self.question.name)
        retStr += "<br /><br />"
        return retStr

    def requestHint(self):
        if self.hintCount < len(self.question.hints):
            self.hintCount += 1
        else:
            raise ErrorMessage("All hints already requested")

    def score(self):
        if self.status == Answer.CORRECT:
            return self.question.score - self.question.hintCost * self.hintCount
        return 0

class AnswerSubmissionQueue:
    answerList = collections.deque()
    
    def __init__(self):
        self.lock = Lock()

    def queueAnswer(self, newAnswer):
        with self.lock:
            for answer in self.answerList:
                if answer.team == newAnswer.team:
                    raise ErrorMessage("Cannot submit another answer until your previous one has been marked (answer: %s pending for question: %s"%(answer.answer, answer.question))
            self.answerList.append(newAnswer)
            refreshAdmin()

    def markAnswer(self, teamName, questionName, mark):
        for answer in self.answerList:
            if answer.team.name == teamName and answer.question.name == questionName:
                answer.mark(mark)
                self.answerList.remove(answer)
                refreshAdmin()
                return
        raise ErrorMessage("Answer not found to mark!")

    def makeAnswerList(self):
        retStr = ""
        for answer in self.answerList:
            if False:
                retStr += '<form action="?" method="get">'
                retStr += '<input type="hidden" name="action" value="Mark" /><input type="hidden" name="teamName" value="%s" /><input type="hidden" name="question" value="%s" />'%(answer.team.name, answer.question.name)
                retStr += 'Team: %s<br />Question: %s<br />Submitted answer: %s<br />Correct answers: %s<br />'%(answer.team.name, answer.question.name, answer.answer, ", ".join(questionList.questionList[answer.question.name].answers))
                retStr += '<button type="submit" name="message" value="1">Correct</button><button type="submit" name="message" value="0">Inorrect</button></form>'
                retStr += "\n"

            retStr += 'Team: %s<br />Question: %s<br />Submitted answer: %s<br />Correct answers: %s<br />'%(answer.team.name, answer.question.name, answer.answer, ", ".join(questionList.questionList[answer.question.name].answers))
            clickFunctionStart = "onclick='sendMessage(\"markAnswer %s %s"%(answer.team.name, answer.question.name)
            retStr += '<button %s correct")\'>Correct</button><button %s incorrect")\'>Incorrect</button>'%(clickFunctionStart, clickFunctionStart)
            retStr += '<br /><br />'
        return retStr

def refreshAdmin():
    for client in clients:
        if client.admin:
            client.sendRefresh()

def refreshTeam(team):
    for client in clients:
        if client.team == team:
            client.sendRefresh()

answerQueue = AnswerSubmissionQueue()
teamList = TeamList()
questionList = QuestionList("questionList.txt")
clients = []
startTime = datetime.datetime.now()