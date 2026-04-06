# Huong Dan Demo Va Luong Hoat Dong - Thuat Toan Tap Trung

Tai lieu nay mo ta day du:
- Cach demo phan centralized trong project.
- Luong logic cua thuat toan tap trung.
- Cach doc log de xac nhan mutual exclusion va FIFO.

## 1. Tong Quan Thuat Toan

Thanh phan:
- Coordinator (1 tien trinh trung tam): cap quyen vao Critical Section (CS).
- Participant (nhieu node): gui yeu cau vao CS va tra quyen sau khi xu ly xong.

Ba loai thong diep bat buoc:
- REQUEST: Node gui den Coordinator de xin vao CS.
- GRANT: Coordinator gui cho Node de cap quyen vao CS.
- RELEASE: Node gui cho Coordinator khi roi CS.

Trang thai local cua Coordinator:
- is_locked (bool): CS dang duoc cap cho node nao do hay dang rong.
- request_queue (FIFO): hang doi cac REQUEST den trong luc CS dang ban.

Quy tac xu ly tai Coordinator:
1. Nhan REQUEST.
- Neu is_locked = False: gui GRANT ngay va dat is_locked = True.
- Neu is_locked = True: dua node vao request_queue theo thu tu FIFO.
2. Nhan RELEASE.
- Neu queue rong: dat is_locked = False.
- Neu queue co node cho: lay node dau tien, gui GRANT, giu is_locked = True.

Quy tac xu ly tai Node:
1. enter_cs.
- Gui REQUEST.
- Cho (block) den khi nhan GRANT hoac timeout.
- Nhan GRANT thi vao CS.
2. exit_cs.
- Gui RELEASE cho Coordinator sau khi roi CS.

## 2. Demo Nhanh Trong 1 Process

File chinh:
- centralized/main.py

Lenh chay:

```powershell
python centralized/main.py
```

Mac dinh file dang goi demo_grant_next() (2 node tranh chap).

Co the doi sang cac ham demo khac trong file:
- demo_single_node(): 1 node yeu cau.
- demo_with_queue(): 3 node, nhin ro queue FIFO.
- demo_grant_next(): 2 node, node sau cho node truoc RELEASE.

## 3. Demo TCP Da Tien Trinh (Nen Dung Cho Bao Cao)

### 3.1. Mo Coordinator

Terminal A:

```powershell
python -m centralized.coordinator_process --port 7500
```

Neu thay log:
- [Coordinator] listening on 127.0.0.1:7500

thi Coordinator da san sang.

### 3.2. Chay Node Tu Dong Xin Vao CS

Terminal B:

```powershell
python -m centralized.node_process --node-id 0 --coordinator-port 7500 --auto-request --hold-seconds 5 --wait-timeout 6
```

Terminal C:

```powershell
python -m centralized.node_process --node-id 1 --coordinator-port 7500 --auto-request --hold-seconds 1 --wait-timeout 6
```

Luu y:
- Tat ca node phai dung cung coordinator-port.
- Neu sai cong, se gap WinError 10061 (connection refused).

### 3.3. Chay Node Bang CLI Tuong Tac

```powershell
python -m centralized.node_process --node-id 2 --coordinator-port 7500
```

Lenh trong CLI:
- request
- request 3
- quit

Y nghia:
- request: xin vao CS voi thoi gian giu CS mac dinh.
- request 3: giu CS trong 3 giay.

## 4. Luong Log Can Theo Doi

Tai Coordinator:
- REQUEST from Node X
- queued Node Y
- GRANT -> Node X
- RELEASE from Node X
- resource free

Tai Node:
- send REQUEST
- received GRANT
- >>> ENTER CS
- <<< EXIT CS

Ky vong dung:
- Tai moi thoi diem chi co 1 node o trang thai ENTER CS.
- Neu 2 node gui REQUEST gan nhau, node den sau bi dua vao queue.
- Node sau chi ENTER sau khi node truoc EXIT va gui RELEASE.

## 5. So Lieu Hieu Nang De Viet Bao Cao

Theo thuat toan centralized chuan:
- 3 message cho moi luot vao/ra CS:
  - REQUEST + GRANT + RELEASE
- Do tre logic de vao CS la 2 thong diep:
  - REQUEST -> GRANT

Vi du demo 2 node vao CS lan luot:
- Tong 6 message.

## 6. Loi Thuong Gap Va Cach Xu Ly

1. WinError 10061 (connection refused).
- Nguyen nhan: chua chay coordinator hoac sai port.
- Cach sua: mo coordinator truoc, dam bao moi node dung cung port.

2. Node cho lau.
- Nguyen nhan: dang cho GRANT, hoac node truoc dang giu CS qua lau (hold-seconds lon).
- Cach sua: giam hold-seconds, giam wait-timeout neu can.

3. Timeout waiting GRANT.
- Nguyen nhan: coordinator down, sai cong, hoac dia chi callback cua node khong hop le.
- Cach sua: kiem tra log coordinator va tham so coordinator/listen.

## 7. Checklist Demo Dat Yeu Cau

- [ ] Coordinator da chay truoc.
- [ ] Tat ca node dung cung coordinator-port.
- [ ] Co it nhat 2 node request gan nhau de quan sat FIFO.
- [ ] Log hien ro thu tu REQUEST -> GRANT -> ENTER -> EXIT -> RELEASE.
- [ ] Khong bao gio co 2 node ENTER CS cung luc.
