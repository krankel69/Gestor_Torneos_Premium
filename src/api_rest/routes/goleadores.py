from fastapi import APIRouter, HTTPException, status
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
