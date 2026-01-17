"""
Scraper de Abogados de Extranjería en Madrid - V2
=================================================
Version optimizada con múltiples fuentes y mejor extracción de datos.
"""

import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import csv
import json
import os
import re
import time
from datetime import datetime
from typing import Optional, List, Dict

from fpdf import FPDF
from scraper_service import ScraperService


OUTPUT_DIR = "resultados"


# ============================================================================
# EXTRACCIÓN DE DATOS MEJORADA
# ============================================================================

def extraer_telefonos(texto: str) -> List[str]:
    """Extrae todos los teléfonos del texto."""
    patrones = [
        r'(?:tel[éeè]?f?o?n?o?|tfno?|phone|móvil|movil|fax)?[:\s]*(\+34[\s\-\.]?\d{3}[\s\-\.]?\d{3}[\s\-\.]?\d{3})',
        r'(?:tel[éeè]?f?o?n?o?|tfno?|phone|móvil|movil)?[:\s]*(\d{3}[\s\-\.]?\d{2}[\s\-\.]?\d{2}[\s\-\.]?\d{2})',
        r'(?:tel[éeè]?f?o?n?o?|tfno?|phone|móvil|movil)?[:\s]*(\d{3}[\s\-\.]?\d{3}[\s\-\.]?\d{3})',
        r'(?:tel[éeè]?f?o?n?o?|tfno?|phone|móvil|movil)?[:\s]*(9[0-9]{8})',
        r'(?:tel[éeè]?f?o?n?o?|tfno?|phone|móvil|movil)?[:\s]*(6[0-9]{8})',
        r'(?:tel[éeè]?f?o?n?o?|tfno?|phone|móvil|movil)?[:\s]*(7[0-9]{8})',
    ]
    telefonos = []
    for patron in patrones:
        matches = re.findall(patron, texto, re.IGNORECASE)
        for match in matches:
            tel = re.sub(r'[\s\-\.]', '', match)
            if len(tel) >= 9 and tel not in telefonos:
                telefonos.append(tel)
    return telefonos


def extraer_emails(texto: str) -> List[str]:
    """Extrae todos los emails del texto."""
    patron = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(patron, texto)
    # Filtrar emails obviamente falsos
    emails_validos = [e for e in emails if not e.endswith('.png') and not e.endswith('.jpg')]
    return list(set(emails_validos))


def extraer_direcciones(texto: str) -> List[str]:
    """Extrae direcciones del texto."""
    patrones = [
        # Calle con número
        r'(?:C/|Calle|c\.)\s*[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+,?\s*(?:n[ºo°]?\.?\s*)?\d+[^,\n]{0,30}',
        # Avenida
        r'(?:Avda?\.|Avenida)\s*[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+,?\s*(?:n[ºo°]?\.?\s*)?\d+[^,\n]{0,30}',
        # Plaza
        r'(?:Pza?\.|Plaza)\s*[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+,?\s*(?:n[ºo°]?\.?\s*)?\d+[^,\n]{0,30}',
        # Paseo
        r'(?:P[ºo]?\.|Paseo)\s*[A-ZÁÉÍÓÚÑa-záéíóúñ\s]+,?\s*(?:n[ºo°]?\.?\s*)?\d+[^,\n]{0,30}',
        # Gran Vía y similares
        r'Gran\s*Vía[^,\n]{0,40}',
        # Con código postal
        r'[A-ZÁÉÍÓÚÑa-záéíóúñ\s,]+\d{5}\s*(?:Madrid|MADRID)',
    ]
    direcciones = []
    for patron in patrones:
        matches = re.findall(patron, texto, re.IGNORECASE)
        for match in matches:
            dir_limpia = match.strip()
            if len(dir_limpia) > 10 and dir_limpia not in direcciones:
                direcciones.append(dir_limpia)
    return direcciones


def extraer_codigo_postal(texto: str) -> str:
    """Extrae código postal de Madrid (28XXX)."""
    match = re.search(r'\b(28\d{3})\b', texto)
    return match.group(1) if match else ""


def limpiar_nombre(nombre: str) -> str:
    """Limpia el nombre de caracteres especiales y símbolos."""
    # Quitar símbolos comunes de SEO
    nombre = re.sub(r'[【】▷►★☆●○→←↑↓✓✔✗✘☎📞📧🏠]', '', nombre)
    nombre = re.sub(r'\s+', ' ', nombre).strip()
    # Quitar "..." al final
    nombre = re.sub(r'\.{2,}$', '', nombre).strip()
    return nombre


def extraer_datos_completos(contenido: str, url: str = "", titulo: str = "") -> Dict:
    """Extrae todos los datos posibles del contenido."""
    
    telefonos = extraer_telefonos(contenido)
    emails = extraer_emails(contenido)
    direcciones = extraer_direcciones(contenido)
    cp = extraer_codigo_postal(contenido)
    
    # Extraer nombre del título o del contenido
    nombre = limpiar_nombre(titulo) if titulo else ""
    if not nombre:
        # Buscar en encabezados
        match = re.search(r'^#\s*(.+?)$', contenido, re.MULTILINE)
        if match:
            nombre = limpiar_nombre(match.group(1))
    
    # Extraer descripción (primeros párrafos significativos)
    descripcion = ""
    parrafos = re.findall(r'(?:^|\n)([A-ZÁÉÍÓÚÑ][^.\n]{20,200}\.)', contenido)
    if parrafos:
        descripcion = ' '.join(parrafos[:2])[:300]
    
    return {
        "nombre": nombre,
        "telefono": telefonos[0] if telefonos else "",
        "telefonos_adicionales": telefonos[1:] if len(telefonos) > 1 else [],
        "email": emails[0] if emails else "",
        "emails_adicionales": emails[1:] if len(emails) > 1 else [],
        "direccion": direcciones[0] if direcciones else "",
        "codigo_postal": cp,
        "ciudad": "Madrid",
        "web": url,
        "descripcion": descripcion,
        "fuente": url
    }


# ============================================================================
# FUENTES DE DATOS EFICIENTES
# ============================================================================

def buscar_en_directorios(scraper: ScraperService, limite_por_busqueda: int = 10) -> List[Dict]:
    """
    Busca abogados en múltiples directorios usando queries específicas.
    Cada búsqueda consume ~1 crédito pero devuelve múltiples resultados.
    """
    
    queries = [
        "abogados extranjeria madrid telefono contacto",
        "bufete abogados extranjeria madrid direccion",
        "despacho abogados inmigracion madrid",
        "abogado nacionalidad española madrid",
        "asesoria extranjeria madrid precios",
    ]
    
    abogados = []
    urls_vistas = set()
    
    for query in queries:
        print(f"\n   [>>] Buscando: '{query[:40]}...'")
        
        try:
            resultados = scraper.search(query, limit=limite_por_busqueda)
            
            data = []
            if hasattr(resultados, 'web') and resultados.web:
                data = resultados.web
            
            print(f"       Encontrados: {len(data)} resultados")
            
            for item in data:
                url = getattr(item, 'url', '') or ''
                
                # Evitar duplicados
                dominio = re.search(r'https?://(?:www\.)?([^/]+)', url)
                if dominio:
                    dominio_base = dominio.group(1)
                    if dominio_base in urls_vistas:
                        continue
                    urls_vistas.add(dominio_base)
                
                titulo = getattr(item, 'title', '') or ''
                descripcion = getattr(item, 'description', '') or ''
                
                # Combinar título y descripción para extracción
                contenido_completo = f"{titulo}\n{descripcion}"
                
                abogado = extraer_datos_completos(contenido_completo, url, titulo)
                
                if abogado["nombre"]:
                    abogados.append(abogado)
                    
            time.sleep(1)  # Pausa entre búsquedas
            
        except Exception as e:
            print(f"       [!] Error: {str(e)[:50]}")
            continue
    
    return abogados


def scrapear_directorios_especificos(scraper: ScraperService, limite: int = 5) -> List[Dict]:
    """
    Scrapea páginas de directorios que tienen listados de abogados.
    Más eficiente: 1 scrape = múltiples abogados.
    """
    
    # URLs de directorios con listados
    directorios = [
        "https://www.abogados365.com/abogados/extranjeria/madrid",
        "https://www.qdq.com/abogados-extranjeria/madrid/",
    ]
    
    abogados = []
    
    for url in directorios[:limite]:
        print(f"\n   [>>] Scrapeando directorio: {url[:50]}...")
        
        try:
            resultado = scraper.scrape_url(url, formats=["markdown"])
            
            markdown = ""
            if isinstance(resultado, dict):
                markdown = resultado.get("markdown", "")
            else:
                markdown = getattr(resultado, "markdown", "")
            
            if markdown:
                # Buscar patrones de listados de abogados
                # Intentar extraer múltiples entradas
                
                # Patrón: bloques que parecen perfiles
                bloques = re.split(r'\n(?=#{1,3}\s|\*\*[A-Z])', markdown)
                
                for bloque in bloques:
                    if len(bloque) > 50:  # Bloque significativo
                        datos = extraer_datos_completos(bloque, url, "")
                        
                        # Solo agregar si parece un abogado/bufete
                        if datos["nombre"] and ("abogado" in datos["nombre"].lower() or 
                                                "bufete" in datos["nombre"].lower() or
                                                datos["telefono"] or datos["email"]):
                            abogados.append(datos)
                
                print(f"       Extraídos: {len([a for a in abogados if a['fuente'] == url])} perfiles")
            
            time.sleep(2)
            
        except Exception as e:
            print(f"       [!] Error: {str(e)[:50]}")
            continue
    
    return abogados


def enriquecer_con_scraping(scraper: ScraperService, abogados: List[Dict], limite: int = 10) -> List[Dict]:
    """
    Hace scraping de las webs individuales para obtener más datos.
    Solo para abogados que les falten datos importantes.
    """
    
    print("\n   [>>] Enriqueciendo datos con scraping individual...")
    
    # Filtrar abogados que necesitan más datos
    abogados_incompletos = [
        a for a in abogados 
        if not a.get("telefono") or not a.get("email")
    ][:limite]
    
    print(f"       Abogados a enriquecer: {len(abogados_incompletos)}")
    
    for i, abogado in enumerate(abogados_incompletos):
        url = abogado.get("web", "")
        if not url:
            continue
            
        print(f"       [{i+1}/{len(abogados_incompletos)}] {url[:40]}...")
        
        try:
            resultado = scraper.scrape_url(url, formats=["markdown"])
            
            markdown = ""
            if isinstance(resultado, dict):
                markdown = resultado.get("markdown", "")
            else:
                markdown = getattr(resultado, "markdown", "")
            
            if markdown:
                datos_nuevos = extraer_datos_completos(markdown, url, abogado.get("nombre", ""))
                
                # Actualizar solo campos vacíos
                for campo in ["telefono", "email", "direccion", "codigo_postal", "descripcion"]:
                    if not abogado.get(campo) and datos_nuevos.get(campo):
                        abogado[campo] = datos_nuevos[campo]
                
                # Agregar teléfonos/emails adicionales
                if datos_nuevos.get("telefonos_adicionales"):
                    abogado["telefonos_adicionales"] = datos_nuevos["telefonos_adicionales"]
                if datos_nuevos.get("emails_adicionales"):
                    abogado["emails_adicionales"] = datos_nuevos["emails_adicionales"]
            
            time.sleep(2)  # Pausa más larga para evitar rate limits
            
        except Exception as e:
            print(f"           [!] Error: {str(e)[:40]}")
            continue
    
    return abogados


# ============================================================================
# GENERACIÓN DE ARCHIVOS
# ============================================================================

class AbogadoPDF(FPDF):
    """PDF profesional para directorio de abogados."""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def limpiar_texto(self, texto: str) -> str:
        reemplazos = {
            '【': '[', '】': ']', '▷': '>', '►': '>',
            '★': '*', '☆': '*', '●': '-', '○': '-',
            '→': '->', '←': '<-', '€': 'EUR',
            '"': '"', '"': '"', ''': "'", ''': "'",
            '–': '-', '—': '-', '…': '...',
        }
        for char, reemplazo in reemplazos.items():
            texto = texto.replace(char, reemplazo)
        return texto.encode('latin-1', errors='replace').decode('latin-1')
    
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(25, 55, 95)
        self.cell(0, 10, "Directorio de Abogados de Extranjeria - Madrid", align="C", ln=True)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="C", ln=True)
        self.ln(3)
        self.set_draw_color(25, 55, 95)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")
    
    def agregar_abogado(self, abogado: dict, numero: int):
        if self.get_y() > 230:
            self.add_page()
        
        # Nombre
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(25, 55, 95)
        nombre = self.limpiar_texto(abogado.get("nombre", "Sin nombre"))[:60]
        self.cell(0, 7, f"{numero}. {nombre}", ln=True)
        
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(2)
        
        # Datos
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        
        campos = [
            ("Tel", abogado.get("telefono", "")),
            ("Email", abogado.get("email", "")),
            ("Dir", abogado.get("direccion", "")),
            ("CP", abogado.get("codigo_postal", "")),
            ("Web", abogado.get("web", "")),
        ]
        
        for etiqueta, valor in campos:
            if valor:
                self.set_font("Helvetica", "B", 8)
                self.cell(12, 5, f"{etiqueta}:")
                self.set_font("Helvetica", "", 8)
                valor_limpio = self.limpiar_texto(str(valor))[:70]
                self.cell(0, 5, valor_limpio, ln=True)
        
        # Descripción (si existe)
        desc = abogado.get("descripcion", "")
        if desc:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 100, 100)
            desc_limpia = self.limpiar_texto(desc)[:150]
            self.multi_cell(0, 4, desc_limpia)
        
        self.ln(5)


def guardar_csv_completo(abogados: List[Dict], filepath: str):
    """Guarda CSV con todos los campos."""
    campos = [
        "nombre", "telefono", "email", "direccion", 
        "codigo_postal", "ciudad", "web", "descripcion", "fuente"
    ]
    
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(abogados)
    
    print(f"   [OK] CSV: {filepath}")


def guardar_pdf_completo(abogados: List[Dict], filepath: str):
    """Genera PDF profesional."""
    pdf = AbogadoPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Resumen
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"Total: {len(abogados)} abogados/despachos", ln=True)
    
    con_telefono = len([a for a in abogados if a.get("telefono")])
    con_email = len([a for a in abogados if a.get("email")])
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 5, f"Con telefono: {con_telefono} | Con email: {con_email}", ln=True)
    pdf.ln(5)
    
    for i, abogado in enumerate(abogados, 1):
        pdf.agregar_abogado(abogado, i)
    
    pdf.output(filepath)
    print(f"   [OK] PDF: {filepath}")


def guardar_json_completo(abogados: List[Dict], filepath: str):
    """Guarda JSON con datos completos."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump({
            "fecha_generacion": datetime.now().isoformat(),
            "total": len(abogados),
            "con_telefono": len([a for a in abogados if a.get("telefono")]),
            "con_email": len([a for a in abogados if a.get("email")]),
            "abogados": abogados
        }, f, ensure_ascii=False, indent=2)
    
    print(f"   [OK] JSON: {filepath}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("   SCRAPER ABOGADOS EXTRANJERIA MADRID - V2")
    print("   Optimizado para maxima eficiencia de creditos")
    print("=" * 60)
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    try:
        scraper = ScraperService()
    except ValueError as e:
        print(f"\n   [ERROR] {e}")
        return
    
    abogados = []
    
    # Fase 1: Búsquedas múltiples (~5 créditos, ~50 resultados)
    print("\n[FASE 1] Busquedas en web...")
    abogados_busqueda = buscar_en_directorios(scraper, limite_por_busqueda=10)
    abogados.extend(abogados_busqueda)
    print(f"\n   Total fase 1: {len(abogados)} abogados")
    
    # Fase 2: Scraping de directorios (~2 créditos, múltiples por página)
    print("\n[FASE 2] Scraping de directorios...")
    abogados_directorios = scrapear_directorios_especificos(scraper, limite=2)
    
    # Combinar sin duplicados
    urls_existentes = {a.get("web", "") for a in abogados}
    for ab in abogados_directorios:
        if ab.get("web") not in urls_existentes:
            abogados.append(ab)
            urls_existentes.add(ab.get("web", ""))
    
    print(f"\n   Total fase 2: {len(abogados)} abogados")
    
    # Fase 3: Enriquecer datos (~10 créditos para los que faltan datos)
    print("\n[FASE 3] Enriqueciendo datos...")
    abogados = enriquecer_con_scraping(scraper, abogados, limite=10)
    
    # Eliminar duplicados finales por nombre similar
    abogados_unicos = []
    nombres_vistos = set()
    for ab in abogados:
        nombre_normalizado = ab.get("nombre", "").lower()[:30]
        if nombre_normalizado and nombre_normalizado not in nombres_vistos:
            abogados_unicos.append(ab)
            nombres_vistos.add(nombre_normalizado)
    
    abogados = abogados_unicos
    
    # Estadísticas
    print("\n" + "=" * 60)
    print("   RESUMEN FINAL")
    print("=" * 60)
    print(f"   Total abogados: {len(abogados)}")
    print(f"   Con telefono:   {len([a for a in abogados if a.get('telefono')])}")
    print(f"   Con email:      {len([a for a in abogados if a.get('email')])}")
    print(f"   Con direccion:  {len([a for a in abogados if a.get('direccion')])}")
    print(f"   Creditos usados: ~17 (estimado)")
    
    if not abogados:
        print("\n   [!] No se encontraron abogados")
        return
    
    # Guardar archivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("\n[GUARDANDO ARCHIVOS]")
    guardar_csv_completo(abogados, os.path.join(OUTPUT_DIR, f"abogados_v2_{timestamp}.csv"))
    guardar_pdf_completo(abogados, os.path.join(OUTPUT_DIR, f"abogados_v2_{timestamp}.pdf"))
    guardar_json_completo(abogados, os.path.join(OUTPUT_DIR, f"abogados_v2_{timestamp}.json"))
    
    print("\n" + "=" * 60)
    print("   [OK] COMPLETADO!")
    print(f"   Archivos en: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
