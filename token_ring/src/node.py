"""
Node trong Token Ring - xử lý token và truyền/nhận dữ liệu
"""
import socket
import threading
import time
import queue
from typing import Optional, Dict, Any
from message import Message, MessageType, create_token_message, create_ack_message
import logging

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


class Node:
    """
    Node trong vòng Token Ring
    Mỗi node có:
    - ID duy nhất
    - Port để lắng nghe
    - Kết nối tới node kế tiếp
    - Queue để xử lý gói tin
    """
    
    def __init__(self, node_id: int, port: int, next_node_host: str = 'localhost', 
                 next_node_port: int = None, max_transmission_time: int = 5):
        """
        Khởi tạo Node
        
        Args:
            node_id: ID của node (0, 1, 2, ...)
            port: Port lắng nghe trên localhost
            next_node_host: Host của node kế tiếp
            next_node_port: Port của node kế tiếp
            max_transmission_time: Thời gian tối đa để gửi/nhận dữ liệu khi có token
        """
        self.node_id = node_id
        self.port = port
        self.next_node_host = next_node_host
        self.next_node_port = next_node_port or port + 1
        self.max_transmission_time = max_transmission_time
        
        # Quản lý token
        self.has_token = False
        self.token_id = None
        self.token_received_time = None
        
        # Hàng đợi xử lý
        self.message_queue = queue.Queue()
        self.send_queue = queue.Queue()
        
        # Bộ đệm lưu trữ gói tin
        self.buffer: Dict[int, Message] = {}  # Lưu trữ theo seq_num
        self.acknowledgments: Dict[int, bool] = {}  # Xác nhận gói tin
        
        # Socket
        self.server_socket = None
        self.client_socket = None
        
        # Trạng thái
        self.is_running = False
        self.logger = logging.getLogger(f"Node-{node_id}")
        
        # Statistics
        self.messages_sent = 0
        self.messages_received = 0
        self.tokens_received = 0

    def start(self):
        """Khởi động node"""
        self.is_running = True
        
        # Tạo server socket để lắng nghe
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('localhost', self.port))
        self.server_socket.listen(1)
        
        self.logger.info(f"Node {self.node_id} khởi động trên port {self.port}")
        
        # Các luồng xử lý
        threading.Thread(target=self._listen_for_messages, daemon=True).start()
        threading.Thread(target=self._process_messages, daemon=True).start()
        threading.Thread(target=self._connect_to_next_node, daemon=True).start()

    def stop(self):
        """Dừng node"""
        self.is_running = False
        if self.server_socket:
            self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()
        self.logger.info(f"Node {self.node_id} dừng")

    def _listen_for_messages(self):
        """Luồng lắng nghe các gói tin đến"""
        while self.is_running:
            try:
                self.server_socket.settimeout(1)
                client, addr = self.server_socket.accept()
                threading.Thread(
                    target=self._handle_incoming_message, 
                    args=(client,), 
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Lỗi lắng nghe: {e}")

    def _handle_incoming_message(self, client_socket: socket.socket):
        """Xử lý khi nhận được kết nối"""
        try:
            # Nhận dữ liệu
            data = client_socket.recv(4096).decode('utf-8')
            if data:
                message = Message.from_json(data)
                self.message_queue.put(message)
                self.messages_received += 1
                self.logger.info(f"Nhận gói tin: {message}")
                
                # Gửi ACK
                if message.msg_type in [MessageType.REQUEST.value, 
                                       MessageType.DATA.value]:
                    ack = create_ack_message(self.node_id, message.sender_id, 
                                           message.sequence_num)
                    client_socket.send(ack.to_json().encode('utf-8'))
        except Exception as e:
            self.logger.error(f"Lỗi xử lý gói tin: {e}")
        finally:
            client_socket.close()

    def _connect_to_next_node(self):
        """Tạo kết nối tới node kế tiếp"""
        while self.is_running:
            try:
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.next_node_host, self.next_node_port))
                self.logger.info(f"Kết nối tới node kế tiếp trên "
                               f"{self.next_node_host}:{self.next_node_port}")
                
                # Đợi cho đến khi mất kết nối
                while self.is_running and self.client_socket:
                    time.sleep(0.1)
            except ConnectionRefusedError:
                # Node kế tiếp chưa sẵn sàng
                self.logger.warning(f"Chưa kết nối được node kế tiếp. "
                                   f"Thử lại sau 2s...")
                time.sleep(2)
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Lỗi kết nối: {e}")
                    time.sleep(2)

    def _process_messages(self):
        """Luồng xử lý hàng đợi gói tin"""
        while self.is_running:
            try:
                message = self.message_queue.get(timeout=1)
                
                if message.msg_type == MessageType.TOKEN.value:
                    self._handle_token(message)
                elif message.msg_type == MessageType.REQUEST.value:
                    self._handle_request(message)
                elif message.msg_type == MessageType.DATA.value:
                    self._handle_data(message)
                elif message.msg_type == MessageType.ACK.value:
                    self._handle_ack(message)
                elif message.msg_type == MessageType.REPLY.value:
                    self._handle_reply(message)
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Lỗi xử lý gói tin: {e}")

    def _handle_token(self, message: Message):
        """Xử lý khi nhận token"""
        self.has_token = True
        self.token_id = message.data.get('token_id') if message.data else None
        self.token_received_time = time.time()
        self.tokens_received += 1
        
        self.logger.info(f"Nhận được TOKEN (id={self.token_id})")
        
        # Xử lý dữ liệu nếu có trong hàng đợi
        time.sleep(0.5)  # Mô phỏng quá trình xử lý
        
        # Chuyển token tới node kế tiếp
        self._pass_token(message)

    def _handle_request(self, message: Message):
        """Xử lý REQUEST từ node khác"""
        self.logger.info(f"Nhận REQUEST từ node {message.sender_id}: {message.data}")
        self.buffer[message.sequence_num] = message

    def _handle_data(self, message: Message):
        """Xử lý DATA từ node khác"""
        self.logger.info(f"Nhận DATA từ node {message.sender_id}: {message.data}")
        self.buffer[message.sequence_num] = message

    def _handle_reply(self, message: Message):
        """Xử lý REPLY từ node khác"""
        self.logger.info(f"Nhận REPLY từ node {message.sender_id}: {message.data}")
        self.buffer[message.sequence_num] = message

    def _handle_ack(self, message: Message):
        """Xử lý ACK từ node khác"""
        self.logger.debug(f"Nhận ACK từ node {message.sender_id} "
                         f"cho gói tin {message.sequence_num}")
        self.acknowledgments[message.sequence_num] = True

    def _pass_token(self, token_message: Message):
        """Chuyển token tới node kế tiếp"""
        self.has_token = False
        
        # Cập nhật thông tin token
        visited_nodes = token_message.visited_nodes or []
        if self.node_id not in visited_nodes:
            visited_nodes.append(self.node_id)
        
        # Gửi token
        try:
            if self.client_socket:
                self.client_socket.send(token_message.to_json().encode('utf-8'))
                self.logger.info(f"Chuyển TOKEN tới node kế tiếp")
                self.messages_sent += 1
        except Exception as e:
            self.logger.error(f"Lỗi chuyển token: {e}")

    def send_message(self, receiver_id: int, msg_type: str, data: Any, 
                    seq_num: int = None) -> bool:
        """
        Gửi gói tin tới node khác
        
        Args:
            receiver_id: ID của node nhận
            msg_type: Loại gói tin
            data: Dữ liệu
            seq_num: Số thứ tự
            
        Returns:
            True nếu gửi thành công
        """
        if not self.has_token:
            self.logger.warning(f"Không có token, không thể gửi gói tin")
            return False
        
        message = Message(
            msg_type=msg_type,
            sender_id=self.node_id,
            receiver_id=receiver_id,
            sequence_num=seq_num or int(time.time() * 1000),
            timestamp=time.time(),
            data=data
        )
        
        self.send_queue.put(message)
        
        # Gửi gói tin
        self._send_message_direct(message)
        self.messages_sent += 1
        return True

    def _send_message_direct(self, message: Message):
        """Gửi gói tin trực tiếp"""
        try:
            if self.client_socket:
                self.client_socket.send(message.to_json().encode('utf-8'))
                self.logger.info(f"Gửi {message.msg_type} tới node {message.receiver_id}")
        except Exception as e:
            self.logger.error(f"Lỗi gửi gói tin: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê của node"""
        return {
            'node_id': self.node_id,
            'port': self.port,
            'has_token': self.has_token,
            'messages_sent': self.messages_sent,
            'messages_received': self.messages_received,
            'tokens_received': self.tokens_received,
            'buffer_size': len(self.buffer),
            'acknowledged': len(self.acknowledgments)
        }

    def __str__(self) -> str:
        return f"Node(id={self.node_id}, port={self.port}, has_token={self.has_token})"
