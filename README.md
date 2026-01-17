# 🔍 Buscador de Abogados de Extranjería

Sistema multi-agente para búsqueda y consolidación de datos de abogados especializados en extranjería en España.

## 🚀 Características

- **Búsqueda Multi-API**: Firecrawl, Google Search, Google Places, Tavily
- **Deduplicación Inteligente**: Hash, teléfono normalizado, similitud fuzzy
- **Dashboard Interactivo**: Visualización y gestión de datos
- **Exportación**: CSV, Excel, PDF, JSON
- **Tracking de Costos**: Monitoreo de uso de APIs

## 📦 Instalación Local

```bash
# Clonar repositorio
git clone https://github.com/TU_USUARIO/scraper-abogados.git
cd scraper-abogados

# Crear entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar APIs
cp .env.example .env
# Editar .env con tus API keys

# Ejecutar
streamlit run app.py
```

## 🔑 APIs Necesarias

| API | Gratis | Obtener Key |
|-----|--------|-------------|
| Tavily | 1000/mes | [tavily.com](https://tavily.com) |
| Firecrawl | 500/mes | [firecrawl.dev](https://firecrawl.dev) |
| Google Search | 100/día | [console.cloud.google.com](https://console.cloud.google.com) |
| OpenAI | Pago | [platform.openai.com](https://platform.openai.com) |

## 🌐 Despliegue en Streamlit Cloud

1. Sube este repo a GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu repositorio
4. En **Settings > Secrets**, añade tus API keys:

```toml
FIRECRAWL_API_KEY = "tu-key"
GOOGLE_API_KEY = "tu-key"
GOOGLE_CSE_ID = "tu-id"
TAVILY_API_KEY = "tu-key"
OPENAI_API_KEY = "tu-key"
```

## 📁 Estructura

```
├── app.py                 # Entrada principal Streamlit
├── pages/                 # Páginas de la aplicación
│   ├── 1_Dashboard.py
│   ├── 2_Buscar.py
│   ├── 3_Datos.py
│   ├── 4_Duplicados.py
│   ├── 5_Exportar.py
│   └── 6_API_Costos.py
├── adapters/              # Conectores de APIs
├── core/                  # Lógica principal
├── prompts/               # Prompts y schemas
├── utils/                 # Utilidades
└── data/                  # Datos JSON
```

## 📊 Uso

1. **Dashboard**: Vista general de estadísticas
2. **Buscar**: Ejecutar búsquedas por ciudad
3. **Datos**: Explorar y editar registros
4. **Duplicados**: Gestionar posibles duplicados
5. **Exportar**: Descargar en varios formatos
6. **API Costos**: Monitorear uso y gastos

## 📄 Licencia

MIT License
