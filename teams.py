from threading import RLock, Lock
import datetime
import collections

from answers import Answer, answerQueue
from questions import questionList
from globalItems import ErrorMessage, startTime
from messageHandler import handleMessage

class Team:
    def __init__(self, name):
        self.name = name
        self.questionAnswers = {}
        self.messages = []
        self.lock = RLock()
        for qName, question in questionList.questionList.items():
            self.questionAnswers[qName] = Answer(question, self)
        self.messagingClients = []

    def notifyTeam(self, message):
        self.messages.append(message)
        for client in self.messagingClients:
            client.write_message(message)

    def sendAllNotifications(self, client):
        # TODO: this looks bad
        for message in self.messages:
            client.write_message(message)

    def submitAnswer(self, question, answer, time):
        if question not in self.questionAnswers:
            raise ErrorMessage("Team does not have access to question: %s"%(question))
        answerItem = self.questionAnswers[question]
        answerItem.submitAnswer(answer, time)
        self.notifyTeam("Answer %s submitted for question %s"%(answer, question))

    def requestHint(self, question):
        if question not in self.questionAnswers:
            raise ErrorMessage("Team does not have access to question: %s"%(question))
        self.questionAnswers[question].requestHint()

    def allowedToSubmitAnswer(self):
        for answer in answerQueue.answerList:
            if answer.team == self:
                return False
        return True

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

    def renderQuestion(self, questionName):
        if questionName in self.questionAnswers:
            return self.questionAnswers[questionName].renderQuestion()
        raise ErrorMessage("Invalid question: %s"%(questionName))

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

teamList = TeamList()

# TODO: This function needs to be locked down!
@handleCommand("createTeam", 1)
def createTeam(server, messageList, _time):
    from teams import teamList
    server.team = teamList.createTeam(messageList[0])