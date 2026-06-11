from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from database import GestorBaseDeDatos

router = APIRouter(prefix="/api/equipos", tags=["equipos"])


class EquipoCreate(BaseModel):
    nombre: str
    ciudad: Optional[str] = None
    grupo: Optional[str] = None


class EquipoResponse(BaseModel):
    id: int
    nombre: str
    ciudad: Optional[str]
    pj: int
    pg: int
    pe: int
    pp: int
    gf: int
    gc: int
    pts: int

    class Config:
        from_attributes = True


def get_db(torneo: str = "liga"):
    torneos_bd = {"liga": "bases_de_datos/liga_futbol_v2.db", "mundial": "bases_de_datos/mundial_2026_v2.db", "champions": "bases_de_datos/champions_gui_v2.db", "euro": "bases_de_datos/eurocopa_2024_v2.db"}
    db_path = torneos_bd.get(torneo, torneos_bd["liga"])
    return GestorBaseDeDatos(db_path)


@router.get("", response_model=List[EquipoResponse])
async def get_equipos(torneo: str = "liga"):
    try:
        db = get_db(torneo)
        equipos = db.obtener_equipos()
        if not equipos:
            return []
        resultado = []
        for eq in equipos:
            eq_dict = dict(eq) if hasattr(eq, "keys") else eq
            resultado.append(eq_dict)
        return resultado
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}")


@router.get("/{equipo_id}", response_model=EquipoResponse)
async def get_equipo(equipo_id: int):
    try:
        db = get_db()
        equipos = db.obtener_equipos()
        for eq in equipos:
            eq_dict = dict(eq) if hasattr(eq, "keys") else eq
            if eq_dict.get("id") == equipo_id:
                return eq_dict
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Equipo {equipo_id} no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}")


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_equipo(equipo: EquipoCreate):
    try:
        if not equipo.nombre or len(equipo.nombre.strip()) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nombre requerido")
        db = get_db()
        resultado = db.agregar_equipo(equipo.nombre, equipo.ciudad or "")
        if resultado:
            return {"status": "success", "message": f"Equipo '{equipo.nombre}' creado", "equipo": equipo.nombre}
        else:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Equipo ya existe")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error: {str(e)}")


@router.put("/{equipo_id}", response_model=dict)
async def update_equipo(equipo_id: int, equipo: dict):
    return {"status": "pending", "message": "Update no implementado"}


@router.delete("/{equipo_id}", response_model=dict)
async def delete_equipo(equipo_id: int):
    return {"status": "pending", "message": "Delete no implementado"}


from firebase_admin import firestore
from fastapi import HTTPException


@router.post("", response_model=dict, status_code=201)
async def create_equipo(equipo: EquipoCreate):
    """Crear nuevo equipo"""
    try:
        if not equipo.nombre or len(equipo.nombre.strip()) == 0:
            raise HTTPException(status_code=400, detail="Nombre requerido")
        db = get_db()
        resultado = db.agregar_equipo(equipo.nombre, equipo.ciudad or "")
        return {"status": "success", "message": f"Equipo '{equipo.nombre}' creado", "equipo": equipo.nombre}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
