import html

import scheduler
from controller import CTX
from commandRegistrar import handleCommand

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
    CTX.enableInsecure = True
    CTX.admin.password = "1"

    if reloading:
        startHunt()
    else:
        scheduler.runIn(5, startHunt)

# Dummy examples of roughly what we might want this file to look like
def loadQuestionList():
    import KPHQuestions

def loadTeamList():
    CTX.teams.createTeam("j", "j","Full Team Name")
    CTX.teams.createTeam("c", "c")
    CTX.teams.createTeam("t", "t")
    CTX.teams.createTeam("a", "a")

# Use @handleCommand if you want to be able to send any messages to this code from the browsers.
@handleCommand("startHunt", adminRequired=True)
def startHunt():
    CTX.state.huntStarted = True
    print("Hunt is starting!!!")
    for question in CTX.questions:
        if question.unlockOn == "initial":
            CTX.enableQuestion(question)
    #CTX.disableQuestion(question, CTX.teams[html.escape("<b>b'b")])
    #scheduler.runIn(6, finalPuzzleCallback)
    scheduler.runIn(180, endHuntCallback)
    scheduler.runIn(60, metaCallback)
    scheduler.displayCountdown("Time remaining", 180)

def endHuntCallback():
    print("Hunt has finished!")
    for question in CTX.questions:
        CTX.disableQuestion(question)
            
def metaCallback():

    for team in CTX.teams:
        if CTX.state.metaQuestion.id not in team.questionAnswers:
            team.notifyTeam("Meta puzzle unlocked automatically!", alert=True)
    CTX.enableQuestion(CTX.state.metaQuestion)

