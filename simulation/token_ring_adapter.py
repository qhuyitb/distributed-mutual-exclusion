import threading
import time
from typing import Any, Dict, List, Optional

from simulation.contracts import (
    AlgorithmAdapter,
    Event,
    EventType,
    Message,
)

from token_ring.src.ring_manager import TokenRingManager
from token_ring.src.message import MessageType


class TokenRingAdapter(AlgorithmAdapter):
    def __init__(self, base_port: int = 8000):
        self.base_port = base_port
        self.manager = None
        self.events: List[Event] = []
        self.seq_num = 0
        self.started = False

        self.pending_requests = set()
        self.last_tokens_received: Dict[int, int] = {}

        self.raw_stats = {
            "messages_sent": 0,
            "cs_entries": 0,
            "cs_exits": 0,
            "node_crashes": 0,
            "node_recovers": 0,
            "request_cs_calls": 0,
            "release_cs_calls": 0,
            "tokens_received_total": 0,
        }

        self.monitor_thread = None
        self.monitor_running = False

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

    def setup(self, num_nodes: int, network_delay_ms: int = 0) -> None:
        self.events = []
        self.seq_num = 0
        self.started = False
        self.pending_requests = set()
        self.last_tokens_received = {}
        self.raw_stats = {
            "messages_sent": 0,
            "cs_entries": 0,
            "cs_exits": 0,
            "node_crashes": 0,
            "node_recovers": 0,
            "request_cs_calls": 0,
            "release_cs_calls": 0,
            "tokens_received_total": 0,
        }

        self.manager = TokenRingManager(num_nodes=num_nodes, base_port=self.base_port)
        self.manager.create_ring()

        for node in self.manager.get_all_nodes():
            stats = node.get_stats()
            self.last_tokens_received[stats["node_id"]] = stats["tokens_received"]

    def start(self) -> None:
        self.manager.start_ring()
        self.started = True
        self.monitor_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self) -> None:
        self.monitor_running = False
        if self.manager:
            self.manager.stop_ring()
        self.started = False

    def request_critical_section(self, node_id: int) -> None:
        if not self.started:
            return

        self.pending_requests.add(node_id)
        self.raw_stats["request_cs_calls"] += 1
        self._emit_event(EventType.REQUEST_CS, node_id)

    def release_critical_section(self, node_id: int) -> None:
        self.raw_stats["release_cs_calls"] += 1
        # Token Ring bản này không cần release riêng;
        # node sẽ "giữ token ngắn" rồi token tự pass tiếp.

    def crash_node(self, node_id: int) -> None:
        self._emit_event(EventType.NODE_CRASH, node_id)
        self.raw_stats["node_crashes"] += 1

    def recover_node(self, node_id: int) -> None:
        self._emit_event(EventType.NODE_RECOVER, node_id)
        self.raw_stats["node_recovers"] += 1

    def send_message(self, message: Message) -> None:
        self._emit_event(EventType.MESSAGE_SENT, message.sender_id, message, message.data)

    def get_event_log(self) -> List[Event]:
        return self.events

    def collect_stats(self) -> Dict[str, Any]:
        return self.raw_stats.copy()

    def _monitor_loop(self):
        while self.monitor_running and self.manager:
            try:
                for node in self.manager.get_all_nodes():
                    stats = node.get_stats()
                    node_id = stats["node_id"]
                    current_tokens = stats["tokens_received"]
                    prev_tokens = self.last_tokens_received.get(node_id, 0)

                    if current_tokens > prev_tokens:
                        prev_node = (node_id - 1) % len(self.manager.get_all_nodes())

                        sent_msg = self._make_message(
                            msg_type=MessageType.TOKEN.value,
                            sender_id=prev_node,
                            receiver_id=node_id,
                            data={"tokens_received": current_tokens},
                        )
                        self._emit_event(EventType.MESSAGE_SENT, prev_node, sent_msg)
                        self.raw_stats["messages_sent"] += 1

                        recv_msg = self._make_message(
                            msg_type=MessageType.TOKEN.value,
                            sender_id=prev_node,
                            receiver_id=node_id,
                            data={"tokens_received": current_tokens},
                        )
                        self._emit_event(EventType.MESSAGE_RECEIVED, node_id, recv_msg)
                        self.raw_stats["tokens_received_total"] += (current_tokens - prev_tokens)

                        # nếu node đang chờ vào CS thì cho nó "vào CS" ngay khi có token
                        if node_id in self.pending_requests:
                            self._emit_event(EventType.ENTER_CS, node_id)
                            self.raw_stats["cs_entries"] += 1

                            time.sleep(0.2)

                            self._emit_event(EventType.EXIT_CS, node_id)
                            self.raw_stats["cs_exits"] += 1
                            self.pending_requests.remove(node_id)

                    self.last_tokens_received[node_id] = current_tokens

                time.sleep(0.1)
            except Exception:
                time.sleep(0.1)