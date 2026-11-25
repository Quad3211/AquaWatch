"""Convert BattLeDIM to AquaWatch format. Same as `aquawatch battledim prepare`.

Kept so older docs and habits still work; prefer the `aquawatch` command.
"""

import sys

from aquawatch.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["battledim", "prepare", *sys.argv[1:]]))
