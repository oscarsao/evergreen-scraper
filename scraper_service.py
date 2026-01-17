"""
Servicio de Web Scraping con Firecrawl
======================================
Este módulo proporciona una clase para extraer datos de diferentes sitios web
utilizando la API de Firecrawl v4.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

# Cargar variables de entorno
load_dotenv()


class ScraperService:
    """Servicio principal de web scraping usando Firecrawl."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el servicio de scraping.
        
        Args:
            api_key: API key de Firecrawl. Si no se proporciona, 
                     se busca en la variable de entorno FIRECRAWL_API_KEY.
        """
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Se requiere una API key de Firecrawl. "
                "Proporciónala como argumento o configura FIRECRAWL_API_KEY en .env"
            )
        self.app = FirecrawlApp(api_key=self.api_key)

    def scrape_url(
        self,
        url: str,
        formats: list[str] = ["markdown"],
        only_main_content: bool = True
    ) -> dict:
        """
        Extrae el contenido de una URL específica.
        
        Args:
            url: La URL a scrapear.
            formats: Lista de formatos deseados ("markdown", "html", "rawHtml", "links", "screenshot").
            only_main_content: Si es True, extrae solo el contenido principal.
            
        Returns:
            Diccionario con el contenido extraído.
        """
        result = self.app.scrape(
            url,
            formats=formats,
            only_main_content=only_main_content
        )
        return result

    def crawl_site(
        self,
        url: str,
        max_depth: int = 2,
        limit: int = 10,
        formats: list[str] = ["markdown"]
    ) -> dict:
        """
        Rastrea un sitio web completo desde una URL base.
        
        Args:
            url: URL base para iniciar el crawl.
            max_depth: Profundidad máxima de navegación.
            limit: Número máximo de páginas a crawlear.
            formats: Formatos de salida deseados.
            
        Returns:
            Diccionario con todos los datos extraídos.
        """
        result = self.app.crawl(
            url,
            limit=limit,
            max_depth=max_depth,
            scrape_options={"formats": formats}
        )
        return result

    def map_site(self, url: str, limit: int = 100) -> dict:
        """
        Obtiene un mapa de todas las URLs de un sitio.
        
        Args:
            url: URL base del sitio.
            limit: Número máximo de URLs a mapear.
            
        Returns:
            Diccionario con la lista de URLs encontradas.
        """
        result = self.app.map(url, limit=limit)
        return result

    def search(self, query: str, limit: int = 10) -> dict:
        """
        Busca en la web y opcionalmente scrapea los resultados.
        
        Args:
            query: Término de búsqueda.
            limit: Número máximo de resultados.
            
        Returns:
            Diccionario con los resultados de búsqueda.
        """
        result = self.app.search(query, limit=limit)
        return result

    def extract_structured_data(
        self,
        urls: list[str],
        schema: dict,
        prompt: Optional[str] = None
    ) -> dict:
        """
        Extrae datos estructurados de múltiples URLs usando un esquema.
        
        Args:
            urls: Lista de URLs de las cuales extraer datos.
            schema: Esquema JSON que define la estructura de datos deseada.
            prompt: Prompt opcional para guiar la extracción con IA.
            
        Returns:
            Diccionario con los datos estructurados extraídos.
        """
        result = self.app.extract(
            urls=urls,
            schema=schema,
            prompt=prompt
        )
        return result


# Ejemplo de esquema para extracción estructurada (como diccionario JSON)
PRODUCT_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "price": {"type": "string"},
        "description": {"type": "string"},
        "image_url": {"type": "string"}
    },
    "required": ["name"]
}


def main():
    """Función principal con ejemplos de uso."""
    
    # Inicializar el servicio
    scraper = ScraperService()
    
    # Ejemplo 1: Scrapear una URL simple
    print("=" * 50)
    print("Ejemplo 1: Scraping de una URL")
    print("=" * 50)
    
    url = "https://example.com"
    result = scraper.scrape_url(url, formats=["markdown", "links"])
    
    print(f"URL: {url}")
    print(f"Contenido (primeros 500 caracteres):")
    
    # Acceder al contenido según la estructura de respuesta
    markdown_content = result.get("markdown", "") if isinstance(result, dict) else getattr(result, "markdown", "")
    if markdown_content:
        print(markdown_content[:500] if len(markdown_content) > 500 else markdown_content)
    else:
        print("No se encontró contenido markdown")
    
    # Ejemplo 2: Mapear URLs de un sitio
    print("\n" + "=" * 50)
    print("Ejemplo 2: Mapa de URLs del sitio")
    print("=" * 50)
    
    site_map = scraper.map_site(url, limit=10)
    print(f"URLs encontradas: {site_map}")
    
    print("\nServicio de scraping funcionando correctamente!")


if __name__ == "__main__":
    main()
