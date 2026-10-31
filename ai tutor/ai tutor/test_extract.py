import asyncio
from app.services.graph_rag.extractor import Extractor
from app.services.graph_rag.builder import build_knowledge_graph

chunks = [{"text": "Photosynthesis is the process by which green plants and some other organisms use sunlight to synthesize foods from carbon dioxide and water.", "source": "test.pdf", "chunk_index": 0}]

print("Extracting...")
e = Extractor()
re = e.extract_all(chunks)
print("Errors:", e.errors)
print("Results:", re)
print("Building...")
kg = build_knowledge_graph(re)
print("Concepts mapped:", len(kg.get_all_concepts()))
