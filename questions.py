from threading import Lock
import json
import collections

from globalItems import ErrorMessage

class Question:
    nextId = 0
    def __init__(self, dictionary):
        self.name = ""
        self.question = ""
        self.answers = []
        self.hints = []
        self.__dict__ = dictionary
        if not (hasattr(self, "name") and
                hasattr(self, "question") and
                hasattr(self, "answers") and
                hasattr(self, "hints")):
            raise ValueError("Invalid question dictionary: %s"%(dictionary))
        self.id = Question.nextId
        Question.nextId += 1
        # TODO: Check dictionary loaded right!

    def toJson(self):
        return json.dumps(self.__dict__, indent = 4)

    def displayQuestionToTeam(self):
        retStr = ""
        retStr += "Question: %s <br />"%(self.name)
        retStr += self.question + "<br />"
        return retStr

    def displayHintsToTeam(self, team, hintsRequested, allowRequest):
        if hintsRequested > len(self.hints) or hintsRequested < 0:
            raise ErrorMessage("Invalid number of requested hints: %d"%(hintsRequested))
        retStr = ""
        if hintsRequested:
            retStr += "Requested hints: <br />"
            for hintNum in range(hintsRequested):
                retStr += "Hint %d: %s<br />"%(hintNum, self.hints[hintNum]["hint"])
        if allowRequest and hintsRequested < len(self.hints):
            retStr += "<button onclick='sendMessage(\"reqHint %s\")'>Request Hint</button><br />"%(self.name)
        return retStr

class QuestionList:
    def __init__(self, jsonFile):
        self.questionList = collections.OrderedDict()
        self.lock = Lock()
        with self.lock:
            with open(jsonFile, "r") as f:
                questionContent = json.load(f)
            for question in questionContent:
                print(question)
                q = Question(question)
                self.questionList[q.name] = q

questionList = QuestionList("questionList.txt")
