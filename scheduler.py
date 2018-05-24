import threading
import collections
import datetime
import time
import contextlib
import traceback

from sections import registerSectionHandler, SectionHandler

class PuzzleScheduler:
    TriggerEvent = collections.namedtuple("TriggerEvent", ["callTime", "callback", "args", "kwargs"])

    def __init__(self):
        self._lock = threading.Lock()
        self._waitsModified = threading.Event()
        self._events = []
        self._reloading = False
        threading.Thread(target=self._schedulerMain, daemon=True).start()

    def _schedulerMain(self):
        runNow = None
        while True:
            #print("start scheduler loop")
            if runNow:
                try:
                    runNow.callback(*runNow.args, **runNow.kwargs)
                except Exception as e:
                    print("Exception in timer callback: " + str(e))
                    traceback.print_exc()
                runNow = None

            self._waitsModified.clear()
            if not self._events:
                #print("Waiting on _waits")
                self._waitsModified.wait()
            else:
                with self._lock:
                    curTime = datetime.datetime.now()
                    firstEvent = self._events[0]
                    if firstEvent.callTime < curTime:
                        runNow = self._events.pop(0)
                        continue
                    timediff = firstEvent.callTime - curTime
                #print("Sleeping for %d"%(timediff.total_seconds()))
                self._waitsModified.wait(timediff.total_seconds())

    def schedule(self, timeAbsolute, callback, args=(), kwargs={}):
        if self._reloading:
            return
        event = self.TriggerEvent(timeAbsolute, callback, args, kwargs)
        with self._lock:
            self._events.append(event)
            self._events.sort(key=lambda x: x.callTime)
            self._waitsModified.set()

    @contextlib.contextmanager
    def reloading(self):
        self._reloading = True
        yield
        self._reloading = False

PUZZLE_SCHEDULER = PuzzleScheduler()

def runIn(timeOffset, callback, args=(), kwargs={}):
    timeAbsolute = datetime.datetime.now() + datetime.timedelta(seconds=timeOffset)
    PUZZLE_SCHEDULER.schedule(timeAbsolute, callback, args, kwargs)

def runAt(timeAbsolute, callback, args=(), kwargs={}):
    PUZZLE_SCHEDULER.schedule(timeAbsolute, callback, args, kwargs)

COUNTDOWN_MESSAGE_STRING = None
COUNTDOWN_MESSAGE_TIME = None
COUNTDOWN_MESSAGE_VERSION = 0

def displayCountdown(messageString, timeOffset = None, timeAbsolute = None):
    if timeOffset:
        timeAbsolute = datetime.datetime.now() + datetime.timedelta(seconds=timeOffset)
    global COUNTDOWN_MESSAGE_STRING, COUNTDOWN_MESSAGE_TIME, COUNTDOWN_MESSAGE_VERSION 
    COUNTDOWN_MESSAGE_STRING = messageString.encode()
    COUNTDOWN_MESSAGE_TIME = timeAbsolute.isoformat().encode()
    COUNTDOWN_MESSAGE_VERSION += 1

@registerSectionHandler("countdown")
class countdownSectionHandler(SectionHandler):
    def __init__(self):
        super().__init__()

    def requestSection(self, requestor, sectionId):
        if sectionId == "0":
            return (COUNTDOWN_MESSAGE_VERSION, 0, COUNTDOWN_MESSAGE_STRING)
        else:
            return (COUNTDOWN_MESSAGE_VERSION, datetime.datetime.now().isoformat(), COUNTDOWN_MESSAGE_TIME)

    def requestUpdateList(self, requestor):
        return [(0, COUNTDOWN_MESSAGE_VERSION), 
                (1, COUNTDOWN_MESSAGE_VERSION)]

# example:
#def fn(a, b=None, c=None):
#    print("called with: (%s, %s, %s)"%(a, b, c))
#scheduler.runIn(2, fn, args="a", kwargs={"c": "asdf"})
