import datetime
import tornado

class ErrorMessage(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

startTime = datetime.datetime.now()
SECTION_LOADER = tornado.template.Loader("www/sections")
