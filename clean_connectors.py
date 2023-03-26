import re
import pathlib as pt


def main():

    cwd = pt.Path(__file__).parent

    required_files = [
        f for f in(cwd/"src/dbqq/connectors").glob("*.py") if not f.name.startswith('_')
    ]

    for file in required_files:

        with open(file, "r") as f:
            content = f.read()

        new_content = "\n#! begin inject regex\n\n"

        new_content += "#! end inject regex"

        replaced = re.sub(
            "\n#! begin inject regex.*?#! end inject regex",
            new_content,
            content,
            flags=re.S
        )

        if replaced != content:
            with open(file, "w") as f:
                f.write(replaced)

    return


if __name__ == "__main__":
    main()