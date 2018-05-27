from threading import RLock, Lock
import datetime
import collections
import html

import sections
from globalItems import ErrorMessage, startTime
from commandRegistrar import handleCommand
from controller import CTX

class Team:
    def __init__(self, name, password):
        self.name = name
        self.questionAnswers = {}
        self.messages = []
        self.lock = RLock()
        self.messagingClients = []
        self.penalty = 0
        # NOTE: very bad practice if teams were allowed to pick passwords
        self.password = password

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
        score -= self.penalty
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

def datetimeToJsString(dtime):
    return str(tuple([i for i in dtime.timetuple()][:6]))

class TeamScore:
    def __init__(self, team):
        self.name = team.name
        self.time, self.score = team.getScore()

class TeamList:
    def __init__(self):
        self.lock = Lock()
        self.teamList = {}

    def createTeam(self, name, password):
        with self.lock:
            name = html.escape(name)
            if name in self.teamList:
                raise ErrorMessage("A team of that name already exists")
            print("Creating new team: %s"%(name))
            newTeam = Team(name, password)
            self.teamList[name] = newTeam
            return newTeam

    def getTeam(self, name, password=None):
        with self.lock:
            if name in self.teamList:
                team = self.teamList[name]
                if password != None and password != team.password:
                    raise ErrorMessage("Invalid password")
                return team
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

@handleCommand("createTeam")
def createTeam(server, messageList, _time):
    if len(messageList) == 1:
        server.team = CTX.teams.createTeam(messageList[0], None)
    elif len(messageList) == 2:
        server.team = CTX.teams.createTeam(messageList[0], messageList[1])

@handleCommand("setTeamPenalty", messageListLen=3, adminRequired=True)
def setTeamPenalty(_server, messageList, _time):
    teamName = messageList[0]
    scorePenalty = int(messageList[1])
    reason = messageList[2]
    team = CTX.teams.getTeam(teamName)
    team.penalty = scorePenalty
    team.notifyTeam("You have been given a penalty of %d points for %s"%(scorePenalty, reason))
