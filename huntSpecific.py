import html

import scheduler
from controller import CTX
from commandRegistrar import handleCommand

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
    import dummyQuestionList

def loadTeamList():
    CTX.teams.createTeam("aa", "a")
    CTX.teams.createTeam("<b>b'b", "b")

# Use @handleCommand if you want to be able to send any messages to this code from the browsers.
@handleCommand("startHunt", adminRequired=True)
def startHunt():
    print("Hunt is starting!!!")
    for question in CTX.questions.questionList.values():
        if question.unlockOn == "initial":
            CTX.enableQuestion(question)
    CTX.disableQuestion(question, CTX.teams.getTeam(html.escape("<b>b'b")))
    #scheduler.runIn(6, finalPuzzleCallback)
    scheduler.runIn(1000, endHuntCallback)
    scheduler.displayCountdown("Time remaining", 1000)

def endHuntCallback():
    print("Hunt has finished!")
    for question in CTX.questions.questionList.values():
        CTX.disableQuestion(question)

def finalPuzzleCallback():
    for question in CTX.questions.questionList.values():
        if question.unlockOn != "finalQuestion":
            CTX.disableQuestion(question)
        else:
            CTX.enableQuestion(question)
