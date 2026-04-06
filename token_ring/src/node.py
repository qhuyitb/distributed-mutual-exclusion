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

from message import Message, MessageType


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
            # Lamport clock for logical timestamps (in-memory nodes)
            self.lamport = 0
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
        # Lamport clock for socket-backed node
        self.lamport = 0

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
            # try to parse our Message framing
            try:
                msg = Message.from_bytes(data)
            except Exception:
                # fallback to old dict-based payloads
                payload = json.loads(data.decode("utf-8"))
                mtype = payload.get("type")
                if mtype == "TOKEN":
                    msg = Message(MessageType.TOKEN.value, payload.get("from"), None, payload.get("token_id"), None, data=None)
                else:
                    msg = Message(MessageType.DATA.value, payload.get("src"), payload.get("dest"), None, None, data=payload.get("body"))

            if msg.msg_type == MessageType.TOKEN.value:
                self._on_token(msg)
            elif msg.msg_type == MessageType.DATA.value:
                self._on_data(msg)
            else:
                print(f"[Node {getattr(self,'node_id', '?')}] unknown message type: {msg.msg_type}")
        except Exception as e:
            print(f"[Node {getattr(self,'node_id','?')}] client handler error: {e}")
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    def _on_token(self, msg: Message) -> None:
        # update Lamport clock from incoming message
        try:
            if msg.lamport is not None:
                self.lamport = max(self.lamport, msg.lamport) + 1
            else:
                self.lamport += 1
        except Exception:
            self.lamport = getattr(self, "lamport", 0) + 1

        with self._lock:
            self.has_token = True
        # increment counter
        try:
            self.token_count += 1
        except Exception:
            pass
        token_id = msg.sequence_num
        print(f"[Node {self.node_id}] received TOKEN (id={token_id}) lamport={self.lamport}")

        # Optional user callback to perform actions while holding the token (e.g. send DATA)
        try:
            if callable(self.on_token):
                # call synchronously so demo actions happen before forwarding
                self.on_token(msg)
        except Exception as e:
            print(f"[Node {self.node_id}] on_token callback error: {e}")

        # simulate small work while holding token
        time.sleep(0.8)

        # forward the token to next node
        self.forward_token(token_id)

    def _on_data(self, msg: Message) -> None:
        # update Lamport clock
        try:
            if msg.lamport is not None:
                self.lamport = max(self.lamport, msg.lamport) + 1
            else:
                self.lamport += 1
        except Exception:
            self.lamport = getattr(self, "lamport", 0) + 1

        dest = msg.receiver_id
        src = msg.sender_id
        body = msg.data
        if dest == self.node_id:
            print(f"[Node {self.node_id}] DATA from {src}: {body} lamport={self.lamport}")
        else:
            # forward along the ring: update message lamport and resend
            try:
                msg.lamport = self.lamport
            except Exception:
                pass
            self._send_payload(msg, self.next_node_port)

    def forward_token(self, token_id=None) -> None:
        with self._lock:
            if not self.has_token:
                return
            self.has_token = False

        # Build a Message.token so the sent packet follows message.py structure
        try:
            payload = Message.token(self.node_id, token_id=token_id or id(time.time()), lamport=getattr(self, "lamport", None))
        except Exception:
            # fallback to legacy dict if Message construction fails
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
        # If this node currently holds the token, log that it is entering the
        # critical section before sending the DATA packet (logging only).
        try:
            if getattr(self, "has_token", False):
                print(f"[Node {self.node_id}] Entering Critical Section")
        except Exception:
            pass

        # Build a Message.data_msg so packet conforms to message.py structure
        try:
            payload = Message.data_msg(self.node_id, int(dest_node), body)
        except Exception:
            payload = {"type": "DATA", "src": self.node_id, "dest": int(dest_node), "body": body}
        # send into ring (to next hop)
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
            # Support sending either raw dict payloads (legacy) or Message objects
            if isinstance(payload, Message):
                s.sendall(payload.to_bytes())
            else:
                s.sendall(json.dumps(payload).encode("utf-8"))
            s.close()
            # successful send - log to stdout for terminal visibility
            try:
                if isinstance(payload, Message):
                    ptype = getattr(payload, "msg_type", "MSG")
                else:
                    ptype = payload.get("type")
                print(f"[Node {self.node_id}] sent {ptype} to port {port}")
                # print full structured payload according to message.py
                try:
                    if isinstance(payload, Message):
                        payload_repr = payload.to_dict()
                    else:
                        payload_repr = payload
                    try:
                        print(f"[Node {self.node_id}] payload: {json.dumps(payload_repr, ensure_ascii=False)}")
                    except Exception:
                        # fallback if payload contains non-serializable objects
                        print(f"[Node {self.node_id}] payload: {payload_repr}")
                except Exception:
                    pass
            except Exception:
                pass
        except Exception as e:
            print(f"[Node {self.node_id}] failed to send to port {port}: {e}")

    def inject_initial_token(self) -> None:
        # Only used by bootstrap node to start the token
        # Build a Message.token so _on_token receives a Message instance (not a raw dict)
        try:
            msg = Message.token(self.node_id, token_id=id(self), lamport=getattr(self, "lamport", None))
        except Exception:
            # fallback to a minimal Message-like dict if Message class is unavailable
            msg = {"type": "TOKEN", "token_id": id(self), "from": self.node_id}
        print(f"[Node {self.node_id}] injecting initial token to self")
        # Deliver to self by calling handler
        threading.Thread(target=self._on_token, args=(msg,), daemon=True).start()

    def __str__(self) -> str:
        return f"Node(id={self.node_id}, port={self.port})"