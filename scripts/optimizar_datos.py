"""
Script de Optimización de Datos
================================
- Normaliza nombres usando dominio como referencia
- Agrupa registros por dominio web (misma web = mismo despacho)
- Fusiona registros de diferentes ciudades con mismo dominio
- Mejora estructura de datos para soportar múltiples ciudades
"""
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict


def extraer_dominio(url: str) -> str:
    """Extrae dominio limpio de URL."""
    if not url:
        return ""
    url = url.lower().replace("https://", "").replace("http://", "").replace("www.", "")
    return url.split("/")[0].split("?")[0].strip()


def normalizar_telefono(tel: str) -> str:
    """Normaliza teléfono para comparación."""
    if not tel:
        return ""
    limpio = re.sub(r'[^\d]', '', tel)
    if len(limpio) >= 9:
        return limpio[-9:]
    return limpio


def extraer_nombre_desde_dominio(dominio: str) -> str:
    """
    Extrae un nombre razonable desde el dominio.
    Ejemplo: 'abogadosextranjeriamadrid.com' -> 'Abogados Extranjería Madrid'
    """
    if not dominio:
        return ""
    
    # Quitar extensiones
    nombre = dominio.split('.')[0]
    
    # Reemplazar guiones y underscores por espacios
    nombre = nombre.replace('-', ' ').replace('_', ' ')
    
    # Capitalizar palabras
    palabras = nombre.split()
    nombre_capitalizado = ' '.join(p.capitalize() for p in palabras)
    
    # Correcciones comunes
    nombre_capitalizado = re.sub(r'\bAbogado\b', 'Abogados', nombre_capitalizado, flags=re.IGNORECASE)
    nombre_capitalizado = re.sub(r'\bExtranjeria\b', 'Extranjería', nombre_capitalizado, flags=re.IGNORECASE)
    
    return nombre_capitalizado


def limpiar_nombre_actual(nombre: str, dominio: str) -> Tuple[str, str]:
    """
    Limpia nombre actual y extrae descripción.
    Returns: (nombre_limpio, descripcion)
    """
    if not nombre:
        return extraer_nombre_desde_dominio(dominio), ""
    
    nombre_orig = nombre
    descripcion = ""
    
    # Separadores comunes
    separadores = [' - ', ' | ', ' – ', ' — ', ' · ', ' • ', ':', ' (', ' [', ' - ']
    
    for sep in separadores:
        if sep in nombre:
            partes = nombre.split(sep, 1)
            nombre = partes[0].strip()
            if len(partes) > 1 and len(partes[1]) > 5:
                desc = partes[1].strip()
                # Quitar paréntesis de cierre
                desc = desc.rstrip(')').rstrip(']')
                if len(desc) > 5 and desc not in ['Madrid', 'Barcelona', 'Valencia', 'España']:
                    descripcion = desc
            break
    
    # Limpiar sufijos
    sufijos = [
        r'\s*[-|]\s*(Abogados?|Despacho|Bufete|Madrid|Barcelona|Valencia|España).*$',
        r'\s*\(.*\)\s*$',
        r'\.{3,}$',
    ]
    
    for patron in sufijos:
        nombre = re.sub(patron, '', nombre, flags=re.IGNORECASE)
    
    nombre = nombre.strip()
    
    # Si el nombre es muy genérico, usar dominio
    if len(nombre) < 3 or nombre.lower() in ['contacto', 'inicio', 'home', 'about']:
        nombre = extraer_nombre_desde_dominio(dominio)
    
    return nombre, descripcion


def fusionar_registros(registros: List[Dict]) -> Dict:
    """
    Fusiona múltiples registros del mismo despacho (mismo dominio).
    Agrupa ciudades, teléfonos, direcciones, etc.
    """
    if not registros:
        return {}
    
    # Seleccionar registro base (el más completo)
    registro_base = max(registros, key=lambda r: sum([
        bool(r.get("telefono")),
        bool(r.get("email")),
        bool(r.get("direccion")),
        len(r.get("especialidades", []))
    ]))
    
    fusionado = registro_base.copy()
    
    # Agrupar ciudades (nueva estructura: ciudades como lista)
    ciudades = set()
    direcciones = []
    distritos = set()
    
    for r in registros:
        if r.get("ciudad"):
            ciudades.add(r.get("ciudad"))
        if r.get("direccion"):
            dir_actual = r.get("direccion")
            if dir_actual not in direcciones:
                direcciones.append(dir_actual)
        if r.get("distrito"):
            distritos.add(r.get("distrito"))
    
    # Nueva estructura: ciudades como lista
    fusionado["ciudades"] = sorted(list(ciudades)) if ciudades else [registro_base.get("ciudad")] if registro_base.get("ciudad") else []
    fusionado["ciudad"] = fusionado["ciudades"][0] if fusionado["ciudades"] else None  # Mantener para compatibilidad
    fusionado["direcciones"] = direcciones if len(direcciones) > 1 else [direcciones[0]] if direcciones else []
    if fusionado["direcciones"] and not fusionado.get("direccion"):
        fusionado["direccion"] = fusionado["direcciones"][0]
    if distritos:
        fusionado["distritos"] = sorted(list(distritos))
    
    # Combinar teléfonos (sin duplicados)
    todos_tels = set()
    for r in registros:
        tels = r.get("telefono", [])
        if isinstance(tels, str):
            tels = [tels]
        for tel in tels:
            if tel:
                tel_norm = normalizar_telefono(tel)
                if tel_norm:
                    # Mantener formato original más legible
                    todos_tels.add(tel)
    
    fusionado["telefono"] = sorted(list(todos_tels), key=lambda x: (len(x), x))
    
    # Combinar especialidades
    todas_esp = set()
    for r in registros:
        esp = r.get("especialidades", [])
        if isinstance(esp, list):
            todas_esp.update(esp)
    fusionado["especialidades"] = sorted(list(todas_esp))
    
    # Combinar idiomas
    todos_idiomas = set()
    for r in registros:
        idiomas = r.get("idiomas", [])
        if isinstance(idiomas, list):
            todos_idiomas.update(idiomas)
    if todos_idiomas:
        fusionado["idiomas"] = sorted(list(todos_idiomas))
    
    # Mejor email (el del dominio si existe)
    dominio = extraer_dominio(fusionado.get("web", ""))
    if dominio:
        for r in registros:
            email = r.get("email", "")
            if email and dominio in email.lower():
                fusionado["email"] = email
                break
    
    # Mejor nombre basado en dominio
    nombre_limpio, descripcion = limpiar_nombre_actual(fusionado.get("nombre", ""), dominio)
    fusionado["nombre"] = nombre_limpio
    if descripcion:
        fusionado["descripcion"] = descripcion
    
    # Fecha de actualización más reciente
    fechas = [r.get("fecha_actualizacion") for r in registros if r.get("fecha_actualizacion")]
    if fechas:
        fusionado["fecha_actualizacion"] = max(fechas)
    else:
        fusionado["fecha_actualizacion"] = datetime.now().isoformat()
    
    # Metadatos
    fusionado["_ciudades_originales"] = sorted(list(ciudades))
    fusionado["_registros_fusionados"] = len(registros)
    
    return fusionado


def cargar_todos_registros() -> List[Dict]:
    """Carga todos los registros de todas las ciudades."""
    data_dir = Path("data")
    todos = []
    
    for archivo in sorted(data_dir.glob("*.json")):
        if "config" in archivo.name or "api_usage" in archivo.name or "historial" in archivo.name:
            continue
        
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            ciudad = archivo.stem.title()
            for r in data.get("registros", []):
                r["_ciudad_origen"] = ciudad
                r["_archivo_origen"] = archivo.name
                todos.append(r)
        except Exception as e:
            print(f"Error cargando {archivo}: {e}")
    
    return todos


def optimizar_datos(dry_run: bool = False) -> Dict:
    """
    Optimiza todos los datos agrupando por dominio web.
    
    Returns:
        Estadísticas de optimización
    """
    print("=" * 60)
    print("OPTIMIZACIÓN DE DATOS")
    print("=" * 60)
    
    # Cargar todos los registros
    print("\n[1] Cargando registros...")
    todos_registros = cargar_todos_registros()
    print(f"    Total cargados: {len(todos_registros)} registros")
    
    # Agrupar por dominio web
    print("\n[2] Agrupando por dominio web...")
    grupos_por_dominio = defaultdict(list)
    
    for r in todos_registros:
        web = r.get("web", "")
        dominio = extraer_dominio(web)
        if dominio:
            grupos_por_dominio[dominio].append(r)
        else:
            # Sin web, mantener como grupo individual
            grupos_por_dominio[f"_sin_web_{id(r)}"].append(r)
    
    print(f"    Grupos encontrados: {len(grupos_por_dominio)}")
    
    # Identificar grupos con múltiples registros
    grupos_multiples = {k: v for k, v in grupos_por_dominio.items() if len(v) > 1}
    grupos_simples = {k: v for k, v in grupos_por_dominio.items() if len(v) == 1}
    
    print(f"    - Con múltiples registros: {len(grupos_multiples)}")
    print(f"    - Únicos: {len(grupos_simples)}")
    
    # Fusionar registros en cada grupo
    print("\n[3] Fusionando registros por dominio...")
    registros_optimizados = []
    
    registros_fusionados = 0
    registros_eliminados = 0
    
    for dominio, registros_grupo in grupos_por_dominio.items():
        if len(registros_grupo) > 1:
            fusionado = fusionar_registros(registros_grupo)
            registros_optimizados.append(fusionado)
            registros_eliminados += len(registros_grupo) - 1
            registros_fusionados += len(registros_grupo)
        else:
            # Un solo registro, normalizar nombre
            r = registros_grupo[0]
            dominio_r = extraer_dominio(r.get("web", ""))
            if dominio_r:
                nombre_limpio, desc = limpiar_nombre_actual(r.get("nombre", ""), dominio_r)
                r["nombre"] = nombre_limpio
                if desc:
                    r["descripcion"] = desc
                # Convertir ciudad a lista para consistencia
                if r.get("ciudad") and "ciudades" not in r:
                    r["ciudades"] = [r["ciudad"]]
            registros_optimizados.append(r)
    
    print(f"    Registros fusionados: {registros_fusionados}")
    print(f"    Registros eliminados: {registros_eliminados}")
    print(f"    Registros finales: {len(registros_optimizados)}")
    
    # Estadísticas
    stats = {
        "total_original": len(todos_registros),
        "total_optimizado": len(registros_optimizados),
        "reduccion": len(todos_registros) - len(registros_optimizados),
        "grupos_fusionados": len(grupos_multiples),
        "registros_con_multiple_ciudad": sum(1 for r in registros_optimizados if len(r.get("ciudades", [])) > 1)
    }
    
    print("\n[4] Estadísticas:")
    print(f"    Total original: {stats['total_original']}")
    print(f"    Total optimizado: {stats['total_optimizado']}")
    print(f"    Reducción: {stats['reduccion']} registros (-{stats['reduccion']/stats['total_original']*100:.1f}%)")
    print(f"    Con múltiples ciudades: {stats['registros_con_multiple_ciudad']}")
    
    if dry_run:
        print("\n[DRY RUN] No se guardaron cambios")
        return stats
    
    # Guardar en archivo unificado
    print("\n[5] Guardando datos optimizados...")
    data_optimizada = {
        "metadata": {
            "fecha_optimizacion": datetime.now().isoformat(),
            "total_registros": len(registros_optimizados),
            "total_original": stats["total_original"],
            "reduccion": stats["reduccion"],
            "fuente": "optimizacion_por_dominio"
        },
        "registros": registros_optimizados
    }
    
    output_path = Path("data/registros_optimizados.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data_optimizada, f, ensure_ascii=False, indent=2)
    
    print(f"    Guardado en: {output_path}")
    
    # También crear backups de archivos originales
    print("\n[6] Creando backups de archivos originales...")
    backup_dir = Path("data/backup_pre_optimizacion")
    backup_dir.mkdir(exist_ok=True)
    
    for archivo in Path("data").glob("*.json"):
        if "config" not in archivo.name and "api_usage" not in archivo.name and "historial" not in archivo.name and "backup" not in str(archivo):
            backup_path = backup_dir / f"{archivo.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_path.write_bytes(archivo.read_bytes())
            print(f"    Backup: {archivo.name}")
    
    print("\n✓ Optimización completada")
    
    return stats


if __name__ == "__main__":
    import sys
    
    # Configurar encoding UTF-8 para Windows
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    
    if dry_run:
        print("\n[MODO DRY RUN] No se guardaran cambios\n")
    
    stats = optimizar_datos(dry_run=dry_run)
    
    if not dry_run:
        print("\n" + "=" * 60)
        print("PRÓXIMOS PASOS:")
        print("1. Revisar data/registros_optimizados.json")
        print("2. Si está bien, actualizar archivos por ciudad con nuevos registros")
        print("3. Actualizar UI para mostrar múltiples ciudades por registro")
        print("=" * 60)
