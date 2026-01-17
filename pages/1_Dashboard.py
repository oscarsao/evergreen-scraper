"""
Dashboard principal con métricas y gráficos.
"""
import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.title("📊 Dashboard")
st.caption("Métricas y estadísticas del sistema")


def cargar_todos_registros():
    """Carga todos los registros de todas las ciudades."""
    data_dir = Path("data")
    registros = []
    
    if not data_dir.exists():
        return registros
    
    for archivo in data_dir.glob("*.json"):
        if "config" in archivo.name:
            continue
        
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for r in data.get("registros", []):
                r["_ciudad"] = archivo.stem.title()
                registros.append(r)
        except:
            continue
    
    return registros


# Cargar datos
registros = cargar_todos_registros()

if not registros:
    st.warning("No hay datos cargados. Ejecuta una búsqueda primero.")
    st.stop()

# Convertir a DataFrame
df = pd.DataFrame(registros)

# Métricas principales
st.subheader("📈 Métricas Generales")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Total Registros", len(df))

with col2:
    con_tel = df["telefono"].apply(lambda x: bool(x) if isinstance(x, list) else bool(x)).sum()
    st.metric("Con Teléfono", con_tel)

with col3:
    con_email = df["email"].notna().sum()
    st.metric("Con Email", con_email)

with col4:
    con_web = df["web"].notna().sum()
    st.metric("Con Web", con_web)

with col5:
    # Contacto completo: tiene los 3
    completo = df.apply(
        lambda r: bool(r.get("telefono")) and bool(r.get("email")) and bool(r.get("web")),
        axis=1
    ).sum()
    st.metric("Contacto Completo", completo)

st.divider()

# Gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("🏙️ Por Ciudad")
    ciudad_counts = df["_ciudad"].value_counts()
    st.bar_chart(ciudad_counts)

with col2:
    st.subheader("📁 Por Tipo")
    if "tipo" in df.columns:
        tipo_counts = df["tipo"].value_counts()
        st.bar_chart(tipo_counts)
    else:
        st.info("No hay datos de tipo")

st.divider()

# Por especialidad
st.subheader("🎯 Por Especialidad")

especialidades_todas = []
for esp_list in df.get("especialidades", []):
    if isinstance(esp_list, list):
        especialidades_todas.extend(esp_list)

if especialidades_todas:
    esp_counts = pd.Series(especialidades_todas).value_counts()
    st.bar_chart(esp_counts.head(10))
else:
    st.info("No hay datos de especialidades")

st.divider()

# Tabla de registros recientes
st.subheader("📋 Últimos Registros")

# Mostrar últimos 10
columnas_mostrar = ["nombre", "tipo", "_ciudad", "email", "web"]
columnas_disponibles = [c for c in columnas_mostrar if c in df.columns]

st.dataframe(
    df[columnas_disponibles].tail(10),
    use_container_width=True,
    hide_index=True
)
