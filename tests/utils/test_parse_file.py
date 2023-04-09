from dbqq import utils

def test_parse_file():

    file_path = "./.scratch/test_file.sql"

    name, query, connector = utils.parse_file(file_path)

    return

if __name__ == "__main__":
    test_parse_file()