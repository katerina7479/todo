import pytest

from validator import validate_title, validate_priority, validate_todo_id, MAX_TITLE_LENGTH


class TestValidateTitle:
    def test_valid_title(self):
        assert validate_title("Buy groceries") == "Buy groceries"

    def test_strips_whitespace(self):
        assert validate_title("  Buy groceries  ") == "Buy groceries"

    def test_empty_title_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_title("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            validate_title("   ")

    def test_non_string_raises_type_error(self):
        with pytest.raises(TypeError, match="string"):
            validate_title(42)

    def test_none_raises_type_error(self):
        with pytest.raises(TypeError, match="string"):
            validate_title(None)

    def test_max_length_accepted(self):
        title = "x" * MAX_TITLE_LENGTH
        assert validate_title(title) == title

    def test_exceeds_max_length_raises(self):
        title = "x" * (MAX_TITLE_LENGTH + 1)
        with pytest.raises(ValueError, match="exceed"):
            validate_title(title)

    def test_single_char_title(self):
        assert validate_title("a") == "a"


class TestValidatePriority:
    def test_valid_low(self):
        assert validate_priority("low") == "low"

    def test_valid_medium(self):
        assert validate_priority("medium") == "medium"

    def test_valid_high(self):
        assert validate_priority("high") == "high"

    def test_normalizes_case(self):
        assert validate_priority("HIGH") == "high"
        assert validate_priority("Medium") == "medium"

    def test_strips_whitespace(self):
        assert validate_priority("  low  ") == "low"

    def test_invalid_priority_raises(self):
        with pytest.raises(ValueError, match="one of"):
            validate_priority("urgent")

    def test_non_string_raises_type_error(self):
        with pytest.raises(TypeError, match="string"):
            validate_priority(1)


class TestValidateTodoId:
    def test_valid_id(self):
        assert validate_todo_id(1) == 1
        assert validate_todo_id(42) == 42

    def test_zero_raises(self):
        with pytest.raises(ValueError, match="positive"):
            validate_todo_id(0)

    def test_negative_raises(self):
        with pytest.raises(ValueError, match="positive"):
            validate_todo_id(-1)

    def test_non_integer_raises(self):
        with pytest.raises(TypeError, match="integer"):
            validate_todo_id("1")

    def test_float_raises(self):
        with pytest.raises(TypeError, match="integer"):
            validate_todo_id(1.0)
