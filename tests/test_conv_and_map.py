"""
変換とマッピングのユニットテスト
"""

import pytest
from x32_mcp.conv import db_to_level, level_to_db
from x32_mcp.mapping import source_to_code, code_to_source


class TestConversion:
    """dB ⇄ level型の変換テスト"""

    def test_db_to_level_min(self):
        assert db_to_level(-90.0) == pytest.approx(0.0)

    def test_db_to_level_max(self):
        # +10 dB is the top of the measured table (0.999022), not exactly 1.0
        assert db_to_level(10.0) == pytest.approx(0.999022, abs=1e-6)

    def test_db_to_level_mid(self):
        # -40 dB is a measured point of the X32 fader curve (0.187683)
        assert db_to_level(-40.0) == pytest.approx(0.187683, abs=1e-6)

    def test_db_to_level_is_monotonic(self):
        values = [db_to_level(db) for db in range(-90, 11, 5)]
        assert values == sorted(values)

    def test_level_to_db_min(self):
        assert level_to_db(0.0) == pytest.approx(-90.0)

    def test_level_to_db_max(self):
        assert level_to_db(1.0) == pytest.approx(10.0)

    def test_round_trip(self):
        """往復変換が元の値に戻る"""
        original_db = -20.0
        level = db_to_level(original_db)
        result_db = level_to_db(level)
        assert result_db == pytest.approx(original_db, abs=0.1)


class TestMapping:
    """出力ソースマッピングのテスト"""

    def test_source_to_code_off(self):
        assert source_to_code("OFF") == 0

    def test_source_to_code_main(self):
        assert source_to_code("MainL") == 1
        assert source_to_code("MainR") == 2

    def test_source_to_code_bus(self):
        assert source_to_code("Bus1") == 4
        assert source_to_code("Bus16") == 19

    def test_source_to_code_matrix(self):
        assert source_to_code("Matrix1") == 20
        assert source_to_code("Matrix6") == 25

    def test_source_to_code_invalid(self):
        with pytest.raises(ValueError, match="無効な出力ソース"):
            source_to_code("InvalidSource")

    def test_code_to_source_off(self):
        assert code_to_source(0) == "OFF"

    def test_code_to_source_main(self):
        assert code_to_source(1) == "MainL"
        assert code_to_source(2) == "MainR"

    def test_code_to_source_bus(self):
        assert code_to_source(4) == "Bus1"
        assert code_to_source(19) == "Bus16"

    def test_code_to_source_invalid(self):
        with pytest.raises(ValueError, match="未定義の出力ソースコード"):
            code_to_source(999)

    def test_round_trip(self):
        """往復変換が元の値に戻る"""
        original = "Bus5"
        code = source_to_code(original)
        result = code_to_source(code)
        assert result == original