from threading import Lock
import datetime
import collections

from globalItems import ErrorMessage, SECTION_LOADER
import sections
from questions import RoundQuestion

from controller import CTX

INCORRECT = 0
SUBMITTED = 1
CORRECT = 2

class Answer:
    """ Class linking a team to a question.  Holds what they've done to it, eg requesting hints, submitting answers """
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
        sections.pushSection("adminQuestion", self.question.id, self.team.name)
        sections.pushSection("adminQuestionViewer", self.question.id)
        sections.pushSection("answerQueue", self.id)
        ## hack - this shouldn't happen this often...
        # also, if the score board changes so it's only updated one team at a time, the 1 should become self.team.name
        sections.pushSection("scoreBoard", 1)

    def submitAnswer(self, answerString, time):
        if not self.enabled:
            raise ErrorMessage("Cannot submit answer to disabled question")
        msg = self.question.submissionCheck(self, answerString, time)
        if msg:
            raise ErrorMessage(msg)
        if self.status == INCORRECT:
            self.answer = answerString.upper().replace(" ", "")
            CTX.answerQueue.queueAnswer(self)
            self.status = SUBMITTED
            if time:
                self.answeredTime = time
            else:
                self.answeredTime = datetime.datetime.now()
            self.question.submitAnswer(self)
            self.update()
        else:
            raise ErrorMessage("Can't submit an answer to an already answered question!")

    def mark(self, mark, score):
        # Admins should still be able to mark questions once they've been disabled if the user submitted an answer before the question was disabled
        if mark:
            self.status = CORRECT
            if score == 0:
                self.score = self.question.score
            else:
                self.score = score
            self.question.completed(self.team)
        else:
            self.status = INCORRECT
            if self.answer not in self.previousAnswers:
                self.previousAnswers.append(self.answer)
        self.question.markNotification(self)
        self.update()

    def renderQuestion(self, admin=False):
        """ Create the HTML to display this to the user """
        version = self.version
        html = SECTION_LOADER.load(self.question.htmlTemplate).generate(answer=self, admin=admin)
        html = html.replace(b"\n", b"")
        return (version, self.question.id, html)

    def renderAnswerQueue(self):
        """ Create the HTML to display this to an admin """
        if self.awaitingAnswer():
            version = self.version
            html = SECTION_LOADER.load(self.question.htmlMarkTemplate).generate(answer=self)
            return (version, self.answeredTime.isoformat(), html)
        print("ERROR: requesting admin answer for one that isn't awaiting an answer")
        return (self.version, 0, None)

    def requestHint(self):
        if self.correct():
            raise ErrorMessage("Attempting to request a hint for an already correct question")
        if self.hintCount < len(self.question.hints):
            self.hintCount += 1
            self.team.notifyTeam("Hint for puzzle %s unlocked"%(self.question.name))
            self.update()

        else:
            raise ErrorMessage("All hints already requested")

    def requestAllHints(self):
        """ Admin function to mark all hints as requested """
        if not self.correct():
            self.hintCount = max(0,len(self.question.hints)-1, self.hintCount)
            
            self.update()

    def getCurrentHintCost(self):
        hintCost = 0
        for hintNo in range(self.hintCount):
            hintCost += self.question.hints[hintNo]["cost"]
        return hintCost

    def getScore(self):
        """ Return how many points this question is worth """
        if self.status == CORRECT:
            hintCost = self.getCurrentHintCost()
            if self.score > hintCost:
                return self.score - hintCost
        return 0

class AnswerSubmissionQueue:
    """ A list of answers that teams have submitted for answering """
    answerList = collections.deque()

    def __init__(self):
        self.lock = Lock()

    def queueAnswer(self, newAnswer):
        """ Team is wanting a question to be marked """
        with self.lock:
            for answer in self.answerList:
                if answer.team == newAnswer.team:
                    raise ErrorMessage("Cannot submit another answer until your previous one has been marked (answer: %s pending for question: %s)" % (answer.answer, answer.question.name))
            self.answerList.append(newAnswer)

    def markAnswer(self, teamName, questionId, mark, value=0):
        """ Admin has replied to the mark request """
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
        """ Make the sectionHTML for showing this answer request to admins """
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
        """ Get a list of all the answer requests """
        entriesList = []
        with self.lock:
            for answer in self.answerList:
                entriesList.append((answer.id, answer.version))
        return entriesList
