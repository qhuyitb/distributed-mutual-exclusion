import time
import threading
import os
from network import Network
from config import NUM_NODES


def clear_console():
    if os.name == "nt":
        os.system("cls")
    else:
        print("\x1b[2J\x1b[H", end="")


def render_ring(snapshot: dict) -> str:
    num = snapshot["num_nodes"]
    cur = snapshot["current_node_index"]
    per_msgs = snapshot["per_node_last_message"]

    # render nodes on one line with token indicator
    parts = []
    for i in range(num):
        token_mark = "[T]" if i == cur else "   "
        last_msg = per_msgs[i]
        label = f"(N{i})"
        parts.append(f"{label}{token_mark}")

    line = "  ".join(parts)

    # prepare per-node last message lines
    msgs = []
    for i, m in enumerate(per_msgs):
        msgs.append(f"N{i} last: {m if m is not None else '-'}")

    return line + "\n" + " | ".join(msgs)


def visualizer(net: Network, stop_event: threading.Event):
    while not stop_event.is_set():
        snap = net.get_snapshot()
        clear_console()
        print("Token Ring demo visualization\n")
        print(render_ring(snap))
        print("\nRecent events:")
        for ts, text in snap["events"][0:12]:
            t = time.strftime("%H:%M:%S", time.localtime(ts))
            print(f"[{t}] {text}")
        time.sleep(0.4)


def main():
    net = Network(NUM_NODES)
    print(f"Created network with {NUM_NODES} nodes")

    # start a visualizer thread
    stop_event = threading.Event()
    viz = threading.Thread(target=visualizer, args=(net, stop_event), daemon=True)
    viz.start()

    # initialize the token on the first node
    net.start_network()
    time.sleep(0.2)

    # Let the token circulate a few rounds while visualizer shows progress
    rounds = 12
    for r in range(rounds):
        time.sleep(0.8)
        net.pass_token()

    # Send a demo DATA message from node 0
    net._log("node 0 injecting demo DATA message")
    net.nodes[0].send_message("Hello from Node 0")

    # Allow a short while for event delivery to appear in visualizer
    time.sleep(2.0)
    stop_event.set()
    time.sleep(0.1)


if __name__ == "__main__":
    main()