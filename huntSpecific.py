import html

import scheduler
from controller import CTX
from commandRegistrar import handleCommand

def initialise(reloading=False):
    print("Initialising")

    loadQuestionList()
    loadTeamList()

    if reloading:
        startHunt()
    else:
        scheduler.runIn(5, startHunt)

def loadQuestionList():
    import dummyQuestionList

def loadTeamList():
    CTX.teams.createTeam("aa")
    CTX.teams.createTeam("<b>b'b")

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