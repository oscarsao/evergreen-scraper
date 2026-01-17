"""
Scraper de Abogados de Extranjería en Madrid
=============================================
Optimizado para bajo consumo de créditos de Firecrawl.
Exporta resultados a CSV y PDF.
"""

import sys
import io

# Configurar encoding para Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import csv
import json
import os
import re
import time
from datetime import datetime
from typing import Optional

from fpdf import FPDF
from scraper_service import ScraperService


# Carpeta de salida
OUTPUT_DIR = "resultados"


class AbogadoPDF(FPDF):
    """Clase personalizada para generar PDF con formato profesional."""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(25, 55, 95)
        self.cell(0, 10, "Directorio de Abogados de Extranjeria", align="C", ln=True)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "Madrid, Espana", align="C", ln=True)
        self.ln(5)
        self.set_draw_color(25, 55, 95)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}} | Generado el {datetime.now().strftime('%d/%m/%Y')}", align="C")
    
    def limpiar_texto(self, texto: str) -> str:
        """Limpia caracteres no compatibles con la fuente."""
        # Reemplazar caracteres especiales comunes
        reemplazos = {
            '【': '[', '】': ']', '▷': '>', '►': '>',
            '★': '*', '☆': '*', '●': '-', '○': '-',
            '→': '->', '←': '<-', '↑': '^', '↓': 'v',
            '€': 'EUR', '£': 'GBP', '¥': 'JPY',
            '"': '"', '"': '"', ''': "'", ''': "'",
            '–': '-', '—': '-', '…': '...',
        }
        for char, reemplazo in reemplazos.items():
            texto = texto.replace(char, reemplazo)
        # Eliminar cualquier otro caracter no latin-1
        return texto.encode('latin-1', errors='replace').decode('latin-1')
    
    def agregar_abogado(self, abogado: dict, numero: int):
        """Agrega un abogado al PDF con formato visual."""
        if self.get_y() > 240:
            self.add_page()
        
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(25, 55, 95)
        nombre = self.limpiar_texto(abogado.get("nombre", "Sin nombre"))
        self.cell(0, 8, f"{numero}. {nombre}", ln=True)
        
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 100, self.get_y())
        self.ln(3)
        
        self.set_font("Helvetica", "", 10)
        self.set_text_color(60, 60, 60)
        
        campos = [
            ("Despacho", abogado.get("despacho", "-")),
            ("Telefono", abogado.get("telefono", "-")),
            ("Email", abogado.get("email", "-")),
            ("Direccion", abogado.get("direccion", "-")),
            ("Web", abogado.get("web", "-")),
        ]
        
        for etiqueta, valor in campos:
            if valor and valor != "-":
                self.set_font("Helvetica", "B", 9)
                self.cell(25, 6, f"{etiqueta}:")
                self.set_font("Helvetica", "", 9)
                valor_limpio = self.limpiar_texto(str(valor))
                valor_mostrar = valor_limpio[:80] + "..." if len(valor_limpio) > 80 else valor_limpio
                self.cell(0, 6, valor_mostrar, ln=True)
        
        self.ln(8)


def extraer_datos_de_markdown(markdown: str, url: str, titulo: str = "") -> dict:
    """
    Extrae datos estructurados del contenido markdown.
    """
    abogado = {
        "nombre": titulo or "",
        "despacho": "",
        "telefono": "",
        "email": "",
        "direccion": "",
        "web": url,
        "fuente": url
    }
    
    # Buscar nombre si no viene del título
    if not abogado["nombre"]:
        nombre_match = re.search(r'^#\s*(.+?)$', markdown, re.MULTILINE)
        if nombre_match:
            abogado["nombre"] = nombre_match.group(1).strip()
    
    # Buscar teléfono
    telefono_patterns = [
        r'(?:tel[éeè]fono|tel|phone|móvil|movil)[:\s]*([+\d\s\-\(\)]{9,})',
        r'(\+34[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{3})',
        r'(\d{3}[\s\-]?\d{3}[\s\-]?\d{3})',
    ]
    for pattern in telefono_patterns:
        match = re.search(pattern, markdown, re.IGNORECASE)
        if match:
            abogado["telefono"] = match.group(1).strip()
            break
    
    # Buscar email
    email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', markdown)
    if email_match:
        abogado["email"] = email_match.group(0)
    
    # Buscar dirección
    direccion_patterns = [
        r'(?:direcci[óo]n|address|ubicaci[óo]n)[:\s]*([^|\n]{10,80})',
        r'((?:calle|c/|avda|avenida|plaza|paseo)\s+[^|\n]{5,60})',
        r'(Madrid[^|\n]{5,40}\d{5})',
    ]
    for pattern in direccion_patterns:
        match = re.search(pattern, markdown, re.IGNORECASE)
        if match:
            abogado["direccion"] = match.group(1).strip()
            break
    
    # Buscar despacho/bufete
    despacho_patterns = [
        r'(?:despacho|bufete|firma|gabinete)[:\s]*([^|\n]{5,60})',
    ]
    for pattern in despacho_patterns:
        match = re.search(pattern, markdown, re.IGNORECASE)
        if match:
            abogado["despacho"] = match.group(1).strip()
            break
    
    return abogado


def guardar_csv(abogados: list, filepath: str):
    """Guarda la lista de abogados en formato CSV."""
    if not abogados:
        print("   [!] No hay abogados para guardar en CSV")
        return
    
    campos = ["nombre", "despacho", "telefono", "email", "direccion", "web", "fuente"]
    
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(abogados)
    
    print(f"   [OK] CSV guardado: {filepath}")


def guardar_pdf(abogados: list, filepath: str):
    """Genera un PDF profesional con la lista de abogados."""
    if not abogados:
        print("   [!] No hay abogados para guardar en PDF")
        return
    
    pdf = AbogadoPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, f"Total de abogados encontrados: {len(abogados)}", ln=True)
    pdf.ln(5)
    
    for i, abogado in enumerate(abogados, 1):
        pdf.agregar_abogado(abogado, i)
    
    pdf.output(filepath)
    print(f"   [OK] PDF guardado: {filepath}")


def guardar_json(abogados: list, filepath: str):
    """Guarda los datos en formato JSON para backup."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(abogados, f, ensure_ascii=False, indent=2)
    print(f"   [OK] JSON guardado: {filepath}")


def scrapear_abogados_con_search(
    query: str = "abogados extranjeria madrid",
    limite: int = 20,
    delay: float = 3.0
) -> list:
    """
    Usa la función SEARCH de Firecrawl para encontrar abogados.
    Esto es más eficiente que map+scrape.
    
    Args:
        query: Término de búsqueda.
        limite: Número máximo de resultados.
        delay: Segundos entre requests.
    
    Returns:
        Lista de diccionarios con datos de abogados.
    """
    print("=" * 60)
    print("   SCRAPER DE ABOGADOS DE EXTRANJERIA - MADRID")
    print("=" * 60)
    print(f"   Configuracion:")
    print(f"   - Busqueda: {query}")
    print(f"   - Limite: {limite} resultados")
    print(f"   - Delay: {delay}s entre requests")
    print("=" * 60)
    
    try:
        scraper = ScraperService()
    except ValueError as e:
        print(f"   [ERROR] {e}")
        print("   Asegurate de configurar FIRECRAWL_API_KEY en el archivo .env")
        return []
    
    abogados = []
    
    print(f"\n   [>>] Buscando: '{query}'...")
    
    try:
        # Usar la función search que hace búsqueda + scrape en uno
        resultados = scraper.search(query, limit=limite)
        
        # Procesar resultados (SearchData tiene .web con lista de SearchResultWeb)
        data = []
        if hasattr(resultados, 'web') and resultados.web:
            data = resultados.web
        elif hasattr(resultados, 'data'):
            data = resultados.data
        elif isinstance(resultados, dict):
            data = resultados.get('data', resultados.get('results', resultados.get('web', [])))
        elif isinstance(resultados, list):
            data = resultados
            
        print(f"   [OK] Encontrados {len(data)} resultados")
        
        for i, item in enumerate(data):
            print(f"\n   [{i+1}/{len(data)}] Procesando resultado...")
            
            # Extraer datos del resultado de búsqueda (SearchResultWeb)
            url = getattr(item, 'url', '') if hasattr(item, 'url') else item.get('url', '') if isinstance(item, dict) else ''
            titulo = getattr(item, 'title', '') if hasattr(item, 'title') else item.get('title', '') if isinstance(item, dict) else ''
            descripcion = getattr(item, 'description', '') if hasattr(item, 'description') else item.get('description', '') if isinstance(item, dict) else ''
            
            if url:
                # Crear abogado con datos del resultado de búsqueda
                abogado = {
                    "nombre": titulo or "",
                    "despacho": "",
                    "telefono": "",
                    "email": "",
                    "direccion": "",
                    "web": url,
                    "fuente": url,
                    "descripcion": descripcion
                }
                
                # Intentar extraer más datos de la descripción
                if descripcion:
                    datos_extra = extraer_datos_de_markdown(descripcion, url, titulo)
                    for key in ["telefono", "email", "direccion", "despacho"]:
                        if datos_extra.get(key) and not abogado.get(key):
                            abogado[key] = datos_extra[key]
                
                if abogado["nombre"]:
                    abogados.append(abogado)
                    print(f"       [+] {abogado['nombre'][:50]}")
                else:
                    print(f"       [-] Sin nombre: {url[:40]}...")
            
            time.sleep(0.5)
            
    except Exception as e:
        print(f"   [ERROR] {str(e)}")
        
        # Si falla search, intentar con approach alternativo
        print("\n   [>>] Intentando metodo alternativo (scrape directo)...")
        
        urls_conocidas = [
            "https://www.abogadosextranjeria.es/",
            "https://www.parainmigrantes.info/directorio-de-abogados-de-extranjeria/",
        ]
        
        for url in urls_conocidas[:3]:  # Limitar para ahorrar créditos
            if len(abogados) >= limite:
                break
                
            print(f"\n   [>>] Scrapeando: {url[:50]}...")
            
            try:
                resultado = scraper.scrape_url(url, formats=["markdown"])
                
                markdown = ""
                if isinstance(resultado, dict):
                    markdown = resultado.get("markdown", "")
                else:
                    markdown = getattr(resultado, "markdown", "")
                
                if markdown:
                    abogado = extraer_datos_de_markdown(markdown, url, "")
                    if abogado["nombre"]:
                        abogados.append(abogado)
                        print(f"       [+] {abogado['nombre']}")
                
                time.sleep(delay)
                
            except Exception as e2:
                print(f"       [ERROR] {str(e2)[:50]}")
                continue
    
    print("\n" + "=" * 60)
    print(f"   RESUMEN:")
    print(f"   - Abogados encontrados: {len(abogados)}")
    print("=" * 60)
    
    return abogados


def main():
    """Función principal que ejecuta el scraping y genera los archivos."""
    
    # Crear carpeta de resultados
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Ejecutar scraping usando SEARCH (más eficiente)
    abogados = scrapear_abogados_con_search(
        query="abogados extranjeria madrid despacho",
        limite=15,  # Limitamos para ahorrar créditos
        delay=3.0
    )
    
    if not abogados:
        print("\n   [!] No se encontraron abogados.")
        print("   Posibles causas:")
        print("   - Rate limit alcanzado (espera unos minutos)")
        print("   - API key inválida")
        print("   - Problemas de conexión")
        return
    
    # Generar timestamp para los archivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Guardar en diferentes formatos
    csv_path = os.path.join(OUTPUT_DIR, f"abogados_extranjeria_madrid_{timestamp}.csv")
    pdf_path = os.path.join(OUTPUT_DIR, f"abogados_extranjeria_madrid_{timestamp}.pdf")
    json_path = os.path.join(OUTPUT_DIR, f"abogados_extranjeria_madrid_{timestamp}.json")
    
    print("\n   [>>] Guardando archivos...")
    guardar_csv(abogados, csv_path)
    guardar_pdf(abogados, pdf_path)
    guardar_json(abogados, json_path)
    
    print("\n" + "=" * 60)
    print("   [OK] PROCESO COMPLETADO!")
    print(f"   Archivos en: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
