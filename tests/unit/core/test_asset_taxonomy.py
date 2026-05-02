"""Unit tests for asset_taxonomy."""
import pytest
from iqoptionapi.strategy.signal import Signal, Direction, AssetType
from iqoptionapi.core.asset_taxonomy import (
    ASSET_RULES, AssetRules, OperationGroup, TaxonomyError,
    MARGIN_ASSET_TYPES, OPTIONS_ASSET_TYPES,
    get_rules, validate_signal, is_otc_asset, normalize_asset_name,
    get_asset_type_from_group_id, is_margin_asset, is_options_asset,
)


class TestGetRules:
    def test_binary_is_options_group(self):
        rules = get_rules(AssetType.BINARY)
        assert rules.group == OperationGroup.OPTIONS

    def test_forex_is_margin_group(self):
        rules = get_rules(AssetType.FOREX)
        assert rules.group == OperationGroup.MARGIN

    def test_forex_needs_leverage(self):
        rules = get_rules(AssetType.FOREX)
        assert rules.needs_leverage is True
        assert rules.needs_tp_sl is True

    def test_binary_needs_duration(self):
        rules = get_rules(AssetType.BINARY)
        assert rules.needs_duration is True
        assert rules.needs_leverage is False

    def test_digital_is_otc_capable(self):
        assert get_rules(AssetType.DIGITAL).is_otc_capable is True

    def test_forex_is_not_otc_capable(self):
        assert get_rules(AssetType.FOREX).is_otc_capable is False

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

    def test_forex_valid_with_zero_duration(self):
        sig = self._make_signal(AssetType.FOREX, 0)
        validate_signal(sig)  # no debe lanzar

    def test_forex_invalid_with_duration(self):
        with pytest.raises(TaxonomyError, match="no debe tener duration"):
            sig = self._make_signal(AssetType.FOREX, 60)
            validate_signal(sig)


class TestOTCHelpers:
    def test_is_otc_true(self):
        assert is_otc_asset("EURUSD-OTC") is True
        assert is_otc_asset("eurusd-otc") is True

    def test_is_otc_false(self):
        assert is_otc_asset("EURUSD") is False
        assert is_otc_asset("BTCUSD") is False

    def test_normalize_forex_rejects_otc_suffix(self):
        with pytest.raises(TaxonomyError, match="no soporta variantes OTC"):
            normalize_asset_name("EURUSD-OTC", AssetType.FOREX)

    def test_normalize_binary_uppercase(self):
        result = normalize_asset_name("eurusd-otc", AssetType.BINARY)
        assert result == "EURUSD-OTC"


class TestGranularTaxonomy:
    def test_all_margin_types_have_instrument_type_field(self):
        for at in MARGIN_ASSET_TYPES:
            rules = get_rules(at)
            assert isinstance(rules.instrument_type, str)
            assert len(rules.instrument_type) > 0

    def test_get_asset_type_from_group_id_forex(self):
        assert get_asset_type_from_group_id(1) == AssetType.FOREX

    def test_get_asset_type_from_group_id_crypto(self):
        assert get_asset_type_from_group_id(16) == AssetType.CRYPTO

    def test_get_asset_type_from_group_id_unknown(self):
        assert get_asset_type_from_group_id(999) is None

    def test_is_margin_asset_true(self):
        for at in MARGIN_ASSET_TYPES:
            assert is_margin_asset(at) is True

    def test_is_options_asset_true(self):
        for at in OPTIONS_ASSET_TYPES:
            assert is_options_asset(at) is True

    def test_forex_max_leverage_1000(self):
        assert get_rules(AssetType.FOREX).max_leverage == 1000

    def test_crypto_max_leverage_200(self):
        assert get_rules(AssetType.CRYPTO).max_leverage == 200

    def test_stocks_max_leverage_100(self):
        assert get_rules(AssetType.STOCKS).max_leverage == 100
