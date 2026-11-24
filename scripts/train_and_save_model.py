"""Train and save the demo Isolation Forest. Same as `aquawatch train`.

Kept so older docs and habits still work; prefer the `aquawatch` command.
"""
import sys

from aquawatch.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["train", *sys.argv[1:]]))
