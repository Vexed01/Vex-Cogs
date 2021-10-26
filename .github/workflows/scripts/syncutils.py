# copy the utils from https://github.com/Vexed01/vex-cog-utils to each cog in this repo
# this is currently triggered manually, may be changed in the future

import datetime
import shutil
from pathlib import Path

import git
from git import Repo

README_MD_TEXT = """## My utils

Hello there! If you're contributing or taking a look, everything in this folder
is synced from a master repo at https://github.com/Vexed01/vex-cog-utils by GitHub Actions -
so it's probably best to look/edit there.

---

Last sync at: {time}

Version: `{version}`

Commit: [`{commit}`](https://github.com/Vexed01/vex-cog-utils/commit/{commit})
"""

utils_repo_clone_location = Path("temp-utils-repo")
utils_repo = Repo.clone_from(
    "https://github.com/Vexed01/vex-cog-utils.git", utils_repo_clone_location
)

utils_location = utils_repo_clone_location / "vexutils"

with open(utils_location / "version.py") as fp:
    data = fp.read()
    curr_ver = data.split('"')[1]

readme = README_MD_TEXT.format(
    time=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z"),
    version=curr_ver,
    commit=utils_repo.head.commit,
)

with open(utils_location / "README.md", "w") as fp:
    fp.write(readme)

cog_folders = [
    "aliases",
    "anotherpingcog",
    "beautify",
    "betteruptime",
    "cmdlog",
    "github",
    "madtranslate",
    "stattrack",
    "status",
    "system",
    "timechannel",
    "wol",
]

for cog in cog_folders:
    destination = Path(cog) / "vexutils"
    if destination.exists():
        shutil.rmtree(destination)

    shutil.copytree(utils_location, destination)

utils_repo.close()
git.rmtree(utils_repo_clone_location)
