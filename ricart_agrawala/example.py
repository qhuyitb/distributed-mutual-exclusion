"""
Example sử dụng Ricart-Agrawala Algorithm
Chạy trực tiếp các scenario cụ thể
"""
from node import NodeManager
import time


def example_1_sequential_requests():
    """
    Ví dụ 1: 3 nodes yêu cầu tuần tự
    Node 0 → Node 1 → Node 2
    """
    print("\n" + "="*70)
    print("EXAMPLE 1: 3 NODES - REQUESTS TUẦN TỰ")
    print("="*70)
    print("Mô tả: Mỗi node yêu cầu sau khi node trước hoàn thành")
    print("Kỳ vọng: Không có xung đột, thứ tự rõ ràng\n")
    
    manager = NodeManager(3)
    manager.run_scenario([
        (0, 0.0),      # Node 0 request ngay
        (1, 0.5),      # Node 1 request sau 0.5s
        (2, 1.0)       # Node 2 request sau 1.0s
    ])


def example_2_concurrent_requests():
    """
    Ví dụ 2: 4 nodes yêu cầu gần cùng lúc
    Mô phỏng "contention" - cạnh tranh truy cập
    """
    print("\n" + "="*70)
    print("EXAMPLE 2: 4 NODES - REQUESTS ĐỒNG THỜI (CONTENTION)")
    print("="*70)
    print("Mô tả: Nhiều nodes yêu cầu cùng lúc, gây tranh chấp resource")
    print("Kỳ vọng: Mutual exclusion được đảm bảo, 1 node vào CS một lúc\n")
    
    manager = NodeManager(4)
    manager.run_scenario([
        (0, 0.0),      # Node 0 request ngay
        (1, 0.1),      # Node 1 request sau 0.1s
        (2, 0.15),     # Node 2 request sau 0.15s
        (3, 0.2)       # Node 3 request sau 0.2s
    ])


def example_3_multiple_requests():
    """
    Ví dụ 3: 5 nodes, mỗi node request 2 lần
    Mô phỏng hệ thống có repeated access
    """
    print("\n" + "="*70)
    print("EXAMPLE 3: 5 NODES - MULTIPLE REQUESTS (2 LƯỢT MỖi NODE)")
    print("="*70)
    print("Mô tả: Mỗi node yêu cầu vào CS 2 lần với delay nhỏ")
    print("Kỳ vọng: Mutual exclusion được duy trì qua nhiều lượt request\n")
    
    manager = NodeManager(5)
    manager.run_scenario([
        (0, 0.0),   (0, 2.5),   # Node 0: request 1 và 2
        (1, 0.3),   (1, 2.8),   # Node 1: request 1 và 2
        (2, 0.6),   (2, 3.1),   # Node 2: request 1 và 2
        (3, 0.9),   (3, 3.4),   # Node 3: request 1 và 2
        (4, 1.2),   (4, 3.7)    # Node 4: request 1 và 2
    ])


def example_4_high_load():
    """
    Ví dụ 4: Tải cao - 8 nodes, 16 requests tổng cộng
    Stress test của thuật toán
    """
    print("\n" + "="*70)
    print("EXAMPLE 4: HIGH LOAD - 8 NODES, 16 REQUESTS")
    print("="*70)
    print("Mô tả: Load cao, nhiều nodes, nhiều requests đồng thời")
    print("Kỳ vọng: Thuật toán xử lý đúng mặc dù contention cao\n")
    
    manager = NodeManager(8)
    manager.run_random_scenario(num_requests=16)


def example_5_starving_prevention():
    """
    Ví dụ 5: Kiểm tra starvation prevention
    Node 0 liên tục request nhưng node khác vẫn được phục vụ
    """
    print("\n" + "="*70)
    print("EXAMPLE 5: STARVATION PREVENTION CHECK")
    print("="*70)
    print("Mô tả: Node 0 request 3 lần liên tiếp, Node 1 request 1 lần")
    print("Kỳ vọng: Node 1 không bị starvation, được phục vụ đúng thứ tự\n")
    
    manager = NodeManager(2)
    manager.run_scenario([
        (0, 0.0),      # Node 0 request lần 1
        (1, 0.1),      # Node 1 request (được serve)
        (0, 0.2),      # Node 0 request lần 2
        (0, 0.3)       # Node 0 request lần 3
    ])


def main():
    """Chạy tất cả examples"""
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  RICART-AGRAWALA ALGORITHM - EXAMPLES".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    examples = [
        ("Sequential Requests", example_1_sequential_requests),
        ("Concurrent Requests (Contention)", example_2_concurrent_requests),
        ("Multiple Requests per Node", example_3_multiple_requests),
        ("High Load Stress Test", example_4_high_load),
        ("Starvation Prevention Check", example_5_starving_prevention)
    ]
    
    try:
        while True:
            print("\n" + "="*70)
            print("DANH SÁCH CÁC EXAMPLES")
            print("="*70)
            for i, (name, _) in enumerate(examples, 1):
                print(f"{i}. {name}")
            print(f"{len(examples)+1}. Chạy tất cả examples")
            print(f"{len(examples)+2}. Thoát")
            print("="*70)
            
            choice = input("Chọn example (1-7): ").strip()
            
            if choice.isdigit():
                choice = int(choice)
                if 1 <= choice <= len(examples):
                    _, example_func = examples[choice-1]
                    example_func()
                    input("\nNhấn ENTER để tiếp tục...")
                elif choice == len(examples) + 1:
                    print("\nChạy tất cả examples...\n")
                    for _, example_func in examples:
                        example_func()
                        input("\nNhấn ENTER để tiếp tục với example tiếp theo...")
                elif choice == len(examples) + 2:
                    print("\nTạm biệt! 👋\n")
                    break
                else:
                    print("❌ Lựa chọn không hợp lệ")
            else:
                print("❌ Vui lòng nhập số hợp lệ")
    
    except KeyboardInterrupt:
        print("\n\nChương trình bị dừng")


if __name__ == "__main__":
    main()
