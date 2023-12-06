import pathlib as pt
from argparse import ArgumentParser
from ..utils import get_connector_details, inject_connector_classes

parser = ArgumentParser(description="Initialize the connections")

cwd = pt.Path(__file__).parent

connector_dir = cwd / "../connectors"


def run():
    _ = parser.parse_args()

    configs = get_connector_details()

    for filename in ["databricks", "mssql", "oracle", "redshift"]:
        try:
            inject_connector_classes(
                connector_dir / ("%s.py" % filename), configs, filename
            )
            print(
                "Connection details found for ",
                filename,
                "generating connections",
            )
            print(
                "Finished generating connection details found for ",
                filename,
            )
        except KeyError:
            print("No", filename, "connection details found, skipping")

    return


if __name__ == "__main__":
    run()
