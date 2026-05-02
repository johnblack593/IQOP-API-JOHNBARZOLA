"""Unit tests for asset_taxonomy."""
import pytest
from iqoptionapi.strategy.signal import Signal, Direction, AssetType
from iqoptionapi.core.asset_taxonomy import (
    ASSET_RULES, AssetRules, OperationGroup, TaxonomyError,
    get_rules, validate_signal, is_otc_asset, normalize_asset_name,
)


class TestGetRules:
    def test_binary_is_options_group(self):
        rules = get_rules(AssetType.BINARY)
        assert rules.group == OperationGroup.OPTIONS

    def test_cfd_is_margin_group(self):
        rules = get_rules(AssetType.CFD)
        assert rules.group == OperationGroup.MARGIN

    def test_cfd_needs_leverage(self):
        rules = get_rules(AssetType.CFD)
        assert rules.needs_leverage is True
        assert rules.needs_tp_sl is True

    def test_binary_needs_duration(self):
        rules = get_rules(AssetType.BINARY)
        assert rules.needs_duration is True
        assert rules.needs_leverage is False

    def test_digital_is_otc_capable(self):
        assert get_rules(AssetType.DIGITAL).is_otc_capable is True

    def test_cfd_is_not_otc_capable(self):
        assert get_rules(AssetType.CFD).is_otc_capable is False

    def test_all_asset_types_have_rules(self):
        for at in AssetType:
            assert at in ASSET_RULES, f"Falta regla para {at}"


class TestValidateSignal:
    def _make_signal(self, asset_type, duration):
        return Signal(
            asset="EURUSD", direction=Direction.CALL,
            duration=duration, amount=1.0,
            asset_type=asset_type, confidence=0.8,
            strategy_id="test"
        )

    def test_binary_valid_with_duration(self):
        sig = self._make_signal(AssetType.BINARY, 60)
        validate_signal(sig)  # no debe lanzar

    def test_binary_invalid_without_duration(self):
        with pytest.raises(TaxonomyError, match="duration > 0"):
            sig = self._make_signal(AssetType.BINARY, 0)
            validate_signal(sig)

    def test_cfd_valid_with_zero_duration(self):
        sig = self._make_signal(AssetType.CFD, 0)
        validate_signal(sig)  # no debe lanzar

    def test_cfd_invalid_with_duration(self):
        with pytest.raises(TaxonomyError, match="no debe tener duration"):
            sig = self._make_signal(AssetType.CFD, 60)
            validate_signal(sig)


class TestOTCHelpers:
    def test_is_otc_true(self):
        assert is_otc_asset("EURUSD-OTC") is True
        assert is_otc_asset("eurusd-otc") is True

    def test_is_otc_false(self):
        assert is_otc_asset("EURUSD") is False
        assert is_otc_asset("BTCUSD") is False

    def test_normalize_cfd_rejects_otc_suffix(self):
        with pytest.raises(TaxonomyError, match="no soporta variantes OTC"):
            normalize_asset_name("EURUSD-OTC", AssetType.CFD)

    def test_normalize_binary_uppercase(self):
        result = normalize_asset_name("eurusd-otc", AssetType.BINARY)
        assert result == "EURUSD-OTC"
