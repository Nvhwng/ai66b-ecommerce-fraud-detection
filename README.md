# ai66b-ecommerce-fraud-detection\
# Quick Start

### 1. Requirements
* Neo4j Desktop (Running) 
* Python 3.10+

### 2. Installation
```bash
pip install fastapi uvicorn neo4j pydantic # chạy terminal
3. Database Setup
Cấu hình thông tin kết nối trong database.py:

URI,User,Password: #để trong file .env hoặc xem trong database.py

Chạy script khởi tạo dữ liệu mẫu:
chạy file seed_data.py

4. Running the App
Khởi chạy Backend Server:
uvicorn main:app --reload #chạy terminal

- Mở giao diện:
Truy cập trực tiếp file index.html bằng trình duyệt. # chạy trong terminal lệnh: open -a "Google Chrome" index.html

5. Test Scenarios
Search S01: Hiển thị chu trình giao dịch ảo (Nodes màu đỏ).
Search C04: Hiển thị cụm tài khoản chung IP (Nodes màu cam).