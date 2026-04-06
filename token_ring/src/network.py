import time

from node import Node
from Token import Token


class Network:
    def __init__(self, num_nodes):
        self.num_nodes = num_nodes
        self.nodes = []
        self.token = None
        self.current_node_index = 0
        # event/log buffers for visualizer/demo
        self._events = []  # list of (timestamp, text)
        self._logs = []
        self._events_max = 200
        # create node instances immediately for simple test usage
        self.create_nodes()

    def create_nodes(self):
        # clear any existing nodes and recreate
        self.nodes = []
        for i in range(self.num_nodes):
            node = Node(i, self)
            self.nodes.append(node)

    def start_network(self):
        self.token = Token()
        # give token to first node
        self.nodes[self.current_node_index].receive_token(self.token)
        self._append_event(f"injected initial token to node {self.current_node_index}")
        self._log(f"node {self.current_node_index} injecting initial token")

    def pass_token(self, token=None):
        # accept token passed from a node, or fall back to stored self.token
        self.token = token or self.token
        self.current_node_index = (self.current_node_index + 1) % self.num_nodes
        self.nodes[self.current_node_index].receive_token(self.token)
        self._append_event(f"token passed to node {self.current_node_index}")
        self._log(f"token passed to node {self.current_node_index}")

    def receive_message(self, message, sender_id):
        # simplistic in-memory delivery: append to next node's received_messages
        # for tests we deliver to node at index sender_id + 1
        dest_index = (sender_id + 1) % self.num_nodes
        self.nodes[dest_index].received_messages.append(message)
        txt = f"{message}"
        print(txt)
        self._append_event(txt)
        self._log(txt)

    def get_snapshot(self):
        """Return a lightweight snapshot of the network state for visualization.

        Snapshot format (compat):
          {
            'nodes': [ {'id': int, 'has_token': bool, 'received': int}, ... ],
            'current_index' or 'current_node_index': int,
            'num_nodes': int,
            'per_node_last_message': [str|None,...],
            'events': [],
            'logs': [],
          }
        """
        snap = {
            "nodes": [],
            # keep both key names in case demo/visualizer expects one or the other
            "current_index": self.current_node_index,
            "current_node_index": self.current_node_index,
            "num_nodes": len(self.nodes),
        }

        for idx, node in enumerate(self.nodes):
            try:
                nid = getattr(node, "id", getattr(node, "node_id", idx))
                has_token = bool(getattr(node, "token", None) is not None or getattr(node, "has_token", False))
                received = len(getattr(node, "received_messages", []))
            except Exception:
                nid = idx
                has_token = False
                received = 0
            snap["nodes"].append({"id": nid, "has_token": has_token, "received": received})

        # per-node last message convenience field (used by some visualizer code)
        per_last = []
        for node in self.nodes:
            try:
                msgs = getattr(node, "received_messages", [])
                per_last.append(msgs[-1] if msgs else None)
            except Exception:
                per_last.append(None)
        snap["per_node_last_message"] = per_last

        # lightweight events list (timestamped events); visualizers may expect this key
        # return a copy to avoid exposing internal buffers
        snap["events"] = list(self._events)
        # optional recent logs
        snap["logs"] = list(self._logs)

        return snap

    def _log(self, msg: str):
        """Simple logging helper used by demo visualizer."""
        try:
            print(f"[Network] {msg}")
            # keep bounded-size logs
            self._logs.append((time.time(), msg))
            if len(self._logs) > self._events_max:
                self._logs.pop(0)
        except Exception:
            pass

    def _append_event(self, text: str):
        """Append a timestamped event to the events buffer."""
        try:
            ts = time.time()
            self._events.append((ts, text))
            # keep bounded size
            if len(self._events) > self._events_max:
                self._events.pop(0)
        except Exception:
            pass