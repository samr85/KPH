import base64
import abc
from commandRegistrar import handleCommand
import tornado

# Sections are the way for list of items on the page to be always kept in sync with what they should show automatically.

# Create a new instalce of this class, and overload the 2 abstractmethod functions.  Register the class using @registerSectionHandler("nameOfSection")
class SectionHandler(abc.ABC):
    def __init__(self):
        self.requireTeam = False
        self.requireAdmin = False
        self.requestors = []

    def registerForUpdates(self, requestor):
        """Request future updates for this type of message"""
        if requestor not in self.requestors:
            self.requestors.append(requestor)

    def getRequestors(self, requestorSubset):
        """Return the subset of requestors that matches requestorSubset.
           Builtin implementation filters on "admin" or team class, can be
           overwritten to do other filtering"""
        # If a team is required, then we must know what team it is
        # otherwise, just filter if we've been given something to filter on
        if self.requireTeam:
            return [x for x in self.requestors if x.team == requestorSubset]

        if not requestorSubset:
            return self.requestors
        if requestorSubset == "admin":
            return [x for x in self.requestors if x.admin]
        else:
            return [x for x in self.requestors if x.team == requestorSubset]

    @abc.abstractmethod
    def requestUpdateList(self, requestor):
        # This function is called by the browser when it wants to know if there is any additional information to look up.
        #return [(id, version), ...]
        return []

    @abc.abstractmethod
    def requestSection(self, requestor, sectionId):
        #return (version, sortValue, content)
        return None

sectionHandlers = {}

def registerSectionHandler(sectionId):
    """Register this class as a handler for the named section"""
    def registerSectionHandlerInt(handlerClass):
        sectionHandlers[sectionId] = handlerClass()
        return handlerClass
    return registerSectionHandlerInt

class InvalidRequest(Exception):
    pass

def getSectionHandler(sectionName):
    if sectionName not in sectionHandlers:
        raise InvalidRequest("Unknown section: %s"%(sectionName))
    return sectionHandlers[sectionName]

def getCheckSectionHandler(sectionName, requestor):
    sectionReqHandler = getSectionHandler(sectionName)
    if sectionReqHandler.requireTeam and not requestor.team:
        raise InvalidRequest("Team required")
    if sectionReqHandler.requireAdmin and not requestor.admin:
        raise InvalidRequest("Admin required")
    return sectionReqHandler

def pushSection(sectionName, sectionId, requestorSubset=None):
    sectionReqHandler = getSectionHandler(sectionName)
    requestors = sectionReqHandler.getRequestors(requestorSubset)
    if not requestors:
        return
    (version, sortValue, html) = sectionReqHandler.requestSection(requestors[0], str(sectionId))
    if not html:
        html = b''
    for requestor in requestors:
        try:
            requestor.write_message("updateSection %s %s %s %s %s"%(sectionName, str(sectionId), version, sortValue,
                                                                    base64.b64encode(html).decode()))
        except tornado.websocket.WebSocketClosedError:
            print("Cannot send push for %s, socket closed"%(sectionName))

@handleCommand("UpdateSectionListRequest", logMessage=False)
def updateSectionListRequest(requestor, messageList, _time):
    # [type]
    try:
        sectionList = []
        for sectionReq in messageList:
            sectionReqHandler = getCheckSectionHandler(sectionReq, requestor)
            sectionReqHandler.registerForUpdates(requestor)
            sectionEntries = sectionReqHandler.requestUpdateList(requestor)
            for entry in sectionEntries:
                if not len(entry) == 2:
                    raise InvalidRequest("id, version list not valid!!: %s"%(" ".join(str(entryItem) for entryItem in entry)))
                sectionList.append(sectionReq + " " + " ".join(str(entryItem) for entryItem in entry))
        requestor.write_message("updateSectionList " + " ".join(sectionList))
    except InvalidRequest as ex:
        requestor.write_message("Error: " + str(ex))

@handleCommand("UpdateSectionRequest", 2, logMessage=False)
def updateSectionRequest(requestor, messageList, _unusedTime):
    # type, id
    try:
        sectionReq = messageList[0]
        sectionId = messageList[1]
        sectionReqHandler = getCheckSectionHandler(sectionReq, requestor)
        (version, sortValue, html) = sectionReqHandler.requestSection(requestor, sectionId)
        if not html:
            html = b''
        requestor.write_message("updateSection %s %s %s %s %s"%(sectionReq, sectionId, version, sortValue,
                                                                base64.b64encode(html).decode()))
    except InvalidRequest as ex:
        requestor.write_message("Error: " + str(ex))

@registerSectionHandler("question")
class QuestionSectionHandler(SectionHandler):
    def __init__(self):
        super().__init__()
        self.requireTeam = True

    def requestSection(self, requestor, sectionId):
        (version, sortValue, html) = requestor.team.renderQuestion(sectionId)
        if version == 0:
            raise InvalidRequest("Question name %s not available to team"%(sectionId))
        return (version, sortValue, html)

    def requestUpdateList(self, requestor):
        versionList = []
        for answer in requestor.team.questionAnswers.values():
            versionList.append((answer.question.id, answer.version))
        return versionList

@registerSectionHandler("answerQueue")
class AdminAnswersHandler(SectionHandler):
    def __init__(self):
        super().__init__()
        self.requireAdmin = True

    def requestSection(self, requestor, sectionId):
        return requestor.admin.renderAnswerQueue(sectionId)

    def requestUpdateList(self, requestor):
        return requestor.admin.getAnswerQueueEntries()

@registerSectionHandler("message")
class TeamMessageLogHandler(SectionHandler):
    def __init__(self):
        super().__init__()

    def requestSection(self, requestor, sectionId):
        try:
            msgIndex = int(sectionId)
            if requestor.team:
                message = requestor.team.messages[msgIndex]
            elif requestor.admin:
                message = requestor.admin.messages[msgIndex]
            else:
                raise InvalidRequest("Not a team or admin, so no messages to request")
        except IndexError:
            if requestor.team:
                raise InvalidRequest("Requested non-existent team message: %s/%d"%(sectionId, len(requestor.team.messages))) from None
            if requestor.admin:
                raise InvalidRequest("Requested non-existent admin message: %s/%d"%(sectionId, len(requestor.admin.messages))) from None
        except ValueError:
            raise InvalidRequest("message number %s is not an integeter"%(sectionId)) from None
        if hasattr(message, "encode"):
            message = message.encode()
        return (1, msgIndex, message)

    def requestUpdateList(self, requestor):
        versionList = []
        if requestor.team:
            max = len(requestor.team.messages)
        elif requestor.admin:
            max = len(requestor.admin.messages)
        else:
            max = 0

        for i in range(max):
            versionList.append((i, 1))
        return versionList