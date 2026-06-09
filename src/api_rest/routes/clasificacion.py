from fastapi import APIRouter, HTTPException, status
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
