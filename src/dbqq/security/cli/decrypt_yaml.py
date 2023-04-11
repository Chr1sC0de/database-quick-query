import argparse
import pathlib as pt

import yaml

from dbqq.security.functions._yaml import decrypt
from dbqq.security.helpers import RSA

parser = argparse.ArgumentParser(
    description="decrypt encrypted configuration file"
)

parser.add_argument("file", type=pt.Path, help="file to decrypt")

parser.add_argument(
    "private_key", type=pt.Path, help="location of the private key"
)

parser.add_argument(
    "--decrypted_file",
    "-l",
    type=pt.Path,
    default=None,
    help="location to save decrypted file, if none save within current folder",
)


def run():
    args = parser.parse_args()

    private_key = args.private_key

    config_file = args.file

    decrypted_file = args.decrypted_file

    rsa_helper = RSA.from_files(None, private_key)

    decrypted = decrypt(config_file, rsa_helper)

    if decrypted_file is None:
        decrypted_file = config_file.parent / "config.yaml"

    with open(decrypted_file, "w") as f:
        f.write(yaml.dump(decrypted))

    return


if __name__ == "__main__":
    run()
