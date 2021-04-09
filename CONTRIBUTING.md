# Contributing to Vex-Cogs

Thanks for taking the time to look into contributing! Whether you'll open an issue or PR, or do something else, _everything_ is appreciated.

Not much else to say really, just this:

## Checks

When you open a PR, they'll be some basic checks to make sure the style is consistent and basic checking that nothing's broken.

Please also SPEAK TO ME either through an issue or in Discord (Vexed#3211) before making any medium/big changes.

This consists of: black, isort, flake8 and mypy.

The config files will let you run all of these without arguments.

```batch
python -m flake8 --ignore E501,F401,W503 .

You can run these locally to check everything's working using tox:

1. If you haven't already, install tox:

    ```batch
    pip install tox
    ```

2. Now run tox:

    ```batch
    tox
    ```
