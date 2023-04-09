import subprocess

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

subprocess.run(
    f"dbqq-encrypt-yaml \
        {db_connectors_yaml} \
        {public_key_file} \
        -ef {encrypted_file}\
    "
)


class TestEncryptKeys:
    rsa_helper = RSA.from_folder(key_folder)
    config = contents

    def test_decrypt_file(self):
        encrypted = dbs.yaml.encrypt(db_connectors_yaml, self.rsa_helper)

        encrypted.dump(encrypted_file)

        result = dbs.yaml.decrypt(encrypted_file, self.rsa_helper)

        assert (
            result == self.config
        ), "decrypted dictionary is not equal original"

        return


if __name__ == "__main__":
    T = TestEncryptKeys()
    T.test_decrypt_file()
    T.test_decrypt_file()
