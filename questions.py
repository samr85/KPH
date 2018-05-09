from threading import Lock
import json
import collections

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
        """ Called when the question is marked correct to unlock dependent questions"""
        from controller import CTX
        for question in QuestionList.questionList.values():
            if question.unlockOn == self.__class__:
                print("unlocking %s for team %s"%(question.name, team.name))
                CTX.enableQuestion(question, team)

class QuestionList:
    questionList = collections.OrderedDict()
    lock = Lock()

    @staticmethod
    def registerQuestion(question):
        q = question()
        with QuestionList.lock:
            QuestionList.questionList[q.name] = q
        return question

registerQuestion = QuestionList.registerQuestion
