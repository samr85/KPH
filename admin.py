from commandRegistrar import handleCommand
from globalItems import ErrorMessage
import sections

from controller import CTX

class AdminList:
    def __init__(self):
        self.messagingClients = []
        self.messages = []
        self.password = None

    def messageAdmin(self, message):
        self.messages.append(message)
        sections.pushSection("message", len(self.messages) - 1, "admin")

    @staticmethod
    def renderAnswerQueue(answerId):
        return CTX.answerQueue.renderEntry(answerId)

    @staticmethod
    def getAnswerQueueEntries():
        return CTX.answerQueue.getEntries()

@handleCommand("markAnswer", adminRequired=True)
def markAnswer(_server, messageList, _time):
    # messageList = teamName questionName correct/incorrect [mark]
    if len(messageList) == 3:
        CTX.answerQueue.markAnswer(messageList[0], messageList[1], messageList[2].lower() == "correct", 0)
    elif len(messageList) == 4:
        try:
            score = int(messageList[3])
        except ValueError:
            raise ErrorMessage("Invalid number for score: %s"%(messageList[3]))
        CTX.answerQueue.markAnswer(messageList[0], messageList[1], messageList[2].lower() == "correct", score)
    else:
        raise ErrorMessage("Incorrect number of parameters to markAnswer (got %d)!"%(len(messageList)))

@handleCommand("messageAdmin", teamRequired=True)
def teamMessageAdmin(server, messageList, _time):
    CTX.admin.messageAdmin("Team Message: %s: %s"%(server.team.name, " ".join(messageList)))
    server.team.notifyTeam("Message Sent: %s"%(" ".join(messageList)))

@handleCommand("messageTeam", adminRequired=True)
def adminMessageTeam(_server, messageList, _time):
    teamName = messageList[0]
    message = " ".join(messageList[1:])
    if teamName == "all":
        CTX.admin.messageAdmin("Announcement: %s"%(message))
        for team in CTX.teams.teamList.values():
            team.notifyTeam("Announcement: %s"%(message))
    else:
        # raises exception on error
        team = CTX.teams.getTeam(teamName)
        team.notifyTeam("Admin Message: %s"%(message))
        CTX.admin.messageAdmin("Message Sent: %s: %s"%(teamName, message))
