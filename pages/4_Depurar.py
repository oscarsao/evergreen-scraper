"""
Página de depuración: duplicados y enriquecimiento de datos.
"""
import streamlit as st
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Depurar Datos", page_icon="🔧", layout="wide")

st.title("🔧 Depurar y Enriquecer Datos")
st.caption("Gestiona duplicados y completa información faltante")

# Importar consolidador para detección de duplicados
try:
    from core.consolidador import Consolidador
    CONSOLIDADOR_DISPONIBLE = True
except ImportError:
    CONSOLIDADOR_DISPONIBLE = False

# Importar Firecrawl para enriquecimiento
try:
    from adapters.firecrawl_adapter import FirecrawlAdapter, SCHEMA_ABOGADO, PROMPT_EXTRACCION
    FIRECRAWL_DISPONIBLE = True
except ImportError:
    FIRECRAWL_DISPONIBLE = False


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


def normalizar_telefono(tel: str) -> str:
    """Normaliza teléfono para comparación."""
    if not tel:
        return ""
    limpio = "".join(c for c in tel if c.isdigit() or c == "+")
    if limpio.startswith("34") and not limpio.startswith("+"):
        limpio = "+" + limpio
    elif limpio and limpio[0] in "6789":
        limpio = "+34" + limpio
    return limpio


def calcular_similitud_nombre(n1: str, n2: str) -> float:
    """Calcula similitud entre nombres."""
    if not n1 or not n2:
        return 0.0
    
    n1 = n1.lower().strip()
    n2 = n2.lower().strip()
    
    if n1 == n2:
        return 100.0
    
    try:
        from rapidfuzz import fuzz
        return max(
            fuzz.ratio(n1, n2),
            fuzz.partial_ratio(n1, n2),
            fuzz.token_sort_ratio(n1, n2)
        )
    except ImportError:
        # Fallback simple
        palabras1 = set(n1.split())
        palabras2 = set(n2.split())
        if not palabras1 or not palabras2:
            return 0.0
        comunes = palabras1 & palabras2
        total = palabras1 | palabras2
        return (len(comunes) / len(total)) * 100


def extraer_dominio(url: str) -> str:
    """Extrae dominio de URL."""
    if not url:
        return ""
    url = url.lower().replace("https://", "").replace("http://", "").replace("www.", "")
    return url.split("/")[0]


def detectar_posibles_duplicados(registros: list, umbral_nombre: float = 75) -> list:
    """
    Detecta pares de posibles duplicados.
    
    Returns:
        Lista de tuplas: (idx1, idx2, registro1, registro2, razon, similitud)
    """
    duplicados = []
    n = len(registros)
    
    # Índices para búsqueda rápida
    indice_telefono = {}
    indice_email = {}
    indice_dominio = {}
    
    for i, r in enumerate(registros):
        # Teléfonos
        tels = r.get("telefono", [])
        if isinstance(tels, str):
            tels = [tels]
        for tel in tels:
            tel_norm = normalizar_telefono(tel)
            if tel_norm:
                if tel_norm not in indice_telefono:
                    indice_telefono[tel_norm] = []
                indice_telefono[tel_norm].append(i)
        
        # Email
        email = (r.get("email") or "").lower()
        if email:
            if email not in indice_email:
                indice_email[email] = []
            indice_email[email].append(i)
        
        # Dominio web
        dom = extraer_dominio(r.get("web", ""))
        if dom:
            if dom not in indice_dominio:
                indice_dominio[dom] = []
            indice_dominio[dom].append(i)
    
    pares_vistos = set()
    
    # Duplicados por teléfono
    for tel, indices in indice_telefono.items():
        if len(indices) > 1:
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx1, idx2 = indices[i], indices[j]
                    par = tuple(sorted([idx1, idx2]))
                    if par not in pares_vistos:
                        pares_vistos.add(par)
                        duplicados.append((
                            idx1, idx2,
                            registros[idx1], registros[idx2],
                            f"Mismo teléfono: {tel}",
                            100
                        ))
    
    # Duplicados por email
    for email, indices in indice_email.items():
        if len(indices) > 1:
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx1, idx2 = indices[i], indices[j]
                    par = tuple(sorted([idx1, idx2]))
                    if par not in pares_vistos:
                        pares_vistos.add(par)
                        duplicados.append((
                            idx1, idx2,
                            registros[idx1], registros[idx2],
                            f"Mismo email: {email}",
                            100
                        ))
    
    # Duplicados por dominio web
    for dom, indices in indice_dominio.items():
        if len(indices) > 1:
            for i in range(len(indices)):
                for j in range(i + 1, len(indices)):
                    idx1, idx2 = indices[i], indices[j]
                    par = tuple(sorted([idx1, idx2]))
                    if par not in pares_vistos:
                        pares_vistos.add(par)
                        duplicados.append((
                            idx1, idx2,
                            registros[idx1], registros[idx2],
                            f"Mismo dominio: {dom}",
                            95
                        ))
    
    # Duplicados por nombre similar (más lento, limitar)
    if n < 500:  # Solo para bases pequeñas
        for i in range(n):
            for j in range(i + 1, n):
                par = tuple(sorted([i, j]))
                if par in pares_vistos:
                    continue
                
                n1 = registros[i].get("nombre", "")
                n2 = registros[j].get("nombre", "")
                
                similitud = calcular_similitud_nombre(n1, n2)
                if similitud >= umbral_nombre:
                    pares_vistos.add(par)
                    duplicados.append((
                        i, j,
                        registros[i], registros[j],
                        f"Nombre similar ({similitud:.0f}%)",
                        similitud
                    ))
    
    # Ordenar por similitud descendente
    duplicados.sort(key=lambda x: -x[5])
    
    return duplicados


def fusionar_registros(r1: dict, r2: dict) -> dict:
    """Fusiona dos registros, combinando sus datos."""
    fusionado = r1.copy()
    
    # Combinar teléfonos
    tels1 = r1.get("telefono", [])
    tels2 = r2.get("telefono", [])
    if isinstance(tels1, str):
        tels1 = [tels1]
    if isinstance(tels2, str):
        tels2 = [tels2]
    
    tels_norm = {}
    for t in tels1 + tels2:
        tn = normalizar_telefono(t)
        if tn and tn not in tels_norm:
            tels_norm[tn] = t
    fusionado["telefono"] = list(tels_norm.values())
    
    # Combinar especialidades
    esp1 = r1.get("especialidades", [])
    esp2 = r2.get("especialidades", [])
    fusionado["especialidades"] = list(set(esp1 + esp2))
    
    # Completar campos vacíos
    for campo in ["email", "web", "direccion", "ciudad", "distrito", "horario"]:
        if not r1.get(campo) and r2.get(campo):
            fusionado[campo] = r2[campo]
    
    fusionado["fecha_actualizacion"] = datetime.now().isoformat()
    
    return fusionado


def enriquecer_con_firecrawl(registro: dict) -> dict:
    """Usa Firecrawl para obtener datos faltantes de la web del despacho."""
    if not FIRECRAWL_DISPONIBLE:
        return registro
    
    web = registro.get("web")
    if not web:
        return registro
    
    adapter = FirecrawlAdapter()
    if not adapter.esta_disponible():
        st.warning("Firecrawl no está configurado. Añade FIRECRAWL_API_KEY en .env")
        return registro
    
    try:
        # Primero intentar extracción estructurada
        st.info(f"Extrayendo datos de {web}...")
        
        # Scrapear página de contacto o principal
        contenido = adapter.scrape_pagina_contacto(web)
        
        if contenido:
            # Intentar extracción estructurada
            resultados = adapter.extract_structured([web])
            
            if resultados:
                datos_nuevos = resultados[0].to_dict()
                
                # Actualizar registro con datos nuevos (sin sobrescribir existentes)
                actualizado = registro.copy()
                
                # Teléfonos: añadir nuevos
                tels_existentes = set(normalizar_telefono(t) for t in registro.get("telefono", []))
                tels_nuevos = datos_nuevos.get("telefono", [])
                for tel in tels_nuevos:
                    if normalizar_telefono(tel) not in tels_existentes:
                        if "telefono" not in actualizado:
                            actualizado["telefono"] = []
                        actualizado["telefono"].append(tel)
                
                # Campos simples: completar si vacío
                for campo in ["email", "direccion", "horario"]:
                    if not registro.get(campo) and datos_nuevos.get(campo):
                        actualizado[campo] = datos_nuevos[campo]
                
                # Especialidades: añadir nuevas
                esp_existentes = set(registro.get("especialidades", []))
                for esp in datos_nuevos.get("especialidades", []):
                    if esp not in esp_existentes:
                        if "especialidades" not in actualizado:
                            actualizado["especialidades"] = []
                        actualizado["especialidades"].append(esp)
                
                actualizado["fecha_actualizacion"] = datetime.now().isoformat()
                return actualizado
        
        return registro
        
    except Exception as e:
        st.error(f"Error al extraer datos: {e}")
        return registro


# === INTERFAZ ===

# Sidebar
with st.sidebar:
    st.header("Configuracion")
    
    ciudades = listar_ciudades()
    if not ciudades:
        st.warning("No hay datos cargados")
        st.stop()
    
    ciudad_sel = st.selectbox("Ciudad", ciudades)
    
    st.divider()
    
    st.subheader("Estado APIs")
    if FIRECRAWL_DISPONIBLE:
        adapter = FirecrawlAdapter()
        if adapter.esta_disponible():
            st.success("OK Firecrawl")
        else:
            st.warning("X Firecrawl (sin API key)")
    else:
        st.warning("X Firecrawl (no instalado)")


# Cargar datos
data = cargar_datos_ciudad(ciudad_sel)
registros = data.get("registros", [])

st.metric("Total registros", len(registros))

# Tabs principales
tab1, tab2, tab3 = st.tabs(["🔍 Duplicados", "📥 Enriquecer Datos", "🗑️ Limpieza Manual"])

# === TAB 1: DUPLICADOS ===
with tab1:
    st.subheader("Detectar y Gestionar Duplicados")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        umbral = st.slider("Umbral similitud nombre (%)", 60, 95, 75)
    with col2:
        if st.button("🔍 Buscar Duplicados", type="primary"):
            st.session_state["buscar_duplicados"] = True
    
    if st.session_state.get("buscar_duplicados"):
        with st.spinner("Analizando registros..."):
            duplicados = detectar_posibles_duplicados(registros, umbral)
        
        if not duplicados:
            st.success("No se encontraron duplicados potenciales")
        else:
            st.warning(f"Se encontraron {len(duplicados)} pares de posibles duplicados")
            
            # Guardar en session_state para persistencia
            if "duplicados_pendientes" not in st.session_state:
                st.session_state["duplicados_pendientes"] = duplicados
            
            # Mostrar cada par
            for i, (idx1, idx2, r1, r2, razon, similitud) in enumerate(duplicados[:20]):
                with st.expander(f"Par #{i+1}: {razon}", expanded=(i < 3)):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Registro A**")
                        st.write(f"**{r1.get('nombre', 'Sin nombre')}**")
                        
                        tels = r1.get("telefono", [])
                        if tels:
                            st.write(f"Tel: {', '.join(tels) if isinstance(tels, list) else tels}")
                        if r1.get("email"):
                            st.write(f"Email: {r1['email']}")
                        if r1.get("web"):
                            st.write(f"Web: {r1['web'][:40]}...")
                        if r1.get("direccion"):
                            st.caption(f"Dir: {r1['direccion'][:50]}...")
                    
                    with col2:
                        st.markdown("**Registro B**")
                        st.write(f"**{r2.get('nombre', 'Sin nombre')}**")
                        
                        tels = r2.get("telefono", [])
                        if tels:
                            st.write(f"Tel: {', '.join(tels) if isinstance(tels, list) else tels}")
                        if r2.get("email"):
                            st.write(f"Email: {r2['email']}")
                        if r2.get("web"):
                            st.write(f"Web: {r2['web'][:40]}...")
                        if r2.get("direccion"):
                            st.caption(f"Dir: {r2['direccion'][:50]}...")
                    
                    # Acciones
                    st.divider()
                    accion_col1, accion_col2, accion_col3, accion_col4 = st.columns(4)
                    
                    with accion_col1:
                        if st.button("🔗 Fusionar", key=f"fusionar_{i}", help="Combina ambos registros"):
                            fusionado = fusionar_registros(r1, r2)
                            # Eliminar el segundo, actualizar el primero
                            registros[idx1] = fusionado
                            registros.pop(idx2)
                            data["registros"] = registros
                            guardar_datos_ciudad(ciudad_sel, data)
                            st.success("Registros fusionados")
                            st.session_state["buscar_duplicados"] = False
                            st.rerun()
                    
                    with accion_col2:
                        if st.button("✅ Mantener A", key=f"keep_a_{i}", help="Elimina B"):
                            registros.pop(idx2)
                            data["registros"] = registros
                            guardar_datos_ciudad(ciudad_sel, data)
                            st.success("Registro B eliminado")
                            st.session_state["buscar_duplicados"] = False
                            st.rerun()
                    
                    with accion_col3:
                        if st.button("✅ Mantener B", key=f"keep_b_{i}", help="Elimina A"):
                            registros.pop(idx1)
                            data["registros"] = registros
                            guardar_datos_ciudad(ciudad_sel, data)
                            st.success("Registro A eliminado")
                            st.session_state["buscar_duplicados"] = False
                            st.rerun()
                    
                    with accion_col4:
                        if st.button("⏭️ No son duplicados", key=f"skip_{i}", help="Mantiene ambos"):
                            st.info("Registros marcados como diferentes")
            
            if len(duplicados) > 20:
                st.info(f"Mostrando 20 de {len(duplicados)} pares. Resuelve estos primero.")


# === TAB 2: ENRIQUECER DATOS ===
with tab2:
    st.subheader("Completar Datos Faltantes")
    
    # Encontrar registros incompletos
    incompletos = []
    for i, r in enumerate(registros):
        tiene_tel = bool(r.get("telefono"))
        tiene_email = bool(r.get("email"))
        tiene_dir = bool(r.get("direccion"))
        tiene_web = bool(r.get("web"))
        
        # Tiene web pero le faltan otros datos
        if tiene_web and not (tiene_tel and tiene_email):
            incompletos.append((i, r, {
                "telefono": tiene_tel,
                "email": tiene_email,
                "direccion": tiene_dir
            }))
    
    st.write(f"**{len(incompletos)}** registros con web pero datos incompletos")
    
    if not FIRECRAWL_DISPONIBLE:
        st.error("Firecrawl no disponible. Instala: pip install firecrawl-py")
    else:
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            filtro_sin_tel = st.checkbox("Sin teléfono", value=True)
        with col2:
            filtro_sin_email = st.checkbox("Sin email", value=True)
        
        # Filtrar
        mostrar = []
        for idx, r, estado in incompletos:
            if filtro_sin_tel and not estado["telefono"]:
                mostrar.append((idx, r, estado))
            elif filtro_sin_email and not estado["email"]:
                mostrar.append((idx, r, estado))
        
        if mostrar:
            st.write(f"Mostrando {len(mostrar[:15])} registros:")
            
            for idx, r, estado in mostrar[:15]:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    
                    with col1:
                        st.write(f"**{r.get('nombre', 'Sin nombre')[:50]}**")
                        st.caption(r.get("web", "")[:60])
                    
                    with col2:
                        faltan = []
                        if not estado["telefono"]:
                            faltan.append("Tel")
                        if not estado["email"]:
                            faltan.append("Email")
                        if not estado["direccion"]:
                            faltan.append("Dir")
                        st.write(f"Falta: {', '.join(faltan)}")
                    
                    with col3:
                        if st.button("📥 Obtener", key=f"enrich_{idx}"):
                            with st.spinner("Extrayendo..."):
                                actualizado = enriquecer_con_firecrawl(r)
                                
                                if actualizado != r:
                                    registros[idx] = actualizado
                                    data["registros"] = registros
                                    guardar_datos_ciudad(ciudad_sel, data)
                                    st.success("Datos actualizados")
                                    st.rerun()
                                else:
                                    st.warning("No se encontraron datos nuevos")
            
            st.divider()
            
            # Enriquecimiento masivo
            if st.button("📥 Enriquecer todos (usa créditos API)", type="secondary"):
                progress = st.progress(0)
                actualizados = 0
                
                for i, (idx, r, estado) in enumerate(mostrar[:10]):  # Limitar a 10
                    progress.progress((i + 1) / min(len(mostrar), 10))
                    
                    actualizado = enriquecer_con_firecrawl(r)
                    if actualizado != r:
                        registros[idx] = actualizado
                        actualizados += 1
                
                if actualizados > 0:
                    data["registros"] = registros
                    guardar_datos_ciudad(ciudad_sel, data)
                    st.success(f"{actualizados} registros actualizados")
                    st.rerun()
                else:
                    st.info("No se encontraron datos nuevos")
        else:
            st.success("Todos los registros con web tienen datos completos")


# === TAB 3: LIMPIEZA MANUAL ===
with tab3:
    st.subheader("Eliminar Registros")
    
    # Búsqueda
    busqueda = st.text_input("Buscar por nombre", "")
    
    if busqueda:
        encontrados = [
            (i, r) for i, r in enumerate(registros)
            if busqueda.lower() in r.get("nombre", "").lower()
        ]
        
        st.write(f"{len(encontrados)} resultados")
        
        for idx, r in encontrados[:20]:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    st.write(f"**{r.get('nombre', 'Sin nombre')}**")
                    info = []
                    if r.get("telefono"):
                        tels = r["telefono"]
                        info.append(f"Tel: {', '.join(tels) if isinstance(tels, list) else tels}")
                    if r.get("email"):
                        info.append(f"Email: {r['email']}")
                    if r.get("web"):
                        info.append(f"Web: {r['web'][:40]}")
                    st.caption(" | ".join(info) if info else "Sin datos de contacto")
                
                with col2:
                    if st.button("🗑️ Eliminar", key=f"del_{idx}"):
                        registros.pop(idx)
                        data["registros"] = registros
                        guardar_datos_ciudad(ciudad_sel, data)
                        st.success("Registro eliminado")
                        st.rerun()
    else:
        st.info("Escribe un término de búsqueda para encontrar registros")
    
    st.divider()
    
    # Estadísticas de limpieza
    st.subheader("Resumen de Datos")
    
    sin_nombre = sum(1 for r in registros if not r.get("nombre"))
    sin_contacto = sum(1 for r in registros if not (r.get("telefono") or r.get("email") or r.get("web")))
    con_todo = sum(1 for r in registros if r.get("telefono") and r.get("email") and r.get("web"))
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Sin nombre", sin_nombre)
    with col2:
        st.metric("Sin contacto", sin_contacto)
    with col3:
        st.metric("Completos", con_todo)
    
    if sin_nombre > 0 or sin_contacto > 0:
        if st.button("🧹 Limpiar registros sin datos", type="secondary"):
            antes = len(registros)
            registros = [
                r for r in registros
                if r.get("nombre") and (r.get("telefono") or r.get("email") or r.get("web"))
            ]
            eliminados = antes - len(registros)
            
            data["registros"] = registros
            guardar_datos_ciudad(ciudad_sel, data)
            st.success(f"Eliminados {eliminados} registros sin datos")
            st.rerun()
