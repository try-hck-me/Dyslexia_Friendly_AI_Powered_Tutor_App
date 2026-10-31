from app.services.vector_store import get_document_count, query_documents
import textwrap

with open('chroma_out.txt', 'w', encoding='utf-8') as f:
    count = get_document_count()
    f.write(f'Total chunks in DB: {count}\n')
    
    f.write('\n--- Testing retrieval for "what is acid?" ---\n')
    results = query_documents('what is acid?', n_results=4)
    for i, chunk in enumerate(results):
        f.write(f"\nResult {i+1} (Source: {chunk.get('source')} | Distance: {chunk.get('distance')}):\n")
        text = chunk.get('text', '')
        f.write(textwrap.shorten(text, width=200, placeholder='...') + '\n')

