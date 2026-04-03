"""
Quản lý vòng Token Ring
Cấu hình, khởi tạo và điều phối các node trong vòng
"""
import time
import threading
from typing import List, Dict, Optional
from node import Node
from message import Message, MessageType, create_token_message
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - RingManager - %(levelname)s - %(message)s'
)


class TokenRingManager:
    """
    Quản lý vòng Token Ring
    
    Chức năng:
    - Tạo và cấu hình các node
    - Khởi tạo token và gửi tới node đầu tiên
    - Giám sát và quản lý hoạt động của các node
    - Thống kê và báo cáo
    """
    
    def __init__(self, num_nodes: int = 4, base_port: int = 5000):
        """
        Khởi tạo Ring Manager
        
        Args:
            num_nodes: Số lượng node trong vòng
            base_port: Port bắt đầu cho node đầu tiên
        """
        self.num_nodes = num_nodes
        self.base_port = base_port
        self.nodes: List[Node] = []
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        
    def create_ring(self):
        """Tạo vòng Token Ring"""
        self.logger.info(f"Tạo vòng Token Ring với {self.num_nodes} node")
        
        # Tạo các node
        for i in range(self.num_nodes):
            port = self.base_port + i
            
            # Xác định node kế tiếp (vòng lặp tới node 0 sau node cuối cùng)
            next_node_index = (i + 1) % self.num_nodes
            next_node_port = self.base_port + next_node_index
            
            node = Node(
                node_id=i,
                port=port,
                next_node_host='localhost',
                next_node_port=next_node_port
            )
            self.nodes.append(node)
            self.logger.info(f"Tạo Node {i} trên port {port} "
                           f"-> Node {next_node_index} trên port {next_node_port}")
        
        self.logger.info("Vòng Token Ring đã được tạo thành công")

    def start_ring(self):
        """Khởi động toàn bộ vòng"""
        self.is_running = True
        self.logger.info("Khởi động vòng Token Ring...")
        
        # Khởi động tất cả các node
        for node in self.nodes:
            node.start()
            time.sleep(0.5)  # Delay để tránh xung đột
        
        self.logger.info("Tất cả các node đã khởi động")
        
        # Chờ các node sẵn sàng
        time.sleep(3)
        
        # Tạo và gửi token tới node đầu tiên
        self._initialize_token()
        
        # Bắt đầu luồng giám sát
        threading.Thread(target=self._monitor_ring, daemon=True).start()

    def _initialize_token(self):
        """Khởi tạo và gửi token tới node đầu tiên"""
        if not self.nodes:
            self.logger.error("Không có node trong vòng")
            return
        
        self.logger.info("Khởi tạo token và gửi tới node đầu tiên...")
        
        # Tạo token message
        token_msg = create_token_message(
            sender_id=self.nodes[0].node_id,
            token_id=1,
            free=True,
            visited_nodes=[]
        )
        
        # Gửi tới node đầu tiên
        self.nodes[0].message_queue.put(token_msg)
        self.logger.info(f"Token đã được gửi tới Node 0")

    def _monitor_ring(self):
        """Luồng giám sát trạng thái vòng"""
        while self.is_running:
            try:
                time.sleep(5)
                self.print_stats()
            except Exception as e:
                self.logger.error(f"Lỗi giám sát: {e}")

    def stop_ring(self):
        """Dừng toàn bộ vòng"""
        self.is_running = False
        self.logger.info("Dừng vòng Token Ring...")
        
        for node in self.nodes:
            node.stop()
            time.sleep(0.1)
        
        self.logger.info("Vòng Token Ring đã dừng")

    def broadcast_message(self, sender_id: int, message_type: str, data: any):
        """
        Gửi tin nhắn broadcast từ một node
        
        Args:
            sender_id: ID của node gửi
            message_type: Loại tin nhắn
            data: Dữ liệu
        """
        if sender_id >= len(self.nodes):
            self.logger.error(f"Node {sender_id} không tồn tại")
            return
        
        self.nodes[sender_id].send_message(-1, message_type, data)

    def unicast_message(self, sender_id: int, receiver_id: int, 
                       message_type: str, data: any):
        """
        Gửi tin nhắn unicast giữa hai node
        
        Args:
            sender_id: ID của node gửi
            receiver_id: ID của node nhận
            message_type: Loại tin nhắn
            data: Dữ liệu
        """
        if sender_id >= len(self.nodes) or receiver_id >= len(self.nodes):
            self.logger.error(f"Node không tồn tại")
            return
        
        self.nodes[sender_id].send_message(receiver_id, message_type, data)

    def print_stats(self):
        """In thống kê của tất cả các node"""
        self.logger.info("=" * 80)
        self.logger.info("THỐNG KÊ VÒNG TOKEN RING")
        self.logger.info("=" * 80)
        
        total_sent = 0
        total_received = 0
        total_tokens = 0
        
        for node in self.nodes:
            stats = node.get_stats()
            self.logger.info(
                f"Node {stats['node_id']}: "
                f"Token={stats['has_token']}, "
                f"Gửi={stats['messages_sent']}, "
                f"Nhận={stats['messages_received']}, "
                f"Token nhận={stats['tokens_received']}, "
                f"Buffer={stats['buffer_size']}"
            )
            total_sent += stats['messages_sent']
            total_received += stats['messages_received']
            total_tokens += stats['tokens_received']
        
        self.logger.info("=" * 80)
        self.logger.info(f"Tổng gửi: {total_sent}, Tổng nhận: {total_received}, "
                        f"Tổng token: {total_tokens}")
        self.logger.info("=" * 80)

    def get_node(self, node_id: int) -> Optional[Node]:
        """Lấy node theo ID"""
        if 0 <= node_id < len(self.nodes):
            return self.nodes[node_id]
        return None

    def get_all_nodes(self) -> List[Node]:
        """Lấy tất cả các node"""
        return self.nodes

    def get_ring_info(self) -> Dict:
        """Lấy thông tin chi tiết về vòng"""
        return {
            'num_nodes': self.num_nodes,
            'base_port': self.base_port,
            'is_running': self.is_running,
            'nodes': [
                {
                    'id': node.node_id,
                    'port': node.port,
                    'has_token': node.has_token,
                    'next_node': (node.node_id + 1) % self.num_nodes
                }
                for node in self.nodes
            ]
        }
