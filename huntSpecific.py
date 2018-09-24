import html

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
    CTX.admin.password = "complete chalk"

    if reloading:
        startHunt()
    else:
        for question in CTX.questions:
            if question.unlockOn == "initial":
                CTX.enableQuestion(question)

# Dummy examples of roughly what we might want this file to look like
def loadQuestionList():
    import KPHQuestions

def loadTeamList():
    CTX.teams.createTeam("103",          "satisfying scissors", "103")
    CTX.teams.createTeam("XMES",         "distinct truck", "Merry XMES")
    CTX.teams.createTeam("nottoblame",   "lyrical frog", "We are not to blame for our lack of gender diversity, she dropped out") 
    CTX.teams.createTeam('Diversity',    "quack channel", '"Diversity"')
    CTX.teams.createTeam("Todd Smith",   "worthless key", "Todd Smith Classics")
    CTX.teams.createTeam("Pirate",       "best engine", "Pirate offering a chair? (2,4)")
    CTX.teams.createTeam("BrRocCraLei",  "lively fold", "BrRocCraLei")
    CTX.teams.createTeam("Red Lorry",    "supreme zoo", "Red Lorry Yellow Jacob")
    CTX.teams.createTeam("Singular",     "utopian cent", "A Singular Hope")
    CTX.teams.createTeam("Black Swan",   "deserted berry", "Black Swan Masochists")
    CTX.teams.createTeam("Team11",       "waiting fireman", "Team11")
    CTX.teams.createTeam("MERJ",  "unruly mind", "MERJ Lanes")
    CTX.teams.createTeam("Non Bonds",  "sombre shop", "The 4 Non Bonds")
    CTX.teams.createTeam("F-B Good",  "ritzy debt", "Finger-Bricking Good")
    CTX.teams.createTeam("TBD",  "bustling arm", "TBD")
    CTX.teams.createTeam("Team16",  "misty business", "Team16")
    CTX.teams.createTeam("Cutting",  "supreme summer", "Here for the cutting and sticking")
    CTX.teams.createTeam("Hmm",  "callous drink", "Hmm")
    CTX.teams.createTeam("Mistake Not",  "zesty business", "Mistake Not...")
    CTX.teams.createTeam("HACHing",  "general balloon", "HACHing cough")
    CTX.teams.createTeam("Bad Rubbish",  "waiting insect", "Make Good Use of Bad Rubbish")
    CTX.teams.createTeam("Erbal",  "smart degree", "Erbal Tom-ay-toes % Herbal Tom-ah-toes")
    CTX.teams.createTeam("order66.exe",  "languid hope", "order66.exe")
    
      

# Use @handleCommand if you want to be able to send any messages to this code from the browsers.
@handleCommand("startHunt", adminRequired=True)
def startHunt(_server = None, _messageList = None, _time = None):
    CTX.state.huntStarted = True
    print("Hunt is starting!!!")
    
    scheduler.runIn(1800, announceHoursCallback, args=([2]))
    scheduler.runIn(5400, announceHoursCallback, args=([1]))
    scheduler.runIn(7200, announceMinutesCallback, args=([30]))
    scheduler.runIn(7800, announceMinutesCallback, args=([20]))
    scheduler.runIn(8400, announceMinutesCallback, args=([10]))
    scheduler.runIn(9000, endHuntCallback)
    scheduler.runIn(5400, metaCallback)
    scheduler.displayCountdown("Time remaining", 9000)


def endHuntCallback():
    print("Hunt has finished!")
    for question in CTX.questions:
        CTX.disableQuestion(question)

def metaCallback():
    for team in CTX.teams:
        if CTX.state.metaQuestion.id not in team.questionAnswers:
            team.notifyTeam("Meta puzzle unlocked automatically!", alert=True)
    CTX.enableQuestion(CTX.state.metaQuestion)
    
def announceHoursCallback(hours):
    for team in CTX.teams:
        if hours > 1:
            team.notifyTeam("Announcement: %d hours remaining!"% hours, alert=True)
        elif hours == 1:
            team.notifyTeam("Announcement: %d hour remaining!"% hours, alert=True)
    
def announceMinutesCallback(minutes):

    for team in CTX.teams:
        team.notifyTeam("Announcement: %d minutes remaining!"% minutes, alert=True)

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
    scoreBoard.set_cols_align(['l']+['r']*(len(questionList)+1))
    scoreBoard.set_cols_width([11]+[10]*len(questionList)+[6])
    scoreBoard.header(['Team Name']+questionList+['TOTAL SCORE'])
    scoreBoard.add_rows([[i.name]+i.fullScore+[i.score] for i in teamScores],header=False)
    return scoreBoard.draw()

