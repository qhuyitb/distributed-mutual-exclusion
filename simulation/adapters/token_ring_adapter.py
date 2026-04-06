from __future__ import annotations

import importlib.util
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


_REPO_ROOT = Path(__file__).resolve().parents[2]
_TR_DIR = _REPO_ROOT / "token_ring" / "src"


def _load_module_from_path(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_token_ring_modules():
    originals = {name: sys.modules.get(name) for name in ("message", "Token", "node", "network")}

    try:
        tr_message = _load_module_from_path("token_ring_message_mod", _TR_DIR / "message.py")
        sys.modules["message"] = tr_message

        tr_token = _load_module_from_path("token_ring_token_mod", _TR_DIR / "Token.py")
        sys.modules["Token"] = tr_token

        tr_node = _load_module_from_path("token_ring_node_mod", _TR_DIR / "node.py")
        sys.modules["node"] = tr_node

        tr_network = _load_module_from_path("token_ring_network_mod", _TR_DIR / "network.py")
        sys.modules["network"] = tr_network

        return tr_message, tr_token, tr_node, tr_network
    finally:
        for name, original in originals.items():
            if original is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = original


_tr_message_module, _tr_token_module, _tr_node_module, _tr_network_module = _load_token_ring_modules()
TRNetwork = _tr_network_module.Network


def _external_node_id(internal_id: int) -> int:
    return internal_id + 1


class TokenRingAdapter(AlgorithmAdapter):
    def __init__(self) -> None:
        self._scenario: Optional[ScenarioDefinition] = None
        self._collector = EventCollector()
        self._network = None
        self._started = False

        self._state_lock = threading.Lock()
        self._request_pending: Dict[int, bool] = {}
        self._cs_durations: Dict[int, float] = {}
        self._current_cs_node: Optional[int] = None

        self._loop_thread: Optional[threading.Thread] = None
        self._stop_requested = threading.Event()

        # Đánh dấu pass token kế tiếp có thuộc luồng phục vụ request hay không
        self._count_next_pass_as_request_related = False

        self._token_pass_interval_seconds = 0.05

    @property
    def algorithm_type(self) -> AlgorithmType:
        return AlgorithmType.TOKEN_RING

    def setup(self, scenario: ScenarioDefinition) -> None:
        self._scenario = scenario
        self._collector = EventCollector()
        self._network = TRNetwork(scenario.num_nodes)
        self._started = False
        self._stop_requested = threading.Event()
        self._loop_thread = None

        self._request_pending = {node_id: False for node_id in range(1, scenario.num_nodes + 1)}
        self._cs_durations = {node_id: 1.0 for node_id in range(1, scenario.num_nodes + 1)}
        self._current_cs_node = None
        self._count_next_pass_as_request_related = False

        self._instrument_nodes()

    def start(self) -> None:
        if self._network is None or self._scenario is None:
            raise RuntimeError("Adapter is not set up")

        for node in self._network.nodes:
            self._collector.add(
                event_type=EventType.NODE_STARTED,
                node_id=_external_node_id(node.id),
                details={"role": "participant", "algorithm": "token_ring"},
            )

        self._network.start_network()
        self._started = True

        self._loop_thread = threading.Thread(
            target=self._circulation_loop,
            name="token-ring-loop",
            daemon=True,
        )
        self._loop_thread.start()

    def request_cs(self, node_id: int) -> None:
        if not self._started:
            raise RuntimeError("Adapter has not been started")
        if node_id not in self._request_pending:
            raise ValueError(f"Unknown node_id: {node_id}")

        with self._state_lock:
            self._request_pending[node_id] = True

        self._collector.add(
            event_type=EventType.REQUEST_CS,
            node_id=node_id,
            details={"mode": "wait_for_token"},
        )

    def stop(self) -> None:
        self._stop_requested.set()

        if self._loop_thread is not None:
            self._loop_thread.join(timeout=(self._scenario.timeout_seconds if self._scenario else 10.0))

        if self._network is not None:
            for node in self._network.nodes:
                self._collector.add(
                    event_type=EventType.NODE_STOPPED,
                    node_id=_external_node_id(node.id),
                    details={"role": "participant", "algorithm": "token_ring"},
                )

        self._started = False

    def collect_events(self) -> List[EventRecord]:
        return self._collector.snapshot()

    def set_next_cs_duration(self, node_id: int, duration_seconds: float) -> None:
        if node_id not in self._cs_durations:
            raise ValueError(f"Unknown node_id: {node_id}")
        with self._state_lock:
            self._cs_durations[node_id] = float(duration_seconds)

    def _instrument_nodes(self) -> None:
        if self._network is None or self._scenario is None:
            return

        total_nodes = self._scenario.num_nodes

        for node in self._network.nodes:
            original_receive_token = node.receive_token
            original_pass_token = node.pass_token

            def wrapped_receive_token(inner_self, token, _orig=original_receive_token):
                _orig(token)
                current_ext = _external_node_id(inner_self.id)
                prev_ext = _external_node_id((inner_self.id - 1) % total_nodes)

                self._collector.add(
                    event_type=EventType.TOKEN_RECEIVED,
                    node_id=current_ext,
                    peer_id=prev_ext,
                    message_type=MessageType.TOKEN,
                )
                self._collector.add(
                    event_type=EventType.MESSAGE_RECEIVED,
                    node_id=current_ext,
                    peer_id=prev_ext,
                    message_type=MessageType.TOKEN,
                )

            def wrapped_pass_token(inner_self, _orig=original_pass_token):
                current_ext = _external_node_id(inner_self.id)
                next_ext = _external_node_id((inner_self.id + 1) % total_nodes)

                with self._state_lock:
                    has_pending = any(self._request_pending.values())
                    in_service = self._current_cs_node is not None
                    force_related = self._count_next_pass_as_request_related

                    traffic_scope = "request_related" if (has_pending or in_service or force_related) else "idle"

                    if force_related:
                        self._count_next_pass_as_request_related = False

                self._collector.add(
                    event_type=EventType.TOKEN_FORWARDED,
                    node_id=current_ext,
                    peer_id=next_ext,
                    message_type=MessageType.TOKEN,
                    details={"traffic_scope": traffic_scope},
                )
                self._collector.add(
                    event_type=EventType.MESSAGE_SENT,
                    node_id=current_ext,
                    peer_id=next_ext,
                    message_type=MessageType.TOKEN,
                    details={"traffic_scope": traffic_scope},
                )

                _orig()

            node.receive_token = MethodType(wrapped_receive_token, node)
            node.pass_token = MethodType(wrapped_pass_token, node)

    def _circulation_loop(self) -> None:
        if self._network is None or self._scenario is None:
            return

        while True:
            with self._state_lock:
                has_pending = any(self._request_pending.values())
                current_cs_node = self._current_cs_node

            if self._stop_requested.is_set() and not has_pending and current_cs_node is None:
                break

            holder_index = self._network.current_node_index
            holder_node = self._network.nodes[holder_index]
            holder_ext = _external_node_id(holder_index)

            if getattr(holder_node, "token", None) is None:
                time.sleep(0.01)
                continue

            run_cs = False
            cs_duration = 0.0

            with self._state_lock:
                if self._request_pending.get(holder_ext, False):
                    self._request_pending[holder_ext] = False
                    self._current_cs_node = holder_ext
                    run_cs = True
                    cs_duration = self._cs_durations.get(holder_ext, 1.0)

            if run_cs:
                self._collector.add(
                    event_type=EventType.ENTER_CS,
                    node_id=holder_ext,
                    details={"reason": "token_arrived"},
                )

                time.sleep(cs_duration)

                self._collector.add(
                    event_type=EventType.EXIT_CS,
                    node_id=holder_ext,
                    details={"reason": "cs_completed"},
                )

                with self._state_lock:
                    self._current_cs_node = None
                    self._count_next_pass_as_request_related = True

            holder_node.pass_token()
            time.sleep(self._token_pass_interval_seconds)