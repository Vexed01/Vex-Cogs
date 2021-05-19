# This is triggered by a workflow (release.yml) on the main branch which checks out this branch

import json
import os
import re

from git import Repo

VER_FILE_LOCATION = "api/v1/versions.json"

repo = Repo()  # repo in working dir

regex = re.compile(r"\[(\w+) (\d+\.\d+\.\d+)\]")

latest_commit = os.environ.get("LATEST_COMMIT")
print("Most recent commit detected as: " + latest_commit)

match = regex.match(latest_commit)
if match is None or len(list(match.groups())) != 2:
    print("Most recent commit does not match regex, nothing to do.")
else:
    print("Commit matches regex.")
    cog = match.group(1).lower()
    if cog == "apc":
        cog = "anotherpingcog"
    ver = match.group(2)

    print("Updating latest version API on GitHub pages...")
    with open(VER_FILE_LOCATION) as fp:
        data = json.load(fp)
    data["cogs"][cog] = ver
    with open(VER_FILE_LOCATION, "w") as fp:
        json.dump(data, fp, indent=4)
    repo.git.add(update=True)
    repo.index.commit("Automated version update")
    repo.remote().push()
    print("Made changes to files.")


print("Script finished.")
