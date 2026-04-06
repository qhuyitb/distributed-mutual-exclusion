"""
Demo Ricart-Agrawala Algorithm
Minh họa thuật toán phân tán Ricart-Agrawala để điều phối truy cập
vào Critical Section (in-memory, không cần coordinator)
"""
import sys
from node import NodeManager


def print_menu():
    print("\n" + "=" * 60)
    print("    DEMO RICART-AGRAWALA ALGORITHM")
    print("=" * 60)
    print("  1. Demo cơ bản   (3 nodes)")
    print("  2. Demo trung bình (5 nodes)")
    print("  3. Demo lớn      (10 nodes)")
    print("  4. Demo tự định nghĩa")
    print("  5. Thoát")
    print("=" * 60)


def run_basic_demo():
    print("\n[DEMO CƠ BẢN - 3 NODES]")
    print("Scenario: Node 0, 1, 2 lần lượt yêu cầu vào CS\n")
    manager = NodeManager(3)
    manager.run_scenario([(0, 0), (1, 0.5), (2, 1.0)])


def run_medium_demo():
    print("\n[DEMO TRUNG BÌNH - 5 NODES]")
    print("Scenario: 5 nodes yêu cầu gần đồng thời\n")
    manager = NodeManager(5)
    manager.run_scenario([(i, i * 0.3) for i in range(5)])


def run_large_demo():
    print("\n[DEMO LỚN - 10 NODES]")
    print("Scenario: 10 nodes, mỗi node request 2 lần\n")
    manager = NodeManager(10)
    manager.run_random_scenario(num_requests=20)


def run_custom_demo():
    print("\n[DEMO TỰ ĐỊNH NGHĨA]")
    try:
        num_nodes = int(input("Nhập số nodes (2-20): "))
        if not (2 <= num_nodes <= 20):
            print("❌ Số nodes phải trong khoảng 2-20")
            return
    except ValueError:
        print("❌ Input không hợp lệ")
        return

    manager = NodeManager(num_nodes)

    print("\nLựa chọn scenario:")
    print("  1. Mỗi node request 1 lần (tuần tự)")
    print("  2. Mỗi node request 2 lần (ngẫu nhiên)")
    print("  3. Tất cả nodes request cùng lúc (delay nhỏ)")
    choice = input("Chọn (1-3): ").strip()

    if choice == "1":
        manager.run_scenario([(i, i * 0.5) for i in range(num_nodes)])
    elif choice == "2":
        manager.run_random_scenario(num_requests=num_nodes * 2)
    elif choice == "3":
        manager.run_scenario([(i, i * 0.1) for i in range(num_nodes)])
    else:
        print("❌ Lựa chọn không hợp lệ")


def main():
    while True:
        print_menu()
        choice = input("Chọn (1-5): ").strip()

        if choice == "1":
            run_basic_demo()
        elif choice == "2":
            run_medium_demo()
        elif choice == "3":
            run_large_demo()
        elif choice == "4":
            run_custom_demo()
        elif choice == "5":
            print("\nTạm biệt! 👋")
            break
        else:
            print("❌ Lựa chọn không hợp lệ, vui lòng thử lại")

        input("\nNhấn ENTER để tiếp tục...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nChương trình bị dừng bởi người dùng")
        sys.exit(0)