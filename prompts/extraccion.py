"""
Prompts y schemas para extracción estructurada de datos.
Usados con Firecrawl Extract y OpenAI.
"""

# =============================================================================
# Schema JSON para extracción de abogados
# =============================================================================

SCHEMA_ABOGADO = {
    "type": "object",
    "properties": {
        "nombre": {
            "type": "string",
            "description": "Nombre completo del abogado o nombre del despacho"
        },
        "tipo": {
            "type": "string",
            "enum": ["despacho", "abogado", "ong"],
            "description": "Tipo de entidad: despacho colectivo, abogado individual u ONG"
        },
        "telefonos": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Todos los números de teléfono encontrados (fijos, móviles, WhatsApp)"
        },
        "email": {
            "type": "string",
            "description": "Email principal de contacto"
        },
        "emails_adicionales": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Otros emails encontrados"
        },
        "web": {
            "type": "string",
            "description": "URL del sitio web oficial"
        },
        "direccion": {
            "type": "string",
            "description": "Dirección física completa incluyendo número y código postal"
        },
        "ciudad": {
            "type": "string",
            "description": "Ciudad donde se ubica"
        },
        "distrito": {
            "type": "string",
            "description": "Distrito o barrio"
        },
        "codigo_postal": {
            "type": "string",
            "description": "Código postal (5 dígitos)"
        },
        "especialidades": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Áreas de especialización: arraigo, asilo, nacionalidad, reagrupación, visados, permisos, expulsiones, recursos"
        },
        "idiomas": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Idiomas que hablan además de español"
        },
        "horario": {
            "type": "string",
            "description": "Horario de atención al público"
        },
        "valoracion": {
            "type": "number",
            "description": "Valoración/rating si está disponible (1-5)"
        },
        "num_opiniones": {
            "type": "integer",
            "description": "Número de opiniones/reviews"
        }
    },
    "required": ["nombre"]
}


# =============================================================================
# Prompts de extracción
# =============================================================================

PROMPT_EXTRACCION = """Extrae TODOS los datos de contacto de abogados y despachos de extranjería de esta página.

REGLAS IMPORTANTES:
1. Incluir TODOS los teléfonos que encuentres (fijos comenzando por 91/93, móviles por 6/7, WhatsApp)
2. Los emails deben contener @ y un dominio válido (.es, .com, etc.)
3. La dirección debe incluir: calle/avenida, número, y código postal si están disponibles
4. Identificar especialidades mencionadas:
   - arraigo (social, laboral, familiar, formativo)
   - asilo y protección internacional
   - nacionalidad española
   - reagrupación familiar
   - visados y permisos de trabajo
   - expulsiones y recursos
5. NO inventar datos - extraer SOLO lo que está explícitamente en la página
6. Si hay múltiples abogados o despachos en la página, extraer TODOS como array
7. Distinguir entre despachos (empresas), abogados individuales, y ONGs

Devuelve JSON válido con array "abogados" conteniendo todos los encontrados."""


PROMPT_EXTRACCION_DIRECTORIO = """Esta es una página de directorio de abogados. Extrae TODOS los profesionales listados.

Para cada abogado/despacho encontrado, extrae:
- Nombre completo o nombre del despacho
- Todos los teléfonos de contacto
- Email(s)
- Dirección física
- Sitio web
- Especialidades mencionadas

IMPORTANTE:
- Cada entrada del directorio debe ser un elemento separado en el array
- No omitir ningún profesional listado
- Si falta algún dato, usar null
- Mantener el formato exacto de teléfonos como aparecen

Formato de salida: {"abogados": [...]}"""


PROMPT_EXTRACCION_CONTACTO = """Esta es una página de contacto de un despacho de abogados. Extrae toda la información disponible.

Busca específicamente:
1. Nombre del despacho o abogado titular
2. TODOS los teléfonos (general, directo, móvil, WhatsApp)
3. TODOS los emails (general, específico por departamento)
4. Dirección completa con código postal
5. Horario de atención
6. Formulario de contacto (si tiene, indicar URL)

También busca:
- Redes sociales (LinkedIn, Twitter/X, Facebook)
- Idiomas que hablan
- Especialidades destacadas

Formato: JSON con todos los campos encontrados."""


PROMPT_EXTRACCION_GOOGLE_MAPS = """Extrae información de este resultado de Google Maps de un despacho de abogados.

Datos a extraer:
- Nombre del negocio
- Dirección completa
- Teléfono
- Sitio web
- Horario de apertura
- Valoración (estrellas)
- Número de reseñas
- Categoría/tipo de negocio

Si hay reseñas visibles, identifica menciones de especialidades en extranjería."""


# =============================================================================
# Prompts para OpenAI (estructuración de texto)
# =============================================================================

PROMPT_ESTRUCTURAR = """Eres un experto en extraer información de contacto de profesionales legales especializados en extranjería.

Dado el siguiente texto extraído de una página web, identifica y estructura la información de todos los abogados/despachos de extranjería mencionados.

INSTRUCCIONES DETALLADAS:

1. IDENTIFICACIÓN:
   - Busca nombres de despachos (terminan en "Abogados", "& Asociados", "Law", etc.)
   - Busca nombres de abogados individuales (con título "D./Dña.", "Lcdo/a.", etc.)
   - Identifica ONGs (CEAR, ACCEM, Cruz Roja, Cáritas, etc.)

2. TELÉFONOS:
   - Normaliza al formato: +34 XXX XXX XXX
   - Incluye prefijo +34 si no lo tiene
   - Identifica tipo: fijo (91, 93, 96...) o móvil (6XX, 7XX)

3. EMAILS:
   - Valida que contengan @ y dominio válido
   - Excluye emails genéricos tipo example@, test@, noreply@
   - Preferir emails con dominio propio sobre gmail/hotmail

4. DIRECCIONES:
   - Formato: "Calle/Avda Nombre, Número, CP Ciudad"
   - Incluir piso/puerta si está disponible
   - Código postal español: 5 dígitos

5. ESPECIALIDADES:
   - Clasificar en: arraigo, asilo, nacionalidad, reagrupacion, visados, permisos_trabajo, expulsiones, recursos
   - Solo incluir si se menciona explícitamente

6. VALIDACIÓN:
   - Un registro válido debe tener al menos: nombre + (teléfono OR email OR web)
   - Si no hay dato, usar null (no string vacío ni "N/A")

FORMATO DE SALIDA (JSON válido):
{
  "abogados": [
    {
      "nombre": "string",
      "tipo": "despacho|abogado|ong",
      "telefono": ["string"] o [],
      "email": "string" o null,
      "web": "string" o null,
      "direccion": "string" o null,
      "ciudad": "string" o null,
      "distrito": "string" o null,
      "especialidades": ["string"] o []
    }
  ],
  "metadata": {
    "total_encontrados": number,
    "con_telefono": number,
    "con_email": number,
    "con_web": number
  }
}

TEXTO A PROCESAR:
{texto}"""


PROMPT_LIMPIAR_REGISTRO = """Dado este registro de abogado con posibles errores o datos incompletos:

{registro}

Limpia y normaliza el registro:
1. Corrige formato de teléfonos a +34 XXX XXX XXX
2. Valida y limpia emails
3. Completa ciudad si se puede inferir del código postal o dirección
4. Elimina datos claramente inválidos (teléfonos con menos de 9 dígitos, etc.)
5. NO inventes datos que no estén presentes

Devuelve el registro limpio en formato JSON."""


PROMPT_FUSIONAR_REGISTROS = """Tengo dos registros que parecen ser del mismo abogado/despacho:

REGISTRO EXISTENTE (prioridad alta):
{registro1}

REGISTRO NUEVO (datos adicionales):
{registro2}

Fusiona los registros siguiendo estas reglas:
1. Mantener TODOS los datos del registro existente
2. Agregar datos nuevos que no existan en el existente
3. Si hay conflicto, preferir el registro existente EXCEPTO si está vacío/null
4. Combinar arrays (teléfonos, especialidades) eliminando duplicados
5. Para valoración, usar el más reciente o el que tenga más opiniones

Devuelve UN SOLO registro fusionado en JSON."""
