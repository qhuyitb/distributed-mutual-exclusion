# -*- coding: utf-8 -*-
"""
Demo ung dung Token Ring
Chay cac kich ban giao tiep giua cac node trong vong
"""
import time
import sys
import os
from ring_manager import TokenRingManager
from message import MessageType
import logging

# Thêm custom logging level MESSAGE
MESSAGE_LEVEL = 25
logging.addLevelName(MESSAGE_LEVEL, "MESSAGE")

def message_log(self, message, *args, **kwargs):
    """Custom log method cho MESSAGE level"""
    if self.isEnabledFor(MESSAGE_LEVEL):
        self._log(MESSAGE_LEVEL, message, args, **kwargs)

logging.Logger.message = message_log

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_basic_ring():
    """Demo cơ bản - khởi động vòng Token Ring"""
    print("\n" + "="*80)
    print("DEMO 1: Token Ring Basic")
    print("="*80 + "\n")
    
    # Create ring with 4 nodes
    manager = TokenRingManager(num_nodes=4, base_port=5000)
    
    # Create ring
    manager.create_ring()
    
    # Start ring
    manager.start_ring()
    
    # Run for 15 seconds
    print("\nToken is circulating...")
    print("Press Ctrl+C to stop or wait 15 seconds\n")
    
    try:
        for i in range(15):
            time.sleep(1)
            sys.stdout.write(f"\rTime: {i+1}/15 seconds")
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\n\nStopped by user")
    
    print("\n")
    manager.print_stats()
    manager.stop_ring()
    
    return manager


def demo_message_passing():
    """Demo gửi tin nhắn giữa các node"""
    print("\n" + "="*80)
    print("DEMO 2: Gửi tin nhắn giữa các node")
    print("="*80 + "\n")
    
    # Tạo vòng
    manager = TokenRingManager(num_nodes=4, base_port=6000)
    manager.create_ring()
    manager.start_ring()
    
    # Chờ token khởi tạo
    time.sleep(3)
    
    # Gửi tin nhắn từ node 0 tới node 2
    print("\nGửi REQUEST từ Node 0 tới Node 2...")
    manager.unicast_message(0, 2, MessageType.REQUEST.value, {
        'action': 'query',
        'params': 'hello from node 0'
    })
    
    time.sleep(2)
    
    # Gửi tin nhắn từ node 1 tới node 3
    print("Gửi DATA từ Node 1 tới Node 3...")
    manager.unicast_message(1, 3, MessageType.DATA.value, {
        'content': 'test data from node 1'
    })
    
    time.sleep(2)
    
    # Gửi tin nhắn từ node 3 tới node 0
    print("Gửi REPLY từ Node 3 tới Node 0...")
    manager.unicast_message(3, 0, MessageType.REPLY.value, {
        'status': 'success',
        'message': 'done'
    })
    
    time.sleep(5)
    manager.print_stats()
    manager.stop_ring()


def demo_token_circulation():
    """Demo token di chuyển xung quanh vòng"""
    print("\n" + "="*80)
    print("DEMO 3: Token di chuyển xung quanh vòng")
    print("="*80 + "\n")
    
    manager = TokenRingManager(num_nodes=6, base_port=7000)
    manager.create_ring()
    
    print("Cấu hình vòng:")
    info = manager.get_ring_info()
    for node_info in info['nodes']:
        print(f"  Node {node_info['id']}: Port {node_info['port']} "
              f"-> Node {node_info['next_node']}")
    
    manager.start_ring()
    
    print("\nToken đang lưu thông qua các node...")
    print("Quan sát token di chuyển:\n")
    
    try:
        for i in range(20):
            time.sleep(1)
            sys.stdout.write(f"\rThời gian: {i+1}/20 giây")
            sys.stdout.flush()
    except KeyboardInterrupt:
        print("\nDừng bởi người dùng")
    
    print("\n")
    
    print("\nTổng quan khi kết thúc:")
    for node in manager.get_all_nodes():
        stats = node.get_stats()
        print(f"  Node {stats['node_id']}: "
              f"Đã nhận {stats['tokens_received']} token, "
              f"Gửi {stats['messages_sent']}, "
              f"Nhận {stats['messages_received']}")
    
    manager.stop_ring()


def demo_multiple_messages():
    """Demo gửi nhiều tin nhắn liên tiếp"""
    print("\n" + "="*80)
    print("DEMO 4: Gửi nhiều tin nhắn")
    print("="*80 + "\n")
    
    manager = TokenRingManager(num_nodes=3, base_port=8000)
    manager.create_ring()
    manager.start_ring()
    
    time.sleep(3)
    
    print("Gửi 5 tin nhắn từ các node khác nhau...\n")
    
    messages = [
        (0, 1, MessageType.REQUEST.value, {'msg': 'Message 1'}),
        (1, 2, MessageType.DATA.value, {'msg': 'Message 2'}),
        (2, 0, MessageType.REPLY.value, {'msg': 'Message 3'}),
        (0, 2, MessageType.REQUEST.value, {'msg': 'Message 4'}),
        (1, 0, MessageType.DATA.value, {'msg': 'Message 5'}),
    ]
    
    for sender, receiver, msg_type, data in messages:
        print(f"Node {sender} -> Node {receiver}: {msg_type}")
        manager.unicast_message(sender, receiver, msg_type, data)
        time.sleep(1)
    
    time.sleep(3)
    manager.print_stats()
    manager.stop_ring()


def main():
    """Chạy các demo"""
    print("\n" + "#"*80)
    print("# DEMO TOKEN RING - Ring Logic with Token Pass")
    print("#"*80)
    
    # Chọn demo nào để chạy
    if len(sys.argv) > 1:
        demo_choice = sys.argv[1]
    else:
        print("\nChọn demo để chạy:")
        print("  1 - Demo cơ bản (khởi động vòng)")
        print("  2 - Demo gửi tin nhắn")
        print("  3 - Demo token di chuyển")
        print("  4 - Demo nhiều tin nhắn")
        print("  5 - Chạy tất cả")
        
        demo_choice = input("\nNhập lựa chọn (1-5): ").strip()
    
    if demo_choice == '1':
        demo_basic_ring()
    elif demo_choice == '2':
        demo_message_passing()
    elif demo_choice == '3':
        demo_token_circulation()
    elif demo_choice == '4':
        demo_multiple_messages()
    elif demo_choice == '5':
        demo_basic_ring()
        time.sleep(2)
        demo_message_passing()
        time.sleep(2)
        demo_token_circulation()
        time.sleep(2)
        demo_multiple_messages()
    else:
        print("Lựa chọn không hợp lệ")
        sys.exit(1)
    
    print("\n" + "#"*80)
    print("# COMPLETE")
    print("#"*80 + "\n")


if __name__ == '__main__':
    main()
    main()
