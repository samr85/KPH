import base64

from commandRegistrar import handleCommand
from globalItems import ErrorMessage, SECTION_LOADER
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

@sections.registerSectionHandler("answerQueue")
class AdminAnswersHandler(sections.SectionHandler):
    def __init__(self):
        super().__init__()
        self.requireAdmin = True

    def requestSection(self, requestor, sectionId):
        return requestor.admin.renderAnswerQueue(sectionId)

    def requestUpdateList(self, requestor):
        return requestor.admin.getAnswerQueueEntries()

@sections.registerSectionHandler("adminTeamViewer")
class AdminTeamViewer(sections.SectionHandler):
    def __init__(self):
        super().__init__()
        self.requireAdmin = True
        self.name = "adminTeamViewer"

    def requestSection(self, requestor, sectionId):
        if self.name not in requestor.sectionAdditionalInformation:
            raise ErrorMessage("You've not requested what team to view")
        teamName = requestor.sectionAdditionalInformation[self.name]
        team = CTX.teams[teamName]
        return team.renderQuestion(sectionId, admin=True)

    def requestUpdateList(self, requestor):
        if self.name not in requestor.sectionAdditionalInformation:
            raise ErrorMessage("You've not requested what team to view")
        teamName = requestor.sectionAdditionalInformation[self.name]
        team = CTX.teams[teamName]
        return team.listQuestionIdVersions()

    def getRequestors(self, team):
        return [r for r in self.requestors if r.sectionAdditionalInformation[self.name] == team.name]

@sections.registerSectionHandler("adminQuestionViewer")
class AdminQuestionViewer(sections.SectionHandler):
    def __init__(self):
        super().__init__()
        self.requireAdmin = True

    @staticmethod
    def calcVersion(question):
        return sum(answer.version for answer in question.teamAnswers)

    def requestSection(self, requestor, sectionId):
        """ Create the HTML to display this to the user """
        question = CTX.questions[sectionId]
        version = self.calcVersion(question)
        html = SECTION_LOADER.load("questionDetails.html").generate(question=question, CTX=CTX)
        return (version, sectionId, html)

    def requestUpdateList(self, requestor):
        versionList = []
        for question in CTX.questions:
            versionList.append((question.id, self.calcVersion(question)))
        return versionList
