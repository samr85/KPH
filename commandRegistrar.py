import json
from collections import OrderedDict
from threading import Lock

from globalItems import ErrorMessage

commands = {}

# Called to initialise command message logging
def setMessageFile(file):
    print("Logging messages to %s"%(file.name))
    Command.logFile = file

# Class responsible for running @handleCommand functions
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

#Expsects to be called as a decorator, eg:
#@handleCommand("nameSentFromBrowser", ...)
#def blah(server, messageList, timeOfCall):
#Server is used to extract team if that's specified,
# check if the user is an admin (though if adminRequired was set this has already been done)
# Reply to this specific client - probably only to be used for error messages
#messageList is a list of what data was sent by the client for this call
#timeOfCall should be used if you need to check time instead of datetime.datetime.now(), as the message might be being replayed, so this is the time of that original call
def handleCommand(command, # Name to identify this in message from the browser
                  messageListLen=-1, # Message must have been split into exactly this number of chunks - if not, an error will be returned instead
                  teamRequired=False, adminRequired=False, # mutually exclusive.  teamRequired means server.team must be set.  adminRequired means server.admin must be true.
                  logMessage=True # If set to False, then this won't be written to the logfile, so can't be replayed.
                  ):
    def handleCommandInt(function):
        commands[command] = Command(command, logMessage, function, messageListLen, teamRequired, adminRequired)
        return function
    return handleCommandInt
