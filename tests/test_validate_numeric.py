"""Test validate_numeric function directly."""

import math

import pytest

from custom_components.sourceful_zap.coordinator import validate_numeric


def test_none_returns_none():
    assert validate_numeric(None) is None


def test_valid_float():
    assert validate_numeric(42.5) == 42.5


def test_valid_int():
    assert validate_numeric(100) == 100.0


def test_valid_zero():
    assert validate_numeric(0) == 0.0


def test_valid_negative():
    assert validate_numeric(-50.0) == -50.0


def test_string_float():
    assert validate_numeric("123.45") == 123.45


def test_string_int():
    assert validate_numeric("100") == 100.0


def test_invalid_string():
    assert validate_numeric("abc") is None


def test_nan_returns_none():
    assert validate_numeric(float("nan")) is None


def test_inf_returns_none():
    assert validate_numeric(float("inf")) is None


def test_negative_inf_returns_none():
    assert validate_numeric(float("-inf")) is None


def test_modbus_sentinel_65535():
    assert validate_numeric(65535) is None


def test_modbus_sentinel_negative_32768():
    assert validate_numeric(-32768) is None


def test_modbus_sentinel_32768():
    assert validate_numeric(32768) is None


def test_modbus_sentinel_32767():
    assert validate_numeric(32767) is None


def test_modbus_sentinel_negative_32767():
    assert validate_numeric(-32767) is None


def test_large_non_energy_value_filtered():
    """Values >1e6 are filtered for non-energy fields."""
    assert validate_numeric(2000000, "some_field") is None


def test_large_energy_value_allowed():
    """Large values allowed for energy fields."""
    assert validate_numeric(50900524, "total_generation_Wh") == 50900524


def test_large_value_allowed_for_import():
    assert validate_numeric(19129172, "total_import_Wh") == 19129172


def test_large_value_allowed_for_export():
    assert validate_numeric(9670222, "total_export_Wh") == 9670222


def test_large_value_allowed_for_charge():
    assert validate_numeric(5261000, "total_charge_Wh") == 5261000


def test_large_value_allowed_for_discharge():
    assert validate_numeric(4389000, "total_discharge_Wh") == 4389000


def test_overflow_rejected():
    assert validate_numeric(4294836224, "total_import_Wh", reject_overflow=True) is None


def test_overflow_not_rejected_by_default():
    assert validate_numeric(4294836224, "total_import_Wh") == 4294836224


def test_min_value_filter():
    assert validate_numeric(-5, "test", min_value=0) is None


def test_max_value_filter():
    assert validate_numeric(200, "test", max_value=150) is None


def test_min_max_in_range():
    assert validate_numeric(50, "test", min_value=0, max_value=100) == 50.0


def test_min_boundary():
    assert validate_numeric(0, "test", min_value=0) == 0.0


def test_max_boundary():
    assert validate_numeric(100, "test", max_value=100) == 100.0


def test_bool_value():
    """Bool is a subclass of int, should convert."""
    assert validate_numeric(True) == 1.0
    assert validate_numeric(False) == 0.0


def test_empty_string():
    assert validate_numeric("") is None


def test_list_value():
    assert validate_numeric([1, 2]) is None


def test_dict_value():
    assert validate_numeric({"a": 1}) is None
