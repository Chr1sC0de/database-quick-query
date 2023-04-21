import re
import pathlib as pt

import argparse

parser = argparse.ArgumentParser(
    description="Clean up all connection information"
)

parser.add_argument("-d", "--placeholder")

arguments = parser.parse_args()


def run():
    cwd = pt.Path(__file__).parent

    required_files = [
        f
        for f in (cwd / "../connectors").glob("*.py")
        if not f.name.startswith("_")
    ]

    for file in required_files:
        with open(file, "r") as f:
            content = f.read()

        new_content = "\n#! begin inject regex\n\n"

        new_content += "#! end inject regex"

        replaced = re.sub(
            r"\n#! begin inject regex.*?#! end inject regex",
            new_content,
            content,
            flags=re.S,
        )

        if replaced != content:
            with open(file, "w") as f:
                f.write(replaced)

    return


if __name__ == "__main__":
    run()
