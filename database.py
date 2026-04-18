import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# 1. Load các biến môi trường từ file .env (URI, USER, PASSWORD)
load_dotenv()

class Neo4jManager:
    def __init__(self):
        # Lấy thông tin cấu hình từ .env
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.driver = None

    def connect(self):
        """Khởi tạo kết nối tới Neo4j Aura nếu chưa có"""
        if not self.driver:
            try:
                self.driver = GraphDatabase.driver(
                    self.uri, 
                    auth=(self.user, self.password)
                )
                # Kiểm tra kết nối ngay lập tức
                self.driver.verify_connectivity()
            except Exception as e:
                print(f"Lỗi kết nối Database: {e}")
                raise e
        return self.driver

    def close(self):
        """Đóng kết nối khi không sử dụng nữa"""
        if self.driver:
            self.driver.close()
            self.driver = None

# 2. Khởi tạo một đối tượng (instance) duy nhất để dùng chung cho toàn bộ ứng dụng
db_manager = Neo4jManager()