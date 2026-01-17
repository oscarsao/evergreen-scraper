"""
Módulos core del sistema de búsqueda multi-agente.
"""
from .consolidador import Consolidador, ConsolidacionResult
from .orquestador import Orquestador

__all__ = [
    "Consolidador",
    "ConsolidacionResult",
    "Orquestador",
]
