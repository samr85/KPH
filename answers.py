from threading import Lock
import datetime
import collections
import tornado

from globalItems import ErrorMessage
import sections

from controller import CTX

SECTION_LOADER = tornado.template.Loader("www/sections")
INCORRECT = 0
SUBMITTED = 1
CORRECT = 2

class Answer:
    nextID = [0]
    idLock = Lock()

    def __init__(self, question, team):
        with self.idLock:
            self.id = self.nextID[0]
            self.nextID[0] += 1
        self.question = question
        self.team = team
        self.status = INCORRECT
        self.previousAnswers = []
        self.hintCount = 0
        self.answer = ""
        self.answeredTime = datetime.datetime.now()
        self.version = 1
        self.score = 0
        self.enabled = False

    def correct(self):
        return self.status == CORRECT

    def canSubmitAnswer(self):
        return self.status == INCORRECT and self.enabled

    def canRequestHint(self):
        return self.canSubmitAnswer() and len(self.question.hints) > self.hintCount and self.enabled

    def awaitingAnswer(self):
        return self.status == SUBMITTED

    def update(self):
        # Team structure holding this should already be locked
        self.version += 1
        sections.pushSection("question", self.question.id, self.team)
        sections.pushSection("answerQueue", self.id)

    def submitAnswer(self, answer, time):
        if not self.enabled:
            raise ErrorMessage("Cannot submit answer to disabled question")
        if self.status == INCORRECT:
            self.answer = answer
            CTX.answerQueue.queueAnswer(self)
            self.status = SUBMITTED
            if time:
                self.answeredTime = time
            else:
                self.answeredTime = datetime.datetime.now()
            self.update()
        else:
            raise ErrorMessage("Can't submit an answer to an already answered question!")

    def mark(self, mark, score):
        # Admins should still be able to mark questions once they've been disabled if the user submitted an answer before the question was disabled
        if mark:
            self.status = CORRECT
            self.team.notifyTeam("%s answer: CORRECT!"%(self.question.name))
            if score == 0:
                self.score = self.question.score
            else:
                self.score = score
            self.question.completed(self.team)
        else:
            self.status = INCORRECT
            self.team.notifyTeam("%s answer: INCORRECT :("%(self.question.name))
            self.previousAnswers.append(self.answer)
        self.update()

    def renderQuestion(self):
        version = self.version
        html = SECTION_LOADER.load("question.html").generate(answer=self)
        return (version, self.question.id, html)

    def renderAnswerQueue(self):
        if self.awaitingAnswer():
            version = self.version
            html = SECTION_LOADER.load("answerQueue.html").generate(answer=self)
            return (version, self.answeredTime.isoformat(), html)
        print("ERROR: requesting admin answer for one that isn't awaiting an answer")
        return (self.version, 0, None)

    def requestHint(self):
        if self.correct():
            raise ErrorMessage("Attempting to request a hint for an already correct question")
        if self.hintCount < len(self.question.hints):
            self.hintCount += 1
            self.team.notifyTeam("Hint for question %s unlocked"%(self.question.name))
            self.update()
        else:
            raise ErrorMessage("All hints already requested")

    def requestAllHints(self):
        if not self.correct():
            self.hintCount = len(self.question.hints)
            self.update()

    def getCurrentHintCost(self):
        hintCost = 0
        for hintNo in range(self.hintCount):
            hintCost += self.question.hints[hintNo]["cost"]
        return hintCost

    def getScore(self):
        if self.status == CORRECT:
            hintCost = self.getCurrentHintCost()
            if self.score > hintCost:
                return self.score - hintCost
        return 0

class AnswerSubmissionQueue:
    answerList = collections.deque()

    def __init__(self):
        self.lock = Lock()

    def queueAnswer(self, newAnswer):
        with self.lock:
            for answer in self.answerList:
                if answer.team == newAnswer.team:
                    raise ErrorMessage("Cannot submit another answer until your previous one has been marked (answer: %s pending for question: %s)" % (answer.answer, answer.question.name))
            self.answerList.append(newAnswer)

    def markAnswer(self, teamName, questionId, mark, value=0):
        found = False
        with self.lock:
            for answer in self.answerList:
                if answer.team.name == teamName and answer.question.id == questionId:
                    found = answer
                    self.answerList.remove(answer)
                    break
        if found:
            # Can't lock team while we have the answerSubQueue lock
            with found.team.lock:
                found.mark(mark, value)
        else:
            raise ErrorMessage("Answer not found to mark!")

    def renderEntry(self, answerId):
        try:
            answerId = int(answerId)
        except ValueError:
            print("Error: invalid answerid: %s", answerId)
            return (0, 0, None)
        with self.lock:
            for answer in self.answerList:
                if answer.id == answerId:
                    return answer.renderAnswerQueue()
        # Question no longer in the answer queue, so remove from the page
        return (0, 0, None)

    def getEntries(self):
        entriesList = []
        with self.lock:
            for answer in self.answerList:
                entriesList.append((answer.id, answer.version))
        return entriesList
