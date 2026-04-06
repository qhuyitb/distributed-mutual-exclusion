"""Launcher to open N terminal windows and start node_process.py for each node.

This script attempts to open new terminal windows on the host OS.
It is written to work on Windows (PowerShell/cmd) and has basic support for Linux/macOS
using common terminal commands.

Usage: python launch_nodes.py --num-nodes 4
"""
import argparse
import os
import platform
import subprocess
import sys


def _windows_launch(cmd: str):
    # Launch PowerShell in a new window and run the command, keeping it open (-NoExit)
    # cmd is a string like: python -u "C:\path\to\node_process.py" --node-id 0 ...
    try:
        subprocess.Popen(["cmd", "/c", "start", "powershell", "-NoExit", "-Command", cmd], shell=False)
    except Exception:
        # fallback to cmd.exe if PowerShell start fails
        subprocess.Popen(["cmd", "/c", "start", "cmd", "/k", cmd], shell=False)


def _posix_launch(terminal_cmd: str):
    # Try gnome-terminal, then xterm, then osascript (mac)
    if shutil_which("gnome-terminal"):
        subprocess.Popen(["gnome-terminal", "--", "bash", "-lc", terminal_cmd])
    elif shutil_which("xterm"):
        subprocess.Popen(["xterm", "-hold", "-e", terminal_cmd])
    elif platform.system() == "Darwin":
        # macOS: open Terminal and run command
        apple_cmd = f"osascript -e 'tell application \"Terminal\" to do script \"{terminal_cmd}\"'"
        subprocess.Popen(apple_cmd, shell=True)
    else:
        # Fallback: run in background (won't open new terminal window)
        subprocess.Popen(terminal_cmd, shell=True)


def shutil_which(name: str):
    from shutil import which

    return which(name)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--num-nodes", type=int, default=4)
    p.add_argument("--base-port", type=int, default=5000)
    p.add_argument("--host", type=str, default="127.0.0.1")
    p.add_argument("--stats-dir", type=str, default=None)
    # auto-demo enabled by default; provide a --no-auto-demo to disable
    p.add_argument("--auto-demo", dest="auto_demo", action="store_true", help="Enable automatic DATA sends on token receipt for launched nodes")
    p.add_argument("--no-auto-demo", dest="auto_demo", action="store_false", help="Disable automatic DATA sends for launched nodes")
    p.set_defaults(auto_demo=True)
    p.add_argument("--demo-chance", type=float, default=0.5, help="Probability (0..1) to send a DATA message when a node receives the token")
    args = p.parse_args()

    num_nodes = args.num_nodes
    base_port = args.base_port
    host = args.host
    stats_dir = args.stats_dir

    here = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(here, "node_process.py")

    system = platform.system()
    print(f"Launching {num_nodes} node processes on {system}...")

    for i in range(num_nodes):
        cmd = f'python -u "{script}" --node-id {i} --base-port {base_port} --num-nodes {num_nodes} --host {host}'
        if stats_dir:
            cmd += f' --stats-dir "{stats_dir}"'
        # propagate demo flags to each node process if requested
        if args.auto_demo:
            cmd += " --auto-demo"
            # include demo chance explicitly so each node uses the same value
            cmd += f' --demo-chance {args.demo_chance}'
        # make node 0 the bootstrapper
        if i == 0:
            cmd += " --bootstrap"

        if system == "Windows":
            _windows_launch(cmd)
        else:
            _posix_launch(cmd)

    print("Launched all nodes.")


if __name__ == "__main__":
    main()
