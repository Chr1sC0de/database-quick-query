import argparse
import pathlib as pt

try:
    from .. import connectors
except ImportError:
    from dbqq import connectors


class ArgumentData:
    file: pt.Path
    rows: str
    show_index: bool


parser = argparse.ArgumentParser(
    description="Run a query directly from an file"
)
parser.add_argument("file", type=pt.Path, help="*.sql file to be run")
parser.add_argument(
    "-n",
    "--rows",
    type=str,
    default="50",
    help="The total number of rows to show, specify 'all' to show all",
)
parser.add_argument(
    "-i",
    "--show_index",
    type=int,
    default=0,
    help="Whether or not to show the dataframes indexes. 0 for don't show 1 to show",
    choices=[0, 1],
)


def run():
    arguments: ArgumentData
    connection: connectors.Base
    index: bool

    arguments = parser.parse_args()

    file = arguments.file
    rows = arguments.rows
    index = bool(arguments.show_index)

    connection, query = connectors.from_file(file)

    results = connection(query)

    if rows == "all":
        print(results.collect().to_pandas().to_markdown(index=index))
    else:
        print(results.fetch(int(rows)).to_pandas().to_markdown(index=index))

    return


if __name__ == "__main__":
    run()
