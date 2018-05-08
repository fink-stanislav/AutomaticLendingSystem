
from threading import Thread, Event

from als.util import custom_logging

logger = custom_logging.get_logger('als.core')


class NoRepeatThread(Thread):
    """
    Thread implementation that runs only once.
    """
    def __init__(self, func, daemon=False, args=None, name='Thread', kind='generic'):
        super(NoRepeatThread, self).__init__()
        super(NoRepeatThread, self).setDaemon(daemon)
        self.func = func
        self.name = name
        self.kind = kind
        self.args = args

    def run(self):
        try:
            if self.args is not None:
                self.func(*self.args)
            else:
                self.func()
        except:
            logger.exception('Error on executing thread. Name={}, Kind={}'.format(self.name, self.kind))

    def start(self):
        Thread.start(self)

    def stop(self):
        pass

class RepeatThread(NoRepeatThread):
    """
    Thread implementation that can run periodically
    """
    def __init__(self, delay, func, daemon=False, args=None, name='Thread', kind='repeating'):
        super(RepeatThread, self).__init__(func, daemon=daemon, args=args, name=name, kind=kind)
        self.delay = delay
        self.event = Event()

    def run(self):
        while not self.event.wait(self.delay):
            try:
                if self.args is not None:
                    self.func(*self.args)
                else:
                    self.func()
            except:
                logger.exception('Error on executing repeating thread. Name={}, Kind={}'.format(self.name, self.kind))

    def start(self):
        self.event = Event()
        Thread.start(self)

    def stop(self):
        self.event.set()
