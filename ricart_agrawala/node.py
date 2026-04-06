"""
Node module - Triển khai Ricart-Agrawala algorithm (in-memory, dùng cho demo)
"""
import threading
import time
from collections import deque
from typing import List, Tuple
from message import create_request_message, create_reply_message


class Node:
    """Node triển khai Ricart-Agrawala algorithm"""

    def __init__(self, node_id: int, all_nodes: List['Node']):
        self.id = node_id
        self.all_nodes = all_nodes
        self.logical_clock = 0
        self.request_queue = deque()          # (node_id, timestamp)
        self.waiting_for_replies: set = set()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.in_cs = False
        self.replies_received = 0
        self.seq_num = 0
        self.my_request_timestamp = float('inf')
        self.cs_work_time = 2

    # ------------------------------------------------------------------ clock
    def increment_clock(self):
        with self.lock:
            self.logical_clock += 1
            return self.logical_clock

    def update_clock(self, timestamp: int):
        with self.lock:
            self.logical_clock = max(self.logical_clock, timestamp) + 1

    # ------------------------------------------------------------------ CS
    def enter_cs(self):
        """Yêu cầu vào Critical Section"""
        with self.lock:
            self.logical_clock += 1
            request_ts = self.logical_clock
            self.request_queue.append((self.id, request_ts))
            self.waiting_for_replies = set(
                i for i in range(len(self.all_nodes)) if i != self.id
            )
            self.replies_received = 0
            self.seq_num += 1
            self.my_request_timestamp = request_ts
            nodes_to_send = list(self.waiting_for_replies)   # snapshot
            num_expected = len(self.waiting_for_replies)

        print(f"[Node {self.id}] Gửi REQUEST (ts={request_ts})")

        for node in self.all_nodes:
            if node.id in nodes_to_send:
                msg = create_request_message(
                    sender_id=self.id,
                    receiver_id=node.id,
                    timestamp=request_ts,
                    seq_num=self.seq_num,
                )
                node.receive_request(msg)

        with self.lock:
            while self.replies_received < num_expected:
                self.condition.wait()

        print(f"[Node {self.id}] >>> NHẬN ĐỦ REPLY - ENTER CS (ts={request_ts})")
        self.in_cs = True
        time.sleep(self.cs_work_time)
        self.exit_cs()

    def exit_cs(self):
        """Thoát CS và gửi REPLY cho pending requests"""
        with self.lock:
            print(f"[Node {self.id}] <<< EXIT CS")
            self.in_cs = False
            self.my_request_timestamp = float('inf')
            self.request_queue = deque(
                (nid, ts) for nid, ts in self.request_queue if nid != self.id
            )
            pending = list(self.request_queue)
            self.logical_clock += 1
            reply_ts = self.logical_clock

        for requester_id, _ in pending:
            msg = create_reply_message(
                sender_id=self.id,
                receiver_id=requester_id,
                timestamp=reply_ts,
                seq_num=self.seq_num,
            )
            self.all_nodes[requester_id].receive_reply(msg)
            print(f"[Node {self.id}] Gửi REPLY tới Node {requester_id}")

    # ------------------------------------------------------------------ handlers
    def receive_request(self, msg):
        """Nhận REQUEST từ node khác"""
        self.update_clock(msg.timestamp)

        with self.lock:
            self.request_queue.append((msg.sender_id, msg.timestamp))
            incoming_priority = (msg.timestamp, msg.sender_id)
            my_priority = (self.my_request_timestamp, self.id)
            should_reply = (
                not self.in_cs
                and (not self.waiting_for_replies or incoming_priority < my_priority)
            )
            reply_ts = self.logical_clock

        if should_reply:
            reply_msg = create_reply_message(
                sender_id=self.id,
                receiver_id=msg.sender_id,
                timestamp=reply_ts,
                seq_num=msg.sequence_num,
            )
            self.all_nodes[msg.sender_id].receive_reply(reply_msg)
            print(f"[Node {self.id}] Gửi REPLY ngay tới Node {msg.sender_id}")

    def receive_reply(self, msg):
        """Nhận REPLY từ node khác"""
        self.update_clock(msg.timestamp)

        with self.lock:
            if msg.sender_id in self.waiting_for_replies:
                self.waiting_for_replies.discard(msg.sender_id)
                self.replies_received += 1
                if self.replies_received == len(self.all_nodes) - 1:
                    self.condition.notify_all()


class NodeManager:
    """Quản lý các nodes và điều phối thực thi"""

    def __init__(self, num_nodes: int):
        self.num_nodes = num_nodes
        self.nodes = [Node(i, []) for i in range(num_nodes)]
        for node in self.nodes:
            node.all_nodes = self.nodes

    def run_scenario(self, request_sequence: List[Tuple[int, float]] = None):
        if request_sequence is None:
            request_sequence = [(i, i * 0.5) for i in range(self.num_nodes)]

        print(f"\n{'='*60}")
        print(f"Ricart-Agrawala Demo: {self.num_nodes} nodes")
        print(f"{'='*60}\n")

        def node_task(node_id: int, delay: float):
            if delay > 0:
                time.sleep(delay)
            self.nodes[node_id].enter_cs()

        threads = [
            threading.Thread(target=node_task, args=(nid, delay))
            for nid, delay in request_sequence
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        print(f"\n{'='*60}")
        print("Demo hoàn thành!")
        print(f"{'='*60}\n")

    def run_random_scenario(self, num_requests: int = None):
        if num_requests is None:
            num_requests = self.num_nodes * 2
        requests_per_node = num_requests // self.num_nodes
        sequence = [
            (i, i * 0.2 + j * 0.1)
            for i in range(self.num_nodes)
            for j in range(requests_per_node)
        ]
        self.run_scenario(sequence)