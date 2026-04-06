# Huong dan chay UI va xem Visualization

## 1) Mo terminal dung thu muc project

Thu muc goc can dung:
D:/workspace/distributed-mutual-exclusion

## 2) Chay menu UI (de test day du)

Lenh:
python visualization/console_ui.py

Khi chay lenh tren, menu se hien:
1) Run dashboard (benchmark + summary + replay)
2) Generate charts
3) Open charts
4) Exit

## 3) Cach test nhanh UI co dung y khong

Buoc de xuat:
- Chon 1 de chay dashboard
- Quan sat:
  - Co chay du 3 thuat toan: centralized, ricart_agrawala, token_ring
  - Co in bang tong hop metric
  - Co replay flow event theo timeline

Neu flow qua nhanh, ban chay bang lenh truc tiep o muc 4 va giam toc do replay.

## 4) Chay truc tiep tung che do (khong vao menu)

Chay dashboard:
python visualization/console_ui.py --mode dashboard --scenario high_contention --replay-speed 12

Tao bieu do:
python visualization/console_ui.py --mode charts

Mo bieu do da tao:
python visualization/console_ui.py --mode open-charts

Chay tat ca trong 1 lenh:
python visualization/console_ui.py --mode all --scenario high_contention --replay-speed 12

## 5) File output de xem visualization

Sau khi generate chart, xem trong folder:
visualization/output

File chinh:
- performance_by_scenario.png
- performance_overall_mean.png
- performance_summary.csv

## 6) Neu gap loi thu vien

Cai matplotlib:
pip install matplotlib

Neu muon giao dien console dep hon (bang mau, panel):
pip install rich

