#!/bin/bash
# Start Ricart-Agrawala Demo with Network Communication
# Khởi động Coordinator + 3 Nodes trong các terminal riêng biệt

echo ""
echo "============================================================"
echo "  Ricart-Agrawala Demo - Multi-Process with Network"
echo "============================================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Starting Coordinator on port 5000..."
gnome-terminal -- bash -c "cd $SCRIPT_DIR && python3 coordinator.py; sleep 2" &
sleep 2

echo "Starting Node 0..."
gnome-terminal -- bash -c "cd $SCRIPT_DIR && python3 node_process.py 0 3" &

echo "Starting Node 1..."
gnome-terminal -- bash -c "cd $SCRIPT_DIR && python3 node_process.py 1 3" &

echo "Starting Node 2..."
gnome-terminal -- bash -c "cd $SCRIPT_DIR && python3 node_process.py 2 3" &

echo ""
echo "============================================================"
echo "4 terminals started:"
echo "- 1 Coordinator (port 5000)"
echo "- 3 Nodes (ports 6000, 6001, 6002)"
echo ""
echo "On each Node terminal, type:"
echo "  request    = Request vào Critical Section"
echo "  quit       = Exit node"
echo "============================================================"
echo ""
