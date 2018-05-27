import datetime
import json

import sections
import messageHandler
from globalItems import ErrorMessage

class HuntContext:
    def __init__(self):
        # This is so that the following imports can do from controller import CTX successfully
        global CTX
        CTX = self
        import teams
        import admin
        import questions
        import answers
        self.questions = questions.QuestionList() 
        self.teams = teams.TeamList()
        self.admin = admin.AdminList()
        self.answerQueue = answers.AnswerSubmissionQueue()
        self.newAnswer = answers.Answer
        self.messagingClients = messageHandler.MessagingClients()

        # Logging in with no passwords
        self.enableInsecure = False

    def importMessages(self, inputFile):
        for line in inputFile:
            messageDict = json.loads(line)
            if "team" in messageDict:
                try:
                    team = self.teams.getTeam(messageDict["team"])
                except ErrorMessage:
                    team = None
                    print("Invalid team in message file: %s" % (messageDict["team"]))
            else:
                team = None
            admin = "admin" in messageDict
            msgTime = datetime.datetime.strptime(messageDict["time"], "%Y-%m-%dT%H:%M:%S.%f")
            messageHandler.sendDummyMessage(messageDict["message"], messageDict["messageList"], team, admin, msgTime)

    def enableQuestion(self, question, team=None):
        if not team:
            for teamIt in self.teams.teamList.values():
                self.enableQuestion(question, teamIt)
            return

        if question.id not in team.questionAnswers:
            team.questionAnswers[question.id] = self.newAnswer(question, team)
        team.questionAnswers[question.id].enabled = True
        sections.pushSection("question", question.id, team)

    def disableQuestion(self, question, team=None):
        if not team:
            for teamIt in self.teams.teamList.values():
                self.disableQuestion(question, teamIt)
            return
        if question.id not in team.questionAnswers:
            return
        team.questionAnswers[question.id].enabled = False
        sections.pushSection("question", question.id, team)

CTX = HuntContext()
