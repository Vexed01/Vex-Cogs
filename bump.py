import re
import sys
from pathlib import Path

COGS = [
    "aliases",
    "anotherpingcog",
    "beautify",
    "betteruptime",
    "cmdlog",
    "github",
    "status",
    "system",
    "timechannel",
]

UPDATE_LEVELS = ["major", "minor", "patch"]

REGEX = r".*__version__ = \"(\d)\.(\d)\.(\d)\".*"


def bump(cogname: str, update_level: str) -> None:
    if cogname == "status":
        to_open = Path(__file__).parent / "status" / "core" / "core.py"
    else:
        to_open = Path(__file__).parent / cogname / f"{cogname}.py"

    with open(to_open, "r") as fp:
        file_data = fp.read()

    match = re.match(REGEX, file_data, flags=re.S)
    if match is None or len(match.groups()) != 3:
        print("Something doesn't look right with that file.")
        return

    old_ver = [int(match.group(1)), int(match.group(2)), int(match.group(3))]

    if update_level == "major":
        new_ver = [old_ver[0] + 1, 0, 0]
    elif update_level == "minor":
        new_ver = [old_ver[0], old_ver[1] + 1, 0]
    elif update_level == "patch":
        new_ver = [old_ver[0], old_ver[1], old_ver[2] + 1]
    else:
        print("hey you broke the code")
        return

    old = ".".join([str(i) for i in old_ver])
    new = ".".join([str(i) for i in new_ver])

    print(f"Old version: {old}\nNew version: {new}")

    new_data = file_data.replace(old, new)

    with open(to_open, "w") as fp:
        fp.write(new_data)


args = sys.argv
print(args)
if len(args) != 3 or args[1] not in COGS or args[2] not in UPDATE_LEVELS:
    print(
        "You must use the format bump <cog> <level>\n<cog> is not dynamic\n"
        "<level> must be patch, minor or major."
    )
else:
    bump(args[1], args[2])
