# THIS IS ONLY HERE FOR... NO REASON!!!
# THIS IS COPIED TO THE gh-pages AS THE WORKFLOW CHECKS OUT THAT BRANCH
# WHICH MEANS IT CAN'T USE STUFF ON THIS BRANCH!!!
# I SHOULD JUST DELETE THIS...

import json
import re

from git import Repo

VER_FILE_LOCATION = "api/v1/version.json"

repo = Repo()  # repo in working dir

regex = re.compile(r"\[(\w+) (\d+\.\d+\.\d+)\]")

latest_commit = repo.head.commit.message
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
    with open(VER_FILE_LOCATION) as fp:
        json.dump(data, fp, index=4)
    repo.index.add([VER_FILE_LOCATION])
    repo.index.commit(f"Update {cog} ver to {ver}")
    repo.remote().push()
    print("Pushed update to the lastest version API.")


print("Script finished.")
