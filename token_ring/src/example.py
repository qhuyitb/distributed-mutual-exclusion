"""
Các ví dụ sử dụng Token Ring Implementation
"""

import time
import sys
from ring_manager import TokenRingManager
from node import Node
from message import MessageType


def example_1_basic_setup():
    """
    Ví dụ 1: Cài đặt cơ bản vòng Token Ring
    """
    print("\n" + "="*60)
    print("VÍ DỤ 1: Cài đặt cơ bản vòng Token Ring")
    print("="*60)
    
    # Tạo quản lý vòng
    manager = TokenRingManager(num_nodes=3, base_port=9000)
    
    # Tạo vòng logic
    manager.create_ring()
    
    print("\nVòng được tạo:")
    info = manager.get_ring_info()
    for node_info in info['nodes']:
        print(f"  Node {node_info['id']}: "
              f"Port {node_info['port']} → Node {node_info['next_node']}")
    
    # Khởi động vòng
    manager.start_ring()
    print("\nVòng đã khởi động")
    
    # Chạy 5 giây
    time.sleep(5)
    
    # In thống kê
    manager.print_stats()
    
    # Dừng vòng
    manager.stop_ring()
    print("✓ Hoàn thành Ví dụ 1\n")


def example_2_unicast_message():
    """
    Ví dụ 2: Gửi unicast message giữa hai node
    """
    print("\n" + "="*60)
    print("VÍ DỤ 2: Gửi unicast message")
    print("="*60)
    
    manager = TokenRingManager(num_nodes=4, base_port=9100)
    manager.create_ring()
    manager.start_ring()
    
    print("\nChờ vòng sẵn sàng...")
    time.sleep(3)
    
    # Gửi REQUEST từ Node 0 tới Node 3
    print("\n1. Node 0 gửi REQUEST tới Node 3")
    manager.unicast_message(
        sender_id=0,
        receiver_id=3,
        msg_type=MessageType.REQUEST.value,
        data={
            'query': 'Hỏi thông tin từ Node 3',
            'timestamp': time.time()
        }
    )
    
    time.sleep(1)
    
    # Gửi REPLY từ Node 3 tới Node 0
    print("2. Node 3 gửi REPLY tới Node 0")
    manager.unicast_message(
        sender_id=3,
        receiver_id=0,
        msg_type=MessageType.REPLY.value,
        data={
            'answer': 'Phản hồi từ Node 3',
            'status': 'OK'
        }
    )
    
    time.sleep(2)
    
    print("\n📊 Thống kê:")
    manager.print_stats()
    
    manager.stop_ring()
    print("✓ Hoàn thành Ví dụ 2\n")


def example_3_multiple_messages():
    """
    Ví dụ 3: Gửi nhiều tin nhắn từ nhiều node
    """
    print("\n" + "="*60)
    print("VÍ DỤ 3: Gửi nhiều tin nhắn")
    print("="*60)
    
    manager = TokenRingManager(num_nodes=3, base_port=9200)
    manager.create_ring()
    manager.start_ring()
    
    time.sleep(3)
    
    messages = [
        (0, 1, MessageType.DATA.value, {'seq': 1, 'data': 'tin 1'}),
        (1, 2, MessageType.DATA.value, {'seq': 2, 'data': 'tin 2'}),
        (2, 0, MessageType.DATA.value, {'seq': 3, 'data': 'tin 3'}),
        (0, 2, MessageType.REQUEST.value, {'seq': 4, 'cmd': 'status'}),
        (1, 0, MessageType.REPLY.value, {'seq': 5, 'msg': 'done'}),
    ]
    
    print("\nGửi các tin nhắn:")
    for sender, receiver, msg_type, data in messages:
        print(f"  {sender} → {receiver}: {msg_type}")
        manager.unicast_message(sender, receiver, msg_type, data)
        time.sleep(0.5)
    
    time.sleep(2)
    
    print("\n📊 Kết quả:")
    manager.print_stats()
    
    manager.stop_ring()
    print("✓ Hoàn thành Ví dụ 3\n")


def example_4_direct_node_access():
    """
    Ví dụ 4: Truy cập trực tiếp các node
    """
    print("\n" + "="*60)
    print("VÍ DỤ 4: Truy cập trực tiếp các node")
    print("="*60)
    
    manager = TokenRingManager(num_nodes=2, base_port=9300)
    manager.create_ring()
    manager.start_ring()
    
    time.sleep(2)
    
    # Lấy các node
    node0 = manager.get_node(0)
    node1 = manager.get_node(1)
    
    print("\nInformation nodes:")
    print(f"  Node 0: {node0}")
    print(f"  Node 1: {node1}")
    
    time.sleep(2)
    
    print("\nThống kê từng node:")
    for node in manager.get_all_nodes():
        stats = node.get_stats()
        print(f"  Node {stats['node_id']}: "
              f"Token={stats['has_token']}, "
              f"Gửi={stats['messages_sent']}, "
              f"Nhận={stats['messages_received']}")
    
    manager.stop_ring()
    print("✓ Hoàn thành Ví dụ 4\n")


def example_5_different_ring_sizes():
    """
    Ví dụ 5: Vòng với kích thước khác nhau
    """
    print("\n" + "="*60)
    print("VÍ DỤ 5: Vòng với kích thước khác nhau")
    print("="*60)
    
    for num_nodes in [2, 3, 4, 5]:
        print(f"\nChạy vòng với {num_nodes} node...")
        
        manager = TokenRingManager(num_nodes=num_nodes, base_port=9400+num_nodes*10)
        manager.create_ring()
        manager.start_ring()
        
        time.sleep(3)
        
        # Lấy thống kê
        total_tokens = sum(node.tokens_received for node in manager.get_all_nodes())
        print(f"  Tổng token nhận được: {total_tokens}")
        
        manager.stop_ring()
    
    print("✓ Hoàn thành Ví dụ 5\n")


def example_6_communication_pattern():
    """
    Ví dụ 6: Mô hình giao tiếp phức tạp
    """
    print("\n" + "="*60)
    print("VÍ DỤ 6: Mô hình giao tiếp phức tạp")
    print("="*60)
    
    manager = TokenRingManager(num_nodes=4, base_port=9500)
    manager.create_ring()
    manager.start_ring()
    
    time.sleep(3)
    
    print("\nMô hình Client-Server:")
    print("  Node 0 là Server")
    print("  Các node khác là Client")
    
    # Client 1 gửi request
    print("\n1. Client (Node 1) gửi REQUEST tới Server (Node 0)")
    manager.unicast_message(1, 0, MessageType.REQUEST.value, 
                           {'client': 1, 'cmd': 'get_data'})
    
    time.sleep(0.5)
    
    # Client 2 gửi request
    print("2. Client (Node 2) gửi REQUEST tới Server (Node 0)")
    manager.unicast_message(2, 0, MessageType.REQUEST.value,
                           {'client': 2, 'cmd': 'get_status'})
    
    time.sleep(0.5)
    
    # Server gửi reply
    print("3. Server (Node 0) gửi REPLY tới Client (Node 1)")
    manager.unicast_message(0, 1, MessageType.REPLY.value,
                           {'data': [1, 2, 3, 4, 5]})
    
    time.sleep(2)
    
    print("\n📊 Kết quả:")
    manager.print_stats()
    
    manager.stop_ring()
    print("✓ Hoàn thành Ví dụ 6\n")


def main():
    """Chạy các ví dụ"""
    print("\n" + "#"*60)
    print("# TOKEN RING - CÁC VÍ DỤ SỬ DỤNG")
    print("#"*60)
    
    examples = {
        '1': ('Cài đặt cơ bản', example_1_basic_setup),
        '2': ('Gửi unicast message', example_2_unicast_message),
        '3': ('Gửi nhiều tin nhắn', example_3_multiple_messages),
        '4': ('Truy cập trực tiếp node', example_4_direct_node_access),
        '5': ('Vòng kích thước khác nhau', example_5_different_ring_sizes),
        '6': ('Mô hình giao tiếp phức tạp', example_6_communication_pattern),
    }
    
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        print("\nChọn ví dụ để chạy:")
        for key, (name, _) in examples.items():
            print(f"  {key} - {name}")
        print("  0 - Chạy tất cả")
        
        choice = input("\nNhập lựa chọn: ").strip()
    
    if choice == '0':
        for key, (name, func) in examples.items():
            try:
                func()
                time.sleep(1)
            except Exception as e:
                print(f"❌ Lỗi: {e}")
    elif choice in examples:
        name, func = examples[choice]
        try:
            func()
        except Exception as e:
            print(f"❌ Lỗi: {e}")
    else:
        print("❌ Lựa chọn không hợp lệ")
        sys.exit(1)
    
    print("\n" + "#"*60)
    print("# HOÀN THÀNH")
    print("#"*60 + "\n")


if __name__ == '__main__':
    main()
