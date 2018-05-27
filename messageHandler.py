import datetime
import base64
import html

from globalItems import ErrorMessage
from commandRegistrar import COMMANDS, handleCommand

# TODO: this is asking for trouble... Think of a better way of doing this!
def sendDummyMessage(message, messageList, team=None, admin=False, time=None):
    if message in COMMANDS:
        class DummyServer:
            def __init__(self, team, admin):
                self.team = team
                self.admin = admin
            def write_message(self, _message, _binary=False):
                pass
            def sendRefresh(self):
                pass

        server = DummyServer(team, admin)
        if not time:
            time = datetime.datetime.now()
        handleSplitMessage(server, message, messageList, time)
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

def handleMessage(server, message):
    mList = html.escape(message).split()
    if mList:
        handleSplitMessage(server, mList[0], mList[1:], datetime.datetime.now())

def handleSplitMessage(server, command, mList, time):
    if command in COMMANDS:
        COMMANDS[command].checkAndRun(server, mList, time)
    else:
        raise ErrorMessage("Unknown command: %s"%command)

@handleCommand("ping", logMessage=False)
def ping(server, _messageList, _time):
    server.write_message("pong")

@handleCommand("subAnswer", 2, teamRequired=True)
def submitAnswer(server, messageList, time):
    answer = html.escape(base64.b64decode(messageList[1]).decode())
    server.team.submitAnswer(messageList[0], answer, time)

@handleCommand("reqHint", 1, teamRequired=True)
def reqHint(server, messageList, _time):
    server.team.requestHint(messageList[0])
