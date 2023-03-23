import re
import os
import yaml
import pathlib as pt
from . security.helpers import RSA
from . security.functions._yaml import decrypt
from triple_quote_clean import TripleQuoteCleaner
from . security.functions._functions import load_private_key


def get_connector_details() -> dict[str]:

    connector_file = pt.Path(os.getenv("DBQQ_CONNECTORS"))
    assert connector_file.exists(), "%s does not exist" % connector_file

    if connector_file.suffix == ".yaml":

        with open(connector_file, "r") as f:
            connector_details = yaml.safe_load(f)

    elif connector_file.suffix == ".dbqq":

        private_key_file = pt.Path(os.getenv("DBQQ_PRIVATE_KEY"))
        assert private_key_file.exists(), "%s does not exist" % private_key_file

        private_key = load_private_key(private_key_file)
        rsa_helper = RSA(private_key=private_key)
        connector_details = decrypt(connector_file, rsa_helper)

    return connector_details


def inject_connector_classes(file_path: pt.Path, configs: dict, connector: str):

    make_connections = os.getenv('DBQQ_MAKE_CONNECTIONS', False)

    if make_connections.lower() == 'false':
        make_connections = False
    elif make_connections.lower() == 'true':
        make_connections = True
    else:
        raise ValueError(
            "DBQQ_MAKE_CONNECTIONS must be either \
                'true' of 'false' not %s" % make_connections
        )

    if make_connections:

        tqc = TripleQuoteCleaner()

        connector_configs = configs[connector]

        with open(file_path, "r") as f:
            content = f.read()

        new_content = "\n#! begin inject regex\n\n"

        for key in connector_configs.keys():

            new_content += f"""
                class {key}(_general_connector):
                    source: str = '{key}'
            """ >> tqc

            new_content += "\n\n"

        new_content += "#! end inject regex"

        replaced = re.sub(
            "\n#! begin inject regex.*?#! end inject regex",
            new_content,
            content,
            flags=re.S
        )

        if replaced != content:
            with open(file_path, "w") as f:
                f.write(replaced)
