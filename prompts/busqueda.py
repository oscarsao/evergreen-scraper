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
    # BARCELONA - Búsquedas exhaustivas
    # -------------------------------------------------------------------------
    "barcelona_centro": [
        '"despacho de abogados" extranjería Barcelona "contacte" OR "llámenos" teléfono',
        '"bufete" inmigración Barcelona "nuestro equipo" OR "sobre nosotros" -directorio',
        '"abogados especialistas" extranjería Barcelona "@" email -listado',
        'abogado extranjería Barcelona "C/" OR "Carrer" "piso" teléfono -ranking',
        '"consulta" extranjería Barcelona "93" OR "6" teléfono despacho -gratis',
    ],
    
    "barcelona_eixample": [
        '"abogado extranjería" Barcelona Eixample "despacho" contacto -directorio',
        'bufete inmigración "Passeig de Gràcia" OR "Rambla Catalunya" teléfono',
        '"abogados" arraigo Barcelona Eixample "cita previa" -listado',
        'despacho nacionalidad Barcelona "Diagonal" email -foro',
    ],
    
    "barcelona_norte": [
        '"abogado extranjería" "Sant Andreu" OR "Nou Barris" Barcelona teléfono',
        'bufete inmigración "Horta" OR "Guinardó" Barcelona contacto -directorio',
        '"abogados" extranjería "Sant Martí" Barcelona "cita" -ranking',
        'despacho arraigo "Poblenou" Barcelona email -foro',
    ],
    
    "barcelona_sur": [
        '"abogado extranjería" "Sants" OR "Montjuïc" Barcelona teléfono -directorio',
        'bufete inmigración "Les Corts" OR "Sarrià" Barcelona contacto',
        '"abogados" extranjería "Ciutat Vella" OR "Raval" Barcelona -listado',
        'despacho nacionalidad "Barceloneta" OR "Gòtic" Barcelona -foro',
    ],
    
    "barcelona_metro": [
        '"abogado extranjería" "L\'Hospitalet" OR "Hospitalet de Llobregat" teléfono',
        'bufete inmigración Badalona OR "Santa Coloma de Gramenet" contacto',
        '"abogados" extranjería "Sant Cugat" OR Cerdanyola despacho -directorio',
        'despacho arraigo Sabadell OR Terrassa Barcelona email -listado',
        '"abogado" nacionalidad Mataró OR Granollers teléfono -foro',
        'bufete extranjería "Cornellà" OR "Esplugues" contacto -ranking',
    ],
    
    "barcelona_especialidades": [
        '"arraigo social" abogado Barcelona "nuestro despacho" teléfono -foro',
        '"arraigo laboral" especialista Barcelona "consulta" contacto',
        '"nacionalidad española" abogado Barcelona "tramitamos" -directorio',
        '"reagrupación familiar" bufete Barcelona teléfono -listado',
        '"permiso residencia" abogado Barcelona despacho "cita" -gratis',
        '"recurso expulsión" abogado Barcelona "experiencia" contacto',
        '"Golden Visa" OR "visa inversor" abogado Barcelona email',
    ],
    
    # -------------------------------------------------------------------------
    # VALENCIA - Búsquedas exhaustivas
    # -------------------------------------------------------------------------
    "valencia_centro": [
        '"despacho de abogados" extranjería Valencia "contacte" OR "llámenos" teléfono',
        '"bufete" inmigración Valencia "nuestro equipo" -directorio -listado',
        '"abogados especialistas" extranjería Valencia "@" email',
        'abogado extranjería Valencia "C/" OR "Calle" teléfono -ranking',
        '"consulta" extranjería Valencia "96" teléfono despacho -gratis',
    ],
    
    "valencia_centro_historico": [
        '"abogado extranjería" Valencia "Ciutat Vella" OR Centro teléfono -directorio',
        'bufete inmigración "L\'Eixample" OR Eixample Valencia contacto',
        '"abogados" arraigo "Extramurs" OR "La Saïdia" Valencia -listado',
        'despacho nacionalidad "Ruzafa" OR "Russafa" Valencia email -foro',
    ],
    
    "valencia_norte": [
        '"abogado extranjería" "Benimaclet" OR "Alboraya" Valencia teléfono',
        'bufete inmigración "Campanar" OR "Benicalap" Valencia contacto -directorio',
        '"abogados" extranjería "Poblats Marítims" Valencia "cita" -ranking',
    ],
    
    "valencia_sur": [
        '"abogado extranjería" "Patraix" OR "Jesús" Valencia teléfono -directorio',
        'bufete inmigración "Quatre Carreres" Valencia contacto',
        '"abogados" extranjería Torrent OR Aldaia despacho -listado',
        'despacho arraigo "Mislata" OR "Quart de Poblet" Valencia -foro',
    ],
    
    "valencia_metro": [
        '"abogado extranjería" Torrent OR Paterna teléfono contacto',
        'bufete inmigración "Burjassot" OR "Mislata" despacho -directorio',
        '"abogados" extranjería Sagunto OR "Puerto de Sagunto" -listado',
        'despacho arraigo Gandía OR Xàtiva Valencia email -foro',
        '"abogado" nacionalidad Alzira OR Ontinyent teléfono -ranking',
    ],
    
    "valencia_especialidades": [
        '"arraigo social" abogado Valencia "nuestro despacho" teléfono -foro',
        '"arraigo laboral" especialista Valencia "consulta" contacto',
        '"nacionalidad española" abogado Valencia "tramitamos" -directorio',
        '"reagrupación familiar" bufete Valencia teléfono -listado',
        '"permiso residencia" abogado Valencia despacho "cita" -gratis',
        '"recurso expulsión" abogado Valencia "experiencia" contacto',
    ],
    
    # -------------------------------------------------------------------------
    # SEVILLA - Búsquedas exhaustivas
    # -------------------------------------------------------------------------
    "sevilla_centro": [
        '"despacho de abogados" extranjería Sevilla "contacte" OR "llámenos" teléfono',
        '"bufete" inmigración Sevilla "nuestro equipo" -directorio -listado',
        '"abogados especialistas" extranjería Sevilla "@" email',
        'abogado extranjería Sevilla "C/" OR "Calle" teléfono -ranking',
        '"consulta" extranjería Sevilla "95" teléfono despacho -gratis',
    ],
    
    "sevilla_distritos": [
        '"abogado extranjería" Sevilla "Triana" OR "Nervión" teléfono -directorio',
        'bufete inmigración "Macarena" OR "San Pablo" Sevilla contacto',
        '"abogados" arraigo "Los Remedios" OR "Santa Cruz" Sevilla -listado',
        'despacho nacionalidad "Casco Antiguo" Sevilla email -foro',
        '"abogado" extranjería "Cerro Amate" OR "Este" Sevilla teléfono',
    ],
    
    "sevilla_metro": [
        '"abogado extranjería" "Dos Hermanas" OR "Alcalá de Guadaíra" teléfono',
        'bufete inmigración "Utrera" OR "Mairena del Aljarafe" contacto -directorio',
        '"abogados" extranjería "San Juan de Aznalfarache" despacho -listado',
        'despacho arraigo "Camas" OR "Gelves" Sevilla -foro',
        '"abogado" nacionalidad "La Rinconada" OR Bormujos teléfono',
    ],
    
    "sevilla_especialidades": [
        '"arraigo social" abogado Sevilla "nuestro despacho" teléfono -foro',
        '"nacionalidad española" abogado Sevilla "tramitamos" -directorio',
        '"reagrupación familiar" bufete Sevilla teléfono -listado',
        '"permiso residencia" abogado Sevilla despacho "cita" -gratis',
    ],
    
    # -------------------------------------------------------------------------
    # MÁLAGA - Búsquedas exhaustivas (incluye Costa del Sol)
    # -------------------------------------------------------------------------
    "malaga_centro": [
        '"despacho de abogados" extranjería Málaga "contacte" OR "llámenos" teléfono',
        '"bufete" inmigración Málaga "nuestro equipo" -directorio -listado',
        '"abogados especialistas" extranjería Málaga "@" email',
        'abogado extranjería Málaga "C/" OR "Calle" teléfono -ranking',
        '"consulta" extranjería Málaga "95" teléfono despacho -gratis',
    ],
    
    "malaga_distritos": [
        '"abogado extranjería" Málaga Centro OR "Centro Histórico" teléfono -directorio',
        'bufete inmigración "Teatinos" OR "Puerto de la Torre" Málaga contacto',
        '"abogados" arraigo "Carretera de Cádiz" OR "Cruz de Humilladero" -listado',
        'despacho nacionalidad "El Palo" OR "Pedregalejo" Málaga email -foro',
    ],
    
    "malaga_costa_sol": [
        '"abogado extranjería" Marbella teléfono despacho contacto -directorio',
        '"Golden Visa" abogado Marbella OR "Puerto Banús" email',
        'bufete inmigración Fuengirola OR "Benalmádena" teléfono -listado',
        '"abogados" extranjería Torremolinos OR Mijas contacto -ranking',
        'despacho arraigo Estepona OR "San Pedro Alcántara" -foro',
        '"abogado" nacionalidad "Rincón de la Victoria" OR Nerja teléfono',
        '"inversores extranjeros" abogado "Costa del Sol" email',
    ],
    
    "malaga_especialidades": [
        '"arraigo social" abogado Málaga "nuestro despacho" teléfono -foro',
        '"Golden Visa" especialista Málaga "inversión inmobiliaria"',
        '"nacionalidad española" abogado Málaga "tramitamos" -directorio',
        '"permiso residencia" abogado "Costa del Sol" despacho "cita"',
    ],
    
    # -------------------------------------------------------------------------
    # ZARAGOZA
    # -------------------------------------------------------------------------
    "zaragoza_centro": [
        '"despacho de abogados" extranjería Zaragoza "contacte" teléfono',
        '"bufete" inmigración Zaragoza "nuestro equipo" -directorio',
        'abogado extranjería Zaragoza "C/" teléfono -ranking -listado',
        '"consulta" extranjería Zaragoza "976" teléfono despacho',
    ],
    
    "zaragoza_distritos": [
        '"abogado extranjería" "Delicias" OR "Casco Histórico" Zaragoza teléfono',
        'bufete inmigración "Actur" OR "Universidad" Zaragoza contacto -directorio',
        '"abogados" arraigo "San José" OR "Las Fuentes" Zaragoza -listado',
        'despacho nacionalidad "Torrero" OR "La Paz" Zaragoza email',
    ],
    
    "zaragoza_especialidades": [
        '"arraigo social" abogado Zaragoza teléfono -foro',
        '"nacionalidad española" abogado Zaragoza "tramitamos" -directorio',
        '"reagrupación familiar" bufete Zaragoza teléfono -listado',
    ],
    
    # -------------------------------------------------------------------------
    # MURCIA
    # -------------------------------------------------------------------------
    "murcia_centro": [
        '"despacho de abogados" extranjería Murcia "contacte" teléfono',
        '"bufete" inmigración Murcia "nuestro equipo" -directorio',
        'abogado extranjería Murcia ciudad teléfono -ranking -listado',
        '"consulta" extranjería Murcia "968" teléfono despacho',
    ],
    
    "murcia_region": [
        '"abogado extranjería" Cartagena teléfono despacho -directorio',
        'bufete inmigración Lorca OR "Molina de Segura" contacto',
        '"abogados" extranjería "Alcantarilla" OR Cieza despacho -listado',
        'despacho arraigo "Torre Pacheco" OR "San Javier" -foro',
    ],
    
    # -------------------------------------------------------------------------
    # PALMA DE MALLORCA
    # -------------------------------------------------------------------------
    "palma_centro": [
        '"despacho de abogados" extranjería Palma Mallorca teléfono',
        '"bufete" inmigración "Palma de Mallorca" -directorio',
        'abogado extranjería Baleares "C/" teléfono -ranking -listado',
        '"consulta" extranjería Mallorca "971" teléfono despacho',
    ],
    
    "palma_isla": [
        '"abogado extranjería" Ibiza OR Eivissa teléfono despacho',
        'bufete inmigración Menorca OR "Mahón" contacto -directorio',
        '"abogados" extranjería "Calvià" OR "Llucmajor" Mallorca -listado',
        '"Golden Visa" abogado Mallorca OR Ibiza inversión email',
    ],
    
    # -------------------------------------------------------------------------
    # ALICANTE
    # -------------------------------------------------------------------------
    "alicante_centro": [
        '"despacho de abogados" extranjería Alicante "contacte" teléfono',
        '"bufete" inmigración Alicante "nuestro equipo" -directorio',
        'abogado extranjería Alicante "C/" teléfono -ranking -listado',
        '"consulta" extranjería Alicante "96" teléfono despacho',
    ],
    
    "alicante_costa": [
        '"abogado extranjería" Benidorm teléfono despacho -directorio',
        'bufete inmigración Elche OR "Elx" contacto -listado',
        '"abogados" extranjería Torrevieja OR "Orihuela Costa" -ranking',
        'despacho arraigo "Santa Pola" OR "Guardamar" -foro',
        '"Golden Visa" abogado "Costa Blanca" inversión email',
    ],
    
    # -------------------------------------------------------------------------
    # BILBAO / PAÍS VASCO
    # -------------------------------------------------------------------------
    "bilbao_centro": [
        '"despacho de abogados" extranjería Bilbao teléfono',
        '"bufete" inmigración Bilbao "nuestro equipo" -directorio',
        'abogado extranjería "País Vasco" Bizkaia teléfono -ranking',
        '"consulta" extranjería Bilbao "94" teléfono despacho',
    ],
    
    "pais_vasco": [
        '"abogado extranjería" "San Sebastián" OR Donostia teléfono',
        'bufete inmigración Vitoria OR "Vitoria-Gasteiz" contacto -directorio',
        '"abogados" extranjería Barakaldo OR Getxo despacho -listado',
        'despacho arraigo Irún OR Eibar "País Vasco" -foro',
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
        {"query": "abogado extranjería", "location": (40.4168, -3.7038), "radius": 5000},
        {"query": "despacho inmigración", "location": (40.3850, -3.7125), "radius": 8000},
        {"query": "abogado nacionalidad española", "location": (40.4500, -3.6900), "radius": 10000},
        {"query": "abogado arraigo", "location": (40.4000, -3.7300), "radius": 7000},
    ],
    "barcelona": [
        {"query": "abogado extranjería", "location": (41.3851, 2.1734), "radius": 6000},
        {"query": "despacho inmigración", "location": (41.4036, 2.1744), "radius": 8000},
        {"query": "abogado arraigo", "location": (41.3700, 2.1500), "radius": 7000},
        {"query": "abogado nacionalidad", "location": (41.4100, 2.2000), "radius": 10000},
    ],
    "valencia": [
        {"query": "abogado extranjería", "location": (39.4699, -0.3763), "radius": 6000},
        {"query": "despacho inmigración", "location": (39.4800, -0.3600), "radius": 8000},
        {"query": "abogado arraigo", "location": (39.4500, -0.4000), "radius": 7000},
    ],
    "sevilla": [
        {"query": "abogado extranjería", "location": (37.3891, -5.9845), "radius": 6000},
        {"query": "despacho inmigración", "location": (37.4000, -6.0000), "radius": 8000},
    ],
    "malaga": [
        {"query": "abogado extranjería", "location": (36.7213, -4.4214), "radius": 6000},
        {"query": "abogado Golden Visa", "location": (36.5100, -4.8900), "radius": 15000},  # Marbella
    ],
    "zaragoza": [
        {"query": "abogado extranjería", "location": (41.6488, -0.8891), "radius": 8000},
    ],
    "murcia": [
        {"query": "abogado extranjería", "location": (37.9922, -1.1307), "radius": 8000},
    ],
    "palma": [
        {"query": "abogado extranjería", "location": (39.5696, 2.6502), "radius": 10000},
    ],
    "alicante": [
        {"query": "abogado extranjería", "location": (38.3452, -0.4810), "radius": 8000},
        {"query": "abogado inmigración", "location": (38.5411, -0.1225), "radius": 15000},  # Benidorm
    ],
    "bilbao": [
        {"query": "abogado extranjería", "location": (43.2630, -2.9350), "radius": 8000},
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
