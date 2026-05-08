import datetime

class Logger:
    def __init__(self, node_id):
        self.node_id = node_id

    def log(self, message, clock=None):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        clock_part = f" | Clock {clock}" if clock is not None else ""
        print(f"[{now}] [Node {self.node_id}{clock_part}] {message}")
