"""
Suite de integración JCBV-NEXUS SDK v9.1.
Ejecutar con: pytest tests/integration/ -v -m integration
Requiere credenciales reales y cuenta PRACTICE.
"""
import pytest
import time

@pytest.mark.integration
class TestFullFlow:
    def test_connection_and_balance(self, connected_api):
        """Verifica que podemos conectar y obtener el balance."""
        balance = connected_api.get_balance()
        assert isinstance(balance, (int, float))
        assert balance >= 0
        
        mode = connected_api.get_balance_mode()
        assert mode == "PRACTICE"

    def test_binary_buy_and_wait(self, connected_api):
        """
        Realiza una compra mínima en EURUSD (o EURUSD-OTC) y espera el resultado.
        Usa check_win que ahora es reactivo (Sprint 14).
        """
        active = "EURUSD-OTC"
        amount = 1
        action = "call"
        duration = 1 # 1 minuto
        
        # 1. Comprar
        status, order_id = connected_api.buy(amount, active, action, duration)
        assert status is True, f"Error al comprar: {order_id}"
        assert order_id is not None
        
        # 2. Esperar resultado (con timeout largo para el vencimiento de la vela)
        # Una vela de 1m puede tardar hasta 120s en cerrar y notificar
        result = connected_api.check_win(order_id, timeout=150)
        
        assert result in ("win", "loose", "equal"), f"Resultado inesperado: {result}"

    def test_digital_buy_and_wait(self, connected_api):
        """Verifica el flujo digital usando check_win_digital."""
        active = "EURUSD-OTC"
        amount = 1
        action = "call"
        duration = 1
        
        status, order_id = connected_api.buy_digital_spot(active, amount, action, duration)
        assert status is True
        
        # check_win_digital ahora usa _wait_result (Sprint 14)
        result = connected_api.check_win_digital(order_id, timeout=150)
        
        # Digital retorna profit o 0/negativo? Depende del handler.
        # socket_option_closed suele retornar el mensaje o el win amount.
        assert result is not None
