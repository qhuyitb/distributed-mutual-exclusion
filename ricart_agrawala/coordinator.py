"""
Network Coordinator - Server quản lý các nodes
Broadcast NODES_UPDATE mỗi khi có node mới register hoặc disconnect
"""
import socket
import threading
import json
import time
from typing import Dict, Tuple


class Coordinator:
    """Coordinator server - quản lý node registration và broadcast updates"""

    def __init__(self, host: str = "localhost", port: int = 5000):
        self.host = host
        self.port = port
        self.node_addresses: Dict[int, Tuple[str, int]] = {}  # node_id -> (host, port)
        self.node_sockets: Dict[int, socket.socket] = {}      # node_id -> socket
        self.lock = threading.Lock()
        self.server_socket = None
        self.running = False

    # ------------------------------------------------------------------ start/stop
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        self.running = True

        print(f"\n[Coordinator] Started on {self.host}:{self.port}")
        print(f"[Coordinator] Waiting for nodes to register...\n")

        threading.Thread(target=self._accept_connections, daemon=True).start()

    def stop(self):
        self.running = False
        with self.lock:
            for sock in self.node_sockets.values():
                try:
                    sock.close()
                except Exception:
                    pass
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

    # ------------------------------------------------------------------ internal
    def _accept_connections(self):
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_node,
                    args=(client_socket, client_address),
                    daemon=True,
                ).start()
            except Exception:
                break

    def _handle_node(self, client_socket: socket.socket, client_address: tuple):
        node_id = None
        try:
            data = client_socket.recv(4096).decode('utf-8')
            if not data:
                return

            msg_dict = json.loads(data)

            if msg_dict.get('type') == 'REGISTER':
                node_id = msg_dict['node_id']
                node_port = msg_dict['listen_port']

                with self.lock:
                    self.node_addresses[node_id] = (client_address[0], node_port)
                    self.node_sockets[node_id] = client_socket

                print(f"[Coordinator] Node {node_id} registered "
                      f"(listening: {client_address[0]}:{node_port})")

                # Gửi danh sách nodes hiện tại cho node vừa connect
                nodes_info = self._get_nodes_except(node_id)
                client_socket.send(json.dumps({
                    'type': 'NODES_LIST',
                    'nodes': nodes_info,
                }).encode('utf-8'))

                # Broadcast update tới tất cả nodes khác
                self._broadcast_nodes_update()

                # Giữ kết nối sống cho đến khi node disconnect
                while self.running:
                    try:
                        data = client_socket.recv(4096)
                        if not data:
                            break
                    except Exception:
                        break

        except Exception as e:
            print(f"[Coordinator] Error handling node {node_id}: {e}")
        finally:
            if node_id is not None:
                with self.lock:
                    self.node_sockets.pop(node_id, None)
                    self.node_addresses.pop(node_id, None)
                try:
                    client_socket.close()
                except Exception:
                    pass
                print(f"[Coordinator] Node {node_id} disconnected")
                self._broadcast_nodes_update()

    def _get_nodes_except(self, exclude_node_id: int) -> dict:
        with self.lock:
            return {
                str(nid): {'host': host, 'port': port}
                for nid, (host, port) in self.node_addresses.items()
                if nid != exclude_node_id
            }

    def _broadcast_nodes_update(self):
        with self.lock:
            current_nodes = dict(self.node_sockets)

        for node_id, sock in current_nodes.items():
            try:
                nodes_info = self._get_nodes_except(node_id)
                sock.send(json.dumps({
                    'type': 'NODES_UPDATE',
                    'nodes': nodes_info,
                }).encode('utf-8'))
            except Exception as e:
                print(f"[Coordinator] Error broadcasting to Node {node_id}: {e}")


def run_coordinator():
    coordinator = Coordinator(port=5000)
    coordinator.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Coordinator] Shutting down...")
        coordinator.stop()


if __name__ == "__main__":
    run_coordinator()