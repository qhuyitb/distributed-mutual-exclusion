# common/config_loader.py
import json
import os
from common.base_process import PeerInfo

def load_config(path: str = None) -> dict:
    """
    Đọc config.json. Tự tìm file từ thư mục gốc project
    nếu không truyền path.
    """
    if path is None:
        # Tìm config.json từ thư mục gốc project
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(root, "config.json")

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    return {
        "nodes"       : [PeerInfo(**n) for n in data["nodes"]],
        "cs_duration" : data.get("cs_duration", 2.0),
        "base_port"   : data.get("base_port", 25000),
    }

def get_peers(all_nodes: list, my_pid: int) -> list:
    """Trả về danh sách peer (tất cả trừ chính mình)."""
    return [n for n in all_nodes if n.pid != my_pid]