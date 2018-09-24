import html
import datetime

import scheduler
from controller import CTX
from commandRegistrar import handleCommand
from sections import SectionHandler, registerSectionHandler

import texttable

# This class is for a global state that anything specific to the hunt can access
class HuntState:
    def __init__(self):
        self.huntStarted = False
        self.lastRoundChange = {}

#Called when the server is loading up.  Only function in here that is called automatically.
# Reloading is set if the server was started with a previous messages file.  Called before any messages are loaded.
#  Will need to work out exactly what state we should be in, so any timers created here need to be worked out somehow
#  I've not fully worked through how this needs to work yet.
# If teams are to be registered in advance, register them here
# Questions should be loaded from here, and this should initiate whatever method is used to allow teams to see the questions
def initialise(reloading=False):
    print("Initialising")

    loadQuestionList()
    loadTeamList()

    # TODO: DISABLE FOR LIVE
    CTX.enableInsecure = False
    CTX.admin.password = "1"

    for question in CTX.questions:
        if question.unlockOn == "initial":
            CTX.enableQuestion(question)

# Dummy examples of roughly what we might want this file to look like
def loadQuestionList():
    import KPHQuestions_sanitized

def loadTeamList():
    CTX.teams.createTeam("apple",  "apple","Team Apple")
    CTX.teams.createTeam("banana", "banana", "Team Banana")

# Use @handleCommand if you want to be able to send any messages to this code from the browsers.
@handleCommand("startHunt", adminRequired=True)
def startHunt(_server = None, _messageList = None, time = None):
    CTX.state.huntStarted = True
    print("Hunt is starting!!!")

    if time:
        timeOffset = (datetime.datetime.now() - time).total_seconds()
    else:
        timeOffset = 0

    scheduler.runIn(9000 - timeOffset, endHuntCallback)
    if 5400 - timeOffset > 0:
        scheduler.runIn(5400 - timeOffset, metaCallback)
    else:
        print("WARNING: Meta timeout already hit, should unlock now if it's not already been done")
    scheduler.displayCountdown("Time remaining", 9000 - timeOffset)

def endHuntCallback():
    print("Hunt has finished!")
    for question in CTX.questions:
        CTX.disableQuestion(question)

def metaCallback():
    for team in CTX.teams:
        if CTX.state.metaQuestion.id not in team.questionAnswers:
            team.notifyTeam("Meta puzzle unlocked automatically!", alert=True)
    CTX.enableQuestion(CTX.state.metaQuestion)

@registerSectionHandler("scoreBoard")
class ScoreBoardHandler(SectionHandler):
    def requestSection(self, requestor, sectionId):
        return (1, scoreVersion(), renderScore().encode())

    def requestUpdateList(self, requestor):
        return [(1, scoreVersion())]

def scoreVersion():
    return sum([team.scoreVersion() for team in CTX.teams])

def renderScore():
    questionList = CTX.questions.getNames()
    teamScores = CTX.teams.getScoreList()

    scoreBoard = texttable.Texttable()
    scoreBoard.set_cols_width([10]*(len(questionList)+2))
    scoreBoard.add_row(['team']+questionList+['score'])
    scoreBoard.add_rows([[i.name]+i.fullScore+[i.score] for i in teamScores],header=False)
    return scoreBoard.draw()

