# Configuración de APIs

Crea un archivo `.env` en la raíz del proyecto con las siguientes claves:

```env
# Firecrawl (Ya configurado)
FIRECRAWL_API_KEY=fc-xxxxx

# Google APIs (100 búsquedas/día gratis)
# Crear en: https://console.cloud.google.com
GOOGLE_API_KEY=AIzaxxxxx
GOOGLE_CSE_ID=xxxxx

# Tavily (1,000/mes gratis) - RECOMENDADA
# Obtener: https://tavily.com
TAVILY_API_KEY=tvly-xxxxx

# OpenAI (Pago por uso ~$0.01/query)
OPENAI_API_KEY=sk-xxxxx
```

## Costos Estimados

| API | Plan Gratis | Uso Típico |
|-----|-------------|------------|
| Firecrawl | 500/mes | Scraping profundo |
| Google Search | 100/día | Búsqueda web |
| Google Places | $200/mes | Negocios locales |
| Tavily | 1,000/mes | Búsqueda IA |
| OpenAI | ~$0.01/query | Estructurar datos |

Para uso normal el costo es **$0** usando planes gratuitos.
