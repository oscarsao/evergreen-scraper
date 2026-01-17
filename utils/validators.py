"""
Funciones de validación y normalización.
"""
import re
from typing import Optional


def validar_email(email: str) -> bool:
    """
    Valida formato de email.
    
    Args:
        email: Email a validar
        
    Returns:
        True si es válido
    """
    if not email:
        return False
    
    # Patrón básico de email
    patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(patron, email):
        return False
    
    # Excluir emails genéricos
    excluidos = ['example', 'test', 'noreply', 'no-reply', 'info@info']
    email_lower = email.lower()
    
    return not any(excl in email_lower for excl in excluidos)


def validar_telefono(telefono: str) -> bool:
    """
    Valida formato de teléfono español.
    
    Args:
        telefono: Teléfono a validar
        
    Returns:
        True si es válido
    """
    if not telefono:
        return False
    
    # Extraer solo dígitos
    digitos = "".join(c for c in telefono if c.isdigit())
    
    # Debe tener 9 dígitos (sin prefijo) o 11-12 (con prefijo 34)
    if len(digitos) == 9:
        # Debe empezar con 6, 7, 8 o 9
        return digitos[0] in "6789"
    elif len(digitos) in [11, 12]:
        # Con prefijo 34
        if digitos.startswith("34"):
            return digitos[2] in "6789"
    
    return False


def normalizar_telefono(telefono: str) -> str:
    """
    Normaliza teléfono al formato +34 XXX XXX XXX.
    
    Args:
        telefono: Teléfono a normalizar
        
    Returns:
        Teléfono normalizado o string vacío si inválido
    """
    if not telefono:
        return ""
    
    # Extraer dígitos y +
    limpio = "".join(c for c in telefono if c.isdigit() or c == "+")
    
    # Quitar + para procesar
    tiene_plus = limpio.startswith("+")
    if tiene_plus:
        limpio = limpio[1:]
    
    # Normalizar a formato 34XXXXXXXXX
    if limpio.startswith("34"):
        pass  # Ya tiene prefijo
    elif len(limpio) == 9 and limpio[0] in "6789":
        limpio = "34" + limpio
    else:
        return ""  # Formato no reconocido
    
    # Verificar longitud final
    if len(limpio) != 11:
        return ""
    
    # Formatear: +34 XXX XXX XXX
    return f"+{limpio[:2]} {limpio[2:5]} {limpio[5:8]} {limpio[8:]}"


def normalizar_email(email: str) -> Optional[str]:
    """
    Normaliza y valida email.
    
    Args:
        email: Email a normalizar
        
    Returns:
        Email normalizado o None si inválido
    """
    if not email:
        return None
    
    email = email.lower().strip()
    
    if validar_email(email):
        return email
    
    return None


def normalizar_url(url: str) -> Optional[str]:
    """
    Normaliza URL.
    
    Args:
        url: URL a normalizar
        
    Returns:
        URL normalizada o None si inválida
    """
    if not url:
        return None
    
    url = url.strip()
    
    # Añadir protocolo si falta
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    # Quitar trailing slash
    url = url.rstrip("/")
    
    # Validación básica
    if "." not in url:
        return None
    
    return url


def extraer_codigo_postal(texto: str) -> Optional[str]:
    """
    Extrae código postal español de un texto.
    
    Args:
        texto: Texto donde buscar
        
    Returns:
        Código postal o None
    """
    if not texto:
        return None
    
    # Buscar 5 dígitos que empiecen con 0-5 (CPs válidos España)
    patron = r'\b([0-5]\d{4})\b'
    match = re.search(patron, texto)
    
    return match.group(1) if match else None


def limpiar_nombre(nombre: str) -> str:
    """
    Limpia y normaliza nombre de despacho/abogado.
    
    Args:
        nombre: Nombre a limpiar
        
    Returns:
        Nombre limpio
    """
    if not nombre:
        return ""
    
    nombre = nombre.strip()
    
    # Eliminar sufijos comunes repetitivos
    sufijos_eliminar = [
        " - Abogados", " | Abogados", " – Abogados",
        " - Despacho", " | Despacho",
    ]
    
    for sufijo in sufijos_eliminar:
        if nombre.endswith(sufijo):
            nombre = nombre[:-len(sufijo)]
    
    # Capitalizar correctamente
    # Mantener acrónimos en mayúscula
    palabras = nombre.split()
    resultado = []
    
    for palabra in palabras:
        if palabra.isupper() and len(palabra) <= 4:
            # Probablemente acrónimo
            resultado.append(palabra)
        else:
            resultado.append(palabra.capitalize())
    
    return " ".join(resultado)
