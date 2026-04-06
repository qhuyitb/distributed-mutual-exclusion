import threading
import time
from typing import Any, Dict, List, Optional

from simulation.contracts import (
    AlgorithmAdapter,
    Event,
    EventType,
    Message,
    MessageType,
)


class CentralizedAdapter(AlgorithmAdapter):
    def __init__(self, coordinator_cls, node_cls):
        self.coordinator_cls = coordinator_cls
        self.node_cls = node_cls

        self.coordinator = None
        self.nodes: Dict[int, Any] = {}
        self.events: List[Event] = []
        self.seq_num = 0
        self.started = False
        self.network_delay_ms = 0

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
        data: Optional[dict] = None,
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
        data: Optional[dict] = None,
    ) -> None:
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
        self._emit_event(EventType.MESSAGE_RECEIVED, receiver_id if receiver_id is not None else -1, msg, data)

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
        self.network_delay_ms = network_delay_ms
        self.raw_stats = {
            "messages_sent": 0,
            "cs_entries": 0,
            "cs_exits": 0,
            "node_crashes": 0,
            "node_recovers": 0,
            "request_cs_calls": 0,
            "release_cs_calls": 0,
        }

        self.coordinator = self.coordinator_cls(adapter=self)
        self.nodes = {}

        for node_id in range(1, num_nodes + 1):
            self.nodes[node_id] = self.node_cls(
                node_id=node_id,
                coordinator=self.coordinator,
                adapter=self,
            )

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.started = False

    def request_critical_section(self, node_id: int) -> None:
        if not self.started or node_id not in self.nodes:
            return

        node = self.nodes[node_id]
        if not getattr(node, "active", True):
            return

        t = threading.Thread(target=node.enter_CS, daemon=True)
        t.start()

    def release_critical_section(self, node_id: int) -> None:
        if node_id not in self.nodes:
            return

        self.raw_stats["release_cs_calls"] += 1
        node = self.nodes[node_id]
        if hasattr(node, "force_release"):
            node.force_release()

    def crash_node(self, node_id: int) -> None:
        if node_id not in self.nodes:
            return
        self.nodes[node_id].active = False
        self.log_node_crash(node_id)

    def recover_node(self, node_id: int) -> None:
        if node_id not in self.nodes:
            return
        self.nodes[node_id].active = True
        self.log_node_recover(node_id)

    def send_message(self, message: Message) -> None:
        self._emit_event(EventType.MESSAGE_SENT, message.sender_id, message, message.data)

    def get_event_log(self) -> List[Event]:
        return self.events

    def collect_stats(self) -> Dict[str, Any]:
        return self.raw_stats.copy()