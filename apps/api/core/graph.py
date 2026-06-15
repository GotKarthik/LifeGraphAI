from sqlalchemy.orm import Session
from models.memory import MemoryNode, MemoryEdge, StructuredMemory
import uuid

def process_memory_graph(db: Session, structured_memory: StructuredMemory):
    entities_list = structured_memory.entities.get("entities", []) if isinstance(structured_memory.entities, dict) else []
    topics_list = structured_memory.entities.get("topics", []) if isinstance(structured_memory.entities, dict) else []
    
    nodes = set(entities_list + topics_list)
    db_nodes = {}
    
    for name in nodes:
        node = db.query(MemoryNode).filter(
            MemoryNode.user_id == structured_memory.user_id,
            MemoryNode.label == name
        ).first()
        
        if not node:
            node_type = "entity" if name in entities_list else "topic"
            node = MemoryNode(
                user_id=structured_memory.user_id,
                label=name,
                node_type=node_type
            )
            db.add(node)
            db.commit()
            db.refresh(node)
            
        db_nodes[name] = node
        
    node_names = list(nodes)
    for i in range(len(node_names)):
        for j in range(i + 1, len(node_names)):
            n1 = db_nodes[node_names[i]]
            n2 = db_nodes[node_names[j]]
            
            id1, id2 = sorted([str(n1.id), str(n2.id)])
            
            edge = db.query(MemoryEdge).filter(
                MemoryEdge.source_node_id == id1,
                MemoryEdge.target_node_id == id2
            ).first()
            if not edge:
                edge = MemoryEdge(
                    user_id=structured_memory.user_id,
                    source_node_id=id1,
                    target_node_id=id2,
                    relationship_type="co-occurs",
                    weight=1
                )
                db.add(edge)
            else:
                edge.weight += 1
                
            db.commit()
            
def get_user_graph(db: Session, user_id: str):
    nodes = db.query(MemoryNode).filter(MemoryNode.user_id == user_id).all()
    
    node_ids = [str(n.id) for n in nodes]
    edges = db.query(MemoryEdge).filter(
        MemoryEdge.source_node_id.in_(node_ids) | MemoryEdge.target_node_id.in_(node_ids)
    ).all()
    
    return {
        "nodes": [{"id": str(n.id), "name": n.label, "group": n.node_type} for n in nodes],
        "links": [{"source": str(e.source_node_id), "target": str(e.target_node_id), "weight": e.weight} for e in edges]
    }
