import answers 
from messageHandler import handleCommand
from globalItems import ErrorMessage

class AdminList:
    def __init__(self):
        self.messagingClients = []

    def messageAdmin(self, message):
        for client in self.messagingClients:
            client.write_message(message)

    def renderAnswerQueue(self, answerId):
        return answers.answerQueue.renderEntry(answerId)

    def getAnswerQueueEntries(self):
        return answers.answerQueue.getEntries()

adminList = AdminList()

@handleCommand("markAnswer", adminRequired=True)
def markAnswer(server, messageList):
    # messageList = teamName questionName correct/incorrect [mark]
    if len(messageList) == 3:
        answers.answerQueue.markAnswer(messageList[0], messageList[1], messageList[2].lower() == "correct", 0)
    elif len(messageList) == 4:
        answers.answerQueue.markAnswer(messageList[0], messageList[1], messageList[2].lower() == "correct", messageList[3])
    else:
        raise ErrorMessage("Incorrect number of parameters to markAnswer (got %d)!"%(len(messageList)))