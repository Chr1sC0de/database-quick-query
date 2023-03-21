import argparse
import pathlib as pt

from dbqq.security.functions._yaml import encrypt
from dbqq.security.helpers import RSA

parser = argparse.ArgumentParser()

parser.add_argument("file", type=pt.Path)

parser.add_argument(
    "--encrypted_file",
    "-ef",
    type    = pt.Path,
    default = None,
    help = "location to save encrypted file, if none save within current folder"
)

parser.add_argument(
    "public_key",
    type = pt.Path,
    help = "location of the public key"
)


def cli_encrypt_yaml():

    args        = parser.parse_args()

    public_key  = args.public_key

    config_file = args.file

    encrypted_file = args.encrypted_file

    rsa_helper = RSA.from_files(public_key, None)

    encrypted = encrypt(config_file, rsa_helper)

    if encrypted_file is None:
        encrypted_file = config_file.parent/"connections.dbqq"

    encrypted.dump(encrypted_file)

    return


if __name__ == "__main__":

    cli_encrypt_yaml()