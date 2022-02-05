import datetime
import re
import sys
from pathlib import Path

COGS = [
    "aliases",
    "anotherpingcog",
    "beautify",
    "betteruptime",
    "buttonpoll",
    "birthday",
    "calc",
    "caseinsensitive",
    "channeltrack",
    "cmdlog",
    "covidgraph",
    "github",
    "ghissues",
    "madtranslate",
    "stattrack",
    "status",
    "system",
    "timechannel",
    "wol",
]

UPDATE_LEVELS = ["major", "minor", "patch"]

VER_REGEX = r".*__version__ = \"(\d)\.(\d)\.(\d)\".*"

DOCS_REGEX = r"({}\n=*\n\n)"


def bump(cogname: str, update_level: str):
    if cogname == "status":
        to_open = Path(__file__).parent / "status" / "core" / "core.py"
    else:
        to_open = Path(__file__).parent / cogname / f"{cogname}.py"

    with open(to_open, "r") as fp:
        file_data = fp.read()

    match = re.match(VER_REGEX, file_data, flags=re.S)
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

    old = ".".join(str(i) for i in old_ver)
    new = ".".join(str(i) for i in new_ver)

    new_data = file_data.replace(old, new)

    with open(to_open, "w") as fp:
        fp.write(new_data)

    return new


def changelog(cogname: str, new_ver: str):
    stars = "*" * (len(new_ver) + 4)  # backticks
    date = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    extra_changelog = f"{stars}\n``{new_ver}``\n{stars}\n\n{date}\n\n"
    print(
        "It's now time to write the changelog. Input each bullet point separately. Enter a blank "
        "entry to finish."
    )
    while True:
        new_bullet = input("- ")
        if not new_bullet:
            break
        extra_changelog += f"- {new_bullet}\n"

    to_open = Path(__file__).parent / "docs" / "changelog.rst"

    with open(to_open, "r") as fp:
        file_data = fp.read()

    match = re.sub(
        DOCS_REGEX.format(cogname), r"\1" + extra_changelog + r"\n", file_data, flags=re.I
    )

    with open(to_open, "w") as fp:
        fp.write(match)

    print("Changelog updated.")


args = sys.argv
if len(args) != 3 or args[1] not in COGS or args[2] not in UPDATE_LEVELS:
    print(
        "You must use the format bump <cog> <level>\n<cog> is not dynamic\n"
        "<level> must be patch, minor or major."
    )
else:
    new = bump(args[1], args[2])
    if new:
        changelog(args[1], new)
        print(f"New version: {new}")
