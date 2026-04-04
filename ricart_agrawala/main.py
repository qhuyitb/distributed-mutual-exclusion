import argparse
import threading

from config import NODES
from node import Node


def main():
    parser = argparse.ArgumentParser(description="Ricart-Agrawala node process")
    parser.add_argument("--id", type=int, required=True, help="Node ID from config")
    parser.add_argument("--mode", choices=["manual", "auto"], default="manual", help="Request mode")
    args = parser.parse_args()

    if args.id not in NODES:
        raise ValueError(f"Node ID {args.id} is not defined in config")

    host, port = NODES[args.id]
    peers = {nid: addr for nid, addr in NODES.items() if nid != args.id}

    node = Node(args.id, host, port, peers)
    node.start()

    if args.mode == "auto":
        threading.Thread(target=node.auto_request_loop, daemon=True).start()

    print("Ready. Type 'r' then Enter to request CS manually, 'q' to quit.")
    while True:
        try:
            cmd = input("Command [r / q]: ").strip().lower()
        except EOFError:
            break

        if cmd == "r":
            threading.Thread(target=node.request_cs, daemon=True).start()
        elif cmd == "q":
            print("Quitting node...")
            break
        else:
            print("Unknown command")

    print("Node terminated")


if __name__ == "__main__":
    main()