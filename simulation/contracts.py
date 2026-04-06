from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AlgorithmType(str, Enum):
    CENTRALIZED = "centralized"
    RICART_AGRAWALA = "ricart_agrawala"
    TOKEN_RING = "token_ring"


class EventType(str, Enum):
    SIMULATION_START = "simulation_start"
    SIMULATION_END = "simulation_end"

    NODE_STARTED = "node_started"
    NODE_STOPPED = "node_stopped"
    NODE_CRASH = "node_crash"
    NODE_RECOVER = "node_recover"

    REQUEST_CS = "request_cs"
    ENTER_CS = "enter_cs"
    EXIT_CS = "exit_cs"

    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"

    TOKEN_RECEIVED = "token_received"
    TOKEN_FORWARDED = "token_forwarded"

    ERROR = "error"
    INFO = "info"


class ActionType(str, Enum):
    REQUEST_CS = "request_cs"
    CRASH_NODE = "crash_node"
    RECOVER_NODE = "recover_node"
    SLEEP = "sleep"


class MessageType(str, Enum):
    REQUEST = "REQUEST"
    REPLY = "REPLY"
    GRANT = "GRANT"
    RELEASE = "RELEASE"
    TOKEN = "TOKEN"
    DATA = "DATA"
    UNKNOWN = "UNKNOWN"


@dataclass(slots=True)
class EventRecord:
    timestamp: float
    event_type: EventType
    node_id: Optional[int] = None
    peer_id: Optional[int] = None
    message_type: Optional[MessageType] = None
    request_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class NodeAction:
    at_seconds: float
    action_type: ActionType
    node_id: Optional[int] = None
    duration_seconds: Optional[float] = None
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ScenarioDefinition:
    name: str
    description: str
    num_nodes: int
    actions: List[NodeAction]
    network_delay_ms: int = 0
    timeout_seconds: float = 30.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class SimulationMetrics:
    total_messages: int = 0
    request_count: int = 0
    cs_entries: int = 0

    avg_waiting_time: float = 0.0
    max_waiting_time: float = 0.0

    mutual_exclusion_violations: int = 0
    fairness_violations: int = 0

    messages_by_type: Dict[str, int] = field(default_factory=dict)
    entries_by_node: Dict[int, int] = field(default_factory=dict)
    waiting_time_by_node: Dict[int, List[float]] = field(default_factory=dict)


@dataclass(slots=True)
class SimulationResult:
    algorithm: AlgorithmType
    scenario_name: str
    success: bool
    started_at: float
    finished_at: float
    duration_seconds: float
    metrics: SimulationMetrics
    events: List[EventRecord] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class AlgorithmAdapter(ABC):
    """
    Lớp bọc chung cho từng thuật toán.
    TV4 chỉ làm việc với interface này, không gọi trực tiếp code lõi từng module.
    """

    @property
    @abstractmethod
    def algorithm_type(self) -> AlgorithmType:
        raise NotImplementedError

    @abstractmethod
    def setup(self, scenario: ScenarioDefinition) -> None:
        raise NotImplementedError

    @abstractmethod
    def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def request_cs(self, node_id: int) -> None:
        raise NotImplementedError

    def crash_node(self, node_id: int) -> None:
        raise NotImplementedError(
            f"{self.algorithm_type.value} does not support crash_node yet"
        )

    def recover_node(self, node_id: int) -> None:
        raise NotImplementedError(
            f"{self.algorithm_type.value} does not support recover_node yet"
        )

    @abstractmethod
    def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def collect_events(self) -> List[EventRecord]:
        raise NotImplementedError


def make_request_id(node_id: int, timestamp: float) -> str:
    return f"req-{node_id}-{int(timestamp * 1000)}"