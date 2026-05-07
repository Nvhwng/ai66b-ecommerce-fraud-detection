from fastapi import FastAPI
from pydantic import BaseModel
from database import db_manager
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- Models ---
class StoreModel(BaseModel):
    id: str
    name: str
    owner_id: str
    ip: str = "127.0.0.1"
    device: str = "Unknown_Device"

class PurchaseModel(BaseModel):
    buyer_id: str
    store_id: str
    ip: str = None  
    device: str = None 

# --- Phân tích đồ thị và phát hiện gian lận ---
@app.get("/api/graph")
def get_graph(search_id: str = None):
    driver = db_manager.connect()
    with driver.session() as session:
        
        # 1. Thuật toán quét hành vi bất thường
        cycle_q = "MATCH (n) WHERE (n)-[:PURCHASED|OWNS*3..8]-(n) RETURN DISTINCT n.id as id"
        cycle_ids = {str(r["id"]) for r in session.run(cycle_q)}

        self_buying_q = """
        MATCH (c:Customer)-[:PURCHASED]->(s:Store)
        WHERE (c)-[:USED_IP|USED_DEVICE|OWNS*1..2]-(s)
        RETURN DISTINCT c.id as cid, s.id as sid
        """
        self_buying_res = session.run(self_buying_q)
        self_buying_ids = set()
        for r in self_buying_res:
            self_buying_ids.update([str(r['cid']), str(r['sid'])])

        community_q = """
        MATCH (n)-[:USED_IP|USED_DEVICE]->()<-[:USED_IP|USED_DEVICE]-(m)
        WHERE n <> m AND NOT (n:Customer AND m:Store AND (n)-[:PURCHASED]->(m))
        RETURN DISTINCT n.id as id
        """
        community_ids = {str(r["id"]) for r in session.run(community_q)}

        # 2. Truy vấn dữ liệu hiển thị
        query = "MATCH (n)-[r*1..2]-(m) WHERE n.id = $sid RETURN n, r, m LIMIT 300" if search_id \
                else "MATCH (n)-[r]-(m) RETURN n, r, m LIMIT 600"
        results = session.run(query, sid=search_id) if search_id else session.run(query)
        
        # 3. Xử lý Node và Edge cho Frontend
        nodes, edges, node_ids = [], [], set()
        for record in results:
            for key in ['n', 'm']:
                node = record[key]
                e_id = node.element_id
                if e_id not in node_ids:
                    label = list(node.labels)[0]
                    orig_id = str(node.get('id', ""))
                    
                    color, status = "#0a84ff", "Normal"
                    if label == "Store": color = "#32d74b"
                    elif label in ["IP", "Device"]: color = "#8e8e93"
                    
                    if orig_id in cycle_ids: color, status = "#ff453a", "Circular Fraud"
                    elif orig_id in self_buying_ids: color, status = "#af52de", "Self-Buying"
                    elif orig_id in community_ids: color, status = "#ff9f0a", "Community Suspect"
                        
                    nodes.append({"id": e_id, "label": f"{label}:{orig_id}", "color": color, "orig_id": orig_id, "status": status})
                    node_ids.add(e_id)
            
            rel_data = record['r']
            rels = rel_data if isinstance(rel_data, list) else [rel_data]
            for r in rels:
                edges.append({"from": r.start_node.element_id, "to": r.end_node.element_id, "label": r.type})
                
        return {"nodes": nodes, "edges": edges}

# --- Nghiệp vụ Database ---
@app.post("/api/add-store")
def add_store(store: StoreModel):
    driver = db_manager.connect()
    with driver.session() as session:
        query = """
        MERGE (c:Customer {id: $owner_id}) SET c.name = 'Owner of ' + $id
        MERGE (s:Store {id: $id}) SET s.name = $name
        MERGE (ip:IP {id: $ip})
        MERGE (dev:Device {id: $device})
        MERGE (c)-[:OWNS]->(s) MERGE (c)-[:USED_IP]->(ip) MERGE (c)-[:USED_DEVICE]->(dev)
        MERGE (s)-[:USED_IP]->(ip) MERGE (s)-[:USED_DEVICE]->(dev)
        """
        session.run(query, id=store.id, name=store.name, owner_id=store.owner_id, ip=store.ip, device=store.device)
        return {"status": "success"}

@app.post("/api/purchase")
def record_purchase(data: PurchaseModel):
    driver = db_manager.connect()
    with driver.session() as session:
        query = """
        MATCH (c:Customer {id: $bid}) MATCH (s:Store {id: $sid})
        MERGE (c)-[r:PURCHASED]->(s) SET r.timestamp = datetime()
        WITH c
        FOREACH (_ IN CASE WHEN $ip IS NOT NULL THEN [1] ELSE [] END |
            MERGE (new_ip:IP {id: $ip}) MERGE (c)-[:USED_IP]->(new_ip))
        FOREACH (_ IN CASE WHEN $dev IS NOT NULL THEN [1] ELSE [] END |
            MERGE (new_dev:Device {id: $dev}) MERGE (c)-[:USED_DEVICE]->(new_dev))
        """
        session.run(query, bid=data.buyer_id, sid=data.store_id, ip=data.ip, dev=data.device)
        return {"status": "Success"}

# --- Tiện ích ---
@app.get("/api/suggestions")
def get_suggestions(label: str = None):
    driver = db_manager.connect()
    with driver.session() as session:
        query = f"MATCH (n:{label}) RETURN DISTINCT n.id as id" if label \
                else "MATCH (n) RETURN DISTINCT n.id as id"
        return [str(r["id"]) for r in session.run(query) if r["id"]]
@app.delete("/api/delete-node/{node_id}")
def delete_node(node_id: str):
    driver = db_manager.connect()
    with driver.session() as session:
        session.run("MATCH (n {id: $id}) DETACH DELETE n", id=node_id)
        return {"status": "deleted"}

@app.delete("/api/delete-relationship")
def delete_relationship(from_id: str, to_id: str, rel_type: str):
    driver = db_manager.connect()
    with driver.session() as session:
        session.run("""
            MATCH (a {id: $from_id})-[r]->(b {id: $to_id})
            WHERE type(r) = $rel_type
            DELETE r
        """, from_id=from_id, to_id=to_id, rel_type=rel_type)
        return {"status": "deleted"}