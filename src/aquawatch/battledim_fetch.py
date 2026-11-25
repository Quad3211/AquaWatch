"""Download the BattLeDIM 2020 benchmark files AquaWatch uses, and verify them.

Source: Zenodo record 4017659 (DOI 10.5281/zenodo.4017659), licence CC BY 4.0.
Vrachimis et al., "Dataset of BattLeDIM: Battle of the Leakage Detection and
Isolation Methods". Files go to data/external/battledim/ (gitignored, never
committed). Each file is checked against the MD5 published by Zenodo;
already-downloaded files that match are skipped.

    aquawatch battledim fetch
"""

from __future__ import annotations

import hashlib
import urllib.request
from pathlib import Path

from aquawatch import config

OUT_DIR = config.BATTLEDIM_DIR
URL = "https://zenodo.org/api/records/4017659/files/{name}/content"

# filename -> MD5 published in the Zenodo record (about 70 MB in total)
FILES = {
    "README.txt": "7ad5cdc2eebfe78197a3412e80d07ddc",
    "dataset_configuration.yaml": "48486401f5b4d0447023f5ce5d242c52",
    "L-TOWN.inp": "bfbb16b8b463e0576200ba6ad360f68e",
    "2018_SCADA_Flows.csv": "d0602c06946b46287e956f007e4264ee",
    "2019_SCADA_Flows.csv": "28fc99fdcbf80fcd26079e7fe602d6dc",
    "2018_SCADA_Pressures.csv": "d389d8541350c19ff0bfc6b80f246d35",
    "2019_SCADA_Pressures.csv": "5ea1e46d3f2f0a89a3f98d6fd39a851d",
    "2018_Leakages.csv": "c2c5fab90420da44f02e29775050abfe",
    "2019_Leakages.csv": "e1f0a43683813a90a9fec8562dde599b",
}


def md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


ATTEMPTS = 12  # each attempt resumes where the last one stopped


def download(name: str, partial: Path) -> None:
    """Fetch one file into ``partial``, resuming a previous partial download.

    Uses an HTTP Range request when part of the file is already on disk, so a
    flaky connection only costs the bytes it lost. Raises if the connection
    ends early; calling again picks up from there.
    """
    have = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "aquawatch-fetch"}
    if have:
        headers["Range"] = f"bytes={have}-"
    request = urllib.request.Request(URL.format(name=name), headers=headers)
    with urllib.request.urlopen(request, timeout=120) as response:
        resumed = response.status == 206
        mode = "ab" if resumed else "wb"
        remaining = int(response.headers.get("Content-Length") or 0)
        total = (have if resumed else 0) + remaining
        with partial.open(mode) as fh:
            while chunk := response.read(1 << 20):
                fh.write(chunk)
    got = partial.stat().st_size
    if total and got != total:
        raise OSError(f"connection closed after {got:,} of {total:,} bytes")


def fetch() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    failed = []
    for name, expected in FILES.items():
        target = OUT_DIR / name
        if target.exists() and md5(target) == expected:
            print(f"ok (cached)  {name}")
            continue
        partial = target.with_suffix(target.suffix + ".part")
        for attempt in range(1, ATTEMPTS + 1):
            have = partial.stat().st_size if partial.exists() else 0
            print(f"downloading  {name} (attempt {attempt}/{ATTEMPTS}, have {have:,} bytes) ...", flush=True)
            try:
                download(name, partial)
            except OSError as exc:  # timeouts, dropped connections
                print(f"  network error: {exc}")
                continue
            if md5(partial) == expected:
                partial.replace(target)
                print(f"ok           {name} ({target.stat().st_size / 1e6:.1f} MB)")
                break
            print(f"  checksum mismatch after {partial.stat().st_size:,} bytes; starting this file again")
            partial.unlink()
        else:
            partial.unlink(missing_ok=True)
            failed.append(name)
            print(f"FAILED       {name}: not saved")
    if failed:
        print(f"\n{len(failed)} file(s) failed verification: {failed}")
        return 1
    print(f"\nAll {len(FILES)} files verified in {OUT_DIR}")
    return 0
