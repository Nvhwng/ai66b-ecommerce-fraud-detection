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
        print(f"Connection Failed! Error: {e}")
        return

    with driver.session() as session:
        print("🧹 Cleaning up old data...")
        session.run("MATCH (n) DETACH DELETE n")

        print("Setting up Constraints...")
        constraints = [
            "CREATE CONSTRAINT store_id IF NOT EXISTS FOR (s:Store) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT cust_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT ip_addr IF NOT EXISTS FOR (i:IP) REQUIRE i.address IS UNIQUE"
        ]
        for cmd in constraints:
            session.run(cmd)

        print("💉 Injecting Fraud Scenarios...")
        master_query = """
        // 1. CIRCULAR TRADING (S01-S02-S03)
        CREATE (s1:Store {id: 'S01', name: 'TechZone Store', risk_level: 'High'})
        CREATE (s2:Store {id: 'S02', name: 'Beauty Queen', risk_level: 'High'})
        CREATE (s3:Store {id: 'S03', name: 'Home Mart', risk_level: 'High'})
        
        CREATE (c1:Customer {id: 'C01', name: 'Owner A'})
        CREATE (c2:Customer {id: 'C02', name: 'Owner B'})
        CREATE (c3:Customer {id: 'C03', name: 'Owner C'})
        
        CREATE (c1)-[:OWNS]->(s1), (c2)-[:OWNS]->(s2), (c3)-[:OWNS]->(s3)
        
        // Vòng lặp: C1 mua S2, C2 mua S3, C3 mua S1
        CREATE (c1)-[:PURCHASED {amount: 5000}]->(s2)
        CREATE (c2)-[:PURCHASED {amount: 5000}]->(s3)
        CREATE (c3)-[:PURCHASED {amount: 5000}]->(s1)

        // 2. CLONE FARM (S04)
        CREATE (s4:Store {id: 'S04', name: 'Flash Sale Shop', risk_level: 'Medium'})
        CREATE (ip:IP {address: '14.226.1.10'})
        CREATE (c4:Customer {id: 'C04', name: 'Clone_1'})
        CREATE (c5:Customer {id: 'C05', name: 'Clone_2'})
        
        CREATE (c4)-[:USED_IP]->(ip), (c5)-[:USED_IP]->(ip)
        CREATE (c4)-[:PURCHASED {amount: 100}]->(s4), (c5)-[:PURCHASED {amount: 100}]->(s4)

        // 3. NORMAL DATA
        CREATE (s5:Store {id: 'S05', name: 'Official Nike Store', risk_level: 'Low'})
        CREATE (c7:Customer {id: 'C07', name: 'Real Buyer'})
        CREATE (c7)-[:PURCHASED {amount: 300}]->(s5)
        """
        session.run(master_query)
        print("SUCCESS: Data seeded successfully!")

if __name__ == "__main__":
    try:
        run_seed()
    finally:
        db_manager.close()