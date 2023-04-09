from dbqq.security.helpers import RSA

try:
    from . shared import private_key_file, public_key_file, key_folder
except ImportError:
    from shared import private_key_file, public_key_file, key_folder


class TestRSAHelper:

    message = "here is a message to encrypt"

    def _encrypt_decrypt(self, helper:RSA):

        encrypted_message = helper.encrypt(self.message)
        decrypted_message = helper.decrypt(encrypted_message)
        assert self.message == decrypted_message, "message was not properly decrypted"


    def test_from_files(self):

        rsa_helper = RSA.from_files(public_key_file, private_key_file)
        self._encrypt_decrypt(rsa_helper)
        return

    def test_from_folder(self):

        rsa_helper = RSA.from_folder(key_folder)
        self._encrypt_decrypt(rsa_helper)
        return




if __name__ == "__main__":
    T = TestRSAHelper()
    T.test_from_files()
    T.test_from_folder()