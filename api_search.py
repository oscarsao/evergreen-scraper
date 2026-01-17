"""
Módulo de Búsqueda con APIs Externas
====================================
Integra múltiples APIs de búsqueda IA para enriquecer datos.
Soporta: Tavily, SerpAPI, OpenAI (con browsing)
"""

import json
import os
from datetime import datetime
from typing import Optional

# Intentar importar las librerías opcionales
try:
    from tavily import TavilyClient
    TAVILY_DISPONIBLE = True
except ImportError:
    TAVILY_DISPONIBLE = False

try:
    import openai
    OPENAI_DISPONIBLE = True
except ImportError:
    OPENAI_DISPONIBLE = False

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class BuscadorAbogados:
    """
    Buscador de abogados usando múltiples APIs de IA.
    Mucho más eficiente que scraping tradicional.
    """
    
    def __init__(self):
        self.tavily_client = None
        self.openai_client = None
        
        # Inicializar Tavily si está disponible
        if TAVILY_DISPONIBLE:
            api_key = os.getenv("TAVILY_API_KEY")
            if api_key:
                self.tavily_client = TavilyClient(api_key=api_key)
                print("   [OK] Tavily API configurada")
            else:
                print("   [!] TAVILY_API_KEY no configurada")
        
        # Inicializar OpenAI si está disponible
        if OPENAI_DISPONIBLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                print("   [OK] OpenAI API configurada")
            else:
                print("   [!] OPENAI_API_KEY no configurada")
    
    def buscar_con_tavily(
        self, 
        query: str = "abogados extranjería Madrid contacto teléfono email",
        max_results: int = 10
    ) -> list:
        """
        Búsqueda con Tavily API (diseñada para agentes IA).
        
        Tavily es muy eficiente para obtener datos estructurados.
        Coste aproximado: $0.01 por búsqueda.
        
        Args:
            query: Consulta de búsqueda
            max_results: Número máximo de resultados
            
        Returns:
            Lista de resultados con datos extraídos
        """
        if not self.tavily_client:
            print("   [!] Tavily no disponible. Instala: pip install tavily-python")
            return []
        
        print(f"   [>>] Buscando con Tavily: '{query[:50]}...'")
        
        try:
            # Búsqueda con extracción de contenido
            response = self.tavily_client.search(
                query=query,
                search_depth="advanced",  # Búsqueda profunda
                max_results=max_results,
                include_answer=True,  # Incluye resumen IA
                include_raw_content=False  # Solo datos procesados
            )
            
            resultados = []
            
            # Procesar respuesta IA
            if response.get("answer"):
                print(f"   [OK] Resumen IA obtenido")
            
            # Procesar resultados individuales
            for item in response.get("results", []):
                resultado = {
                    "titulo": item.get("title", ""),
                    "url": item.get("url", ""),
                    "contenido": item.get("content", ""),
                    "score": item.get("score", 0),
                    "fuente": "tavily"
                }
                resultados.append(resultado)
            
            print(f"   [OK] {len(resultados)} resultados de Tavily")
            return resultados
            
        except Exception as e:
            print(f"   [ERROR] Tavily: {str(e)}")
            return []
    
    def buscar_con_openai(
        self,
        query: str = "Dame una lista de abogados de extranjería en Madrid con teléfono y email",
        modelo: str = "gpt-4o-mini"
    ) -> dict:
        """
        Búsqueda con OpenAI (requiere modelo con browsing o datos de entrenamiento).
        
        Útil para obtener datos estructurados y razonados.
        
        Args:
            query: Consulta en lenguaje natural
            modelo: Modelo a usar (gpt-4o-mini es más económico)
            
        Returns:
            Diccionario con respuesta estructurada
        """
        if not self.openai_client:
            print("   [!] OpenAI no disponible. Instala: pip install openai")
            return {}
        
        print(f"   [>>] Consultando OpenAI...")
        
        try:
            response = self.openai_client.chat.completions.create(
                model=modelo,
                messages=[
                    {
                        "role": "system",
                        "content": """Eres un asistente experto en encontrar información de contacto de profesionales.
                        Responde SIEMPRE en formato JSON con la estructura:
                        {
                            "abogados": [
                                {
                                    "nombre": "...",
                                    "despacho": "...",
                                    "telefono": "...",
                                    "email": "...",
                                    "direccion": "...",
                                    "web": "...",
                                    "especialidades": ["..."]
                                }
                            ]
                        }
                        Si no tienes datos verificados, indica null en el campo."""
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            contenido = response.choices[0].message.content
            datos = json.loads(contenido)
            
            num_abogados = len(datos.get("abogados", []))
            print(f"   [OK] {num_abogados} resultados de OpenAI")
            
            return datos
            
        except Exception as e:
            print(f"   [ERROR] OpenAI: {str(e)}")
            return {}
    
    def buscar_y_combinar(
        self,
        query: str = "abogados extranjería Madrid",
        usar_tavily: bool = True,
        usar_openai: bool = True
    ) -> dict:
        """
        Combina resultados de múltiples fuentes.
        
        Args:
            query: Consulta de búsqueda
            usar_tavily: Usar Tavily API
            usar_openai: Usar OpenAI API
            
        Returns:
            Diccionario con todos los resultados combinados
        """
        resultados = {
            "metadata": {
                "query": query,
                "fecha": datetime.now().isoformat(),
                "fuentes": []
            },
            "tavily": [],
            "openai": {},
            "combinados": []
        }
        
        if usar_tavily and self.tavily_client:
            resultados["tavily"] = self.buscar_con_tavily(query)
            resultados["metadata"]["fuentes"].append("tavily")
        
        if usar_openai and self.openai_client:
            query_openai = f"Lista de {query} con teléfono, email y dirección de contacto"
            resultados["openai"] = self.buscar_con_openai(query_openai)
            resultados["metadata"]["fuentes"].append("openai")
        
        return resultados
    
    def guardar_resultados(self, resultados: dict, filepath: str):
        """Guarda los resultados en JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(resultados, f, ensure_ascii=False, indent=2)
        print(f"   [OK] Resultados guardados: {filepath}")


def mostrar_apis_disponibles():
    """Muestra qué APIs están configuradas."""
    print("\n" + "=" * 60)
    print("   APIS DE BUSQUEDA DISPONIBLES")
    print("=" * 60)
    
    # Tavily
    print(f"\n   TAVILY (Recomendada para agentes IA)")
    print(f"   - Instalada: {'Sí' if TAVILY_DISPONIBLE else 'No (pip install tavily-python)'}")
    print(f"   - API Key: {'Configurada' if os.getenv('TAVILY_API_KEY') else 'No (TAVILY_API_KEY en .env)'}")
    print(f"   - Coste: ~$0.01/búsqueda")
    print(f"   - Web: https://tavily.com")
    
    # OpenAI
    print(f"\n   OPENAI")
    print(f"   - Instalada: {'Sí' if OPENAI_DISPONIBLE else 'No (pip install openai)'}")
    print(f"   - API Key: {'Configurada' if os.getenv('OPENAI_API_KEY') else 'No (OPENAI_API_KEY en .env)'}")
    print(f"   - Coste: Variable según modelo")
    
    # Firecrawl (ya existente)
    print(f"\n   FIRECRAWL (Ya configurado)")
    print(f"   - API Key: {'Configurada' if os.getenv('FIRECRAWL_API_KEY') else 'No'}")
    print(f"   - Útil para: Scraping de páginas específicas")
    
    print("\n" + "=" * 60)


def ejemplo_uso():
    """Ejemplo de uso del buscador."""
    print("=" * 60)
    print("   EJEMPLO DE BUSQUEDA CON APIS")
    print("=" * 60)
    
    buscador = BuscadorAbogados()
    
    # Si hay alguna API disponible, hacer búsqueda de prueba
    if buscador.tavily_client or buscador.openai_client:
        resultados = buscador.buscar_y_combinar(
            query="abogados extranjería Madrid nacionalidad arraigo",
            usar_tavily=bool(buscador.tavily_client),
            usar_openai=bool(buscador.openai_client)
        )
        
        # Guardar resultados
        os.makedirs("data", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"data/busqueda_api_{timestamp}.json"
        buscador.guardar_resultados(resultados, filepath)
    else:
        print("\n   [!] No hay APIs configuradas.")
        print("   Configura al menos una en el archivo .env")
    
    print("=" * 60)


if __name__ == "__main__":
    mostrar_apis_disponibles()
    print()
    ejemplo_uso()
