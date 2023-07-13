import sys
import dbqq.security.cli.write_keys
from unittest import mock

try:
    from .shared import private_key_file, public_key_file, key_folder
except ImportError:
    from shared import private_key_file, public_key_file, key_folder


def test_cli_write_keys():
    public_key_file.unlink(missing_ok=True)
    private_key_file.unlink(missing_ok=True)

    with mock.patch.object(
        sys,
        "argv",
        [
            __file__,
            "-k=1024",
            f"-l={key_folder.resolve()}",
            "-pbn=public_key",
            "-prn=private_key",
            "-f=PEM",
        ],
    ):
        dbqq.security.cli.write_keys.run()

    assert private_key_file.exists(), f"{private_key_file} does not exist"
    assert public_key_file.exists(), f"{public_key_file} does not exist"


if __name__ == "__main__":
    test_cli_write_keys()
