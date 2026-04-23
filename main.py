from fastapi import FastAPI
from pydantic import BaseModel
from database import db_manager
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class StoreModel(BaseModel):
    id: str
    name: str
    owner_id: str
    ip: str = "127.0.0.1"
    device: str = "Unknown_Device"

@app.get("/api/graph")
def get_graph(search_id: str = None):
    driver = db_manager.connect()
    with driver.session() as session:
        # THUẬT TOÁN 1: Tìm chu trình mua bán ảo (Circular Trading)
        # Quét đường đi từ 3-8 bước qua cả OWNS và PURCHASED
        cycle_q = """
        MATCH path = (n)-[:PURCHASED|OWNS*3..8]-(n)
        UNWIND nodes(path) as nodes
        RETURN DISTINCT nodes.id as id
        """
        cycle_ids = {str(r["id"]) for r in session.run(cycle_q)}

        # THUẬT TOÁN 2: Phát hiện "Chủ shop tự mua hàng" (Self-Buying)
        # Tìm Customer mua hàng tại Store mà mình sở hữu hoặc dùng chung IP/Device
        self_buying_q = """
        MATCH (c:Customer)-[:PURCHASED]->(s:Store)
        MATCH (c)-[:USED_IP|USED_DEVICE|OWNS]-(infra)-[:USED_IP|USED_DEVICE|OWNS]-(s)
        RETURN DISTINCT c.id as cid, s.id as sid
        """
        self_buying_res = session.run(self_buying_q)
        self_buying_ids = set()
        for r in self_buying_res:
            self_buying_ids.add(str(r['cid']))
            self_buying_ids.add(str(r['sid']))

        # THUẬT TOÁN 3: Community Detection (Dùng chung hạ tầng)
        community_q = """
        MATCH (c1:Customer)-[:USED_IP|USED_DEVICE]->(infra)<-[:USED_IP|USED_DEVICE]-(c2:Customer)
        WHERE c1 <> c2
        RETURN DISTINCT c1.id as id
        """
        community_ids = {str(r["id"]) for r in session.run(community_q)}

        # LẤY DỮ LIỆU ĐỒ THỊ
        if search_id:
            query = "MATCH (n)-[r*1..2]-(m) WHERE n.id = $sid RETURN n, r, m LIMIT 300"
            results = session.run(query, sid=search_id)
        else:
            results = session.run("MATCH (n)-[r]-(m) RETURN n, r, m LIMIT 600")
        
        nodes, edges, node_ids = [], [], set()

        for record in results:
            for node in [record['n'], record['m']]:
                e_id = node.element_id
                if e_id not in node_ids:
                    label = list(node.labels)[0]
                    orig_id = str(node.get('id') or node.get('address') or "")
                    
                    # Phân cấp màu sắc (Ưu tiên mức độ nguy hiểm)
                    color = "#0a84ff" # Customer
                    status = "Normal"
                    
                    if label == "Store": color = "#32d74b"
                    if label in ["IP", "Device"]: color = "#8e8e93"

                    if orig_id in cycle_ids:
                        color = "#ff453a" # ĐỎ: Chu trình ảo
                        status = "Circular Fraud"
                    elif orig_id in self_buying_ids:
                        color = "#af52de" # TÍM: Tự mua hàng
                        status = "Self-Buying"
                    elif orig_id in community_ids:
                        color = "#ff9f0a" # CAM: Chung thiết bị/IP
                        status = "Community Suspect"

                    nodes.append({
                        "id": e_id, "label": f"{label}:{orig_id}", 
                        "color": color, "orig_id": orig_id, "status": status
                    })
                    node_ids.add(e_id)
            
            rel = record['r']
            rels = rel if isinstance(rel, list) else [rel]
            for r in rels:
                edges.append({"from": r.start_node.element_id, "to": r.end_node.element_id, "label": r.type})
            
        return {"nodes": nodes, "edges": edges}
@app.post("/api/add-store")
def add_store(store: StoreModel):
    driver = db_manager.connect()
    with driver.session() as session:
        query = """
        MERGE (c:Customer {id: $owner_id})
        SET c.name = 'Owner of ' + $id
        MERGE (s:Store {id: $id})
        SET s.name = $name
        MERGE (ip:IP {id: $ip})
        MERGE (dev:Device {id: $device})
        
        // Tạo các mối quan hệ thực thể
        MERGE (c)-[:OWNS]->(s)
        MERGE (c)-[:USED_IP]->(ip)
        MERGE (c)-[:USED_DEVICE]->(dev)
        
        // Tùy chọn: Nếu muốn Store mới cũng dùng chung hạ tầng này
        MERGE (s)-[:USED_IP]->(ip)
        MERGE (s)-[:USED_DEVICE]->(dev)
        """
        session.run(query, 
            id=store.id, 
            name=store.name, 
            owner_id=store.owner_id, 
            ip=store.ip, 
            device=store.device
        )
        return {"status": "success", "added_id": store.id}
class PurchaseModel(BaseModel):
    buyer_id: str
    store_id: str

class PurchaseModel(BaseModel):
    buyer_id: str
    store_id: str
    ip: str = None  
    device: str = None 

@app.post("/api/purchase")
def record_purchase(data: PurchaseModel):
    driver = db_manager.connect()
    with driver.session() as session:
        # 1. Tạo quan hệ mua bán
        # 2. Nếu có IP/Device mới, nối thêm dây vào Customer đó luôn
        query = """
        MATCH (c:Customer {id: $bid})
        MATCH (s:Store {id: $sid})
        MERGE (c)-[r:PURCHASED]->(s)
        SET r.timestamp = datetime()
        
        WITH c
        FOREACH (_ IN CASE WHEN $ip IS NOT NULL THEN [1] ELSE [] END |
            MERGE (new_ip:IP {id: $ip})
            MERGE (c)-[:USED_IP]->(new_ip)
        )
        FOREACH (_ IN CASE WHEN $dev IS NOT NULL THEN [1] ELSE [] END |
            MERGE (new_dev:Device {id: $dev})
            MERGE (c)-[:USED_DEVICE]->(new_dev)
        )
        """
        session.run(query, bid=data.buyer_id, sid=data.store_id, ip=data.ip, dev=data.device)
        return {"status": "Success"}
@app.get("/api/suggestions")
def get_suggestions():
    driver = db_manager.connect()
    with driver.session() as session:
        # Lấy tất cả ID của Store, Customer, IP, Device
        query = "MATCH (n) RETURN DISTINCT n.id as id"
        results = session.run(query)
        return [str(r["id"]) for r in results if r["id"]]