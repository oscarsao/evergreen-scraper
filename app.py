"""
Dashboard Unificado - Sistema de Abogados de Extranjería
=========================================================
Vista completa en una sola pantalla con métricas, gráficos y acciones rápidas.
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, date

# Configuración de página
st.set_page_config(
    page_title="Dashboard - Abogados Extranjería",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para dashboard compacto
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 1rem;
        color: white;
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .status-ok { color: #00c853; }
    .status-warn { color: #ffc107; }
    .status-error { color: #ff5252; }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
    }
    .stProgress > div > div > div > div {
        background-color: #667eea;
    }
</style>
""", unsafe_allow_html=True)


def cargar_todos_los_datos():
    """
    Carga datos optimizados si existen, sino carga datos por ciudad.
    Soporta múltiples ciudades por registro.
    """
    data_dir = Path("data")
    todos_registros = []
    ciudades_stats = {}
    
    if not data_dir.exists():
        return [], []
    
    # Prioridad 1: Datos optimizados
    optimizado_path = data_dir / "registros_optimizados.json"
    if optimizado_path.exists():
        try:
            with open(optimizado_path, "r", encoding="utf-8") as f:
                data_opt = json.load(f)
            
            registros = data_opt.get("registros", [])
            
            # Procesar registros optimizados (pueden tener múltiples ciudades)
            for r in registros:
                # Obtener ciudades: array o campo único
                ciudades = r.get("ciudades", [])
                if not ciudades and r.get("ciudad"):
                    ciudades = [r["ciudad"]]
                if not ciudades:
                    ciudades = ["Sin ciudad"]
                
                # Para compatibilidad, usar primera ciudad
                r["_ciudad"] = ciudades[0] if ciudades else "Sin ciudad"
                r["_ciudades_lista"] = ciudades  # Lista completa
                
                # Contar para estadísticas
                for ciudad in ciudades:
                    if ciudad not in ciudades_stats:
                        ciudades_stats[ciudad] = {
                            "ciudad": ciudad,
                            "total": 0,
                            "con_tel": 0,
                            "con_email": 0,
                            "con_web": 0,
                            "con_dir": 0
                        }
                    ciudades_stats[ciudad]["total"] += 1
                    if r.get("telefono"):
                        ciudades_stats[ciudad]["con_tel"] += 1
                    if r.get("email"):
                        ciudades_stats[ciudad]["con_email"] += 1
                    if r.get("web"):
                        ciudades_stats[ciudad]["con_web"] += 1
                    if r.get("direccion"):
                        ciudades_stats[ciudad]["con_dir"] += 1
                
                todos_registros.append(r)
            
            # Convertir a lista para compatibilidad
            ciudades_stats = list(ciudades_stats.values())
            
            print(f"[Dashboard] Cargados {len(todos_registros)} registros optimizados")
            return todos_registros, ciudades_stats
            
        except Exception as e:
            print(f"[Dashboard] Error cargando datos optimizados: {e}")
            # Continuar con carga tradicional
    
    # Fallback: Cargar por ciudad (método tradicional)
    for archivo in sorted(data_dir.glob("*.json")):
        if "config" in archivo.name or "api_usage" in archivo.name or "optimizados" in archivo.name:
            continue
        
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            registros = data.get("registros", [])
            ciudad = archivo.stem.title()
            
            # Añadir ciudad a cada registro
            for r in registros:
                r["_ciudad"] = ciudad
                if "ciudades" not in r:
                    r["_ciudades_lista"] = [ciudad]
                todos_registros.append(r)
            
            # Stats por ciudad
            ciudades_stats.append({
                "ciudad": ciudad,
                "total": len(registros),
                "con_tel": sum(1 for r in registros if r.get("telefono")),
                "con_email": sum(1 for r in registros if r.get("email")),
                "con_web": sum(1 for r in registros if r.get("web")),
                "con_dir": sum(1 for r in registros if r.get("direccion")),
            })
        except:
            continue
    
    return todos_registros, ciudades_stats


def cargar_uso_apis():
    """Carga estadísticas de uso de APIs."""
    api_path = Path("data/api_usage.json")
    if not api_path.exists():
        return {}
    
    try:
        with open(api_path, "r") as f:
            return json.load(f)
    except:
        return {}


def verificar_apis():
    """Verifica estado de APIs."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    return {
        "Tavily": {"key": bool(os.getenv("TAVILY_API_KEY")), "limite": 1000},
        "Firecrawl": {"key": bool(os.getenv("FIRECRAWL_API_KEY")), "limite": 500},
        "Google": {"key": bool(os.getenv("GOOGLE_API_KEY")), "limite": 100},
        "OpenAI": {"key": bool(os.getenv("OPENAI_API_KEY")), "limite": None},
    }


def calcular_completitud(registro):
    """Calcula nivel de completitud de un registro."""
    campos = ["telefono", "email", "web", "direccion"]
    completos = sum(1 for c in campos if registro.get(c))
    return completos / len(campos) * 100


# === CARGAR DATOS ===
registros, ciudades_stats = cargar_todos_los_datos()
api_usage = cargar_uso_apis()
apis = verificar_apis()

# === HEADER ===
col_title, col_refresh = st.columns([5, 1])
with col_title:
    st.title("⚖️ Dashboard - Abogados de Extranjería")
with col_refresh:
    if st.button("🔄", help="Actualizar datos"):
        st.rerun()

# === MÉTRICAS PRINCIPALES ===
st.markdown("### 📊 Resumen General")

total = len(registros)
con_tel = sum(1 for r in registros if r.get("telefono"))
con_email = sum(1 for r in registros if r.get("email"))
con_web = sum(1 for r in registros if r.get("web"))
con_dir = sum(1 for r in registros if r.get("direccion"))
completos = sum(1 for r in registros if r.get("telefono") and r.get("email") and r.get("web"))

col1, col2, col3, col4, col5, col6 = st.columns(6)

with col1:
    st.metric("Total Registros", f"{total:,}")
with col2:
    pct_tel = con_tel/max(total,1)*100
    st.metric("Con Teléfono", f"{con_tel:,}", f"{pct_tel:.0f}%")
with col3:
    pct_email = con_email/max(total,1)*100
    st.metric("Con Email", f"{con_email:,}", f"{pct_email:.0f}%")
with col4:
    pct_web = con_web/max(total,1)*100
    st.metric("Con Web", f"{con_web:,}", f"{pct_web:.0f}%")
with col5:
    pct_dir = con_dir/max(total,1)*100
    st.metric("Con Dirección", f"{con_dir:,}", f"{pct_dir:.0f}%")
with col6:
    pct_comp = completos/max(total,1)*100
    st.metric("Completos", f"{completos:,}", f"{pct_comp:.0f}%")

# === FILA PRINCIPAL: Ciudades + Calidad + APIs ===
st.markdown("---")
col_ciudades, col_calidad, col_apis = st.columns([2, 2, 1.5])

# --- Columna Ciudades ---
with col_ciudades:
    st.markdown("### 🏙️ Por Ciudad")
    
    # Verificar si estamos usando datos optimizados
    optimizado_path = Path("data/registros_optimizados.json")
    usando_optimizados = optimizado_path.exists()
    
    if usando_optimizados:
        st.caption("✨ Datos optimizados - Un registro puede aparecer en múltiples ciudades")
    
    if ciudades_stats:
        df_ciudades = pd.DataFrame(ciudades_stats)
        df_ciudades = df_ciudades.sort_values("total", ascending=False)
        
        # Gráfico de barras horizontal
        chart_data = df_ciudades.set_index("ciudad")[["total", "con_tel", "con_email"]]
        chart_data.columns = ["Total", "Teléfono", "Email"]
        st.bar_chart(chart_data, horizontal=True, height=300)
        
        # Tabla compacta
        df_display = df_ciudades[["ciudad", "total", "con_tel", "con_email"]].copy()
        df_display.columns = ["Ciudad", "Total", "Tel", "Email"]
        df_display["% Tel"] = (df_display["Tel"] / df_display["Total"] * 100).round(0).astype(int).astype(str) + "%"
        st.dataframe(df_display, use_container_width=True, hide_index=True, height=200)
    else:
        st.info("No hay datos cargados")

# --- Columna Calidad de Datos ---
with col_calidad:
    st.markdown("### 📈 Calidad de Datos")
    
    if registros:
        # Calcular niveles de completitud
        niveles = {"Completo (4/4)": 0, "Alto (3/4)": 0, "Medio (2/4)": 0, "Bajo (1/4)": 0, "Mínimo (0/4)": 0}
        
        for r in registros:
            campos = sum(1 for c in ["telefono", "email", "web", "direccion"] if r.get(c))
            if campos == 4:
                niveles["Completo (4/4)"] += 1
            elif campos == 3:
                niveles["Alto (3/4)"] += 1
            elif campos == 2:
                niveles["Medio (2/4)"] += 1
            elif campos == 1:
                niveles["Bajo (1/4)"] += 1
            else:
                niveles["Mínimo (0/4)"] += 1
        
        # Mostrar como barras de progreso
        for nivel, count in niveles.items():
            pct = count / max(total, 1) * 100
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.progress(pct / 100, text=f"{nivel}")
            with col_b:
                st.write(f"{count} ({pct:.0f}%)")
        
        st.markdown("---")
        
        # Datos faltantes
        st.markdown("**📋 Datos Faltantes:**")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.write(f"Sin teléfono: **{total - con_tel}**")
            st.write(f"Sin email: **{total - con_email}**")
        with col_f2:
            st.write(f"Sin dirección: **{total - con_dir}**")
            st.write(f"Sin web: **{total - con_web}**")
    else:
        st.info("No hay datos para analizar")

# --- Columna APIs ---
with col_apis:
    st.markdown("### 🔌 Estado APIs")
    
    for api_name, api_info in apis.items():
        if api_info["key"]:
            st.success(f"✓ {api_name}")
        else:
            st.error(f"✗ {api_name}")
    
    st.markdown("---")
    st.markdown("**💰 Uso Este Mes:**")
    
    # Calcular uso del mes actual
    mes_actual = date.today().strftime("%Y-%m")
    uso_mes = {}
    
    for fecha, apis_data in api_usage.get("dia_actual", {}).items():
        if fecha.startswith(mes_actual):
            for api, datos in apis_data.items():
                if api not in uso_mes:
                    uso_mes[api] = {"requests": 0, "costo": 0}
                uso_mes[api]["requests"] += datos.get("requests", 0)
                uso_mes[api]["costo"] += datos.get("costo", 0)
    
    if uso_mes:
        total_requests = sum(d["requests"] for d in uso_mes.values())
        total_costo = sum(d["costo"] for d in uso_mes.values())
        st.metric("Requests", total_requests)
        st.metric("Costo Est.", f"${total_costo:.2f}")
    else:
        st.write("Sin uso este mes")

# === FILA ACCIONES: Búsqueda Rápida + Acciones ===
st.markdown("---")
col_busqueda, col_acciones = st.columns([3, 2])

# --- Búsqueda Rápida ---
with col_busqueda:
    st.markdown("### 🔍 Búsqueda Rápida")
    
    col_ciudad, col_btn = st.columns([3, 1])
    
    with col_ciudad:
        ciudad_buscar = st.selectbox(
            "Ciudad",
            ["Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga", 
             "Zaragoza", "Murcia", "Palma", "Alicante", "Bilbao"],
            label_visibility="collapsed"
        )
    
    with col_btn:
        buscar_clicked = st.button("🚀 Buscar", type="primary", use_container_width=True)
    
    if buscar_clicked:
        with st.spinner(f"Buscando en {ciudad_buscar}..."):
            try:
                from core.orquestador import Orquestador, BusquedaConfig
                
                config = BusquedaConfig(
                    ciudad=ciudad_buscar,
                    apis_habilitadas=["tavily"],
                    max_resultados_por_api=20,
                    usar_places=False,
                    scraping_profundo=False
                )
                
                orq = Orquestador()
                resultado = orq.ejecutar_busqueda(config)
                
                if resultado.consolidacion:
                    st.success(f"✓ {resultado.consolidacion.total_nuevos} nuevos, {len(resultado.consolidacion.actualizados)} actualizados")
                else:
                    st.info(f"Encontrados: {resultado.total_encontrados}")
                    
            except Exception as e:
                st.error(f"Error: {e}")

# --- Acciones Rápidas ---
with col_acciones:
    st.markdown("### ⚡ Acciones Rápidas")
    
    col_a1, col_a2 = st.columns(2)
    
    with col_a1:
        if st.button("📥 Enriquecer Datos", use_container_width=True):
            st.switch_page("pages/4_Enriquecer.py")
        
        if st.button("🔧 Depurar", use_container_width=True):
            st.switch_page("pages/4_Depurar.py")
    
    with col_a2:
        if st.button("📊 Explorar Datos", use_container_width=True):
            st.switch_page("pages/3_Datos.py")
        
        if st.button("📤 Exportar", use_container_width=True):
            st.switch_page("pages/5_Exportar.py")

# === FILA INFERIOR: Registros Incompletos + Últimos Añadidos ===
st.markdown("---")
col_incompletos, col_ultimos = st.columns(2)

# --- Registros que necesitan atención ---
with col_incompletos:
    st.markdown("### 🔧 Necesitan Enriquecimiento")
    
    # Filtrar registros con web pero sin tel/email
    necesitan = [
        r for r in registros 
        if r.get("web") and (not r.get("telefono") or not r.get("email"))
    ][:10]
    
    if necesitan:
        for r in necesitan:
            with st.container(border=True):
                col_info, col_btn = st.columns([4, 1])
                with col_info:
                    st.write(f"**{r.get('nombre', 'Sin nombre')[:40]}**")
                    falta = []
                    if not r.get("telefono"):
                        falta.append("Tel")
                    if not r.get("email"):
                        falta.append("Email")
                    if not r.get("direccion"):
                        falta.append("Dir")
                    
                    # Mostrar ciudades (múltiples si existen)
                    ciudades_display = r.get("_ciudades_lista", [r.get("_ciudad", "")] if r.get("_ciudad") else [])
                    ciudades_str = ", ".join(ciudades_display[:2])
                    if len(ciudades_display) > 2:
                        ciudades_str += f" +{len(ciudades_display)-2}"
                    st.caption(f"Falta: {', '.join(falta)} | 🏙️ {ciudades_str}")
                with col_btn:
                    st.button("📥", key=f"enrich_{r.get('nombre', '')[:20]}", help="Enriquecer")
        
        st.caption(f"Mostrando 10 de {len([r for r in registros if r.get('web') and (not r.get('telefono') or not r.get('email'))])} registros")
    else:
        st.success("Todos los registros con web tienen datos completos")

# --- Últimos añadidos ---
with col_ultimos:
    st.markdown("### 🕐 Últimos Añadidos")
    
    # Ordenar por fecha de actualización
    registros_con_fecha = [r for r in registros if r.get("fecha_actualizacion")]
    registros_ordenados = sorted(
        registros_con_fecha, 
        key=lambda x: x.get("fecha_actualizacion", ""), 
        reverse=True
    )[:10]
    
    if registros_ordenados:
        for r in registros_ordenados:
            with st.container(border=True):
                col_info, col_fecha = st.columns([3, 1])
                with col_info:
                    st.write(f"**{r.get('nombre', 'Sin nombre')[:35]}**")
                    # Mostrar ciudades (múltiples si existen)
                    ciudades_display = r.get("_ciudades_lista", [r.get("_ciudad", "")] if r.get("_ciudad") else [])
                    ciudades_str = ", ".join(ciudades_display[:2])
                    if len(ciudades_display) > 2:
                        ciudades_str += f" +{len(ciudades_display)-2}"
                    st.caption(f"🏙️ {ciudades_str}")
                with col_fecha:
                    fecha = r.get("fecha_actualizacion", "")[:10]
                    st.caption(fecha)
    else:
        st.info("No hay registros con fecha")

# === FOOTER ===
st.markdown("---")
st.caption(f"Dashboard actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Total: {total} registros en {len(ciudades_stats)} ciudades")
