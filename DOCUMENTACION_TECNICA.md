# 📋 Documentación Técnica y Funcional
## Sistema de Búsqueda y Gestión de Abogados de Extranjería

**Versión:** 1.0  
**Fecha:** 2026-01-17  
**Autor:** Sistema Multi-Agente de Búsqueda

---

## 📑 Índice

1. [Descripción General del Proyecto](#1-descripción-general-del-proyecto)
2. [Arquitectura Técnica](#2-arquitectura-técnica)
3. [Estructura de Directorios y Archivos](#3-estructura-de-directorios-y-archivos)
4. [Modelo de Datos](#4-modelo-de-datos)
5. [APIs y Servicios Externos](#5-apis-y-servicios-externos)
6. [Componentes Principales](#6-componentes-principales)
7. [Sistema de Filtrado y Validación](#7-sistema-de-filtrado-y-validación)
8. [Flujos de Trabajo Principales](#8-flujos-de-trabajo-principales)
9. [Páginas de la Aplicación Streamlit](#9-páginas-de-la-aplicación-streamlit)
10. [Sistema de Tracking de APIs](#10-sistema-de-tracking-de-apis)
11. [Configuración y Variables de Entorno](#11-configuración-y-variables-de-entorno)
12. [Funcionalidades por Módulo](#12-funcionalidades-por-módulo)

---

## 1. Descripción General del Proyecto

### 1.1 Objetivo

Sistema multi-agente para búsqueda, consolidación y gestión de datos de abogados y despachos especializados en extranjería e inmigración en España. El sistema utiliza múltiples APIs de búsqueda web, scraping inteligente y consolidación de datos para crear una base de datos completa y actualizada.

### 1.2 Tecnologías Principales

- **Framework Web:** Streamlit 1.29+
- **Lenguaje:** Python 3.8+
- **Almacenamiento:** JSON (archivos en `data/`)
- **APIs Externas:** Firecrawl, Tavily, Google Search, Google Places, OpenAI
- **Procesamiento:** pandas, rapidfuzz
- **Exportación:** CSV, Excel, PDF

### 1.3 Características Principales

- ✅ **Búsqueda Multi-API:** Ejecución paralela con múltiples servicios
- ✅ **Deduplicación Inteligente:** Hash exacto, teléfono normalizado, similitud fuzzy
- ✅ **Filtrado Automático:** Eliminación de listados, blogs, directorios
- ✅ **Dashboard Unificado:** Visualización completa en una sola pantalla
- ✅ **Gestión de Datos:** Edición en lote, limpieza de nombres, detección de duplicados
- ✅ **Enriquecimiento:** Completado automático de datos faltantes
- ✅ **Tracking de Costos:** Monitoreo de uso y gastos de APIs
- ✅ **Exportación Multi-formato:** CSV, Excel, PDF, JSON

---

## 2. Arquitectura Técnica

### 2.1 Patrón de Diseño

**Arquitectura Multi-Agente con Orquestador Central**

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit App                        │
│                  (app.py + pages/)                      │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Orquestador (core/orquestador.py)         │
│  - Coordina búsquedas                                  │
│  - Gestiona adapters                                   │
│  - Pipeline completo                                   │
└────┬──────────────┬──────────────┬─────────────────────┘
     │              │              │
┌────▼────┐  ┌──────▼─────┐  ┌────▼──────────┐
│Adapters │  │Consolidador│  │Filtros/Valid. │
│(APIs)   │  │(core/)     │  │(utils/)       │
└─────────┘  └────────────┘  └───────────────┘
```

### 2.2 Componentes Principales

1. **Orquestador (`core/orquestador.py`)**
   - Coordina búsquedas con múltiples APIs
   - Gestiona pipeline: búsqueda → scraping → consolidación → guardado
   - Maneja errores y retry logic

2. **Consolidador (`core/consolidador.py`)**
   - Detecta duplicados con 3 niveles de precisión
   - Fusiona registros duplicados
   - Aplica filtros automáticos
   - Gestiona índices para búsqueda rápida

3. **Adapters (`adapters/*.py`)**
   - Clase base abstracta: `SearchAdapter`
   - Implementaciones: Firecrawl, Tavily, Google, OpenAI
   - Estandarización de resultados a `SearchResult`

4. **Sistema de Filtros (`utils/filtros.py`)**
   - Exclusión de dominios (listados, redes sociales, etc.)
   - Patrones de nombres inválidos
   - URLs de blogs/artículos
   - Validación de registros

5. **Tracking de APIs (`utils/api_tracker.py`)**
   - Registro de uso por API
   - Cálculo de costos estimados
   - Límites y alertas

---

## 3. Estructura de Directorios y Archivos

```
Scraper/
├── app.py                      # Dashboard unificado principal
├── pages/                      # Páginas Streamlit
│   ├── 1_Dashboard.py         # Vista general con métricas
│   ├── 2_Buscar.py            # Interfaz de búsqueda
│   ├── 3_Datos.py             # Gestión avanzada de datos
│   ├── 4_Depurar.py           # Depuración de duplicados
│   ├── 4_Enriquecer.py        # Enriquecimiento de datos
│   ├── 5_Exportar.py          # Exportación multi-formato
│   └── 6_API_Costos.py        # Tracking de costos
│
├── adapters/                   # Conectores de APIs
│   ├── base.py                # Clase base SearchAdapter
│   ├── firecrawl_adapter.py   # Firecrawl (scraping)
│   ├── google_adapter.py      # Google Search + Places
│   ├── tavily_adapter.py      # Tavily (búsqueda IA)
│   └── openai_adapter.py      # OpenAI (estructuración)
│
├── core/                       # Lógica principal
│   ├── orquestador.py         # Coordinador principal
│   └── consolidador.py        # Motor de consolidación
│
├── prompts/                    # Prompts y schemas
│   ├── busqueda.py            # Prompts de búsqueda por ciudad
│   ├── extraccion.py          # Prompts de extracción
│   └── schemas.py             # Schemas de validación
│
├── utils/                      # Utilidades
│   ├── filtros.py             # Sistema de filtrado
│   ├── validators.py          # Validación de datos
│   ├── api_tracker.py         # Tracking de APIs
│   └── database.py            # Funciones de BD
│
├── data/                       # Datos JSON
│   ├── madrid.json            # Registros de Madrid
│   ├── barcelona.json         # Registros de Barcelona
│   ├── [ciudad].json          # Otros archivos por ciudad
│   ├── api_usage.json         # Uso de APIs
│   └── config_agentes.json    # Configuración de agentes
│
├── scripts/                    # Scripts CLI
│   ├── buscar_ciudad.py       # Búsqueda automatizada
│   └── resumen.py             # Generación de resúmenes
│
├── .streamlit/                 # Configuración Streamlit
│   ├── config.toml            # Configuración general
│   └── secrets.toml.example   # Ejemplo de secrets
│
├── requirements.txt            # Dependencias Python
├── .env                        # Variables de entorno (no commit)
└── README.md                   # Documentación básica
```

---

## 4. Modelo de Datos

### 4.1 Estructura de Archivo JSON por Ciudad

```json
{
  "metadata": {
    "fecha_actualizacion": "2026-01-17T05:46:06.118041",
    "total_registros": 627,
    "fuente": "consolidador_multiagente"
  },
  "registros": [
    {
      "nombre": "Abogados Extranjería Madrid",
      "tipo": "despacho",              // despacho | abogado | ong | oficial | pagina
      "telefono": ["+34 616 482 664", "+34 649 117 806"],
      "email": "info@abogadosextranjeriamadrid.com",
      "web": "https://www.abogadosextranjeriamadrid.com",
      "direccion": "C/ Marqués de Mondejar 16, 7A, 28028 Madrid",
      "ciudad": "Madrid",
      "distrito": "Salamanca",
      "codigo_postal": "28028",
      "especialidades": [
        "arraigo",
        "asilo",
        "nacionalidad",
        "reagrupación",
        "visados",
        "permisos",
        "expulsiones",
        "recursos"
      ],
      "idiomas": ["inglés", "francés"],
      "horario": "L-V: 9:00-18:00",
      "valoracion": "4.8/5 (+100 reseñas)",
      "fuente": "firecrawl_search",
      "url_origen": "https://www.abogadosextranjeriamadrid.com/contacto",
      "fecha_extraccion": "2026-01-17T03:44:40.963084",
      "fecha_actualizacion": "2026-01-17T05:07:25.537097"
    }
  ]
}
```

### 4.2 Campos del Registro

| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `nombre` | string | ✅ Sí | Nombre del despacho/abogado |
| `tipo` | string | ✅ Sí | `despacho`, `abogado`, `ong`, `oficial`, `pagina` |
| `telefono` | array[string] | ⚠️ Al menos 1 contacto | Lista de teléfonos |
| `email` | string \| null | ⚠️ Al menos 1 contacto | Email principal |
| `web` | string \| null | ⚠️ Al menos 1 contacto | URL del sitio web |
| `direccion` | string \| null | ❌ No | Dirección física completa |
| `ciudad` | string \| null | ❌ No | Ciudad donde se ubica |
| `distrito` | string \| null | ❌ No | Distrito o barrio |
| `codigo_postal` | string \| null | ❌ No | Código postal (5 dígitos) |
| `especialidades` | array[string] | ❌ No | Lista de especialidades |
| `idiomas` | array[string] | ❌ No | Idiomas hablados |
| `horario` | string \| null | ❌ No | Horario de atención |
| `valoracion` | string \| null | ❌ No | Rating/reseñas |
| `fuente` | string | ❌ No | API/origen de los datos |
| `url_origen` | string \| null | ❌ No | URL de donde se extrajo |
| `fecha_extraccion` | string (ISO) | ❌ No | Fecha de extracción inicial |
| `fecha_actualizacion` | string (ISO) | ❌ No | Última actualización |

### 4.3 Tipos Válidos

- **`despacho`:** Despacho colectivo o bufete
- **`abogado`:** Abogado individual
- **`ong`:** Organización no gubernamental
- **`oficial`:** Servicio público/oficial
- **`pagina`:** Página web genérica (puede ser inválido)

### 4.4 Especialidades Reconocidas

```
arraigo, arraigo_social, arraigo_laboral, arraigo_familiar, arraigo_formativo,
asilo, proteccion_internacional, nacionalidad, reagrupacion, reagrupacion_familiar,
visados, permisos_trabajo, autorizacion_residencia, expulsiones, recursos, golden_visa
```

---

## 5. APIs y Servicios Externos

### 5.1 Firecrawl API

**Propósito:** Scraping profundo y extracción estructurada

**Características:**
- Scraping de páginas web completas
- Extracción estructurada con JSON Schema
- Búsqueda web integrada
- Crawling de sitios completos

**Configuración:**
- Variable: `FIRECRAWL_API_KEY`
- Límite gratis: 500 créditos/mes
- Costo adicional: ~$0.01 por crédito

**Uso en el Sistema:**
- Scraping de URLs encontradas
- Extracción de datos de contacto
- Procesamiento de directorios
- Funcionalidad de enriquecimiento

### 5.2 Tavily API

**Propósito:** Búsqueda web optimizada para IA

**Características:**
- Búsqueda semántica avanzada
- Respuestas resumidas por IA
- Profundidad configurable (basic/advanced)

**Configuración:**
- Variable: `TAVILY_API_KEY`
- Límite gratis: 1,000 requests/mes
- Costo adicional: ~$0.001 por request

**Uso en el Sistema:**
- Búsqueda inicial amplia
- Encontrar sitios web de despachos
- Validación de URLs

### 5.3 Google Custom Search API

**Propósito:** Búsqueda web estándar

**Características:**
- Búsqueda avanzada con operadores
- Filtros por idioma/país
- Restricción a sitios específicos

**Configuración:**
- Variables: `GOOGLE_API_KEY`, `GOOGLE_CSE_ID`
- Límite gratis: 100 requests/día
- Costo adicional: ~$0.005 por request

**Uso en el Sistema:**
- Búsqueda complementaria
- Validación cruzada con otros APIs

### 5.4 Google Places API

**Propósito:** Negocios locales

**Características:**
- Búsqueda por ubicación
- Detalles de negocios (teléfono, dirección, horario)
- Valoraciones y reseñas

**Configuración:**
- Variable: `GOOGLE_API_KEY`
- Crédito gratis: $200 USD/mes
- Costo: ~$0.017 por request

**Uso en el Sistema:**
- Búsqueda por coordenadas
- Completar datos de contacto
- Validación de direcciones

### 5.5 OpenAI API

**Propósito:** Estructuración de datos con IA

**Características:**
- Extracción estructurada de texto libre
- Normalización de datos
- Clasificación de tipos

**Configuración:**
- Variable: `OPENAI_API_KEY`
- Modelo: `gpt-4o-mini`
- Costo: ~$0.01 por query

**Uso en el Sistema:**
- Procesamiento de texto no estructurado
- Clasificación de registros
- Validación inteligente

---

## 6. Componentes Principales

### 6.1 Orquestador (`core/orquestador.py`)

**Clase:** `Orquestador`

**Responsabilidades:**
- Coordinar búsquedas con múltiples APIs
- Gestionar pipeline completo
- Manejar errores y retries
- Consolidar resultados

**Métodos Principales:**

```python
ejecutar_busqueda(config: BusquedaConfig) -> ResultadoBusqueda
_buscar_con_adapter(adapter, prompts, max_resultados) -> List[SearchResult]
_inicializar_adapters() -> None
```

**Pipeline de Ejecución:**

1. **Búsqueda Amplia:** Tavily, Google Search
2. **Búsqueda Local:** Google Places (opcional)
3. **Scraping Profundo:** Firecrawl en URLs encontradas
4. **Filtrado:** Sistema de filtros automático
5. **Consolidación:** Deduplicación y fusión
6. **Guardado:** Actualización de JSON por ciudad

### 6.2 Consolidador (`core/consolidador.py`)

**Clase:** `Consolidador`

**Responsabilidades:**
- Detectar duplicados (3 niveles)
- Fusionar registros duplicados
- Aplicar filtros de validación
- Gestionar índices para búsqueda rápida

**Niveles de Detección de Duplicados:**

1. **Hash Exacto:** `hash(nombre + telefono_principal + email)`
2. **Teléfono Normalizado:** Comparación de teléfonos normalizados
3. **Similitud Fuzzy:** Similitud de nombres >85% (rapidfuzz)

**Métodos Principales:**

```python
procesar_batch(registros: List[Dict], verbose=False) -> ConsolidacionResult
es_duplicado(registro: Dict) -> Tuple[bool, Optional[int]]
fusionar(existente: Dict, nuevo: Dict) -> Dict
guardar() -> None
```

**Resultados de Consolidación:**

- `agregados`: Registros nuevos agregados
- `actualizados`: Registros existentes actualizados
- `duplicados_ignorados`: Registros duplicados ignorados
- `invalidos`: Registros que no pasan validación básica
- `filtrados`: Registros rechazados por filtros (blogs, etc.)

### 6.3 Sistema de Adapters (`adapters/`)

**Clase Base:** `SearchAdapter` (abstracta)

**Método Principal:**
```python
@abstractmethod
def search(query: str, **kwargs) -> List[SearchResult]
```

**Implementaciones:**

- **FirecrawlAdapter:** Scraping y extracción estructurada
- **TavilyAdapter:** Búsqueda semántica
- **GoogleSearchAdapter:** Búsqueda web estándar
- **GooglePlacesAdapter:** Negocios locales
- **OpenAIAdapter:** Estructuración con IA

**Tipo de Retorno:** `List[SearchResult]`

**SearchResult (dataclass):**
```python
@dataclass
class SearchResult:
    nombre: str
    tipo: str
    telefono: List[str]
    email: Optional[str]
    web: Optional[str]
    direccion: Optional[str]
    ciudad: Optional[str]
    distrito: Optional[str]
    especialidades: List[str]
    valoracion: Optional[float]
    fuente: Optional[str]
    url_origen: Optional[str]
    fecha_extraccion: str
```

---

## 7. Sistema de Filtrado y Validación

### 7.1 Filtros de Dominios (`utils/filtros.py`)

**Dominios Excluidos:**

- **Diccionarios/Traducciones:** reverso.net, spanishdict.com, wordreference.com
- **Redes Sociales:** facebook.com, linkedin.com/pulse, twitter.com
- **Noticias:** elpais.com, elmundo.es, abc.es
- **Directorios:** paginasamarillas, qdq.com, justia.com
- **Q&A:** quora.com, yahoo.com/answers, stackoverflow.com
- **Otros Países:** `.cl/`, `.mx/`, `.ar/`, `.co/`
- **USA:** abogado.la, laligadefensora.com (Los Angeles)

### 7.2 Patrones de Nombres Excluidos

**Regex Patterns:**
- `\bmejores?\b`, `\btranslation\b`, `\bdiccionario\b`
- `^top \d+`, `^listado de`, `^ranking`
- `\bblog\b`, `\barticulo\b`, `\bnoticia\b`
- `^como `, `^que es `, `^requisitos para`

### 7.3 Patrones de URLs Excluidas

**Patrones que indican blog/artículo:**
- `/blog`, `/blog-juridico/`, `/blogs/`
- `/articulo`, `/noticia`, `/news`
- `/post/`, `/article/`
- `/categoria/`, `/category/`
- `/\d{4}/\d{2}/` (URLs con fecha)

### 7.4 Función de Validación

```python
def es_registro_valido(registro: Dict) -> Tuple[bool, str]:
    """
    Returns: (es_valido, razon_si_invalido)
    """
```

**Validaciones:**
1. Nombre válido (mínimo 3 caracteres)
2. Web válida (mínimo 10 caracteres)
3. Dominio no excluido
4. Nombre no coincide con patrones excluidos
5. URL no coincide con patrones de blog

---

## 8. Flujos de Trabajo Principales

### 8.1 Flujo de Búsqueda Completo

```
1. Usuario selecciona ciudad y configuración
   ↓
2. Orquestador carga prompts específicos de ciudad
   ↓
3. Ejecución paralela de búsquedas:
   - Tavily (búsqueda semántica)
   - Google Search (búsqueda estándar)
   - Google Places (negocios locales)
   ↓
4. Agregación de URLs encontradas
   ↓
5. Scraping profundo con Firecrawl (opcional):
   - Extracción estructurada con JSON Schema
   - Procesamiento de directorios
   ↓
6. Filtrado automático:
   - Exclusión de dominios
   - Validación de nombres
   - Detección de blogs/artículos
   ↓
7. Consolidación:
   - Detección de duplicados (3 niveles)
   - Fusión de registros duplicados
   - Validación final
   ↓
8. Guardado en JSON por ciudad
   ↓
9. Actualización de estadísticas de APIs
```

### 8.2 Flujo de Consolidación

```
1. Cargar base de datos existente
   ↓
2. Construir índices:
   - Hash (nombre + tel + email)
   - Teléfono normalizado
   - Email normalizado
   ↓
3. Para cada registro nuevo:
   a. Verificar hash exacto → ¿duplicado?
   b. Verificar teléfono normalizado → ¿duplicado?
   c. Calcular similitud fuzzy de nombre → ¿>85%?
   ↓
4. Si es duplicado:
   - Fusionar con registro existente
   - Actualizar campos faltantes
   - Combinar listas (teléfonos, especialidades)
   ↓
5. Si es nuevo:
   - Agregar a base de datos
   - Actualizar índices
   ↓
6. Guardar cambios
```

### 8.3 Flujo de Enriquecimiento

```
1. Identificar registros con web pero sin teléfono/email
   ↓
2. Para cada registro:
   a. Obtener URL de web
   b. Scraping con Firecrawl
   c. Extraer datos estructurados (JSON Schema)
   d. Parsear HTML para teléfonos/emails
   ↓
3. Validar datos extraídos:
   - Formato de teléfono español
   - Formato de email válido
   - Dirección completa
   ↓
4. Actualizar registro:
   - Agregar teléfonos encontrados
   - Agregar email si no existe
   - Completar dirección si falta
   ↓
5. Guardar cambios con fecha_actualizacion
```

---

## 9. Páginas de la Aplicación Streamlit

### 9.1 Dashboard Unificado (`app.py`)

**Funcionalidad:**
- Vista completa en una sola pantalla
- Métricas principales (total, completitud, etc.)
- Gráficos por ciudad
- Indicadores de calidad de datos
- Estado de APIs configuradas
- Acciones rápidas (búsqueda, enriquecimiento, exportar)

**Métricas Mostradas:**
- Total de registros
- Con teléfono / Email / Web / Dirección
- Registros completos (4/4 campos)
- Distribución por ciudad
- Niveles de completitud (4/4, 3/4, 2/4, etc.)

**Gráficos:**
- Barras horizontales por ciudad
- Progreso de completitud
- Uso de APIs (si está disponible)

### 9.2 Página de Búsqueda (`pages/2_Buscar.py`)

**Funcionalidades:**
- Selección de ciudad
- Configuración de APIs a usar
- Opciones avanzadas (max resultados, scraping profundo)
- Búsqueda rápida automática
- Búsqueda manual personalizada
- Historial de búsquedas

**Configuración:**
- APIs: Firecrawl, Tavily, Google Search, Google Places
- Máximo de resultados por API (5-50)
- Activar/desactivar Google Places
- Activar/desactivar scraping profundo

### 9.3 Gestión de Datos (`pages/3_Datos.py`)

**Pestañas Principales:**

#### 9.3.1 Vista de Tabla
- Tabla ordenable con todos los campos
- Filtros por tipo, datos completos/incompletos
- Búsqueda por nombre
- Exportación a CSV

#### 9.3.2 Edición en Lote
- Checkboxes para seleccionar múltiples registros
- Seleccionar/deseleccionar todos
- Cambiar tipo en masa
- Cambiar ciudad en masa
- Indicadores visuales (📞📧🌐)

#### 9.3.3 Agrupar Duplicados
- Detección por dominio web
- Detección por teléfono
- Vista expandible de grupos
- Funcionalidad de fusión (en desarrollo)

#### 9.3.4 Limpiar Nombres
- Análisis automático de nombres
- Separación nombre/descripción
- Detección automática de tipo
- Selección con checkboxes
- Aplicación en lote

**Filtros del Sidebar:**
- Ciudad (o "Todas")
- Tipo (despacho, abogado, ong, etc.)
- Estado de datos (completos, incompletos, sin teléfono, sin email)
- Búsqueda por nombre
- Ordenación (nombre, tipo, fecha_actualizacion, ciudad)

### 9.4 Enriquecimiento (`pages/4_Enriquecer.py`)

**Funcionalidades:**

#### 9.4.1 Lista para Enriquecimiento
- Filtros: Sin teléfono, sin email, sin dirección
- Selección de ciudad
- Tabla con registros a enriquecer

#### 9.4.2 Enriquecimiento Masivo
- Seleccionar múltiples registros
- Método: Requests (básico), Tavily (búsqueda), Firecrawl (estructurado)
- Procesamiento en batch
- Resultados con estadísticas

#### 9.4.3 Enriquecimiento Individual
- Vista detallada de registro actual
- Datos actuales vs. datos encontrados
- Aprobación manual de cambios
- Revisión paso a paso

**Métodos de Enriquecimiento:**
- **Requests:** Scraping básico de HTML
- **Tavily:** Búsqueda inteligente de datos faltantes
- **Firecrawl:** Extracción estructurada con JSON Schema

### 9.5 Depuración (`pages/4_Depurar.py`)

**Funcionalidades:**
- Detección de posibles duplicados
- Revisión manual de pares similares
- Fusión de duplicados confirmados
- Opción de mantener ambos si no son duplicados

### 9.6 Exportación (`pages/5_Exportar.py`)

**Formatos Disponibles:**
- **CSV:** Para Excel/hojas de cálculo
- **Excel (.xlsx):** Con formato y columnas
- **PDF:** Para impresión/documentación
- **JSON:** Para desarrollo/integración

**Opciones:**
- Selección de ciudad (o todas)
- Filtros por tipo, completitud
- Selección de columnas a exportar

### 9.7 API Costos (`pages/6_API_Costos.py`)

**Funcionalidades:**
- Uso por API (hoy, mes actual, total)
- Costos estimados
- Límites y alertas
- Gráficos de uso
- Historial de uso

---

## 10. Sistema de Tracking de APIs

### 10.1 Estructura de Datos (`data/api_usage.json`)

```json
{
  "dia_actual": {
    "2026-01-17": {
      "firecrawl": {"requests": 10, "creditos": 15, "costo": 0.15},
      "tavily": {"requests": 25, "creditos": 0, "costo": 0.025}
    }
  },
  "mes_actual": {
    "2026-01": {
      "firecrawl": {"requests": 450, "creditos": 680, "costo": 6.80},
      "tavily": {"requests": 800, "creditos": 0, "costo": 0.80}
    }
  },
  "totales": {
    "firecrawl": {"requests": 1500, "creditos": 2200, "costo": 22.00},
    "tavily": {"requests": 3000, "creditos": 0, "costo": 3.00}
  }
}
```

### 10.2 Clase APITracker (`utils/api_tracker.py`)

**Métodos Principales:**

```python
registrar_uso(api, requests=1, creditos=0, tokens_input=0, tokens_output=0)
obtener_uso_hoy(api) -> Dict
obtener_uso_mes(api, mes) -> Dict
obtener_totales(api) -> Dict
_calcular_costo(api, requests, creditos, tokens_input, tokens_output) -> float
```

**Costos Estimados (USD):**

| API | Unidad | Costo |
|-----|--------|-------|
| Firecrawl | Crédito | $0.01 |
| Google Search | Request | $0.005 |
| Google Places | Request | $0.017 |
| Tavily | Request | $0.001 |
| OpenAI | Query (~1k tokens) | $0.01 |

---

## 11. Configuración y Variables de Entorno

### 11.1 Archivo `.env`

```env
# Firecrawl - https://firecrawl.dev
FIRECRAWL_API_KEY=fc-tu-api-key-aqui

# Google APIs - https://console.cloud.google.com
GOOGLE_API_KEY=tu-google-api-key
GOOGLE_CSE_ID=tu-custom-search-engine-id

# Tavily - https://tavily.com
TAVILY_API_KEY=tvly-tu-api-key-aqui

# OpenAI - https://platform.openai.com
OPENAI_API_KEY=sk-tu-api-key-aqui
```

### 11.2 Streamlit Cloud Secrets

Para despliegue en Streamlit Cloud, configurar en **Settings > Secrets:**

```toml
FIRECRAWL_API_KEY = "fc-tu-api-key"
GOOGLE_API_KEY = "tu-google-api-key"
GOOGLE_CSE_ID = "tu-cse-id"
TAVILY_API_KEY = "tvly-tu-api-key"
OPENAI_API_KEY = "sk-tu-api-key"
```

### 11.3 Configuración de Agentes (`data/config_agentes.json`)

```json
{
  "apis": {
    "firecrawl": {"habilitado": true, "prioridad": 1},
    "google_search": {"habilitado": true, "prioridad": 2},
    "tavily": {"habilitado": true, "prioridad": 4}
  },
  "busqueda": {
    "max_resultados_por_query": 10,
    "max_queries_por_api": 5,
    "delay_entre_requests_ms": 1000
  },
  "consolidacion": {
    "umbral_similitud_nombre": 85,
    "umbral_similitud_telefono": 60
  }
}
```

---

## 12. Funcionalidades por Módulo

### 12.1 Prompts de Búsqueda (`prompts/busqueda.py`)

**Estructura:**
- Prompts por ciudad y zona
- Exclusiones automáticas en cada prompt
- Prompts por especialidad
- URLs de directorios por ciudad

**Ejemplo de Prompt:**
```python
"madrid_centro": [
    '"despacho de abogados" extranjería Madrid "llámenos" OR "contacte" OR "cita previa"',
    '"bufete" inmigración Madrid "nuestro equipo" OR "sobre nosotros" teléfono',
    ...
]
```

### 12.2 Validadores (`utils/validators.py`)

**Funciones:**
- `validar_email(email: str) -> bool`
- `validar_telefono(telefono: str) -> bool`
- `normalizar_telefono(telefono: str) -> str`
- `normalizar_email(email: str) -> str`

### 12.3 Database Utils (`utils/database.py`)

**Funciones:**
- `cargar_ciudad(ciudad: str) -> Dict`
- `guardar_ciudad(ciudad: str, data: Dict) -> bool`
- `listar_ciudades() -> List[str]`
- `buscar_registro(ciudad: str, criterio: Dict) -> Optional[Dict]`

### 12.4 Scripts CLI

#### 12.4.1 `scripts/buscar_ciudad.py`

**Uso:**
```bash
py scripts/buscar_ciudad.py Madrid 3
```

**Funcionalidad:**
- Ejecuta múltiples rondas de búsqueda
- Configuración automática de APIs
- Estadísticas al finalizar

#### 12.4.2 `scripts/resumen.py`

**Funcionalidad:**
- Genera tabla resumen de registros por ciudad
- Estadísticas de completitud
- Exportación a texto

---

## 13. Notas Técnicas Adicionales

### 13.1 Normalización de Teléfonos

**Formato Estándar:** `+34 XXX XXX XXX`

**Reglas:**
- Prefijo `+34` siempre presente
- Eliminación de espacios, guiones, paréntesis
- Validación: 9 dígitos (sin prefijo) o 11-12 (con prefijo)
- Primer dígito debe ser 6, 7, 8 o 9

### 13.2 Detección de Tipo

**Lógica:**
1. Si nombre contiene "Contacto", "Los mejores", etc. → `pagina`
2. Si nombre coincide con patrón "Abogado [Nombre]" → `abogado`
3. Si nombre contiene "& Asociados", "S.L.", "Bufete" → `despacho`
4. Si es muy corto o genérico → `revisar`

### 13.3 Limpieza de Nombres

**Separadores detectados:**
- ` - `, ` | `, ` – `, ` — `, ` · `, ` • `, `:`

**Sufijos eliminados:**
- `| Abogados`, ` - Madrid`, ` (España)`

**Resultado:**
- Nombre limpio separado de descripción
- Descripción extraída si es relevante (>5 caracteres)

### 13.4 Manejo de Errores

**Estrategias:**
- Try/except en todas las llamadas a APIs
- Retry logic en orquestador (máx. 3 intentos)
- Logging de errores sin detener el proceso
- Continuación con otras APIs si una falla

### 13.5 Performance

**Optimizaciones:**
- Índices en memoria para búsqueda rápida de duplicados
- Procesamiento en batch para consolidación
- Paralelización de búsquedas con múltiples APIs
- Carga lazy de datos en Streamlit (solo cuando se necesita)

---

## 14. Instrucciones para Desarrollo Externo

### 14.1 Uso de Este Documento

Este documento está diseñado para ser utilizado con **Gemini** o **otros LLMs** para generar instrucciones y prompts precisos para el desarrollo del sistema, sin necesidad de estar en Cursor.

### 14.2 Estructura de Prompt Sugerida

Al usar este documento con un LLM, estructura tu prompt así:

```
Soy desarrollador del sistema de búsqueda de abogados de extranjería. 
Necesito [DESCRIPCIÓN DE LA TAREA].

Información del sistema:
[Incluir secciones relevantes de este documento]

Por favor, proporciona:
1. Instrucciones paso a paso
2. Código específico si es necesario
3. Cambios en archivos afectados
4. Consideraciones técnicas
```

### 14.3 Áreas de Mejora Futuras

- [ ] Implementar base de datos SQLite/PostgreSQL para mejor performance
- [ ] Sistema de caché para resultados de APIs
- [ ] API REST para integraciones externas
- [ ] Sistema de webhooks para actualizaciones
- [ ] Dashboard de administración avanzado
- [ ] Sistema de notificaciones por email
- [ ] Integración con LinkedIn para datos profesionales
- [ ] Scraping de colegios oficiales de abogados
- [ ] Sistema de validación de emails (MX records)
- [ ] Machine Learning para detección de calidad de datos

---

## 15. Contacto y Soporte

**Repositorio GitHub:** `oscarsao/evergreen-scraper`  
**Plataforma de Despliegue:** Streamlit Cloud  
**Documentación:** Este archivo

---

**Fin del Documento Técnico**
