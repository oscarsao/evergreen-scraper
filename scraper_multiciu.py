"""
Scraper Multi-Ciudad de Abogados de Extranjería
================================================
Sistema escalable para múltiples ciudades de España.
Usa datos pre-investigados con IA y genera exports por ciudad.
"""

import csv
import json
import os
from datetime import datetime
from typing import Optional

from fpdf import FPDF
from fpdf.enums import XPos, YPos


# Configuración
DATA_DIR = "data"
OUTPUT_DIR = "resultados"
CONFIG_FILE = "config_ciudades.json"


def es_valido(registro: dict) -> bool:
    """
    Un registro es válido si tiene al menos uno de: teléfono, email o web.
    No son excluyentes entre sí.
    """
    tiene_telefono = bool(registro.get("telefono")) and len(registro.get("telefono", [])) > 0
    tiene_email = bool(registro.get("email"))
    tiene_web = bool(registro.get("web"))
    return tiene_telefono or tiene_email or tiene_web


def cargar_config() -> dict:
    """Carga la configuración de ciudades."""
    filepath = os.path.join(DATA_DIR, CONFIG_FILE)
    if not os.path.exists(filepath):
        return {"ciudades": []}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def cargar_ciudad(nombre_archivo: str) -> dict:
    """Carga los datos de una ciudad."""
    filepath = os.path.join(DATA_DIR, nombre_archivo)
    if not os.path.exists(filepath):
        return {"metadata": {}, "registros": []}
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def filtrar_validos(registros: list) -> list:
    """Filtra solo registros que tienen al menos teléfono, email o web."""
    return [r for r in registros if es_valido(r)]


class MultiCiudadPDF(FPDF):
    """Clase para generar PDF profesional multi-ciudad."""
    
    def __init__(self, ciudad: str = ""):
        super().__init__()
        self.ciudad = ciudad
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(25, 55, 95)
        titulo = f"Abogados de Extranjeria - {self.ciudad}" if self.ciudad else "Abogados de Extranjeria"
        self.cell(0, 10, titulo, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
                  new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        self.ln(3)
        self.set_draw_color(25, 55, 95)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}} | Fuente: Investigacion IA", align="C")
    
    def limpiar_texto(self, texto: str) -> str:
        """Limpia caracteres no compatibles."""
        if not texto:
            return ""
        reemplazos = {
            '【': '[', '】': ']', '▷': '>', '►': '>',
            '★': '*', '☆': '*', '●': '-', '○': '-',
            '→': '->', '←': '<-', '€': 'EUR',
            '"': '"', '"': '"', ''': "'", ''': "'",
            '–': '-', '—': '-', '…': '...',
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
            'ñ': 'n', 'Ñ': 'N', 'ü': 'u', 'Ü': 'U',
        }
        for char, reemplazo in reemplazos.items():
            texto = texto.replace(char, reemplazo)
        return texto.encode('latin-1', errors='replace').decode('latin-1')
    
    def agregar_registro(self, registro: dict, numero: int):
        """Agrega un registro al PDF."""
        if self.get_y() > 235:
            self.add_page()
        
        # Título
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(25, 55, 95)
        nombre = self.limpiar_texto(registro.get("nombre", "Sin nombre"))
        tipo = registro.get("tipo", "despacho").upper()
        self.cell(0, 7, f"{numero}. [{tipo}] {nombre}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Línea
        self.set_draw_color(220, 220, 220)
        self.line(10, self.get_y(), 100, self.get_y())
        self.ln(2)
        
        # Datos
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        
        # Teléfono
        telefonos = registro.get("telefono", [])
        if telefonos and len(telefonos) > 0:
            self.set_font("Helvetica", "B", 8)
            self.cell(22, 5, "Tel:")
            self.set_font("Helvetica", "", 8)
            tel_str = ", ".join(telefonos[:3])  # Máximo 3 teléfonos
            self.cell(0, 5, self.limpiar_texto(tel_str), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Email
        email = registro.get("email")
        if email:
            self.set_font("Helvetica", "B", 8)
            self.cell(22, 5, "Email:")
            self.set_font("Helvetica", "", 8)
            self.cell(0, 5, self.limpiar_texto(email), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Web
        web = registro.get("web")
        if web:
            self.set_font("Helvetica", "B", 8)
            self.cell(22, 5, "Web:")
            self.set_font("Helvetica", "", 8)
            web_corta = web[:60] + "..." if len(web) > 60 else web
            self.cell(0, 5, self.limpiar_texto(web_corta), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # Dirección (opcional)
        direccion = registro.get("direccion")
        if direccion:
            self.set_font("Helvetica", "B", 8)
            self.cell(22, 5, "Dir:")
            self.set_font("Helvetica", "", 8)
            dir_corta = direccion[:55] + "..." if len(direccion) > 55 else direccion
            self.cell(0, 5, self.limpiar_texto(dir_corta), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        self.ln(4)


def generar_csv_ciudad(registros: list, ciudad: str, filepath: str):
    """Genera CSV para una ciudad."""
    if not registros:
        print(f"   [!] Sin registros para {ciudad}")
        return
    
    campos = ["nombre", "tipo", "telefono", "email", "web", "direccion", "ciudad", "distrito", "especialidades"]
    
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        
        for reg in registros:
            row = {
                "nombre": reg.get("nombre", ""),
                "tipo": reg.get("tipo", ""),
                "telefono": ", ".join(reg.get("telefono", [])),
                "email": reg.get("email", "") or "",
                "web": reg.get("web", "") or "",
                "direccion": reg.get("direccion", "") or "",
                "ciudad": reg.get("ciudad", ciudad),
                "distrito": reg.get("distrito", "") or "",
                "especialidades": ", ".join(reg.get("especialidades", []))
            }
            writer.writerow(row)
    
    print(f"   [OK] CSV: {filepath}")


def generar_pdf_ciudad(registros: list, ciudad: str, filepath: str):
    """Genera PDF para una ciudad."""
    if not registros:
        return
    
    pdf = MultiCiudadPDF(ciudad=ciudad)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Resumen
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(60, 60, 60)
    
    # Contar por tipo
    despachos = sum(1 for r in registros if r.get("tipo") == "despacho")
    abogados = sum(1 for r in registros if r.get("tipo") == "abogado")
    ongs = sum(1 for r in registros if r.get("tipo") == "ong")
    oficiales = sum(1 for r in registros if r.get("tipo") == "oficial")
    
    resumen = f"Total: {len(registros)} | Despachos: {despachos} | Abogados: {abogados}"
    if ongs > 0:
        resumen += f" | ONGs: {ongs}"
    if oficiales > 0:
        resumen += f" | Oficiales: {oficiales}"
    
    pdf.cell(0, 6, resumen, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(5)
    
    # Registros
    for i, registro in enumerate(registros, 1):
        pdf.agregar_registro(registro, i)
    
    pdf.output(filepath)
    print(f"   [OK] PDF: {filepath}")


def procesar_ciudad(config_ciudad: dict, timestamp: str) -> dict:
    """Procesa una ciudad y genera sus exports."""
    nombre = config_ciudad["nombre"]
    archivo = config_ciudad["archivo"]
    
    print(f"\n   [>>] Procesando: {nombre}")
    
    # Cargar datos
    datos = cargar_ciudad(archivo)
    registros = datos.get("registros", [])
    
    if not registros:
        print(f"   [!] No hay datos para {nombre}")
        return {"ciudad": nombre, "total": 0, "validos": 0}
    
    # Filtrar válidos
    validos = filtrar_validos(registros)
    
    print(f"       Total: {len(registros)} | Válidos: {len(validos)}")
    
    if not validos:
        return {"ciudad": nombre, "total": len(registros), "validos": 0}
    
    # Generar archivos
    ciudad_slug = nombre.lower().replace(" ", "_")
    
    csv_path = os.path.join(OUTPUT_DIR, f"{ciudad_slug}_{timestamp}.csv")
    pdf_path = os.path.join(OUTPUT_DIR, f"{ciudad_slug}_{timestamp}.pdf")
    
    generar_csv_ciudad(validos, nombre, csv_path)
    generar_pdf_ciudad(validos, nombre, pdf_path)
    
    return {"ciudad": nombre, "total": len(registros), "validos": len(validos)}


def generar_resumen_total(resultados: list, timestamp: str):
    """Genera un CSV resumen con todas las ciudades."""
    filepath = os.path.join(OUTPUT_DIR, f"resumen_total_{timestamp}.csv")
    
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["ciudad", "total_registros", "registros_validos"])
        writer.writeheader()
        
        for r in resultados:
            writer.writerow({
                "ciudad": r["ciudad"],
                "total_registros": r["total"],
                "registros_validos": r["validos"]
            })
    
    print(f"\n   [OK] Resumen: {filepath}")


def main():
    """Función principal."""
    print("=" * 60)
    print("   SCRAPER MULTI-CIUDAD DE ABOGADOS DE EXTRANJERIA")
    print("   Sistema escalable para múltiples ciudades")
    print("=" * 60)
    
    # Crear carpetas
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Cargar configuración
    config = cargar_config()
    ciudades = config.get("ciudades", [])
    
    if not ciudades:
        print("\n   [!] No hay ciudades configuradas en config_ciudades.json")
        return
    
    print(f"\n   Ciudades configuradas: {len(ciudades)}")
    for c in ciudades:
        print(f"   - {c['nombre']}")
    
    # Timestamp para archivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Procesar cada ciudad
    resultados = []
    
    for ciudad_config in ciudades:
        archivo = ciudad_config.get("archivo", "")
        filepath = os.path.join(DATA_DIR, archivo)
        
        # Solo procesar si existe el archivo de datos
        if os.path.exists(filepath):
            resultado = procesar_ciudad(ciudad_config, timestamp)
            resultados.append(resultado)
    
    # Generar resumen
    if resultados:
        generar_resumen_total(resultados, timestamp)
    
    # Estadísticas finales
    print("\n" + "=" * 60)
    print("   RESUMEN FINAL")
    print("=" * 60)
    
    total_registros = sum(r["total"] for r in resultados)
    total_validos = sum(r["validos"] for r in resultados)
    
    for r in resultados:
        print(f"   {r['ciudad']}: {r['validos']}/{r['total']} válidos")
    
    print(f"\n   TOTAL: {total_validos}/{total_registros} registros válidos")
    print(f"   Archivos en: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
