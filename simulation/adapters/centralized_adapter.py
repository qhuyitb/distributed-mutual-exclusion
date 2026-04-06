from __future__ import annotations

import socket
import threading
import time
from typing import Dict, List, Optional

from simulation.contracts import (
    AlgorithmAdapter,
    AlgorithmType,
    EventRecord,
    EventType,
    MessageType,
    ScenarioDefinition,
)

from centralized.communication import CommunicationLayer
from centralized.coordinator import Coordinator
from centralized.message import Message
from centralized.message import MessageType as CentralizedMessageType
from centralized.node import Node


def _find_free_port() -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _map_message_type(message_type: Optional[CentralizedMessageType]) -> Optional[MessageType]:
    if message_type is None:
        return None

    mapping = {
        CentralizedMessageType.REQUEST: MessageType.REQUEST,
        CentralizedMessageType.GRANT: MessageType.GRANT,
        CentralizedMessageType.RELEASE: MessageType.RELEASE,
    }
    return mapping.get(message_type, MessageType.UNKNOWN)


class EventCollector:
    def __init__(self) -> None:
        self._events: List[EventRecord] = []
        self._lock = threading.Lock()

    def add(
        self,
        event_type: EventType,
        node_id: Optional[int] = None,
        peer_id: Optional[int] = None,
        message_type: Optional[MessageType] = None,
        request_id: Optional[str] = None,
        details: Optional[dict] = None,
    ) -> None:
        event = EventRecord(
            timestamp=time.time(),
            event_type=event_type,
            node_id=node_id,
            peer_id=peer_id,
            message_type=message_type,
            request_id=request_id,
            details=details or {},
        )
        with self._lock:
            self._events.append(event)

    def snapshot(self) -> List[EventRecord]:
        with self._lock:
            return list(sorted(self._events, key=lambda e: e.timestamp))


class InstrumentedCommunicationLayer(CommunicationLayer):
    def __init__(self, collector: EventCollector, network_delay_ms: int = 0) -> None:
        super().__init__()
        self.collector = collector
        self.network_delay_ms = network_delay_ms

    def send(self, message: Message) -> None:
        self.collector.add(
            event_type=EventType.MESSAGE_SENT,
            node_id=message.sender_id,
            peer_id=message.receiver_id,
            message_type=_map_message_type(message.msg_type),
            request_id=str(message.request_id) if message.request_id is not None else None,
            details={"raw_timestamp": message.timestamp},
        )

        if self.network_delay_ms > 0:
            time.sleep(self.network_delay_ms / 1000.0)

        super().send(message)

    @staticmethod
    def _handle_client(endpoint, client_sock: socket.socket) -> None:
        try:
            data = client_sock.recv(4096)
            if not data:
                return
            message = Message.from_bytes(data)

            collector = getattr(endpoint, "_event_collector", None)
            if collector is not None:
                collector.add(
                    event_type=EventType.MESSAGE_RECEIVED,
                    node_id=message.receiver_id,
                    peer_id=message.sender_id,
                    message_type=_map_message_type(message.msg_type),
                    request_id=str(message.request_id) if message.request_id is not None else None,
                    details={"raw_timestamp": message.timestamp},
                )

            endpoint.on_message(message)
        finally:
            try:
                client_sock.close()
            except Exception:
                pass


class InstrumentedCoordinator(Coordinator):
    def __init__(self, coordinator_id: int, comm: CommunicationLayer, collector: EventCollector):
        super().__init__(coordinator_id=coordinator_id, comm=comm)
        self._event_collector = collector


class InstrumentedNode(Node):
    def __init__(
        self,
        node_id: int,
        coordinator_id: int,
        comm: CommunicationLayer,
        collector: EventCollector,
    ):
        super().__init__(node_id=node_id, coordinator_id=coordinator_id, comm=comm)
        self._event_collector = collector
        self.default_cs_duration_seconds = 1.0

    def enter_CS(
        self,
        wait_timeout: float = 10.0,
        cs_duration_seconds: Optional[float] = None,
    ):
        self._event_collector.add(
            event_type=EventType.REQUEST_CS,
            node_id=self.id,
            peer_id=self.coordinator_id,
            message_type=MessageType.REQUEST,
        )

        self.last_request_ts = time.time()
        request = Message(
            msg_type=CentralizedMessageType.REQUEST,
            sender_id=self.id,
            receiver_id=self.coordinator_id,
            timestamp=self.last_request_ts,
        )
        self.comm.send(request)

        granted = self.granted_event.wait(timeout=wait_timeout)
        if not granted:
            raise TimeoutError(
                f"Node {self.id} timeout waiting GRANT - possible coordinator failure"
            )

        self._event_collector.add(
            event_type=EventType.ENTER_CS,
            node_id=self.id,
            details={
                "grant_latency_seconds": self.last_grant_latency,
            },
        )

        time.sleep(cs_duration_seconds or self.default_cs_duration_seconds)

        self.exit_CS()

    def exit_CS(self):
        self._event_collector.add(
            event_type=EventType.EXIT_CS,
            node_id=self.id,
            peer_id=self.coordinator_id,
            message_type=MessageType.RELEASE,
        )

        self.granted_event.clear()
        release = Message(
            msg_type=CentralizedMessageType.RELEASE,
            sender_id=self.id,
            receiver_id=self.coordinator_id,
            timestamp=time.time(),
        )
        self.comm.send(release)


class CentralizedAdapter(AlgorithmAdapter):
    def __init__(self) -> None:
        self._scenario: Optional[ScenarioDefinition] = None
        self._collector = EventCollector()
        self._comm: Optional[InstrumentedCommunicationLayer] = None
        self._coordinator: Optional[InstrumentedCoordinator] = None
        self._nodes: Dict[int, InstrumentedNode] = {}
        self._worker_threads: List[threading.Thread] = []
        self._started = False
        self._coordinator_id = -1

    @property
    def algorithm_type(self) -> AlgorithmType:
        return AlgorithmType.CENTRALIZED

    def setup(self, scenario: ScenarioDefinition) -> None:
        self._scenario = scenario
        self._collector = EventCollector()
        self._worker_threads = []
        self._nodes = {}

        self._comm = InstrumentedCommunicationLayer(
            collector=self._collector,
            network_delay_ms=scenario.network_delay_ms,
        )

        self._coordinator = InstrumentedCoordinator(
            coordinator_id=self._coordinator_id,
            comm=self._comm,
            collector=self._collector,
        )

        coordinator_port = _find_free_port()
        self._comm.register(self._coordinator_id, self._coordinator, port=coordinator_port)

        for node_id in range(1, scenario.num_nodes + 1):
            node = InstrumentedNode(
                node_id=node_id,
                coordinator_id=self._coordinator_id,
                comm=self._comm,
                collector=self._collector,
            )
            self._nodes[node_id] = node
            self._comm.register(node_id, node, port=_find_free_port())

    def start(self) -> None:
        if self._comm is None:
            raise RuntimeError("Adapter is not set up")

        self._comm.start()
        self._started = True

        # Cho listener TCP khởi động xong trước khi gửi message đầu tiên
        time.sleep(0.2)

        self._collector.add(
            event_type=EventType.NODE_STARTED,
            node_id=self._coordinator_id,
            details={"role": "coordinator"},
        )

        for node_id in self._nodes:
            self._collector.add(
                event_type=EventType.NODE_STARTED,
                node_id=node_id,
                details={"role": "participant"},
            )

    def request_cs(self, node_id: int) -> None:
        if not self._started:
            raise RuntimeError("Adapter has not been started")
        if self._scenario is None:
            raise RuntimeError("Scenario is missing")
        if node_id not in self._nodes:
            raise ValueError(f"Unknown node_id: {node_id}")

        node = self._nodes[node_id]

        cs_duration = 1.0
        wait_timeout = self._scenario.timeout_seconds
        # runner sẽ truyền cs_duration_seconds qua action.details
        # ở bước này ta đọc từ attribute tạm trên node nếu có, nếu không dùng mặc định

        def worker() -> None:
            try:
                node.enter_CS(
                    wait_timeout=wait_timeout,
                    cs_duration_seconds=getattr(node, "_next_cs_duration_seconds", cs_duration),
                )
            except Exception as exc:
                self._collector.add(
                    event_type=EventType.ERROR,
                    node_id=node_id,
                    details={"error": str(exc)},
                )

        thread = threading.Thread(target=worker, name=f"centralized-node-{node_id}-request")
        thread.start()
        self._worker_threads.append(thread)

    def stop(self) -> None:
        for thread in self._worker_threads:
            thread.join(timeout=5.0)

        if self._comm is not None:
            self._comm.stop()

        for node_id in self._nodes:
            self._collector.add(
                event_type=EventType.NODE_STOPPED,
                node_id=node_id,
                details={"role": "participant"},
            )

        self._collector.add(
            event_type=EventType.NODE_STOPPED,
            node_id=self._coordinator_id,
            details={"role": "coordinator"},
        )

        self._started = False

    def collect_events(self) -> List[EventRecord]:
        return self._collector.snapshot()

    def set_next_cs_duration(self, node_id: int, duration_seconds: float) -> None:
        if node_id not in self._nodes:
            raise ValueError(f"Unknown node_id: {node_id}")
        setattr(self._nodes[node_id], "_next_cs_duration_seconds", duration_seconds)