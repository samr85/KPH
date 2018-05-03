import base64
import abc
from commandRegistrar import handleCommand

class SectionHandler(abc.ABC):
    def __init__(self):
        self.requireTeam = False
        self.requireAdmin = False

    @abc.abstractmethod
    def requestUpdateList(self, server):
        #return [(id, version), ...]
        return []

    @abc.abstractmethod
    def requestSection(self, server, sectionId):
        #return (version, content)
        return None

sectionHandlers = {}

def registerSectionHandler(id):
    def registerSectionHandlerInt(handlerClass):
        sectionHandlers[id] = handlerClass()
        return handlerClass
    return registerSectionHandlerInt

class InvalidRequest(Exception):
    pass

def getSectionHandler(sectionReq, server):
    if sectionReq not in sectionHandlers:
        raise InvalidRequest("Unknown section: %d"%(sectionReq))
    sectionReqHandler = sectionHandlers[sectionReq]
    if sectionReqHandler.requireTeam and not server.team:
        raise InvalidRequest("Team required")
    if sectionReqHandler.requireAdmin and not server.admin:
        raise InvalidRequest("Admin required")
    return sectionReqHandler

def pushSection(servers, section, sectionId):
    if not servers:
        return
    sectionReqHandler = getSectionHandler(section, servers[0])
    (version, html) = sectionReqHandler.requestSection(servers[0], sectionId)
    if not html:
        html = b''
    for server in servers:
        server.write_message("updateSection %s %s %s %s"%(section, sectionId, version,
                                                          base64.b64encode(html).decode()))


@handleCommand("UpdateSectionListRequest", logMessage=False)
def updateSectionListRequest(server, messageList, _time):
    # [type]
    try:
        sectionList = []
        for sectionReq in messageList:
            sectionReqHandler = getSectionHandler(sectionReq, server)
            sectionEntries = sectionReqHandler.requestUpdateList(server)
            for entry in sectionEntries:
                if not len(entry) == 2:
                    raise InvalidRequest("id, version list not valid!!: %s"%(" ".join(str(entryItem) for entryItem in entry)))
                sectionList.append(sectionReq + " " + " ".join(str(entryItem) for entryItem in entry))
        server.write_message("updateSectionList " + " ".join(sectionList))
    except InvalidRequest as ex:
        server.write_message("error " + str(ex))

@handleCommand("UpdateSectionRequest", 2, logMessage=False)
def updateSectionRequest(server, messageList, _unusedTime):
    # type, id
    try:
        sectionReq = messageList[0]
        sectionId = messageList[1]
        sectionReqHandler = getSectionHandler(sectionReq, server)
        (version, html) = sectionReqHandler.requestSection(server, sectionId)
        if not html:
            html = b''
        server.write_message("updateSection %s %s %s %s"%(sectionReq, sectionId, version,
                                                          base64.b64encode(html).decode()))
    except InvalidRequest as ex:
        server.write_message("error " + str(ex))

@registerSectionHandler("question")
class QuestionSectionHandler(SectionHandler):
    def __init__(self):
        super().__init__()
        self.requireTeam = True

    def requestSection(self, server, sectionId):
        (version, html) = server.team.renderQuestion(sectionId)
        if version == 0:
            raise InvalidRequest("Question name %s not available to team"%(sectionId))
        return (version, html)

    def requestUpdateList(self, server):
        versionList = []
        for answer in server.team.questionAnswers.values():
            versionList.append((answer.question.name, answer.version))
        return versionList

@registerSectionHandler("answerQueue")
class AdminAnswersHandler(SectionHandler):
    def __init__(self):
        super().__init__()
        self.requireAdmin = True

    def requestSection(self, server, sectionId):
        return server.admin.renderAnswerQueue(sectionId)

    def requestUpdateList(self, server):
        return server.admin.getAnswerQueueEntries()
