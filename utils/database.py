"""
Funciones de acceso a la base de datos JSON.
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


DATA_DIR = Path(__file__).parent.parent / "data"


def cargar_ciudad(ciudad: str) -> Dict[str, Any]:
    """
    Carga los datos de una ciudad.
    
    Args:
        ciudad: Nombre de la ciudad
        
    Returns:
        Dict con metadata y registros
    """
    archivo = DATA_DIR / f"{ciudad.lower()}.json"
    
    if not archivo.exists():
        return {
            "metadata": {
                "ciudad": ciudad,
                "fecha_actualizacion": None,
                "total_registros": 0
            },
            "registros": []
        }
    
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando {ciudad}: {e}")
        return {"metadata": {}, "registros": []}


def guardar_ciudad(ciudad: str, data: Dict[str, Any]) -> bool:
    """
    Guarda los datos de una ciudad.
    
    Args:
        ciudad: Nombre de la ciudad
        data: Datos a guardar
        
    Returns:
        True si se guardó correctamente
    """
    DATA_DIR.mkdir(exist_ok=True)
    archivo = DATA_DIR / f"{ciudad.lower()}.json"
    
    # Actualizar metadata
    data["metadata"]["fecha_actualizacion"] = datetime.now().isoformat()
    data["metadata"]["total_registros"] = len(data.get("registros", []))
    
    try:
        with open(archivo, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error guardando {ciudad}: {e}")
        return False


def listar_ciudades() -> List[Dict[str, Any]]:
    """
    Lista todas las ciudades disponibles con estadísticas.
    
    Returns:
        Lista de dicts con info de cada ciudad
    """
    ciudades = []
    
    if not DATA_DIR.exists():
        return ciudades
    
    for archivo in DATA_DIR.glob("*.json"):
        if archivo.name == "config_agentes.json" or archivo.name == "config_ciudades.json":
            continue
        
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            registros = data.get("registros", [])
            
            ciudades.append({
                "nombre": archivo.stem.title(),
                "archivo": str(archivo),
                "total_registros": len(registros),
                "con_telefono": sum(1 for r in registros if r.get("telefono")),
                "con_email": sum(1 for r in registros if r.get("email")),
                "con_web": sum(1 for r in registros if r.get("web")),
                "fecha_actualizacion": data.get("metadata", {}).get("fecha_actualizacion"),
            })
        except:
            continue
    
    return sorted(ciudades, key=lambda x: x["total_registros"], reverse=True)


def obtener_todos_registros() -> List[Dict[str, Any]]:
    """
    Obtiene todos los registros de todas las ciudades.
    
    Returns:
        Lista de todos los registros
    """
    todos = []
    
    for ciudad_info in listar_ciudades():
        data = cargar_ciudad(ciudad_info["nombre"])
        for registro in data.get("registros", []):
            registro["_ciudad_origen"] = ciudad_info["nombre"]
            todos.append(registro)
    
    return todos


def buscar_registros(
    termino: str,
    ciudad: str = None,
    tipo: str = None,
    especialidad: str = None
) -> List[Dict[str, Any]]:
    """
    Busca registros con filtros.
    
    Args:
        termino: Término de búsqueda (nombre)
        ciudad: Filtrar por ciudad
        tipo: Filtrar por tipo (despacho, abogado, ong)
        especialidad: Filtrar por especialidad
        
    Returns:
        Lista de registros que coinciden
    """
    resultados = []
    
    if ciudad:
        ciudades = [ciudad]
    else:
        ciudades = [c["nombre"] for c in listar_ciudades()]
    
    termino_lower = termino.lower() if termino else ""
    
    for nombre_ciudad in ciudades:
        data = cargar_ciudad(nombre_ciudad)
        
        for registro in data.get("registros", []):
            # Filtro por nombre
            if termino_lower and termino_lower not in registro.get("nombre", "").lower():
                continue
            
            # Filtro por tipo
            if tipo and registro.get("tipo") != tipo:
                continue
            
            # Filtro por especialidad
            if especialidad:
                especialidades = registro.get("especialidades", [])
                if especialidad.lower() not in [e.lower() for e in especialidades]:
                    continue
            
            registro["_ciudad_origen"] = nombre_ciudad
            resultados.append(registro)
    
    return resultados


def estadisticas_globales() -> Dict[str, Any]:
    """
    Calcula estadísticas globales de toda la base de datos.
    
    Returns:
        Dict con estadísticas
    """
    ciudades = listar_ciudades()
    
    total_registros = sum(c["total_registros"] for c in ciudades)
    total_telefono = sum(c["con_telefono"] for c in ciudades)
    total_email = sum(c["con_email"] for c in ciudades)
    total_web = sum(c["con_web"] for c in ciudades)
    
    # Por tipo
    por_tipo = {"despacho": 0, "abogado": 0, "ong": 0}
    for ciudad_info in ciudades:
        data = cargar_ciudad(ciudad_info["nombre"])
        for r in data.get("registros", []):
            tipo = r.get("tipo", "despacho")
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
    
    return {
        "total_ciudades": len(ciudades),
        "total_registros": total_registros,
        "con_telefono": total_telefono,
        "con_email": total_email,
        "con_web": total_web,
        "contacto_completo": min(total_telefono, total_email, total_web),  # aprox
        "por_tipo": por_tipo,
        "ciudades": ciudades,
    }
