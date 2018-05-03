from threading import Lock
import json
import collections

class Question:
    nextId = 0
    def __init__(self, dictionary):
        self.name = ""
        self.question = ""
        self.answers = []
        self.hints = []
        self.hintCost = 0
        self.__dict__ = dictionary
        if not (hasattr(self, "name") and
                hasattr(self, "question") and
                hasattr(self, "answers") and
                hasattr(self, "hints")):
            raise ValueError("Invalid question dictionary: %s"%(dictionary))
        for hint in self.hints:
            if "cost" not in hint:
                hint["cost"] = self.hintCost
        self.id = Question.nextId
        Question.nextId += 1
        # TODO: Check dictionary loaded right!

    def toJson(self):
        return json.dumps(self.__dict__, indent=4)

class QuestionList:
    def __init__(self):
        self.questionList = collections.OrderedDict()
        self.lock = Lock()

    def importQuestions(self, jsonFile):
        with self.lock:
            with open(jsonFile, "r") as f:
                questionContent = json.load(f)
            for question in questionContent:
                print(question)
                q = Question(question)
                self.questionList[q.name] = q
