"""
Adapters para Google APIs.
- Google Custom Search API (100 búsquedas/día gratis)
- Google Places API ($200 crédito/mes gratis)
"""
import os
import re
from typing import List, Optional, Dict, Any
from .base import SearchAdapter, SearchResult

try:
    import requests
    REQUESTS_DISPONIBLE = True
except ImportError:
    REQUESTS_DISPONIBLE = False


class GoogleSearchAdapter(SearchAdapter):
    """Adapter para Google Custom Search API."""
    
    BASE_URL = "https://www.googleapis.com/customsearch/v1"
    
    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        super().__init__(api_key or os.getenv("GOOGLE_API_KEY"))
        self.cse_id = cse_id or os.getenv("GOOGLE_CSE_ID")
        self.nombre = "google_search"
        self.limite_requests = 100  # por día
    
    def esta_disponible(self) -> bool:
        return REQUESTS_DISPONIBLE and bool(self.api_key) and bool(self.cse_id)
    
    def search(self, query: str, num: int = 10, **kwargs) -> List[SearchResult]:
        """Búsqueda con Google Custom Search."""
        if not self.esta_disponible():
            return []
        
        resultados = []
        try:
            params = {
                "key": self.api_key,
                "cx": self.cse_id,
                "q": query,
                "num": min(num, 10),  # máximo 10 por request
                "lr": "lang_es",  # resultados en español
                "cr": "countryES",  # desde España
            }
            
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            self.incrementar_contador()
            
            if response.status_code == 200:
                data = response.json()
                resultados = self._procesar_resultados(data, query)
            else:
                print(f"[GoogleSearch] Error {response.status_code}: {response.text[:200]}")
                
        except Exception as e:
            print(f"[GoogleSearch] Error: {e}")
        
        return resultados
    
    def search_site(self, site: str, query: str, num: int = 10) -> List[SearchResult]:
        """Búsqueda restringida a un sitio específico."""
        query_completa = f"site:{site} {query}"
        return self.search(query_completa, num)
    
    def search_abogados_madrid(self, zona: str = "", especialidad: str = "") -> List[SearchResult]:
        """Búsqueda optimizada para abogados de extranjería en Madrid."""
        partes = ['"abogado extranjería"', "Madrid"]
        if zona:
            partes.append(f'"{zona}"')
        if especialidad:
            partes.append(f'"{especialidad}"')
        partes.append("(teléfono OR email OR contacto)")
        partes.append("-foro -pregunta")
        
        query = " ".join(partes)
        return self.search(query)
    
    def _procesar_resultados(self, data: Dict, query: str) -> List[SearchResult]:
        """Procesa respuesta de Google Search API."""
        resultados = []
        
        items = data.get("items", [])
        for item in items:
            nombre = item.get("title", "")
            link = item.get("link", "")
            snippet = item.get("snippet", "")
            
            if not nombre:
                continue
            
            # Limpiar nombre (quitar " - Abogados" y similares)
            nombre = re.sub(r'\s*[-|]\s*(Abogados?|Despacho|Bufete).*$', '', nombre)
            nombre = nombre.strip()
            
            sr = SearchResult(
                nombre=nombre,
                web=link,
                fuente="google_search",
                url_origen=link,
            )
            
            # Extraer datos del snippet
            self._extraer_de_snippet(sr, snippet)
            
            resultados.append(sr)
        
        return resultados
    
    def _extraer_de_snippet(self, sr: SearchResult, snippet: str):
        """Extrae teléfono y email del snippet."""
        if not snippet:
            return
        
        # Teléfonos españoles
        patron_tel = r'(?:\+34)?[\s.-]?[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}'
        telefonos = re.findall(patron_tel, snippet)
        if telefonos:
            sr.telefono = [self.normalizar_telefono(t) for t in telefonos[:2]]
        
        # Email
        patron_email = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(patron_email, snippet)
        if emails:
            sr.email = emails[0]
        
        # Dirección (patrón básico con código postal)
        patron_dir = r'(?:C/|Calle|Avda\.|Avenida|Plaza)\s+[^,]+,?\s*\d{5}'
        direcciones = re.findall(patron_dir, snippet, re.IGNORECASE)
        if direcciones:
            sr.direccion = direcciones[0]


class GooglePlacesAdapter(SearchAdapter):
    """Adapter para Google Places API."""
    
    BASE_URL = "https://maps.googleapis.com/maps/api/place"
    
    # Coordenadas de distritos de Madrid
    DISTRITOS_MADRID = {
        "centro": (40.4168, -3.7038),
        "salamanca": (40.4297, -3.6836),
        "chamberí": (40.4350, -3.7050),
        "retiro": (40.4110, -3.6830),
        "tetuán": (40.4600, -3.6980),
        "chamartín": (40.4620, -3.6770),
        "carabanchel": (40.3850, -3.7400),
        "usera": (40.3850, -3.7050),
        "latina": (40.4000, -3.7500),
        "vallecas": (40.3800, -3.6500),
        "arganzuela": (40.3950, -3.6950),
        "moncloa": (40.4350, -3.7200),
        "fuencarral": (40.4900, -3.7100),
        "hortaleza": (40.4750, -3.6400),
        "ciudad lineal": (40.4500, -3.6500),
        "san blas": (40.4300, -3.6100),
    }
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key or os.getenv("GOOGLE_API_KEY"))
        self.nombre = "google_places"
        # Places API tiene límite basado en créditos ($200/mes gratis)
        self.limite_requests = 1000
    
    def esta_disponible(self) -> bool:
        return REQUESTS_DISPONIBLE and bool(self.api_key)
    
    def search(self, query: str, **kwargs) -> List[SearchResult]:
        """Búsqueda general - usa search_nearby con centro de Madrid."""
        return self.search_nearby(
            query=query,
            lat=40.4168,
            lng=-3.7038,
            radius=15000
        )
    
    def search_nearby(
        self, 
        query: str, 
        lat: float, 
        lng: float, 
        radius: int = 5000
    ) -> List[SearchResult]:
        """Búsqueda de lugares cercanos a coordenadas."""
        if not self.esta_disponible():
            return []
        
        resultados = []
        try:
            url = f"{self.BASE_URL}/nearbysearch/json"
            params = {
                "key": self.api_key,
                "location": f"{lat},{lng}",
                "radius": radius,
                "keyword": query,
                "language": "es",
                "type": "lawyer",
            }
            
            response = requests.get(url, params=params, timeout=30)
            self.incrementar_contador()
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    resultados = self._procesar_places(data.get("results", []))
                elif data.get("status") == "ZERO_RESULTS":
                    pass  # Sin resultados, no es error
                else:
                    print(f"[GooglePlaces] Status: {data.get('status')}")
                    
        except Exception as e:
            print(f"[GooglePlaces] Error: {e}")
        
        return resultados
    
    def search_by_district(self, query: str, distrito: str) -> List[SearchResult]:
        """Búsqueda en un distrito específico de Madrid."""
        distrito_lower = distrito.lower()
        
        if distrito_lower in self.DISTRITOS_MADRID:
            lat, lng = self.DISTRITOS_MADRID[distrito_lower]
        else:
            # Si no conocemos el distrito, usar centro de Madrid
            lat, lng = 40.4168, -3.7038
        
        return self.search_nearby(query, lat, lng, radius=5000)
    
    def search_all_districts(self, query: str) -> List[SearchResult]:
        """Búsqueda en todos los distritos de Madrid."""
        todos_resultados = []
        place_ids_vistos = set()
        
        for distrito, (lat, lng) in self.DISTRITOS_MADRID.items():
            resultados = self.search_nearby(query, lat, lng, radius=3000)
            
            # Filtrar duplicados por place_id
            for r in resultados:
                place_id = getattr(r, '_place_id', r.nombre)
                if place_id not in place_ids_vistos:
                    place_ids_vistos.add(place_id)
                    r.distrito = distrito.title()
                    todos_resultados.append(r)
        
        return todos_resultados
    
    def get_details(self, place_id: str) -> Optional[SearchResult]:
        """Obtiene detalles completos de un lugar."""
        if not self.esta_disponible():
            return None
        
        try:
            url = f"{self.BASE_URL}/details/json"
            params = {
                "key": self.api_key,
                "place_id": place_id,
                "fields": "name,formatted_address,formatted_phone_number,website,rating,reviews,opening_hours,types",
                "language": "es",
            }
            
            response = requests.get(url, params=params, timeout=30)
            self.incrementar_contador()
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "OK":
                    return self._place_detail_to_result(data.get("result", {}))
                    
        except Exception as e:
            print(f"[GooglePlaces] Error obteniendo detalles: {e}")
        
        return None
    
    def _procesar_places(self, places: List[Dict]) -> List[SearchResult]:
        """Procesa lista de lugares de Google Places."""
        resultados = []
        
        for place in places:
            nombre = place.get("name", "")
            if not nombre:
                continue
            
            sr = SearchResult(
                nombre=nombre,
                direccion=place.get("vicinity", place.get("formatted_address")),
                valoracion=place.get("rating"),
                ciudad="Madrid",
                fuente="google_places",
            )
            
            # Guardar place_id para obtener detalles después
            sr._place_id = place.get("place_id", "")
            
            # Tipos pueden indicar especialización
            types = place.get("types", [])
            if "lawyer" in types:
                sr.tipo = "despacho"
            
            resultados.append(sr)
        
        return resultados
    
    def _place_detail_to_result(self, detail: Dict) -> SearchResult:
        """Convierte detalle de lugar a SearchResult."""
        telefono = detail.get("formatted_phone_number", "")
        
        return SearchResult(
            nombre=detail.get("name", ""),
            telefono=[self.normalizar_telefono(telefono)] if telefono else [],
            web=detail.get("website", ""),
            direccion=detail.get("formatted_address", ""),
            valoracion=detail.get("rating"),
            ciudad="Madrid",
            fuente="google_places_detail",
        )
    
    def enriquecer_con_detalles(self, resultados: List[SearchResult]) -> List[SearchResult]:
        """Enriquece resultados con detalles completos (consume más API calls)."""
        enriquecidos = []
        
        for r in resultados:
            place_id = getattr(r, '_place_id', None)
            if place_id:
                detalle = self.get_details(place_id)
                if detalle:
                    # Fusionar datos
                    if detalle.telefono:
                        r.telefono = detalle.telefono
                    if detalle.web:
                        r.web = detalle.web
                    if detalle.direccion:
                        r.direccion = detalle.direccion
                    if detalle.valoracion:
                        r.valoracion = detalle.valoracion
            
            enriquecidos.append(r)
        
        return enriquecidos
