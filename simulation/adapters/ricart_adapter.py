from __future__ import annotations

import importlib
import sys
import threading
import time
from pathlib import Path
from types import MethodType
from typing import Dict, List, Optional

from simulation.contracts import (
    AlgorithmAdapter,
    AlgorithmType,
    EventRecord,
    EventType,
    MessageType,
    ScenarioDefinition,
)
from .centralized_adapter import EventCollector


# -------------------------------------------------------------------
# Load đúng code Ricart-Agrawala từ thư mục main hiện tại
# Vì module của bạn kia đang dùng kiểu "from message import ..."
# nên adapter thêm path ricart_agrawala vào sys.path để tái sử dụng.
# -------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
_RA_DIR = _REPO_ROOT / "ricart_agrawala"

if str(_RA_DIR) not in sys.path:
    sys.path.insert(0, str(_RA_DIR))

ra_node_module = importlib.import_module("node")
ra_message_module = importlib.import_module("message")

RANodeManager = ra_node_module.NodeManager
create_request_message = ra_message_module.create_request_message
create_reply_message = ra_message_module.create_reply_message


def _external_node_id(internal_id: int) -> int:
    return internal_id + 1


def _internal_node_id(external_id: int) -> int:
    return external_id - 1


class RicartAgrawalaAdapter(AlgorithmAdapter):
    def __init__(self) -> None:
        self._scenario: Optional[ScenarioDefinition] = None
        self._collector = EventCollector()
        self._manager = None
        self._nodes = []
        self._worker_threads: List[threading.Thread] = []
        self._started = False

    @property
    def algorithm_type(self) -> AlgorithmType:
        return AlgorithmType.RICART_AGRAWALA

    def setup(self, scenario: ScenarioDefinition) -> None:
        self._scenario = scenario
        self._collector = EventCollector()
        self._worker_threads = []

        self._manager = RANodeManager(scenario.num_nodes)
        self._nodes = self._manager.nodes

        for node in self._nodes:
            self._instrument_node(node)

    def start(self) -> None:
        if self._scenario is None:
            raise RuntimeError("Adapter is not set up")

        self._started = True

        for node in self._nodes:
            self._collector.add(
                event_type=EventType.NODE_STARTED,
                node_id=_external_node_id(node.id),
                details={"role": "participant", "algorithm": "ricart_agrawala"},
            )

    def request_cs(self, node_id: int) -> None:
        if not self._started:
            raise RuntimeError("Adapter has not been started")
        if self._scenario is None:
            raise RuntimeError("Scenario is missing")

        internal_id = _internal_node_id(node_id)
        if internal_id < 0 or internal_id >= len(self._nodes):
            raise ValueError(f"Unknown node_id: {node_id}")

        node = self._nodes[internal_id]

        def worker() -> None:
            try:
                node.enter_cs()
            except Exception as exc:
                self._collector.add(
                    event_type=EventType.ERROR,
                    node_id=node_id,
                    details={"error": str(exc)},
                )

        thread = threading.Thread(target=worker, name=f"ra-node-{node_id}-request")
        thread.start()
        self._worker_threads.append(thread)

    def stop(self) -> None:
        for thread in self._worker_threads:
            thread.join(timeout=10.0)

        for node in self._nodes:
            self._collector.add(
                event_type=EventType.NODE_STOPPED,
                node_id=_external_node_id(node.id),
                details={"role": "participant", "algorithm": "ricart_agrawala"},
            )

        self._started = False

    def collect_events(self) -> List[EventRecord]:
        return self._collector.snapshot()

    def set_next_cs_duration(self, node_id: int, duration_seconds: float) -> None:
        internal_id = _internal_node_id(node_id)
        if internal_id < 0 or internal_id >= len(self._nodes):
            raise ValueError(f"Unknown node_id: {node_id}")
        setattr(self._nodes[internal_id], "_next_cs_duration_seconds", float(duration_seconds))

    # ------------------------------------------------------------------
    # Instrument đúng logic lõi của main, thêm event log cho TV4
    # ------------------------------------------------------------------
    def _instrument_node(self, node) -> None:
        collector = self._collector

        def instrumented_enter_cs(inner_self) -> None:
            with inner_self.lock:
                inner_self.logical_clock += 1
                request_ts = inner_self.logical_clock
                inner_self.request_queue.append((inner_self.id, request_ts))
                inner_self.waiting_for_replies = set(
                    i for i in range(len(inner_self.all_nodes)) if i != inner_self.id
                )
                inner_self.replies_received = 0
                inner_self.seq_num += 1
                inner_self.my_request_timestamp = request_ts
                nodes_to_send = list(inner_self.waiting_for_replies)
                num_expected = len(inner_self.waiting_for_replies)

            collector.add(
                event_type=EventType.REQUEST_CS,
                node_id=_external_node_id(inner_self.id),
                details={
                    "lamport_timestamp": request_ts,
                    "expected_replies": num_expected,
                },
            )

            for peer in inner_self.all_nodes:
                if peer.id in nodes_to_send:
                    msg = create_request_message(
                        sender_id=inner_self.id,
                        receiver_id=peer.id,
                        timestamp=request_ts,
                        seq_num=inner_self.seq_num,
                    )

                    collector.add(
                        event_type=EventType.MESSAGE_SENT,
                        node_id=_external_node_id(inner_self.id),
                        peer_id=_external_node_id(peer.id),
                        message_type=MessageType.REQUEST,
                        details={
                            "lamport_timestamp": request_ts,
                            "sequence_num": inner_self.seq_num,
                        },
                    )

                    peer.receive_request(msg)

            with inner_self.lock:
                while inner_self.replies_received < num_expected:
                    inner_self.condition.wait()

            collector.add(
                event_type=EventType.ENTER_CS,
                node_id=_external_node_id(inner_self.id),
                details={
                    "lamport_timestamp": request_ts,
                    "replies_received": inner_self.replies_received,
                },
            )

            inner_self.in_cs = True
            time.sleep(getattr(inner_self, "_next_cs_duration_seconds", inner_self.cs_work_time))
            inner_self.exit_cs()

        def instrumented_exit_cs(inner_self) -> None:
            collector.add(
                event_type=EventType.EXIT_CS,
                node_id=_external_node_id(inner_self.id),
                details={"phase": "before_reply_pending"},
            )

            with inner_self.lock:
                inner_self.in_cs = False
                inner_self.my_request_timestamp = float("inf")
                inner_self.request_queue = ra_node_module.deque(
                    (nid, ts) for nid, ts in inner_self.request_queue if nid != inner_self.id
                )
                pending = list(inner_self.request_queue)
                inner_self.logical_clock += 1
                reply_ts = inner_self.logical_clock

            for requester_id, _ in pending:
                msg = create_reply_message(
                    sender_id=inner_self.id,
                    receiver_id=requester_id,
                    timestamp=reply_ts,
                    seq_num=inner_self.seq_num,
                )

                collector.add(
                    event_type=EventType.MESSAGE_SENT,
                    node_id=_external_node_id(inner_self.id),
                    peer_id=_external_node_id(requester_id),
                    message_type=MessageType.REPLY,
                    details={
                        "lamport_timestamp": reply_ts,
                        "reply_mode": "deferred",
                    },
                )

                inner_self.all_nodes[requester_id].receive_reply(msg)

        def instrumented_receive_request(inner_self, msg) -> None:
            collector.add(
                event_type=EventType.MESSAGE_RECEIVED,
                node_id=_external_node_id(inner_self.id),
                peer_id=_external_node_id(msg.sender_id),
                message_type=MessageType.REQUEST,
                details={
                    "lamport_timestamp": msg.timestamp,
                    "sequence_num": msg.sequence_num,
                },
            )

            inner_self.update_clock(msg.timestamp)

            with inner_self.lock:
                inner_self.request_queue.append((msg.sender_id, msg.timestamp))
                incoming_priority = (msg.timestamp, msg.sender_id)
                my_priority = (inner_self.my_request_timestamp, inner_self.id)
                should_reply = (
                    not inner_self.in_cs
                    and (not inner_self.waiting_for_replies or incoming_priority < my_priority)
                )
                reply_ts = inner_self.logical_clock

            if should_reply:
                reply_msg = create_reply_message(
                    sender_id=inner_self.id,
                    receiver_id=msg.sender_id,
                    timestamp=reply_ts,
                    seq_num=msg.sequence_num,
                )

                collector.add(
                    event_type=EventType.MESSAGE_SENT,
                    node_id=_external_node_id(inner_self.id),
                    peer_id=_external_node_id(msg.sender_id),
                    message_type=MessageType.REPLY,
                    details={
                        "lamport_timestamp": reply_ts,
                        "reply_mode": "immediate",
                    },
                )

                inner_self.all_nodes[msg.sender_id].receive_reply(reply_msg)

        def instrumented_receive_reply(inner_self, msg) -> None:
            collector.add(
                event_type=EventType.MESSAGE_RECEIVED,
                node_id=_external_node_id(inner_self.id),
                peer_id=_external_node_id(msg.sender_id),
                message_type=MessageType.REPLY,
                details={
                    "lamport_timestamp": msg.timestamp,
                    "sequence_num": msg.sequence_num,
                },
            )

            inner_self.update_clock(msg.timestamp)

            with inner_self.lock:
                if msg.sender_id in inner_self.waiting_for_replies:
                    inner_self.waiting_for_replies.discard(msg.sender_id)
                    inner_self.replies_received += 1
                    if inner_self.replies_received == len(inner_self.all_nodes) - 1:
                        inner_self.condition.notify_all()

        node.enter_cs = MethodType(instrumented_enter_cs, node)
        node.exit_cs = MethodType(instrumented_exit_cs, node)
        node.receive_request = MethodType(instrumented_receive_request, node)
        node.receive_reply = MethodType(instrumented_receive_reply, node)