import answers 

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