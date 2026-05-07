#  FraudCanvas: E-Commerce Fraud Detection
### **AI66B - Advanced Database Project | NEU**

Hệ thống phát hiện gian lận thương mại điện tử thời gian thực dựa trên công nghệ **Graph Database (Neo4j)**.

---

##  Tính năng cốt lõi
*    **Circular Fraud Detection**: Tự động phát hiện các chuỗi giao dịch khép kín (độ sâu từ `3-8 bước`).
*    **Community Suspect Discovery**: Nhận diện các nhóm tài khoản dùng chung hạ tầng `IP` hoặc `Device`.
*    **Real-time Visualization**: Minh họa mạng lưới giao dịch trực quan với hệ thống **Color-Coding**.
*    **Quick Data Injection**: Thêm dữ liệu trực tiếp từ giao diện để kiểm tra giả thuyết tức thì.

---

##  Công nghệ sử dụng
*   **Database**: `Neo4j Cloud` (Graph Database)
*   **Backend**: `FastAPI` (Python), `Uvicorn`
*   **Frontend**: `Vis.js Network`, `Bootstrap 5`
*   **Security**: `Python-dotenv`, `Pydantic`

---

##  Hướng dẫn cài đặt

### 1. Cài đặt thư viện
Chạy lệnh sau trong terminal để cài đặt các phụ thuộc:
bash
pip install fastapi uvicorn neo4j pydantic python-dotenv

### 2. Cấu hình Database

Tạo file `.env` tại thư mục gốc và nhập thông tin kết nối từ Instance Neo4j của bạn:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=điền_mật_khẩu_của_bạn
```

>  **Lưu ý:** File `.env` đã được liệt kê trong `.gitignore` để đảm bảo mật khẩu cá nhân không bị đẩy lên GitHub.

---

##  Khởi chạy ứng dụng

**Bước 1 — Khởi tạo dữ liệu mẫu (Seeding)**

Nạp các kịch bản gian lận mô phỏng vào Graph DB:

```bash
python scripts/seed_data.py
```

**Bước 2 — Chạy Backend API**

```bash
python -m uvicorn main:app --reload
```

**Bước 3 — Mở Giao diện**

Mở trực tiếp file `index.html` bằng trình duyệt (Chrome, Edge hoặc Safari).

---

##  Kịch bản kiểm thử (Test Cases)

Sử dụng thanh **Search** trên giao diện để kiểm tra các Node đặc biệt sau:

| ID | Loại hình gian lận | Trạng thái hiển thị |
|:---:|---|---|
| `S01` | Circular Trading | 🔴 Màu Đỏ — High Risk |
| `C05` | Shared Infrastructure | 🟠 Màu Cam — Suspect |
| `S05` | Normal Transaction | 🔵 Màu Xanh — Safe |
