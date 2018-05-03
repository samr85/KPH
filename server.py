import threading
import os.path
import argparse
import datetime
import tornado.web
import tornado.websocket

from globalItems import ErrorMessage, startTime
import messageHandler
import commandRegistrar
import huntSpecific
from controller import CTX
from admin import adminList

class WSHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team = None
        self.admin = False
        self.validConnection = False

    def open(self):
        print('connection opened.')
        teamName = self.get_secure_cookie("team", None)
        if teamName:
            teamName = teamName.decode()
            if teamName in CTX.teams.teamList:
                self.team = CTX.teams.teamList[teamName]
                self.team.sendAllNotifications(self)
            else:
                self.write_message("Error: team %s doesn't exist!!"%(teamName))
                self.sendRefresh()
                self.close()
                return
        else: # Can't be both a team and admin
            admin = self.get_secure_cookie("admin", None)
            if admin:
                self.admin = adminList
            else:
                # Correct for eg login page
                print("Connection is neither team or admin")
        self.validConnection = True
        messageHandler.clients.addClient(self)

    def on_message(self, message):
        if not self.validConnection:
            print("ERROR: Got message from invalid connection: " + message)
            return
        print('MSG Rx: ' + message)
        try:
            messageHandler.handleMessage(self, message)
        except ErrorMessage as ex:
            self.write_message("Error: %s"%(ex.message))

    def on_close(self):
        messageHandler.clients.removeClient(self)
        print('connection closed.')

    def write_message(self, message, binary=False):
        print("MSG Tx: " + message)
        return super().write_message(message, binary)

    def sendRefresh(self):
        self.write_message("js: location.reload();")

class TeamRequestHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super().__init__(application, request, **kwargs)
        self.team = None

    def get(self, *args, **kwargs):
        teamName = self.get_secure_cookie("team")
        if not teamName:
            self.redirect("login")
            return
        teamName = teamName.decode()
        print("Team: %s"%(teamName))
        if teamName in CTX.teams.teamList:
            self.team = CTX.teams.teamList[teamName]
        else:
            self.redirect("login")
            return
        self.getTeam(*args, **kwargs)

    def getTeam(self):
        raise NotImplementedError("This function should have been overloaded!! " + self.request)

class TeamPage(TeamRequestHandler):
    def getTeam(self):
        self.render("www\\sections.html", answers=self.team.questionAnswers.values(), pageTitle="Team %s"%(self.team.name))

class AdminRequestHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        admin = self.get_secure_cookie("admin", None)
        if not admin:
            self.redirect("login")
            return
        self.getAdmin(*args, **kwargs)
    def getAdmin(self):
        raise NotImplementedError("This function should have been overloaded!! " + self.request)

class AdminPage(AdminRequestHandler):
    def getAdmin(self):
        self.render("www\\admin.html")

class ScorePage(tornado.web.RequestHandler):
    def get(self):
        self.render("www\\score.html", teamScoreList=CTX.teams.getScoreList(), teamScoreHistory=CTX.team.getScoreHistory(), startTime=startTime)

class Login(tornado.web.RequestHandler):
    def get(self):
        self.clear_cookie("team")
        self.clear_cookie("admin")
        self.render("www\\login.html", getTeamQuickLogin=self.getTeamQuickLogin, Errors=[])

    def getTeamQuickLogin(self):
        retHTML = ""
        for team in CTX.teams.teamList:
            retHTML += "<input name='QuickLogin' type='Submit' value='%s' /><br />"%(team)
        return retHTML

    def post(self):
        errorMessages = []
        try:
            if (self.get_argument("QuickLogin", None)):
                teamName = self.get_argument("QuickLogin")
                if teamName in CTX.teams.teamList:
                    self.set_secure_cookie("team", teamName)
                    self.redirect("\\teampage")
                    return
                errorMessages.append("Unknown team: %s"%(teamName))
            elif (self.get_argument("createTeam", None)):
                teamName = self.get_argument("teamName")
                # Excepts on error
                messageHandler.sendDummyMessage("createTeam", [teamName])
                self.set_secure_cookie("team", teamName)
                self.redirect("\\teampage")
                return
            elif (self.get_argument("login", None)):
                teamName = self.get_argument("teamName")
                if teamName in CTX.teams.teamList:
                    self.set_secure_cookie("team", teamName)
                    self.redirect("\\teampage")
                    return
                errorMessages.append("Unknown team: %s"%(teamName))
            elif (self.get_argument("admin", None)):
                self.set_secure_cookie("admin", "1")
                self.redirect("\\admin")
                return
        except ErrorMessage as ex:
            errorMessages.append(ex.message)
        self.render("www\\login.html", getTeamQuickLogin=self.getTeamQuickLogin, Errors=errorMessages)


def startServer():
    serverThread = threading.Thread(target=tornado.ioloop.IOLoop.instance().start)
    # Exit the server thread when the main thread terminates
    serverThread.daemon = True
    serverThread.start()

def initilise():
    parser = argparse.ArgumentParser(description="Runs KPH webserver")
    parser.add_argument("--reloadMessages", "-r", type=argparse.FileType("r"), help="Reload the messages from specified file")
    # Open mode of x means fail if the file already exists
    parser.add_argument("--messageFile", "-m", type=argparse.FileType("x"), nargs='?',
                        default="messages\\%s.txt"%(datetime.datetime.now().strftime("%Y%m%dT%H%M%S")),
                        help="Save messages to specified file.  Default: messages.%s.txt"%
                        (datetime.datetime.now().strftime("%Y%m%dT%H%M%S")))
    parser.add_argument("--port", "-p", type=int, default=9092, help="Port to listen on, default: 9092")
    args = parser.parse_args()

    commandRegistrar.setMessageFile(args.messageFile)
    if args.reloadMessages:
        import scheduler
        with scheduler.PuzzleScheduler.reloading():
            huntSpecific.initialise(reloading=True)
            messageHandler.importMessages(args.reloadMessages)
    else:
        huntSpecific.initialise(reloading=False)

    settings = {
        "debug": True,
        "static_path": os.path.join(os.path.dirname(__file__), "www\\static"),
        "cookie_secret": "123",
        "autoreload": False
        }
    application = tornado.web.Application([
        (r"/", Login),
        (r"/ws", WSHandler),
        (r"/login", Login),
        (r"/teampage", TeamPage),
        (r"/admin", AdminPage),
        (r"/score", ScorePage)
        ], **settings)
    application.listen(args.port)

    startServer()
    import readline
    import rlcompleter #pylint: disable=unused-variable
    import code
    readline.parse_and_bind("tab: complete")
    code.interact(local=locals())
    tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":
    initilise()
