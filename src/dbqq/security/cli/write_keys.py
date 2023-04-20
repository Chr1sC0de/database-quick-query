import argparse
import pathlib as pt
from dbqq.security.functions import get_keys, write_key


parser: argparse.ArgumentParser = argparse.ArgumentParser(
    description="generate public and private keys"
)

parser.add_argument(
    "--key_length", "-k", type=int, default=512, help="the length of th key"
)

parser.add_argument(
    "--location",
    "-l",
    type=pt.Path,
    default=".",
    help="the location to save the keys",
)

parser.add_argument(
    "--pb_key_name",
    "-pbn",
    type=str,
    default="public_key",
    help="the saved public key name",
)

parser.add_argument(
    "--pr_key_name",
    "-prn",
    type=str,
    default="private_key",
    help="the saved private key name",
)

parser.add_argument(
    "--format",
    "-f",
    type=str,
    default="DER",
    choices=["PEM", "DER"],
    help="The format the output the keys use \
        PEM for human readable DER for purely binary format",
)

parser.add_argument(
    "--poolsize", "-ps", type=int, default=2, help="number of cores to use"
)


def run():
    arguments = parser.parse_args()
    location = arguments.location
    save_format = arguments.format
    poolsize = arguments.poolsize

    pb_key_name, pr_key_name = (arguments.pb_key_name, arguments.pr_key_name)
    public_key, private_key = get_keys(
        key_length=arguments.key_length, poolsize=poolsize
    )

    for key, name in zip(
        (public_key, private_key), (pb_key_name, pr_key_name)
    ):
        key_file_name = location / ("%s.%s" % (name, save_format.lower()))

        write_key(key, key_file_name, format=save_format)


if __name__ == "__main__":
    run()
