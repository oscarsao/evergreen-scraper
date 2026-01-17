"""
Biblioteca de prompts optimizados para búsqueda de abogados.
"""
from .busqueda import PROMPTS_BUSQUEDA, URLS_DIRECTORIOS, QUERIES_PLACES
from .extraccion import SCHEMA_ABOGADO, PROMPT_EXTRACCION, PROMPT_ESTRUCTURAR
from .schemas import SCHEMA_REGISTRO, CAMPOS_REQUERIDOS

__all__ = [
    "PROMPTS_BUSQUEDA",
    "URLS_DIRECTORIOS", 
    "QUERIES_PLACES",
    "SCHEMA_ABOGADO",
    "PROMPT_EXTRACCION",
    "PROMPT_ESTRUCTURAR",
    "SCHEMA_REGISTRO",
    "CAMPOS_REQUERIDOS",
]
