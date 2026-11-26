# Benchmark & Observability Report — Day 14

> Copy file này thành `BENCHMARK_REPORT.md` trong repo của bạn và điền đầy đủ.
> Mọi con số phải lấy từ report JSON / CSV / screenshot thật, không ước lượng.

**Họ tên:** Vương Thu Thảo
**Ngày chạy:** 26/11/2026
**Môi trường:** Windows 11/PowerShell, Docker Desktop; cấu hình CPU/RAM

---

## 1. SLO của agent

| SLI | SLO | Lý do chọn ngưỡng này |
|---|---|---|
| p95 latency `/ask` | < 500 ms | Ngưỡng đang được sử dụng trong trường slo.p95_ms của các report load test. |
| Error rate `/ask` | < 2 % | Ngưỡng đang được sử dụng trong trường slo.error_rate của các report load test.|
| Accuracy trên golden dataset | ≥ 80 % | Ngưỡng quality gate ban đầu trong eval_v2.json (min_accuracy: 0.8). Bản sửa KB cuối cùng đạt 100%.|
---

## 2. Benchmark hiệu năng (develop, `load_test.py`)

### 2.1 Concurrency vs latency (agent v2)

| Concurrency | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Error rate | SLO |
|---:|---:|---:|---:|---:|---:|---|
| 1 | 3.96 | 204.6 | 238.1 | 1703.1 | 1.67% | PASS |
| 10 | 35.23 | 192.0 | 466.2 | 1712.1 | 1.67% | PASS |
| 50 | 80.91 | 303.2 | 1252.3 | 2013.1 | 0.67% | FAIL |
| 100 | 38.82 | 1105.7 | 5539.9 | 5729.0 | 0.67% | FAIL |

**Nhận xét:** RPS có tăng tuyến tính theo concurrency không? Vì sao?

RPS không tăng tuyến tính theo concurrency. RPS tăng từ 3.96 ở concurrency 1 lên 80.91 ở concurrency 50, nhưng giảm còn 38.82 ở concurrency 100. Khi tải tăng cao, latency p95/p99 tăng mạnh; hệ thống có dấu hiệu quá tải hoặc nghẽn tài nguyên, khiến thông lượng không còn tăng tương ứng với số người dùng đồng thời. Theo report, concurrency 1 và 10 đạt SLO; concurrency 50 và 100 không đạt do p95 vượt 500 ms.

### 2.2 Tail latency


| `MOCK_SLOW_RATE` | avg (ms) | p95 (ms) | p99 (ms) |
|---:|---:|---:|---:|
| 0 | 219.9 | 477.9 | 501.4 |
| 0.03 (mặc định) | 247.3 | 502.4 | 1708.2 |
| 0.1 | 369.4 | 1699.6 | 1728.4 |

**Nhận xét:** Chỉ số nào nhạy nhất với request chậm? Vì sao SLO không nên đặt theo average?

p99 thể hiện rõ ảnh hưởng của các request chậm ở cấu hình mặc định: tăng từ 501.4 ms (slow_rate=0) lên 1708.2 ms (0.03). Khi tăng tỷ lệ request chậm lên 0.1, p95 tăng lên 1699.6 ms và p99 lên 1728.4 ms. Average cũng tăng, nhưng có thể che khuất nhóm request có thời gian phản hồi rất lớn; vì vậy SLO nên theo dõi percentile như p95/p99 thay vì chỉ dựa vào average.

---

## 3. Benchmark chất lượng (develop, `eval/run_eval.py`)


| Chỉ số | Agent v1 | Agent v2 | Agent v2 (sau khi sửa KB) |
|---|---:|---:|---:|
| Accuracy | 4.35% (1/23) | 91.30% (21/23) | 100% (23/23) |
| Avg tokens / câu | 58 | 109 | 125 |
| Tổng cost (USD) | 0.000417 | 0.000759 | 0.000888 |
| Cost / câu đúng (USD) | 0.00041715 | 0.00003616 | 0.00003863 |
| Quality gate | FAIL | PASS | PASS |

**Những câu v2 trả lời sai ban đầu và cách bạn sửa:**

| ID | Keyword bị thiếu | Bạn đã sửa gì |
|---|---|---|
| `security-02` | `token`, `hết hạn`, `chữ ký` | Bổ sung kiến thức về JWT: access token/refresh token, thời hạn token, kiểm tra chữ ký và thời điểm hết hạn. |
| `scaling-03` | `cpu`, `memory`, `custom metrics` | Bổ sung kiến thức Kubernetes HPA/autoscaling: scale Pod theo CPU, memory và custom metrics. |

**Nhận xét về trade-off chất lượng / chi phí / latency giữa v1 và v2:**

- V2 cải thiện accuracy từ 4.35% lên 91.30%; sau khi bổ sung KB, accuracy đạt 100%.
- Tổng cost tăng từ 0.000417 USD (v1) lên 0.000759 USD (v2), rồi 0.000888 USD (v2 sau sửa KB), do lượng token trung bình tăng từ 58 lên 109 và 125.
- Cost trên mỗi câu đúng giảm mạnh từ 0.00041715 USD ở v1 xuống 0.00003616 USD ở v2; bản sửa KB là 0.00003863 USD/câu đúng.
- Latency p50/p95 trong eval: v1 là 164.6/1526.9 ms; v2 là 216.0/220.5 ms; v2 sau sửa KB là 199.4/252.2 ms. V1 có p95 cao bất thường so với p50; v2 và bản sửa KB ổn định hơn trong lần eval tương ứng.

---

## 4. Observability stack (production)

### 4.1 Screenshot

- [ ] Dashboard Grafana khi đang có tải (thấy rõ Golden Signals)
- [ ] Một trace chậm trong Jaeger (thấy span nào chiếm thời gian)
- [ ] Một trace lỗi trong Jaeger (có event `exception`)
- [ ] Trang Alerts của Prometheus với ít nhất 1 alert đang **firing**

### 4.2 Thí nghiệm "phá hệ thống"

| # | Thay đổi | Alert nào firing | Thời gian từ lúc đổi → firing | Panel nào phản ánh rõ nhất |
|---|---|---|---|---|
| A | `MOCK_ERROR_RATE=0.2` | Chưa có dữ liệu | Chưa có dữ liệu | Chưa có dữ liệu |
| B | `MOCK_SLOW_RATE=0.3` | Chưa có dữ liệu | Chưa có dữ liệu | Chưa có dữ liệu |
| C | `LLM_MODEL=mock-llm-large` | Chưa có dữ liệu | Chưa có dữ liệu | Chưa có dữ liệu |
| D | `docker pause` 1 instance | Chưa có dữ liệu | Chưa có dữ liệu | Chưa có dữ liệu |
| E | `AGENT_VERSION=v1` | Chưa có dữ liệu | Chưa có dữ liệu | Chưa có dữ liệu |

**Thí nghiệm E không làm alert nào firing. Bạn sẽ phát hiện loại sự cố này trong production bằng cách nào?**

Dùng quality monitoring thay vì chỉ dựa vào hạ tầng alert: chạy định kỳ golden-dataset evaluation hoặc canary evaluation cho từng phiên bản; theo dõi accuracy, tỷ lệ câu trả lời đúng, tỷ lệ fallback và regression theo AGENT_VERSION. Đặt quality gate khi deploy để chặn phiên bản có accuracy thấp hơn ngưỡng; đồng thời phát cảnh báo khi chất lượng giảm dù latency, error rate và CPU vẫn bình thường. Đây là đề xuất vận hành, chưa phải kết quả đo trong các file đã cung cấp.


### 4.3 Debug bằng trace

Chọn 1 trace chậm nhất bạn tìm được:

- `trace_id`: ...
- Tổng thời gian: ... ms
- Span chiếm nhiều thời gian nhất: ... (... ms, ...%)
- Dòng log tương ứng (grep theo `trace_id`):

```json

```

---

## 5. Benchmark scaling (production, Locust headless, 100 users, 2 phút)

| Số instance | RPS | p50 (ms) | p95 (ms) | p99 (ms) | Failures |
|---:|---:|---:|---:|---:|---:|
| 1 | 62.54 | 3 | 13 | 2000 | 7,466 / 7,466 (100%) |
| 3 | 70.20 | 3 | 7 | 20 | 8,386 / 8,386 (100%) |

**Giải thích kết quả:** Scale có cải thiện p95 không? Nút thắt nằm ở đâu?

Theo CSV Locust, khi tăng từ 1 lên 3 instance, RPS tăng từ 62.54 lên 70.20; p95 giảm từ 13 ms xuống 7 ms và p99 giảm từ 2000 ms xuống 20 ms. Tuy nhiên, cả hai lần chạy đều ghi nhận toàn bộ request là failure (1 instance: 7,466/7,466; 3 instance: 8,386/8,386). Vì vậy không thể kết luận hệ thống đã scale thành công hoặc p95 phản ánh latency của request thành công. Cần xử lý lỗi upstream trước, kiểm tra scale_1_failures.csv và scale_3_failures.csv: các lỗi ghi nhận gồm HTTP 502 Bad Gateway và 504 Gateway Time-out ở /ask và /health. Sau khi sửa, chạy lại Locust headless để có số liệu scaling hợp lệ.

---

## 6. Kết luận

- 3 điều bạn học được về benchmark & observability:
  1. Concurrency tăng không đồng nghĩa RPS tăng tuyến tính; khi quá tải, p95/p99 có thể tăng mạnh và throughput có thể giảm.
  2. Average latency không phản ánh đầy đủ tail latency; cần theo dõi p95/p99 để phát hiện nhóm request chậm.
  3.Benchmark phải đọc cả request count và failure count. RPS hoặc percentile đẹp không có ý nghĩa nếu toàn bộ request đều thất bại; cần kết hợp metrics, logs và distributed traces để tìm nguyên nhân.
- Nếu đưa agent này lên production thật, bạn sẽ thêm metric / alert nào nữa?

Theo dõi thêm tỷ lệ HTTP 5xx/4xx, request rate, p50/p95/p99 theo endpoint, số request đang xử lý, timeout, retry, queue depth, CPU/RAM, restart/OOM container, số lượng LLM token và cost theo model/version, tỷ lệ fallback, accuracy trên golden dataset và tỷ lệ regression theo AGENT_VERSION. Thiết lập alert riêng cho availability, latency, error rate, tài nguyên và chất lượng câu trả lời.
