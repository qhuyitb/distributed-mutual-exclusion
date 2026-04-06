"""
Entrypoint chạy 1 node Token Ring trong process độc lập.

Mục tiêu:
- Mỗi node chạy trong 1 terminal/window riêng để mô phỏng môi trường phân tán.
- Nhận lệnh `STOP` qua socket để dừng node.
- Ghi stats ra file JSON để demo tổng hợp khi kết thúc.
"""

import argparse
import json
import os
import sys
import time

from .node import Node


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-id", type=int, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--next-host", type=str, default="localhost")
    parser.add_argument("--next-port", type=int, required=True)
    parser.add_argument("--stats-out", type=str, required=True)
    parser.add_argument(
        "--wait-on-exit",
        action="store_true",
        help="Giữ terminal mở sau khi node dừng để quan sát logging.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Node tự cấu hình logging trong node.py; ở đây chỉ cần đảm bảo unbuffered output.
    node = Node(
        node_id=args.node_id,
        port=args.port,
        next_node_host=args.next_host,
        next_node_port=args.next_port,
    )
    node.start()

    try:
        # Block cho tới khi nhận STOP (node.stop() sẽ set is_running=False)
        while node.is_running:
            time.sleep(0.5)
    except KeyboardInterrupt:
        node.stop()
    finally:
        stats = node.get_stats()
        os.makedirs(os.path.dirname(args.stats_out), exist_ok=True)
        with open(args.stats_out, "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        if args.wait_on_exit:
            # Giữ console mở để người dùng xem log sau khi demo kết thúc.
            try:
                input("\nNode stopped. Press Enter to close this terminal...\n")
            except EOFError:
                pass


if __name__ == "__main__":
    main()