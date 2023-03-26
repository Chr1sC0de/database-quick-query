import re
import os
import yaml
import pathlib as pt
from typing import Tuple
from collections import OrderedDict
from . security.helpers import RSA
from . security.functions._yaml import decrypt
from triple_quote_clean import TripleQuoteCleaner
from . security.functions._functions import load_private_key


def get_connector_details() -> "dict[str]":

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


def parse_file(filepath: pt.Path) -> Tuple[str, str, "dbqq.connectors.Base"]:

    with open(filepath, "r") as f:
        query = f.read()

    found = re.findall("--!\s+(\w+)\/(.+)", query)

    assert len(found) > 0, "no connector string found"

    import dbqq

    module = dbqq

    name, connector_string = found[0]

    query = re.sub("--!\s+\w+\/.+\n+", "", query)

    for m in connector_string.split("."):
        module = getattr(module, m)

    return name, query, module


def tab(string, tab="    ", n=1):
    return "\n".join(
        [n*tab+s for s in string.split("\n")])


def tab2(string):
    return tab(string, n=2)


def in_databricks():
    return "DATABRICKS_RUNTIME_VERSION" in os.environ.keys()


class CommonTableExpression:

    def __init__(self):
        self.queries = OrderedDict()
        # self.queries[name] = query
        self.history = [self.queries]

    def add_query(self, name, query):
        self.queries[name] = query
        self.history.append(self.queries)

    def rollback(self, version_no):
        self.history = self.history[:(version_no+1)]
        self.queries = self.history[-1]

    def rollback_one(self):
        return self.rollback(len(self.history)-1)

    def generate(self):
        output = "with\n"
        for i, (name, query) in enumerate(self.queries.items()):
            if i == 0:
                output += f"{name} as (\n{tab(query)}\n)"
            else:
                output += f"\n,\n{name} as (\n{tab(query)}\n)"
        return output

    def __call__(self, query):
        return self.generate() + f"\n{query}"

    def __repr__(self) -> str:
        return self.generate()

    def __str__(self) -> str:
        return self.generate()
