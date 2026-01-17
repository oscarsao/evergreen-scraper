"""
Tracker de uso y costos de APIs.
"""
import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict


# Costos aproximados por API (USD)
COSTOS_API = {
    "firecrawl": {
        "por_credito": 0.01,
        "limite_gratis": 500,  # créditos/mes
    },
    "google_search": {
        "por_request": 0.005,  # $5 por 1000
        "limite_gratis": 100,  # por día
    },
    "google_places": {
        "por_request": 0.017,  # aprox
        "credito_gratis_mes": 200,  # USD
    },
    "tavily": {
        "por_request": 0.001,  # ~$1 por 1000
        "limite_gratis": 1000,  # por mes
    },
    "openai": {
        "por_1k_tokens_input": 0.00015,  # gpt-4o-mini
        "por_1k_tokens_output": 0.0006,
        "por_query_aprox": 0.01,
    },
}


@dataclass
class APIUsage:
    """Uso de una API."""
    api: str
    requests: int = 0
    creditos: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    costo_estimado: float = 0.0
    fecha: str = field(default_factory=lambda: date.today().isoformat())
    
    def to_dict(self) -> Dict:
        return asdict(self)


class APITracker:
    """Tracker de uso y costos de APIs."""
    
    def __init__(self, data_path: str = "data/api_usage.json"):
        self.data_path = Path(data_path)
        self.usage: Dict[str, Dict[str, Any]] = {}
        self._cargar()
    
    def _cargar(self):
        """Carga datos de uso existentes."""
        if self.data_path.exists():
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    self.usage = json.load(f)
            except:
                self.usage = {}
        else:
            self.usage = {
                "historico": [],
                "dia_actual": {},
                "mes_actual": {},
                "totales": {}
            }
    
    def _guardar(self):
        """Guarda datos de uso."""
        self.data_path.parent.mkdir(exist_ok=True)
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(self.usage, f, ensure_ascii=False, indent=2)
    
    def registrar_uso(
        self,
        api: str,
        requests: int = 1,
        creditos: int = 0,
        tokens_input: int = 0,
        tokens_output: int = 0
    ):
        """Registra uso de una API."""
        hoy = date.today().isoformat()
        mes = date.today().strftime("%Y-%m")
        
        # Calcular costo
        costo = self._calcular_costo(api, requests, creditos, tokens_input, tokens_output)
        
        # Actualizar día actual
        if "dia_actual" not in self.usage:
            self.usage["dia_actual"] = {}
        
        if hoy not in self.usage["dia_actual"]:
            self.usage["dia_actual"] = {hoy: {}}
        
        if api not in self.usage["dia_actual"].get(hoy, {}):
            self.usage["dia_actual"][hoy] = self.usage["dia_actual"].get(hoy, {})
            self.usage["dia_actual"][hoy][api] = {
                "requests": 0, "creditos": 0, "costo": 0.0
            }
        
        self.usage["dia_actual"][hoy][api]["requests"] += requests
        self.usage["dia_actual"][hoy][api]["creditos"] += creditos
        self.usage["dia_actual"][hoy][api]["costo"] += costo
        
        # Actualizar mes actual
        if "mes_actual" not in self.usage:
            self.usage["mes_actual"] = {}
        
        if mes not in self.usage["mes_actual"]:
            self.usage["mes_actual"] = {mes: {}}
        
        if api not in self.usage["mes_actual"].get(mes, {}):
            self.usage["mes_actual"][mes] = self.usage["mes_actual"].get(mes, {})
            self.usage["mes_actual"][mes][api] = {
                "requests": 0, "creditos": 0, "costo": 0.0
            }
        
        self.usage["mes_actual"][mes][api]["requests"] += requests
        self.usage["mes_actual"][mes][api]["creditos"] += creditos
        self.usage["mes_actual"][mes][api]["costo"] += costo
        
        # Actualizar totales
        if "totales" not in self.usage:
            self.usage["totales"] = {}
        
        if api not in self.usage["totales"]:
            self.usage["totales"][api] = {"requests": 0, "creditos": 0, "costo": 0.0}
        
        self.usage["totales"][api]["requests"] += requests
        self.usage["totales"][api]["creditos"] += creditos
        self.usage["totales"][api]["costo"] += costo
        
        self._guardar()
    
    def _calcular_costo(
        self,
        api: str,
        requests: int,
        creditos: int,
        tokens_input: int,
        tokens_output: int
    ) -> float:
        """Calcula el costo estimado."""
        if api not in COSTOS_API:
            return 0.0
        
        costos = COSTOS_API[api]
        
        if api == "firecrawl":
            return creditos * costos.get("por_credito", 0.01)
        elif api == "openai":
            costo_input = (tokens_input / 1000) * costos.get("por_1k_tokens_input", 0)
            costo_output = (tokens_output / 1000) * costos.get("por_1k_tokens_output", 0)
            if costo_input + costo_output == 0:
                return requests * costos.get("por_query_aprox", 0.01)
            return costo_input + costo_output
        else:
            return requests * costos.get("por_request", 0.001)
    
    def obtener_uso_dia(self, fecha: str = None) -> Dict[str, Any]:
        """Obtiene uso del día."""
        fecha = fecha or date.today().isoformat()
        return self.usage.get("dia_actual", {}).get(fecha, {})
    
    def obtener_uso_mes(self, mes: str = None) -> Dict[str, Any]:
        """Obtiene uso del mes."""
        mes = mes or date.today().strftime("%Y-%m")
        return self.usage.get("mes_actual", {}).get(mes, {})
    
    def obtener_totales(self) -> Dict[str, Any]:
        """Obtiene totales históricos."""
        return self.usage.get("totales", {})
    
    def obtener_resumen(self) -> Dict[str, Any]:
        """Obtiene resumen completo."""
        hoy = date.today().isoformat()
        mes = date.today().strftime("%Y-%m")
        
        uso_hoy = self.obtener_uso_dia(hoy)
        uso_mes = self.obtener_uso_mes(mes)
        totales = self.obtener_totales()
        
        # Calcular costos
        costo_hoy = sum(api.get("costo", 0) for api in uso_hoy.values())
        costo_mes = sum(api.get("costo", 0) for api in uso_mes.values())
        costo_total = sum(api.get("costo", 0) for api in totales.values())
        
        # Requests
        requests_hoy = sum(api.get("requests", 0) for api in uso_hoy.values())
        requests_mes = sum(api.get("requests", 0) for api in uso_mes.values())
        requests_total = sum(api.get("requests", 0) for api in totales.values())
        
        return {
            "hoy": {
                "fecha": hoy,
                "requests": requests_hoy,
                "costo": round(costo_hoy, 4),
                "por_api": uso_hoy,
            },
            "mes": {
                "mes": mes,
                "requests": requests_mes,
                "costo": round(costo_mes, 4),
                "por_api": uso_mes,
            },
            "total": {
                "requests": requests_total,
                "costo": round(costo_total, 4),
                "por_api": totales,
            },
            "limites": self._obtener_limites_restantes(uso_mes),
        }
    
    def _obtener_limites_restantes(self, uso_mes: Dict) -> Dict[str, Any]:
        """Calcula límites restantes de planes gratis."""
        limites = {}
        
        for api, costos in COSTOS_API.items():
            usado = uso_mes.get(api, {}).get("requests", 0)
            
            if "limite_gratis" in costos:
                limite = costos["limite_gratis"]
                limites[api] = {
                    "limite": limite,
                    "usado": usado,
                    "restante": max(0, limite - usado),
                    "porcentaje": min(100, (usado / limite) * 100) if limite > 0 else 0,
                }
        
        return limites


# Instancia global
_tracker: Optional[APITracker] = None


def get_tracker() -> APITracker:
    """Obtiene instancia global del tracker."""
    global _tracker
    if _tracker is None:
        _tracker = APITracker()
    return _tracker


def registrar_uso(api: str, requests: int = 1, **kwargs):
    """Shortcut para registrar uso."""
    get_tracker().registrar_uso(api, requests, **kwargs)
