import html

import scheduler
from controller import CTX
from commandRegistrar import handleCommand

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

    if reloading:
        startHunt()
    else:
        scheduler.runIn(5, startHunt)

# Dummy examples of roughly what we might want this file to look like
def loadQuestionList():
    import KPHQuestions

def loadTeamList():
    CTX.teams.createTeam("apple",  "Talented_Ghost","Team Apple")
    CTX.teams.createTeam("banana", "Quiet_Umbrella", "Team Banana")
    CTX.teams.createTeam("tom",    "Easy_Week", "Tom's Team")
    CTX.teams.createTeam("will",   "Wild_Kitten", "Will's Team")

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
    
def renderScore():
    questionList = CTX.questions.getNames()
    teamScores = CTX.teams.getScoreList()

    scoreBoard = texttable.Texttable()
    scoreBoard.set_cols_width([10]*(len(questionList)+2))
    scoreBoard.add_row(['team']+questionList+['score'])
    scoreBoard.add_rows([[i.name]+i.fullScore+[i.score] for i in teamScores],header=False)
    return scoreBoard.draw()

