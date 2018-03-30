from threading import Lock
import datetime
import collections
import tornado

from globalItems import ErrorMessage
import sections
import admin

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

    def correct(self):
        return self.status == CORRECT

    def canSubmitAnswer(self):
        return self.status == INCORRECT

    def canRequestHint(self):
        return self.canSubmitAnswer() and len(self.question.hints) > self.hintCount

    def awaitingAnswer(self):
        return self.status == SUBMITTED

    def update(self):
        # Team structure holding this should already be locked
        self.version += 1
        sections.pushSection(self.team.messagingClients, "question", self.question.name)
        sections.pushSection(admin.adminList.messagingClients, "answerQueue", self.id)

    def submitAnswer(self, answer):
        if self.status == INCORRECT:
            self.answer = answer
            answerQueue.queueAnswer(self)
            self.status = SUBMITTED
            self.answeredTime = datetime.datetime.now()
            self.update()
        else:
            raise ErrorMessage("Can't submit an answer to an already answered question!")

    def mark(self, mark):
        if mark:
            self.status = CORRECT
            self.team.notifyTeam("%s answer: CORRECT!"%(self.question.name), refreshAnswer = self)
        else:
            self.status = INCORRECT
            self.team.notifyTeam("%s answer: INCORRECT :("%(self.question.name), refreshAnswer = self)
            self.previousAnswers.append(self.answer)
        self.update()

    def renderQuestion(self):
        version = self.version
        html = SECTION_LOADER.load("question.html").generate(answer=self)
        return (version, html)

    def renderAnswerQueue(self):
        if self.awaitingAnswer():
            version = self.version
            html = SECTION_LOADER.load("answerQueue.html").generate(answer=self)
            return (version, html)
        else:
            print("ERROR: requesting admin answer for one that isn't awaiting an answer")
            return (self.version, None)

    def requestHint(self):
        if self.hintCount < len(self.question.hints):
            self.hintCount += 1
            self.team.notifyTeam("Hint for question %s unlocked"%(self.question.name))
            self.update()
        else:
            raise ErrorMessage("All hints already requested")

    def getScore(self):
        if self.status == CORRECT:
            return self.question.score - self.question.hintCost * self.hintCount
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

    def markAnswer(self, teamName, questionName, mark):
        found = False
        with self.lock:
            for answer in self.answerList:
                if answer.team.name == teamName and answer.question.name == questionName:
                    found = answer
                    self.answerList.remove(answer)
                    break;
        if found:
            # Can't lock team while we have the answerSubQueue lock
            with answer.team.lock:
                answer.mark(mark)
        else:
            raise ErrorMessage("Answer not found to mark!")

    def renderEntry(self, answerId):
        try:
            answerId = int(answerId)
        except ValueError:
            print("Error: invalid answerid: %s", answerId)
            return (0, None)
        with self.lock:
            for answer in self.answerList:
                if answer.id == answerId:
                    return answer.renderAnswerQueue()
        print("ERROR: answer requested for rendering %d not found", answerId)
        return (0, None)

    def getEntries(self):
        entriesList = []
        with self.lock:
            for answer in self.answerList:
                entriesList.append((answer.id, answer.version))
        return entriesList


answerQueue = AnswerSubmissionQueue()
