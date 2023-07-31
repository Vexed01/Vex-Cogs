# Contributing to Vex-Cogs

Thanks for taking the time to look into contributing! Whether you'll open an issue or PR, or do something else, _everything_ is appreciated.

To avoid wasting time, it's sometimes best to speak to me in Discord (`@vexingvexed`) or create an Issue before making non-trivial Pull Requests.

Not much else to say really, just this:

## Checks

When you open a PR, they'll be some basic checks to make sure the style is consistent so other checks that nothing's broken.

**You do not need to set up pre-commit or similar locally for smaller PRs**, as GitHub Actions will let you know if there's an issue with details in the logs. However, you may need to use black or isort.

Pyright (or Pylance if you're using VS Code) is used for type checking.

The config files in the repo will let you run any style checks and type checking without arguments.

## pre-commit

I've set up pre-commit. This will ensure your code conforms to the correct style when you commit changes.

To use it, simply run this:

        pip install pre-commit

        pre-commit install

It will now automatically run on every commit.

## tox

If you would like, you can run (almost) the full test suite using `tox`

1. If you haven't already, install tox:

        pip install tox

2. Now run tox:

        tox
