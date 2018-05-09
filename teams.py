from threading import RLock, Lock
import datetime
import collections
import html

import sections
from globalItems import ErrorMessage, startTime
from commandRegistrar import handleCommand

class Team:
    def __init__(self, name):
        self.name = name
        self.questionAnswers = {}
        self.messages = []
        self.lock = RLock()
        self.messagingClients = []

    def notifyTeam(self, message):
        self.messages.append(message)
        sections.pushSection("message", len(self.messages) - 1, self)

    def submitAnswer(self, questionId, answerString, time):
        if questionId not in self.questionAnswers:
            raise ErrorMessage("Team does not have access to question: %s"%(questionId))
        answerItem = self.questionAnswers[questionId]
        answerItem.submitAnswer(answerString, time)
        self.notifyTeam("Answer %s submitted for question %s"%(answerString, questionId))

    def requestHint(self, questionId):
        if questionId not in self.questionAnswers:
            raise ErrorMessage("Team does not have access to question: %s"%(questionId))
        self.questionAnswers[questionId].requestHint()

    def getScore(self):
        score = 0
        lastScoreTime = datetime.datetime.now()
        for answer in self.questionAnswers.values():
            thisScore = answer.getScore()
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
            thisScore = answer.getScore()
            if thisScore:
                curScore += thisScore
                answerHistory.append((answer.answeredTime, curScore, datetimeToJsString(answer.answeredTime)))
        answerHistory.append((datetime.datetime.now(), curScore, datetimeToJsString(datetime.datetime.now())))
        return answerHistory

    def renderQuestion(self, questionId):
        if questionId in self.questionAnswers:
            return self.questionAnswers[questionId].renderQuestion()
        raise ErrorMessage("Invalid question: %s"%(questionId))

def datetimeToJsString(dt):
    return  str(tuple([i for i in dt.timetuple()][:6]))

class TeamScore:
    def __init__(self, team):
        self.name = team.name
        self.time, self.score = team.getScore()

class TeamList:
    def __init__(self):
        self.lock = Lock()
        self.teamList = {}

    def createTeam(self, name):
        with self.lock:
            name = html.escape(name)
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
        scores = [TeamScore(team) for team in self.teamList.values()]
        dtnow = datetime.datetime.now()
        #TODO: Sorting is wrong!!!
        return sorted(scores, key=lambda teamS: (teamS.score, dtnow - teamS.time), reverse=True)

    def getScoreHistory(self):
        scoreHistory = collections.OrderedDict()
        for teamName in sorted(self.teamList.keys()):
            scoreHistory[teamName] = self.teamList[teamName].getScoreHistory()
        return scoreHistory

@handleCommand("createTeam", 1)
def createTeam(server, messageList, _time):
    from controller import CTX
    server.team = CTX.teams.createTeam(messageList[0])
