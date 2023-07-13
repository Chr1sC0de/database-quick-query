import os
import pathlib as pt
import re
from collections import OrderedDict
from typing import Dict

import yaml
from triple_quote_clean import TripleQuoteCleaner

from .security.functions._functions import load_private_key
from .security.functions._yaml import decrypt
from .security.helpers import RSA
from .data import parsed


def get_ssm_connector_details(name: str, region: str = "ap-southeast-2"):
    import boto3
    import yaml

    client = boto3.client("ssm", region_name=region)
    parameter = client.get_parameter(Name=name, WithDecryption=True)[
        "Parameter"
    ]["Value"]
    return yaml.safe_load(parameter)


def get_connector_details(dev_path: pt.Path = None) -> Dict[str, str]:
    ssm_name = os.getenv("DBQQ_SSM_NAME", None)
    ssm_region = os.getenv("DBQQ_SSM_REGION", "ap-southeast-2")
    connector_path = os.getenv("DBQQ_CONNECTORS", None)
    if dev_path is not None:
        connector_file = pt.Path(dev_path)
    elif ssm_name is not None:
        return get_ssm_connector_details(ssm_name, region=ssm_region)
    else:
        try:
            connector_file = pt.Path(connector_path)
        except TypeError as type_error:
            print("DBQQ_CONNECTORS environment variable not set")
            raise type_error
    assert connector_file.exists(), "%s does not exist" % connector_file

    if connector_file.suffix == ".yaml":
        with open(connector_file, "r") as f:
            connector_details = yaml.safe_load(f)

    elif connector_file.suffix == ".dbqq":
        private_key_file = pt.Path(os.getenv("DBQQ_PRIVATE_KEY"))
        assert private_key_file.exists(), (
            "%s does not exist" % private_key_file
        )

        private_key = load_private_key(private_key_file)
        rsa_helper = RSA(private_key=private_key)
        connector_details = decrypt(connector_file, rsa_helper)

    return connector_details


def inject_connector_classes(
    file_path: pt.Path, configs: dict, connector: str
):
    tqc = TripleQuoteCleaner()

    connector_configs = configs[connector]

    with open(file_path, "r") as f:
        content = f.read()

    new_content = "\n#! begin inject regex\n\n"

    for key in connector_configs.keys():
        new_content += (
            f"""
                class {key}(_general_connector):
                    source: str = '{key}'
            """
            >> tqc
        )

        new_content += "\n\n"

    new_content += "#! end inject regex"

    replaced = re.sub(
        r"\n#! begin inject regex.*?#! end inject regex",
        new_content,
        content,
        flags=re.S,
    )

    if replaced != content:
        with open(file_path, "w") as f:
            f.write(replaced)


def parse_file(filepath: pt.Path, cache: bool = False) -> parsed.sql.Base:
    def _get_module(connector_string):
        import dbqq

        module = dbqq
        for m in connector_string.split("."):
            module = getattr(module, m)
        return module

    def _parse_with_cache_and_date(found, query):
        name, cache_folder, date, connector_string = found[0]
        cache_folder = pt.Path(cache_folder)
        date_lower_bound = eval("import datetime, timedelta;" + date)
        module = _get_module(connector_string)
        return parsed.sql.NameQueryModuleCacheDate(
            name, query, module, cache_folder, date_lower_bound
        )

    def _parse_with_cache(found, query):
        name, cache_folder, connector_string = found[0]
        cache_folder = pt.Path(cache_folder)
        module = _get_module(connector_string)
        return parsed.sql.NameQueryModuleCache(
            name, query, module, cache_folder
        )

    def _parse_no_cache(found, query):
        name, connector_string = found[0]
        module = _get_module(connector_string)
        return parsed.sql.NameQueryModule(name, query, module)

    with open(filepath, "r") as f:
        query = f.read()

    found_cache_with_date = re.findall(
        r"--!\s+(\w+)\/['\"](.+)['\"]\/(.+?)\/(.+)", query
    )
    found_cache = re.findall(r"--!\s+(.+?)\/['\"](.+)['\"]\/(.+)", query)
    found_no_cache = re.findall(r"--!\s+(\w+)\/(.+)", query)

    query = re.sub(r"--!.+\n", "", query)

    if len(found_cache_with_date) > 0:
        return _parse_with_cache_and_date(found_cache_with_date, query)
    elif len(found_cache) > 0:
        return _parse_with_cache(found_cache, query)
    elif len(found_no_cache) > 0:
        return _parse_no_cache(found_no_cache, query)
    else:
        raise "No connector string found"


def tab(string: str, tab: str = "    ", n: int = 1):
    return "\n".join([n * tab + s for s in string.split("\n")])


def tab2(string):
    return tab(string, n=2)


def in_databricks():
    return "DATABRICKS_RUNTIME_VERSION" in os.environ.keys()


class CommonTableExpression:
    def __init__(self):
        self.queries = OrderedDict()
        self.history = [self.queries]

    def add_query(self, name: str, query: str):
        self.queries[name] = query
        self.history.append(self.queries)
        return self

    def rollback(self, version_no: int):
        self.history = self.history[: (version_no + 1)]
        self.queries = self.history[-1]
        return self

    def rollback_one(self) -> "CommonTableExpression":
        return self.rollback(len(self.history) - 1)

    def generate(self) -> str:
        output = "with\n"
        for i, (name, query) in enumerate(self.queries.items()):
            if i == 0:
                output += f"{name} as (\n{tab(query)}\n)"
            else:
                output += f"\n,\n{name} as (\n{tab(query)}\n)"
        return output

    def __call__(self, query: str) -> str:
        return self.generate() + f"\n{query}"

    def __repr__(self) -> str:
        return self.generate()

    def __str__(self) -> str:
        return self.generate()
