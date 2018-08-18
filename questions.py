from threading import Lock
import json
import collections

from controller import CTX
import sections
from globalItems import SECTION_LOADER

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
        # Display the score on the scoreboard?
        self.noScore = False
        # If the hint cost isn't specified for individual hints, they cost this much
        self.defaultHintCost = 1
        # List of the valid answers to the question
        self.answers = []
        # When the question unlocks.  This should be set to either another question,
        #  or something that is compared against in huntSpecific code
        self.unlockOn = "initial"
        # HTML template to use to display this question
        self.htmlTemplate = "questionDisplay.html"
        # HTML template to use to display for marking
        self.htmlMarkTemplate = "questionMark.html"
        # Additional classes for the question
        self.htmlClasses = []

        ## Do not modify these
        # A list of the team Answer structures refering to this question
        self.teamAnswers = []
        # List of hints - modify using addHint()
        self.hints = []
        # Id for the question, used for communicating with clients
        self.id = "%03d"%(Question._nextId)
        Question._nextId += 1

    def addHint(self, hintHtml, cost=-1):
        """ Adds a hint to the question"""
        if cost == -1:
            cost = self.defaultHintCost
        self.hints.append({"hint": hintHtml, "cost": cost})

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
        answer.team.notifyTeam('Answer "%s" submitted for question "%s"'%(answer.answer, self.name))

    def submissionCheck(self, answer, answerString, currentTime):
        """ Overload this if there might be a special reason that answers (or a specific answer) can't be submitted.  Return with a string to refuse submission """
        pass

    def markNotification(self, answer):
        """ Overload this to change what messages (if any!) are sent to the user when the questions is marked """
        if answer.correct():
            answer.team.notifyTeam('Correct: Answer "%s" to question "%s" accepted'%(answer.answer, self.name), alert=True)
        else:
            answer.team.notifyTeam('Incorrect: Answer "%s" to question "%s" rejected'%(answer.answer, self.name), alert=True)

class RoundHeading(Question):
    roundName = ""
    def __init__(self):
        super().__init__()
        self.htmlTemplate = "RoundHeading.html"
        self.score = 0
        self.htmlClasses.append("roundHeading")

class RoundQuestion(Question):
    def __init__(self, roundClass):
        super().__init__()
        self.htmlClasses.append(roundClass.__name__)
        self.htmlClasses.append("roundQuestion")

class QuestionList:
    """ A container holding of all questions in the quiz """
    questionList = collections.OrderedDict()
    lock = Lock()

    @staticmethod
    def registerQuestion(question):
        newQ = question()
        with QuestionList.lock:
            QuestionList.questionList[newQ.id] = newQ
        return question

    # Make this class act as if it was a dict of questionList
    def __iter__(self):
        return self.questionList.values().__iter__()
    def __len__(self):
        return self.questionList.__len__()
    def __getitem__(self, key):
        return self.questionList.__getitem__(key)
    
    def getNames(self):
        return " ".join([question.name for question in self.questionList.values() if not(question.noScore)])

def registerQuestion(question):
    return QuestionList.registerQuestion(question)

@sections.registerSectionHandler("question")
class QuestionSectionHandler(sections.SectionHandler):
    def __init__(self):
        super().__init__()
        self.requireTeam = True

    def requestSection(self, requestor, sectionId):
        (version, sortValue, html) = requestor.team.renderQuestion(sectionId)
        if version == 0:
            raise sections.InvalidRequest("Question name %s not available to team"%(sectionId))
        return (version, sortValue, html)

    def requestUpdateList(self, requestor):
        return requestor.team.listQuestionIdVersions()

@sections.registerSectionHandler("adminQuestion")
class AdminQuestionSectionHandler(sections.SegragatedSectionHandler):
    """ Shows an editable version of a team's question entries to the admins """
    def __init__(self):
        super().__init__()
        self.requireAdmin = True

    def requestSectionSegment(self, requestor, sectionId, segment):
        team = CTX.teams[segment]
        return team.renderQuestion(sectionId, admin=True)

    def requestUpdateListSegment(self, requestor, segment):
        team = CTX.teams[segment]
        return team.listQuestionIdVersions()

@sections.registerSectionHandler("adminQuestionViewer")
class AdminQuestionViewer(sections.SectionHandler):
    """ Lists all of the questions to the admins """
    def __init__(self):
        super().__init__()
        self.requireAdmin = True

    @staticmethod
    def calcVersion(question):
        return sum(answer.version for answer in question.teamAnswers)

    def requestSection(self, requestor, sectionId):
        """ Create the HTML to display this to the user """
        question = CTX.questions[sectionId]
        version = self.calcVersion(question)
        html = SECTION_LOADER.load("questionDetails.html").generate(question=question, CTX=CTX)
        return (version, sectionId, html)

    def requestUpdateList(self, requestor):
        versionList = []
        for question in CTX.questions:
            versionList.append((question.id, self.calcVersion(question)))
        return versionList
