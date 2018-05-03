import json
from collections import OrderedDict
from threading import Lock

from globalItems import ErrorMessage

commands = {}

def setMessageFile(file):
    print("Logging messages to %s"%(file.name))
    Command.logFile = file

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
