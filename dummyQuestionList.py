from questions import Question, registerQuestion

@registerQuestion
class name_of_question(Question):
    def __init__(self):
        super().__init__()
        self.question = "what is 1+1?"
        self.answers = ["2", "a window"]
        self.score = 10
        self.defaultHintCost = 2
        self.addHint("Use a calculator")
        self.addHint("1 less than 3", 5)

@registerQuestion
class dependentOn1(Question):
    def __init__(self):
        super().__init__()
        self.question = "what is 2+2"
        self.answers.append("4")
        self.unlockOn = name_of_question
        self.score = 10

@registerQuestion
class Q2(Question):
    def __init__(self):
        super().__init__()
        self.name = "<i>4</i>!"
        self.addHint("the answer is: <img src='static/dummyQuestions/4.jpg' />")
        self.answers.append("24")
