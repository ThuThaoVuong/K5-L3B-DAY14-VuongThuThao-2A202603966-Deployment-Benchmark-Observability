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

### Exercise 3.1: Railway deployment
- URL: https://your-app.railway.app
- Screenshot: [Link to screenshot in repo]

## Part 4: API Security

### Exercise 4.1-4.3: Test results
[Paste your test outputs]

### Exercise 4.4: Cost guard implementation
[Explain your approach]

## Part 5: Scaling & Reliability

### Exercise 5.1-5.5: Implementation notes
[Your explanations and test results]