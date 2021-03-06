# pylint: disable=wrong-import-position, abstract-method
# pylint doesn't like modifying the path before importing local modules
import sys
import threading
import os
import argparse
import datetime
import html
import base64
import asyncio

import tornado.web
import tornado.websocket

sys.path.insert(0, "KPH")

# This must be first
from controller import CTX

from globalItems import ErrorMessage
import messageHandler
import commandRegistrar
import huntSpecific

class WSHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team = None
        self.admin = False
        self.validConnection = False
        self.sectionAdditionalInformation = {}

    def open(self): # pylint: disable=arguments-differ
        teamName = self.get_secure_cookie("team", None)
        if teamName:
            teamName = teamName.decode()
            destString = "team " + teamName
            try:
                self.team = CTX.teams[teamName]
            except ErrorMessage:
                print('ERROR: Connection opened from non-existent team: %s!'%(teamName))
                self.write_message("Error: team %s doesn't exist!!"%(teamName))
                self.sendRefresh()
                self.close()
                return
        else: # Can't be both a team and admin
            destString = "admin"
            admin = self.get_secure_cookie("admin", None)
            if admin:
                self.admin = CTX.admin
            else:
                # Correct for eg login page
                destString = "no one"
        print('MSG C : Connection from ' + destString)
        self.validConnection = True
        CTX.messagingClients.addClient(self)

    def on_message(self, message):
        try:
            if not self.validConnection:
                print("ERROR: Got message from invalid connection: " + message)
                return
            print('MSG Rx: ' + message)
            messageHandler.handleMessage(self, message)
        except ErrorMessage as ex:
            errMsg = "Error: %s"%(ex.message)
            self.write_message("alert %s"%(base64.b64encode(errMsg.encode()).decode()))
        except UnicodeError:
            print('ERROR: Rx message with invalid unicode')
            errMsg = "Error: invalid characters in message"
            self.write_message("alert %s"%(base64.b64encode(errMsg.encode()).decode()))
            return

    def on_close(self):
        CTX.messagingClients.removeClient(self)
        dest = ""
        if self.admin:
            dest = "admin"
        elif self.team:
            dest = "team " + self.team.name
        else:
            dest = "no one"
        print('MSG D : Connection closed from ' + dest)

    def write_message(self, message, binary=False):
        print("MSG Tx: " + ((message[:75] + "...") if len(message) > 78 else message))
        return super().write_message(message, binary)

    def sendRefresh(self):
        self.write_message("js: location.reload();")

# pylint really doesn't like this class, so this is to make it stop complaining
class RequestHandler(tornado.web.RequestHandler):
    def get(self): # pylint: disable=arguments-differ, useless-super-delegation
        return super().get()
    def post(self): # pylint: disable=arguments-differ, useless-super-delegation
        return super().post()

class TeamRequestHandler(RequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.team = None

    def get(self):
        teamName = self.get_secure_cookie("team")
        if not teamName:
            self.redirect("login")
            return
        teamName = teamName.decode()
        print("Request for team page for: %s"%(teamName))
        try:
            self.team = CTX.teams[teamName]
        except ErrorMessage:
            self.redirect("login")
            return
        self.getTeam()

    def getTeam(self):
        raise NotImplementedError("This function should have been overloaded!! " + self.request)

class TeamPage(TeamRequestHandler):
    def getTeam(self):
        self.render(os.path.join("www", "teampage.html"), answers=self.team.questionAnswers.values(), team=self.team)

class AdminRequestHandler(RequestHandler):
    def get(self):
        admin = self.get_secure_cookie("admin", None)
        if not admin:
            self.redirect("login")
            return
        self.getAdmin()
    def getAdmin(self):
        raise NotImplementedError("This function should have been overloaded!! " + self.request)

class AdminPage(AdminRequestHandler):
    def getAdmin(self):
        self.render(os.path.join("www", "admin.html"), CTX=CTX)

class AdminTeamViewerPage(AdminRequestHandler):
    def getAdmin(self):
        teamName = self.get_argument("teamSelect", None)
        team = CTX.teams[teamName]
        self.render(os.path.join("www", "adminTeamViewer.html"), team=team)
class AdminQuestionViewerPage(AdminRequestHandler):
    def getAdmin(self):
        self.render(os.path.join("www", "adminQuestionViewer.html"))

class ScorePage(RequestHandler):
    def get(self):
        self.render(os.path.join("www", "score.html"))
        
class TimerPage(RequestHandler):
    def get(self):
        self.render(os.path.join("www", "timer.html"))

class Login(RequestHandler):
    def get(self):
        self.clear_cookie("team")
        self.clear_cookie("admin")
        self.render(os.path.join("www", "login.html"), Errors=[], CTX=CTX)

    def post(self):
        errorMessages = []
        try:
            teamName = self.get_argument("teamSelect", None)
            password = self.get_argument("teamPassword", None)
            if not password:
                raise ErrorMessage("Please specify a password")

            if not teamName:
                # Was this an admin login?
                if password == CTX.admin.password:
                    self.set_secure_cookie("admin", "1")
                    self.redirect("/admin")
                    return
                raise ErrorMessage("Please specify a team")

            teamName = html.escape(teamName)
            # Excepts an ErrorMessage on error
            CTX.teams.getTeam(teamName, password)
            self.set_secure_cookie("team", teamName)
            self.redirect("/teampage")
            return

        except ErrorMessage as ex:
            errorMessages.append(ex.message)
        self.render(os.path.join("www", "login.html"), Errors=errorMessages, CTX=CTX)

class TestLogin(RequestHandler):
    def get(self):
        self.clear_cookie("team")
        self.clear_cookie("admin")
        self.render(os.path.join("www", "testLogin.html"), getTeamQuickLogin=self.getTeamQuickLogin, Errors=[], CTX=CTX)

    @staticmethod
    def getTeamQuickLogin():
        retHTML = ""
        for team in CTX.teams:
            retHTML += "<input name='QuickLogin' type='Submit' value='%s' /><br />"%(team.name)
        return retHTML

    def post(self):
        errorMessages = []
        try:
            if self.get_argument("QuickLogin", None):
                teamName = html.escape(self.get_argument("QuickLogin"))
                if teamName in CTX.teams:
                    self.set_secure_cookie("team", teamName)
                    self.redirect("/teampage")
                    return
                errorMessages.append("Unknown team: %s"%(teamName))
            elif self.get_argument("createTeam", None):
                teamName = html.escape(self.get_argument("teamName"))
                # Excepts on error
                messageHandler.sendDummyMessage("createTeam", [teamName])
                self.set_secure_cookie("team", teamName)
                self.redirect("/teampage")
                return
            elif self.get_argument("login", None):
                teamName = html.escape(self.get_argument("teamName"))
                if teamName in CTX.teams:
                    self.set_secure_cookie("team", teamName)
                    self.redirect("/teampage")
                    return
                errorMessages.append("Unknown team: %s"%(teamName))
            elif self.get_argument("admin", None):
                self.set_secure_cookie("admin", "1")
                self.redirect("/admin")
                return
        except ErrorMessage as ex:
            errorMessages.append(ex.message)
        self.render(os.path.join("www", "testLogin.html"), getTeamQuickLogin=self.getTeamQuickLogin, Errors=errorMessages)

def initialiseTornado():
    asyncio.set_event_loop(asyncio.new_event_loop())
    tornado.ioloop.IOLoop.instance().start()

def startServer():
    serverThread = threading.Thread(target=initialiseTornado)
    # Exit the server thread when the main thread terminates
    serverThread.daemon = True
    serverThread.start()

def initilise():
    os.makedirs("messages", exist_ok=True)
    parser = argparse.ArgumentParser(description="Runs KPH webserver")
    parser.add_argument("--reloadMessages", "-r", type=argparse.FileType("r"), help="Reload the messages from specified file")
    # Open mode of x means fail if the file already exists
    parser.add_argument("--messageFile", "-m", type=argparse.FileType("x"), nargs='?',
                        default=os.path.join("messages", "%s.txt"%(datetime.datetime.now().strftime("%Y%m%dT%H%M%S"))),
                        help="Save messages to specified file.  Default: messages/%s.txt"%
                        (datetime.datetime.now().strftime("%Y%m%dT%H%M%S")))
    parser.add_argument("--port", "-p", type=int, default=9092, help="Port to listen on, default: 9092")
    args = parser.parse_args()

    commandRegistrar.setMessageFile(args.messageFile)
    if args.reloadMessages:
        import scheduler
        with scheduler.PUZZLE_SCHEDULER.reloading():
            CTX.reloading = True
            huntSpecific.initialise(reloading=True)
            CTX.importMessages(args.reloadMessages)
            CTX.reloading = False
    else:
        huntSpecific.initialise(reloading=False)

    settings = {
        "debug": True,
        "static_path": os.path.join(os.path.dirname(__file__), "www", "static"),
        "cookie_secret": "123",
        "autoreload": False
        }
    pageList = [
        (r"/ws", WSHandler),
        (r"/login", Login),
        (r"/teampage", TeamPage),
        (r"/admin", AdminPage),
        (r"/adminTeamViewer", AdminTeamViewerPage),
        (r"/adminQuestionViewer", AdminQuestionViewerPage),
        (r"/scorescore", ScorePage),
        (r"/timer", TimerPage)
        ]
    if CTX.enableInsecure:
        pageList.append((r"/testLogin", TestLogin))
        pageList.append((r"/", TestLogin))
    else:
        pageList.append((r"/", Login))
    application = tornado.web.Application(pageList, **settings)
    application.listen(args.port)

    startServer()
    import readline
    import rlcompleter #pylint: disable=unused-variable, possibly-unused-variable
    import code
    readline.parse_and_bind("tab: complete")
    code.interact(local=locals())
    tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    initilise()
