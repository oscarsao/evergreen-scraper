"""
Gestión de Base de Datos - Vista y Edición Avanzada
====================================================
- Vista de tabla con ordenación
- Edición en lote con checkboxes
- Limpieza de nombres
- Detección de tipo (abogado/despacho/web)
- Agrupación por web/teléfono
- Historial de cambios
"""
import streamlit as st
import json
import re
import pandas as pd
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Gestión de Datos", page_icon="📊", layout="wide")

st.title("📊 Gestión de Base de Datos")

# === FUNCIONES AUXILIARES ===

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


def limpiar_nombre(nombre: str) -> tuple:
    """
    Limpia el nombre y extrae descripción.
    Returns: (nombre_limpio, descripcion, tipo_detectado)
    """
    if not nombre:
        return "", "", "desconocido"
    
    nombre_original = nombre
    descripcion = ""
    tipo = "despacho"  # Por defecto
    
    # Patrones para detectar tipo
    patrones_abogado = [
        r'^(Abogad[oa]|Letrad[oa])\s+',
        r'\b(Abogad[oa]|Letrad[oa])\s+\w+\s+\w+$',
        r'^[A-Z][a-záéíóú]+\s+[A-Z][a-záéíóú]+\s*$',  # Nombre Apellido simple
    ]
    
    patrones_despacho = [
        r'\b(Despacho|Bufete|Abogados|& Asociados|Asociados|S\.?L\.?|Law|Legal|Lawyers)\b',
    ]
    
    patrones_web = [
        r'^(Contacto|Contact[ae]|Inicio|Home|Sobre|About|Blog|Artículo)',
        r'^\d+\s+(mejores|top)',
        r'^(Los|Las)\s+\d+\s+mejores',
        r'^\►|^\▸|^►|^→',
    ]
    
    # Detectar si es una página web (no un despacho real)
    for patron in patrones_web:
        if re.search(patron, nombre, re.IGNORECASE):
            tipo = "pagina"
            break
    
    # Detectar abogado individual
    if tipo != "pagina":
        for patron in patrones_abogado:
            if re.search(patron, nombre, re.IGNORECASE):
                tipo = "abogado"
                break
    
    # Detectar despacho
    if tipo != "pagina" and tipo != "abogado":
        for patron in patrones_despacho:
            if re.search(patron, nombre, re.IGNORECASE):
                tipo = "despacho"
                break
    
    # Limpiar nombre
    # Eliminar separadores y lo que viene después
    separadores = [' - ', ' | ', ' – ', ' — ', ' · ', ' • ', ':', ' ⚖️', ' ►', ' ▸']
    
    for sep in separadores:
        if sep in nombre:
            partes = nombre.split(sep, 1)
            nombre = partes[0].strip()
            if len(partes) > 1 and len(partes[1]) > 5:
                descripcion = partes[1].strip()
            break
    
    # Eliminar sufijos comunes de webs
    sufijos_web = [
        r'\s*\|\s*.*$',
        r'\s*[-–—]\s*(Abogados?|Despacho|Bufete|Madrid|Barcelona|Valencia|España).*$',
        r'\s*【.*】\s*$',
        r'\s*\(.*\)\s*$',
        r'\.{3,}$',
    ]
    
    for patron in sufijos_web:
        nombre = re.sub(patron, '', nombre, flags=re.IGNORECASE)
    
    # Capitalizar correctamente
    nombre = nombre.strip()
    
    # Si es muy corto o genérico, marcar como revisar
    if len(nombre) < 3 or nombre.lower() in ['contacto', 'inicio', 'home', 'about']:
        tipo = "revisar"
    
    return nombre, descripcion, tipo


def extraer_dominio(url: str) -> str:
    """Extrae dominio de URL."""
    if not url:
        return ""
    url = url.lower().replace("https://", "").replace("http://", "").replace("www.", "")
    return url.split("/")[0]


def normalizar_telefono(tel: str) -> str:
    """Normaliza teléfono para comparación."""
    if not tel:
        return ""
    limpio = re.sub(r'[^\d]', '', tel)
    if len(limpio) >= 9:
        return limpio[-9:]  # Últimos 9 dígitos
    return limpio


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


def detectar_grupos(registros: list) -> dict:
    """Detecta grupos de registros por dominio web o teléfono."""
    grupos_web = {}
    grupos_tel = {}
    
    for i, r in enumerate(registros):
        # Por dominio
        dominio = extraer_dominio(r.get("web", ""))
        if dominio:
            if dominio not in grupos_web:
                grupos_web[dominio] = []
            grupos_web[dominio].append(i)
        
        # Por teléfono
        tels = r.get("telefono", [])
        if isinstance(tels, str):
            tels = [tels]
        for tel in tels:
            tel_norm = normalizar_telefono(tel)
            if tel_norm:
                if tel_norm not in grupos_tel:
                    grupos_tel[tel_norm] = []
                if i not in grupos_tel[tel_norm]:
                    grupos_tel[tel_norm].append(i)
    
    # Solo grupos con más de 1 registro
    grupos_web = {k: v for k, v in grupos_web.items() if len(v) > 1}
    grupos_tel = {k: v for k, v in grupos_tel.items() if len(v) > 1}
    
    return {"por_web": grupos_web, "por_telefono": grupos_tel}


# === SIDEBAR ===
with st.sidebar:
    st.header("⚙️ Configuración")
    
    ciudades = listar_ciudades()
    if not ciudades:
        st.warning("No hay datos cargados")
        st.stop()
    
    ciudad_sel = st.selectbox("Ciudad", ["Todas"] + ciudades)
    
    st.divider()
    
    # Filtros
    st.subheader("🔍 Filtros")
    
    filtro_tipo = st.multiselect(
        "Tipo",
        ["despacho", "abogado", "ong", "oficial", "pagina", "revisar", "desconocido"],
        default=["despacho", "abogado"]
    )
    
    filtro_datos = st.radio(
        "Datos",
        ["Todos", "Completos", "Incompletos", "Sin teléfono", "Sin email"]
    )
    
    busqueda = st.text_input("Buscar por nombre", "")
    
    st.divider()
    
    # Ordenación
    st.subheader("📊 Ordenar por")
    orden_campo = st.selectbox(
        "Campo",
        ["nombre", "tipo", "fecha_actualizacion", "ciudad"],
        label_visibility="collapsed"
    )
    orden_dir = st.radio("Dirección", ["Ascendente", "Descendente"], horizontal=True)


# === CARGAR DATOS ===
if ciudad_sel == "Todas":
    registros = []
    for ciudad in ciudades:
        data = cargar_datos_ciudad(ciudad)
        for r in data.get("registros", []):
            r["_ciudad"] = ciudad
            r["_idx_original"] = len(registros)
            registros.append(r)
else:
    data = cargar_datos_ciudad(ciudad_sel)
    registros = data.get("registros", [])
    for i, r in enumerate(registros):
        r["_ciudad"] = ciudad_sel
        r["_idx_original"] = i

# Aplicar filtros
registros_filtrados = []
for r in registros:
    # Filtro tipo
    tipo = r.get("tipo", "despacho")
    if filtro_tipo and tipo not in filtro_tipo:
        continue
    
    # Filtro datos
    if filtro_datos == "Completos":
        if not (r.get("telefono") and r.get("email") and r.get("web")):
            continue
    elif filtro_datos == "Incompletos":
        if r.get("telefono") and r.get("email") and r.get("web"):
            continue
    elif filtro_datos == "Sin teléfono":
        if r.get("telefono"):
            continue
    elif filtro_datos == "Sin email":
        if r.get("email"):
            continue
    
    # Búsqueda
    if busqueda:
        if busqueda.lower() not in r.get("nombre", "").lower():
            continue
    
    registros_filtrados.append(r)

# Ordenar
reverse = orden_dir == "Descendente"
registros_filtrados.sort(
    key=lambda x: (x.get(orden_campo) or "").lower() if isinstance(x.get(orden_campo), str) else str(x.get(orden_campo, "")),
    reverse=reverse
)


# === MÉTRICAS ===
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Total", len(registros))
with col2:
    st.metric("Filtrados", len(registros_filtrados))
with col3:
    tipos = {}
    for r in registros:
        t = r.get("tipo", "despacho")
        tipos[t] = tipos.get(t, 0) + 1
    st.metric("Despachos", tipos.get("despacho", 0))
with col4:
    st.metric("Abogados", tipos.get("abogado", 0))
with col5:
    sin_tel = sum(1 for r in registros if not r.get("telefono"))
    st.metric("Sin Tel.", sin_tel)

st.divider()

# === TABS PRINCIPALES ===
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Vista de Tabla", 
    "✏️ Edición en Lote", 
    "🔗 Agrupar Duplicados",
    "🧹 Limpiar Nombres"
])


# === TAB 1: VISTA DE TABLA ===
with tab1:
    if not registros_filtrados:
        st.info("No hay registros que mostrar con los filtros actuales")
    else:
        # Preparar DataFrame
        tabla_data = []
        for r in registros_filtrados:
            tels = r.get("telefono", [])
            tel_str = ", ".join(tels[:2]) if isinstance(tels, list) else str(tels) if tels else ""
            if len(tels) > 2:
                tel_str += f" (+{len(tels)-2})"
            
            fecha = r.get("fecha_actualizacion", "")[:16] if r.get("fecha_actualizacion") else ""
            
            tabla_data.append({
                "Nombre": r.get("nombre", "")[:50],
                "Tipo": r.get("tipo", "despacho"),
                "Ciudad": r.get("_ciudad", ""),
                "Teléfono": tel_str[:30],
                "Email": (r.get("email") or "")[:30],
                "Web": extraer_dominio(r.get("web", ""))[:25],
                "Actualizado": fecha,
                "_idx": r.get("_idx_original", 0)
            })
        
        df = pd.DataFrame(tabla_data)
        
        # Mostrar tabla
        st.dataframe(
            df[["Nombre", "Tipo", "Ciudad", "Teléfono", "Email", "Web", "Actualizado"]],
            use_container_width=True,
            hide_index=True,
            height=500
        )
        
        # Exportar
        col1, col2 = st.columns([3, 1])
        with col2:
            csv = df.to_csv(index=False)
            st.download_button("📥 Exportar CSV", csv, "registros.csv", "text/csv")


# === TAB 2: EDICIÓN EN LOTE ===
with tab2:
    st.subheader("Edición en Lote")
    st.caption("Selecciona registros para editar múltiples a la vez")
    
    if not registros_filtrados:
        st.info("No hay registros para editar")
    else:
        # Estado de selección
        if "seleccionados" not in st.session_state:
            st.session_state.seleccionados = set()
        
        # Botones de selección
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Seleccionar todos"):
                st.session_state.seleccionados = set(r.get("_idx_original", i) for i, r in enumerate(registros_filtrados))
                st.rerun()
        with col2:
            if st.button("❌ Deseleccionar todos"):
                st.session_state.seleccionados = set()
                st.rerun()
        with col3:
            st.write(f"**{len(st.session_state.seleccionados)}** seleccionados")
        
        st.divider()
        
        # Lista con checkboxes
        for i, r in enumerate(registros_filtrados[:100]):
            idx = r.get("_idx_original", i)
            
            col_check, col_info, col_actions = st.columns([0.5, 4, 1])
            
            with col_check:
                checked = st.checkbox(
                    "sel",
                    value=idx in st.session_state.seleccionados,
                    key=f"check_{idx}",
                    label_visibility="collapsed"
                )
                if checked:
                    st.session_state.seleccionados.add(idx)
                else:
                    st.session_state.seleccionados.discard(idx)
            
            with col_info:
                nombre = r.get("nombre", "Sin nombre")[:45]
                tipo = r.get("tipo", "despacho")
                ciudad = r.get("_ciudad", "")
                
                # Indicadores
                indicadores = []
                if r.get("telefono"):
                    indicadores.append("📞")
                if r.get("email"):
                    indicadores.append("📧")
                if r.get("web"):
                    indicadores.append("🌐")
                
                st.write(f"**{nombre}** | {tipo} | {ciudad} {' '.join(indicadores)}")
            
            with col_actions:
                if st.button("✏️", key=f"edit_{idx}", help="Editar"):
                    st.session_state.editando = idx
        
        if len(registros_filtrados) > 100:
            st.caption(f"Mostrando 100 de {len(registros_filtrados)}")
        
        st.divider()
        
        # Acciones en lote
        if st.session_state.seleccionados:
            st.subheader(f"Acciones para {len(st.session_state.seleccionados)} registros")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nuevo_tipo = st.selectbox(
                    "Cambiar tipo a:",
                    ["(sin cambio)", "despacho", "abogado", "ong", "oficial", "pagina", "revisar"]
                )
            
            with col2:
                nueva_ciudad = st.selectbox(
                    "Cambiar ciudad a:",
                    ["(sin cambio)"] + ciudades
                )
            
            if st.button("💾 Aplicar cambios", type="primary"):
                # Cargar datos por ciudad y aplicar cambios
                cambios_por_ciudad = {}
                
                for idx in st.session_state.seleccionados:
                    # Encontrar el registro
                    for r in registros:
                        if r.get("_idx_original") == idx:
                            ciudad = r.get("_ciudad")
                            if ciudad not in cambios_por_ciudad:
                                cambios_por_ciudad[ciudad] = cargar_datos_ciudad(ciudad)
                            
                            # Buscar índice real
                            for i, reg in enumerate(cambios_por_ciudad[ciudad]["registros"]):
                                if reg.get("nombre") == r.get("nombre") and reg.get("web") == r.get("web"):
                                    if nuevo_tipo != "(sin cambio)":
                                        cambios_por_ciudad[ciudad]["registros"][i]["tipo"] = nuevo_tipo
                                    if nueva_ciudad != "(sin cambio)":
                                        cambios_por_ciudad[ciudad]["registros"][i]["ciudad"] = nueva_ciudad
                                    cambios_por_ciudad[ciudad]["registros"][i]["fecha_actualizacion"] = datetime.now().isoformat()
                                    break
                            break
                
                # Guardar
                for ciudad, data in cambios_por_ciudad.items():
                    guardar_datos_ciudad(ciudad, data)
                
                st.success(f"✓ {len(st.session_state.seleccionados)} registros actualizados")
                st.session_state.seleccionados = set()
                st.rerun()


# === TAB 3: AGRUPAR DUPLICADOS ===
with tab3:
    st.subheader("Detectar Posibles Duplicados")
    st.caption("Fusiona registros que comparten dominio web o teléfono")
    
    grupos = detectar_grupos(registros)
    
    # Por dominio web
    st.markdown("### 🌐 Mismo Dominio Web")
    
    if grupos["por_web"]:
        for dominio, indices in list(grupos["por_web"].items())[:20]:
            with st.expander(f"**{dominio}** ({len(indices)} registros)"):
                registros_grupo = [registros[idx] for idx in indices]
                
                # Seleccionar registro principal (el primero con más datos)
                registro_principal = None
                idx_principal = None
                max_datos = -1
                
                for idx in indices:
                    r = registros[idx]
                    datos_count = sum([bool(r.get("telefono")), bool(r.get("email")), 
                                     bool(r.get("web")), bool(r.get("direccion"))])
                    if datos_count > max_datos:
                        max_datos = datos_count
                        registro_principal = r
                        idx_principal = idx
                
                # Mostrar todos los registros del grupo
                for idx in indices:
                    r = registros[idx]
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        es_principal = "⭐ " if idx == idx_principal else "  • "
                        st.write(f"{es_principal}{r.get('nombre', 'Sin nombre')[:50]}")
                        st.caption(f"Tipo: {r.get('tipo')} | Ciudad: {r.get('_ciudad')}")
                        if r.get("telefono"):
                            tels = r.get("telefono", [])
                            tel_str = ", ".join(tels[:2]) if isinstance(tels, list) else str(tels)
                            st.caption(f"Tel: {tel_str[:30]}")
                    with col2:
                        if idx != idx_principal and ciudad_sel != "Todas":
                            if st.button("🔗 Fusionar", key=f"merge_web_{dominio}_{idx}"):
                                # Fusionar con el principal
                                fusionado = fusionar_registros(registro_principal, r)
                                
                                # Cargar datos de la ciudad
                                data = cargar_datos_ciudad(ciudad_sel)
                                
                                # Encontrar índices reales en el archivo
                                idx1_real = None
                                idx2_real = None
                                
                                for i, reg in enumerate(data["registros"]):
                                    if reg.get("nombre") == registro_principal.get("nombre") and \
                                       reg.get("web") == registro_principal.get("web"):
                                        idx1_real = i
                                    if reg.get("nombre") == r.get("nombre") and \
                                       reg.get("web") == r.get("web"):
                                        idx2_real = i
                                
                                if idx1_real is not None and idx2_real is not None:
                                    # Actualizar el principal con datos fusionados
                                    data["registros"][idx1_real] = fusionado
                                    # Eliminar el duplicado
                                    data["registros"].pop(idx2_real)
                                    # Guardar
                                    guardar_datos_ciudad(ciudad_sel, data)
                                    st.success(f"✓ Registros fusionados. {r.get('nombre', 'Sin nombre')[:30]} eliminado.")
                                    st.rerun()
                                else:
                                    st.error("No se encontraron los registros en la base de datos")
                        elif ciudad_sel == "Todas":
                            st.caption("Fusionar solo por ciudad")
                
                # Botón para fusionar todo el grupo
                if len(indices) > 2 and ciudad_sel != "Todas":
                    if st.button(f"🔗 Fusionar todos ({len(indices)} registros)", key=f"merge_all_{dominio}"):
                        data = cargar_datos_ciudad(ciudad_sel)
                        registro_final = registro_principal.copy()
                        
                        # Fusionar todos con el principal
                        indices_a_eliminar = []
                        for idx_secundario in indices:
                            if idx_secundario != idx_principal:
                                r_sec = registros[idx_secundario]
                                registro_final = fusionar_registros(registro_final, r_sec)
                                indices_a_eliminar.append(idx_secundario)
                        
                        # Encontrar y actualizar en archivo
                        idx_principal_real = None
                        for i, reg in enumerate(data["registros"]):
                            if reg.get("nombre") == registro_principal.get("nombre") and \
                               reg.get("web") == registro_principal.get("web"):
                                idx_principal_real = i
                                break
                        
                        if idx_principal_real is not None:
                            data["registros"][idx_principal_real] = registro_final
                            
                            # Eliminar duplicados
                            registros_a_eliminar = []
                            for idx_elim in indices_a_eliminar:
                                r_elim = registros[idx_elim]
                                for i, reg in enumerate(data["registros"]):
                                    if reg.get("nombre") == r_elim.get("nombre") and \
                                       reg.get("web") == r_elim.get("web"):
                                        registros_a_eliminar.append(i)
                            
                            # Eliminar en orden inverso para mantener índices
                            for i in sorted(registros_a_eliminar, reverse=True):
                                data["registros"].pop(i)
                            
                            guardar_datos_ciudad(ciudad_sel, data)
                            st.success(f"✓ {len(indices)} registros fusionados en uno")
                            st.rerun()
    else:
        st.success("✓ No hay registros con el mismo dominio")
    
    st.divider()
    
    # Por teléfono
    st.markdown("### 📞 Mismo Teléfono")
    
    if grupos["por_telefono"]:
        for tel, indices in list(grupos["por_telefono"].items())[:20]:
            with st.expander(f"**{tel}** ({len(indices)} registros)"):
                for idx in indices:
                    r = registros[idx]
                    st.write(f"• {r.get('nombre', 'Sin nombre')[:50]} | {r.get('_ciudad')}")
                    if ciudad_sel != "Todas":
                        st.caption("💡 Nota: Usa la fusión por dominio web para mejores resultados")
    else:
        st.success("✓ No hay registros con el mismo teléfono")


# === TAB 4: LIMPIAR NOMBRES ===
with tab4:
    st.subheader("Limpiar y Clasificar Nombres")
    st.caption("Analiza nombres para separar nombre real de descripción y detectar tipo")
    
    if st.button("🔍 Analizar nombres", type="primary"):
        resultados_limpieza = []
        
        for r in registros[:200]:
            nombre_original = r.get("nombre", "")
            nombre_limpio, descripcion, tipo_detectado = limpiar_nombre(nombre_original)
            
            if nombre_limpio != nombre_original or tipo_detectado != r.get("tipo", "despacho"):
                resultados_limpieza.append({
                    "original": nombre_original[:40],
                    "limpio": nombre_limpio[:40],
                    "descripcion": descripcion[:30] if descripcion else "",
                    "tipo_actual": r.get("tipo", "despacho"),
                    "tipo_sugerido": tipo_detectado,
                    "ciudad": r.get("_ciudad", ""),
                    "_idx": r.get("_idx_original", 0),
                    "_registro": r
                })
        
        st.session_state.resultados_limpieza = resultados_limpieza
    
    # Mostrar resultados
    if "resultados_limpieza" in st.session_state and st.session_state.resultados_limpieza:
        st.write(f"**{len(st.session_state.resultados_limpieza)}** nombres a revisar:")
        
        # Filtro por tipo sugerido
        tipos_sugeridos = list(set(r["tipo_sugerido"] for r in st.session_state.resultados_limpieza))
        filtro_tipo_limpieza = st.multiselect("Filtrar por tipo sugerido", tipos_sugeridos, default=tipos_sugeridos)
        
        resultados_mostrar = [r for r in st.session_state.resultados_limpieza if r["tipo_sugerido"] in filtro_tipo_limpieza]
        
        # Selección para aplicar
        if "seleccion_limpieza" not in st.session_state:
            st.session_state.seleccion_limpieza = set()
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Seleccionar todos", key="sel_all_clean"):
                st.session_state.seleccion_limpieza = set(r["_idx"] for r in resultados_mostrar)
                st.rerun()
        with col2:
            if st.button("❌ Deseleccionar", key="desel_clean"):
                st.session_state.seleccion_limpieza = set()
                st.rerun()
        
        st.divider()
        
        for r in resultados_mostrar[:50]:
            col_check, col_orig, col_nuevo, col_tipo = st.columns([0.5, 2, 2, 1.5])
            
            with col_check:
                checked = st.checkbox(
                    "s",
                    value=r["_idx"] in st.session_state.seleccion_limpieza,
                    key=f"clean_{r['_idx']}",
                    label_visibility="collapsed"
                )
                if checked:
                    st.session_state.seleccion_limpieza.add(r["_idx"])
                else:
                    st.session_state.seleccion_limpieza.discard(r["_idx"])
            
            with col_orig:
                st.write(f"**Original:** {r['original']}")
                if r['descripcion']:
                    st.caption(f"Desc: {r['descripcion']}")
            
            with col_nuevo:
                st.write(f"**Limpio:** {r['limpio']}")
            
            with col_tipo:
                cambio_tipo = "→" if r['tipo_actual'] != r['tipo_sugerido'] else "="
                st.write(f"{r['tipo_actual']} {cambio_tipo} **{r['tipo_sugerido']}**")
        
        st.divider()
        
        # Aplicar cambios
        if st.session_state.seleccion_limpieza:
            st.write(f"**{len(st.session_state.seleccion_limpieza)}** seleccionados para limpiar")
            
            if st.button("💾 Aplicar limpieza", type="primary"):
                cambios_por_ciudad = {}
                
                for r in st.session_state.resultados_limpieza:
                    if r["_idx"] not in st.session_state.seleccion_limpieza:
                        continue
                    
                    ciudad = r["ciudad"]
                    if ciudad not in cambios_por_ciudad:
                        cambios_por_ciudad[ciudad] = cargar_datos_ciudad(ciudad)
                    
                    # Buscar y actualizar
                    registro_orig = r["_registro"]
                    nombre_limpio, descripcion, tipo_detectado = limpiar_nombre(registro_orig.get("nombre", ""))
                    
                    for i, reg in enumerate(cambios_por_ciudad[ciudad]["registros"]):
                        if reg.get("nombre") == registro_orig.get("nombre") and reg.get("web") == registro_orig.get("web"):
                            cambios_por_ciudad[ciudad]["registros"][i]["nombre"] = nombre_limpio
                            if descripcion:
                                cambios_por_ciudad[ciudad]["registros"][i]["descripcion"] = descripcion
                            cambios_por_ciudad[ciudad]["registros"][i]["tipo"] = tipo_detectado
                            cambios_por_ciudad[ciudad]["registros"][i]["fecha_actualizacion"] = datetime.now().isoformat()
                            break
                
                # Guardar
                for ciudad, data in cambios_por_ciudad.items():
                    guardar_datos_ciudad(ciudad, data)
                
                st.success(f"✓ {len(st.session_state.seleccion_limpieza)} registros limpiados")
                st.session_state.seleccion_limpieza = set()
                st.session_state.resultados_limpieza = []
                st.rerun()
    
    elif "resultados_limpieza" in st.session_state:
        st.success("✓ Todos los nombres están correctos")


# === FOOTER ===
st.divider()
st.caption(f"Última actualización: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(registros)} registros totales")
