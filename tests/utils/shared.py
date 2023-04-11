import pathlib as pt

cwd = pt.Path(__file__).parent

key_folder = cwd / "../keys"
db_connectors_yaml = cwd / "../dummy.yaml"
encrypted_file = cwd / "../dummy.dbqq"

public_key_file = key_folder / "public_key.pem"
private_key_file = key_folder / "private_key.pem"


if not key_folder.exists():
    key_folder.mkdir()
