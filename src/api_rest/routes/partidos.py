from fastapi import APIRouter, HTTPException, status
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
