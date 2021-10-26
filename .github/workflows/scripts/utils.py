# copy the utils from https://github.com/Vexed01/vex-cog-utils to each cog in this repo
# this is currently triggered manually, may be changed in the future

README_MD_TEXT = """## The utils package

Hello there! If you're contributing or taking a look, everything in this folder
is synced from a master repo at https://github.com/Vexed01/vex-cog-utils by GitHub Actions - 
so it's probably best to look/edit there.

---

Current utils version: ``{version}``

Last sync at: ``{time}``
"""

from git import Repo
from pathlib import Path

utils_repo_clone_location = Path("temp-utils-repo")

utils_repo = Repo.clone_from("https://github.com/Vexed01/vex-cog-utils.git", utils_repo_clone_location)

utils_location = utils_repo_clone_location / "vexcogutils"
