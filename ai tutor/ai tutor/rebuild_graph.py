import chromadb, pickle, networkx as nx, re

# Node type colors matching the frontend graph/page.js NODE_TYPES
NODE_COLORS = {
    "chapter":    "#4A9FFF",  # blue
    "section":    "#F47B6E",  # red  (Topic)
    "concept":    "#7C5CFC",  # purple
    "definition": "#4CAF82",  # green (Term)
    "example":    "#4CAF82",  # green
    "question":   "#F9A825",  # amber
}

# Keywords that indicate a definition/term (specific named things)
TERM_KEYWORDS = [
    "scale", "tube", "bottle", "acid", "soda", "extinguisher",
    "carbonate", "hydrogen", "sodium", "bicarbonate",
]

# Keywords for concepts (abstract ideas, processes, reactions)
CONCEPT_KEYWORDS = [
    "reaction", "process", "behavior", "behaviour", "concentration",
    "formation", "effect", "occurrence", "change", "order", "uses",
]

# Keywords for topic/section (broad categories)
TOPIC_KEYWORDS = [
    "acidic", "alkaline", "neutral", "strongly", "weakly",
]

client = chromadb.PersistentClient(path="data/chroma_db")
col = client.get_collection("graph_concept_nodes")
result = col.get(include=["documents"])

g = nx.DiGraph()
concept_index = {}
name_index = {}

ids = result["ids"]
docs = result["documents"]

print(f"Processing {len(ids)} nodes from ChromaDB...\n")

for i, (doc_id, doc) in enumerate(zip(ids, docs)):
    text = doc or ""
    text_lower = text.lower()

    # Parse concept name and definition
    name_match = re.search(r"Concept:\s*(.+?)(?:\n|$)", text)
    def_match = re.search(r"Definition:\s*(.+?)(?:\n|$)", text)
    kw_match = re.search(r"Keywords:\s*(.+?)(?:\n|$)", text)
    
    label = name_match.group(1).strip() if name_match else doc_id
    definition = def_match.group(1).strip() if def_match else text[:200]
    keywords = [k.strip() for k in kw_match.group(1).split(",")] if kw_match else []
    label_lower = label.lower()

    # --- Classify node_type based on concept name ---
    # 1. Concepts — processes, reactions, scientific phenomena
    if any(kw in label_lower for kw in ["reaction", "occurrence", "formation", "change", "behavior", "behaviour", "effect"]):
        node_type = "concept"
    elif "scale" in label_lower or "concentration" in label_lower:
        node_type = "concept"
    # 2. Terms — lab equipment, chemical compounds
    elif any(kw in label_lower for kw in ["tube", "bottle", "extinguisher"]):
        node_type = "definition"
    elif any(kw in label_lower for kw in ["soda", "sodium", "acid", "carbonate"]):
        node_type = "definition"
    # 3. Topics — broad pH categories, uses, ordering
    elif any(kw in label_lower for kw in ["uses", "order"]):
        node_type = "section"
    elif any(kw in label_lower for kw in TOPIC_KEYWORDS):
        node_type = "section"
    else:
        node_type = "concept"       # Default

    color = NODE_COLORS.get(node_type, NODE_COLORS["concept"])

    node_data = {
        "type": "concept",
        "node_type": node_type,
        "name": label,
        "label": label,
        "definition": definition,
        "examples": [],
        "keywords": keywords,
        "source_text": text,
        "color": color,
    }
    g.add_node(doc_id, **node_data)
    concept_index[doc_id] = node_data
    name_index[label.lower()] = doc_id
    print(f"  [{i+1:2d}] {node_type:12s}  {color}  {label}")

# Create edges between related concepts
node_list = list(g.nodes)
for i in range(len(node_list)):
    for j in range(i + 1, len(node_list)):
        text_i = g.nodes[node_list[i]].get("source_text", "").lower()
        text_j = g.nodes[node_list[j]].get("source_text", "").lower()
        name_i = g.nodes[node_list[i]].get("name", "").lower()
        name_j = g.nodes[node_list[j]].get("name", "").lower()

        if name_j in text_i or name_i in text_j:
            g.add_edge(node_list[i], node_list[j], type="related_to", label="related_to")

# Save
with open("data/knowledge_graph.pkl", "wb") as f:
    pickle.dump({"graph": g, "concept_index": concept_index, "name_index": name_index}, f)

# Print summary
types = {}
for _, d in g.nodes(data=True):
    t = d.get("node_type", "concept")
    types[t] = types.get(t, 0) + 1

print(f"\nRebuilt: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
print("Type breakdown:")
for t, c in sorted(types.items()):
    print(f"  {t}: {c}")
print("Saved to data/knowledge_graph.pkl")
