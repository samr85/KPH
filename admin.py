import base64

from commandRegistrar import handleCommand
from globalItems import ErrorMessage
import sections

from controller import CTX

class AdminList:
    """ Structure holding information for admins """
    def __init__(self):
        self.messagingClients = []
        self.messages = []
        self.password = None

    def messageAdmin(self, message, alert=False):
        self.messages.append(message)
        sections.pushSection("message", len(self.messages) - 1, "admin")
        if alert:
            for client in self.messagingClients:
                client.write_message("alert %s"%(base64.b64encode(message.encode()).decode()))


    @staticmethod
    def renderAnswerQueue(answerId):
        return CTX.answerQueue.renderEntry(answerId)

    @staticmethod
    def getAnswerQueueEntries():
        return CTX.answerQueue.getEntries()

@handleCommand("markAnswer", adminRequired=True)
def markAnswer(_server, messageList, _time):
    """ Message from the admins specifying if submitted answer is correct or not """
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
    """ Send a message from a team to the admins.  Possibly disable? """
    CTX.admin.messageAdmin("Team Message: %s: %s"%(server.team.name, " ".join(messageList)), alert=True)
    server.team.notifyTeam("Message Sent: %s"%(" ".join(messageList)))

@handleCommand("messageTeam", adminRequired=True)
def adminMessageTeam(_server, messageList, _time):
    """ Send a message from the admins to either a specific team or all teams """
    teamName = messageList[0]
    message = " ".join(messageList[1:])
    if teamName == "all":
        CTX.admin.messageAdmin("Announcement: %s"%(message))
        for team in CTX.teams:
            team.notifyTeam("Announcement: %s"%(message), alert=True)
    else:
        # raises exception on error
        team = CTX.teams[teamName]
        team.notifyTeam("Admin Message: %s"%(message), alert=True)
        CTX.admin.messageAdmin("Message Sent: %s: %s"%(teamName, message))

@handleCommand("adjustAnswer", messageListLen=4, adminRequired=True)
def adjustAnswer(_server, messageList, _time):
    """ Modify the answer referring to a team's submission """
    adjustType = messageList[0]
    questionId = messageList[1]
    teamName = messageList[2]
    newValue = messageList[3]
    team = CTX.teams.getTeam(teamName)
    try:
        answer = team.questionAnswers[questionId]
    except KeyError:
        raise ErrorMessage("Invalid questionId: %s"%(questionId))
    if adjustType == "hintLevel":
        try:
            newValue = int(newValue)
        except ValueError:
            raise ErrorMessage("Invalid hint level: %s"%(newValue))
        if newValue > len(answer.question.hints):
            raise ErrorMessage("Hint level too high: %d/%d"%(newValue, len(answer.question.hints)))
        answer.hintCount = newValue
        answer.update()
    elif adjustType == 'score':
        try:
            newValue = int(newValue)
        except ValueError:
            raise ErrorMessage("Invalid score: %s"%(newValue))
        answer.score = newValue
        answer.update()
    elif adjustType == 'mark':
        if newValue == "true":
            mark = True
        elif newValue == "false":
            mark = False
        else:
            raise ErrorMessage("Invalid true/false: %s"%(newValue))
        answer.mark(mark, 0)
    else:
        raise ErrorMessage("Unknown command: %s"%(adjustType))


@sections.registerSectionHandler("answerQueue")
class AdminAnswersHandler(sections.SectionHandler):
    def __init__(self):
        super().__init__()
        self.requireAdmin = True

    def requestSection(self, requestor, sectionId):
        return requestor.admin.renderAnswerQueue(sectionId)

    def requestUpdateList(self, requestor):
        return requestor.admin.getAnswerQueueEntries()
