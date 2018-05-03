from questions import Question, registerQuestion

#Question defaults:
# score: 10
# hintCost: 2

@registerQuestion
class name_of_question(Question):
    def __init__(self):
        super().__init__()
        self.question = "what is 1+1?"
        self.addHint("Use a calculator")
        self.addHint("1 less than 3", 5)
        self.answers = ["2", "a window"]
        # leaving score at the default of 10

@registerQuestion
class Q2(Question):
    def __init__(self):
        super().__init__()
        self.name = "<i>4</i>!"
        self.addHint("the answer is: <img src='static/dummyQuestions/4.jpg' />")
        self.answers.append("24")
