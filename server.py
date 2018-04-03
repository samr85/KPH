import threading
import os.path
import tornado.web
import tornado.websocket

from globalItems import ErrorMessage, startTime
import messageHandler
from teams import teamList
from admin import adminList

templateLoader = tornado.template.Loader("www")

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
            if teamName in teamList.teamList:
                self.team = teamList.teamList[teamName]
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
        except ErrorMessage as e:
            self.write_message("Error: %s"%(e.message))

    def on_close(self):
        messageHandler.clients.removeClient(self)
        print('connection closed.')

    def write_message(self, message, binary = False):
        print("MSG Tx: " + message)
        return super().write_message(message, binary)

    def sendRefresh(self):
        self.write_message("js: location.reload();")

class teamRequestHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        teamName = self.get_secure_cookie("team")
        if not teamName:
            self.redirect("login")
            return
        teamName = teamName.decode()
        print("Team: %s"%(teamName))
        if teamName in teamList.teamList:
            self.team = teamList.teamList[teamName]
        else:
            self.redirect("login")
            return
        self.getTeam(*args, **kwargs)

    def getTeam(self):
        raise NotImplementedError("This function should have been overloaded!! " + self.request)

class teamPage(teamRequestHandler):
    def getTeam(self):
        self.render("www\\sections.html", answers=self.team.questionAnswers.values(), pageTitle="Team %s"%(self.team.name))

class adminRequestHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        admin = self.get_secure_cookie("admin", None)
        if not admin:
            self.redirect("login")
            return
        self.getAdmin(*args, **kwargs)
    def getAdmin(self):
        raise NotImplementedError("This function should have been overloaded!! " + self.request)

class adminPage(adminRequestHandler):
    def getAdmin(self):
        self.render("www\\admin.html")

class scorePage(tornado.web.RequestHandler):
    def get(self):
        self.render("www\\score.html", teamScoreList = teamList.getScoreList(), teamScoreHistory = teamList.getScoreHistory(), startTime=startTime)

class login(tornado.web.RequestHandler):
    def get(self):
        self.clear_cookie("team")
        self.clear_cookie("admin")
        self.render("www\\login.html", getTeamQuickLogin=self.getTeamQuickLogin, Errors = [])

    def getTeamQuickLogin(self):
        retHTML = ""
        for team in teamList.teamList:
            retHTML += "<input name='QuickLogin' type='Submit' value='%s' /><br />"%(team)
        return retHTML

    def post(self):
        errorMessages = []
        try:
            if (self.get_argument("QuickLogin", None)):
                teamName = self.get_argument("QuickLogin")
                if teamName in teamList.teamList:
                    self.set_secure_cookie("team", teamName)
                    self.redirect("\\teampage")
                    return
                errorMessages.append("Unknown team: %s"%(teamName))
            elif (self.get_argument("createTeam", None)):
                teamName = self.get_argument("teamName")
                # Excepts on error
                teamList.createTeam(teamName)
                self.set_secure_cookie("team", teamName)
                self.redirect("\\teampage")
                return
            elif (self.get_argument("login", None)):
                teamName = self.get_argument("teamName")
                if teamName in teamList.teamList:
                    self.set_secure_cookie("team", teamName)
                    self.redirect("\\teampage")
                    return 
                errorMessages.append("Unknown team: %s"%(teamName))
            elif (self.get_argument("admin", None)):
                self.set_secure_cookie("admin", "1")
                self.redirect("\\admin")
                return
        except ErrorMessage as e:
            errorMessages.append(e.message)
        self.render("www\\login.html", getTeamQuickLogin=self.getTeamQuickLogin, Errors = errorMessages)


def startServer():
    server_thread = threading.Thread(target=tornado.ioloop.IOLoop.instance().start)
    # Exit the server thread when the main thread terminates
    server_thread.daemon = True
    server_thread.start()

if __name__ == "__main__":
    settings={
        "debug": True,
        "static_path": os.path.join(os.path.dirname(__file__), "www\\static"),
        "cookie_secret": "123",
        "autoreload": False 
        }
    application = tornado.web.Application([
        (r"/", login),
        (r"/ws", WSHandler),
        (r"/login", login),
        (r"/teampage", teamPage),
        (r"/admin", adminPage),
        (r"/score", scorePage)
        ], **settings)
    application.listen(9092)

    startServer()
    import readline
    import rlcompleter
    import code
    readline.parse_and_bind("tab: complete")
    code.interact(local=locals())
    tornado.ioloop.IOLoop.instance().stop()
