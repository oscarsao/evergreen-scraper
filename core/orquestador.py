"""
Orquestador del sistema multi-agente.
Coordina búsquedas paralelas, selección de APIs y pipeline completo.
"""
import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Cargar variables de entorno ANTES de importar adapters
from dotenv import load_dotenv
load_dotenv()

# Soporte para Streamlit Cloud secrets
def _cargar_streamlit_secrets():
    """Carga secrets de Streamlit Cloud si están disponibles."""
    try:
        import streamlit as st
        if hasattr(st, 'secrets'):
            for key in ['FIRECRAWL_API_KEY', 'GOOGLE_API_KEY', 'GOOGLE_CSE_ID', 
                       'TAVILY_API_KEY', 'OPENAI_API_KEY']:
                if key in st.secrets and not os.getenv(key):
                    os.environ[key] = st.secrets[key]
    except:
        pass  # No estamos en Streamlit

_cargar_streamlit_secrets()

from adapters import (
    SearchAdapter, SearchResult,
    FirecrawlAdapter, GoogleSearchAdapter, GooglePlacesAdapter,
    TavilyAdapter, OpenAIAdapter
)
from core.consolidador import Consolidador, ConsolidacionResult
from prompts.busqueda import PROMPTS_BUSQUEDA, URLS_DIRECTORIOS, get_prompts_ciudad


@dataclass
class BusquedaConfig:
    """Configuración para una búsqueda."""
    ciudad: str
    zonas: List[str] = field(default_factory=list)
    apis_habilitadas: List[str] = field(default_factory=lambda: ["tavily", "firecrawl"])
    max_resultados_por_api: int = 20
    usar_places: bool = True
    scraping_profundo: bool = True


@dataclass
class ResultadoBusqueda:
    """Resultado de una ejecución de búsqueda."""
    ciudad: str
    fecha: str
    resultados_por_api: Dict[str, int] = field(default_factory=dict)
    total_encontrados: int = 0
    consolidacion: Optional[ConsolidacionResult] = None
    errores: List[str] = field(default_factory=list)
    duracion_segundos: float = 0


class Orquestador:
    """
    Coordinador principal del sistema de búsqueda.
    
    Pipeline:
    1. Búsqueda amplia (Google/Tavily)
    2. Filtrar URLs relevantes
    3. Scraping profundo (Firecrawl)
    4. Extracción estructurada
    5. Consolidación y guardado
    """
    
    def __init__(self, config_path: str = None, data_dir: str = "data"):
        """
        Inicializa el orquestador.
        
        Args:
            config_path: Ruta al archivo de configuración
            data_dir: Directorio para datos
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Cargar configuración
        self.config = self._cargar_config(config_path)
        
        # Inicializar adapters
        self.adapters: Dict[str, SearchAdapter] = {}
        self._inicializar_adapters()
        
        # Consolidador (se inicializa por ciudad)
        self.consolidador: Optional[Consolidador] = None
    
    def _cargar_config(self, config_path: str) -> Dict:
        """Carga configuración desde archivo o usa defaults."""
        default_config = {
            "apis": {
                "firecrawl": {"habilitado": True, "prioridad": 1},
                "google_search": {"habilitado": True, "prioridad": 2},
                "google_places": {"habilitado": True, "prioridad": 3},
                "tavily": {"habilitado": True, "prioridad": 4},
                "openai": {"habilitado": True, "prioridad": 5},
            },
            "busqueda": {
                "max_resultados_por_query": 10,
                "delay_entre_requests": 1,
                "max_paralelo": 3,
            }
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                # Merge con defaults
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
            except Exception as e:
                print(f"[Orquestador] Error cargando config: {e}")
        
        return default_config
    
    def _inicializar_adapters(self):
        """Inicializa todos los adapters disponibles."""
        # Firecrawl
        if self.config["apis"].get("firecrawl", {}).get("habilitado", True):
            adapter = FirecrawlAdapter()
            if adapter.esta_disponible():
                self.adapters["firecrawl"] = adapter
                print("[Orquestador] ✓ Firecrawl disponible")
        
        # Google Search
        if self.config["apis"].get("google_search", {}).get("habilitado", True):
            adapter = GoogleSearchAdapter()
            if adapter.esta_disponible():
                self.adapters["google_search"] = adapter
                print("[Orquestador] ✓ Google Search disponible")
        
        # Google Places
        if self.config["apis"].get("google_places", {}).get("habilitado", True):
            adapter = GooglePlacesAdapter()
            if adapter.esta_disponible():
                self.adapters["google_places"] = adapter
                print("[Orquestador] ✓ Google Places disponible")
        
        # Tavily
        if self.config["apis"].get("tavily", {}).get("habilitado", True):
            adapter = TavilyAdapter()
            if adapter.esta_disponible():
                self.adapters["tavily"] = adapter
                print("[Orquestador] ✓ Tavily disponible")
        
        # OpenAI
        if self.config["apis"].get("openai", {}).get("habilitado", True):
            adapter = OpenAIAdapter()
            if adapter.esta_disponible():
                self.adapters["openai"] = adapter
                print("[Orquestador] ✓ OpenAI disponible")
        
        if not self.adapters:
            print("[Orquestador] ⚠ No hay APIs configuradas")
    
    def apis_disponibles(self) -> List[str]:
        """Devuelve lista de APIs disponibles."""
        return list(self.adapters.keys())
    
    def ejecutar_busqueda(self, config: BusquedaConfig) -> ResultadoBusqueda:
        """
        Ejecuta búsqueda completa para una ciudad.
        
        Args:
            config: Configuración de la búsqueda
            
        Returns:
            ResultadoBusqueda con estadísticas
        """
        inicio = datetime.now()
        resultado = ResultadoBusqueda(
            ciudad=config.ciudad,
            fecha=inicio.isoformat()
        )
        
        # Inicializar consolidador para esta ciudad
        db_path = self.data_dir / f"{config.ciudad.lower()}.json"
        self.consolidador = Consolidador(str(db_path))
        
        todos_resultados: List[SearchResult] = []
        
        try:
            # Paso 1: Búsqueda con APIs de búsqueda
            print(f"\n[Orquestador] === Buscando en {config.ciudad} ===")
            
            # Obtener prompts para la ciudad
            prompts = get_prompts_ciudad(config.ciudad)
            if not prompts:
                prompts = [f"abogado extranjería {config.ciudad} contacto teléfono"]
            
            # Búsqueda paralela con diferentes APIs
            for api_nombre in config.apis_habilitadas:
                if api_nombre not in self.adapters:
                    continue
                
                adapter = self.adapters[api_nombre]
                print(f"\n[{api_nombre}] Ejecutando búsquedas...")
                
                resultados_api = self._buscar_con_adapter(
                    adapter, 
                    prompts[:5],  # Limitar prompts por API
                    config.max_resultados_por_api
                )
                
                resultado.resultados_por_api[api_nombre] = len(resultados_api)
                todos_resultados.extend(resultados_api)
                print(f"[{api_nombre}] Encontrados: {len(resultados_api)}")
            
            # Paso 2: Google Places si está habilitado
            if config.usar_places and "google_places" in self.adapters:
                print("\n[google_places] Buscando negocios locales...")
                places_adapter = self.adapters["google_places"]
                
                resultados_places = places_adapter.search(
                    f"abogado extranjería {config.ciudad}"
                )
                resultado.resultados_por_api["google_places"] = len(resultados_places)
                todos_resultados.extend(resultados_places)
                print(f"[google_places] Encontrados: {len(resultados_places)}")
            
            # Paso 3: Scraping profundo con Firecrawl
            if config.scraping_profundo and "firecrawl" in self.adapters:
                print("\n[firecrawl] Scraping de directorios...")
                firecrawl = self.adapters["firecrawl"]
                
                # URLs de directorios para la ciudad
                urls = URLS_DIRECTORIOS.get(config.ciudad.lower(), [])
                urls.extend(URLS_DIRECTORIOS.get("generales", [])[:2])
                
                for url in urls[:3]:  # Limitar scraping
                    try:
                        resultados_scrape = firecrawl.extract_structured([url])
                        todos_resultados.extend(resultados_scrape)
                    except Exception as e:
                        resultado.errores.append(f"Error scraping {url}: {e}")
            
            # Paso 4: Consolidación con filtrado automático
            print(f"\n[Consolidador] Procesando {len(todos_resultados)} resultados con filtros...")
            
            # Convertir SearchResult a dict
            registros = [
                r.to_dict() if isinstance(r, SearchResult) else r 
                for r in todos_resultados
            ]
            
            # Procesar batch con filtrado verbose
            consolidacion = self.consolidador.procesar_batch(registros, verbose=True)
            resultado.consolidacion = consolidacion
            resultado.total_encontrados = len(todos_resultados)
            
            # Guardar
            self.consolidador.guardar()
            
            # Estadísticas
            stats = self.consolidador.estadisticas()
            print(f"\n[Resultado] Ciudad: {config.ciudad}")
            print(f"  - Total en BD: {stats['total']}")
            print(f"  - Nuevos agregados: {consolidacion.total_nuevos}")
            print(f"  - Actualizados: {len(consolidacion.actualizados)}")
            print(f"  - Duplicados: {len(consolidacion.duplicados_ignorados)}")
            print(f"  - Filtrados (rechazados): {len(consolidacion.filtrados)}")
            
            # Mostrar razones de filtrado si hay
            if consolidacion.razones_filtrado:
                print(f"\n[Filtrado] Razones:")
                for razon, count in sorted(consolidacion.razones_filtrado.items(), key=lambda x: -x[1])[:5]:
                    print(f"  - {razon}: {count}")
            
        except Exception as e:
            resultado.errores.append(f"Error general: {e}")
            print(f"[Orquestador] Error: {e}")
        
        resultado.duracion_segundos = (datetime.now() - inicio).total_seconds()
        return resultado
    
    def _buscar_con_adapter(
        self, 
        adapter: SearchAdapter, 
        prompts: List[str],
        max_total: int
    ) -> List[SearchResult]:
        """Ejecuta múltiples búsquedas con un adapter."""
        resultados = []
        
        for prompt in prompts:
            if len(resultados) >= max_total:
                break
            
            if not adapter.dentro_de_limite():
                print(f"  [{adapter.nombre}] Límite alcanzado")
                break
            
            try:
                res = adapter.search(prompt, max_results=10)
                resultados.extend(res)
            except Exception as e:
                print(f"  [{adapter.nombre}] Error en búsqueda: {e}")
        
        return resultados[:max_total]
    
    def ejecutar_multiciudad(
        self, 
        ciudades: List[str],
        paralelo: bool = False
    ) -> Dict[str, ResultadoBusqueda]:
        """
        Ejecuta búsqueda en múltiples ciudades.
        
        Args:
            ciudades: Lista de ciudades
            paralelo: Si ejecutar en paralelo
            
        Returns:
            Dict de ciudad -> ResultadoBusqueda
        """
        resultados = {}
        
        if paralelo:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {
                    executor.submit(
                        self.ejecutar_busqueda,
                        BusquedaConfig(ciudad=ciudad)
                    ): ciudad
                    for ciudad in ciudades
                }
                
                for future in as_completed(futures):
                    ciudad = futures[future]
                    try:
                        resultados[ciudad] = future.result()
                    except Exception as e:
                        print(f"Error en {ciudad}: {e}")
        else:
            for ciudad in ciudades:
                config = BusquedaConfig(ciudad=ciudad)
                resultados[ciudad] = self.ejecutar_busqueda(config)
        
        return resultados
    
    def generar_reporte(self, resultados: Dict[str, ResultadoBusqueda]) -> str:
        """Genera reporte de texto de los resultados."""
        lineas = [
            "=" * 60,
            "REPORTE DE BÚSQUEDA MULTI-AGENTE",
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
            ""
        ]
        
        total_encontrados = 0
        total_nuevos = 0
        
        for ciudad, res in resultados.items():
            lineas.append(f"\n📍 {ciudad.upper()}")
            lineas.append("-" * 40)
            lineas.append(f"  Encontrados: {res.total_encontrados}")
            
            if res.consolidacion:
                lineas.append(f"  Nuevos: {res.consolidacion.total_nuevos}")
                lineas.append(f"  Actualizados: {len(res.consolidacion.actualizados)}")
                lineas.append(f"  Duplicados: {len(res.consolidacion.duplicados_ignorados)}")
                total_nuevos += res.consolidacion.total_nuevos
            
            lineas.append(f"  Duración: {res.duracion_segundos:.1f}s")
            
            if res.resultados_por_api:
                lineas.append("  Por API:")
                for api, count in res.resultados_por_api.items():
                    lineas.append(f"    - {api}: {count}")
            
            if res.errores:
                lineas.append("  ⚠ Errores:")
                for error in res.errores[:3]:
                    lineas.append(f"    - {error[:50]}...")
            
            total_encontrados += res.total_encontrados
        
        lineas.extend([
            "",
            "=" * 60,
            "RESUMEN TOTAL",
            "=" * 60,
            f"Ciudades procesadas: {len(resultados)}",
            f"Total encontrados: {total_encontrados}",
            f"Total nuevos agregados: {total_nuevos}",
        ])
        
        return "\n".join(lineas)


def main():
    """Función principal para ejecutar desde CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Orquestador de búsqueda multi-agente")
    parser.add_argument("--ciudad", "-c", default="Madrid", help="Ciudad a buscar")
    parser.add_argument("--ciudades", "-m", nargs="+", help="Múltiples ciudades")
    parser.add_argument("--config", help="Ruta al archivo de configuración")
    parser.add_argument("--paralelo", "-p", action="store_true", help="Ejecutar en paralelo")
    
    args = parser.parse_args()
    
    # Crear orquestador
    orquestador = Orquestador(config_path=args.config)
    
    print("\n" + "=" * 60)
    print("SISTEMA MULTI-AGENTE DE BÚSQUEDA")
    print("=" * 60)
    print(f"APIs disponibles: {', '.join(orquestador.apis_disponibles())}")
    
    if args.ciudades:
        # Múltiples ciudades
        resultados = orquestador.ejecutar_multiciudad(args.ciudades, args.paralelo)
    else:
        # Una ciudad
        config = BusquedaConfig(ciudad=args.ciudad)
        resultados = {args.ciudad: orquestador.ejecutar_busqueda(config)}
    
    # Mostrar reporte
    print(orquestador.generar_reporte(resultados))


if __name__ == "__main__":
    main()
