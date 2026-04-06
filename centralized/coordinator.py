import threading
from queue import Queue


class Coordinator:
    def __init__(self, adapter=None):
        self.is_locked = False
        self.queue = Queue()
        self.lock = threading.Lock()
        self.adapter = adapter
        self.active = True

    def handle_request(self, node):
        if not self.active:
            return

        with self.lock:
            print(f"[Coordinator] REQUEST từ Node {node.id}")

            if self.adapter:
                self.adapter.log_message_received("REQUEST", node.id, 0)

            if not self.is_locked:
                self.is_locked = True
                print(f"[Coordinator] → GRANT cho Node {node.id}")

                if self.adapter:
                    self.adapter.log_message_sent("GRANT", 0, node.id)

                node.receive_grant()
            else:
                print(f"[Coordinator] → Queue Node {node.id}")
                self.queue.put(node)

    def handle_release(self, node):
        if not self.active:
            return

        with self.lock:
            print(f"[Coordinator] RELEASE từ Node {node.id}")

            if self.adapter:
                self.adapter.log_message_received("RELEASE", node.id, 0)

            if not self.queue.empty():
                next_node = self.queue.get()
                print(f"[Coordinator] → GRANT cho Node {next_node.id}")

                if self.adapter:
                    self.adapter.log_message_sent("GRANT", 0, next_node.id)

                next_node.receive_grant()
            else:
                self.is_locked = False
                print(f"[Coordinator] → Resource FREE")