import pytest
import yaml
from dbqq.security.functions import yaml as yamled
from dbqq.utils import get_connector_details
from dbqq.security import helpers

try:
    from .shared import db_connectors_yaml, key_folder, encrypted_file
except ImportError:
    from shared import db_connectors_yaml, key_folder, encrypted_file


@pytest.mark.depends(on=["test_cli_write_keys.py::test_cli_write_keys"])
def test_get_connector_details():
    rsa_helper = helpers.RSA.from_folder(key_folder)

    with open(db_connectors_yaml, "r") as f:
        config = yaml.safe_load(f)

    yamled.encrypt(db_connectors_yaml, rsa_helper).dump(encrypted_file)

    details = get_connector_details(dev_path=db_connectors_yaml)

    assert config == details, "incorrectly decrypted"

    return


if __name__ == "__main__":
    test_get_connector_details()
