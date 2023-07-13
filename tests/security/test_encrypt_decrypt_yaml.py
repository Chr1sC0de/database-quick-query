import pytest
import yaml
import dbqq.security.functions as dbs
from dbqq.security.helpers import RSA

try:
    from .shared import db_connectors_yaml, key_folder, encrypted_file
except ImportError:
    from shared import db_connectors_yaml, key_folder, encrypted_file

with open(db_connectors_yaml, "r") as f:
    contents = yaml.safe_load(f)


class TestEncryptDecrypt:
    @pytest.mark.depends(name="test_cli_write_keys.py::test_cli_write_keys")
    def test_encrypt_dictionary(self):
        rsa_helper = RSA.from_folder(key_folder)
        config = contents
        encrypted = dbs.yaml.encrypt(config, rsa_helper)

        decrypted = dbs.yaml.decrypt(encrypted, rsa_helper)

        encrypted.dump(encrypted_file)

        assert (
            config == decrypted
        ), "decrypted dictionary is not equal original"

        return

    @pytest.mark.depends(name="test_cli_write_keys.py::test_cli_write_keys")
    def test_encrypt_file(self):
        rsa_helper = RSA.from_folder(key_folder)
        config = contents
        encrypted = dbs.yaml.encrypt(db_connectors_yaml, rsa_helper)
        decrypted = dbs.yaml.decrypt(encrypted, rsa_helper)

        encrypted.dump(encrypted_file)

        assert (
            config == decrypted
        ), "decrypted dictionary is not equal original"

        return

    @pytest.mark.depends(name="test_cli_write_keys.py::test_cli_write_keys")
    def test_decrypt_file(self):
        rsa_helper = RSA.from_folder(key_folder)
        config = contents
        encrypted = dbs.yaml.encrypt(db_connectors_yaml, rsa_helper)

        encrypted.dump(encrypted_file)

        result = dbs.yaml.decrypt(encrypted_file, rsa_helper)

        assert result == config, "decrypted dictionary is not equal original"

        return


if __name__ == "__main__":
    T = TestEncryptDecrypt()
    T.test_encrypt_dictionary()
    T.test_encrypt_file()
    T.test_decrypt_file()
