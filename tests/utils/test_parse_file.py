import pathlib as pt

from dbqq import utils

cwd = pt.Path(__file__)
sql = cwd / "../sql"


class TestParseFile:
    def test_parse_file(self):
        file_path = sql / "test_file.sql"
        output = utils.parse_file(file_path)
        return

    def test_parse_file_with_cache(self):
        file_path = sql / "test_cache.sql"
        output = utils.parse_file(file_path, cache=True)
        return


if __name__ == "__main__":
    T = TestParseFile()
    T.test_parse_file()
    T.test_parse_file_with_cache()
