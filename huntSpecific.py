import scheduler
from controller import CTX

def initialise(reloading=False):
    print("Initialising")

    loadQuestionList()
    loadTeamList()

    if not reloading:
        scheduler.runIn(2, startHunt)

def loadQuestionList():
    import dummyQuestionList

def loadTeamList():
    CTX.teams.createTeam("aa")
    CTX.teams.createTeam("bb")

def startHunt():
    print("Hunt is starting!!!")
    for question in CTX.questions.questionList.values():
        CTX.enableQuestion(question)
    CTX.disableQuestion(question, CTX.teams.getTeam("bb"))


def huntEnd():
    print("Hunt has finished!")
    for question in CTX.questions.questionList.values():
        CTX.disableQuestion(question)
