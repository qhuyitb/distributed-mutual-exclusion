"""
Token Ring Manager - Quản lý vòng Token Ring
Xử lý logic truyền token giữa các node
"""
import threading
import time
from typing import List, Dict, Any, Optional
from .message import Message, Token, create_token_message, MessageType
import logging

logger = logging.getLogger(__name__)

# Thêm custom MESSAGE level
MESSAGE_LEVEL = 25
logging.addLevelName(MESSAGE_LEVEL, "MESSAGE")


class Node:
    """Node trong vòng Token Ring"""
    
    def __init__(self, node_id: int, port: int = 0):
        self.node_id = node_id
        self.port = port
        self.next_node_id = None
        self.has_token = False
        self.running = False
        
        # Thống kê
        self.tokens_received = 0
        self.tokens_passed = 0
        self.messages_sent = 0
        self.messages_received = 0
        self.message_queue = []
        
        # Lock để thread-safe
        self.lock = threading.Lock()
    
    def receive_token(self, token: Token) -> None:
        """Node nhận token từ node trước"""
        with self.lock:
            self.has_token = True
            self.tokens_received += 1
            logger.info(f"Node {self.node_id} received token from Node {token.current_holder}")
            
            # Cập nhật token holder
            token.current_holder = self.node_id
            token.visited_nodes.append(self.node_id)
    
    def pass_token(self, token: Token) -> Token:
        """Node gửi token cho node tiếp theo"""
        with self.lock:
            if not self.has_token:
                return None
            
            # Cập nhật token trước khi gửi
            token.current_holder = self.next_node_id
            self.tokens_passed += 1
            self.has_token = False
            
            # Log info
            logger.info(f"Node {self.node_id} passing token to Node {self.next_node_id}")
            
            # Log message structure
            token_msg = Message(
                msg_type="TOKEN",
                sender_id=self.node_id,
                receiver_id=self.next_node_id,
                sequence_num=self.tokens_passed,
                timestamp=time.time(),
                token_holder=self.next_node_id,
                visited_nodes=token.visited_nodes
            )
            logger.log(MESSAGE_LEVEL, f"{token_msg}")
            
            return token
    
    def send_message(self, receiver_id: int, msg_type: str, data: Any) -> Message:
        """Node gửi tin nhắn"""
        msg = Message(
            msg_type=msg_type,
            sender_id=self.node_id,
            receiver_id=receiver_id,
            sequence_num=self.messages_sent,
            timestamp=time.time(),
            data=data
        )
        with self.lock:
            self.messages_sent += 1
        logger.log(MESSAGE_LEVEL, f"Node {self.node_id} -> Node {receiver_id}: {msg_type} | Data: {data}")
        return msg
    
    def receive_message(self, message: Message) -> None:
        """Node nhận tin nhắn"""
        with self.lock:
            self.messages_received += 1
            self.message_queue.append(message)
        logger.log(MESSAGE_LEVEL, f"Node {self.node_id} received {message.msg_type} from Node {message.sender_id} | Data: {message.data}")

    
    def get_stats(self) -> Dict[str, Any]:
        """Lấy thống kê node"""
        with self.lock:
            return {
                'node_id': self.node_id,
                'has_token': self.has_token,
                'tokens_received': self.tokens_received,
                'tokens_passed': self.tokens_passed,
                'messages_sent': self.messages_sent,
                'messages_received': self.messages_received,
            }


class TokenRingManager:
    """Quản lý vòng Token Ring"""
    
    def __init__(self, num_nodes: int, base_port: int = 5000):
        self.num_nodes = num_nodes
        self.base_port = base_port
        self.nodes: List[Node] = []
        self.token: Optional[Token] = None
        self.running = False
        self.token_thread = None
        self.lock = threading.Lock()
    
    def create_ring(self) -> None:
        """Tạo vòng Token Ring"""
        logger.info(f"Creating ring with {self.num_nodes} nodes")
        
        # Tạo các node
        for i in range(self.num_nodes):
            node = Node(node_id=i, port=self.base_port + i)
            self.nodes.append(node)
        
        # Kết nối các node theo vòng: 0 -> 1 -> 2 -> ... -> N-1 -> 0
        for i in range(self.num_nodes):
            next_id = (i + 1) % self.num_nodes
            self.nodes[i].next_node_id = next_id
        
        # Tạo token ban đầu ở node 0
        self.token = Token(token_id=0, initial_holder=0)
        self.nodes[0].has_token = True
        
        logger.info("Ring created successfully")
    
    def start_ring(self) -> None:
        """Khởi động vòng Token Ring"""
        with self.lock:
            if self.running:
                logger.warning("Ring already running")
                return
            self.running = True
        
        logger.info("Starting Token Ring...")
        
        # Khởi động thread truyền token
        self.token_thread = threading.Thread(target=self._token_circulation_loop, daemon=True)
        self.token_thread.start()
        
        logger.info("Token Ring started")
    
    def _token_circulation_loop(self) -> None:
        """Vòng lặp truyền token"""
        hold_time = 1.0  # Thời gian mỗi node giữ token
        
        while self.running:
            try:
                # Tìm node hiện tại giữ token
                current_holder = None
                with self.lock:
                    for node in self.nodes:
                        if node.has_token:
                            current_holder = node
                            break
                
                if current_holder is None:
                    time.sleep(0.1)
                    continue
                
                # Node giữ token một khoảng thời gian
                time.sleep(hold_time)
                
                # Node gửi token cho node tiếp theo
                next_node_id = current_holder.next_node_id
                next_node = self.nodes[next_node_id]
                
                # Cập nhật token
                token_msg = current_holder.pass_token(self.token)
                if token_msg:
                    time.sleep(0.1)  # Mô phỏng trễ mạng
                    next_node.receive_token(self.token)
                
            except Exception as e:
                logger.error(f"Error in token circulation: {e}")
                time.sleep(0.1)
    
    def stop_ring(self) -> None:
        """Dừng vòng Token Ring"""
        with self.lock:
            self.running = False
        
        if self.token_thread:
            self.token_thread.join(timeout=2)
        
        logger.info("Token Ring stopped")
    
    def unicast_message(self, sender_id: int, receiver_id: int, 
                       msg_type: str, data: Any) -> None:
        """Gửi tin nhắn từ sender tới receiver"""
        if sender_id < 0 or sender_id >= self.num_nodes:
            logger.error(f"Invalid sender ID: {sender_id}")
            return
        
        if receiver_id < 0 or receiver_id >= self.num_nodes:
            logger.error(f"Invalid receiver ID: {receiver_id}")
            return
        
        sender = self.nodes[sender_id]
        receiver = self.nodes[receiver_id]
        
        msg = sender.send_message(receiver_id, msg_type, data)
        receiver.receive_message(msg)
    
    def get_ring_info(self) -> Dict[str, Any]:
        """Lấy thông tin về vòng"""
        nodes_info = []
        for node in self.nodes:
            nodes_info.append({
                'id': node.node_id,
                'port': node.port,
                'next_node': node.next_node_id,
                'has_token': node.has_token,
            })
        
        return {
            'num_nodes': self.num_nodes,
            'nodes': nodes_info,
            'token': {
                'id': self.token.token_id,
                'holder': self.token.current_holder,
                'free': self.token.free,
            }
        }
    
    def get_all_nodes(self) -> List[Node]:
        """Lấy danh sách tất cả các node"""
        return self.nodes
    
    def print_stats(self) -> None:
        """In thống kê"""
        print("\n" + "="*80)
        print("THỐNG KÊ TOKEN RING")
        print("="*80)
        
        total_tokens = 0
        total_messages = 0
        
        for node in self.nodes:
            stats = node.get_stats()
            print(f"\nNode {stats['node_id']}:")
            print(f"  Token nhận: {stats['tokens_received']}")
            print(f"  Token gửi: {stats['tokens_passed']}")
            print(f"  Tin nhắn gửi: {stats['messages_sent']}")
            print(f"  Tin nhắn nhận: {stats['messages_received']}")
            print(f"  Có token: {stats['has_token']}")
            
            total_tokens += stats['tokens_received']
            total_messages += stats['messages_sent']
        
        print(f"\n{'='*80}")
        print(f"Tổng token lưu thông: {total_tokens}")
        print(f"Tổng tin nhắn gửi: {total_messages}")
        print(f"{'='*80}\n")
