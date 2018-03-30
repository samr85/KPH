import datetime

class ErrorMessage(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

startTime = datetime.datetime.now()
