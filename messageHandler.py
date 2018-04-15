import datetime
from threading import Lock
import json
from collections import OrderedDict

from globalItems import ErrorMessage

def setMessageFile(file):
    print("Logging messages to %s"%(file.name))
    Command.logFile = file

def importMessages(inputFile):
    from teams import teamList
    for line in inputFile:
        messageDict = json.loads(line)
        if "team" in messageDict:
            try:
                team = teamList.getTeam(messageDict["team"])
            except ErrorMessage:
                team = None
                #raise ErrorMessage("Invalid team in message file: %s" % (messageDict["team"]))
        else:
            team = None
        if "admin" in messageDict:
            admin = True
        else:
            admin = False
        time = datetime.datetime.strptime(messageDict["time"], "%Y-%m-%dT%H:%M:%S.%f")
        sendDummyMessage(messageDict["message"], messageDict["messageList"], team, admin, time)

# TODO: this is asking for trouble... Think of a better way of doing this!
def sendDummyMessage(message, messageList, team=None, admin=False, time = None):
    if message in commands:
        class DummyServer:
            def __init__(self, team, admin):
                self.team = team
                self.admin = admin
            def write_message(self, _message, _binary=False): pass
            def sendRefresh(self): pass

        server = DummyServer(team, admin)
        if not time:
            time = datetime.datetime.now()
        commands[message].checkAndRun(server, messageList, time)
    else:
        raise ErrorMessage("Invalid command: %s"%(message))

class MessagingClients:
    def __init__(self):
        self.clients = []

    def addClient(self, client):
        self.clients.append(client)
        if client.team:
            client.team.messagingClients.append(client)
        if client.admin:
            client.admin.messagingClients.append(client)

    def removeClient(self, client):
        if client.team and (client in client.team.messagingClients):
            client.team.messagingClients.remove(client)
        if client.admin and (client in client.admin.messagingClients):
            client.admin.messagingClients.remove(client)
        if client in self.clients:
            self.clients.remove(client)

clients = MessagingClients()

def handleMessage(server, message):
    mList = message.split()
    if mList:
        if mList[0] in commands:
            commands[mList[0]].checkAndRun(server, mList[1:], datetime.datetime.now())
        else:
            raise ErrorMessage("Unknown command: %s"%(mList[0]))

commands = {}

class Command:
    logFile = None
    logLock = Lock()

    def __init__(self, name, logMessage, function, messageListLen, teamRequired, adminRequired):
        self.name = name
        self.logMessage = logMessage
        self.function = function
        self.messageListLen = messageListLen
        self.teamRequired = teamRequired
        self.adminRequired = adminRequired

    def checkAndRun(self, server, messageList, time):
        if self.messageListLen >= 0:
            if len(messageList) != self.messageListLen:
                raise ErrorMessage("Invalid parameters for %s: %d required"%(self.name, self.messageListLen))
        if self.teamRequired and not server.team:
            raise ErrorMessage("Cannot do %s if you're not logged in as a team"%(self.name))
        if self.adminRequired and not server.admin:
            raise ErrorMessage("Cannot do %s if you're not admin"%(self.name))

        if self.logMessage:
            self.log(server, messageList, time)

        try:
            if self.teamRequired and server.team:
                with server.team.lock:
                    self.function(server, messageList, time)
            else:
                self.function(server, messageList, time)
        except ErrorMessage as ex:
            server.write_message("Error: %s"%(ex.message))

    def log(self, server, messageList, time):
        sObject = OrderedDict((("time", time.isoformat()), 
                               ("message", self.name),
                               ("messageList", messageList)))
        if server.team:
            sObject["team"] = server.team.name
        if server.admin:
            sObject["admin"] = True
        
        json.dump(sObject, Command.logFile)
        Command.logFile.write("\n")
        Command.logFile.flush()

def handleCommand(command, messageListLen=-1, teamRequired=False, adminRequired=False, logMessage=True):
    def handleCommandInt(function):
        commands[command] = Command(command, logMessage, function, messageListLen, teamRequired, adminRequired)
        return function
    return handleCommandInt

@handleCommand("ping", logMessage=False)
def ping(server, _messageList, _time):
    server.write_message("pong")

@handleCommand("subAnswer", 2, teamRequired=True)
def submitAnswer(server, messageList, time):
    server.team.submitAnswer(messageList[0], messageList[1], time)

@handleCommand("reqHint", 1, teamRequired=True)
def reqHint(server, messageList, _time):
    server.team.requestHint(messageList[0])
