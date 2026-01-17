"""
Sistema de Enriquecimiento de Datos
===================================
Completa información faltante usando scraping de las URLs existentes.
"""
import streamlit as st
import json
import re
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Enriquecer Datos", page_icon="📥", layout="wide")

st.title("📥 Enriquecer Datos")
st.caption("Completa teléfonos, emails y direcciones usando las URLs de cada despacho")

# === IMPORTS Y FUNCIONES ===

def cargar_datos_ciudad(ciudad: str):
    """Carga datos de una ciudad."""
    archivo = Path("data") / f"{ciudad.lower()}.json"
    if archivo.exists():
        with open(archivo, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"metadata": {}, "registros": []}


def guardar_datos_ciudad(ciudad: str, data: dict):
    """Guarda datos de una ciudad."""
    archivo = Path("data") / f"{ciudad.lower()}.json"
    data["metadata"]["fecha_actualizacion"] = datetime.now().isoformat()
    data["metadata"]["total_registros"] = len(data.get("registros", []))
    with open(archivo, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def listar_ciudades():
    """Lista ciudades disponibles."""
    data_dir = Path("data")
    if not data_dir.exists():
        return []
    ciudades = []
    for archivo in data_dir.glob("*.json"):
        if "config" not in archivo.name and "api_usage" not in archivo.name:
            ciudades.append(archivo.stem.title())
    return sorted(ciudades)


def extraer_datos_de_html(html: str) -> dict:
    """Extrae teléfono, email y dirección de HTML/texto."""
    datos = {"telefono": [], "email": None, "direccion": None}
    
    # Patrones de teléfono español
    patrones_tel = [
        r'(?:\+34)?[\s.-]?[6789]\d{2}[\s.-]?\d{3}[\s.-]?\d{3}',
        r'(?:\+34)?[\s.-]?[6789]\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}',
        r'tel[éeEÉ]?fono[:\s]+([+\d\s.-]+)',
    ]
    
    telefonos_encontrados = set()
    for patron in patrones_tel:
        matches = re.findall(patron, html, re.IGNORECASE)
        for m in matches:
            # Limpiar y normalizar
            tel = re.sub(r'[^\d+]', '', m if isinstance(m, str) else m)
            if len(tel) >= 9:
                # Normalizar formato
                if tel.startswith('34'):
                    tel = '+' + tel
                elif tel[0] in '6789' and len(tel) == 9:
                    tel = '+34' + tel
                if len(tel) >= 12:
                    telefonos_encontrados.add(tel)
    
    datos["telefono"] = list(telefonos_encontrados)[:3]
    
    # Email
    patron_email = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(patron_email, html)
    # Filtrar emails genéricos
    emails_filtrados = [
        e for e in emails 
        if not any(x in e.lower() for x in ['example', 'test', 'noreply', 'wordpress', 'wix'])
    ]
    if emails_filtrados:
        datos["email"] = emails_filtrados[0]
    
    # Dirección (patrón básico)
    patrones_dir = [
        r'(?:C/|Calle|Avda\.|Avenida|Plaza|Paseo|Pº)\s+[^<\n]{10,60}',
        r'direcci[óo]n[:\s]+([^<\n]{10,80})',
    ]
    
    for patron in patrones_dir:
        matches = re.findall(patron, html, re.IGNORECASE)
        if matches:
            dir_text = matches[0] if isinstance(matches[0], str) else matches[0]
            # Limpiar
            dir_text = re.sub(r'<[^>]+>', '', dir_text)
            dir_text = dir_text.strip()
            if len(dir_text) > 10:
                datos["direccion"] = dir_text[:100]
                break
    
    return datos


def enriquecer_con_firecrawl(url: str) -> dict:
    """Usa Firecrawl para scrapear una URL y extraer datos."""
    try:
        from adapters.firecrawl_adapter import FirecrawlAdapter
        
        adapter = FirecrawlAdapter()
        if not adapter.esta_disponible():
            return {"error": "Firecrawl no disponible"}
        
        # Scrapear página
        resultado = adapter.scrape_url(url, formats=["markdown"])
        
        if resultado and resultado.get("markdown"):
            return extraer_datos_de_html(resultado["markdown"])
        
        return {"error": "No se pudo obtener contenido"}
        
    except Exception as e:
        return {"error": str(e)}


def enriquecer_con_tavily(url: str, nombre: str) -> dict:
    """Usa Tavily para buscar información adicional."""
    try:
        from adapters.tavily_adapter import TavilyAdapter
        
        adapter = TavilyAdapter()
        if not adapter.esta_disponible():
            return {"error": "Tavily no disponible"}
        
        # Buscar información de contacto
        query = f'"{nombre}" contacto teléfono email'
        resultados = adapter.search(query, max_results=3)
        
        datos = {"telefono": [], "email": None, "direccion": None}
        
        for r in resultados:
            if r.telefono:
                datos["telefono"].extend(r.telefono)
            if r.email and not datos["email"]:
                datos["email"] = r.email
            if r.direccion and not datos["direccion"]:
                datos["direccion"] = r.direccion
        
        # Eliminar duplicados de teléfono
        datos["telefono"] = list(set(datos["telefono"]))[:3]
        
        return datos
        
    except Exception as e:
        return {"error": str(e)}


def enriquecer_con_requests(url: str) -> dict:
    """Scrapeo básico con requests (sin API)."""
    try:
        import requests
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return extraer_datos_de_html(response.text)
        
        return {"error": f"HTTP {response.status_code}"}
        
    except Exception as e:
        return {"error": str(e)}


# === INTERFAZ ===

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuración")
    
    ciudades = listar_ciudades()
    if not ciudades:
        st.warning("No hay datos cargados")
        st.stop()
    
    ciudad_sel = st.selectbox("Ciudad", ciudades)
    
    st.divider()
    
    # Método de enriquecimiento
    st.subheader("Método")
    metodo = st.radio(
        "Usar",
        ["Requests (sin API)", "Tavily (búsqueda)", "Firecrawl (scraping)"],
        index=0,
        help="Requests es gratis pero menos preciso. Tavily y Firecrawl usan créditos API."
    )
    
    st.divider()
    
    # Filtros
    st.subheader("Filtros")
    filtro_sin_tel = st.checkbox("Sin teléfono", value=True)
    filtro_sin_email = st.checkbox("Sin email", value=True)
    filtro_sin_dir = st.checkbox("Sin dirección", value=False)


# Cargar datos
data = cargar_datos_ciudad(ciudad_sel)
registros = data.get("registros", [])

# Filtrar registros que necesitan enriquecimiento
def necesita_enriquecimiento(r):
    if not r.get("web"):
        return False
    
    condiciones = []
    if filtro_sin_tel:
        condiciones.append(not r.get("telefono"))
    if filtro_sin_email:
        condiciones.append(not r.get("email"))
    if filtro_sin_dir:
        condiciones.append(not r.get("direccion"))
    
    return any(condiciones) if condiciones else False

registros_filtrados = [(i, r) for i, r in enumerate(registros) if necesita_enriquecimiento(r)]

# === MÉTRICAS ===
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Registros", len(registros))
with col2:
    st.metric("Necesitan Datos", len(registros_filtrados))
with col3:
    sin_tel = sum(1 for r in registros if not r.get("telefono"))
    st.metric("Sin Teléfono", sin_tel)
with col4:
    sin_email = sum(1 for r in registros if not r.get("email"))
    st.metric("Sin Email", sin_email)

st.divider()

# === TABS ===
tab1, tab2, tab3 = st.tabs(["📋 Lista para Enriquecer", "⚡ Enriquecimiento Masivo", "🔍 Enriquecer Individual"])

# --- TAB 1: Lista ---
with tab1:
    if not registros_filtrados:
        st.success("✓ Todos los registros tienen los datos seleccionados")
    else:
        st.write(f"**{len(registros_filtrados)}** registros necesitan enriquecimiento:")
        
        # Mostrar en tabla
        tabla_data = []
        for idx, r in registros_filtrados[:50]:
            falta = []
            if not r.get("telefono"):
                falta.append("Tel")
            if not r.get("email"):
                falta.append("Email")
            if not r.get("direccion"):
                falta.append("Dir")
            
            tabla_data.append({
                "Nombre": r.get("nombre", "Sin nombre")[:40],
                "Web": r.get("web", "")[:50],
                "Falta": ", ".join(falta),
                "idx": idx
            })
        
        # Dataframe con selección
        import pandas as pd
        df = pd.DataFrame(tabla_data)
        
        st.dataframe(
            df[["Nombre", "Web", "Falta"]],
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        if len(registros_filtrados) > 50:
            st.caption(f"Mostrando 50 de {len(registros_filtrados)}")

# --- TAB 2: Masivo ---
with tab2:
    st.subheader("Enriquecimiento Masivo")
    
    col1, col2 = st.columns(2)
    with col1:
        cantidad = st.slider("Cantidad de registros", 1, min(20, len(registros_filtrados)), 5)
    with col2:
        st.write(f"Método: **{metodo}**")
    
    if st.button("🚀 Iniciar Enriquecimiento", type="primary", disabled=len(registros_filtrados) == 0):
        progress = st.progress(0)
        status = st.empty()
        resultados_enriq = {"exito": 0, "sin_datos": 0, "error": 0}
        
        for i, (idx, r) in enumerate(registros_filtrados[:cantidad]):
            progress.progress((i + 1) / cantidad)
            status.write(f"Procesando: {r.get('nombre', 'Sin nombre')[:40]}...")
            
            url = r.get("web", "")
            nombre = r.get("nombre", "")
            
            # Enriquecer según método
            if "Firecrawl" in metodo:
                datos = enriquecer_con_firecrawl(url)
            elif "Tavily" in metodo:
                datos = enriquecer_con_tavily(url, nombre)
            else:
                datos = enriquecer_con_requests(url)
            
            # Aplicar datos encontrados
            if "error" in datos:
                resultados_enriq["error"] += 1
            else:
                cambios = False
                
                # Teléfonos: añadir nuevos
                if datos.get("telefono"):
                    tels_existentes = set(r.get("telefono", []))
                    for tel in datos["telefono"]:
                        if tel not in tels_existentes:
                            if "telefono" not in registros[idx]:
                                registros[idx]["telefono"] = []
                            registros[idx]["telefono"].append(tel)
                            cambios = True
                
                # Email: solo si no existe
                if datos.get("email") and not r.get("email"):
                    registros[idx]["email"] = datos["email"]
                    cambios = True
                
                # Dirección: solo si no existe
                if datos.get("direccion") and not r.get("direccion"):
                    registros[idx]["direccion"] = datos["direccion"]
                    cambios = True
                
                if cambios:
                    registros[idx]["fecha_actualizacion"] = datetime.now().isoformat()
                    resultados_enriq["exito"] += 1
                else:
                    resultados_enriq["sin_datos"] += 1
        
        # Guardar
        data["registros"] = registros
        guardar_datos_ciudad(ciudad_sel, data)
        
        progress.empty()
        status.empty()
        
        # Mostrar resultados
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Actualizados", resultados_enriq["exito"])
        with col2:
            st.metric("Sin datos nuevos", resultados_enriq["sin_datos"])
        with col3:
            st.metric("Errores", resultados_enriq["error"])
        
        if resultados_enriq["exito"] > 0:
            st.success(f"✓ {resultados_enriq['exito']} registros actualizados")
            st.rerun()

# --- TAB 3: Individual ---
with tab3:
    st.subheader("Enriquecer Registro Individual")
    
    if registros_filtrados:
        # Selector de registro
        opciones = [f"{r.get('nombre', 'Sin nombre')[:40]} - {r.get('web', '')[:30]}" 
                   for _, r in registros_filtrados[:100]]
        
        seleccion = st.selectbox("Seleccionar registro", opciones)
        idx_sel = opciones.index(seleccion)
        idx_real, registro = registros_filtrados[idx_sel]
        
        # Mostrar datos actuales
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Datos Actuales:**")
            st.write(f"Nombre: {registro.get('nombre', 'Sin nombre')}")
            st.write(f"Web: {registro.get('web', 'N/A')}")
            
            tels = registro.get("telefono", [])
            st.write(f"Teléfono: {', '.join(tels) if tels else '❌ Sin dato'}")
            st.write(f"Email: {registro.get('email') or '❌ Sin dato'}")
            st.write(f"Dirección: {registro.get('direccion') or '❌ Sin dato'}")
        
        with col2:
            st.markdown("**Enriquecer:**")
            
            if st.button("🔍 Buscar Datos", type="primary"):
                with st.spinner("Buscando..."):
                    url = registro.get("web", "")
                    nombre = registro.get("nombre", "")
                    
                    # Probar todos los métodos
                    st.write("Probando Requests...")
                    datos_req = enriquecer_con_requests(url)
                    
                    # Mostrar resultados
                    st.markdown("**Datos Encontrados:**")
                    
                    if "error" in datos_req:
                        st.warning(f"Error: {datos_req['error']}")
                    else:
                        if datos_req.get("telefono"):
                            st.write(f"📞 Teléfonos: {', '.join(datos_req['telefono'])}")
                        if datos_req.get("email"):
                            st.write(f"📧 Email: {datos_req['email']}")
                        if datos_req.get("direccion"):
                            st.write(f"📍 Dirección: {datos_req['direccion']}")
                        
                        if any([datos_req.get("telefono"), datos_req.get("email"), datos_req.get("direccion")]):
                            if st.button("✅ Aplicar Datos"):
                                # Aplicar
                                if datos_req.get("telefono"):
                                    if "telefono" not in registros[idx_real]:
                                        registros[idx_real]["telefono"] = []
                                    for tel in datos_req["telefono"]:
                                        if tel not in registros[idx_real]["telefono"]:
                                            registros[idx_real]["telefono"].append(tel)
                                
                                if datos_req.get("email") and not registro.get("email"):
                                    registros[idx_real]["email"] = datos_req["email"]
                                
                                if datos_req.get("direccion") and not registro.get("direccion"):
                                    registros[idx_real]["direccion"] = datos_req["direccion"]
                                
                                registros[idx_real]["fecha_actualizacion"] = datetime.now().isoformat()
                                
                                data["registros"] = registros
                                guardar_datos_ciudad(ciudad_sel, data)
                                
                                st.success("✓ Datos aplicados")
                                st.rerun()
                        else:
                            st.info("No se encontraron datos nuevos")
    else:
        st.success("✓ Todos los registros están completos")

# === FOOTER ===
st.divider()
st.caption("Consejo: El método 'Requests' es gratuito pero menos preciso. Usa Tavily o Firecrawl para mejores resultados.")
