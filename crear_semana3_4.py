from pathlib import Path

# ════════════════════════════════════════════════════════════════════════════
# PARTIDOS.PY
# ════════════════════════════════════════════════════════════════════════════

partidos_code = """from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from database import GestorBaseDeDatos

router = APIRouter(prefix="/api/partidos", tags=["partidos"])

class PartidoCreate(BaseModel):
    fecha: datetime
    equipo_local_id: int
    equipo_visitante_id: int
    goles_local: int = -1
    goles_visitante: int = -1
    jugado: int = 0
    estadio: Optional[str] = None

class PartidoResponse(BaseModel):
    id: int
    fecha: datetime
    equipo_local_id: int
    equipo_visitante_id: int
    goles_local: int
    goles_visitante: int
    jugado: int
    class Config:
        from_attributes = True

def get_db():
    db_path = "bases_de_datos/liga_futbol_v2.db"
    return GestorBaseDeDatos(db_path)

@router.get("", response_model=List[PartidoResponse])
async def get_partidos():
    try:
        db = get_db()
        partidos = db.obtener_partidos()
        if not partidos:
            return []
        resultado = []
        for p in partidos:
            p_dict = dict(p) if hasattr(p, 'keys') else p
            resultado.append(p_dict)
        return resultado
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/{partido_id}", response_model=PartidoResponse)
async def get_partido(partido_id: int):
    try:
        db = get_db()
        partidos = db.obtener_partidos()
        for p in partidos:
            p_dict = dict(p) if hasattr(p, 'keys') else p
            if p_dict.get('id') == partido_id:
                return p_dict
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Partido {partido_id} no encontrado"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_partido(partido: PartidoCreate):
    try:
        db = get_db()
        resultado = db.agregar_partido(
            partido.equipo_local_id,
            partido.equipo_visitante_id,
            partido.fecha.isoformat()
        )
        if resultado:
            return {
                "status": "success",
                "message": "Partido creado",
                "partido_id": resultado
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Error creando partido"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.put("/{partido_id}", response_model=dict)
async def update_partido(partido_id: int, partido: dict):
    return {"status": "pending", "message": "Update no implementado"}

@router.delete("/{partido_id}", response_model=dict)
async def delete_partido(partido_id: int):
    return {"status": "pending", "message": "Delete no implementado"}
"""

# ════════════════════════════════════════════════════════════════════════════
# GOLEADORES.PY
# ════════════════════════════════════════════════════════════════════════════

goleadores_code = """from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from database import GestorBaseDeDatos

router = APIRouter(prefix="/api/goleadores", tags=["goleadores"])

class GoleadorCreate(BaseModel):
    jugador: str
    equipo: str
    goles: int = 1
    partido_id: Optional[int] = None

class GoleadorResponse(BaseModel):
    id: int
    jugador: str
    equipo: str
    goles_marcados: int
    class Config:
        from_attributes = True

def get_db():
    db_path = "bases_de_datos/liga_futbol_v2.db"
    return GestorBaseDeDatos(db_path)

@router.get("", response_model=List[dict])
async def get_goleadores():
    try:
        db = get_db()
        goleadores = db.obtener_goleadores_top()
        if not goleadores:
            return []
        resultado = []
        for i, g in enumerate(goleadores, 1):
            g_dict = dict(g) if hasattr(g, 'keys') else g
            g_dict['posicion'] = i
            resultado.append(g_dict)
        return resultado
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/{goleador_id}", response_model=dict)
async def get_goleador(goleador_id: int):
    try:
        db = get_db()
        goleadores = db.obtener_goleadores_top()
        for g in goleadores:
            g_dict = dict(g) if hasattr(g, 'keys') else g
            if g_dict.get('id') == goleador_id:
                return g_dict
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Goleador {goleador_id} no encontrado"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_goleador(goleador: GoleadorCreate):
    try:
        if not goleador.jugador or not goleador.equipo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Jugador y equipo requeridos"
            )
        
        db = get_db()
        resultado = db.agregar_goleador(goleador.jugador, goleador.equipo, goleador.goles)
        
        if resultado:
            return {
                "status": "success",
                "message": f"{goleador.jugador} registrado",
                "goles": goleador.goles
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Error registrando goleador"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.put("/{goleador_id}", response_model=dict)
async def update_goleador(goleador_id: int, goleador: dict):
    return {"status": "pending", "message": "Update no implementado"}

@router.delete("/{goleador_id}", response_model=dict)
async def delete_goleador(goleador_id: int):
    return {"status": "pending", "message": "Delete no implementado"}
"""

# ════════════════════════════════════════════════════════════════════════════
# CLASIFICACION.PY
# ════════════════════════════════════════════════════════════════════════════

clasificacion_code = """from fastapi import APIRouter, HTTPException, status
from typing import List
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from database import GestorBaseDeDatos

router = APIRouter(prefix="/api/clasificacion", tags=["clasificacion"])

def get_db():
    db_path = "bases_de_datos/liga_futbol_v2.db"
    return GestorBaseDeDatos(db_path)

@router.get("", response_model=List[dict])
async def get_clasificacion():
    try:
        db = get_db()
        clas = db.recalcular_y_obtener_clasificacion()
        if not clas:
            return []
        resultado = []
        for i, eq in enumerate(clas, 1):
            eq_dict = dict(eq) if hasattr(eq, 'keys') else eq
            eq_dict['posicion'] = i
            eq_dict['dif'] = eq_dict.get('gf', 0) - eq_dict.get('gc', 0)
            resultado.append(eq_dict)
        return resultado
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.get("/equipo/{equipo_id}", response_model=dict)
async def get_clasificacion_equipo(equipo_id: int):
    try:
        db = get_db()
        clas = db.recalcular_y_obtener_clasificacion()
        for eq in clas:
            eq_dict = dict(eq) if hasattr(eq, 'keys') else eq
            if eq_dict.get('id') == equipo_id:
                eq_dict['dif'] = eq_dict.get('gf', 0) - eq_dict.get('gc', 0)
                return eq_dict
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Equipo {equipo_id} no encontrado"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )

@router.post("/recalcular", response_model=dict)
async def recalcular_clasificacion():
    try:
        db = get_db()
        clas = db.recalcular_y_obtener_clasificacion()
        return {
            "status": "success",
            "message": "Clasificacion recalculada",
            "equipos": len(clas)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error: {str(e)}"
        )
"""

# ════════════════════════════════════════════════════════════════════════════
# MAIN.PY ACTUALIZADO
# ════════════════════════════════════════════════════════════════════════════

main_code = """from fastapi import FastAPI
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
"""

# ════════════════════════════════════════════════════════════════════════════
# CREAR ARCHIVOS
# ════════════════════════════════════════════════════════════════════════════

with open("src/api_rest/routes/partidos.py", "w") as f:
    f.write(partidos_code)

with open("src/api_rest/routes/goleadores.py", "w") as f:
    f.write(goleadores_code)

with open("src/api_rest/routes/clasificacion.py", "w") as f:
    f.write(clasificacion_code)

with open("src/api_rest/main.py", "w") as f:
    f.write(main_code)

print("[OK] partidos.py creado")
print("[OK] goleadores.py creado")
print("[OK] clasificacion.py creado")
print("[OK] main.py actualizado")
print("\nAhora reinicia uvicorn:")
print("  Presiona CTRL+C en la terminal")
print("  python -m uvicorn api_rest.main:app --reload")
