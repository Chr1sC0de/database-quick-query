import re
import rsa
import pathlib as pt
from dataclasses import dataclass
from dbqq.security.functions import load_private_key, load_public_key


@dataclass
class RSA:
    public_key: rsa.PublicKey = None
    private_key: rsa.PrivateKey = None

    @classmethod
    def from_folder(
        cls,
        folder: pt.Path,
        pub_reg: str = r".*public.*\.%s",
        prv_reg: str = r".*private.*\.%s",
    ) -> "RSA":
        key_files = tuple(folder.glob("*"))
        key_files = [k for k in key_files if k.suffix in [".pem", ".der"]]

        for s_format in ["pem", "der"]:
            public_key_file = [
                f
                for f in key_files
                if re.match(pub_reg % s_format, f.name) is not None
            ]

            if len(public_key_file) > 0:
                public_key_file = public_key_file[0]
            else:
                public_key_file = None

            private_key_file = [
                f
                for f in key_files
                if re.match(prv_reg % s_format, f.name) is not None
            ]

            if len(private_key_file) > 0:
                private_key_file = private_key_file[0]
            else:
                private_key_file = None

            if any(
                [k is not None for k in (public_key_file, private_key_file)]
            ):
                return cls.from_files(public_key_file, private_key_file)

        raise FileNotFoundError(
            f"No public and private keys found in {key_files}"
        )

    @classmethod
    def from_files(
        cls, pub_file: pt.Path = None, prv_file: pt.Path = None
    ) -> "RSA":
        if pub_file is not None:
            public_key = load_public_key(pub_file)
        else:
            public_key = None

        if prv_file is not None:
            private_key = load_private_key(prv_file)
        else:
            private_key = None

        return cls(public_key, private_key)

    def encrypt(self, input_string: str) -> bytes:
        encrypted = rsa.encrypt(input_string.encode("utf8"), self.public_key)
        return encrypted

    def decrypt(self, input_string: bytes) -> str:
        decrypted = rsa.decrypt(input_string, self.private_key).decode("utf8")
        return decrypted
