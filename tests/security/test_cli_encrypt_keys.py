import dbqq.security.cli.encrypt_yaml
import sys
from unittest import mock
import pytest

import yaml

import dbqq.security.functions as dbs
from dbqq.security.helpers import RSA

try:
    from .shared import (
        db_connectors_yaml,
        encrypted_file,
        key_folder,
        public_key_file,
    )
except ImportError:
    from shared import (
        db_connectors_yaml,
        encrypted_file,
        key_folder,
        public_key_file,
    )

with open(db_connectors_yaml, "r") as f:
    contents = yaml.safe_load(f)

encrypted_file.unlink(missing_ok=True)


@pytest.mark.depends(name="test_cli_write_keys.py::test_cli_write_keys")
def test_encrypt_file():
    rsa_helper = RSA.from_folder(key_folder)
    config = contents

    with mock.patch.object(
        sys,
        "argv",
        [
            __file__,
            f"{db_connectors_yaml.resolve()}",
            f"{public_key_file.resolve()}",
            f"-l={encrypted_file.resolve()}",
        ],
    ):
        dbqq.security.cli.encrypt_yaml.run()

    encrypted = dbs.yaml.encrypt(db_connectors_yaml, rsa_helper)

    encrypted.dump(encrypted_file)

    result = dbs.yaml.decrypt(encrypted_file, rsa_helper)

    assert result == config, "decrypted dictionary is not equal original"

    return


if __name__ == "__main__":
    test_encrypt_file()
