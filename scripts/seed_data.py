import sys
import os

# Đảm bảo Python tìm thấy file database.py ở thư mục cha
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import db_manager

def run_seed():
    print("Starting the Seeding process...")
    try:
        driver = db_manager.connect()
    except Exception as e:
        print(f" Connection Failed! Error: {e}")
        return

    with driver.session() as session:
        print("Cleaning up old data...")
        session.run("MATCH (n) DETACH DELETE n")

        print("Setting up Constraints...")
        # Thêm constraint cho Device để đồng bộ với logic mới
        constraints = [
            "CREATE CONSTRAINT store_id IF NOT EXISTS FOR (s:Store) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT cust_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT ip_addr IF NOT EXISTS FOR (i:IP) REQUIRE i.id IS UNIQUE",
            "CREATE CONSTRAINT dev_id IF NOT EXISTS FOR (d:Device) REQUIRE d.id IS UNIQUE"
        ]
        for cmd in constraints:
            try:
                session.run(cmd)
            except:
                pass

        print("Injecting Fraud Scenarios...")
        master_query = """
        // --- 1. CIRCULAR TRADING (Vòng lặp khép kín - Nodes Màu Đỏ) ---
        CREATE (s1:Store {id: 'S01', name: 'TechZone Store'})
        CREATE (s2:Store {id: 'S02', name: 'Beauty Queen'})
        CREATE (s3:Store {id: 'S03', name: 'Home Mart'})
        
        CREATE (c1:Customer {id: 'C01', name: 'Owner A'})
        CREATE (c2:Customer {id: 'C02', name: 'Owner B'})
        CREATE (c3:Customer {id: 'C03', name: 'Owner C'})
        
        CREATE (c1)-[:OWNS]->(s1), (c2)-[:OWNS]->(s2), (c3)-[:OWNS]->(s3)
        CREATE (c1)-[:PURCHASED {amount: 5000}]->(s2)
        CREATE (c2)-[:PURCHASED {amount: 5000}]->(s3)
        CREATE (c3)-[:PURCHASED {amount: 5000}]->(s1)

        // --- 2. SELF-BUYING (Chủ shop tự mua hàng - Nodes Màu Tím) ---
        // C04 sở hữu S04 và dùng chính Device/IP đó để mua hàng của mình
        CREATE (s4:Store {id: 'S04', name: 'Personal Shop'})
        CREATE (c4:Customer {id: 'C04', name: 'Solo Seller'})
        CREATE (dev1:Device {id: 'DEV-IPHONE-X'})
        CREATE (ip1:IP {id: '192.168.1.5'})
        
        CREATE (c4)-[:OWNS]->(s4)
        CREATE (c4)-[:USED_DEVICE]->(dev1), (s4)-[:USED_DEVICE]->(dev1)
        CREATE (c4)-[:USED_IP]->(ip1), (s4)-[:USED_IP]->(ip1)
        CREATE (c4)-[:PURCHASED {amount: 1500}]->(s4)

        // --- 3. CLONE FARM / COMMUNITY (Chung hạ tầng - Nodes Màu Cam) ---
        // Một nhóm khách hàng dùng chung IP/Device để tập trung mua ở Store S05
        CREATE (s5:Store {id: 'S05', name: 'Flash Sale Center'})
        CREATE (ip2:IP {id: '14.226.1.10'})
        CREATE (dev2:Device {id: 'PC-FARM-01'})
        CREATE (c5:Customer {id: 'C05', name: 'Clone_1'})
        CREATE (c6:Customer {id: 'C06', name: 'Clone_2'})
        CREATE (c7:Customer {id: 'C07', name: 'Clone_3'})
        
        CREATE (c5)-[:USED_IP]->(ip2), (c6)-[:USED_IP]->(ip2), (c7)-[:USED_IP]->(ip2)
        CREATE (c5)-[:USED_DEVICE]->(dev2), (c6)-[:USED_DEVICE]->(dev2), (c7)-[:USED_DEVICE]->(dev2)
        CREATE (c5)-[:PURCHASED]->(s5), (c6)-[:PURCHASED]->(s5), (c7)-[:PURCHASED]->(s5)

        // --- 4. DATA MỞ RỘNG (Nhiều Store/Customer hơn để làm dày đồ thị) ---
        CREATE (s6:Store {id: 'S06', name: 'Fashion Hub'})
        CREATE (s7:Store {id: 'S07', name: 'Gadget World'})
        CREATE (s8:Store {id: 'S08', name: 'Book Store'})
        
        CREATE (c8:Customer {id: 'C08', name: 'Casual Buyer A'})
        CREATE (c9:Customer {id: 'C09', name: 'Casual Buyer B'})
        CREATE (c10:Customer {id: 'C10', name: 'Casual Buyer C'})
        
        CREATE (c8)-[:PURCHASED]->(s6), (c8)-[:PURCHASED]->(s7)
        CREATE (c9)-[:PURCHASED]->(s7), (c9)-[:PURCHASED]->(s8)
        CREATE (c10)-[:PURCHASED]->(s1) // Khách bình thường mua ở Store thuộc vòng lặp
        
        // Tạo thêm liên kết IP cho khách bình thường
        CREATE (ip3:IP {id: '172.16.0.1'})
        CREATE (c8)-[:USED_IP]->(ip3), (c9)-[:USED_IP]->(ip3)
        """
        session.run(master_query)
        print("SUCCESS: Data seeded successfully with 8 Stores and 10 Customers!")

if __name__ == "__main__":
    try:
        run_seed()
    finally:
        db_manager.close()