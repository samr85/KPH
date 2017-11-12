import threading
import tornado.web
import tornado.websocket
import os.path

import KPH
from KPH import ErrorMessage
import messageHandler

class WSHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.team = None
        self.admin = False

    def open(self):
        print('connection opened...')
        KPH.clients.append(self)
        team = self.get_secure_cookie("team", None)
        if (team):
            team = team.decode()
            if team in KPH.teamList.teamList:
                self.team = KPH.teamList.teamList[team]
                self.team.sendAllNotifications(self)
            else:
                self.write_message("Error: team %s doesn't exist!!"%(team))
        else: # Can't be both a team and admin
            admin = self.get_secure_cookie("admin", None)
            if admin:
                self.admin = True

    def on_message(self, message):
        print('received:' + message)
        try:
            messageHandler.handleMessage(self, message)
        except ErrorMessage as e:
            self.write_message("Error: %s"%(e.message))

    def on_close(self):
        KPH.clients.remove(self)
        print('connection closed...')

    def sendRefresh(self):
        self.write_message("js: location.reload();")

class teamPage(tornado.web.RequestHandler):
    def get(self):
        team = self.get_secure_cookie("team").decode()
        print("Team: %s"%(team))
        if team in KPH.teamList.teamList:
            self.team = KPH.teamList.teamList[team]
        else:
            self.redirect("login")
            return
        self.render("www\\teampage.html", teamname = team, getQuestions=self.getQuestions)

    def getQuestions(self):
        return self.team.makeQuestionList()

class adminPage(tornado.web.RequestHandler):
    def get(self):
        admin = self.get_secure_cookie("admin", None)
        if not admin:
            self.redirect("login")
            return
        self.render("www\\admin.html", answerList=KPH.answerQueue.makeAnswerList)

class scorePage(tornado.web.RequestHandler):
    def get(self):
        self.render("www\\score.html", teamScoreList = KPH.teamList.getScoreList(), teamScoreHistory = KPH.teamList.getScoreHistory(), startTime=KPH.startTime)

class login(tornado.web.RequestHandler):
    def get(self):
        self.clear_cookie("team")
        self.clear_cookie("admin")
        self.render("www\\login.html", getTeamQuickLogin=self.getTeamQuickLogin, Errors = [])

    def getTeamQuickLogin(self):
        retHTML = ""
        for team in KPH.teamList.teamList:
            retHTML += "<input name='QuickLogin' type='Submit' value='%s' /><br />"%(team)
        return retHTML

    def post(self):
        errorMessages = []
        try:
            if (self.get_argument("QuickLogin", None)):
                teamName = self.get_argument("QuickLogin")
                if teamName in KPH.teamList.teamList:
                    self.set_secure_cookie("team", teamName)
                    self.redirect("\\teampage")
                    return
                errorMessages.append("Unknown team: %s"%(teamName))
            elif (self.get_argument("createTeam", None)):
                teamName = self.get_argument("teamName")
                # Excepts on error
                KPH.teamList.createTeam(teamName)
                self.set_secure_cookie("team", teamName)
                self.redirect("\\teampage")
                return
            elif (self.get_argument("login", None)):
                teamName = self.get_argument("teamName")
                if teamName in KPH.teamList.teamList:
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
    application.listen(9090)

    startServer()
    import readline
    import rlcompleter
    import code
    readline.parse_and_bind("tab: complete")
    code.interact(local=locals())
    tornado.ioloop.IOLoop.instance().stop()
