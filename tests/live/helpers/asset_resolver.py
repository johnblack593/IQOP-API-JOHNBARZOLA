"""
tests/live/helpers/asset_resolver.py
────────────────────────────────────
Resuelve activos abiertos y montos mínimos para la validación de trading.
"""

import iqoptionapi.core.constants as OP_code
from iqoptionapi.core.logger import get_logger

class AssetResolver:
    def __init__(self, api):
        self.api = api
        self.logger = get_logger(__name__)
        self.open_times = {}
        
        # Mapa de preferencias (Grupo A y B)
        self.PREFERENCES = {
            "blitz":    ["EURUSD-OTC", "GBPUSD-OTC", "AUDUSD-OTC"],
            "binary":   ["EURUSD-OTC", "GBPUSD-OTC", "EURGBP-OTC", "EURUSD", "GBPUSD"],
            "digital":  ["EURUSD-OTC", "GBPUSD-OTC", "AUDUSD-OTC", "EURUSD", "GBPUSD"],
            "forex":    ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "EURGBP"],
            "stocks":   ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
            "crypto":   ["BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD"],
            "commodity":["Gold", "Silver", "CrudeOil"],
            "index":    ["US500", "US30", "USTECH"],
            "etf":      ["SPY", "QQQ", "GLD"]
        }

    def sync(self):
        """Sincroniza el estado de los mercados abiertos."""
        self.open_times = self.api.get_all_open_time()
        if not self.open_times:
            self.logger.warning("No se pudo obtener el catálogo de apertura de mercados.")
        return self.open_times

    def resolve(self, subcategory: str) -> str:
        """
        Retorna el primer activo disponible en la subcategoría según preferencias.
        """
        if subcategory not in self.PREFERENCES:
            return None
            
        candidates = self.PREFERENCES[subcategory]
        
        # Mapeo de subcategoría a clave en get_all_open_time()
        cat_map = {
            "blitz": "blitz",
            "binary": "binary",
            "digital": "digital",
            "forex": "forex",
            "stocks": "stock",
            "crypto": "crypto",
            "commodity": "commodity",
            "index": "index",
            "etf": "etf"
        }
        
        market_key = cat_map.get(subcategory)
        if not market_key or market_key not in self.open_times:
            # Intentar buscar el activo directamente en ACTIVES
            for asset in candidates:
                if asset in OP_code.ACTIVES:
                    return asset
            return candidates[0]

        # 1. Buscar entre los candidatos preferidos
        for asset in candidates:
            market_data = self.open_times[market_key].get(asset, {})
            if market_data.get("open"):
                return asset
        
        # 2. Si es OTC time, buscar versiones OTC de los candidatos
        for asset in candidates:
            otc_asset = f"{asset}-OTC"
            market_data = self.open_times[market_key].get(otc_asset, {})
            if market_data.get("open"):
                return otc_asset

        # 3. Si ninguno de los preferidos está abierto, buscar CUALQUIER abierto en esa categoría
        # Pero filtramos para evitar mezclar tipos (ej: no usar BTCUSD en forex)
        for asset, data in self.open_times[market_key].items():
            if data.get("open"):
                # Filtro heurístico: forex suele tener 6 letras, crypto suele tener BTC/ETH/LTC
                if subcategory == "forex" and (len(asset.replace("-OTC","")) != 6):
                    continue
                if subcategory == "crypto" and not any(c in asset for c in ["BTC", "ETH", "LTC", "XRP"]):
                    continue
                return asset
                
        return candidates[0] # Fallback final

    def get_min_amount(self, asset: str, instrument_type: str) -> float:
        """
        Retorna el monto mínimo + margen de seguridad.
        """
        # Regla general de IQ Option: $1.0 para opciones, $1.0-$2.0 para margen
        if instrument_type in ["binary", "turbo", "digital", "blitz"]:
            return 1.0
            
        # Para margen, intentar consultar leverages si es posible
        try:
            active_id = OP_code.ACTIVES.get(asset)
            if active_id:
                # get_available_leverages requiere instrument_type real (forex, cfd, crypto)
                # simplificado: la mayoría de forex/crypto en practice permiten $1
                return 1.01
        except:
            pass
            
        return 1.0
