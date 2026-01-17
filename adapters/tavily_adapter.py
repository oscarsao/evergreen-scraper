"""
Adapter para Tavily API.
Búsqueda web optimizada para IA (1,000 requests/mes gratis).
"""
import os
import re
from typing import List, Optional, Dict, Any
from .base import SearchAdapter, SearchResult

try:
    from tavily import TavilyClient
    TAVILY_DISPONIBLE = True
except ImportError:
    TAVILY_DISPONIBLE = False


class TavilyAdapter(SearchAdapter):
    """Adapter para Tavily - búsqueda web optimizada para IA."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("TAVILY_API_KEY"))
        self.nombre = "tavily"
        self.limite_requests = 1000  # por mes
        self.client = None
        
        if TAVILY_DISPONIBLE and self.api_key:
            self.client = TavilyClient(api_key=self.api_key)
    
    def esta_disponible(self) -> bool:
        return TAVILY_DISPONIBLE and bool(self.api_key) and self.client is not None
    
    def search(
        self, 
        query: str, 
        max_results: int = 10,
        search_depth: str = "advanced",
        include_answer: bool = True,
        **kwargs
    ) -> List[SearchResult]:
        """
        Búsqueda con Tavily.
        
        Args:
            query: Consulta de búsqueda
            max_results: Máximo de resultados (5-20)
            search_depth: "basic" o "advanced" (más profundo)
            include_answer: Incluir respuesta IA resumida
        """
        if not self.esta_disponible():
            return []
        
        resultados = []
        try:
            response = self.client.search(
                query=query,
                max_results=min(max_results, 20),
                search_depth=search_depth,
                include_answer=include_answer,
                include_domains=[],  # Sin restricción
                exclude_domains=["facebook.com", "twitter.com", "linkedin.com"],
            )
            self.incrementar_contador()
            
            resultados = self._procesar_respuesta(response, query)
            
        except Exception as e:
            print(f"[Tavily] Error: {e}")
        
        return resultados
    
    def search_abogados(
        self, 
        ciudad: str = "Madrid",
        zona: str = "",
        especialidad: str = "",
        incluir_contacto: bool = True
    ) -> List[SearchResult]:
        """Búsqueda optimizada para abogados de extranjería."""
        partes = ["abogado extranjería", ciudad]
        
        if zona:
            partes.append(zona)
        if especialidad:
            partes.append(especialidad)
        if incluir_contacto:
            partes.append("contacto teléfono email")
        
        query = " ".join(partes)
        return self.search(query, search_depth="advanced")
    
    def search_directorios(self, ciudad: str = "Madrid") -> List[SearchResult]:
        """Busca en directorios de abogados."""
        queries = [
            f"directorio abogados extranjería {ciudad}",
            f"listado despachos inmigración {ciudad}",
            f"colegio abogados {ciudad} especialistas extranjería",
        ]
        
        todos_resultados = []
        for query in queries:
            resultados = self.search(query, max_results=5)
            todos_resultados.extend(resultados)
        
        return todos_resultados
    
    def search_ongs(self, ciudad: str = "Madrid") -> List[SearchResult]:
        """Busca ONGs y servicios gratuitos."""
        query = f"ONG asistencia legal gratuita inmigrantes extranjería {ciudad} contacto"
        return self.search(query, max_results=10)
    
    def get_context(self, query: str, max_tokens: int = 4000) -> str:
        """
        Obtiene contexto resumido para usar con LLMs.
        Útil para alimentar a OpenAI con información actualizada.
        """
        if not self.esta_disponible():
            return ""
        
        try:
            context = self.client.get_search_context(
                query=query,
                max_tokens=max_tokens,
            )
            self.incrementar_contador()
            return context
        except Exception as e:
            print(f"[Tavily] Error obteniendo contexto: {e}")
            return ""
    
    def _procesar_respuesta(self, response: Dict, query: str) -> List[SearchResult]:
        """Procesa respuesta de Tavily."""
        resultados = []
        
        # Procesar resultados individuales
        for item in response.get("results", []):
            titulo = item.get("title", "")
            url = item.get("url", "")
            contenido = item.get("content", "")
            
            if not titulo:
                continue
            
            # Limpiar título
            titulo = self._limpiar_titulo(titulo)
            
            sr = SearchResult(
                nombre=titulo,
                web=url,
                fuente="tavily",
                url_origen=url,
            )
            
            # Extraer datos del contenido
            self._extraer_de_contenido(sr, contenido)
            
            resultados.append(sr)
        
        return resultados
    
    def _limpiar_titulo(self, titulo: str) -> str:
        """Limpia el título de sufijos comunes."""
        # Eliminar sufijos típicos
        patrones = [
            r'\s*[-|–]\s*(Abogados?|Despacho|Bufete|Law).*$',
            r'\s*[-|–]\s*\w+\.(com|es|net).*$',
            r'\s*\|\s*.*$',
        ]
        
        for patron in patrones:
            titulo = re.sub(patron, '', titulo, flags=re.IGNORECASE)
        
        return titulo.strip()
    
    def _extraer_de_contenido(self, sr: SearchResult, contenido: str):
        """Extrae información de contacto del contenido."""
        if not contenido:
            return
        
        # Teléfonos españoles
        patron_tel = r'(?:\+34)?[\s.-]?[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}'
        telefonos = re.findall(patron_tel, contenido)
        if telefonos:
            sr.telefono = list(set([self.normalizar_telefono(t) for t in telefonos[:3]]))
        
        # Email
        patron_email = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(patron_email, contenido.lower())
        # Filtrar emails genéricos
        emails_validos = [e for e in emails if not any(x in e for x in ['example', 'test', 'noreply'])]
        if emails_validos:
            sr.email = emails_validos[0]
        
        # Dirección con código postal
        patron_dir = r'(?:C/|Calle|Avda\.|Av\.|Avenida|Plaza|Pº|Paseo)\s+[^,\n]+(?:,\s*\d+)?(?:,?\s*\d{5})?'
        direcciones = re.findall(patron_dir, contenido, re.IGNORECASE)
        if direcciones:
            sr.direccion = direcciones[0].strip()
        
        # Detectar especialidades
        especialidades = []
        keywords_especialidades = {
            "arraigo": ["arraigo", "arraigo social", "arraigo laboral", "arraigo familiar"],
            "asilo": ["asilo", "refugiado", "protección internacional"],
            "nacionalidad": ["nacionalidad", "nacionalidad española"],
            "reagrupación": ["reagrupación", "reagrupación familiar"],
            "visados": ["visado", "visa", "visados"],
            "permisos": ["permiso trabajo", "permiso residencia", "autorización"],
            "expulsiones": ["expulsión", "expulsiones", "devolución"],
            "recursos": ["recurso", "recursos", "denegación"],
        }
        
        contenido_lower = contenido.lower()
        for esp, keywords in keywords_especialidades.items():
            if any(kw in contenido_lower for kw in keywords):
                especialidades.append(esp)
        
        if especialidades:
            sr.especialidades = especialidades
        
        # Ciudad
        if "madrid" in contenido_lower:
            sr.ciudad = "Madrid"
        elif "barcelona" in contenido_lower:
            sr.ciudad = "Barcelona"
        elif "valencia" in contenido_lower:
            sr.ciudad = "Valencia"
