import os
import threading
from datetime import datetime

class SharedResource:
    """Quản lý truy cập file tài nguyên dùng chung"""
    
    def __init__(self):
        # Sử dụng path tuyệt đối để đảm bảo ghi vào đúng vị trí
        self.SHARED_FILE = os.path.join(os.path.dirname(__file__), "shared.txt")
        # Lock để đảm bảo atomicity khi đọc/ghi file
        self.file_lock = threading.Lock()
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Tạo file nếu chưa tồn tại"""
        if not os.path.exists(self.SHARED_FILE):
            with open(self.SHARED_FILE, 'w') as f:
                f.write("Shared Resource - Access Log\n")
                f.write("============================\n")
    
    def read(self):
        """Đọc nội dung file"""
        with self.file_lock:
            try:
                with open(self.SHARED_FILE, 'r') as f:
                    return f.read()
            except FileNotFoundError:
                return ""
    
    def append(self, node_id, content):
        """Thêm nội dung vào file"""
        with self.file_lock:
            try:
                with open(self.SHARED_FILE, 'a') as f:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    f.write(f"\n[{timestamp}] Node {node_id}: {content}")
            except IOError as e:
                print(f"Error writing to shared file: {e}")
    
    def write_access_record(self, node_id, message=""):
        """Ghi record truy cập và thay đổi nội dung file"""
        with self.file_lock:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                access_record = f"\n[{timestamp}] Node {node_id} accessed CS - {message}"
                
                with open(self.SHARED_FILE, 'a') as f:
                    f.write(access_record)
                    f.flush()  # Đảm bảo dữ liệu được ghi xuống
                    os.fsync(f.fileno())  # Sync với filesystem
            except IOError as e:
                print(f"Error writing to shared file: {e}")
    
    def get_access_count(self):
        """Lấy số lần đã truy cập"""
        content = self.read()
        count = content.count("Node") - 1  # Trừ 1 dòng header
        return max(0, count)
    
    def write_data(self, node_id, data):
        """Ghi dữ liệu tùy ý vào file"""
        with self.file_lock:
            try:
                with open(self.SHARED_FILE, 'a') as f:
                    f.write(f"\n{data}")
            except IOError as e:
                print(f"Error writing to shared file: {e}")
