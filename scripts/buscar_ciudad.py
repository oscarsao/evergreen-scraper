"""
Script para ejecutar búsquedas en una ciudad específica.
Uso: py scripts/buscar_ciudad.py <ciudad> [rondas]
"""
import sys
import os

# Configurar encoding para Windows
sys.stdout.reconfigure(encoding='utf-8')

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.orquestador import Orquestador, BusquedaConfig


def main():
    if len(sys.argv) < 2:
        print("Uso: py scripts/buscar_ciudad.py <ciudad> [rondas]")
        print("Ejemplo: py scripts/buscar_ciudad.py Barcelona 3")
        sys.exit(1)
    
    ciudad = sys.argv[1]
    rondas = int(sys.argv[2]) if len(sys.argv) > 2 else 2
    
    print(f"=== BUSQUEDA {ciudad.upper()} ===")
    print(f"Rondas planificadas: {rondas}")
    print("")
    
    orq = Orquestador()
    
    # Ejecutar multiples rondas
    for ronda in range(1, rondas + 1):
        print(f"\n--- RONDA {ronda}/{rondas} ---")
        config = BusquedaConfig(
            ciudad=ciudad,
            apis_habilitadas=["tavily", "firecrawl", "google_search"],
            max_resultados_por_api=30,
            usar_places=True,
            scraping_profundo=True
        )
        resultado = orq.ejecutar_busqueda(config)
    
    print("")
    print("=== RESULTADO FINAL ===")
    if resultado.consolidacion:
        print(f"Nuevos: {resultado.consolidacion.total_nuevos}")
        print(f"Actualizados: {len(resultado.consolidacion.actualizados)}")
        print(f"Duplicados: {len(resultado.consolidacion.duplicados_ignorados)}")
        print(f"Filtrados: {len(resultado.consolidacion.filtrados)}")
    print(f"Total procesados: {resultado.total_encontrados}")


if __name__ == "__main__":
    main()
