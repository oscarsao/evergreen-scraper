"""
Motor de consolidación y deduplicación de registros.
Detecta duplicados con 3 niveles de precisión y fusiona datos.
"""
import json
import hashlib
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime
from pathlib import Path

# Intentar importar rapidfuzz para similitud fuzzy
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_DISPONIBLE = True
except ImportError:
    RAPIDFUZZ_DISPONIBLE = False


@dataclass
class ConsolidacionResult:
    """Resultado de una operación de consolidación."""
    agregados: List[Dict] = field(default_factory=list)
    actualizados: List[Dict] = field(default_factory=list)
    duplicados_ignorados: List[Dict] = field(default_factory=list)
    invalidos: List[Dict] = field(default_factory=list)
    
    @property
    def total_procesados(self) -> int:
        return (len(self.agregados) + len(self.actualizados) + 
                len(self.duplicados_ignorados) + len(self.invalidos))
    
    @property
    def total_nuevos(self) -> int:
        return len(self.agregados)
    
    def to_dict(self) -> Dict:
        return {
            "agregados": len(self.agregados),
            "actualizados": len(self.actualizados),
            "duplicados_ignorados": len(self.duplicados_ignorados),
            "invalidos": len(self.invalidos),
            "total_procesados": self.total_procesados,
        }


class Consolidador:
    """
    Motor de consolidación con detección de duplicados multinivel.
    
    Niveles de detección:
    1. Hash exacto (nombre + teléfono principal + email)
    2. Teléfono normalizado
    3. Similitud fuzzy de nombre (>85%)
    """
    
    def __init__(self, base_datos_path: str = None):
        """
        Inicializa el consolidador.
        
        Args:
            base_datos_path: Ruta al archivo JSON de la base de datos
        """
        self.base_datos_path = Path(base_datos_path) if base_datos_path else None
        self.registros: List[Dict] = []
        self.indice_hash: Dict[str, int] = {}  # hash -> índice
        self.indice_telefono: Dict[str, Set[int]] = {}  # telefono -> índices
        self.indice_email: Dict[str, int] = {}  # email -> índice
        
        if self.base_datos_path and self.base_datos_path.exists():
            self._cargar_base_datos()
    
    def _cargar_base_datos(self):
        """Carga la base de datos y construye índices."""
        try:
            with open(self.base_datos_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self.registros = data.get("registros", [])
            self._construir_indices()
            print(f"[Consolidador] Cargados {len(self.registros)} registros")
            
        except Exception as e:
            print(f"[Consolidador] Error cargando base de datos: {e}")
            self.registros = []
    
    def _construir_indices(self):
        """Construye índices para búsqueda rápida."""
        self.indice_hash = {}
        self.indice_telefono = {}
        self.indice_email = {}
        
        for i, registro in enumerate(self.registros):
            # Índice por hash
            hash_registro = self.calcular_hash(registro)
            self.indice_hash[hash_registro] = i
            
            # Índice por teléfonos
            telefonos = registro.get("telefono", [])
            if isinstance(telefonos, str):
                telefonos = [telefonos]
            for tel in telefonos:
                tel_norm = self.normalizar_telefono(tel)
                if tel_norm:
                    if tel_norm not in self.indice_telefono:
                        self.indice_telefono[tel_norm] = set()
                    self.indice_telefono[tel_norm].add(i)
            
            # Índice por email
            email = registro.get("email") or ""
            if email:
                self.indice_email[email.lower()] = i
    
    def calcular_hash(self, registro: Dict) -> str:
        """
        Calcula hash único para un registro.
        Usa: nombre normalizado + primer teléfono + email
        """
        nombre = (registro.get("nombre") or "").lower().strip()
        
        telefonos = registro.get("telefono") or []
        if isinstance(telefonos, str):
            telefonos = [telefonos]
        telefono = self.normalizar_telefono(telefonos[0]) if telefonos else ""
        
        email = (registro.get("email") or "").lower().strip()
        
        # Crear string para hash
        hash_string = f"{nombre}|{telefono}|{email}"
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def normalizar_telefono(self, telefono: str) -> str:
        """Normaliza teléfono a solo dígitos con +34."""
        if not telefono:
            return ""
        
        # Solo dígitos y +
        limpio = "".join(c for c in telefono if c.isdigit() or c == "+")
        
        # Asegurar formato +34XXXXXXXXX
        if limpio.startswith("34") and not limpio.startswith("+"):
            limpio = "+" + limpio
        elif limpio and limpio[0] in "6789":
            limpio = "+34" + limpio
        
        return limpio
    
    def normalizar_nombre(self, nombre: str) -> str:
        """Normaliza nombre para comparación."""
        if not nombre:
            return ""
        
        nombre = nombre.lower().strip()
        
        # Eliminar sufijos comunes
        sufijos = [
            "abogados", "abogado", "despacho", "bufete",
            "& asociados", "y asociados", "asociados",
            "s.l.", "s.l.p.", "s.c.", "s.a.",
            "law", "lawyers", "legal",
        ]
        for sufijo in sufijos:
            nombre = re.sub(rf'\s*{re.escape(sufijo)}\.?\s*$', '', nombre, flags=re.IGNORECASE)
        
        # Eliminar caracteres especiales
        nombre = re.sub(r'[^\w\s]', '', nombre)
        nombre = re.sub(r'\s+', ' ', nombre).strip()
        
        return nombre
    
    def similitud_nombre(self, nombre1: str, nombre2: str) -> float:
        """
        Calcula similitud entre dos nombres (0-100).
        Usa rapidfuzz si está disponible, sino comparación simple.
        """
        n1 = self.normalizar_nombre(nombre1)
        n2 = self.normalizar_nombre(nombre2)
        
        if not n1 or not n2:
            return 0.0
        
        if n1 == n2:
            return 100.0
        
        if RAPIDFUZZ_DISPONIBLE:
            # Usar múltiples métricas y promediar
            ratio = fuzz.ratio(n1, n2)
            partial = fuzz.partial_ratio(n1, n2)
            token_sort = fuzz.token_sort_ratio(n1, n2)
            return max(ratio, partial, token_sort)
        else:
            # Comparación simple por palabras comunes
            palabras1 = set(n1.split())
            palabras2 = set(n2.split())
            if not palabras1 or not palabras2:
                return 0.0
            comunes = palabras1 & palabras2
            total = palabras1 | palabras2
            return (len(comunes) / len(total)) * 100
    
    def buscar_duplicado(self, registro: Dict) -> Tuple[bool, Optional[Dict], str]:
        """
        Busca si un registro ya existe en la base de datos.
        
        Returns:
            Tuple: (es_duplicado, registro_existente, metodo_deteccion)
        """
        # Nivel 1: Hash exacto
        hash_nuevo = self.calcular_hash(registro)
        if hash_nuevo in self.indice_hash:
            idx = self.indice_hash[hash_nuevo]
            return True, self.registros[idx], "hash_exacto"
        
        # Nivel 2: Teléfono
        telefonos = registro.get("telefono", [])
        if isinstance(telefonos, str):
            telefonos = [telefonos]
        
        for tel in telefonos:
            tel_norm = self.normalizar_telefono(tel)
            if tel_norm and tel_norm in self.indice_telefono:
                # Verificar que el nombre sea similar
                for idx in self.indice_telefono[tel_norm]:
                    existente = self.registros[idx]
                    similitud = self.similitud_nombre(
                        registro.get("nombre", ""),
                        existente.get("nombre", "")
                    )
                    if similitud > 60:  # Umbral bajo porque teléfono ya coincide
                        return True, existente, "telefono"
        
        # Nivel 3: Email exacto
        email = registro.get("email", "")
        if email:
            email_lower = email.lower()
            if email_lower in self.indice_email:
                idx = self.indice_email[email_lower]
                return True, self.registros[idx], "email"
        
        # Nivel 4: Similitud fuzzy de nombre (solo si no tiene contacto único)
        nombre_nuevo = registro.get("nombre", "")
        if nombre_nuevo:
            for existente in self.registros:
                similitud = self.similitud_nombre(nombre_nuevo, existente.get("nombre", ""))
                if similitud > 85:
                    # Verificar que tengan algún dato en común
                    if self._tienen_datos_comunes(registro, existente):
                        return True, existente, "nombre_similar"
        
        return False, None, ""
    
    def _tienen_datos_comunes(self, reg1: Dict, reg2: Dict) -> bool:
        """Verifica si dos registros tienen datos de contacto en común."""
        # Comparar teléfonos
        tels1 = set(self.normalizar_telefono(t) for t in reg1.get("telefono", []))
        tels2 = set(self.normalizar_telefono(t) for t in reg2.get("telefono", []))
        if tels1 & tels2:
            return True
        
        # Comparar email
        email1 = (reg1.get("email") or "").lower()
        email2 = (reg2.get("email") or "").lower()
        if email1 and email2 and email1 == email2:
            return True
        
        # Comparar web (dominio)
        web1 = reg1.get("web") or ""
        web2 = reg2.get("web") or ""
        if web1 and web2:
            dom1 = self._extraer_dominio(web1)
            dom2 = self._extraer_dominio(web2)
            if dom1 and dom2 and dom1 == dom2:
                return True
        
        return False
    
    def _extraer_dominio(self, url: str) -> str:
        """Extrae el dominio de una URL."""
        url = url.lower().replace("https://", "").replace("http://", "")
        url = url.replace("www.", "")
        return url.split("/")[0]
    
    def fusionar(self, existente: Dict, nuevo: Dict) -> Dict:
        """
        Fusiona dos registros, priorizando el existente.
        Añade datos nuevos que no existan.
        """
        fusionado = existente.copy()
        
        # Campos que se combinan (listas)
        for campo in ["telefono", "especialidades", "idiomas"]:
            valores_existentes = existente.get(campo, [])
            valores_nuevos = nuevo.get(campo, [])
            
            if isinstance(valores_existentes, str):
                valores_existentes = [valores_existentes]
            if isinstance(valores_nuevos, str):
                valores_nuevos = [valores_nuevos]
            
            # Normalizar teléfonos para comparación
            if campo == "telefono":
                existentes_norm = {self.normalizar_telefono(t): t for t in valores_existentes}
                for tel in valores_nuevos:
                    tel_norm = self.normalizar_telefono(tel)
                    if tel_norm and tel_norm not in existentes_norm:
                        valores_existentes.append(tel)
                fusionado[campo] = valores_existentes
            else:
                # Para otros campos, simplemente combinar únicos
                combinados = list(set(valores_existentes + valores_nuevos))
                fusionado[campo] = combinados
        
        # Campos que se completan si están vacíos
        for campo in ["email", "web", "direccion", "ciudad", "distrito", "horario"]:
            if not existente.get(campo) and nuevo.get(campo):
                fusionado[campo] = nuevo[campo]
        
        # Valoración: usar la más reciente o la que tenga valor
        if nuevo.get("valoracion") is not None:
            if existente.get("valoracion") is None:
                fusionado["valoracion"] = nuevo["valoracion"]
        
        # Actualizar fecha
        fusionado["fecha_actualizacion"] = datetime.now().isoformat()
        
        return fusionado
    
    def es_valido(self, registro: Dict) -> bool:
        """Verifica si un registro cumple los requisitos mínimos."""
        # Debe tener nombre
        if not registro.get("nombre"):
            return False
        
        # Debe tener al menos un método de contacto
        tiene_telefono = bool(registro.get("telefono"))
        tiene_email = bool(registro.get("email"))
        tiene_web = bool(registro.get("web"))
        
        return tiene_telefono or tiene_email or tiene_web
    
    def procesar_batch(self, nuevos: List[Dict]) -> ConsolidacionResult:
        """
        Procesa un lote de registros nuevos.
        
        Args:
            nuevos: Lista de registros a procesar
            
        Returns:
            ConsolidacionResult con estadísticas
        """
        resultado = ConsolidacionResult()
        
        for registro in nuevos:
            # Validar
            if not self.es_valido(registro):
                resultado.invalidos.append(registro)
                continue
            
            # Buscar duplicado
            es_dup, existente, metodo = self.buscar_duplicado(registro)
            
            if es_dup:
                # Verificar si el nuevo aporta datos
                fusionado = self.fusionar(existente, registro)
                if fusionado != existente:
                    # Actualizar en la base
                    idx = self.registros.index(existente)
                    self.registros[idx] = fusionado
                    self._actualizar_indices(idx, fusionado)
                    resultado.actualizados.append({
                        "original": existente,
                        "actualizado": fusionado,
                        "metodo": metodo
                    })
                else:
                    resultado.duplicados_ignorados.append({
                        "registro": registro,
                        "existente": existente,
                        "metodo": metodo
                    })
            else:
                # Agregar nuevo registro
                registro["fecha_actualizacion"] = datetime.now().isoformat()
                self.registros.append(registro)
                idx = len(self.registros) - 1
                self._actualizar_indices(idx, registro)
                resultado.agregados.append(registro)
        
        return resultado
    
    def _actualizar_indices(self, idx: int, registro: Dict):
        """Actualiza los índices para un registro."""
        # Hash
        hash_reg = self.calcular_hash(registro)
        self.indice_hash[hash_reg] = idx
        
        # Teléfonos
        telefonos = registro.get("telefono", [])
        if isinstance(telefonos, str):
            telefonos = [telefonos]
        for tel in telefonos:
            tel_norm = self.normalizar_telefono(tel)
            if tel_norm:
                if tel_norm not in self.indice_telefono:
                    self.indice_telefono[tel_norm] = set()
                self.indice_telefono[tel_norm].add(idx)
        
        # Email
        email = registro.get("email", "")
        if email:
            self.indice_email[email.lower()] = idx
    
    def guardar(self, path: str = None):
        """Guarda la base de datos consolidada."""
        path = Path(path) if path else self.base_datos_path
        if not path:
            raise ValueError("No se especificó ruta para guardar")
        
        # Asegurar que existe el directorio
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "metadata": {
                "fecha_actualizacion": datetime.now().isoformat(),
                "total_registros": len(self.registros),
                "fuente": "consolidador_multiagente"
            },
            "registros": self.registros
        }
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"[Consolidador] Guardados {len(self.registros)} registros en {path}")
    
    def estadisticas(self) -> Dict:
        """Devuelve estadísticas de la base de datos."""
        total = len(self.registros)
        
        con_telefono = sum(1 for r in self.registros if r.get("telefono"))
        con_email = sum(1 for r in self.registros if r.get("email"))
        con_web = sum(1 for r in self.registros if r.get("web"))
        con_direccion = sum(1 for r in self.registros if r.get("direccion"))
        
        # Por tipo
        por_tipo = {}
        for r in self.registros:
            tipo = r.get("tipo", "despacho")
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
        
        # Por ciudad
        por_ciudad = {}
        for r in self.registros:
            ciudad = r.get("ciudad", "Sin ciudad")
            por_ciudad[ciudad] = por_ciudad.get(ciudad, 0) + 1
        
        return {
            "total": total,
            "con_telefono": con_telefono,
            "con_email": con_email,
            "con_web": con_web,
            "con_direccion": con_direccion,
            "contacto_completo": sum(
                1 for r in self.registros 
                if r.get("telefono") and r.get("email") and r.get("web")
            ),
            "por_tipo": por_tipo,
            "por_ciudad": por_ciudad,
        }
