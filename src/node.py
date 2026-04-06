"""Node implementation using TCP sockets.

Each node listens on localhost:base_port + node_id.
When it receives a TOKEN message it holds it for a short time
and then forwards it to the next node.

This file provides a Node class used by `node_process.py`.
"""
import socket
import threading
import json
import time
from typing import Optional


class Node:
    def __init__(self, node_id: int, base_port: int = 5000, host: str = "127.0.0.1"):
        # Compatibility: some older in-memory Network constructs call Node(i, network)
        # Detect that case by duck-typing the second parameter.
        if not isinstance(base_port, int) and hasattr(base_port, "nodes") and hasattr(base_port, "num_nodes"):
            # In-memory simulated node used by tests
            self.id = int(node_id)
            self.network = base_port
            self.received_messages = []
            self.token = None
            # minimal fields to avoid attribute errors
            self.num_nodes = self.network.num_nodes
            self.next_node_port = None
            self.port = None
            self.is_running = False
            self.has_token = False
            self._lock = threading.Lock()
            self.on_token = None
            self.token_count = 0
            self.data_sent_count = 0
            return

        # Normal socket-backed node
        self.node_id = int(node_id)
        self.base_port = int(base_port)
        self.host = host
        self.port = self.base_port + self.node_id
        self.num_nodes: Optional[int] = None
        self.next_node_port = None
        self.server = None
        self.is_running = False
        self.has_token = False
        self._lock = threading.Lock()
        # Hook: optional callable(payload) invoked when this node receives a token
        self.on_token = None
        # Counters for basic stats
        self.token_count = 0
        self.data_sent_count = 0

    # Compatibility methods for in-memory simulated nodes (used by tests)
    def receive_token(self, token):
        # called by Network to hand over a token
        try:
            self.token = token
            # record event in the in-memory network if available
            try:
                nid = getattr(self, "id", getattr(self, "node_id", None))
                txt = f"node {nid} received token {getattr(token, 'token_id', token)}"
                if hasattr(self, "network") and hasattr(self.network, "_append_event"):
                    self.network._append_event(txt)
                if hasattr(self, "network") and hasattr(self.network, "_log"):
                    self.network._log(txt)
            except Exception:
                pass
        except Exception:
            pass

    def pass_token(self):
        # pass token to next node in the in-memory network
        try:
            tok = getattr(self, "token", None)
            # log that this node is passing the token
            try:
                nid = getattr(self, "id", getattr(self, "node_id", None))
                txt = f"node {nid} passing token {getattr(tok, 'token_id', tok)}"
                if hasattr(self, "network") and hasattr(self.network, "_append_event"):
                    self.network._append_event(txt)
                if hasattr(self, "network") and hasattr(self.network, "_log"):
                    self.network._log(txt)
            except Exception:
                pass
            self.token = None
            self.network.pass_token(tok)
        except Exception:
            pass

    def send_message(self, message: str):
        # deliver message into the simulated network
        try:
            # record send event
            try:
                nid = getattr(self, "id", getattr(self, "node_id", None))
                txt = f"node {nid} sending message: {message}"
                if hasattr(self, "network") and hasattr(self.network, "_append_event"):
                    self.network._append_event(txt)
                if hasattr(self, "network") and hasattr(self.network, "_log"):
                    self.network._log(txt)
            except Exception:
                pass
            self.network.receive_message(message, self.id)
        except Exception as e:
            print(f"[Node {getattr(self, 'id', '?')}] send_message error: {e}")

    def set_ring(self, num_nodes: int):
        self.num_nodes = int(num_nodes)
        self.next_node_port = self.base_port + ((self.node_id + 1) % self.num_nodes)

    def start(self) -> None:
        """Start server thread to listen for incoming messages."""
        self.is_running = True
        t = threading.Thread(target=self._serve_forever, daemon=True)
        t.start()
        print(f"[Node {self.node_id}] listening on {self.host}:{self.port}")

    def stop(self) -> None:
        self.is_running = False
        try:
            if self.server:
                self.server.close()
        except Exception:
            pass

    def _serve_forever(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.server.listen(5)

        while self.is_running:
            try:
                self.server.settimeout(1.0)
                client, addr = self.server.accept()
                threading.Thread(target=self._handle_client, args=(client,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    print(f"[Node {self.node_id}] server error: {e}")

    def _handle_client(self, client_sock: socket.socket) -> None:
        try:
            data = client_sock.recv(4096)
            if not data:
                return
            payload = json.loads(data.decode("utf-8"))
            mtype = payload.get("type")
            if mtype == "TOKEN":
                self._on_token(payload)
            elif mtype == "DATA":
                self._on_data(payload)
            else:
                print(f"[Node {self.node_id}] unknown message type: {mtype}")
        except Exception as e:
            print(f"[Node {self.node_id}] client handler error: {e}")
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    def _on_token(self, payload: dict) -> None:
        with self._lock:
            self.has_token = True
        # increment counter
        try:
            self.token_count += 1
        except Exception:
            pass
        token_id = payload.get("token_id")
        print(f"[Node {self.node_id}] received TOKEN (id={token_id})")

        # Optional user callback to perform actions while holding the token (e.g. send DATA)
        try:
            if callable(self.on_token):
                # call synchronously so demo actions happen before forwarding
                self.on_token(payload)
        except Exception as e:
            print(f"[Node {self.node_id}] on_token callback error: {e}")

        # simulate small work while holding token
        time.sleep(0.8)

        # forward the token to next node
        self.forward_token(token_id)

    def _on_data(self, payload: dict) -> None:
        dest = payload.get("dest")
        src = payload.get("src")
        body = payload.get("body")
        if dest == self.node_id:
            print(f"[Node {self.node_id}] DATA from {src}: {body}")
        else:
            # forward along the ring
            self._send_payload(payload, self.next_node_port)

    def forward_token(self, token_id=None) -> None:
        with self._lock:
            if not self.has_token:
                return
            self.has_token = False

        payload = {"type": "TOKEN", "token_id": token_id or id(time.time()), "from": self.node_id}
        # destination info for nicer logging
        try:
            dest_id = (self.node_id + 1) % self.num_nodes if self.num_nodes else None
        except Exception:
            dest_id = None
        if dest_id is not None:
            print(f"[Node {self.node_id}] forwarding TOKEN to node {dest_id} (port {self.next_node_port})")
        else:
            print(f"[Node {self.node_id}] forwarding TOKEN to port {self.next_node_port}")
        self._send_payload(payload, self.next_node_port)

    def send_data(self, dest_node: int, body: str) -> None:
        payload = {"type": "DATA", "src": self.node_id, "dest": int(dest_node), "body": body}
        # send into ring (to next hop)
        print(f"[Node {self.node_id}] sending DATA to node {dest_node} via port {self.next_node_port}: {body}")
        self._send_payload(payload, self.next_node_port)
        try:
            self.data_sent_count += 1
        except Exception:
            pass

    def _send_payload(self, payload: dict, port: int) -> None:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((self.host, port))
            s.sendall(json.dumps(payload).encode("utf-8"))
            s.close()
            # successful send - log to stdout for terminal visibility
            try:
                ptype = payload.get("type")
                print(f"[Node {self.node_id}] sent {ptype} to port {port}")
            except Exception:
                pass
        except Exception as e:
            print(f"[Node {self.node_id}] failed to send to port {port}: {e}")

    def inject_initial_token(self) -> None:
        # Only used by bootstrap node to start the token
        payload = {"type": "TOKEN", "token_id": id(self)}
        print(f"[Node {self.node_id}] injecting initial token to self")
        # Deliver to self by calling handler
        threading.Thread(target=self._on_token, args=(payload,), daemon=True).start()

    def __str__(self) -> str:
        return f"Node(id={self.node_id}, port={self.port})"