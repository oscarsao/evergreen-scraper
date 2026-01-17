"""
Página de gestión de duplicados.
"""
import streamlit as st
import json
from pathlib import Path
from typing import List, Dict

st.set_page_config(page_title="Duplicados", page_icon="🔄", layout="wide")

st.title("🔄 Gestión de Duplicados")
st.caption("Detecta y resuelve posibles registros duplicados")


def cargar_todos_registros():
    """Carga todos los registros."""
    data_dir = Path("data")
    registros = []
    
    for archivo in data_dir.glob("*.json"):
        if "config" in archivo.name:
            continue
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            for r in data.get("registros", []):
                r["_ciudad"] = archivo.stem.title()
                r["_archivo"] = str(archivo)
                registros.append(r)
        except:
            continue
    
    return registros


def normalizar_telefono(tel: str) -> str:
    """Normaliza teléfono para comparación."""
    if not tel:
        return ""
    return "".join(c for c in tel if c.isdigit())


def calcular_similitud_simple(nombre1: str, nombre2: str) -> float:
    """Calcula similitud simple entre nombres."""
    n1 = nombre1.lower().strip()
    n2 = nombre2.lower().strip()
    
    if n1 == n2:
        return 100.0
    
    # Comparar palabras comunes
    palabras1 = set(n1.split())
    palabras2 = set(n2.split())
    
    if not palabras1 or not palabras2:
        return 0.0
    
    comunes = palabras1 & palabras2
    total = palabras1 | palabras2
    
    return len(comunes) / len(total) * 100


def detectar_duplicados(registros: List[Dict]) -> List[tuple]:
    """Detecta posibles duplicados."""
    duplicados = []
    vistos = set()
    
    for i, r1 in enumerate(registros):
        for j, r2 in enumerate(registros[i+1:], i+1):
            par = (min(i, j), max(i, j))
            if par in vistos:
                continue
            
            es_duplicado = False
            razon = ""
            
            # Por teléfono
            tels1 = set(normalizar_telefono(t) for t in r1.get("telefono", []) if t)
            tels2 = set(normalizar_telefono(t) for t in r2.get("telefono", []) if t)
            
            if tels1 & tels2:
                es_duplicado = True
                razon = "Mismo teléfono"
            
            # Por email
            elif r1.get("email") and r2.get("email"):
                if r1["email"].lower() == r2["email"].lower():
                    es_duplicado = True
                    razon = "Mismo email"
            
            # Por nombre muy similar
            elif calcular_similitud_simple(r1.get("nombre", ""), r2.get("nombre", "")) > 85:
                es_duplicado = True
                razon = "Nombre similar"
            
            if es_duplicado:
                vistos.add(par)
                duplicados.append((r1, r2, razon))
    
    return duplicados


# Cargar registros
registros = cargar_todos_registros()

if not registros:
    st.warning("No hay registros cargados.")
    st.stop()

# Detectar duplicados
with st.spinner("Analizando duplicados..."):
    duplicados = detectar_duplicados(registros)

# Mostrar resultados
st.metric("Posibles Duplicados Encontrados", len(duplicados))

if not duplicados:
    st.success("No se encontraron duplicados evidentes.")
    st.stop()

st.divider()

# Lista de duplicados
for i, (r1, r2, razon) in enumerate(duplicados):
    with st.expander(f"#{i+1}: {razon} - {r1.get('nombre', '')[:30]}...", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Registro 1")
            st.write(f"**Nombre:** {r1.get('nombre', '')}")
            st.write(f"**Tipo:** {r1.get('tipo', '')}")
            st.write(f"**Ciudad:** {r1.get('_ciudad', '')}")
            
            tels = r1.get("telefono", [])
            if tels:
                st.write(f"**Teléfono:** {', '.join(tels) if isinstance(tels, list) else tels}")
            
            if r1.get("email"):
                st.write(f"**Email:** {r1['email']}")
            if r1.get("web"):
                st.write(f"**Web:** {r1['web']}")
            if r1.get("direccion"):
                st.write(f"**Dirección:** {r1['direccion'][:50]}...")
        
        with col2:
            st.subheader("Registro 2")
            st.write(f"**Nombre:** {r2.get('nombre', '')}")
            st.write(f"**Tipo:** {r2.get('tipo', '')}")
            st.write(f"**Ciudad:** {r2.get('_ciudad', '')}")
            
            tels = r2.get("telefono", [])
            if tels:
                st.write(f"**Teléfono:** {', '.join(tels) if isinstance(tels, list) else tels}")
            
            if r2.get("email"):
                st.write(f"**Email:** {r2['email']}")
            if r2.get("web"):
                st.write(f"**Web:** {r2['web']}")
            if r2.get("direccion"):
                st.write(f"**Dirección:** {r2['direccion'][:50]}...")
        
        st.divider()
        
        # Acciones
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            if st.button("✅ Mantener Registro 1", key=f"keep1_{i}"):
                st.info("Funcionalidad de fusión próximamente")
        
        with col_b:
            if st.button("✅ Mantener Registro 2", key=f"keep2_{i}"):
                st.info("Funcionalidad de fusión próximamente")
        
        with col_c:
            if st.button("🔀 Fusionar", key=f"merge_{i}"):
                st.info("Funcionalidad de fusión próximamente")

st.divider()

# Acciones masivas
st.subheader("Acciones Masivas")

col1, col2 = st.columns(2)

with col1:
    if st.button("🔍 Re-escanear", use_container_width=True):
        st.rerun()

with col2:
    if st.button("📊 Exportar Reporte", use_container_width=True):
        # Crear reporte
        reporte = {
            "fecha": str(Path),
            "total_registros": len(registros),
            "duplicados_detectados": len(duplicados),
            "detalles": [
                {
                    "registro1": r1.get("nombre"),
                    "registro2": r2.get("nombre"),
                    "razon": razon
                }
                for r1, r2, razon in duplicados
            ]
        }
        
        st.download_button(
            "📥 Descargar JSON",
            json.dumps(reporte, ensure_ascii=False, indent=2),
            "reporte_duplicados.json",
            "application/json"
        )
