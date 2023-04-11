import pathlib as pt
from typing import Tuple

import rsa


def get_keys(
    key_length: int = 1024, poolsize: int = 2
) -> Tuple[rsa.PublicKey, rsa.PrivateKey]:
    public_key, private_key = rsa.newkeys(key_length, poolsize=poolsize)

    return public_key, private_key


def write_key(
    key: rsa.key.AbstractKey, target: pt.Path, format: str = "pem"
) -> None:
    target = pt.Path(target)
    with open(target, "wb") as f:
        f.write(key.save_pkcs1(format=format.upper()))


def load_public_key(source: pt.Path) -> rsa.PublicKey:
    with open(source, "rb") as f:
        public_key = rsa.PublicKey.load_pkcs1(
            f.read(), format=source.suffix.upper().strip(".").upper()
        )
    return public_key


def load_private_key(source: pt.Path) -> rsa.PrivateKey:
    with open(source, "rb") as f:
        private_key = rsa.PrivateKey.load_pkcs1(
            f.read(), format=source.suffix.upper().strip(".").upper()
        )
    return private_key
