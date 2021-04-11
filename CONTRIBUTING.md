# Contributing to Vex-Cogs

Thanks for taking the time to look into contributing! Whether you'll open an issue or PR, or do something else, _everything_ is appreciated.

Not much else to say really, just this:

## Checks

When you open a PR, they'll be some basic checks to make sure the style is consistent and basic checking that nothing's broken.

Please also SPEAK TO ME either through an issue or in Discord (Vexed#3211) before making any medium/big changes.

This consists of: black, isort, flake8 and mypy.

The config files will let you run all of these without arguments.

> ### **Warning for MyPy**
>
> You will need to install these stubs: ``pip install -U discord.py-stubs pandas-stubs``
>
> You ``mypy .`` sometimes errors. It's pretty random.
>
> Try again (trust me, that sometimes makes it work) or do this to run it "repo-wide":
>
>       mypy aliases anotherpingcog betteruptime github status system
>
> This is what tox and the PR cheks run. You could also only run mypy on the cog you're contributing to or use it in your editor - that _seems_ to work.
>
> This does appear to be on the GitHub for mypy in a few separate issues.
>
> If the error still persists, you might want to try deleting the mypy cache folder (in the working dir).

You can run these locally to check everything's working using tox:

1. If you haven't already, install tox:

        pip install tox

2. Now run tox:

        tox
