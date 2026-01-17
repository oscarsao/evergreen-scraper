"""
Página de seguimiento de costos de APIs.
"""
import streamlit as st
import json
from pathlib import Path
from datetime import date

st.set_page_config(page_title="Costos APIs", page_icon="💰", layout="wide")

st.title("💰 Costos y Uso de APIs")
st.caption("Seguimiento de uso y gastos estimados")


# Costos de referencia
COSTOS_REF = {
    "firecrawl": {"limite": 500, "unidad": "créditos/mes", "costo": "$0.01/crédito"},
    "google_search": {"limite": 100, "unidad": "req/día", "costo": "$0.005/req"},
    "google_places": {"limite": 200, "unidad": "USD/mes", "costo": "~$0.017/req"},
    "tavily": {"limite": 1000, "unidad": "req/mes", "costo": "$0.001/req"},
    "openai": {"limite": "∞", "unidad": "pago por uso", "costo": "~$0.01/query"},
}


def cargar_uso():
    """Carga datos de uso de APIs."""
    path = Path("data/api_usage.json")
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"dia_actual": {}, "mes_actual": {}, "totales": {}}


# Cargar datos
uso = cargar_uso()
hoy = date.today().isoformat()
mes = date.today().strftime("%Y-%m")

uso_hoy = uso.get("dia_actual", {}).get(hoy, {})
uso_mes = {}
for fecha, apis in uso.get("dia_actual", {}).items():
    if fecha.startswith(mes):
        for api, datos in apis.items():
            if api not in uso_mes:
                uso_mes[api] = {"requests": 0, "costo": 0}
            uso_mes[api]["requests"] += datos.get("requests", 0)
            uso_mes[api]["costo"] += datos.get("costo", 0)

totales = uso.get("totales", {})

# Calcular totales
costo_hoy = sum(api.get("costo", 0) for api in uso_hoy.values())
costo_mes = sum(api.get("costo", 0) for api in uso_mes.values())
costo_total = sum(api.get("costo", 0) for api in totales.values())

requests_hoy = sum(api.get("requests", 0) for api in uso_hoy.values())
requests_mes = sum(api.get("requests", 0) for api in uso_mes.values())
requests_total = sum(api.get("requests", 0) for api in totales.values())

# Métricas principales
st.subheader("📊 Resumen de Gastos")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Costo Hoy",
        f"${costo_hoy:.4f}",
        f"{requests_hoy} requests"
    )

with col2:
    st.metric(
        "Costo Este Mes",
        f"${costo_mes:.4f}",
        f"{requests_mes} requests"
    )

with col3:
    st.metric(
        "Costo Total",
        f"${costo_total:.4f}",
        f"{requests_total} requests"
    )

with col4:
    # Estimación mensual basada en uso actual
    dias_mes = 30
    dia_actual = date.today().day
    if dia_actual > 0 and costo_mes > 0:
        estimacion = (costo_mes / dia_actual) * dias_mes
    else:
        estimacion = 0
    st.metric(
        "Estimación Mes",
        f"${estimacion:.2f}",
        "proyectado"
    )

st.divider()

# Uso por API
st.subheader("📈 Uso por API")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Hoy")
    if uso_hoy:
        for api, datos in uso_hoy.items():
            with st.container(border=True):
                st.markdown(f"**{api.upper()}**")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"Requests: {datos.get('requests', 0)}")
                with col_b:
                    st.write(f"Costo: ${datos.get('costo', 0):.4f}")
    else:
        st.info("Sin uso hoy")

with col2:
    st.markdown("#### Este Mes")
    if uso_mes:
        for api, datos in uso_mes.items():
            with st.container(border=True):
                st.markdown(f"**{api.upper()}**")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"Requests: {datos.get('requests', 0)}")
                with col_b:
                    st.write(f"Costo: ${datos.get('costo', 0):.4f}")
    else:
        st.info("Sin uso este mes")

st.divider()

# Límites de planes gratuitos
st.subheader("🎁 Límites de Planes Gratuitos")

for api, info in COSTOS_REF.items():
    usado = uso_mes.get(api, {}).get("requests", 0)
    limite = info["limite"]
    
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        
        with col1:
            st.markdown(f"**{api.upper()}**")
        
        with col2:
            st.write(f"Usado: {usado}")
        
        with col3:
            st.write(f"Límite: {limite} {info['unidad']}")
        
        with col4:
            if isinstance(limite, int) and limite > 0:
                porcentaje = min(100, (usado / limite) * 100)
                st.progress(porcentaje / 100, text=f"{porcentaje:.0f}%")
            else:
                st.write(info["costo"])

st.divider()

# Tabla de precios de referencia
st.subheader("💵 Precios de Referencia")

st.markdown("""
| API | Plan Gratis | Costo Extra | Notas |
|-----|-------------|-------------|-------|
| **Firecrawl** | 500 créditos/mes | $0.01/crédito | Scraping + Extracción |
| **Google Search** | 100/día | $5/1000 | Custom Search API |
| **Google Places** | $200/mes crédito | ~$0.017/req | Negocios locales |
| **Tavily** | 1,000/mes | $0.001/req | Búsqueda optimizada IA |
| **OpenAI** | - | ~$0.01/query | gpt-4o-mini |
""")

st.divider()

# Consejos de optimización
with st.expander("💡 Consejos para Reducir Costos"):
    st.markdown("""
    1. **Usa Tavily primero** - Es la más barata y tiene buen límite gratis
    2. **Limita búsquedas por sesión** - 10-15 resultados suele ser suficiente
    3. **Evita scraping profundo** si no es necesario
    4. **Google Search** - 100/día gratis, úsalos sabiamente
    5. **OpenAI** - Solo para estructurar datos complejos
    6. **Consolida antes de buscar** - Evita duplicar búsquedas
    """)

# Botón para resetear (solo desarrollo)
with st.expander("⚙️ Administración"):
    if st.button("🗑️ Resetear estadísticas", type="secondary"):
        path = Path("data/api_usage.json")
        if path.exists():
            path.unlink()
        st.success("Estadísticas reseteadas")
        st.rerun()
