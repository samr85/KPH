from KPH import ErrorMessage
import KPH

def handleMessage(server, message):
    mList = message.split()
    if len(mList):
        if mList[0] in commands:
            commands[mList[0]].checkAndRun(server, mList[1:])
        else:
            raise ErrorMessage("Unknown command: %s"%(mList[0]))

commands = {}

class Command:
    def __init__(self, name, function, messageListLen, teamRequired, adminRequired):
        self.name = name
        self.function = function
        self.messageListLen = messageListLen
        self.teamRequired = teamRequired
        self.adminRequired = adminRequired

    def checkAndRun(self, server, messageList):
        if self.messageListLen >=0:
            if len(messageList) != self.messageListLen:
                raise ErrorMessage("Invalid parameters for %s: %d required"%(self.name, self.messageListLen))
        if self.teamRequired and not server.team:
            raise ErrorMessage("Cannot do %s if you're not logged in as a team"%(self.name))
        if self.adminRequired and not server.admin:
            raise ErrorMessage("Cannot do %s if you're not admin"%(self.name))

        try:
            self.function(server, messageList)
        except ErrorMessage as e:
            server.write_message("Error: %s"%(e.message))

def handleCommand(command, messageListLen = -1, teamRequired = False, adminRequired = False):
    def int(function):
        commands[command] = Command(command, function, messageListLen, teamRequired, adminRequired)
        return function
    return int 

# These aren't used any more - for testing only, remove for production, or make admin only
@handleCommand("createTeam", 1)
def createTeam(server, messageList):
    server.team = KPH.teamList.createTeam(messageList[0])
@handleCommand("team", 1)
def team(server, messageList):
    server.team = KPH.teamList.getTeam(messageList[0])
@handleCommand("print")
def print(server, messageList):
    if server.team:
        server.write_message("team: %s"%server.team.name)
    else:
        server.write_message("no team")
###### end superfluous function

@handleCommand("subAnswer", 2, teamRequired = True)
def submitAnswer(server, messageList):
    server.team.submitAnswer(messageList[0], messageList[1])

@handleCommand("reqHint", 1, teamRequired = True)
def reqHint(server, messageList):
    server.team.requestHint(messageList[0])

@handleCommand("markAnswer", 3, adminRequired = True)
def markAnswer(server, messageList):
    if messageList[2] == "correct":
        mark = True
    else:
        mark = False
    KPH.answerQueue.markAnswer(messageList[0], messageList[1], mark)
    server.sendRefresh()