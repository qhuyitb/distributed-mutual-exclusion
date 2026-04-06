import threading
import time
from typing import Any, Dict, List, Optional

from simulation.contracts import (
    AlgorithmAdapter,
    Event,
    EventType,
    Message,
)

from ricart_agrawala.node import Node


class RicartAgrawalaAdapter(AlgorithmAdapter):
    def __init__(self, base_port: int = 6100, host: str = "127.0.0.1"):
        self.base_port = base_port
        self.host = host

        self.nodes: Dict[int, Any] = {}
        self.events: List[Event] = []
        self.seq_num = 0
        self.started = False

        self.raw_stats = {
            "messages_sent": 0,
            "cs_entries": 0,
            "cs_exits": 0,
            "node_crashes": 0,
            "node_recovers": 0,
            "request_cs_calls": 0,
            "release_cs_calls": 0,
        }

    def _next_seq(self) -> int:
        self.seq_num += 1
        return self.seq_num

    def _make_message(
        self,
        msg_type: str,
        sender_id: int,
        receiver_id: Optional[int],
        data=None,
    ) -> Message:
        return Message(
            msg_type=msg_type,
            sender_id=sender_id,
            receiver_id=receiver_id,
            sequence_num=self._next_seq(),
            timestamp=time.time(),
            data=data or {},
        )

    def _emit_event(
        self,
        event_type: str,
        node_id: int,
        message: Optional[Message] = None,
        data=None,
    ):
        self.events.append(
            Event(
                event_type=event_type,
                node_id=node_id,
                timestamp=time.time(),
                message=message,
                data=data or {},
            )
        )

    def log_message_sent(self, msg_type: str, sender_id: int, receiver_id: Optional[int], data=None):
        msg = self._make_message(msg_type, sender_id, receiver_id, data)
        self._emit_event(EventType.MESSAGE_SENT, sender_id, msg, data)
        self.raw_stats["messages_sent"] += 1

    def log_message_received(self, msg_type: str, sender_id: int, receiver_id: Optional[int], data=None):
        msg = self._make_message(msg_type, sender_id, receiver_id, data)
        self._emit_event(
            EventType.MESSAGE_RECEIVED,
            receiver_id if receiver_id is not None else -1,
            msg,
            data,
        )

    def log_request_cs(self, node_id: int):
        self._emit_event(EventType.REQUEST_CS, node_id)
        self.raw_stats["request_cs_calls"] += 1

    def log_enter_cs(self, node_id: int):
        self._emit_event(EventType.ENTER_CS, node_id)
        self.raw_stats["cs_entries"] += 1

    def log_exit_cs(self, node_id: int):
        self._emit_event(EventType.EXIT_CS, node_id)
        self.raw_stats["cs_exits"] += 1

    def log_node_crash(self, node_id: int):
        self._emit_event(EventType.NODE_CRASH, node_id)
        self.raw_stats["node_crashes"] += 1

    def log_node_recover(self, node_id: int):
        self._emit_event(EventType.NODE_RECOVER, node_id)
        self.raw_stats["node_recovers"] += 1

    def setup(self, num_nodes: int, network_delay_ms: int = 0) -> None:
        self.events = []
        self.seq_num = 0
        self.started = False
        self.raw_stats = {
            "messages_sent": 0,
            "cs_entries": 0,
            "cs_exits": 0,
            "node_crashes": 0,
            "node_recovers": 0,
            "request_cs_calls": 0,
            "release_cs_calls": 0,
        }

        self.nodes = {}
        node_configs = {}

        for node_id in range(1, num_nodes + 1):
            node_configs[node_id] = {
                "host": self.host,
                "port": self.base_port + node_id,
            }

        for node_id in range(1, num_nodes + 1):
            peers = {
                peer_id: (cfg["host"], cfg["port"])
                for peer_id, cfg in node_configs.items()
                if peer_id != node_id
            }

            node = Node(
                node_id=node_id,
                host=node_configs[node_id]["host"],
                port=node_configs[node_id]["port"],
                peers=peers,
                adapter=self,
            )
            self.nodes[node_id] = node

    def start(self) -> None:
        for node in self.nodes.values():
            node.start()
        time.sleep(1.0)
        self.started = True

    def stop(self) -> None:
        for node in self.nodes.values():
            if hasattr(node, "stop"):
                node.stop()
        self.started = False

    def request_critical_section(self, node_id: int) -> None:
        if not self.started or node_id not in self.nodes:
            return

        node = self.nodes[node_id]
        if not getattr(node, "active", True):
            return

        t = threading.Thread(target=node.request_cs, daemon=True)
        t.start()

    def release_critical_section(self, node_id: int) -> None:
        self.raw_stats["release_cs_calls"] += 1
        node = self.nodes.get(node_id)
        if node and hasattr(node, "force_release"):
            node.force_release()

    def crash_node(self, node_id: int) -> None:
        node = self.nodes.get(node_id)
        if not node:
            return
        node.stop()
        self.log_node_crash(node_id)

    def recover_node(self, node_id: int) -> None:
        self.log_node_recover(node_id)

    def send_message(self, message: Message) -> None:
        self._emit_event(EventType.MESSAGE_SENT, message.sender_id, message, message.data)

    def get_event_log(self) -> List[Event]:
        return self.events

    def collect_stats(self) -> Dict[str, Any]:
        return self.raw_stats.copy()