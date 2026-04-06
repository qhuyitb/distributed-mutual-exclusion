import threading
import time

try:
    from .communication import CommunicationLayer
    from .coordinator import Coordinator
    from .node import Node
except ImportError:
    from communication import CommunicationLayer
    from coordinator import Coordinator
    from node import Node

"""Các kịch bản chạy thử thuật toán loại trừ tương hỗ tập trung.

Mục tiêu của file này:
- Minh họa đúng luồng REQUEST -> GRANT -> RELEASE.
- Quan sát hành vi FIFO tại Coordinator khi có tranh chấp.
- Ghi nhanh số liệu thực nghiệm cơ bản: tổng số message và độ trễ request-grant.
"""


# Hình 1: 1 Node truy cập
def demo_single_node():
    """Kịch bản một nút: kiểm tra luồng cấp quyền cơ bản."""

    print("\nDEMO 1: SINGLE NODE\n")

    comm = CommunicationLayer()
    coordinator = Coordinator(coordinator_id=-1, comm=comm)
    node0 = Node(0, coordinator_id=-1, comm=comm)

    comm.register(-1, coordinator, port=7000)
    comm.register(0, node0, port=7001)
    comm.start()

    t = threading.Thread(target=node0.enter_CS)
    t.start()
    t.join()
    time.sleep(0.1)
    comm.stop()

    print(f"[Metrics] total messages: {comm.total_messages}")
    print(f"[Metrics] node0 request->grant latency: {node0.last_grant_latency:.4f}s")


# Hình 2: Có hàng đợi
def demo_with_queue():
    """Kịch bản ba nút: kiểm tra hàng đợi FIFO khi vùng tới hạn bận."""

    print("\nDEMO 2: QUEUE\n")

    comm = CommunicationLayer()
    coordinator = Coordinator(coordinator_id=-1, comm=comm)

    node0 = Node(0, coordinator_id=-1, comm=comm)
    node1 = Node(1, coordinator_id=-1, comm=comm)
    node2 = Node(2, coordinator_id=-1, comm=comm)

    comm.register(-1, coordinator, port=7100)
    comm.register(0, node0, port=7101)
    comm.register(1, node1, port=7102)
    comm.register(2, node2, port=7103)
    comm.start()

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
    time.sleep(0.1)
    comm.stop()

    print(f"[Metrics] total messages: {comm.total_messages}")
    print("[Metrics] per critical-section entry: 3 messages (REQUEST, GRANT, RELEASE)")


# Hình 3: Cấp quyền tiếp theo
def demo_grant_next():
    """Kịch bản hai nút liên tiếp: kiểm tra cấp quyền cho nút kế tiếp."""

    print("\nDEMO 3: GRANT NEXT\n")

    comm = CommunicationLayer()
    coordinator = Coordinator(coordinator_id=-1, comm=comm)

    node0 = Node(0, coordinator_id=-1, comm=comm)
    node1 = Node(1, coordinator_id=-1, comm=comm)

    comm.register(-1, coordinator, port=7200)
    comm.register(0, node0, port=7201)
    comm.register(1, node1, port=7202)
    comm.start()

    t0 = threading.Thread(target=node0.enter_CS)
    t1 = threading.Thread(target=node1.enter_CS)

    t0.start()
    time.sleep(0.1)  # đảm bảo node0 vào trước

    t1.start()

    t0.join()
    t1.join()
    time.sleep(0.1)
    comm.stop()

    print(f"[Metrics] total messages: {comm.total_messages}")
    print(f"[Metrics] node0 request->grant latency: {node0.last_grant_latency:.4f}s")
    print(f"[Metrics] node1 request->grant latency: {node1.last_grant_latency:.4f}s")


if __name__ == "__main__":
    # demo_single_node()
    # demo_with_queue()
    demo_grant_next()