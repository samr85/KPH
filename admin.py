import answers
from commandRegistrar import handleCommand
from globalItems import ErrorMessage
import sections

class AdminList:
    def __init__(self):
        self.messagingClients = []
        self.messages = []

    def messageAdmin(self, message):
        self.messages.append(message)
        sections.pushSection("message", len(self.messages) - 1, "admin")

    @staticmethod
    def renderAnswerQueue(answerId):
        return answers.answerQueue.renderEntry(answerId)

    @staticmethod
    def getAnswerQueueEntries():
        return answers.answerQueue.getEntries()

adminList = AdminList()

@handleCommand("markAnswer", adminRequired=True)
def markAnswer(_server, messageList, _time):
    # messageList = teamName questionName correct/incorrect [mark]
    if len(messageList) == 3:
        answers.answerQueue.markAnswer(messageList[0], messageList[1], messageList[2].lower() == "correct", 0)
    elif len(messageList) == 4:
        try:
            score = int(messageList[3])
        except ValueError:
            raise ErrorMessage("Invalid number for score: %s"%(messageList[3]))
        answers.answerQueue.markAnswer(messageList[0], messageList[1], messageList[2].lower() == "correct", score)
    else:
        raise ErrorMessage("Incorrect number of parameters to markAnswer (got %d)!"%(len(messageList)))
