import pathlib as pt
import os

cwd              = pt.Path(__file__).parent
key_folder       = pt.Path(os.getenv("DB_CONNECTOR_KEY_FOLDER"))
encrypted_file   = pt.Path(os.getenv("DB_CONNECTIONS_ENCRYPTED"))
public_key_file  = key_folder/"public_key.pem"
private_key_file = key_folder/"private_key.pem"

db_connectors_yaml = os.getenv("DB_CONNECTOR_CONFIG")

if not key_folder.exists():
    key_folder.mkdir()
