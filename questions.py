from threading import Lock
import json
import collections

class Question:
    nextId = 0
    def __init__(self):
        self.name = self.__class__.__name__.replace("_", " ")
        self.question = ""
        self.score = 10
        self.answers = []
        self.hints = []
        for hint in self.hints:
            if "cost" not in hint:
                hint["cost"] = self.hintCost
        self.id = str(Question.nextId)
        Question.nextId += 1
        # TODO: Check dictionary loaded right!

    def addHint(self, hintHTML, cost = 2):
        """ Adds a hint to the question"""
        self.hints.append({"hint": hintHTML, "cost": cost})

    def toJson(self):
        return json.dumps(self.__dict__, indent=4)

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
