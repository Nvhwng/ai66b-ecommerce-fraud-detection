AI66B E-Commerce Fraud Detection
Hệ thống phát hiện gian lận giao dịch bằng Graph Database.

1. Cài đặt thư viện
Chạy lệnh sau trong terminal:

Bash
pip install fastapi uvicorn neo4j pydantic python-dotenv
2. Cấu hình Database
Tạo file .env tại thư mục gốc và nhập thông tin sau:

Plaintext
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=điền_mật_khẩu_của_bạn
3. Khởi tạo dữ liệu mẫu
Chạy script để nạp dữ liệu vào Neo4j:

Bash
python scripts/seed_data.py
4. Khởi chạy ứng dụng
Chạy Backend:

Bash
python -m uvicorn main:app --reload
Mở Giao diện:
Mở trực tiếp file index.html bằng trình duyệt Chrome hoặc Edge.

5. Kịch bản kiểm thử
Nhập các ID sau vào ô Search để kiểm tra:

S01: Gian lận vòng tròn (Màu đỏ).

C01: Chủ shop tự mua hàng (Màu tím).

C04: Dùng chung IP/Thiết bị (Màu cam).

Lưu ý: File .env đã được chặn bởi .gitignore để bảo mật mật khẩu cá nhân.