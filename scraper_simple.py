"""
Scraper Simplificado de Abogados de Extranjería
================================================
Usa datos pre-investigados con IA + APIs opcionales para enriquecer.
Mucho más eficiente que scraping tradicional.
"""

import csv
import json
import os
from datetime import datetime
from typing import Optional

from fpdf import FPDF


# Configuración
DATA_DIR = "data"
OUTPUT_DIR = "resultados"
DATA_FILE = "abogados_extranjeria_madrid.json"


class AbogadoPDF(FPDF):
    """Clase para generar PDF profesional."""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(25, 55, 95)
        self.cell(0, 10, "Directorio de Abogados de Extranjeria - Madrid", align="C", ln=True)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}", align="C", ln=True)
        self.ln(5)
        self.set_draw_color(25, 55, 95)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}} | Fuente: Investigacion IA + Directorios oficiales", align="C")
    
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
        }
        for char, reemplazo in reemplazos.items():
            texto = texto.replace(char, reemplazo)
        return texto.encode('latin-1', errors='replace').decode('latin-1')
    
    def agregar_entrada(self, datos: dict, numero: int, tipo: str = "despacho"):
        """Agrega una entrada al PDF."""
        if self.get_y() > 230:
            self.add_page()
        
        # Título
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(25, 55, 95)
        nombre = self.limpiar_texto(datos.get("nombre", "Sin nombre"))
        icono = "🏢" if tipo == "despacho" else "👤" if tipo == "abogado" else "🏛️"
        self.cell(0, 8, f"{numero}. {nombre}", ln=True)
        
        # Línea
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 120, self.get_y())
        self.ln(3)
        
        # Datos
        self.set_font("Helvetica", "", 9)
        self.set_text_color(60, 60, 60)
        
        campos = [
            ("Tipo", tipo.capitalize()),
            ("Direccion", datos.get("direccion", "-")),
            ("Telefono", ", ".join(datos.get("telefonos", [])) if datos.get("telefonos") else "-"),
            ("Email", datos.get("email", "-")),
            ("Web", datos.get("web", "-")),
            ("Especialidades", ", ".join(datos.get("especialidades", [])) if datos.get("especialidades") else "-"),
            ("Valoracion", datos.get("valoracion", "-")),
        ]
        
        # Si es abogado individual, añadir número colegiado
        if tipo == "abogado" and datos.get("numero_colegiado"):
            campos.insert(1, ("Colegiado ICAM", datos.get("numero_colegiado")))
        
        for etiqueta, valor in campos:
            if valor and valor != "-":
                self.set_font("Helvetica", "B", 9)
                self.cell(28, 5, f"{etiqueta}:")
                self.set_font("Helvetica", "", 9)
                valor_limpio = self.limpiar_texto(str(valor))
                valor_mostrar = valor_limpio[:75] + "..." if len(valor_limpio) > 75 else valor_limpio
                self.cell(0, 5, valor_mostrar, ln=True)
        
        self.ln(6)


def cargar_datos_base() -> dict:
    """Carga los datos de la base JSON."""
    filepath = os.path.join(DATA_DIR, DATA_FILE)
    
    if not os.path.exists(filepath):
        print(f"   [!] No existe el archivo de datos: {filepath}")
        return {}
    
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def aplanar_datos(datos: dict) -> list:
    """Convierte la estructura JSON en una lista plana para exportar."""
    registros = []
    
    # Despachos
    for despacho in datos.get("despachos", []):
        registros.append({
            "nombre": despacho.get("nombre", ""),
            "tipo": "Despacho",
            "direccion": despacho.get("direccion", ""),
            "telefono": ", ".join(despacho.get("telefonos", [])),
            "email": despacho.get("email", ""),
            "web": despacho.get("web", ""),
            "especialidades": ", ".join(despacho.get("especialidades", [])),
            "valoracion": despacho.get("valoracion", ""),
            "numero_colegiado": "",
            "fuente": despacho.get("fuente", "")
        })
    
    # Abogados individuales
    for abogado in datos.get("abogados_individuales", []):
        registros.append({
            "nombre": abogado.get("nombre", ""),
            "tipo": "Abogado",
            "direccion": abogado.get("direccion", ""),
            "telefono": ", ".join(abogado.get("telefonos", [])),
            "email": abogado.get("email", ""),
            "web": abogado.get("web", "") or "",
            "especialidades": "",
            "valoracion": "",
            "numero_colegiado": abogado.get("numero_colegiado", ""),
            "fuente": abogado.get("fuente", "")
        })
    
    return registros


def guardar_csv(registros: list, filepath: str):
    """Guarda los datos en CSV."""
    if not registros:
        print("   [!] No hay registros para guardar")
        return
    
    campos = ["nombre", "tipo", "direccion", "telefono", "email", "web", 
              "especialidades", "valoracion", "numero_colegiado", "fuente"]
    
    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(registros)
    
    print(f"   [OK] CSV guardado: {filepath}")


def guardar_pdf(datos: dict, filepath: str):
    """Genera PDF profesional."""
    pdf = AbogadoPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Estadísticas
    total_despachos = len(datos.get("despachos", []))
    total_abogados = len(datos.get("abogados_individuales", []))
    total_oficiales = len(datos.get("servicios_oficiales", []))
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 7, f"Resumen: {total_despachos} despachos, {total_abogados} abogados, {total_oficiales} servicios oficiales", ln=True)
    pdf.ln(5)
    
    numero = 1
    
    # Sección: Despachos
    if datos.get("despachos"):
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(25, 55, 95)
        pdf.cell(0, 10, "DESPACHOS Y BUFETES", ln=True)
        pdf.ln(3)
        
        for despacho in datos["despachos"]:
            pdf.agregar_entrada(despacho, numero, "despacho")
            numero += 1
    
    # Sección: Abogados individuales
    if datos.get("abogados_individuales"):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(25, 55, 95)
        pdf.cell(0, 10, "ABOGADOS INDIVIDUALES (APAEM/ICAM)", ln=True)
        pdf.ln(3)
        
        for abogado in datos["abogados_individuales"]:
            pdf.agregar_entrada(abogado, numero, "abogado")
            numero += 1
    
    # Sección: Servicios oficiales
    if datos.get("servicios_oficiales"):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(25, 55, 95)
        pdf.cell(0, 10, "SERVICIOS OFICIALES", ln=True)
        pdf.ln(3)
        
        for servicio in datos["servicios_oficiales"]:
            pdf.agregar_entrada(servicio, numero, "oficial")
            numero += 1
    
    pdf.output(filepath)
    print(f"   [OK] PDF guardado: {filepath}")


def guardar_json(registros: list, filepath: str):
    """Guarda los datos en JSON."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=2)
    print(f"   [OK] JSON guardado: {filepath}")


def mostrar_estadisticas(datos: dict):
    """Muestra estadísticas de los datos."""
    despachos = datos.get("despachos", [])
    abogados = datos.get("abogados_individuales", [])
    oficiales = datos.get("servicios_oficiales", [])
    
    # Contar datos de contacto
    con_telefono = sum(1 for d in despachos + abogados if d.get("telefonos"))
    con_email = sum(1 for d in despachos + abogados if d.get("email"))
    con_web = sum(1 for d in despachos + abogados if d.get("web"))
    
    print("\n" + "=" * 60)
    print("   ESTADISTICAS DE LA BASE DE DATOS")
    print("=" * 60)
    print(f"   Despachos/Bufetes:     {len(despachos)}")
    print(f"   Abogados individuales: {len(abogados)}")
    print(f"   Servicios oficiales:   {len(oficiales)}")
    print(f"   ---")
    print(f"   Con telefono:          {con_telefono}/{len(despachos) + len(abogados)}")
    print(f"   Con email:             {con_email}/{len(despachos) + len(abogados)}")
    print(f"   Con web:               {con_web}/{len(despachos) + len(abogados)}")
    print("=" * 60)


def main():
    """Función principal."""
    print("=" * 60)
    print("   GENERADOR DE DIRECTORIO DE ABOGADOS")
    print("   Basado en investigacion IA + Directorios oficiales")
    print("=" * 60)
    
    # Crear carpetas
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Cargar datos
    print("\n   [>>] Cargando base de datos...")
    datos = cargar_datos_base()
    
    if not datos:
        print("   [!] No hay datos. Ejecuta primero la investigacion con IA.")
        return
    
    # Mostrar estadísticas
    mostrar_estadisticas(datos)
    
    # Aplanar para CSV
    registros = aplanar_datos(datos)
    
    # Generar archivos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    csv_path = os.path.join(OUTPUT_DIR, f"abogados_ia_{timestamp}.csv")
    pdf_path = os.path.join(OUTPUT_DIR, f"abogados_ia_{timestamp}.pdf")
    json_path = os.path.join(OUTPUT_DIR, f"abogados_ia_{timestamp}.json")
    
    print("\n   [>>] Generando archivos...")
    guardar_csv(registros, csv_path)
    guardar_pdf(datos, pdf_path)
    guardar_json(registros, json_path)
    
    print("\n" + "=" * 60)
    print("   [OK] PROCESO COMPLETADO!")
    print(f"   Archivos en: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
