import threading
import collections
import datetime
import time
import contextlib

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
            if runNow:
                try:
                    runNow.callback(*runNow.args, **runNow.kwargs)
                except Exception as e:
                    print("Exception in timer callback: " + str(e))
                runNow = None

            self._waitsModified.clear()
            if not self._events:
                self._waitsModified.wait()
            else:
                with self._lock:
                    curTime = datetime.datetime.now()
                    firstEvent = self._events[0]
                    if firstEvent.callTime < curTime:
                        runNow = self._events.pop(0)
                        continue
                    timediff = curTime - firstEvent.callTime
                    timediff = datetime.timedelta()
                time.sleep(timediff.total_seconds())

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

# example:
#def fn(a, b=None, c=None):
#    print("called with: (%s, %s, %s)"%(a, b, c))
#scheduler.runIn(2, fn, args="a", kwargs={"c": "asdf"})