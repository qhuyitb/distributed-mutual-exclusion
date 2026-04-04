import random
import threading
import time
from functools import total_ordering

from lamport import LamportClock
from logger import Logger
from message import Message
from network import Network
from config import CS_DURATION


@total_ordering
class RequestEntry:
    def __init__(self, timestamp, node_id):
        self.timestamp = timestamp
        self.node_id = node_id

    def __eq__(self, other):
        return (self.timestamp, self.node_id) == (other.timestamp, other.node_id)

    def __lt__(self, other):
        return (self.timestamp, self.node_id) < (other.timestamp, other.node_id)


class Node:
    def __init__(self, node_id, host, port, peers):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.peers = peers

        self.clock = LamportClock()
        self.logger = Logger(self.node_id)
        self.network = Network(self.node_id, host, port, self._on_message)

        self.request_queue = []
        self.reply_count = 0
        self.deferred_replies = set()
        self.requesting_cs = False
        self.in_cs = False
        self.request_timestamp = None
        self.seq = 0

        self.lock = threading.RLock()
        self.cs_condition = threading.Condition(self.lock)

    def start(self):
        self.logger.log("Starting node server", self.clock.get_time())
        self.network.start()

    def _on_message(self, msg: Message):
        self.logger.log(f"RECEIVE {msg.msg_type} from Node {msg.sender_id} (ts={msg.timestamp})", self.clock.get_time())
        with self.lock:
            self.clock.update(msg.timestamp)
            if msg.msg_type == "REQUEST":
                self._handle_request(msg)
            elif msg.msg_type == "REPLY":
                self._handle_reply(msg)

    def _handle_request(self, msg: Message):
        sender = msg.sender_id
        req_entry = RequestEntry(msg.timestamp, sender)
        if req_entry not in self.request_queue:
            self.request_queue.append(req_entry)
        self.request_queue.sort()

        self.logger.log(f"Queue: {[f'({r.timestamp},{r.node_id})' for r in self.request_queue]}", self.clock.get_time())

        should_defer = False
        if self.in_cs:
            should_defer = True
        elif self.requesting_cs:
            own_req = RequestEntry(self.request_timestamp, self.node_id)
            if own_req < req_entry:
                should_defer = True

        if should_defer:
            self.deferred_replies.add(sender)
            self.logger.log(f"DEFER REQUEST from Node {sender}", self.clock.get_time())
            self.logger.log(f"Deferred: {sorted(self.deferred_replies)}", self.clock.get_time())
        else:
            self.logger.log(f"REPLY immediately to Node {sender}", self.clock.get_time())
            self._send_reply(sender)

    def _handle_reply(self, msg: Message):
        self.reply_count += 1
        self.logger.log(f"RECEIVE REPLY from Node {msg.sender_id} (count={self.reply_count})", self.clock.get_time())
        self.cs_condition.notify_all()

    def _send_request(self):
        self.clock.increment()
        self.seq += 1
        self.request_timestamp = self.clock.get_time()

        self.requesting_cs = True
        self.reply_count = 0

        self.request_queue.append(RequestEntry(self.request_timestamp, self.node_id))
        self.request_queue.sort()

        self.logger.log("SEND REQUEST to all", self.clock.get_time())

        for peer_id, (p_host, p_port) in self.peers.items():
            msg = Message("REQUEST", self.node_id, peer_id, self.seq, self.request_timestamp)
            threading.Thread(target=self.network.send_message, args=(p_host, p_port, msg), daemon=True).start()

    def _send_reply(self, target_id):
        target = self.peers.get(target_id)
        if not target:
            return
        self.clock.increment()
        self.seq += 1
        reply_ts = self.clock.get_time()
        msg = Message("REPLY", self.node_id, target_id, self.seq, reply_ts)
        threading.Thread(target=self.network.send_message, args=(target[0], target[1], msg), daemon=True).start()

    def request_cs(self):
        with self.lock:
            if self.requesting_cs or self.in_cs:
                self.logger.log("Already requesting or already in CS", self.clock.get_time())
                return
            self._send_request()

        with self.cs_condition:
            while True:
                with self.lock:
                    # Elected khi nhận reply từ tất cả peer khác
                    elected = len(self.peers) == self.reply_count
                    
                    if elected:
                        self.logger.log("Elected to enter CS", self.clock.get_time())
                        break
                
                self.cs_condition.wait(timeout=0.5)

        self._enter_cs()

    def _enter_cs(self):
        with self.lock:
            self.in_cs = True
            self.logger.log(f">>> ENTER CS (request timestamp={self.request_timestamp})", self.clock.get_time())

        time.sleep(CS_DURATION)

        with self.lock:
            self.logger.log("<<< EXIT CS", self.clock.get_time())
            self._exit_cs()

    def _exit_cs(self):
        self.in_cs = False
        self.requesting_cs = False
        self.request_queue = [r for r in self.request_queue if r.node_id != self.node_id]

        for peer_id in sorted(self.deferred_replies):
            self.logger.log(f"SEND deferred REPLY to Node {peer_id}", self.clock.get_time())
            self._send_reply(peer_id)
        self.deferred_replies.clear()

        self.reply_count = 0

    def auto_request_loop(self, min_sleep=3, max_sleep=6):
        while True:
            wait = random.uniform(min_sleep, max_sleep)
            time.sleep(wait)
            self.logger.log(f"Auto mode: requesting CS after {wait:.1f}s", self.clock.get_time())
            self.request_cs()