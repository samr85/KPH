from threading import RLock, Lock
import datetime
import collections
import html
import base64
import re

import sections

from globalItems import ErrorMessage, startTime, SECTION_LOADER
from commandRegistrar import handleCommand
from controller import CTX

class Team:
    def __init__(self, name, password, fullName = None):
        self.name = name
        self.fullName = fullName or name
        self.questionAnswers = {}
        self.messages = []
        self.lock = RLock()
        self.messagingClients = []
        self.penalty = 0
        self.penaltyReason = ""
        self.penaltyId = 0
        # NOTE: very bad practice if teams were allowed to pick passwords
        self.password = password

    def notifyTeam(self, message, alert=False):
        self.messages.append(message)
        sections.pushSection("message", len(self.messages) - 1, self)
        if alert:
            for client in self.messagingClients:
                client.write_message("alert %s"%(base64.b64encode(message.encode()).decode()))

    def submitAnswer(self, questionId, answerString, time):
        if questionId not in self.questionAnswers:
            raise ErrorMessage("Team does not have access to question: %s"%(questionId))
        answerItem = self.questionAnswers[questionId]
        answerString = html.unescape(answerString)
        answerItem.submitAnswer(re.sub('\W+', '', answerString), time)

    def requestHint(self, questionId):
        if questionId not in self.questionAnswers:
            raise ErrorMessage("Team does not have access to question: %s"%(questionId))
        self.questionAnswers[questionId].requestHint()

    def getScore(self):
        score = 0
        scoreHist = dict()
        lastScoreTime = datetime.datetime.now()
        for id, answer in self.questionAnswers.items():
            thisScore = answer.getScore()
            if thisScore:
                score += thisScore
                if answer.answeredTime < lastScoreTime:
                    lastScoreTime = answer.answeredTime
                scoreHist[id] = str(thisScore)
            else: 
                scoreHist[id] = '0'
        score -= self.penalty
        return lastScoreTime, score, self.renderScore(scoreHist)

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

    def renderQuestion(self, questionId, admin=False):
        if questionId in self.questionAnswers:
            return self.questionAnswers[questionId].renderQuestion(admin)
        raise ErrorMessage("Invalid question: %s"%(questionId))
    
    def renderScore(self, fullScore):
        scoreLine = []
        for question in CTX.questions:
            if not(question.noScore):
                #scoreLine += " "+question.name+" "
                if question.id in fullScore.keys():
                    scoreLine += [fullScore[question.id]]
                else:
                    scoreLine += ["x"]
        return scoreLine      

    def listQuestionIdVersions(self):
        versionList = []
        for answer in self.questionAnswers.values():
            versionList.append((answer.question.id, answer.version))
        versionList.sort(key=lambda x:x[0])
        return versionList

def datetimeToJsString(dtime):
    return str(tuple([i for i in dtime.timetuple()][:6]))

class TeamScore:
    def __init__(self, team):
        self.name = team.fullName
        self.time, self.score, self.fullScore = team.getScore()

class TeamList:
    def __init__(self):
        self.lock = Lock()
        self.teamList = collections.OrderedDict()

    # Make this class act as a dictionay of teams, so can just do for team in CTX.teams or CTX.teams[teamName]
    def __iter__(self):
        return self.teamList.values().__iter__()
    def __len__(self):
        return self.teamList.__len__()
    def __getitem__(self, key):
        return self.getTeam(key)

    def createTeam(self, name, password, fullName = None):
        """ Make a new team """
        with self.lock:
            name = html.escape(name)
            if name in self.teamList:
                raise ErrorMessage("A team of that name already exists")
            if name.lower() in ["all", "admin"]:
                raise ErrorMessage("Team name %s is not allowed"%(name))
            print("Creating new team: %s"%(name))
            newTeam = Team(name, password, fullName)
            self.teamList[name] = newTeam
            return newTeam

    def getTeam(self, name, password=None):
        """ Get the team structure from the name.  Check the team's password if one is given """
        with self.lock:
            # Might have to html escape the name, if this was called manually
            if html.escape(name) in self.teamList:
                name = html.escape(name)
            if name in self.teamList:
                team = self.teamList[name]
                if password != None and password != team.password:
                    raise ErrorMessage("Invalid password")
                return team
            else:
                raise ErrorMessage("Team %s doesn't exist!"%(name))

    def getScoreList(self):
        scores = [TeamScore(team) for team in self]
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
    """ Currenly unused, as createTeam is called from huntSpecific """
    if len(messageList) == 1:
        server.team = CTX.teams.createTeam(messageList[0], None)
    elif len(messageList) == 2:
        server.team = CTX.teams.createTeam(messageList[0], messageList[1])

@handleCommand("setTeamPenalty", messageListLen=3, adminRequired=True)
def setTeamPenalty(_server, messageList, _time):
    teamName = messageList[0]
    scorePenalty = int(messageList[1])
    reason = html.escape(base64.b64decode(messageList[2]).decode())
    team = CTX.teams[teamName]
    team.penalty = scorePenalty
    team.penaltyReason = reason
    team.penaltyId += 1
    team.notifyTeam("Penalty: You have been given a penalty of %d points for reason:<br />%s"%(scorePenalty, reason), alert=True)
    sections.pushSection("penalty", 0, team)
    sections.pushSection("adminPenalty", 0, team)

@sections.registerSectionHandler("penalty")
class PenaltySectionHandler(sections.SectionHandler):
    def __init__(self):
        super().__init__()
        self.requireTeam = True

    def requestSection(self, requestor, sectionId):
        if sectionId == "0" and requestor.team.penalty != 0:
            return (requestor.team.penaltyId, 0, SECTION_LOADER.load("penaltyDisplay.html").generate(team=requestor.team, admin=False))
        return (0, 0, None)

    def requestUpdateList(self, requestor):
        if requestor.team.penalty > 0:
            return [(0, requestor.team.penaltyId)]
        return []

@sections.registerSectionHandler("adminPenalty")
class AdminPenaltySectionHandler(sections.SegragatedSectionHandler):
    def __init__(self):
        super().__init__()
        self.requireAdmin = True

    def requestSectionSegment(self, requestor, sectionId, segment):
        team = CTX.teams.getTeam(segment)
        if sectionId == "0":
            return (team.penaltyId, 0, SECTION_LOADER.load("penaltyDisplay.html").generate(team=team, admin=True))
        return (0, 0, None)

    def requestUpdateListSegment(self, requestor, segment):
        team = CTX.teams.getTeam(segment)
        return [(0, team.penaltyId)]
