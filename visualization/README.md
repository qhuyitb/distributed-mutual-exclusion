# Visualization - So sanh hieu nang 3 thuat toan

Folder nay tong hop script va output de ve bieu do so sanh hieu nang giua:
- Centralized
- Ricart-Agrawala
- Token Ring

Ngoai ra co Console UI de theo doi luong chay simulation (timeline event, trang thai node)
va tao/mo bieu do ngay trong mot giao dien menu don gian.

Nguon du lieu:
- compare_benchmark_all.json (uu tien)
- compare_benchmark_all.csv (fallback)

## Cach chay

```bash
python visualization/plot_performance.py
```

## Console UI (theo doi luong chay + xem visualize)

Menu interactive:

```bash
python visualization/console_ui.py
```

Chay dashboard truc tiep (khong vao menu):

```bash
python visualization/console_ui.py --mode dashboard --scenario high_contention
```

Tao bieu do:

```bash
python visualization/console_ui.py --mode charts
```

Mo file bieu do da tao:

```bash
python visualization/console_ui.py --mode open-charts
```

Chay all-in-one (benchmark + replay + tao chart + mo chart):

```bash
python visualization/console_ui.py --mode all
```

## Ket qua sinh ra

Trong folder `visualization/output`:
- performance_by_scenario.png: so sanh tung metric theo moi scenario
- performance_overall_mean.png: so sanh gia tri trung binh giua cac scenario
- performance_summary.csv: bang tong hop metric da chuan hoa

## Metric duoc ve

- duration_seconds
- total_messages
- avg_waiting_time
- max_waiting_time
