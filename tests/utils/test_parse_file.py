import pytest
import pathlib as pt

from dbqq import utils, connectors

cwd = pt.Path(__file__)
sql = cwd / "../sql"


class TestParseFile:
    @pytest.mark.skipif(
        condition=not hasattr(connectors.oracle, "improd"),
        reason="improd must exist",
    )
    def test_parse_file(self):
        file_path = sql / "test_file.sql"
        utils.parse_file(file_path)

    @pytest.mark.skipif(
        condition=not hasattr(connectors.oracle, "improd"),
        reason="improd must exist",
    )
    def test_parse_file_with_cache(self):
        file_path = sql / "test_cache.sql"
        utils.parse_file(file_path, cache=True)


if __name__ == "__main__":
    T = TestParseFile()
    T.test_parse_file()
    T.test_parse_file_with_cache()
