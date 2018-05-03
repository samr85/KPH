import scheduler
from controller import CTX

def initialise(reloading=False):
    print("Initialising")

    loadQuestionList()
    loadTeamList()

    if not reloading:
        scheduler.runIn(10, startHunt)

def loadQuestionList():
    CTX.questions.importQuestions("questionList.txt")

def loadTeamList():
    CTX.teams.createTeam("aa")
    CTX.teams.createTeam("bb")

def startHunt():
    print("Hunt is starting!!!")
    for question in CTX.questions.questionList.values():
        CTX.enableQuestion(question)
