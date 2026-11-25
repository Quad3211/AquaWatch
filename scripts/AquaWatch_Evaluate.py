"""Compare every detector on a dataset. Same as `aquawatch evaluate`.

Kept so older docs and habits still work; prefer the `aquawatch` command.
"""

import sys

from aquawatch.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["evaluate", *sys.argv[1:]]))
