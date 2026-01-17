"""
Adapter para Firecrawl API.
Soporta: búsqueda, scraping, extracción estructurada y crawling.
"""
import os
import re
from typing import List, Optional, Dict, Any
from .base import SearchAdapter, SearchResult

try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_DISPONIBLE = True
except ImportError:
    FIRECRAWL_DISPONIBLE = False


# Schema para extracción de datos de abogados
SCHEMA_ABOGADO = {
    "type": "object",
    "properties": {
        "nombre": {
            "type": "string",
            "description": "Nombre completo del abogado o despacho"
        },
        "telefonos": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Todos los números de teléfono encontrados"
        },
        "email": {
            "type": "string",
            "description": "Email principal de contacto"
        },
        "direccion": {
            "type": "string",
            "description": "Dirección física completa con código postal"
        },
        "web": {
            "type": "string",
            "description": "URL del sitio web"
        },
        "especialidades": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Áreas: arraigo, asilo, nacionalidad, reagrupación, etc."
        },
        "horario": {
            "type": "string",
            "description": "Horario de atención"
        }
    },
    "required": ["nombre"]
}

PROMPT_EXTRACCION = """
Extrae TODOS los datos de contacto de abogados/despachos de extranjería de esta página.

REGLAS:
1. Incluir TODOS los teléfonos (fijos, móviles, WhatsApp)
2. Email debe contener @
3. Dirección con calle, número y CP si están
4. Identificar especialidades: arraigo, asilo, nacionalidad, reagrupación, visados, permisos, expulsiones
5. NO inventar datos - solo lo explícito en la página
6. Si hay múltiples profesionales, extraer TODOS

Devuelve JSON válido.
"""


class FirecrawlAdapter(SearchAdapter):
    """Adapter para Firecrawl con capacidades avanzadas de scraping."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("FIRECRAWL_API_KEY"))
        self.nombre = "firecrawl"
        self.limite_requests = 500  # créditos mensuales plan gratis
        self.app = None
        
        if FIRECRAWL_DISPONIBLE and self.api_key:
            self.app = FirecrawlApp(api_key=self.api_key)
    
    def esta_disponible(self) -> bool:
        return FIRECRAWL_DISPONIBLE and bool(self.api_key) and self.app is not None
    
    def search(self, query: str, limit: int = 10, **kwargs) -> List[SearchResult]:
        """Búsqueda web con Firecrawl."""
        if not self.esta_disponible():
            return []
        
        try:
            resultado = self.app.search(query, limit=limit)
            self.incrementar_contador()
            return self._procesar_resultados_busqueda(resultado, query)
        except Exception as e:
            print(f"[Firecrawl] Error en búsqueda: {e}")
            return []
    
    def scrape_url(self, url: str, formats: List[str] = None) -> Dict[str, Any]:
        """Scrapea una URL específica."""
        if not self.esta_disponible():
            return {}
        
        formats = formats or ["markdown", "links"]
        try:
            resultado = self.app.scrape(url, formats=formats, only_main_content=True)
            self.incrementar_contador()
            return resultado if isinstance(resultado, dict) else {"markdown": str(resultado)}
        except Exception as e:
            print(f"[Firecrawl] Error scraping {url}: {e}")
            return {}
    
    def scrape_pagina_contacto(self, url_base: str) -> Dict[str, Any]:
        """Intenta encontrar y scrapear la página de contacto."""
        if not self.esta_disponible():
            return {}
        
        # URLs comunes de contacto
        variantes = [
            "/contacto", "/contacto/", "/contact", "/contact/",
            "/contactanos", "/sobre-nosotros", "/about",
            "/quienes-somos", "/equipo"
        ]
        
        # Primero intentar mapear el sitio para encontrar contacto
        try:
            mapa = self.app.map(url_base, limit=20)
            self.incrementar_contador()
            
            urls = mapa.get("urls", []) if isinstance(mapa, dict) else []
            
            # Buscar URL de contacto en el mapa
            for url in urls:
                url_lower = url.lower()
                if any(v in url_lower for v in ["contact", "contacto"]):
                    return self.scrape_url(url)
            
            # Si no encuentra, probar variantes comunes
            url_base = url_base.rstrip("/")
            for variante in variantes[:3]:  # Limitar intentos
                try:
                    resultado = self.scrape_url(url_base + variante)
                    if resultado.get("markdown"):
                        return resultado
                except:
                    continue
                    
        except Exception as e:
            print(f"[Firecrawl] Error buscando contacto en {url_base}: {e}")
        
        # Último recurso: scrapear la página principal
        return self.scrape_url(url_base)
    
    def extract_structured(
        self, 
        urls: List[str], 
        schema: Dict = None, 
        prompt: str = None
    ) -> List[SearchResult]:
        """Extrae datos estructurados de múltiples URLs."""
        if not self.esta_disponible():
            return []
        
        schema = schema or SCHEMA_ABOGADO
        prompt = prompt or PROMPT_EXTRACCION
        
        resultados = []
        try:
            # Firecrawl extract acepta lista de URLs
            extraction = self.app.extract(urls=urls, schema=schema, prompt=prompt)
            self.incrementar_contador(len(urls))
            
            # Procesar resultado
            if isinstance(extraction, dict):
                data = extraction.get("data", extraction)
                resultados.extend(self._convertir_extraccion(data, urls[0] if urls else ""))
            elif isinstance(extraction, list):
                for item in extraction:
                    resultados.extend(self._convertir_extraccion(item, urls[0] if urls else ""))
                    
        except Exception as e:
            print(f"[Firecrawl] Error en extracción estructurada: {e}")
        
        return resultados
    
    def crawl_directorio(
        self, 
        url: str, 
        max_pages: int = 10, 
        patron_url: str = None
    ) -> List[SearchResult]:
        """Crawlea un directorio de abogados."""
        if not self.esta_disponible():
            return []
        
        resultados = []
        try:
            crawl_result = self.app.crawl(
                url,
                limit=max_pages,
                max_depth=2,
                scrape_options={"formats": ["markdown"]}
            )
            self.incrementar_contador(max_pages)
            
            # Procesar cada página crawleada
            pages = crawl_result.get("data", []) if isinstance(crawl_result, dict) else []
            for page in pages:
                if patron_url and patron_url not in page.get("url", ""):
                    continue
                contenido = page.get("markdown", "")
                url_pagina = page.get("url", url)
                resultados.extend(self._extraer_de_texto(contenido, url_pagina))
                
        except Exception as e:
            print(f"[Firecrawl] Error en crawl de {url}: {e}")
        
        return resultados
    
    def _procesar_resultados_busqueda(
        self, 
        resultado: Any, 
        query: str
    ) -> List[SearchResult]:
        """Procesa resultados de búsqueda Firecrawl."""
        resultados = []
        
        # Firecrawl v2 devuelve objeto SearchData con .web
        if hasattr(resultado, 'web') and resultado.web:
            items = resultado.web
        elif isinstance(resultado, dict):
            items = resultado.get("results", resultado.get("data", []))
        elif isinstance(resultado, list):
            items = resultado
        else:
            return resultados
        
        for item in items:
            # Manejar tanto dict como objetos pydantic
            if isinstance(item, dict):
                nombre = item.get("title", item.get("name", ""))
                url = item.get("url", item.get("link", ""))
                snippet = item.get("snippet", item.get("description", ""))
            else:
                # Objeto pydantic (Firecrawl v2)
                nombre = getattr(item, 'title', '') or getattr(item, 'name', '')
                url = getattr(item, 'url', '') or getattr(item, 'link', '')
                snippet = getattr(item, 'snippet', '') or getattr(item, 'description', '')
            
            if not nombre:
                continue
            
            sr = SearchResult(
                nombre=nombre,
                web=url,
                fuente="firecrawl_search",
                url_origen=url,
            )
            
            # Extraer datos del snippet si existe
            self._extraer_contacto_de_texto(sr, snippet)
            
            if sr.nombre:
                resultados.append(sr)
        
        return resultados
    
    def _convertir_extraccion(self, data: Any, url_origen: str) -> List[SearchResult]:
        """Convierte datos extraídos a SearchResult."""
        resultados = []
        
        if isinstance(data, list):
            for item in data:
                sr = self._item_a_search_result(item, url_origen)
                if sr:
                    resultados.append(sr)
        elif isinstance(data, dict):
            # Puede ser un solo resultado o contener array
            if "abogados" in data:
                for item in data["abogados"]:
                    sr = self._item_a_search_result(item, url_origen)
                    if sr:
                        resultados.append(sr)
            else:
                sr = self._item_a_search_result(data, url_origen)
                if sr:
                    resultados.append(sr)
        
        return resultados
    
    def _item_a_search_result(self, item: Dict, url_origen: str) -> Optional[SearchResult]:
        """Convierte un item extraído a SearchResult."""
        if not isinstance(item, dict):
            return None
        
        nombre = item.get("nombre", "")
        if not nombre:
            return None
        
        telefonos = item.get("telefonos", item.get("telefono", []))
        if isinstance(telefonos, str):
            telefonos = [telefonos]
        
        # Normalizar teléfonos
        telefonos = [self.normalizar_telefono(t) for t in telefonos if t]
        
        email = item.get("email", "")
        if email and not self.validar_email(email):
            email = None
        
        return SearchResult(
            nombre=nombre,
            tipo=item.get("tipo", "despacho"),
            telefono=telefonos,
            email=email,
            web=self.limpiar_url(item.get("web", "")),
            direccion=item.get("direccion"),
            ciudad=item.get("ciudad"),
            distrito=item.get("distrito"),
            especialidades=item.get("especialidades", []),
            fuente="firecrawl_extract",
            url_origen=url_origen,
        )
    
    def _extraer_de_texto(self, texto: str, url_origen: str) -> List[SearchResult]:
        """Extrae información básica de texto plano."""
        resultados = []
        
        # Patrones regex
        patron_tel = r'(?:\+34)?[\s.-]?[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}'
        patron_email = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        
        telefonos = re.findall(patron_tel, texto)
        emails = re.findall(patron_email, texto)
        
        if telefonos or emails:
            sr = SearchResult(
                nombre=f"Extraído de {url_origen.split('/')[-1]}",
                telefono=[self.normalizar_telefono(t) for t in telefonos[:5]],
                email=emails[0] if emails else None,
                fuente="firecrawl_text",
                url_origen=url_origen,
            )
            resultados.append(sr)
        
        return resultados
    
    def _extraer_contacto_de_texto(self, sr: SearchResult, texto: str):
        """Extrae datos de contacto de un texto y los añade al SearchResult."""
        if not texto:
            return
        
        # Teléfonos
        patron_tel = r'(?:\+34)?[\s.-]?[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}'
        telefonos = re.findall(patron_tel, texto)
        sr.telefono = [self.normalizar_telefono(t) for t in telefonos[:3]]
        
        # Email
        patron_email = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(patron_email, texto)
        if emails:
            sr.email = emails[0]
