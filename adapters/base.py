"""
Clase base para todos los adapters de búsqueda.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class SearchResult:
    """Resultado estandarizado de búsqueda."""
    nombre: str
    tipo: str = "despacho"  # despacho, abogado, ong
    telefono: List[str] = field(default_factory=list)
    email: Optional[str] = None
    web: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    distrito: Optional[str] = None
    especialidades: List[str] = field(default_factory=list)
    valoracion: Optional[float] = None
    fuente: Optional[str] = None
    url_origen: Optional[str] = None
    fecha_extraccion: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para JSON."""
        return {
            "nombre": self.nombre,
            "tipo": self.tipo,
            "telefono": self.telefono,
            "email": self.email,
            "web": self.web,
            "direccion": self.direccion,
            "ciudad": self.ciudad,
            "distrito": self.distrito,
            "especialidades": self.especialidades,
            "valoracion": self.valoracion,
            "fuente": self.fuente,
            "url_origen": self.url_origen,
            "fecha_extraccion": self.fecha_extraccion,
        }
    
    def es_valido(self) -> bool:
        """Verifica si tiene al menos un método de contacto."""
        return bool(self.telefono or self.email or self.web)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SearchResult":
        """Crea instancia desde diccionario."""
        return cls(
            nombre=data.get("nombre", ""),
            tipo=data.get("tipo", "despacho"),
            telefono=data.get("telefono", []),
            email=data.get("email"),
            web=data.get("web"),
            direccion=data.get("direccion"),
            ciudad=data.get("ciudad"),
            distrito=data.get("distrito"),
            especialidades=data.get("especialidades", []),
            valoracion=data.get("valoracion"),
            fuente=data.get("fuente"),
            url_origen=data.get("url_origen"),
            fecha_extraccion=data.get("fecha_extraccion", datetime.now().isoformat()),
        )


class SearchAdapter(ABC):
    """Clase base abstracta para adapters de búsqueda."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.nombre = "base"
        self.requests_realizados = 0
        self.limite_requests = None
    
    @abstractmethod
    def search(self, query: str, **kwargs) -> List[SearchResult]:
        """Ejecuta una búsqueda y devuelve resultados."""
        pass
    
    def esta_disponible(self) -> bool:
        """Verifica si el adapter tiene API key configurada."""
        return bool(self.api_key)
    
    def dentro_de_limite(self) -> bool:
        """Verifica si está dentro del límite de requests."""
        if self.limite_requests is None:
            return True
        return self.requests_realizados < self.limite_requests
    
    def incrementar_contador(self, cantidad: int = 1, creditos: int = 0):
        """Incrementa el contador de requests y registra uso."""
        self.requests_realizados += cantidad
        
        # Registrar en el tracker de costos
        try:
            from utils.api_tracker import registrar_uso
            registrar_uso(
                api=self.nombre,
                requests=cantidad,
                creditos=creditos if creditos else cantidad
            )
        except ImportError:
            pass  # Tracker no disponible
    
    def resetear_contador(self):
        """Resetea el contador de requests."""
        self.requests_realizados = 0
    
    def normalizar_telefono(self, telefono: str) -> str:
        """Normaliza un número de teléfono español."""
        if not telefono:
            return ""
        # Eliminar espacios, guiones, paréntesis
        limpio = "".join(c for c in telefono if c.isdigit() or c == "+")
        # Añadir prefijo +34 si no tiene
        if limpio.startswith("34") and not limpio.startswith("+"):
            limpio = "+" + limpio
        elif limpio.startswith("6") or limpio.startswith("9"):
            limpio = "+34" + limpio
        return limpio
    
    def validar_email(self, email: str) -> bool:
        """Valida formato básico de email."""
        if not email:
            return False
        return "@" in email and "." in email.split("@")[-1]
    
    def limpiar_url(self, url: str) -> str:
        """Limpia y normaliza una URL."""
        if not url:
            return ""
        url = url.strip()
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        return url.rstrip("/")
