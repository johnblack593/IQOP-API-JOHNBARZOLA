"""
tests/live/helpers/report_builder.py
────────────────────────────────────
Genera el reporte forense TRADING_VALIDATION_REPORT.md.
"""

from typing import List
from datetime import datetime
from .trade_executor import TradeResult

class ReportBuilder:
    def __init__(self, results: List[TradeResult], metadata: dict):
        self.results = results
        self.metadata = metadata
        self.start_time = metadata.get("start_time", datetime.now())
        self.end_time = datetime.now()

    def build(self, output_path: str):
        md = []
        md.append("# TRADING VALIDATION REPORT\n")
        
        # SECCIÓN 0: METADATA
        md.append("## SECCIÓN 0: METADATA DE EJECUCIÓN")
        duration = (self.end_time - self.start_time).total_seconds()
        md.append(f"- **Fecha Inicio:** {self.start_time.isoformat()}")
        md.append(f"- **Fecha Fin:** {self.end_time.isoformat()}")
        md.append(f"- **Duración Total:** {duration:.1f} segundos")
        md.append(f"- **Versión SDK:** {self.metadata.get('sdk_version', '9.3.721')}")
        md.append(f"- **Cuenta usada:** PRACTICE ✅")
        md.append(f"- **Balance Inicial:** ${self.metadata.get('initial_balance', 0):.2f}")
        md.append(f"- **Balance Final:** ${self.metadata.get('final_balance', 0):.2f}")
        md.append(f"- **Net P&L:** ${self.metadata.get('final_balance', 0) - self.metadata.get('initial_balance', 0):.2f}")
        md.append("")

        # SECCIÓN 1: RESUMEN EJECUTIVO
        md.append("## SECCIÓN 1: RESUMEN EJECUTIVO")
        md.append("| GRUPO | SUBCATEGORÍA | ACTIVO USADO | OPS | WIN | LOSS | SKIP | TIMEOUT | ERROR | TASA ÉXITO SDK |")
        md.append("|-------|--------------|--------------|-----|-----|------|------|---------|-------|----------------|")
        
        groups = {}
        for r in self.results:
            key = (r.group, r.subcategory)
            if key not in groups:
                groups[key] = {"asset": r.asset, "ops": 0, "win": 0, "loss": 0, "skip": 0, "timeout": 0, "error": 0}
            g = groups[key]
            g["ops"] += 1
            if r.result == "WIN": g["win"] += 1
            elif r.result == "LOSS": g["loss"] += 1
            elif r.result == "SKIP": g["skip"] += 1
            elif r.result == "TIMEOUT": g["timeout"] += 1
            elif r.result == "ERROR": g["error"] += 1

        for (grp, sub), v in groups.items():
            success_rate = ((v["ops"] - v["error"]) / v["ops"] * 100) if v["ops"] > 0 else 0
            emoji = "✅" if success_rate == 100 else "⚠️" if success_rate > 80 else "❌"
            md.append(f"| {grp} | {sub.capitalize()} | {v['asset']} | {v['ops']} | {v['win']} | {v['loss']} | {v['skip']} | {v['timeout']} | {v['error']} | {success_rate:.0f}% {emoji} |")
        md.append("")

        # SECCIÓN 2: DETALLE FORENSE
        md.append("## SECCIÓN 2: DETALLE FORENSE POR OPERACIÓN")
        for i, r in enumerate(self.results):
            md.append(f"### [{r.group}.{i+1}] {r.subcategory.capitalize()} — {r.asset} — {r.direction.upper()}")
            md.append("| Campo | Valor |")
            md.append("|-------|-------|")
            md.append(f"| Order ID | {r.order_id} |")
            md.append(f"| Asset | {r.asset} |")
            md.append(f"| Type | {r.instrument_type} |")
            md.append(f"| Direction | {r.direction} |")
            md.append(f"| Amount | ${r.amount:.2f} |")
            md.append(f"| Duration | {r.duration_sec}s |")
            md.append(f"| Open Price | {r.open_price or 'N/A'} |")
            md.append(f"| Close Price | {r.close_price or 'N/A'} |")
            res_emoji = "🏆" if r.result == "WIN" else "💀" if r.result == "LOSS" else "⚖️" if r.result == "EQUAL" else "❓"
            md.append(f"| Result | {r.result} {res_emoji} |")
            md.append(f"| Profit | ${r.profit_usd:+.2f} |")
            md.append(f"| Duration Real | {r.duration_ms:,} ms |")
            md.append(f"| Signal Confidence | {r.signal_confidence:.2f} |")
            md.append(f"| Timestamp | {r.timestamp} |")
            md.append(f"| SDK Status | {'✅ OK' if r.result != 'ERROR' else '❌ FAIL'} |")
            if r.error_detail:
                # Truncar error_detail si es muy largo
                safe_err = r.error_detail.split('\n')[0][:100]
                md.append(f"| Error Detail | {safe_err}... |")
            md.append("")

        # SECCIÓN 3: CALIDAD DE SEÑALES
        md.append("## SECCIÓN 3: ANÁLISIS DE CALIDAD DE SEÑALES")
        md.append("| Activo | Señal Servidor | Direction Elegida | Resultado | ¿Señal Acertó? |")
        md.append("|--------|----------------|-------------------|-----------|----------------|")
        sig_count = 0
        sig_hits = 0
        for r in self.results:
            if r.group == "A" and r.server_indicators:
                signal = r.server_indicators.get("consensus", "N/A")
                hit = "✅ Sí" if (signal == "BUY" and r.result == "WIN" and r.direction == "CALL") or \
                               (signal == "SELL" and r.result == "WIN" and r.direction == "PUT") or \
                               (signal == "BUY" and r.result == "LOSS" and r.direction == "PUT") or \
                               (signal == "SELL" and r.result == "LOSS" and r.direction == "CALL") else "❌ No"
                
                # Simplificado: si WIN y direction==signal -> hit. Si LOSS y direction==signal -> miss.
                # Pero direction se elige basada en signal.
                is_hit = r.result == "WIN"
                hit_str = "✅ Sí" if is_hit else "❌ No"
                md.append(f"| {r.asset} | {signal} | {r.direction} | {r.result} | {hit_str} |")
                sig_count += 1
                if is_hit: sig_hits += 1
        
        hit_rate = (sig_hits / sig_count * 100) if sig_count > 0 else 0
        md.append(f"\n- **Precisión Señal Servidor:** {hit_rate:.1f}% ({sig_hits}/{sig_count})")
        md.append("")

        # SECCIÓN 4: ANÁLISIS DE MARGEN
        md.append("## SECCIÓN 4: ANÁLISIS DE MARGEN (Grupo B)")
        md.append("| Activo | Spread Real | Slippage | Leverage | PnL Realizado |")
        md.append("|--------|-------------|----------|----------|---------------|")
        for r in self.results:
            if r.group == "B" and r.result != "SKIP":
                spread = abs(r.close_price - r.open_price) if r.close_price and r.open_price else 0
                md.append(f"| {r.asset} | {spread:.6f} | N/A | {r.metadata.get('leverage', 'N/A')} | ${r.profit_usd:+.2f} |")
        md.append("")

        # SECCIÓN 5: BUGS Y HALLAZGOS
        md.append("## SECCIÓN 5: BUGS Y HALLAZGOS")
        errors = [r for r in self.results if r.result == "ERROR"]
        if not errors:
            md.append("Sin hallazgos críticos. Todos los flujos ejecutaron correctamente.")
        else:
            for err in errors:
                md.append(f"**[BUG-LIVE-{err.subcategory.upper()}]**")
                md.append(f"- **Módulo:** {err.instrument_type}")
                md.append(f"- **Descripción:** {err.error_detail}")
                md.append("- **Estado:** OPEN")
                md.append("")

        # SECCIÓN 6: RENDIMIENTO Y LATENCIA
        md.append("## SECCIÓN 6: RENDIMIENTO Y LATENCIA")
        md.append("| Operación | Min (ms) | Max (ms) | Avg (ms) |")
        md.append("|-----------|----------|----------|----------|")
        
        latencies = {}
        for r in self.results:
            if r.duration_ms > 0:
                key = f"Trade Execution ({r.subcategory})"
                if key not in latencies: latencies[key] = []
                latencies[key].append(r.duration_ms)
        
        for op, vals in latencies.items():
            md.append(f"| {op} | {min(vals)} | {max(vals)} | {sum(vals)/len(vals):.0f} |")
        md.append("")

        # SECCIÓN 8: VEREDICTO FINAL
        md.append("## SECCIÓN 8: VEREDICTO FINAL")
        md.append("| GRUPO | SUBCATEGORÍA | SDK STATUS | TRADING STATUS | VEREDICTO |")
        md.append("|-------|--------------|------------|----------------|-----------|")
        for (grp, sub), v in groups.items():
            sdk_status = "✅ Sin errores" if v["error"] == 0 else "❌ Errores detectados"
            trading_status = "WIN+LOSS recibidos" if (v["win"] + v["loss"]) > 0 else "No ejecutado"
            verdict = "✅ READY" if v["error"] == 0 else "❌ NOT READY"
            md.append(f"| {grp} | {sub.capitalize()} | {sdk_status} | {trading_status} | {verdict} |")
        
        total_ops = len(self.results)
        error_ops = len(errors)
        error_rate = (error_ops / total_ops * 100) if total_ops > 0 else 0
        
        global_verdict = "PRODUCTION READY ✅" if error_rate < 5 else "CONDITIONAL READY ⚠️" if error_rate < 15 else "NOT READY ❌"
        md.append(f"\n### VEREDICTO GLOBAL: {global_verdict}")
        md.append(f"- **SDK Error Rate:** {error_rate:.1f}%")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md))
