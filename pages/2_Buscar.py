"""
Página de búsqueda con múltiples APIs.
"""
import streamlit as st
import os
import json
from pathlib import Path
from datetime import datetime

st.set_page_config(page_title="Buscar", page_icon="🔍", layout="wide")

st.title("🔍 Nueva Búsqueda")
st.caption("Ejecuta búsquedas con múltiples APIs y agentes")


def verificar_apis():
    """Verifica APIs disponibles."""
    from dotenv import load_dotenv
    load_dotenv()
    
    return {
        "firecrawl": bool(os.getenv("FIRECRAWL_API_KEY")),
        "google_search": bool(os.getenv("GOOGLE_API_KEY") and os.getenv("GOOGLE_CSE_ID")),
        "google_places": bool(os.getenv("GOOGLE_API_KEY")),
        "tavily": bool(os.getenv("TAVILY_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
    }


# Estado de sesión
if "busqueda_resultados" not in st.session_state:
    st.session_state.busqueda_resultados = []
if "busqueda_ejecutando" not in st.session_state:
    st.session_state.busqueda_ejecutando = False

# Sidebar - Configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Ciudad
    ciudad = st.selectbox(
        "Ciudad",
        ["Madrid", "Barcelona", "Valencia", "Sevilla", "Málaga", "Bilbao"],
        index=0
    )
    
    # APIs a usar
    st.subheader("APIs a usar")
    apis_estado = verificar_apis()
    
    apis_seleccionadas = []
    for api, disponible in apis_estado.items():
        if disponible:
            if st.checkbox(api.title(), value=True, key=f"api_{api}"):
                apis_seleccionadas.append(api)
        else:
            st.checkbox(api.title(), value=False, disabled=True, key=f"api_{api}_dis")
            st.caption("No configurada")
    
    st.divider()
    
    # Opciones avanzadas
    with st.expander("Opciones Avanzadas"):
        max_resultados = st.slider("Máx. resultados por API", 5, 50, 20)
        usar_places = st.checkbox("Usar Google Places", value=True)
        scraping_profundo = st.checkbox("Scraping profundo", value=True)

# Contenido principal
tab1, tab2, tab3 = st.tabs(["🎯 Búsqueda Rápida", "🔧 Búsqueda Manual", "📜 Historial"])

with tab1:
    st.subheader("Búsqueda Automática")
    st.write(f"Buscar abogados de extranjería en **{ciudad}** usando APIs seleccionadas.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        zonas = st.multiselect(
            "Zonas específicas (opcional)",
            ["Centro", "Norte", "Sur", "Este", "Oeste", "Área metropolitana"],
            default=[]
        )
    
    with col2:
        especialidad = st.selectbox(
            "Especialidad",
            ["Todas", "Arraigo", "Asilo", "Nacionalidad", "Reagrupación", "Visados"]
        )
    
    if st.button("🚀 Ejecutar Búsqueda", type="primary", use_container_width=True):
        if not apis_seleccionadas:
            st.error("Selecciona al menos una API")
        else:
            st.session_state.busqueda_ejecutando = True
            
            with st.spinner(f"Buscando en {ciudad}..."):
                try:
                    # Importar orquestador
                    from core.orquestador import Orquestador, BusquedaConfig
                    
                    # Crear configuración
                    config = BusquedaConfig(
                        ciudad=ciudad,
                        zonas=zonas if zonas else [],
                        apis_habilitadas=apis_seleccionadas,
                        max_resultados_por_api=max_resultados,
                        usar_places=usar_places,
                        scraping_profundo=scraping_profundo
                    )
                    
                    # Ejecutar
                    orquestador = Orquestador()
                    resultado = orquestador.ejecutar_busqueda(config)
                    
                    # Mostrar resultados
                    st.success(f"Búsqueda completada en {resultado.duracion_segundos:.1f}s")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Encontrados", resultado.total_encontrados)
                    with col2:
                        if resultado.consolidacion:
                            st.metric("Nuevos", resultado.consolidacion.total_nuevos)
                    with col3:
                        if resultado.consolidacion:
                            st.metric("Duplicados", len(resultado.consolidacion.duplicados_ignorados))
                    
                    # Detalle por API
                    if resultado.resultados_por_api:
                        st.subheader("Por API")
                        for api, count in resultado.resultados_por_api.items():
                            st.write(f"- {api}: {count} resultados")
                    
                    # Errores
                    if resultado.errores:
                        with st.expander("⚠️ Errores"):
                            for error in resultado.errores:
                                st.warning(error)
                    
                    # Guardar en historial
                    historial_path = Path("data/historial_busquedas.json")
                    historial_path.parent.mkdir(exist_ok=True)
                    
                    # Cargar historial existente
                    if historial_path.exists():
                        try:
                            with open(historial_path, "r", encoding="utf-8") as f:
                                historial = json.load(f)
                        except:
                            historial = []
                    else:
                        historial = []
                    
                    # Agregar nueva búsqueda
                    entrada_historial = {
                        "fecha": resultado.fecha,
                        "ciudad": ciudad,
                        "zonas": zonas,
                        "apis_usadas": apis_seleccionadas,
                        "total_encontrados": resultado.total_encontrados,
                        "nuevos": resultado.consolidacion.total_nuevos if resultado.consolidacion else 0,
                        "actualizados": len(resultado.consolidacion.actualizados) if resultado.consolidacion else 0,
                        "duplicados": len(resultado.consolidacion.duplicados_ignorados) if resultado.consolidacion else 0,
                        "filtrados": len(resultado.consolidacion.filtrados) if resultado.consolidacion else 0,
                        "duracion_segundos": round(resultado.duracion_segundos, 2),
                        "resultados_por_api": resultado.resultados_por_api,
                        "max_resultados_por_api": max_resultados,
                        "usar_places": usar_places,
                        "scraping_profundo": scraping_profundo
                    }
                    
                    historial.append(entrada_historial)
                    
                    # Mantener solo las últimas 100 búsquedas
                    historial = historial[-100:]
                    
                    # Guardar
                    with open(historial_path, "w", encoding="utf-8") as f:
                        json.dump(historial, f, ensure_ascii=False, indent=2)
                                
                except ImportError as e:
                    st.error(f"Error importando módulos: {e}")
                    st.info("Asegúrate de tener todas las dependencias instaladas.")
                except Exception as e:
                    st.error(f"Error en búsqueda: {e}")
                finally:
                    st.session_state.busqueda_ejecutando = False

with tab2:
    st.subheader("Búsqueda Manual")
    st.write("Ejecuta una búsqueda personalizada con un query específico.")
    
    query_manual = st.text_area(
        "Query de búsqueda",
        value=f'"abogado extranjería" {ciudad} teléfono email contacto',
        height=100
    )
    
    api_manual = st.selectbox(
        "API a usar",
        [api for api, disp in apis_estado.items() if disp],
        key="api_manual"
    )
    
    if st.button("🔍 Buscar", key="btn_manual"):
        with st.spinner("Ejecutando búsqueda..."):
            try:
                # Importar adapter
                if api_manual == "tavily":
                    from adapters import TavilyAdapter
                    adapter = TavilyAdapter()
                elif api_manual == "google_search":
                    from adapters import GoogleSearchAdapter
                    adapter = GoogleSearchAdapter()
                elif api_manual == "firecrawl":
                    from adapters import FirecrawlAdapter
                    adapter = FirecrawlAdapter()
                else:
                    st.error("API no soportada para búsqueda manual")
                    st.stop()
                
                if adapter.esta_disponible():
                    resultados = adapter.search(query_manual)
                    
                    st.success(f"Encontrados: {len(resultados)} resultados")
                    
                    for r in resultados[:10]:
                        with st.expander(r.nombre):
                            st.write(f"**Tipo:** {r.tipo}")
                            if r.telefono:
                                st.write(f"**Teléfono:** {', '.join(r.telefono)}")
                            if r.email:
                                st.write(f"**Email:** {r.email}")
                            if r.web:
                                st.write(f"**Web:** {r.web}")
                            if r.direccion:
                                st.write(f"**Dirección:** {r.direccion}")
                else:
                    st.error("API no disponible (falta configuración)")
                    
            except Exception as e:
                st.error(f"Error: {e}")

with tab3:
    st.subheader("Historial de Búsquedas")
    st.caption("Registro de todas las búsquedas ejecutadas")
    
    historial_path = Path("data/historial_busquedas.json")
    if historial_path.exists():
        try:
            with open(historial_path, "r", encoding="utf-8") as f:
                historial = json.load(f)
            
            if historial:
                # Mostrar últimas 20 búsquedas
                historial_reciente = historial[-20:]
                historial_reciente.reverse()  # Más recientes primero
                
                st.write(f"**Total de búsquedas:** {len(historial)} (mostrando últimas {len(historial_reciente)})")
                st.divider()
                
                for h in historial_reciente:
                    fecha_str = h.get("fecha", "")[:19] if h.get("fecha") else "Sin fecha"
                    
                    with st.expander(f"🔍 {h.get('ciudad', 'Sin ciudad')} - {fecha_str} ({h.get('duracion_segundos', 0)}s)"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**Resultados:**")
                            st.write(f"- Total encontrados: **{h.get('total_encontrados', 0)}**")
                            st.write(f"- Nuevos: **{h.get('nuevos', 0)}**")
                            st.write(f"- Actualizados: **{h.get('actualizados', 0)}**")
                            st.write(f"- Duplicados: **{h.get('duplicados', 0)}**")
                            st.write(f"- Filtrados: **{h.get('filtrados', 0)}**")
                        
                        with col2:
                            st.markdown("**Configuración:**")
                            st.write(f"- APIs: {', '.join(h.get('apis_usadas', []))}")
                            if h.get('zonas'):
                                st.write(f"- Zonas: {', '.join(h.get('zonas', []))}")
                            st.write(f"- Max resultados/API: {h.get('max_resultados_por_api', 0)}")
                            st.write(f"- Places: {'✓' if h.get('usar_places') else '✗'}")
                            st.write(f"- Scraping: {'✓' if h.get('scraping_profundo') else '✗'}")
                        
                        # Resultados por API
                        if h.get('resultados_por_api'):
                            st.markdown("**Por API:**")
                            for api, count in h.get('resultados_por_api', {}).items():
                                st.caption(f"- {api}: {count} resultados")
            else:
                st.info("No hay búsquedas registradas aún. Ejecuta una búsqueda para comenzar.")
        except Exception as e:
            st.error(f"Error cargando historial: {e}")
    else:
        st.info("No hay búsquedas registradas aún. Ejecuta una búsqueda para comenzar.")
