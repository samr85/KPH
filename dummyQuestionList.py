# pylint: disable=invalid-name
# Class names are used as the question names, so need to be correct
from questions import Question, registerQuestion

@registerQuestion
class name_of_question(Question):
    def __init__(self):
        super().__init__()
        self.question = "what is 1+1?"
        self.answers = ["2", "a window"]
        self.score = 5
        self.defaultHintCost = 2
        self.addHint("Use a calculator")
        self.addHint("1 less than 3", 5)

    def completed(self, team):
        for answer in team.questionAnswers.values():
            if answer.enabled and not answer.correct():
                answer.requestAllHints()
        super().completed(team)


@registerQuestion
class dependentOn1(Question):
    def __init__(self):
        super().__init__()
        self.question = "what is 2+2"
        self.answers.append("4")
        self.unlockOn = name_of_question

@registerQuestion
class Q2(Question):
    def __init__(self):
        super().__init__()
        self.name = "<i>4</i>!"
        self.addHint("the answer is: <img src='static/dummyQuestions/4.jpg' />")
        self.answers.append("24")

@registerQuestion
class finalQuestion(Question):
    def __init__(self):
        super().__init__()
        self.name = "final question"
        self.addHint("11111", 5)
        self.addHint("22222")
        self.score = 20
        self.unlockOn = "finalQuestion"
