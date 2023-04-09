import subprocess
try:
    from . shared import private_key_file, public_key_file, key_folder
except ImportError:
    from shared import private_key_file, public_key_file, key_folder


def test_cli_write_keys():

    public_key_file.unlink(missing_ok=True)
    private_key_file.unlink(missing_ok=True)

    subprocess.run(
        f"dbqq-write-keys \
            -k 1024 \
            -l {key_folder} \
            -pbn public_key \
            -prn private_key \
            -f PEM \
        "
    )

    assert private_key_file.exists(), f"{private_key_file} does not exist"
    assert public_key_file.exists(), f"{public_key_file} does not exist"


if __name__ == "__main__":
    test_cli_write_keys()


"""
dbqq-write-keys -k 1024 -l C:/Users/cmamo/Documents/python/dbqq/.scratch/keys -pbn public_key -prn private_key -f PEM
"""