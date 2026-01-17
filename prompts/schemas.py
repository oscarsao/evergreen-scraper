"""
Schemas y validación de datos.
"""
from typing import List, Optional, Dict, Any

# =============================================================================
# Schema de registro estandarizado
# =============================================================================

SCHEMA_REGISTRO = {
    "nombre": str,           # Requerido
    "tipo": str,             # despacho, abogado, ong
    "telefono": list,        # Lista de strings
    "email": (str, None),    # String o None
    "web": (str, None),
    "direccion": (str, None),
    "ciudad": (str, None),
    "distrito": (str, None),
    "codigo_postal": (str, None),
    "especialidades": list,
    "idiomas": list,
    "horario": (str, None),
    "valoracion": (float, None),
    "fuente": (str, None),
    "url_origen": (str, None),
    "fecha_actualizacion": (str, None),
}

# Campos mínimos requeridos para que un registro sea válido
CAMPOS_REQUERIDOS = ["nombre"]
CAMPOS_CONTACTO = ["telefono", "email", "web"]  # Al menos uno debe tener valor

# Tipos válidos
TIPOS_VALIDOS = ["despacho", "abogado", "ong"]

# Especialidades reconocidas
ESPECIALIDADES_VALIDAS = [
    "arraigo",
    "arraigo_social",
    "arraigo_laboral", 
    "arraigo_familiar",
    "arraigo_formativo",
    "asilo",
    "proteccion_internacional",
    "nacionalidad",
    "reagrupacion",
    "reagrupacion_familiar",
    "visados",
    "permisos_trabajo",
    "autorizacion_residencia",
    "expulsiones",
    "recursos",
    "golden_visa",
    "general",  # extranjería general
]

# Ciudades principales
CIUDADES_PRINCIPALES = [
    "Madrid",
    "Barcelona", 
    "Valencia",
    "Sevilla",
    "Málaga",
    "Bilbao",
    "Zaragoza",
    "Alicante",
    "Murcia",
    "Palma de Mallorca",
]

# Distritos de Madrid
DISTRITOS_MADRID = [
    "Centro", "Arganzuela", "Retiro", "Salamanca", "Chamartín",
    "Tetuán", "Chamberí", "Fuencarral-El Pardo", "Moncloa-Aravaca",
    "Latina", "Carabanchel", "Usera", "Puente de Vallecas",
    "Moratalaz", "Ciudad Lineal", "Hortaleza", "Villaverde",
    "Villa de Vallecas", "Vicálvaro", "San Blas-Canillejas", "Barajas",
]


def validar_registro(registro: Dict[str, Any]) -> tuple:
    """
    Valida un registro y devuelve (es_valido, errores).
    
    Returns:
        tuple: (bool, list) - (es_valido, lista_de_errores)
    """
    errores = []
    
    # Verificar campos requeridos
    for campo in CAMPOS_REQUERIDOS:
        if not registro.get(campo):
            errores.append(f"Campo requerido faltante: {campo}")
    
    # Verificar que tenga al menos un método de contacto
    tiene_contacto = any(
        registro.get(campo) for campo in CAMPOS_CONTACTO
    )
    if not tiene_contacto:
        errores.append("Debe tener al menos teléfono, email o web")
    
    # Validar tipo
    tipo = registro.get("tipo", "despacho")
    if tipo not in TIPOS_VALIDOS:
        errores.append(f"Tipo inválido: {tipo}")
    
    # Validar email si existe
    email = registro.get("email")
    if email and "@" not in email:
        errores.append(f"Email inválido: {email}")
    
    # Validar teléfonos
    telefonos = registro.get("telefono", [])
    if isinstance(telefonos, str):
        telefonos = [telefonos]
    for tel in telefonos:
        digitos = "".join(c for c in tel if c.isdigit())
        if len(digitos) < 9:
            errores.append(f"Teléfono muy corto: {tel}")
    
    return len(errores) == 0, errores


def normalizar_registro(registro: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza un registro al formato estándar.
    """
    normalizado = {}
    
    # Nombre (requerido)
    normalizado["nombre"] = str(registro.get("nombre", "")).strip()
    
    # Tipo
    tipo = registro.get("tipo", "despacho").lower()
    normalizado["tipo"] = tipo if tipo in TIPOS_VALIDOS else "despacho"
    
    # Teléfonos (normalizar a lista)
    telefonos = registro.get("telefono", registro.get("telefonos", []))
    if isinstance(telefonos, str):
        telefonos = [telefonos] if telefonos else []
    normalizado["telefono"] = [normalizar_telefono(t) for t in telefonos if t]
    
    # Email
    email = registro.get("email", "")
    normalizado["email"] = email.lower().strip() if email and "@" in email else None
    
    # Web
    web = registro.get("web", "")
    if web:
        web = web.strip()
        if not web.startswith(("http://", "https://")):
            web = "https://" + web
        normalizado["web"] = web.rstrip("/")
    else:
        normalizado["web"] = None
    
    # Dirección
    normalizado["direccion"] = registro.get("direccion", "").strip() or None
    
    # Ciudad
    ciudad = registro.get("ciudad", "")
    if ciudad:
        # Capitalizar correctamente
        ciudad = ciudad.strip().title()
    normalizado["ciudad"] = ciudad or None
    
    # Distrito
    normalizado["distrito"] = registro.get("distrito", "").strip() or None
    
    # Especialidades (normalizar a lista)
    especialidades = registro.get("especialidades", [])
    if isinstance(especialidades, str):
        especialidades = [especialidades] if especialidades else []
    normalizado["especialidades"] = [
        e.lower().replace(" ", "_") for e in especialidades if e
    ]
    
    # Valoración
    valoracion = registro.get("valoracion")
    if valoracion is not None:
        try:
            normalizado["valoracion"] = float(valoracion)
        except (ValueError, TypeError):
            normalizado["valoracion"] = None
    else:
        normalizado["valoracion"] = None
    
    # Metadata
    normalizado["fuente"] = registro.get("fuente")
    normalizado["url_origen"] = registro.get("url_origen")
    normalizado["fecha_actualizacion"] = registro.get("fecha_actualizacion")
    
    return normalizado


def normalizar_telefono(telefono: str) -> str:
    """Normaliza un teléfono español al formato estándar."""
    if not telefono:
        return ""
    
    # Eliminar espacios, guiones, paréntesis, puntos
    limpio = "".join(c for c in telefono if c.isdigit() or c == "+")
    
    # Si empieza con 34 sin +, añadir +
    if limpio.startswith("34") and not limpio.startswith("+"):
        limpio = "+" + limpio
    # Si empieza con 6, 7, 8 o 9 (móvil o fijo español), añadir +34
    elif limpio and limpio[0] in "6789":
        limpio = "+34" + limpio
    
    # Formato: +34 XXX XXX XXX
    if limpio.startswith("+34") and len(limpio) == 12:
        return f"{limpio[:3]} {limpio[3:6]} {limpio[6:9]} {limpio[9:]}"
    
    return limpio


def es_registro_valido(registro: Dict[str, Any]) -> bool:
    """Verifica rápidamente si un registro es válido."""
    if not registro.get("nombre"):
        return False
    
    tiene_contacto = (
        registro.get("telefono") or 
        registro.get("email") or 
        registro.get("web")
    )
    return bool(tiene_contacto)


def crear_registro_vacio() -> Dict[str, Any]:
    """Crea un registro con todos los campos en sus valores por defecto."""
    return {
        "nombre": "",
        "tipo": "despacho",
        "telefono": [],
        "email": None,
        "web": None,
        "direccion": None,
        "ciudad": None,
        "distrito": None,
        "especialidades": [],
        "valoracion": None,
        "fuente": None,
        "url_origen": None,
        "fecha_actualizacion": None,
    }
