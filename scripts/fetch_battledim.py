"""Same as `aquawatch battledim fetch`. Kept so older docs and habits still work."""
import sys

from aquawatch.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["battledim", "fetch", *sys.argv[1:]]))
