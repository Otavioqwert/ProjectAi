from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import os
import sqlite3
from tools.rbm_indexer import RBMIndexer

# Inicialização do App
app = FastAPI(title="ProjectAI Backend", description="API para Enxame de Agentes e Memória RBM")

# Instância do Indexador RBM
rbm_indexer = RBMIndexer(db_path="memory.db")

# Modelos Pydantic
class TextCompressRequest(BaseModel):
    text: str
    source: Optional[str] = "user_input"

class MemorySearchRequest(BaseModel):
    query: str

class TripletResponse(BaseModel):
    id: int
    subject: str
    predicate: str
    object: str
    source_text: Optional[str]

# Endpoints
@app.get("/")
def read_root():
    return {"status": "online", "message": "ProjectAI Backend Rodando"}

@app.post("/memory/compress")
def compress_memory(request: TextCompressRequest):
    """Comprime texto em tripletos RBM e salva no banco."""
    try:
        count = rbm_indexer.index_text(request.text, request.source)
        return {"status": "success", "triplets_added": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/memory/search")
def search_memory(request: MemorySearchRequest):
    """Busca na memória RBM por palavra-chave."""
    try:
        results = rbm_indexer.search_by_keyword(request.query)
        # Formata para linguagem natural
        formatted_results = []
        for r in results:
            natural_lang = f"{r['subject']} {r['predicate']} {r['object']}"
            formatted_results.append({
                "id": r['id'],
                "natural_language": natural_lang,
                "source": r['source_text']
            })
        return {"status": "success", "results": formatted_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/memory/all")
def get_all_memory():
    """Lista todos os tripletos armazenados."""
    try:
        results = rbm_indexer.get_all_triplets()
        return {"status": "success", "count": len(results), "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
