from threading import Lock
import json
import collections

from controller import CTX

class Question:
    """ Class holding the questions for the hunt.
        Wrap question classes in @registerQuestion"""
    _nextId = 0
    def __init__(self):
        # The name of the questions, is displayed to the user
        self.name = self.__class__.__name__.replace("_", " ")
        # The text of the questions, displays to the user if set
        self.question = ""
        # How many points are scored for getting the question correct
        # 0 means force the admin to enter a score when marking it
        self.score = 5
        # If the hint cost isn't specified for individual hints, they cost this much
        self.defaultHintCost = 1
        # List of the valid answers to the question
        self.answers = []
        # When the question unlocks.  This should be set to either another question,
        #  or something that is compared against in huntSpecific code
        self.unlockOn = "initial"
        # HTML template to use to display this question
        self.HTMLTemplate = "questionDisplay.html"
        # HTML template to use to display for marking
        self.HTMLMarkTemplate = "questionMark.html"

        ## Do not modify these
        # List of hints - modify using addHint()
        self.hints = []
        # Id for the question, used for communicating with clients
        self.id = str(Question._nextId)
        Question._nextId += 1

    def addHint(self, hintHTML, cost=-1):
        """ Adds a hint to the question"""
        if cost == -1:
            cost = self.defaultHintCost
        self.hints.append({"hint": hintHTML, "cost": cost})

    def toJson(self):
        """ For debugging questions, prints the question details """
        return json.dumps(self.__dict__, indent=4)

    def completed(self, team):
        """ Called when the question is marked correct to unlock dependent questions.
            Overload and call super().complete(team) if you want to do more """
        for question in QuestionList.questionList.values():
            if question.unlockOn == self.__class__:
                print("unlocking %s for team %s"%(question.name, team.name))
                CTX.enableQuestion(question, team)

    def submitAnswer(self, answer):
        """ Overload if you want something special to happen when an answer is submitted """
        pass

    def submissionCheck(self, answer, answerString, currentTime):
        """ Overload this if there might be a special reason that answers (or a specific answer) can't be submitted.  Reply with a string to refuse submission """
        return None

class QuestionList:
    """ A container holding of all questions in the hunt """
    questionList = collections.OrderedDict()
    lock = Lock()

    @staticmethod
    def registerQuestion(question):
        newQ = question()
        with QuestionList.lock:
            QuestionList.questionList[newQ.name] = newQ
        return question

registerQuestion = QuestionList.registerQuestion
