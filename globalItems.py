import datetime
import tornado
import os

class ErrorMessage(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

startTime = datetime.datetime.now()
SECTION_LOADER = tornado.template.Loader(os.path.join("www", "sections"))
