#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║        Ricart-Agrawala Distributed Mutex — TCP           ║
╠══════════════════════════════════════════════════════════╣
║  Chạy mỗi node trong 1 terminal riêng:                  ║
║    python test/run_node.py 0 3                           ║
║    python test/run_node.py 1 3                           ║
║    python test/run_node.py 2 3                           ║
║                                                          ║
║  Điều khiển:                                             ║
║    r + Enter  →  Request Critical Section                ║
║    q + Enter  →  Quit                                    ║
╚══════════════════════════════════════════════════════════╝

Thuật toán Ricart-Agrawala:
  - Khi muốn vào CS: gửi REQUEST(ts, id) cho tất cả node khác
  - Nhận REQUEST từ node j:
      • Nếu đang HELD    → hoãn REPLY
      • Nếu đang WANTED  → hoãn nếu (req_ts, my_id) < (ts_j, j), ngược lại REPLY ngay
      • Nếu RELEASED     → REPLY ngay
  - Vào CS khi nhận đủ (n-1) REPLY
  - Ra CS: gửi REPLY cho tất cả request đã hoãn
"""

import socket
import threading
import time
import sys
import json

# ── ANSI color codes ───────────────────────────────────────────────────────────
RST = '\033[0m'
BLD = '\033[1m'
DIM = '\033[2m'
RED = '\033[91m'
GRN = '\033[92m'
YLW = '\033[93m'
BLU = '\033[94m'
MGT = '\033[95m'
CYN = '\033[96m'
WHT = '\033[97m'

# ── Cấu hình ──────────────────────────────────────────────────────────────────
BASE_PORT   = 5000   # Node i lắng nghe trên cổng BASE_PORT + i
CS_DURATION = 3      # Thời gian giữ CS (giây) để dễ demo


class Node:
    """
    Một node trong hệ thống Ricart-Agrawala.

    Trạng thái:
        RELEASED  : Không cần CS
        WANTED    : Đã gửi REQUEST, đang chờ đủ REPLY
        HELD      : Đang trong Critical Section
    """

    def __init__(self, node_id: int, n: int):
        self.id = node_id
        self.n  = n

        # Đồng hồ Lamport
        self.clock = 0
        # Trạng thái hiện tại
        self.state = 'RELEASED'
        # Timestamp lúc gửi REQUEST (dùng để so sánh ưu tiên)
        self.req_ts = 0
        # Số REPLY đã nhận cho request hiện tại
        self.replies = 0
        # Danh sách các node cần gửi REPLY bị hoãn
        self.deferred: list[int] = []

        # Cổng TCP của node này
        self.port = BASE_PORT + node_id

        # Lock bảo vệ tất cả state trên
        self.mu = threading.Lock()

    # ── Logging ───────────────────────────────────────────────────────────────

    def log(self, msg: str, color: str = WHT):
        """In log với timestamp thực và Lamport clock."""
        ts = time.strftime('%H:%M:%S')
        print(
            f"{DIM}[{ts}]{RST} "
            f"{BLD}{CYN}[Node-{self.id}]{RST} "
            f"{DIM}[clk={self.clock:03d}]{RST} "
            f"{color}{msg}{RST}",
            flush=True
        )

    # ── Mạng ──────────────────────────────────────────────────────────────────

    def _send(self, target_id: int, mtype: str, clock_val: int = None):
        """
        Mở kết nối TCP tới node target_id và gửi một JSON message.
        Tự động thử lại 3 lần nếu thất bại.
        """
        clk = clock_val if clock_val is not None else self.clock
        payload = json.dumps({
            'type':  mtype,
            'from':  self.id,
            'clock': clk,
        }).encode()

        port = BASE_PORT + target_id
        for attempt in range(3):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5)
                s.connect(('localhost', port))
                s.sendall(payload)
                s.close()
                return
            except OSError:
                if attempt < 2:
                    time.sleep(0.3 * (attempt + 1))
        self.log(f"✗ Không kết nối được Node-{target_id} sau 3 lần thử", RED)

    def _serve(self, server: socket.socket):
        """Accept loop: mỗi kết nối chạy trên 1 thread riêng."""
        while True:
            try:
                conn, _ = server.accept()
                threading.Thread(
                    target=self._handle_conn,
                    args=(conn,),
                    daemon=True
                ).start()
            except Exception as e:
                self.log(f"Server error: {e}", RED)

    def _handle_conn(self, conn: socket.socket):
        """Đọc một message từ conn, cập nhật clock và dispatch."""
        try:
            data = b''
            while chunk := conn.recv(4096):
                data += chunk
            msg = json.loads(data)

            # Cập nhật Lamport clock khi nhận
            with self.mu:
                self.clock = max(self.clock, msg['clock']) + 1

            if msg['type'] == 'REQUEST':
                self._on_request(sender=msg['from'], ts_j=msg['clock'])
            elif msg['type'] == 'REPLY':
                self._on_reply(sender=msg['from'])
        except Exception:
            pass
        finally:
            conn.close()

    # ── Thuật toán ────────────────────────────────────────────────────────────

    def _on_request(self, sender: int, ts_j: int):
        """
        Nhận REQUEST(ts_j) từ node `sender`.
        Quyết định REPLY ngay hoặc hoãn lại.
        """
        defer  = False
        reason = ''

        with self.mu:
            if self.state == 'HELD':
                # Đang trong CS → luôn hoãn
                defer  = True
                reason = f"{YLW}đang trong CS{RST}"

            elif self.state == 'WANTED':
                # Cả hai cùng muốn vào CS → so sánh ưu tiên
                # Tuple (timestamp, id) nhỏ hơn → ưu tiên cao hơn
                my_key    = (self.req_ts, self.id)
                their_key = (ts_j, sender)

                if my_key < their_key:
                    defer  = True
                    reason = (
                        f"ta ({self.req_ts},{self.id}) < "
                        f"họ ({ts_j},{sender}) → ta ưu tiên"
                    )
                else:
                    reason = (
                        f"họ ({ts_j},{sender}) ≤ "
                        f"ta ({self.req_ts},{self.id}) → họ ưu tiên"
                    )
            else:
                # RELEASED → REPLY ngay
                reason = "ta đang RELEASED"

            if defer:
                self.deferred.append(sender)
                self.clock += 1

        if defer:
            self.log(
                f"📥 REQUEST ← Node-{sender} [ts={ts_j}]  "
                f"➜  {YLW}DEFERRED{RST}  ({reason})",
                YLW
            )
        else:
            self.log(
                f"📥 REQUEST ← Node-{sender} [ts={ts_j}]  "
                f"➜  {CYN}REPLY ngay{RST}  ({reason})",
                CYN
            )
            with self.mu:
                self.clock += 1
            self._send(sender, 'REPLY')

    def _on_reply(self, sender: int):
        """Nhận REPLY từ node `sender`."""
        enter = False
        cnt   = 0

        with self.mu:
            # Bỏ qua REPLY stale (không đang WANTED)
            if self.state != 'WANTED':
                self.log(
                    f"📨 REPLY ← Node-{sender}  (bỏ qua, state={self.state})",
                    DIM
                )
                return
            self.replies += 1
            cnt   = self.replies
            enter = (cnt == self.n - 1)

        self.log(
            f"📨 REPLY ← Node-{sender}  "
            f"[{cnt}/{self.n - 1} replies nhận được]",
            GRN
        )

        if enter:
            self._enter_cs()

    # ── Critical Section lifecycle ────────────────────────────────────────────

    def request_cs(self):
        """Khởi tạo request vào CS (gọi từ thread nhập lệnh)."""
        with self.mu:
            if self.state != 'RELEASED':
                self.log(f"⚠  Đang ở trạng thái '{self.state}' — bỏ qua request", YLW)
                return
            self.clock  += 1
            self.req_ts  = self.clock
            self.state   = 'WANTED'
            self.replies = 0
            ts = self.req_ts   # Lưu lại TRƯỚC khi release lock

        self.log('─' * 54, MGT)
        self.log(
            f"🙋 REQUEST CS  [ts={ts}]  →  broadcast tới {self.n - 1} node(s)…",
            MGT
        )

        others = [i for i in range(self.n) if i != self.id]
        for nid in others:
            # Gửi với clock_val = req_ts để receiver so sánh chính xác
            self._send(nid, 'REQUEST', clock_val=ts)
            self.log(f"   📤 REQUEST → Node-{nid}", BLU)

        # Trường hợp chỉ có 1 node → vào CS ngay
        if not others:
            self._enter_cs()

    def _enter_cs(self):
        """Vào Critical Section."""
        with self.mu:
            self.state = 'HELD'

        bar = '═' * 54
        self.log(bar, GRN)
        self.log(f"🔒  ENTERED  CRITICAL  SECTION", f"{GRN}{BLD}")
        self.log(bar, GRN)

        for remaining in range(CS_DURATION, 0, -1):
            self.log(f"   ⏳  Đang thực thi trong CS…  thoát sau {remaining}s", GRN)
            time.sleep(1)

        self._exit_cs()

    def _exit_cs(self):
        """Thoát CS và gửi REPLY cho các request đã hoãn."""
        with self.mu:
            self.state  = 'RELEASED'
            self.clock += 1
            deferred    = self.deferred[:]
            self.deferred.clear()

        self.log(
            f"🔓  RELEASED CS  |  deferred queue: "
            f"{deferred if deferred else '∅'}",
            f"{GRN}{BLD}"
        )
        self.log('─' * 54, GRN)

        for nid in deferred:
            with self.mu:
                self.clock += 1
            self._send(nid, 'REPLY')
            self.log(f"   📤 Deferred REPLY → Node-{nid}", CYN)

    # ── Khởi động ─────────────────────────────────────────────────────────────

    def _start_server(self):
        """Bind và bắt đầu lắng nghe kết nối TCP đến."""
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            srv.bind(('localhost', self.port))
        except OSError as e:
            print(f"{RED}✗ Không thể bind cổng {self.port}: {e}{RST}")
            print(f"{YLW}  Hãy chắc chắn không có process nào đang dùng cổng này.{RST}")
            sys.exit(1)
        srv.listen(50)
        threading.Thread(target=self._serve, args=(srv,), daemon=True).start()
        self.log(f"🟢 Lắng nghe trên localhost:{self.port}", GRN)

    def run(self):
        self._start_server()
        time.sleep(0.2)   # Chờ server sẵn sàng

        # Hiển thị banner
        w = 54
        lines = [
            f"{'═'*w}",
            f"  Ricart-Agrawala Mutual Exclusion  (TCP Sockets)",
            f"  Node ID : {self.id}   |   Tổng số nodes : {self.n}",
            f"  Port    : localhost:{self.port}",
            f"{'─'*w}",
            f"  r + Enter  →  Request Critical Section",
            f"  q + Enter  →  Quit",
            f"{'═'*w}",
        ]
        print(f"\n{CYN}{BLD}", flush=True)
        for line in lines:
            print(f"  {line}")
        print(f"{RST}", flush=True)

        # Vòng lặp nhập lệnh
        while True:
            try:
                cmd = input().strip().lower()
            except (EOFError, KeyboardInterrupt):
                break

            if cmd == 'r':
                threading.Thread(target=self.request_cs, daemon=True).start()
            elif cmd == 'q':
                break
            elif cmd == '':
                pass   # ignore blank line
            else:
                self.log(f"Lệnh không hợp lệ: '{cmd}' (dùng r hoặc q)", DIM)

        self.log("Đang tắt node…", DIM)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(
            f"\nCách dùng:\n"
            f"  python {sys.argv[0]} <node_id> [total_nodes]\n\n"
            f"Ví dụ (3 terminal):\n"
            f"  python {sys.argv[0]} 0 3\n"
            f"  python {sys.argv[0]} 1 3\n"
            f"  python {sys.argv[0]} 2 3\n"
        )
        sys.exit(1)

    try:
        nid = int(sys.argv[1])
        n   = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    except ValueError:
        print(f"{RED}Lỗi: node_id và total_nodes phải là số nguyên.{RST}")
        sys.exit(1)

    if not (0 <= nid < n):
        print(f"{RED}Lỗi: node_id phải trong khoảng [0, {n-1}]{RST}")
        sys.exit(1)

    Node(nid, n).run()
