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
    ip: str = "127.0.0.1" # Mặc định cho môi trường Mac
    device: str = "Unknown_Device"

@app.get("/api/graph")
def get_graph(search_id: str = None):
    driver = db_manager.connect()
    with driver.session() as session:
        # LOGIC 1: PHÁT HIỆN VÒNG LẶP GIAO DỊCH (Sửa lại cực kỳ quan trọng)
        # Chúng ta tìm vòng lặp đi qua cả quan hệ sở hữu (OWNS) và mua hàng (PURCHASED)
        # Hướng mũi tên có thể khác nhau nên dùng (-) thay vì (->) để quét toàn bộ liên kết
        cycle_q = """
        MATCH path = (n)-[:PURCHASED|OWNS*3..8]-(n)
        UNWIND nodes(path) as nodes
        RETURN DISTINCT nodes.id as id
        """
        # Lưu ý: Dùng dấu gạch ngang (-) thay vì (->) giúp tìm vòng lặp bất kể hướng mũi tên
        results_cycle = session.run(cycle_q)
        cycle_ids = {str(r["id"]) for r in results_cycle}

        # LOGIC 2: Community Detection (Giữ nguyên vì đã chuẩn)
        community_q = """
        MATCH (c1:Customer)-[:USED_IP|USED_DEVICE]->(infra)<-[:USED_IP|USED_DEVICE]-(c2:Customer)
        WHERE c1 <> c2
        RETURN DISTINCT c1.id as id1, c2.id as id2
        """
        community_results = session.run(community_q)
        community_members = set()
        for r in community_results:
            community_members.add(str(r['id1']))
            community_members.add(str(r['id2']))

        # TRUY VẤN DỮ LIỆU ĐỂ VẼ ĐỒ THỊ
        if search_id:
            query = "MATCH (n)-[r*1..2]-(m) WHERE n.id = $sid RETURN n, r, m LIMIT 200"
            results = session.run(query, sid=search_id)
        else:
            results = session.run("MATCH (n)-[r]-(m) RETURN n, r, m LIMIT 500")
        
        nodes, edges, node_ids = [], [], set()

        for record in results:
            for node in [record['n'], record['m']]:
                e_id = node.element_id
                if e_id not in node_ids:
                    label = list(node.labels)[0]
                    # Lấy ID từ thuộc tính 'id' hoặc 'address' (cho IP)
                    orig_id = str(node.get('id') or node.get('address') or "")
                    
                    color = "#0a84ff" # Default: Customer
                    status = "Normal"
                    
                    if label == "Store": color = "#32d74b" 
                    if label in ["IP", "Device"]: color = "#8e8e93"
                    
                    # Highlight Fraud
                    if orig_id in cycle_ids:
                        color = "#ff453a" # Đỏ cho vòng lặp
                        status = "Circular Fraud"
                    elif orig_id in community_members:
                        color = "#ff9f0a" # Cam cho cộng đồng
                        status = "Community Suspect"

                    nodes.append({
                        "id": e_id, 
                        "label": f"{label}: {orig_id}", 
                        "color": color, 
                        "orig_id": orig_id,
                        "status": status
                    })
                    node_ids.add(e_id)
            
            # Xử lý quan hệ
            rel = record['r']
            rels = rel if isinstance(rel, list) else [rel]
            for r in rels:
                edges.append({
                    "from": r.start_node.element_id, 
                    "to": r.end_node.element_id, 
                    "label": r.type
                })
            
        return {"nodes": nodes, "edges": edges}

@app.post("/api/add-store")
def add_store(store: StoreModel):
    driver = db_manager.connect()
    with driver.session() as session:
        query = """
        MERGE (c:Customer {id: $owner_id})
        MERGE (s:Store {id: $id, name: $name})
        MERGE (ip:IP {id: $ip})
        MERGE (dev:Device {id: $device})
        MERGE (c)-[:OWNS]->(s)
        MERGE (c)-[:USED_IP]->(ip)
        MERGE (c)-[:USED_DEVICE]->(dev)
        """
        session.run(query, id=store.id, name=store.name, owner_id=store.owner_id, ip=store.ip, device=store.device)
        return {"status": "success"}

@app.delete("/api/delete-node/{node_id}")
def delete_node(node_id: str):
    driver = db_manager.connect()
    with driver.session() as session:
        session.run("MATCH (n) WHERE n.id = $id DETACH DELETE n", id=node_id)
        return {"status": "deleted"}