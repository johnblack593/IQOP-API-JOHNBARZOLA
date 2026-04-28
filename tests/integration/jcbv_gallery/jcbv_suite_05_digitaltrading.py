import os, time, unittest
from dotenv import load_dotenv
from iqoptionapi.stable_api import IQ_Option

load_dotenv()
iq = None
digital_order_id = None

class Suite05DigitalTrading(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        global iq
        iq = IQ_Option(os.getenv("IQ_EMAIL"), os.getenv("IQ_PASSWORD"))
        check, reason = iq.connect()
        assert check, f"Conexión fallida: {reason}"
        iq.change_balance("PRACTICE")
        time.sleep(2)

    def test_01_discover_digital_assets(self):
        """Verifica que el fallback de activos digitales funciona."""
        assets = iq.get_all_open_time()
        digital = assets.get("digital", {})
        open_assets = [k for k, v in digital.items() if v.get("open")]
        print(f"\nActivos digitales abiertos: {len(open_assets)}")
        print(f"Muestra: {open_assets[:5]}")
        self.assertGreater(len(open_assets), 0,
            "No hay activos digitales abiertos. Verificar horario de mercado "
            "o usar activos OTC: EURUSD-OTC")

    def test_02_buy_digital_call(self):
        """Ejecuta un trade digital CALL y captura el order_id."""
        global digital_order_id
        # Usar OTC si disponible para evitar dependencia de horario
        assets = iq.get_all_open_time()
        digital = assets.get("digital", {})
        open_assets = [k for k, v in digital.items() if v.get("open")]
        # Priorizar AUDUSD-op (formato común para digital) o EURUSD-OTC
        asset = next((a for a in open_assets if a == "AUDUSD-op"), None)
        if not asset:
            asset = next((a for a in open_assets if a == "EURUSD-OTC"), None)
        if not asset:
            asset = next((a for a in open_assets if "OTC" in a or "-op" in a), None)
        if not asset and open_assets:
            asset = open_assets[0]

        print(f"\nActivo seleccionado: {asset}")
        self.assertIsNotNone(asset, "No hay activos digitales disponibles")
        
        # Monto mínimo 1 USD, duración 1 minuto
        success, order_id = iq.buy_digital_spot_v2(asset, 1, "call", 1)
        print(f"success={success}, order_id={order_id}")
        self.assertTrue(success, "buy_digital_spot_v2 retornó False")
        self.assertIsNotNone(order_id, "order_id es None tras buy exitoso")
        digital_order_id = order_id
        print(f"✅ Digital CALL abierto: order_id={order_id}")

    def test_03_check_win_digital(self):
        """Verifica que check_win_digital retorna resultado antes del timeout."""
        self.assertIsNotNone(digital_order_id, "No hay order_id del test anterior")
        print(f"\nEsperando resultado para order_id={digital_order_id}...")
        t_start = time.time()
        result = iq.check_win_digital(digital_order_id, timeout=130)
        elapsed = time.time() - t_start
        print(f"Resultado: {result} | Tiempo: {elapsed:.2f}s")
        
        # Criterio de aceptación: resultado antes del timeout
        self.assertIsNotNone(result,
            f"check_win_digital hizo TIMEOUT ({elapsed:.1f}s).")
        # El SDK retorna profit (float) o strings ("win", "loose", "equal")
        self.assertTrue(isinstance(result, (int, float, str)),
            f"Resultado de tipo inesperado: {type(result)} -> {result}")
        self.assertLess(elapsed, 125,
            f"Tiempo excesivo: {elapsed:.1f}s (debería ser <= expiración + 5s)")
        print(f"✅ Digital trade validado: {result} en {elapsed:.2f}s")

    @classmethod
    def tearDownClass(cls):
        if iq and hasattr(iq, "api"):
            iq.api.close()

if __name__ == "__main__":
    unittest.main(verbosity=2)
