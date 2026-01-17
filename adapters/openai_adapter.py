"""
Adapter para OpenAI API.
Usado para estructurar datos y consultas inteligentes.
"""
import os
import json
import re
from typing import List, Optional, Dict, Any
from .base import SearchAdapter, SearchResult

try:
    from openai import OpenAI
    OPENAI_DISPONIBLE = True
except ImportError:
    OPENAI_DISPONIBLE = False


# Prompt para extraer datos estructurados
PROMPT_EXTRAER_ABOGADOS = """Eres un experto en extraer información de contacto de profesionales legales.

Dado el siguiente texto, extrae información de abogados de extranjería en formato JSON.

INSTRUCCIONES:
1. Extrae SOLO información explícita, no inventes datos
2. Normaliza teléfonos al formato: +34 XXX XXX XXX
3. Valida que los emails contengan @ y dominio válido
4. Clasifica especialidades en: arraigo, asilo, nacionalidad, reagrupación, visados, permisos_trabajo, expulsiones, recursos
5. Si no hay dato, usa null (no string vacío)
6. tipo debe ser: "despacho", "abogado" o "ong"

FORMATO SALIDA (JSON válido):
{
  "abogados": [
    {
      "nombre": "string",
      "tipo": "despacho|abogado|ong",
      "telefono": ["string"] o null,
      "email": "string" o null,
      "web": "string" o null,
      "direccion": "string" o null,
      "ciudad": "string" o null,
      "distrito": "string" o null,
      "especialidades": ["string"] o []
    }
  ]
}

TEXTO A PROCESAR:
{texto}"""

PROMPT_BUSCAR_INFO = """Necesito información de contacto de abogados de extranjería en {ciudad}.

Busca y proporciona datos de abogados/despachos especializados en:
- Extranjería e inmigración
- Arraigo (social, laboral, familiar)
- Nacionalidad española
- Visados y permisos de trabajo
- Asilo y protección internacional

Para cada uno incluye (si está disponible):
- Nombre del despacho o abogado
- Teléfono(s) de contacto
- Email
- Dirección física
- Sitio web
- Especialidades específicas

Solo incluye profesionales que tengan al menos teléfono, email o web verificable.
Responde en formato JSON."""


class OpenAIAdapter(SearchAdapter):
    """Adapter para OpenAI - estructuración de datos y consultas."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"))
        self.nombre = "openai"
        self.model = model
        self.client = None
        
        if OPENAI_DISPONIBLE and self.api_key:
            self.client = OpenAI(api_key=self.api_key)
    
    def esta_disponible(self) -> bool:
        return OPENAI_DISPONIBLE and bool(self.api_key) and self.client is not None
    
    def search(self, query: str, **kwargs) -> List[SearchResult]:
        """
        No es una búsqueda real - usa el conocimiento del modelo.
        Para búsqueda real, usar con Tavily primero.
        """
        ciudad = kwargs.get("ciudad", "Madrid")
        return self.consultar_abogados(ciudad)
    
    def consultar_abogados(self, ciudad: str = "Madrid") -> List[SearchResult]:
        """Consulta al modelo sobre abogados (datos pueden no estar actualizados)."""
        if not self.esta_disponible():
            return []
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un asistente que proporciona información verificable sobre profesionales legales. Solo proporciona datos que conozcas con certeza."
                    },
                    {
                        "role": "user", 
                        "content": PROMPT_BUSCAR_INFO.format(ciudad=ciudad)
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            self.incrementar_contador()
            
            contenido = response.choices[0].message.content
            return self._procesar_json_response(contenido)
            
        except Exception as e:
            print(f"[OpenAI] Error en consulta: {e}")
            return []
    
    def estructurar_texto(self, texto: str) -> List[SearchResult]:
        """Extrae datos estructurados de un texto usando IA."""
        if not self.esta_disponible():
            return []
        
        if not texto or len(texto) < 50:
            return []
        
        # Truncar texto muy largo
        texto = texto[:8000]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Extrae información de contacto de abogados. Responde SOLO con JSON válido."
                    },
                    {
                        "role": "user",
                        "content": PROMPT_EXTRAER_ABOGADOS.format(texto=texto)
                    }
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            self.incrementar_contador()
            
            contenido = response.choices[0].message.content
            return self._procesar_json_response(contenido)
            
        except Exception as e:
            print(f"[OpenAI] Error estructurando texto: {e}")
            return []
    
    def validar_duplicados(
        self, 
        registro1: Dict, 
        registro2: Dict
    ) -> Dict[str, Any]:
        """Usa IA para determinar si dos registros son duplicados."""
        if not self.esta_disponible():
            return {"es_duplicado": False, "confianza": 0}
        
        prompt = f"""Compara estos dos registros de abogados y determina si son el mismo:

REGISTRO 1:
{json.dumps(registro1, ensure_ascii=False, indent=2)}

REGISTRO 2:
{json.dumps(registro2, ensure_ascii=False, indent=2)}

Responde JSON:
{{
  "es_duplicado": true/false,
  "confianza": 0.0-1.0,
  "razon": "explicación breve",
  "datos_nuevos": ["campos del registro2 que aportan info nueva al registro1"]
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Analiza duplicados de registros. Solo JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            self.incrementar_contador()
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"[OpenAI] Error validando duplicados: {e}")
            return {"es_duplicado": False, "confianza": 0}
    
    def enriquecer_registro(
        self, 
        registro: Dict, 
        info_adicional: str
    ) -> Dict:
        """Enriquece un registro existente con información adicional."""
        if not self.esta_disponible():
            return registro
        
        prompt = f"""Dado este registro de abogado:
{json.dumps(registro, ensure_ascii=False, indent=2)}

Y esta información adicional encontrada:
{info_adicional[:2000]}

Genera un registro actualizado que:
1. Mantenga los datos existentes
2. Agregue información nueva que no existía
3. Actualice datos si los nuevos son más completos
4. NO elimine datos existentes
5. Mantenga el mismo formato JSON

Responde SOLO con el JSON actualizado."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Fusiona registros de datos. Solo JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            self.incrementar_contador()
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            print(f"[OpenAI] Error enriqueciendo registro: {e}")
            return registro
    
    def _procesar_json_response(self, contenido: str) -> List[SearchResult]:
        """Procesa respuesta JSON de OpenAI."""
        resultados = []
        
        try:
            data = json.loads(contenido)
            
            # Buscar array de abogados en diferentes estructuras posibles
            abogados = []
            if isinstance(data, list):
                abogados = data
            elif isinstance(data, dict):
                abogados = data.get("abogados", data.get("results", data.get("data", [])))
                if not isinstance(abogados, list):
                    abogados = [data]  # Es un solo registro
            
            for item in abogados:
                if not isinstance(item, dict):
                    continue
                
                nombre = item.get("nombre", "")
                if not nombre:
                    continue
                
                telefonos = item.get("telefono", item.get("telefonos", []))
                if isinstance(telefonos, str):
                    telefonos = [telefonos] if telefonos else []
                
                # Normalizar teléfonos
                telefonos = [self.normalizar_telefono(t) for t in telefonos if t]
                
                email = item.get("email")
                if email and not self.validar_email(email):
                    email = None
                
                sr = SearchResult(
                    nombre=nombre,
                    tipo=item.get("tipo", "despacho"),
                    telefono=telefonos,
                    email=email,
                    web=self.limpiar_url(item.get("web", "")),
                    direccion=item.get("direccion"),
                    ciudad=item.get("ciudad"),
                    distrito=item.get("distrito"),
                    especialidades=item.get("especialidades", []),
                    fuente="openai",
                )
                
                if sr.es_valido():
                    resultados.append(sr)
                    
        except json.JSONDecodeError as e:
            print(f"[OpenAI] Error parseando JSON: {e}")
        
        return resultados
    
    def estimar_costo(self, tokens_input: int, tokens_output: int) -> float:
        """Estima el costo de una consulta en USD."""
        # Precios aproximados gpt-4o-mini (enero 2025)
        precio_input = 0.00015 / 1000  # por token
        precio_output = 0.0006 / 1000  # por token
        
        return (tokens_input * precio_input) + (tokens_output * precio_output)
