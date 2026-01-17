"""
Página de exploración y gestión de datos.
"""
import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.set_page_config(page_title="Datos", page_icon="📊", layout="wide")

st.title("📊 Explorar Datos")
st.caption("Visualiza, filtra y gestiona los registros")


def cargar_datos_ciudad(ciudad: str):
    """Carga datos de una ciudad específica."""
    archivo = Path("data") / f"{ciudad.lower()}.json"
    if archivo.exists():
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"metadata": {}, "registros": []}


def guardar_datos_ciudad(ciudad: str, data: dict):
    """Guarda datos de una ciudad."""
    archivo = Path("data") / f"{ciudad.lower()}.json"
    archivo.parent.mkdir(exist_ok=True)
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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


# Sidebar - Filtros
with st.sidebar:
    st.header("🔍 Filtros")
    
    # Seleccionar ciudad
    ciudades = listar_ciudades()
    if not ciudades:
        st.warning("No hay datos cargados")
        st.stop()
    
    ciudad_sel = st.selectbox("Ciudad", ["Todas"] + ciudades)
    
    # Filtro por tipo
    tipo_filtro = st.selectbox(
        "Tipo",
        ["Todos", "despacho", "abogado", "ong"]
    )
    
    # Filtro por contacto
    st.subheader("Contacto")
    filtro_telefono = st.checkbox("Con teléfono", value=False)
    filtro_email = st.checkbox("Con email", value=False)
    filtro_web = st.checkbox("Con web", value=False)
    
    # Búsqueda por nombre
    busqueda = st.text_input("Buscar por nombre", "")

# Cargar datos
if ciudad_sel == "Todas":
    registros = []
    for ciudad in ciudades:
        data = cargar_datos_ciudad(ciudad)
        for r in data.get("registros", []):
            r["_ciudad"] = ciudad
            registros.append(r)
else:
    data = cargar_datos_ciudad(ciudad_sel)
    registros = data.get("registros", [])
    for r in registros:
        r["_ciudad"] = ciudad_sel

# Aplicar filtros
registros_filtrados = registros.copy()

if tipo_filtro != "Todos":
    registros_filtrados = [r for r in registros_filtrados if r.get("tipo") == tipo_filtro]

if filtro_telefono:
    registros_filtrados = [r for r in registros_filtrados if r.get("telefono")]

if filtro_email:
    registros_filtrados = [r for r in registros_filtrados if r.get("email")]

if filtro_web:
    registros_filtrados = [r for r in registros_filtrados if r.get("web")]

if busqueda:
    registros_filtrados = [
        r for r in registros_filtrados 
        if busqueda.lower() in r.get("nombre", "").lower()
    ]

# Mostrar métricas
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Filtrados", len(registros_filtrados))
with col2:
    st.metric("Total en Base", len(registros))
with col3:
    if registros:
        porcentaje = len(registros_filtrados) / len(registros) * 100
        st.metric("% Mostrado", f"{porcentaje:.1f}%")

st.divider()

# Tabs para diferentes vistas
tab1, tab2, tab3 = st.tabs(["📋 Tabla", "🗂️ Tarjetas", "✏️ Editar"])

with tab1:
    if registros_filtrados:
        # Convertir a DataFrame
        df = pd.DataFrame(registros_filtrados)
        
        # Seleccionar columnas a mostrar
        columnas_disponibles = list(df.columns)
        columnas_default = ["nombre", "tipo", "_ciudad", "email", "web"]
        columnas_mostrar = [c for c in columnas_default if c in columnas_disponibles]
        
        # Procesar teléfono para mostrar
        if "telefono" in df.columns:
            df["telefono_str"] = df["telefono"].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else str(x) if x else ""
            )
            columnas_mostrar.insert(3, "telefono_str")
        
        st.dataframe(
            df[columnas_mostrar],
            use_container_width=True,
            hide_index=True,
            height=500
        )
        
        # Opción de descarga
        csv = df[columnas_mostrar].to_csv(index=False)
        st.download_button(
            "📥 Descargar CSV",
            csv,
            f"abogados_{ciudad_sel.lower()}.csv",
            "text/csv"
        )
    else:
        st.info("No hay registros que coincidan con los filtros")

with tab2:
    if registros_filtrados:
        # Vista de tarjetas
        cols = st.columns(2)
        
        for i, registro in enumerate(registros_filtrados[:20]):
            col = cols[i % 2]
            
            with col:
                with st.container(border=True):
                    st.markdown(f"**{registro.get('nombre', 'Sin nombre')}**")
                    st.caption(f"{registro.get('tipo', 'despacho')} | {registro.get('_ciudad', '')}")
                    
                    if registro.get("telefono"):
                        tels = registro["telefono"]
                        if isinstance(tels, list):
                            st.write(f"📞 {', '.join(tels)}")
                        else:
                            st.write(f"📞 {tels}")
                    
                    if registro.get("email"):
                        st.write(f"📧 {registro['email']}")
                    
                    if registro.get("web"):
                        st.write(f"🌐 [{registro['web'][:30]}...]({registro['web']})")
                    
                    if registro.get("direccion"):
                        st.caption(f"📍 {registro['direccion'][:50]}...")
        
        if len(registros_filtrados) > 20:
            st.info(f"Mostrando 20 de {len(registros_filtrados)} registros")
    else:
        st.info("No hay registros que mostrar")

with tab3:
    st.subheader("Editar Registro")
    
    if registros_filtrados:
        # Selector de registro
        nombres = [r.get("nombre", f"Sin nombre {i}") for i, r in enumerate(registros_filtrados)]
        registro_sel = st.selectbox("Seleccionar registro", nombres)
        
        idx = nombres.index(registro_sel)
        registro = registros_filtrados[idx]
        
        # Formulario de edición
        with st.form("editar_registro"):
            nombre_edit = st.text_input("Nombre", registro.get("nombre", ""))
            tipo_edit = st.selectbox(
                "Tipo", 
                ["despacho", "abogado", "ong"],
                index=["despacho", "abogado", "ong"].index(registro.get("tipo", "despacho"))
            )
            
            tels = registro.get("telefono", [])
            telefono_edit = st.text_input(
                "Teléfono(s)", 
                ", ".join(tels) if isinstance(tels, list) else str(tels) if tels else ""
            )
            
            email_edit = st.text_input("Email", registro.get("email", "") or "")
            web_edit = st.text_input("Web", registro.get("web", "") or "")
            direccion_edit = st.text_area("Dirección", registro.get("direccion", "") or "")
            
            submitted = st.form_submit_button("💾 Guardar Cambios")
            
            if submitted:
                # Actualizar registro
                registro["nombre"] = nombre_edit
                registro["tipo"] = tipo_edit
                registro["telefono"] = [t.strip() for t in telefono_edit.split(",") if t.strip()]
                registro["email"] = email_edit if email_edit else None
                registro["web"] = web_edit if web_edit else None
                registro["direccion"] = direccion_edit if direccion_edit else None
                
                # Guardar en archivo
                ciudad = registro.get("_ciudad", ciudad_sel)
                data = cargar_datos_ciudad(ciudad)
                
                # Buscar y actualizar en la lista
                for i, r in enumerate(data.get("registros", [])):
                    if r.get("nombre") == nombres[idx]:
                        data["registros"][i] = {k: v for k, v in registro.items() if k != "_ciudad"}
                        break
                
                guardar_datos_ciudad(ciudad, data)
                st.success("Registro actualizado")
                st.rerun()
    else:
        st.info("No hay registros para editar")
