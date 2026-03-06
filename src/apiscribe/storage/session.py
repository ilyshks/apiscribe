import threading

class RuntimeSession:
    def __init__(self):
        self.proxy = None
        self.collector = None
        self.thread = None
        self.running = False


session = RuntimeSession()