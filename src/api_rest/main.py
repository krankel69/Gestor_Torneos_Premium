from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from api_rest.routes.equipos import router as equipos_router
from api_rest.routes.partidos import router as partidos_router
from api_rest.routes.goleadores import router as goleadores_router
from api_rest.routes.clasificacion import router as clasificacion_router

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

app.include_router(equipos_router)
app.include_router(partidos_router)
app.include_router(goleadores_router)
app.include_router(clasificacion_router)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc),
            "type": exc.__class__.__name__
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
