import re

from git import Repo

# hello person looking at my code
# i chose not to do releases as they are "repo-wide"... but then so are tags. tags just feel less
# sorta... invasive. idk.

TAG_MESSAGE = """
Created with GitHub Actions.

The changelog can be found at
https://vex-cogs.readthedocs.io/en/latest/changelog.html#{cogname}

This is an automatically created tag based of the following commit:
{commit}
"""

repo = Repo()  # repo in working dir

regex = re.compile(r"\[(\w+) (\d+\.\d+\.\d+)\]")

latest_commit = repo.head.commit.message
print("Most recent commit detected as: " + latest_commit)

match = regex.match(latest_commit)
if match is None or len(list(match.groups())) != 2:
    print("Most recent commit does not match regex, nothing to do.")
else:
    print("Commit matches regex. Creating and pushing new tag...")
    cog = match.group(1).lower()
    ver = match.group(2)
    tag_name = f"{cog}-{ver}"

    repo.create_tag(tag_name, message=TAG_MESSAGE.format(cogname=cog, commit=latest_commit))
    origin = repo.remote().push(f"refs/tags/{tag_name}")
    print(f"Pushed a new tag {tag_name}.")
