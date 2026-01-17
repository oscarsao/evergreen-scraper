"""
Prompts de búsqueda optimizados para encontrar DESPACHOS Y ABOGADOS REALES.
Estrategia: Buscar páginas web propias con datos de contacto.

IMPORTANTE: Excluir siempre directorios, listados, blogs y artículos.
"""

# Exclusiones globales para añadir a cada búsqueda
EXCLUSIONES = "-directorio -listado -ranking -mejores -top -comparativa -blog -articulo -noticia -foro -pregunta -yahoo -quora"

# =============================================================================
# CAPA 1: Prompts para búsqueda web (Google/Tavily/Serper)
# Enfocados en encontrar WEBS PROPIAS de despachos, no listados
# =============================================================================

PROMPTS_BUSQUEDA = {
    # -------------------------------------------------------------------------
    # MADRID - Búsquedas específicas de despachos
    # -------------------------------------------------------------------------
    "madrid_centro": [
        # Buscar webs propias con datos de contacto específicos
        '"despacho de abogados" extranjería Madrid "llámenos" OR "contacte" OR "cita previa"',
        '"bufete" inmigración Madrid "nuestro equipo" OR "sobre nosotros" teléfono',
        '"abogados especialistas" extranjería Madrid "@" email',
        'abogado extranjería Madrid "C/" OR "Calle" "piso" teléfono -directorio -listado',
        '"consulta" extranjería Madrid "91" OR "6" teléfono despacho -gratis -gratuita',
    ],
    
    "madrid_sur": [
        '"abogado extranjería" Carabanchel "teléfono" OR "contacto" despacho -directorio',
        '"despacho" inmigración Usera OR Villaverde "cita" -listado -ranking',
        'bufete abogados extranjería Vallecas "llame" OR "escriba" -foro',
        '"abogado" arraigo Leganés OR Getafe "consulta" teléfono -gratis',
        'despacho extranjería Móstoles OR Fuenlabrada "dirección" contacto',
        '"abogados" inmigración Parla OR Alcorcón "equipo" OR "profesionales"',
    ],
    
    "madrid_norte": [
        '"abogado extranjería" Tetuán OR Chamartín "despacho" contacto -directorio',
        'bufete inmigración Alcobendas OR "Tres Cantos" teléfono -listado',
        '"abogados" extranjería "San Sebastián de los Reyes" "cita" -ranking',
        'despacho arraigo Pozuelo OR "Las Rozas" "consulta" email',
        '"abogado" nacionalidad Majadahonda "contacte" -foro -pregunta',
    ],
    
    "madrid_este": [
        '"abogado extranjería" "Ciudad Lineal" despacho "teléfono" -directorio',
        'bufete inmigración "San Blas" OR Vicálvaro "contacto" -listado',
        '"abogados" extranjería Coslada OR "San Fernando" "cita previa"',
        'despacho arraigo Torrejón OR "Alcalá de Henares" email -ranking',
        '"abogado" permisos Rivas OR Arganda "llámenos" -foro',
    ],
    
    # -------------------------------------------------------------------------
    # MADRID - Búsquedas por especialidad (webs propias)
    # -------------------------------------------------------------------------
    "madrid_especialidades": [
        # Arraigo (alta demanda)
        '"arraigo social" abogado Madrid "nuestro despacho" OR "le ayudamos" teléfono',
        '"arraigo laboral" especialista Madrid "consulta" contacto -foro',
        '"arraigo familiar" abogado Madrid "experiencia" "casos" -directorio',
        
        # Nacionalidad
        '"nacionalidad española" abogado Madrid "tramitamos" OR "gestionamos" -listado',
        '"expediente nacionalidad" bufete Madrid teléfono -ranking',
        
        # Permisos y visados
        '"permiso residencia" abogado Madrid despacho "cita" -gratis',
        '"reagrupación familiar" especialista Madrid "contacte" -foro',
        '"Golden Visa" OR "visa inversor" abogado Madrid "asesoramiento" email',
        
        # Recursos y defensa
        '"recurso expulsión" abogado Madrid "defendemos" OR "experiencia" teléfono',
        '"recurso denegación" extranjería Madrid despacho contacto',
        'abogado "protección internacional" asilo Madrid "equipo" -ong',
    ],
    
    "madrid_nombres": [
        # Buscar por estructura de nombre de despacho
        '"& Asociados" abogados extranjería Madrid contacto',
        '"Abogados S.L." extranjería Madrid teléfono',
        '"Bufete" extranjería Madrid "sobre nosotros" -directorio',
        '"Despacho" abogados inmigración Madrid "equipo" email',
        '"Law" OR "Legal" extranjería Madrid "contact" -ranking',
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
