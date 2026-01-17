"""
Prompts de búsqueda optimizados por zona y fuente.
Estrategia de 4 capas para máxima cobertura.
"""

# =============================================================================
# CAPA 1: Prompts para búsqueda web (Google/Tavily/Serper)
# =============================================================================

PROMPTS_BUSQUEDA = {
    # -------------------------------------------------------------------------
    # MADRID - Por zonas geográficas
    # -------------------------------------------------------------------------
    "madrid_centro": [
        # Búsqueda por valoraciones (encuentra los más activos)
        'site:google.com/maps "abogado extranjería" Madrid centro opiniones',
        
        # Directorios profesionales
        "site:abogados.portaley.com extranjería Madrid",
        "site:easyoffer.es abogado extranjería Madrid contacto",
        
        # Búsqueda geográfica precisa por CP
        '"abogado extranjería" Madrid "28001" OR "28002" OR "28003" OR "28004" teléfono',
        '"despacho inmigración" Madrid centro "calle" email contacto',
        
        # Por especialidad + ubicación
        '"arraigo social" abogado Madrid telefono -foro -pregunta -yahoo',
        '"nacionalidad española" abogado Madrid "consulta" contacto',
        
        # Colegios y asociaciones
        "site:icam.es OR site:apaem.net abogado extranjería directorio",
    ],
    
    "madrid_sur": [
        '"abogado extranjería" Carabanchel OR Usera OR Villaverde teléfono email',
        '"despacho inmigración" "Latina" OR "Vallecas" Madrid contacto',
        'site:google.com/maps abogado inmigración Leganés OR Getafe OR Móstoles',
        '"arraigo" abogado "zona sur" Madrid contacto dirección',
        '"abogado extranjería" Parla OR Fuenlabrada teléfono',
        '"permiso trabajo" abogado Alcorcón OR Leganés contacto',
    ],
    
    "madrid_norte": [
        '"abogado extranjería" Tetuán OR Fuencarral OR Chamartín teléfono email',
        'site:google.com/maps abogado extranjería Alcobendas OR "Tres Cantos"',
        '"inmigración" despacho "corredor Henares" Alcalá teléfono',
        '"abogado extranjería" "San Sebastián de los Reyes" OR Colmenar contacto',
        '"nacionalidad" abogado Pozuelo OR "Las Rozas" OR Majadahonda',
    ],
    
    "madrid_este": [
        '"abogado extranjería" "Ciudad Lineal" OR "San Blas" OR Vicálvaro teléfono',
        '"despacho inmigración" Coslada OR "San Fernando" contacto',
        '"arraigo" abogado Torrejón OR Alcalá email',
        'site:google.com/maps abogado extranjería Rivas-Vaciamadrid OR Arganda',
    ],
    
    # -------------------------------------------------------------------------
    # MADRID - Fuentes especializadas
    # -------------------------------------------------------------------------
    "madrid_directorios": [
        "directorio abogados extranjería Madrid 2024 2025 listado completo",
        "mejores abogados extranjería Madrid ranking valoraciones",
        "colegio abogados Madrid especialistas inmigración directorio",
        '"APAEM" asociación profesional abogados extranjería listado',
    ],
    
    "madrid_ongs": [
        'site:cear.es OR site:accem.es Madrid extranjería contacto teléfono',
        '"servicio orientación jurídica" extranjería Madrid ayuntamiento CAM',
        '"turno de oficio" extranjería Madrid ICAM cómo solicitar requisitos',
        'ONG "asistencia legal gratuita" inmigrantes Madrid listado',
        '"Cruz Roja" Madrid extranjería asistencia jurídica contacto',
        '"Cáritas" Madrid inmigración asesoría legal teléfono',
    ],
    
    "madrid_especialidades": [
        '"recurso expulsión" abogado Madrid especialista contacto experiencia',
        '"protección internacional" OR asilo abogado Madrid despacho',
        '"reagrupación familiar" abogado Madrid experiencia teléfono',
        '"permiso trabajo" OR "autorización residencia" abogado Madrid 2024 2025',
        '"Golden Visa" OR "visado inversor" abogado Madrid',
        '"arraigo formativo" OR "arraigo para formación" abogado Madrid',
        '"modificación permiso" extranjería abogado Madrid',
    ],
    
    # -------------------------------------------------------------------------
    # BARCELONA
    # -------------------------------------------------------------------------
    "barcelona_centro": [
        '"abogado extranjería" Barcelona "Eixample" OR "Ciutat Vella" teléfono',
        'site:google.com/maps abogado inmigración Barcelona centro opiniones',
        '"despacho extranjería" Barcelona "Gràcia" OR "Sant Martí" contacto',
        '"arraigo" abogado Barcelona email -foro',
    ],
    
    "barcelona_area": [
        '"abogado extranjería" Hospitalet OR Badalona OR "Santa Coloma" teléfono',
        '"inmigración" despacho Sabadell OR Terrassa contacto',
        'site:icab.cat abogado extranjería directorio',
    ],
    
    # -------------------------------------------------------------------------
    # VALENCIA
    # -------------------------------------------------------------------------
    "valencia": [
        '"abogado extranjería" Valencia ciudad teléfono email',
        'site:google.com/maps abogado inmigración Valencia opiniones',
        '"despacho extranjería" Valencia contacto -foro',
        '"arraigo" OR "nacionalidad" abogado Valencia',
    ],
    
    # -------------------------------------------------------------------------
    # Otras ciudades
    # -------------------------------------------------------------------------
    "sevilla": [
        '"abogado extranjería" Sevilla teléfono email contacto',
        '"despacho inmigración" Sevilla "Triana" OR "Nervión"',
    ],
    
    "malaga": [
        '"abogado extranjería" Málaga teléfono contacto',
        '"Golden Visa" abogado "Costa del Sol" Marbella',
    ],
    
    "bilbao": [
        '"abogado extranjería" Bilbao OR "País Vasco" teléfono',
        '"inmigración" despacho Vitoria OR "San Sebastián"',
    ],
}

# Prompts avanzados con operadores
PROMPTS_AVANZADOS = {
    "valoraciones_google": [
        'site:google.com/maps "abogado extranjería" "{ciudad}" "5 estrellas" OR "muy recomendado"',
        'site:google.com/maps "despacho inmigración" "{ciudad}" opiniones reviews',
    ],
    
    "exclusion_ruido": [
        '"{especialidad}" abogado {ciudad} teléfono -foro -pregunta -yahoo -respuestas -"hace años"',
        '"abogado extranjería" {ciudad} "2024" OR "2025" contacto -blog -noticia',
    ],
    
    "actualidad": [
        '"abogado extranjería" {ciudad} "nuevo despacho" OR "apertura" 2024 2025',
        '"abogado extranjería" {ciudad} "ahora" OR "actualmente" contacto',
    ],
}


# =============================================================================
# CAPA 2: URLs de directorios para scraping directo (Firecrawl)
# =============================================================================

URLS_DIRECTORIOS = {
    "generales": [
        "https://www.abogados.portaley.com/extranjeria/",
        "https://www.easyoffer.es/abogados/extranjeria/",
        "https://www.tusabogadosyasesores.com/abogados/extranjeria/",
        "https://www.paginasamarillas.es/search/abogados-extranjeria/",
        "https://www.qdq.com/abogados-extranjeria/",
    ],
    
    "madrid": [
        "https://www.abogados.portaley.com/extranjeria/madrid/",
        "https://www.easyoffer.es/abogados/extranjeria/madrid",
        "https://www.paginasamarillas.es/search/abogados-extranjeria/madrid/",
        "https://www.qdq.com/abogados-extranjeria/madrid/",
    ],
    
    "colegios": [
        "https://web.icam.es/buscador-abogados/",  # Madrid
        "https://www.icab.cat/es/servicios/buscador-de-profesionales/",  # Barcelona
        "https://www.icav.es/ver/1/guia-profesional",  # Valencia
    ],
    
    "ongs": [
        "https://www.cear.es/donde-estamos/",
        "https://www.accem.es/sedes/",
        "https://www2.cruzroja.es/buscador-centros",
        "https://www.caritas.es/donde-estamos/",
    ],
    
    "barcelona": [
        "https://www.abogados.portaley.com/extranjeria/barcelona/",
        "https://www.paginasamarillas.es/search/abogados-extranjeria/barcelona/",
    ],
    
    "valencia": [
        "https://www.abogados.portaley.com/extranjeria/valencia/",
        "https://www.paginasamarillas.es/search/abogados-extranjeria/valencia/",
    ],
}


# =============================================================================
# CAPA 3: Queries para Google Places API
# =============================================================================

QUERIES_PLACES = {
    "madrid": [
        {
            "query": "abogado extranjería",
            "location": (40.4168, -3.7038),  # Centro
            "radius": 5000,
        },
        {
            "query": "despacho inmigración",
            "location": (40.3850, -3.7125),  # Sur
            "radius": 8000,
        },
        {
            "query": "abogado nacionalidad española",
            "location": (40.4500, -3.6900),  # Norte
            "radius": 10000,
        },
        {
            "query": "abogado arraigo",
            "location": (40.4000, -3.7300),  # Oeste
            "radius": 7000,
        },
    ],
    
    "barcelona": [
        {
            "query": "abogado extranjería",
            "location": (41.3851, 2.1734),
            "radius": 8000,
        },
        {
            "query": "abogado inmigración",
            "location": (41.4036, 2.1744),  # Norte
            "radius": 10000,
        },
    ],
    
    "valencia": [
        {
            "query": "abogado extranjería",
            "location": (39.4699, -0.3763),
            "radius": 8000,
        },
    ],
}


# =============================================================================
# Funciones auxiliares
# =============================================================================

def get_prompts_ciudad(ciudad: str) -> list:
    """Obtiene todos los prompts para una ciudad."""
    ciudad_lower = ciudad.lower()
    prompts = []
    
    for key, value in PROMPTS_BUSQUEDA.items():
        if ciudad_lower in key:
            prompts.extend(value)
    
    return prompts


def get_urls_ciudad(ciudad: str) -> list:
    """Obtiene URLs de directorios para una ciudad."""
    ciudad_lower = ciudad.lower()
    urls = URLS_DIRECTORIOS.get("generales", []).copy()
    urls.extend(URLS_DIRECTORIOS.get(ciudad_lower, []))
    return urls


def generar_prompt_zona(ciudad: str, zona: str, especialidad: str = "") -> str:
    """Genera un prompt personalizado para zona específica."""
    partes = [f'"abogado extranjería"', ciudad]
    
    if zona:
        partes.append(f'"{zona}"')
    if especialidad:
        partes.append(f'"{especialidad}"')
    
    partes.append("teléfono OR email OR contacto")
    partes.append("-foro -pregunta -yahoo")
    
    return " ".join(partes)


def generar_prompt_especialidad(ciudad: str, especialidad: str) -> str:
    """Genera prompt para buscar especialista específico."""
    especialidades_keywords = {
        "arraigo": '"arraigo social" OR "arraigo laboral" OR "arraigo familiar"',
        "asilo": '"asilo" OR "protección internacional" OR "refugiado"',
        "nacionalidad": '"nacionalidad española" OR "ciudadanía"',
        "reagrupacion": '"reagrupación familiar"',
        "visados": '"visado" OR "visa"',
        "permisos": '"permiso trabajo" OR "autorización residencia"',
        "expulsiones": '"recurso expulsión" OR "anulación expulsión"',
        "recursos": '"recurso denegación" OR "recurso contencioso"',
    }
    
    keyword = especialidades_keywords.get(especialidad.lower(), f'"{especialidad}"')
    return f'{keyword} abogado {ciudad} teléfono contacto -foro'
