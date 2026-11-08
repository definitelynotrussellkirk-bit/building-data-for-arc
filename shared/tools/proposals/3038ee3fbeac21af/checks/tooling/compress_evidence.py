"""Lossless checks/ JSON compression with retained raw originals and restoration.

Compress after checks finish:
  python checks/tooling/compress_evidence.py compress --work WORK \
    --raw-archive OUTER/evidence-raw --map checks/COMPRESSION-MAP.json
Restore into a fresh inspection directory, leaving the compact package alone:
  python checks/tooling/compress_evidence.py restore --work WORK \
    --map checks/COMPRESSION-MAP.json --dest FRESH_INSPECTION_WORK

Only regular files under checks/ are eligible. Existing destinations or maps
are never replaced. Compression records hashes before any source mutation.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import os
import shutil
import sys
import uuid

SCHEMA = "arcpuzzles-lossless-evidence-map-v1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def safe_absolute(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f"Symlink path forbidden: {part}")
    return path.resolve()


def under(root, name):
    value = PurePosixPath(name)
    if (not name.startswith("checks/") or value.is_absolute() or ".." in value.parts
            or "\\" in name or "\0" in name or value.as_posix() != name):
        raise ValueError(f"Expected safe checks-relative path: {name!r}")
    return safe_absolute(root.joinpath(*value.parts))


def atomic_new(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with temporary.open("xb") as output:
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        os.link(temporary, path)  # atomic claim; cannot overwrite an existing path
    finally:
        if temporary.exists():
            temporary.unlink()


def update_map(path, value):
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with temporary.open("x") as output:
            json.dump(value, output, indent=2, sort_keys=True)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)  # updates only the map claimed by this invocation
    finally:
        if temporary.exists():
            temporary.unlink()


def compress(args):
    root, archive = safe_absolute(args.work), safe_absolute(args.raw_archive)
    checks = safe_absolute(root / "checks")
    if archive == checks or checks in archive.parents:
        raise ValueError("Raw archive must be outside WORK/checks")
    map_path = under(root, args.map)
    if map_path.exists():
        raise FileExistsError(f"Map already exists: {map_path}")
    if args.path:
        names = sorted(set(args.path))
    else:
        names = []
        for path in checks.rglob("*"):
            if path.is_symlink():
                raise ValueError(f"Symlink evidence forbidden: {path}")
            if path.is_file() and path.suffix == ".json" and path.stat().st_size >= args.threshold:
                names.append(path.relative_to(root).as_posix())
    rows = []
    for name in names:
        source = under(root, name)
        destination = under(root, name + ".gz")
        retained = under(archive, name)
        if source == map_path or source.suffix != ".json" or not source.is_file():
            raise ValueError(f"Expected regular JSON evidence: {name}")
        if destination.exists() or retained.exists():
            raise FileExistsError(f"Compression/archive collision: {name}")
        raw = source.read_bytes()
        compressed = gzip.compress(raw, compresslevel=9, mtime=0)
        if gzip.decompress(compressed) != raw:
            raise ValueError(f"Compression round trip failed: {name}")
        rows.append({"original_path": name, "original_bytes": len(raw), "original_sha256": sha(raw),
                     "compressed_path": name + ".gz", "compressed_bytes": len(compressed),
                     "compressed_sha256": sha(compressed), "retained_raw_path": str(retained),
                     "state": "planned"})
    value = {"schema": SCHEMA, "status": "in_progress", "work_directory": str(root),
             "raw_archive": str(archive), "policy": "gzip level 9, mtime 0; exact originals retained",
             "restore_command": [sys.executable, "checks/tooling/compress_evidence.py", "restore",
                "--work", str(root), "--map", args.map, "--dest", "FRESH_INSPECTION_WORK"],
             "files": rows}
    atomic_new(map_path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())
    try:
        for row in rows:
            source = under(root, row["original_path"])
            destination = under(root, row["compressed_path"])
            retained = safe_absolute(row["retained_raw_path"])
            raw = source.read_bytes()
            if sha(raw) != row["original_sha256"]:
                raise ValueError(f"Evidence changed after inventory: {source}")
            compressed = gzip.compress(raw, compresslevel=9, mtime=0)
            atomic_new(destination, compressed)
            restored = gzip.decompress(destination.read_bytes())
            if sha(restored) != row["original_sha256"] or len(restored) != row["original_bytes"]:
                raise ValueError(f"Stored compression verification failed: {source}")
            row["state"] = "compressed_verified"
            update_map(map_path, value)
            atomic_new(retained, raw)
            shutil.copystat(source, retained, follow_symlinks=False)
            if sha(retained.read_bytes()) != row["original_sha256"]:
                raise ValueError(f"Retained original verification failed: {retained}")
            row["state"] = "raw_archived_verified"
            update_map(map_path, value)
            if sha(source.read_bytes()) != row["original_sha256"]:
                raise ValueError(f"Evidence changed before archival move: {source}")
            source.unlink()  # both verified byte-identical copies now exist
            row["state"] = "complete"
            update_map(map_path, value)
        value["status"] = "complete"
        update_map(map_path, value)
    except Exception as exc:
        value.update(status="failed", error=str(exc))
        update_map(map_path, value)
        raise
    print(f"Compressed {len(rows)} files; map: {map_path}")


def restore(args):
    root, destination = safe_absolute(args.work), safe_absolute(args.dest)
    value = json.loads(under(root, args.map).read_text())
    if value.get("schema") != SCHEMA or not isinstance(value.get("files"), list):
        raise ValueError("Invalid compression map")
    planned, seen = [], set()
    for row in value["files"]:
        name = row["original_path"]
        if name in seen or row["compressed_path"] != name + ".gz":
            raise ValueError("Duplicate or mismatched compression map path")
        seen.add(name)
        target = under(destination, name)
        if target.exists():
            raise FileExistsError(f"Refusing restore collision: {target}")
        compressed = under(root, row["compressed_path"]).read_bytes()
        if sha(compressed) != row["compressed_sha256"] or len(compressed) != row["compressed_bytes"]:
            raise ValueError(f"Compressed size/hash mismatch: {name}")
        raw = gzip.decompress(compressed)
        if sha(raw) != row["original_sha256"] or len(raw) != row["original_bytes"]:
            raise ValueError(f"Restored size/hash mismatch: {name}")
        planned.append((target, raw))
    for target, raw in planned:
        atomic_new(target, raw)
    print(f"Restored {len(planned)} exact original files under {destination}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("compress", "restore"):
        sub = commands.add_parser(name)
        sub.add_argument("--work", type=Path, required=True)
        sub.add_argument("--map", default="checks/COMPRESSION-MAP.json")
        if name == "compress":
            sub.add_argument("--raw-archive", type=Path, required=True)
            sub.add_argument("--threshold", type=int, default=1024 * 1024)
            sub.add_argument("--path", action="append")
        else:
            sub.add_argument("--dest", type=Path, required=True)
    args = parser.parse_args()
    try:
        {"compress": compress, "restore": restore}[args.command](args)
    except (ValueError, OSError, KeyError, TypeError, EOFError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
