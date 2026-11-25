"""Regenerate data/simulated/ with WNTR. Same as `aquawatch simulate`.

Kept so older docs and habits still work; prefer the `aquawatch` command.
"""

import sys

from aquawatch.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["simulate", *sys.argv[1:]]))
