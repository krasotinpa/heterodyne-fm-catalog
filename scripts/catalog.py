#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Validate the catalog and build a release (index.json + ZIP).

    python3 scripts/catalog.py validate [--base origin/main]
    python3 scripts/catalog.py build OUT_DIR REVISION
"""
import argparse
import datetime
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGIONS = ROOT / "regions"

MAX_REGION_BYTES = 64 * 1024
MAX_STATIONS = 500
MAX_NAME = 80
MAX_REGIONS = 100
MAX_INDEX_BYTES = 32 * 1024
MAX_ZIP_BYTES = 8 * 1024 * 1024
FM_MIN_KHZ, FM_MAX_KHZ, FM_STEP_KHZ = 87500, 108000, 100  # same rule as the app's isSelectableFrequency

ID_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def is_date(s):
    try:
        return bool(DATE_RE.fullmatch(s)) and bool(datetime.date.fromisoformat(s))
    except (TypeError, ValueError):
        return False


def is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def check_name(name, what, errors):
    if not isinstance(name, str) or not name.strip() or len(name) > MAX_NAME:
        errors.append(f"{what}: name must be a non-blank string of at most {MAX_NAME} characters")


def validate_region(path):
    """Return a list of error strings for one region file."""
    errors = []
    raw = path.read_bytes()
    if len(raw) > MAX_REGION_BYTES:
        errors.append(f"file is larger than {MAX_REGION_BYTES} bytes")
    if b"\r" in raw or not raw.endswith(b"\n"):
        errors.append("file must use LF line endings and end with a newline")
    try:
        data = json.loads(raw.decode("utf-8"))
    except ValueError as e:
        return errors + [f"not valid UTF-8 JSON: {e}"]
    if not isinstance(data, dict) or data.get("schema") != 1 or not is_int(data.get("schema")):
        return errors + ["unknown schema (expected 1)"]
    if not is_date(data.get("revision")):
        errors.append("revision must be a date YYYY-MM-DD")
    region = data.get("region")
    rid = region.get("id") if isinstance(region, dict) else None
    if not isinstance(rid, str) or not ID_RE.fullmatch(rid):
        return errors + ["region.id must be lowercase latin letters, digits and hyphens"]
    if rid != path.stem:
        errors.append(f"region.id '{rid}' must match the file name '{path.stem}'")
    check_name(region.get("name"), "region", errors)
    source = data.get("source")
    if not (isinstance(source, dict) and all(isinstance(source.get(k), str) and source[k] for k in ("text", "url"))):
        errors.append("source must have non-empty text and url")
    stations = data.get("stations")
    if not isinstance(stations, list) or not stations:
        return errors + ["stations must be a non-empty list"]
    if len(stations) > MAX_STATIONS:
        errors.append(f"more than {MAX_STATIONS} stations")
    seen = set()
    for i, s in enumerate(stations):
        where = f"station #{i + 1}"
        if not isinstance(s, dict):
            errors.append(f"{where}: must be an object")
            continue
        sid = s.get("id")
        if not isinstance(sid, str) or not ID_RE.fullmatch(sid) or not sid.startswith(rid + "-"):
            errors.append(f"{where}: id must be lowercase, start with '{rid}-' and use only letters, digits and hyphens")
        elif sid in seen:
            errors.append(f"{where}: duplicate id '{sid}'")
        else:
            seen.add(sid)
        check_name(s.get("name"), where, errors)
        f = s.get("frequencyKhz")
        if s.get("band") != "FM":
            errors.append(f"{where}: band must be FM")
        if not is_int(f) or not FM_MIN_KHZ <= f <= FM_MAX_KHZ or (f - FM_MIN_KHZ) % FM_STEP_KHZ:
            errors.append(f"{where}: frequencyKhz {f!r} is not an FM frequency "
                          f"({FM_MIN_KHZ}..{FM_MAX_KHZ} kHz, step {FM_STEP_KHZ})")
    return errors


def region_files():
    return sorted(REGIONS.glob("*.json"))


def region_revision(raw):
    try:
        return json.loads(raw)["revision"]
    except (ValueError, KeyError, TypeError):
        return None


def check_revision_bumped(base):
    """A changed region file must carry a new revision."""
    errors = []
    for path in region_files():
        rel = path.relative_to(ROOT).as_posix()
        old = subprocess.run(["git", "show", f"{base}:{rel}"], cwd=ROOT, capture_output=True)
        if old.returncode == 0 and old.stdout != path.read_bytes() \
                and region_revision(old.stdout) == region_revision(path.read_bytes()):
            errors.append(f"{rel}: file changed but revision was not changed")
    return errors


def validate_all(base=None):
    errors = []
    files = region_files()
    if not files:
        errors.append("no region files")
    if len(files) > MAX_REGIONS:
        errors.append(f"more than {MAX_REGIONS} regions")
    for path in files:
        errors += [f"{path.name}: {e}" for e in validate_region(path)]
    if base:
        errors += check_revision_bumped(base)
    return errors


def build(out, revision):
    if not is_date(revision):
        sys.exit("revision must be a date YYYY-MM-DD")
    errors = validate_all()
    if errors:
        sys.exit("\n".join(errors))
    out.mkdir(parents=True, exist_ok=True)
    regions = []
    for path in region_files():
        raw = path.read_bytes()
        data = json.loads(raw)
        regions.append({"id": data["region"]["id"], "name": data["region"]["name"], "file": path.name,
                        "sha256": hashlib.sha256(raw).hexdigest(), "revision": data["revision"]})
        (out / path.name).write_bytes(raw)
    index = (json.dumps({"schema": 1, "revision": revision, "regions": regions},
                        ensure_ascii=False, indent=2) + "\n").encode()
    if len(index) > MAX_INDEX_BYTES:
        sys.exit(f"index.json is larger than {MAX_INDEX_BYTES} bytes")
    (out / "index.json").write_bytes(index)
    archive = out / f"catalog-{revision}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("index.json", index)
        for r in regions:
            z.write(out / r["file"], r["file"])
    if archive.stat().st_size > MAX_ZIP_BYTES:
        sys.exit(f"ZIP is larger than {MAX_ZIP_BYTES} bytes")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("--base", help="git ref to compare region revisions with")
    b = sub.add_parser("build")
    b.add_argument("out", type=Path)
    b.add_argument("revision")
    a = p.parse_args()
    if a.cmd == "build":
        build(a.out, a.revision)
        return
    errors = validate_all(a.base)
    print("\n".join(errors) if errors else "OK")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
