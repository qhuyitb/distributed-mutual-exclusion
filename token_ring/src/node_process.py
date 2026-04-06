"""Process entrypoint for a single token-ring node.

Runs a Node instance (from node.py) which listens on base_port + node_id.
This script is intended to be started multiple times (once per node),
each in its own terminal window for a distributed demo.
"""
import argparse
import json
import os
import signal
import time
from datetime import datetime
import random

from node import Node


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--node-id", type=int, required=True)
    p.add_argument("--base-port", type=int, default=5000)
    p.add_argument("--num-nodes", type=int, default=4)
    p.add_argument("--host", type=str, default="127.0.0.1")
    p.add_argument("--bootstrap", action="store_true", help="If set, this node will inject the initial token")
    p.add_argument("--stats-dir", type=str, default=None, help="Directory to write per-node stats on exit")
    p.add_argument("--auto-demo", action="store_true", help="Automatically send DATA messages when holding the token")
    p.add_argument("--demo-chance", type=float, default=0.5, help="Probability [0..1] to send a DATA message when receiving the token")
    p.add_argument("--demo-burst-max", type=int, default=1, help="If >1, send between 1 and this many DATA messages when demo triggers")
    return p.parse_args()


def main():
    args = parse_args()
    node_id = args.node_id
    base_port = args.base_port
    num_nodes = args.num_nodes
    host = args.host
    bootstrap = args.bootstrap
    stats_dir = args.stats_dir or os.getcwd()

    node = Node(node_id=node_id, base_port=base_port, host=host)
    node.set_ring(num_nodes)
    node.start()

    # If requested, attach a demo callback that sends one or more DATA messages with some probability
    if args.auto_demo:
        def demo_on_token(payload):
            try:
                # pick random destinations and send a burst of messages
                if node.num_nodes and node.num_nodes > 1 and random.random() <= args.demo_chance:
                    burst_max = max(1, int(getattr(args, "demo_burst_max", 1)))
                    count = random.randint(1, burst_max)
                    for _ in range(count):
                        dest = random.randrange(0, node.num_nodes)
                        if dest == node.node_id:
                            dest = (dest + 1) % node.num_nodes
                        body = f"auto message from {node.node_id} at {time.time()}"
                        node.send_data(dest, body)
            except Exception as e:
                print(f"[Node {node_id}] demo_on_token error: {e}")

        node.on_token = demo_on_token

    start_time = time.time()

    if bootstrap:
        # Wait briefly for other nodes to start listening then inject token
        time.sleep(1.2)
        node.inject_initial_token()

    def handle_shutdown(signum, frame):
        print(f"[Node {node_id}] shutting down (signal={signum})")
        node.stop()
        uptime = time.time() - start_time
        stats = {
            "node_id": node_id,
            "host": host,
            "port": node.port,
            "num_nodes": num_nodes,
            "token_count": getattr(node, "token_count", None),
            "data_sent_count": getattr(node, "data_sent_count", None),
            "uptime_seconds": round(uptime, 3),
            "stopped_at": datetime.utcnow().isoformat() + "Z",
        }
        try:
            os.makedirs(stats_dir, exist_ok=True)
            path = os.path.join(stats_dir, f"stats_node_{node_id}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)
            print(f"[Node {node_id}] wrote stats to {path}")
        except Exception as e:
            print(f"[Node {node_id}] failed to write stats: {e}")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    print(f"[Node {node_id}] started (base_port={base_port}, next_port={node.next_node_port})")

    try:
        while True:
            time.sleep(1)
    except SystemExit:
        pass
    except Exception as e:
        print(f"[Node {node_id}] main loop exception: {e}")
        node.stop()


if __name__ == "__main__":
    main()
