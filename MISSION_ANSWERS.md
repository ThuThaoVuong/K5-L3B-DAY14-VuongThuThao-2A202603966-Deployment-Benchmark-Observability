# Day 14 Lab - Mission Answers

## Part 1: Localhost vs Production

### Exercise 1.1: Anti-patterns found
1. Vấn đề 1: API key hardcode trong code
2. Vấn đề 2: Không có config management
3. Vấn đề 3: Print thay vì proper logging, từ đó in ra secret key
4. Vấn đề 4: Không có health check endpoint. Nếu agent crash, platform không biết để restart
5. Vấn đề 5: Port cố định — không đọc từ environment. Trên Railway/Render, PORT được inject qua env var
...

### Exercise 1.3: Comparison table
| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
Config | Hardcode API key, DATABASE URL, DEBUG, PORT trong code | Sử dụng Environment Variables (.env, config.py) | Bảo mật thông tin nhạy cảm, dễ thay đổi cấu hình giữa Development và Production mà không cần sửa code.|
Health check | Không có endpoint kiểm tra trạng thái ứng dụng | Có /health, /ready, /metrics | Giúp giám sát tình trạng hoạt động, phát hiện lỗi và xác định khi nào ứng dụng sẵn sàng nhận request.|
Logging | print() trực tiếp ra console, có thể log cả API key | Structured JSON Logging bằng logging | Dễ tìm kiếm, phân tích và giám sát log; tránh làm lộ thông tin nhạy cảm.|
Shutdown | Tắt ứng dụng đột ngột, không quản lý vòng đời | Graceful Shutdown thông qua lifespan và xử lý SIGTERM | Cho phép hoàn thành request đang xử lý và giải phóng tài nguyên trước khi ứng dụng dừng.|


## Part 2: Docker

### Exercise 2.1: Dockerfile questions
1. Base image là gì? 
2. Working directory là gì?
3. Tại sao COPY requirements.txt trước?
4. CMD vs ENTRYPOINT khác nhau thế nào?
1. Base image: `python:3.11` – cung cấp môi trường Python phiên bản 3.11 cho container.
2. Working directory: `/app` – thư mục làm việc bên trong container.
3. COPY requirements.txt trước: Tận dụng Docker Layer Cache, tránh cài lại dependencies khi chỉ thay đổi source code.
4. CMD vs ENTRYPOINT: `CMD ["python", "app.py"]` là lệnh mặc định có thể ghi đè, còn ENTRYPOINT cố định chương trình chính khi chạy container.
...

### Exercise 2.3: Image size comparison
- Develop: 426 MB
- Production: 57.4 MB
- Difference: 13.5%

## Part 3: Cloud Deployment

### Exercise 3.2: Render deployment
- URL: https://ai-agent-ohu0.onrender.com
- Screenshot: ![Ảnh render](./screenshots/render%20ex3.2.png)

## Part 4: API Security

### Exercise 4.1-4.3: Test results
[Paste your test outputs]
- Ex 4.1
    - Test không có API Key: Missing API key. Include header: X-API-Key: <your-key>
    - Test API Key sai: Invalid API key.
    - Kết quả: API từ chối request khi thiếu hoặc sai API Key, xác nhận cơ chế xác thực hoạt động.

- Ex 4.2
    - JWT Authentication: Lấy access token thành công qua /auth/token.
    - Protected API: Gửi JWT Bearer Token đến /ask thành công.
    - Test question: what is docker?
    - Result: API trả về câu trả lời: Container là cách đóng gói app để chạy mọi nơi. Build once, run anywhere!

- Ex 4.3
    - Gửi liên tục 20 requests đến endpoint /ask.
    - 10 requests đầu: Được xử lý thành công.
    - Từ request 11–20: Bị từ chối với lỗi Rate limit exceeded. Trả lỗi 429 Too Many Requests
    - Giới hạn: 10 requests / 60 giây.
    - Thời gian chờ để thử lại: 59 giây.

### Exercise 4.4: Cost guard implementation
[Explain your approach]
Sử dụng Redis để lưu chi phí theo từng user và tháng (`budget:{user_id}:{month}`). Kiểm tra tổng chi phí hiện tại cộng chi phí ước tính không vượt quá $10/tháng. Nếu vượt, trả về `False`; nếu còn budget, cập nhật chi phí bằng `incrbyfloat()` và đặt TTL 32 ngày để tự động xóa dữ liệu cũ.

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
[Your explanations and test results]

- Ex 5.1:
    - `/health`: Kiểm tra agent còn hoạt động, trả về uptime, version, environment và trạng thái memory.
    - `/ready`: Kiểm tra agent đã sẵn sàng nhận request chưa, trả về HTTP 503 nếu chưa ready.
    - Sử dụng biến `_is_ready` để quản lý trạng thái khởi động và shutdown.

- Ex 5.2:
    - Đăng ký handler cho `SIGTERM` và `SIGINT`.
    - Theo dõi số request đang xử lý bằng `_in_flight_requests`.
    - Khi shutdown, ngừng nhận request mới và chờ request hiện tại hoàn thành tối đa 30 giây.
    - Sử dụng `lifespan` và `timeout_graceful_shutdown=30` của Uvicorn.

- Ex 5.3
    - Thiết kế API theo hướng Stateless, không lưu trạng thái phiên làm việc trực tiếp trên từng instance.
    - Sử dụng **Redis** để lưu trữ lịch sử hội thoại theo `session_id`, giúp các instance có thể truy cập chung dữ liệu.
    - Thiết lập TTL 3600 giây cho session để tự động hết hạn sau một khoảng thời gian.
    - API hỗ trợ tạo session mới, tiếp tục hội thoại, xem lịch sử và xóa session.

- Ex 5.4
    - Triển khai nhiều instance API để xử lý request đồng thời.
    - Sử dụng Nginx làm Load Balancer, phân phối request đến các instance backend.
    - Sử dụng Redis làm kho lưu trữ session dùng chung, giúp request có thể được xử lý bởi bất kỳ instance nào mà không mất lịch sử hội thoại.
    - Theo dõi instance xử lý request thông qua trường `served_by`.

- Ex 5.5
    - Gửi nhiều request hội thoại với cùng một `session_id` để kiểm tra khả năng duy trì lịch sử.
    - Gửi các request liên tiếp qua hệ thống có nhiều instance.


## Part 6:
```
================================================================
  Production Readiness Check — Day 14 Lab
================================================================

✅ 1. Dockerfile (multi-stage, < 500 MB)
     ✅ Dockerfile tồn tại
     ✅ requirements.txt tồn tại
     ✅ Multi-stage build (≥ 2 lệnh FROM)
     ✅ Base image gọn (slim / alpine / distroless) — stage cuối dùng python:3.11-slim
     ✅ Chạy bằng user non-root
     ✅ Có HEALTHCHECK
     ✅ Docker: build image thành công — 4s
     ✅ Docker: image < 500 MB — 63 MB
     ✅ Docker: container chạy được, GET /health → 200

✅ 2. docker-compose.yml (agent + redis)
     ✅ docker-compose.yml tồn tại
     ✅ Có service agent (build từ Dockerfile) + redis — services: agent, redis — đọc bằng docker compose config
     ✅ Service agent kết nối redis (REDIS_URL + depends_on)

✅ 3. .dockerignore
     ✅ .dockerignore tồn tại và có nội dung
     ✅ .dockerignore loại trừ .env (secrets)
     ✅ .dockerignore loại trừ __pycache__, venv

✅ 4. Health check endpoint (GET /health)
     ✅ Code có route /health
     ✅ Khi chạy: GET /health → 200 — uvicorn --workers 2

✅ 5. Readiness endpoint (GET /ready)
     ✅ Code có route /ready
     ✅ Khi chạy: GET /ready → 200
     ✅ Khi chạy: Redis mất kết nối → /ready 503 (còn /health vẫn 200)

✅ 6. API Key authentication
     ✅ Code đọc header X-API-Key
     ✅ Khi chạy: thiếu / sai API key → 401
     ✅ Khi chạy: API key đúng → 200

✅ 7. Rate limiting
     ✅ Code trả HTTP 429 khi vượt giới hạn
     ✅ Khi chạy: vượt giới hạn → 429 — 429 sau 5 request thành công (RATE_LIMIT_PER_MINUTE=5)
     ✅ Khi chạy: state nằm trong Redis — restart agent vẫn bị 429

✅ 8. Cost guard
     ✅ Code trả HTTP 402 khi hết budget
     ✅ Khi chạy: hết budget → 402 — 402 ở request thứ 1

✅ 9. Config từ environment variables
     ✅ app/config.py đọc biến môi trường
     ✅ .env.example liệt kê đủ biến cấu hình
     ✅ .env nằm trong .gitignore
     ✅ Không hard-code secret trong code
     ✅ Khi chạy: agent dùng AGENT_API_KEY và RATE_LIMIT_PER_MINUTE từ env

✅ 10. Structured logging
     ✅ Code ghi log dạng JSON
     ✅ Khi chạy: mọi dòng log của app là JSON hợp lệ — 17 dòng JSON

⚠️  11. Graceful shutdown
     ✅ Code xử lý SIGTERM / lifespan shutdown
     ⚠️  Khi chạy: SIGTERM lúc đang có request → request vẫn 200, process tự thoát — chưa kiểm tra được — Windows không gửi được SIGTERM (phần Docker sẽ kiểm tra)
     ✅ Docker: `docker stop` tắt êm (exit code 0, < 10s) — exit code 0, 1.0s

✅ 12. Public URL ready (Railway / Render config)
     ✅ Có railway.toml hoặc render.yaml (không chỉ toàn comment)
     ✅ railway.toml: builder + healthcheckPath = "/health"
     ✅ App lắng nghe theo biến PORT do platform cấp

================================================================
  📋 Checklist Deliverable
     ✅ Dockerfile (multi-stage, < 500 MB)
     ✅ docker-compose.yml (agent + redis)
     ✅ .dockerignore
     ✅ Health check endpoint (GET /health)
     ✅ Readiness endpoint (GET /ready)
     ✅ API Key authentication
     ✅ Rate limiting
     ✅ Cost guard
     ✅ Config từ environment variables
     ✅ Structured logging
     ✅  Graceful shutdown
     ✅ Public URL ready (Railway / Render config)
----------------------------------------------------------------
  Result: 12/12 tiêu chí đạt · 40/40 checks passed
================================================================
```