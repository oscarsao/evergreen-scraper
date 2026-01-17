"""
🔍 Sistema Multi-Agente de Búsqueda de Abogados
==============================================
Interfaz Streamlit para gestionar búsquedas, datos y exportaciones.

Ejecutar: streamlit run app.py
"""
import streamlit as st
import json
from pathlib import Path

# Configuración de página
st.set_page_config(
    page_title="Buscador Abogados Extranjería",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


def cargar_estadisticas():
    """Carga estadísticas de todas las ciudades."""
    data_dir = Path("data")
    estadisticas = {
        "total_registros": 0,
        "con_telefono": 0,
        "con_email": 0,
        "con_web": 0,
        "ciudades": []
    }
    
    if not data_dir.exists():
        return estadisticas
    
    for archivo in data_dir.glob("*.json"):
        if "config" in archivo.name:
            continue
        
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            registros = data.get("registros", [])
            n = len(registros)
            
            ciudad_stats = {
                "nombre": archivo.stem.title(),
                "total": n,
                "telefono": sum(1 for r in registros if r.get("telefono")),
                "email": sum(1 for r in registros if r.get("email")),
                "web": sum(1 for r in registros if r.get("web")),
            }
            
            estadisticas["ciudades"].append(ciudad_stats)
            estadisticas["total_registros"] += n
            estadisticas["con_telefono"] += ciudad_stats["telefono"]
            estadisticas["con_email"] += ciudad_stats["email"]
            estadisticas["con_web"] += ciudad_stats["web"]
            
        except:
            continue
    
    return estadisticas


def verificar_apis():
    """Verifica qué APIs están configuradas."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    apis = {
        "Firecrawl": bool(os.getenv("FIRECRAWL_API_KEY")),
        "Google Search": bool(os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID")),
        "Google Places": bool(os.getenv("GOOGLE_API_KEY")),
        "Tavily": bool(os.getenv("TAVILY_API_KEY")),
        "OpenAI": bool(os.getenv("OPENAI_API_KEY")),
    }
    return apis


def main():
    # Header
    st.markdown('<p class="main-header">⚖️ Buscador de Abogados de Extranjería</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Sistema multi-agente con IA para España</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuración")
        
        # Estado de APIs
        st.subheader("APIs Configuradas")
        apis = verificar_apis()
        for api, estado in apis.items():
            if estado:
                st.success(f"OK {api}")
            else:
                st.warning(f"X {api}")
        
        st.divider()
        
        # Navegación rápida
        st.subheader("📍 Accesos Rápidos")
        if st.button("🔍 Nueva Búsqueda", use_container_width=True):
            st.switch_page("pages/2_Buscar.py")
        if st.button("📊 Ver Datos", use_container_width=True):
            st.switch_page("pages/3_Datos.py")
        if st.button("📥 Exportar", use_container_width=True):
            st.switch_page("pages/5_Exportar.py")
    
    # Contenido principal
    stats = cargar_estadisticas()
    
    # Métricas principales
    st.subheader("📊 Resumen General")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Registros",
            value=stats["total_registros"],
            delta=None
        )
    
    with col2:
        st.metric(
            label="Con Teléfono",
            value=stats["con_telefono"],
            delta=f"{stats['con_telefono']/max(stats['total_registros'],1)*100:.0f}%"
        )
    
    with col3:
        st.metric(
            label="Con Email",
            value=stats["con_email"],
            delta=f"{stats['con_email']/max(stats['total_registros'],1)*100:.0f}%"
        )
    
    with col4:
        st.metric(
            label="Con Web",
            value=stats["con_web"],
            delta=f"{stats['con_web']/max(stats['total_registros'],1)*100:.0f}%"
        )
    
    # Costos de APIs
    st.divider()
    st.subheader("💰 Uso de APIs (Este Mes)")
    
    try:
        api_usage_path = Path("data/api_usage.json")
        if api_usage_path.exists():
            with open(api_usage_path, "r") as f:
                api_usage = json.load(f)
            
            from datetime import date
            mes = date.today().strftime("%Y-%m")
            uso_mes = {}
            for fecha, apis in api_usage.get("dia_actual", {}).items():
                if fecha.startswith(mes):
                    for api, datos in apis.items():
                        if api not in uso_mes:
                            uso_mes[api] = {"requests": 0, "costo": 0}
                        uso_mes[api]["requests"] += datos.get("requests", 0)
                        uso_mes[api]["costo"] += datos.get("costo", 0)
            
            if uso_mes:
                costo_total = sum(d["costo"] for d in uso_mes.values())
                requests_total = sum(d["requests"] for d in uso_mes.values())
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Requests", requests_total)
                with col2:
                    st.metric("Costo Estimado", f"${costo_total:.4f}")
                with col3:
                    if st.button("Ver Detalles", use_container_width=True):
                        st.switch_page("pages/6_API_Costos.py")
            else:
                st.info("Sin uso de APIs este mes")
        else:
            st.info("Sin datos de uso de APIs")
    except Exception as e:
        st.warning(f"No se pudo cargar uso de APIs")
    
    st.divider()
    
    # Estadísticas por ciudad
    st.subheader("🏙️ Registros por Ciudad")
    
    if stats["ciudades"]:
        # Preparar datos para gráfico
        ciudades_nombres = [c["nombre"] for c in stats["ciudades"]]
        ciudades_totales = [c["total"] for c in stats["ciudades"]]
        
        # Gráfico de barras
        import pandas as pd
        df_ciudades = pd.DataFrame({
            "Ciudad": ciudades_nombres,
            "Registros": ciudades_totales
        })
        df_ciudades = df_ciudades.sort_values("Registros", ascending=True)
        
        st.bar_chart(df_ciudades.set_index("Ciudad"))
        
        # Tabla detallada
        st.subheader("📋 Detalle por Ciudad")
        
        df_detalle = pd.DataFrame(stats["ciudades"])
        df_detalle.columns = ["Ciudad", "Total", "Con Tel.", "Con Email", "Con Web"]
        df_detalle["% Completo"] = (
            (df_detalle["Con Tel."] > 0).astype(int) +
            (df_detalle["Con Email"] > 0).astype(int) +
            (df_detalle["Con Web"] > 0).astype(int)
        ) / 3 * 100
        df_detalle["% Completo"] = df_detalle["% Completo"].round(0).astype(int).astype(str) + "%"
        
        st.dataframe(
            df_detalle.sort_values("Total", ascending=False),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay datos cargados. Ve a 'Buscar' para iniciar una búsqueda.")
    
    st.divider()
    
    # Acciones rápidas
    st.subheader("🚀 Acciones Rápidas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 🔍 Buscar")
        st.write("Ejecuta búsquedas con múltiples APIs y agentes.")
        if st.button("Ir a Búsqueda", key="btn_buscar"):
            st.switch_page("pages/2_Buscar.py")
    
    with col2:
        st.markdown("### 📊 Explorar Datos")
        st.write("Visualiza, filtra y edita los registros.")
        if st.button("Ver Datos", key="btn_datos"):
            st.switch_page("pages/3_Datos.py")
    
    with col3:
        st.markdown("### 📥 Exportar")
        st.write("Descarga en CSV, PDF, Excel o JSON.")
        if st.button("Exportar", key="btn_exportar"):
            st.switch_page("pages/5_Exportar.py")
    
    # Footer
    st.divider()
    st.caption("Sistema Multi-Agente de Búsqueda | Desarrollado con Streamlit + Python")


if __name__ == "__main__":
    main()
