"""Same as `aquawatch sizing`. Kept so older docs and habits still work."""

import sys

from aquawatch.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["sizing", *sys.argv[1:]]))
