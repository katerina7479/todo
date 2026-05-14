import pytest

from validator import validate_title, validate_id


class TestValidateTitle:
    def test_valid_title(self):
        assert validate_title("Buy groceries") == "Buy groceries"

    def test_strips_leading_whitespace(self):
        assert validate_title("  Buy groceries") == "Buy groceries"

    def test_strips_trailing_whitespace(self):
        assert validate_title("Buy groceries  ") == "Buy groceries"

    def test_strips_both_ends(self):
        assert validate_title("  Buy groceries  ") == "Buy groceries"

    def test_empty_raises_value_error(self):
        with pytest.raises(ValueError):
            validate_title("")

    def test_whitespace_only_raises_value_error(self):
        with pytest.raises(ValueError):
            validate_title("   ")

    def test_single_character_accepted(self):
        assert validate_title("a") == "a"

    def test_returns_string(self):
        assert isinstance(validate_title("hello"), str)


class TestValidateId:
    def test_valid_integer_string(self):
        assert validate_id("1") == 1

    def test_returns_int(self):
        assert isinstance(validate_id("5"), int)

    def test_large_id(self):
        assert validate_id("9999") == 9999

    def test_zero_raises_value_error(self):
        with pytest.raises(ValueError):
            validate_id("0")

    def test_negative_raises_value_error(self):
        with pytest.raises(ValueError):
            validate_id("-1")

    def test_non_numeric_string_raises_value_error(self):
        with pytest.raises(ValueError):
            validate_id("abc")

    def test_float_string_raises_value_error(self):
        with pytest.raises(ValueError):
            validate_id("1.5")

    def test_empty_string_raises_value_error(self):
        with pytest.raises(ValueError):
            validate_id("")

    def test_none_raises_value_error(self):
        with pytest.raises(ValueError):
            validate_id(None)
