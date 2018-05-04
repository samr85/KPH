import base64
import abc
from commandRegistrar import handleCommand
from globalItems import ErrorMessage

class SectionHandler(abc.ABC):
    def __init__(self):
        self.requireTeam = False
        self.requireAdmin = False
        self.requestors = []

    def registerForUpdates(self, requestor):
        if requestor not in self.requestors:
            self.requestors.append(requestor)

    def getRequestors(self, requestorTeam):
        # Should this have other filters beyond just the team?
        if not self.requireTeam:
            return self.requestors
        if not requestorTeam:
            raise ErrorMessage("getRequestors called with a required team, but no team given")
        reqs = []
        for req in self.requestors:
            if req.team == requestorTeam:
                reqs.append(req)
        return reqs

    @abc.abstractmethod
    def requestUpdateList(self, requestor):
        #return [(id, version), ...]
        return []

    @abc.abstractmethod
    def requestSection(self, requestor, sectionId):
        #return (version, sortValue, content)
        return None

sectionHandlers = {}

def registerSectionHandler(sectionId):
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
        requestor.write_message("updateSection %s %s %s %s %s"%(sectionName, str(sectionId), version, sortValue,
                                                                base64.b64encode(html).decode()))

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
        requestor.write_message("error " + str(ex))

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
        requestor.write_message("error " + str(ex))

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
