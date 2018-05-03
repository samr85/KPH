import datetime
import json

import teams
import questions
import answers
import sections
import messageHandler
from globalItems import ErrorMessage

class HuntContext:
    def __init__(self):
        self.questions = questions.QuestionList()
        self.teams = teams.TeamList()

    def importMessages(self, inputFile):
        for line in inputFile:
            messageDict = json.loads(line)
            if "team" in messageDict:
                try:
                    team = self.teams.getTeam(messageDict["team"])
                except ErrorMessage:
                    team = None
                    #raise ErrorMessage("Invalid team in message file: %s" % (messageDict["team"]))
            else:
                team = None
            if "admin" in messageDict:
                admin = True
            else:
                admin = False
            msgTime = datetime.datetime.strptime(messageDict["time"], "%Y-%m-%dT%H:%M:%S.%f")
            messageHandler.sendDummyMessage(messageDict["message"], messageDict["messageList"], team, admin, msgTime)

    def enableQuestion(self, question, team=None):
        if not team:
            for teamIt in self.teams.teamList.values():
                self.enableQuestion(question, teamIt)
            return

        if question.name not in team.questionAnswers:
            team.questionAnswers[question.name] = answers.Answer(question, team)
        team.questionAnswers[question.name].enabled = True
        sections.pushSection(team.messagingClients, "question", question.name)

    def disableQuestion(self, question, team=None):
        if not team:
            for teamIt in self.teams.teamList.values():
                self.enableQuestion(question, teamIt)
            return
        if question.name not in team.questionAnswers:
            return
        team.questionAnswers[question.name].enabled = False
        sections.pushSection(team.messagingClients, "question", question.name)

CTX = HuntContext()
