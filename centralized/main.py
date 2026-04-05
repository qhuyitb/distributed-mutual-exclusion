import threading
import time
from coordinator import Coordinator
from node import Node

"""
Main module - chạy các kịch bản mô phỏng thuật toán Centralized.

Bao gồm các case:
- Truy cập đơn lẻ (single node)
- Tranh chấp tài nguyên (queue)
- Cấp quyền theo thứ tự FIFO

Dùng để kiểm thử và minh họa hoạt động của hệ thống.
"""


# Hình 1: 1 Node truy cập
def demo_single_node():
    print("\nDEMO 1: SINGLE NODE\n")

    coordinator = Coordinator()
    node0 = Node(0, coordinator)

    t = threading.Thread(target=node0.enter_CS)
    t.start()
    t.join()


# Hình 2: Có hàng đợi
def demo_with_queue():
    print("\nDEMO 2: QUEUE\n")

    coordinator = Coordinator()

    node0 = Node(0, coordinator)
    node1 = Node(1, coordinator)
    node2 = Node(2, coordinator)

    t0 = threading.Thread(target=node0.enter_CS)
    t1 = threading.Thread(target=node1.enter_CS)
    t2 = threading.Thread(target=node2.enter_CS)

    t0.start()
    time.sleep(0.1)  # đảm bảo node0 vào trước

    t1.start()
    t2.start()

    t0.join()
    t1.join()
    t2.join()


# Hình 3: Cấp quyền tiếp theo
def demo_grant_next():
    print("\nDEMO 3: GRANT NEXT\n")

    coordinator = Coordinator()

    node0 = Node(0, coordinator)
    node1 = Node(1, coordinator)

    t0 = threading.Thread(target=node0.enter_CS)
    t1 = threading.Thread(target=node1.enter_CS)

    t0.start()
    time.sleep(0.1)  # đảm bảo node0 vào trước

    t1.start()

    t0.join()
    t1.join()


if __name__ == "__main__":
    # demo_single_node()
    # demo_with_queue()
    demo_grant_next()