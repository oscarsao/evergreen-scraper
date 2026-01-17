"""
Filtros de validación para registros de abogados.
Elimina listados, blogs, traducciones y otros datos no válidos.
"""
import re
from typing import Dict, Tuple


# Dominios a excluir completamente
DOMINIOS_EXCLUIR = [
    # Diccionarios y traducciones
    'reverso.net', 'spanishdict.com', 'collinsdictionary.com', 'nglish.com',
    'cambridge.org', 'wiktionary.org', 'thefreedictionary.com', 'linguee',
    'wordreference.com', 'online-translator', 'translate.google',
    'deepl.com', 'bab.la',
    
    # Comercio/irrelevante
    'ikea.com', 'amazon.com', 'target.com', 'ebay.com', 'aliexpress',
    'mercadolibre', 'wallapop',
    
    # USA (Los Angeles, California, etc)
    'abogado.la', 'laligadefensora.com', 'abogadosinmigracionlosangeles',
    'abogadosfinder.us', 'losabogadoshispanos.us', 'abogadoshispanos.us',
    '/california/', '/los-angeles/', '/losangeles/',
    
    # Otros países (no España)
    'extranjeria.gob.cl', '.gob.cl', '.gob.mx', '.gob.ar',
    '.cl/', '.mx/', '.ar/', '.co/', '.pe/', '.ve/',
    
    # Redes sociales
    'facebook.com', 'instagram.com', 'twitter.com', 'x.com',
    'linkedin.com/pulse', 'linkedin.com/posts',
    'youtube.com', 'tiktok.com', 'pinterest.com',
    
    # Noticias y medios
    'elpais.com', 'elmundo.es', 'abc.es', 'larazon.es', '20minutos.es',
    'lavanguardia.com', 'elconfidencial', 'europapress', 'huffpost',
    'eldiario.es', 'publico.es', 'elperiodico.com',
    
    # Directorios y listados
    'paginasamarillas', 'qdq.com', 'infoisinfo', 'easyoffer', 'portaley',
    'justia.com', 'findlaw.com', 'avvo.com', 'lawyers.com',
    'tusabogadosyasesores', 'abogadosenespana', 'mejoresabogados',
    'lomejordelbarrio.com', 'guiadeabogados', 'directorioabogados',
    
    # Wikipedia y Q&A
    'wikipedia.org', 'wikihow.com', 'quora.com', 'yahoo.com/answers',
    'stackoverflow.com', 'reddit.com',
    
    # Google
    'google.com/maps', 'maps.google', 'google.com/search',
    
    # Blogs genéricos
    'blogspot.com', 'wordpress.com', 'medium.com', 'tumblr.com',
    'squarespace.com', 'wix.com/blog', 'blogger.com',
]

# Patrones en nombre que indican NO es un despacho real
NOMBRES_EXCLUIR = [
    r'\bmejores?\b', r'\btranslation\b', r'\btraduccion\b', r'\bdiccionario\b',
    r'\bdictionary\b', r'\benglish\b', r'\bspanish\b', r'\bwiktionary\b',
    r'\bsignificado\b', r'\bdefinicion\b',
    r'^top \d+', r'^listado de', r'^directorio de', r'^ranking',
    r'^comparativa', r'^los mejores', r'^mejores \d+',
    r'\bblog\b', r'\barticulo\b', r'\bnoticia\b',
    r'coffee table', r'\bikea\b', r'\bamazon\b', r'\btarget\b',
    r'los angeles', r'\bcalifornia\b', r'\bchile\b', r'\bmexico\b',
    r'^como ', r'^que es ', r'^requisitos para', r'^guia de',
    r'^pasos para', r'^documentos para', r'^tramites para',
]

# Patrones en URL que indican blog o artículo (no página principal)
URL_BLOG_PATTERNS = [
    r'/blog',  # Coincide con /blog/, /blog-juridico/, /blogs/, etc.
    r'/articulo', r'/noticia', r'/news',
    r'/post/', r'/article/',
    r'/categoria/', r'/category/',
    r'/noticias/', r'/actualidad/', r'/magazine/',
    r'/\d{4}/\d{2}/',  # URLs con fecha tipo /2024/01/
]


def es_registro_valido(registro: Dict) -> Tuple[bool, str]:
    """
    Verifica si un registro es válido (despacho/abogado real).
    
    Returns:
        Tuple[bool, str]: (es_valido, razon_si_invalido)
    """
    nombre = (registro.get('nombre') or '').lower().strip()
    web = (registro.get('web') or '').lower().strip()
    
    # Debe tener nombre
    if not nombre or len(nombre) < 3:
        return False, 'sin_nombre'
    
    # Debe tener web
    if not web or len(web) < 10:
        return False, 'sin_web'
    
    # Verificar dominios excluidos
    for dominio in DOMINIOS_EXCLUIR:
        if dominio in web:
            return False, f'dominio_excluido:{dominio}'
    
    # Verificar patrones de nombre inválido
    for patron in NOMBRES_EXCLUIR:
        if re.search(patron, nombre, re.IGNORECASE):
            return False, f'nombre_invalido:{patron}'
    
    # Verificar si es URL de blog/artículo
    for patron in URL_BLOG_PATTERNS:
        if re.search(patron, web):
            return False, 'url_blog'
    
    # Verificar que sea dominio .es o internacional válido
    # (pero no de otros países latinoamericanos para búsquedas de España)
    dominios_pais_excluir = ['.cl', '.mx', '.ar', '.co', '.pe', '.ve', '.ec', '.bo']
    for ext in dominios_pais_excluir:
        if web.endswith(ext) or f'{ext}/' in web:
            return False, f'pais_no_espana:{ext}'
    
    return True, 'ok'


def filtrar_registros(registros: list) -> Tuple[list, dict]:
    """
    Filtra una lista de registros, eliminando los inválidos.
    
    Returns:
        Tuple[list, dict]: (registros_validos, estadisticas_eliminados)
    """
    validos = []
    eliminados = {}
    
    for r in registros:
        es_valido, razon = es_registro_valido(r)
        if es_valido:
            validos.append(r)
        else:
            eliminados[razon] = eliminados.get(razon, 0) + 1
    
    return validos, eliminados


def limpiar_nombre(nombre: str) -> str:
    """Limpia y normaliza un nombre de despacho/abogado."""
    if not nombre:
        return ""
    
    # Eliminar sufijos comunes de títulos web
    sufijos_eliminar = [
        r'\s*[-|·•]\s*.*$',  # Todo después de - | · •
        r'\s*\|\s*.*$',
        r'\s*«.*$',
        r'\s*».*$',
        r'\.\.\.$',
    ]
    
    for patron in sufijos_eliminar:
        nombre = re.sub(patron, '', nombre)
    
    return nombre.strip()
