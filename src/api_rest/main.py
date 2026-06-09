from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Gestor Premium de Torneos API",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "OK", "version": "2.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/equipos")
async def get_equipos():
    return {"status": "TODO"}

@app.get("/api/partidos")
async def get_partidos():
    return {"status": "TODO"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
