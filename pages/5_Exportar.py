"""
Página de exportación de datos.
"""
import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
import io

st.set_page_config(page_title="Exportar", page_icon="📥", layout="wide")

st.title("📥 Exportar Datos")
st.caption("Descarga los datos en diferentes formatos")


def cargar_datos_ciudad(ciudad: str):
    """Carga datos de una ciudad."""
    archivo = Path("data") / f"{ciudad.lower()}.json"
    if archivo.exists():
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"metadata": {}, "registros": []}


def listar_ciudades():
    """Lista ciudades disponibles."""
    data_dir = Path("data")
    if not data_dir.exists():
        return []
    
    ciudades = []
    for archivo in data_dir.glob("*.json"):
        if "config" not in archivo.name:
            ciudades.append(archivo.stem.title())
    return sorted(ciudades)


def preparar_df(registros: list) -> pd.DataFrame:
    """Prepara DataFrame para exportación."""
    df = pd.DataFrame(registros)
    
    # Convertir listas a strings
    if "telefono" in df.columns:
        df["telefono"] = df["telefono"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else str(x) if x else ""
        )
    
    if "especialidades" in df.columns:
        df["especialidades"] = df["especialidades"].apply(
            lambda x: ", ".join(x) if isinstance(x, list) else str(x) if x else ""
        )
    
    return df


def generar_pdf(df: pd.DataFrame, titulo: str) -> bytes:
    """Genera PDF con los datos."""
    try:
        from fpdf import FPDF
        
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, titulo, ln=True, align="C")
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 10, f"Generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        pdf.ln(10)
        
        pdf.set_font("Helvetica", "", 9)
        
        for _, row in df.iterrows():
            pdf.set_font("Helvetica", "B", 10)
            nombre = str(row.get("nombre", ""))[:50]
            pdf.cell(0, 6, nombre, ln=True)
            
            pdf.set_font("Helvetica", "", 9)
            
            if row.get("telefono"):
                pdf.cell(0, 5, f"  Tel: {row['telefono']}", ln=True)
            if row.get("email"):
                pdf.cell(0, 5, f"  Email: {row['email']}", ln=True)
            if row.get("web"):
                pdf.cell(0, 5, f"  Web: {str(row['web'])[:60]}", ln=True)
            if row.get("direccion"):
                pdf.cell(0, 5, f"  Dir: {str(row['direccion'])[:60]}", ln=True)
            
            pdf.ln(3)
            
            # Nueva página si necesario
            if pdf.get_y() > 270:
                pdf.add_page()
        
        return pdf.output()
        
    except ImportError:
        return None


# Sidebar - Configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    ciudades = listar_ciudades()
    if not ciudades:
        st.warning("No hay datos disponibles")
        st.stop()
    
    # Selección de ciudades
    ciudades_sel = st.multiselect(
        "Ciudades a exportar",
        ciudades,
        default=ciudades[:1]
    )
    
    st.divider()
    
    # Filtros
    st.subheader("Filtros")
    solo_con_telefono = st.checkbox("Solo con teléfono")
    solo_con_email = st.checkbox("Solo con email")
    solo_con_web = st.checkbox("Solo con web")
    
    st.divider()
    
    # Formato
    formato = st.radio(
        "Formato de exportación",
        ["CSV", "Excel", "JSON", "PDF"]
    )

# Cargar datos seleccionados
registros = []
for ciudad in ciudades_sel:
    data = cargar_datos_ciudad(ciudad)
    for r in data.get("registros", []):
        r["ciudad_origen"] = ciudad
        registros.append(r)

# Aplicar filtros
if solo_con_telefono:
    registros = [r for r in registros if r.get("telefono")]
if solo_con_email:
    registros = [r for r in registros if r.get("email")]
if solo_con_web:
    registros = [r for r in registros if r.get("web")]

# Mostrar preview
st.subheader(f"📋 Vista Previa ({len(registros)} registros)")

if registros:
    df = preparar_df(registros)
    
    # Seleccionar columnas
    columnas_disponibles = list(df.columns)
    columnas_default = ["nombre", "tipo", "telefono", "email", "web", "direccion", "ciudad_origen"]
    columnas_mostrar = [c for c in columnas_default if c in columnas_disponibles]
    
    columnas_sel = st.multiselect(
        "Columnas a exportar",
        columnas_disponibles,
        default=columnas_mostrar
    )
    
    if columnas_sel:
        df_export = df[columnas_sel]
        
        st.dataframe(df_export.head(10), use_container_width=True, hide_index=True)
        
        if len(df_export) > 10:
            st.caption(f"Mostrando 10 de {len(df_export)} registros")
        
        st.divider()
        
        # Botón de descarga
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ciudades_str = "_".join(c.lower() for c in ciudades_sel)
        
        if formato == "CSV":
            csv = df_export.to_csv(index=False)
            st.download_button(
                "📥 Descargar CSV",
                csv,
                f"abogados_{ciudades_str}_{timestamp}.csv",
                "text/csv",
                use_container_width=True
            )
        
        elif formato == "Excel":
            try:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Abogados')
                
                st.download_button(
                    "📥 Descargar Excel",
                    buffer.getvalue(),
                    f"abogados_{ciudades_str}_{timestamp}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except ImportError:
                st.error("Instala openpyxl para exportar a Excel: pip install openpyxl")
        
        elif formato == "JSON":
            # Usar registros originales para JSON
            json_data = json.dumps(registros, ensure_ascii=False, indent=2)
            st.download_button(
                "📥 Descargar JSON",
                json_data,
                f"abogados_{ciudades_str}_{timestamp}.json",
                "application/json",
                use_container_width=True
            )
        
        elif formato == "PDF":
            pdf_bytes = generar_pdf(df_export, f"Abogados de Extranjería - {', '.join(ciudades_sel)}")
            if pdf_bytes:
                st.download_button(
                    "📥 Descargar PDF",
                    pdf_bytes,
                    f"abogados_{ciudades_str}_{timestamp}.pdf",
                    "application/pdf",
                    use_container_width=True
                )
            else:
                st.error("Instala fpdf2 para exportar a PDF: pip install fpdf2")
    else:
        st.warning("Selecciona al menos una columna")
else:
    st.info("No hay registros que coincidan con los filtros seleccionados")

# Estadísticas de exportación
st.divider()
st.subheader("📊 Estadísticas")

if registros:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total a exportar", len(registros))
    
    with col2:
        con_tel = sum(1 for r in registros if r.get("telefono"))
        st.metric("Con teléfono", con_tel)
    
    with col3:
        con_email = sum(1 for r in registros if r.get("email"))
        st.metric("Con email", con_email)
    
    with col4:
        con_web = sum(1 for r in registros if r.get("web"))
        st.metric("Con web", con_web)
