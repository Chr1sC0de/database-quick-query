import yaml
import subprocess
import dbqq.security.functions as dbs
from dbqq.security.helpers import RSA

try:
    from . shared import db_connectors_yaml, key_folder, encrypted_file
except ImportError:
    from shared import db_connectors_yaml, key_folder, encrypted_file

with open(db_connectors_yaml, "r") as f:
    contents = yaml.safe_load(f)

subprocess.run(
    f"dbqq-write-keys \
        -k 1024 \
        -l {key_folder} \
        -pbn public_key \
        -prn private_key \
        -f PEM \
    "
)

class TestEncryptDecrypt:

    rsa_helper = RSA.from_folder(key_folder)
    config     = contents

    def test_encrypt_dictionary(self):

        encrypted = dbs.yaml.encrypt(self.config, self.rsa_helper)

        decrypted = dbs.yaml.decrypt(encrypted, self.rsa_helper)

        encrypted.dump(encrypted_file)

        assert self.config == decrypted, \
            "decrypted dictionary is not equal original"

        return

    def test_encrypt_file(self):

        encrypted = dbs.yaml.encrypt(db_connectors_yaml, self.rsa_helper)
        decrypted = dbs.yaml.decrypt(encrypted, self.rsa_helper)

        encrypted.dump(encrypted_file)

        assert self.config == decrypted, \
            "decrypted dictionary is not equal original"

        return

    def test_decrypt_file(self):

        encrypted = dbs.yaml.encrypt(db_connectors_yaml, self.rsa_helper)

        encrypted.dump(encrypted_file)

        result = dbs.yaml.decrypt(encrypted_file, self.rsa_helper)

        assert result == self.config,\
            "decrypted dictionary is not equal original"

        return



if __name__ == "__main__":
    T = TestEncryptDecrypt()
    T.test_encrypt_dictionary()
    T.test_encrypt_file()
    T.test_decrypt_file()
