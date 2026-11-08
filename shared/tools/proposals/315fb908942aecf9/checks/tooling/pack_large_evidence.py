"""Losslessly compress large JSON/JSONL evidence, with verified safe restoration.

All paths in the manifest are relative to the extracted packet. This tool never
executes evidence. Only pack without --dry-run mutates evidence; it retains raw
backups outside the packet before removing originals from checks/.
Run pack only after all evidence writers have stopped; concurrent writers are
not supported. Restore reads verified archives and never overwrites an output.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import uuid


SCHEMA = "review-large-evidence-v1"
MANIFEST = "checks/compressed/MANIFEST.json"
RESTORE = "checks/compressed/RESTORE.md"
EXCLUDED = {"checks/compressed", "checks/tooling"}
CHUNK = 1024 * 1024
RESTORE_TEXT = """# Restore losslessly compressed evidence

MANIFEST.json maps every original packet-relative path to its gzip file, exact
byte count, and SHA-256. Compressed bytes have independent size and hash checks.
The original JSON and JSONL bytes, including every failure, are preserved.

From the extracted packet root:

    python3 checks/tooling/pack_large_evidence.py verify
    python3 checks/tooling/pack_large_evidence.py restore --destination /absolute/path/to/restored-evidence

The destination must be new or empty. The helper rejects symlinks, traversal,
file collisions, overwrites, and corrupt or truncated gzip data. It verifies all
archives before creating restored output. Restored files appear beneath
DESTINATION/checks/ at their original relative paths. Replace the absolute
destination example with your desired location. Paths containing '..' are
deliberately rejected; use an explicit absolute backup or restore location.

If the return's checks/ files were put into EVIDENCE-BUNDLE.tar.gz, first unpack
that verified bundle using the packet's public review evidence-extract command.
The compression helper and this manifest are themselves ordinary checks/ files.

Source-bound reports may still name original evidence paths and hashes. After
restoration those bytes and names match exactly. Do not edit an original report
to make its references point at compressed files. RESULTS.json evidence_paths
must instead name retained compressed paths and this manifest.

Pack keeps a second original copy beneath the explicitly selected --raw-backup
directory, using the same packet-relative paths. That scratch copy is not
needed for restoration from the returned archive. Pack never overwrites a raw
backup. On interruption inspect the manifest and retained originals; do not
delete unexplained partial files merely to force a retry.
"""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def relative(name):
    if not isinstance(name, str) or not name or any(c in name for c in ("\0", "\\", ":")):
        raise ValueError(f"Unsafe relative path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or path.as_posix() != name or any(p in {".", ".."} for p in path.parts):
        raise ValueError(f"Unsafe relative path: {name!r}")
    return path


def absolute(path):
    path = Path(path)
    if ".." in path.parts:
        raise ValueError(f"Parent traversal is not permitted: {path}")
    return Path(os.path.abspath(path))


class Tree:
    """Directory descriptors prevent following symlinks in any path component."""

    def __init__(self, path, *, create=False):
        self.path = absolute(path)
        self.fd = os.open(self.path.anchor, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in self.path.parts[1:]:
                if create:
                    try:
                        os.mkdir(part, mode=0o755, dir_fd=self.fd)
                    except FileExistsError:
                        pass
                nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=self.fd)
                os.close(self.fd)
                self.fd = nxt
        except BaseException:
            os.close(self.fd)
            raise

    def __enter__(self):
        return self

    def __exit__(self, *_):
        os.close(self.fd)

    @contextmanager
    def parent(self, name, *, create=False):
        parts = relative(name).parts
        fd = os.dup(self.fd)
        try:
            for part in parts[:-1]:
                if create:
                    try:
                        os.mkdir(part, mode=0o755, dir_fd=fd)
                    except FileExistsError:
                        pass
                nxt = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                os.close(fd)
                fd = nxt
            yield fd, parts[-1]
        finally:
            os.close(fd)

    def exists(self, name):
        try:
            with self.parent(name) as (fd, leaf):
                info = os.stat(leaf, dir_fd=fd, follow_symlinks=False)
                if stat.S_ISLNK(info.st_mode):
                    raise ValueError(f"Symlink forbidden: {name}")
                return True
        except FileNotFoundError:
            return False

    def read(self, name):
        with self.parent(name) as (fd, leaf):
            source = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(source, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                raise ValueError(f"Expected a regular file: {name}")
            return handle.read()

    def write_new(self, name, data):
        with self.parent(name, create=True) as (fd, leaf):
            target = os.open(leaf, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o644, dir_fd=fd)
            with os.fdopen(target, "wb") as handle:
                if hasattr(data, "read"):
                    shutil.copyfileobj(data, handle, CHUNK)
                else:
                    handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.fsync(fd)

    def replace_manifest(self, raw):
        # This is the sole intentional replacement: publishing an updated map.
        with self.parent(MANIFEST, create=True) as (fd, leaf):
            temporary = "." + leaf + ".tmp-" + uuid.uuid4().hex
            target = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o644, dir_fd=fd)
            try:
                with os.fdopen(target, "wb") as handle:
                    handle.write(raw)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temporary, leaf, src_dir_fd=fd, dst_dir_fd=fd)
                os.fsync(fd)
            finally:
                try:
                    os.unlink(temporary, dir_fd=fd)
                except FileNotFoundError:
                    pass

    def remove_original(self, row):
        name = row["original_path"]
        raw = self.read(name)
        if len(raw) != row["original_bytes"] or digest(raw) != row["original_sha256"]:
            raise ValueError(f"Original changed during packing; left in place: {name}")
        with self.parent(name) as (fd, leaf):
            os.unlink(leaf, dir_fd=fd)
            os.fsync(fd)


def compressed_name(original):
    return "checks/compressed/files/" + original.removeprefix("checks/") + ".gz"


def make_manifest(rows):
    rows = sorted(rows, key=lambda row: row["original_path"])
    return {"schema": SCHEMA, "compression": "gzip", "count": len(rows),
            "original_bytes": sum(row["original_bytes"] for row in rows),
            "compressed_bytes": sum(row["compressed_bytes"] for row in rows), "files": rows}


def load_manifest(tree, *, required=False):
    if not tree.exists(MANIFEST):
        if required:
            raise ValueError(f"No compression manifest: {MANIFEST}")
        return make_manifest([])
    return validate_manifest(json.loads(tree.read(MANIFEST)))


def validate_manifest(value):
    if not isinstance(value, dict) or value.get("schema") != SCHEMA or value.get("compression") != "gzip":
        raise ValueError("Invalid compression manifest schema")
    rows = value.get("files")
    if not isinstance(rows, list):
        raise ValueError("Manifest files must be a list")
    seen = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Invalid manifest row")
        path = relative(row.get("original_path"))
        original = path.as_posix()
        if (not original.startswith("checks/") or path.suffix.lower() not in {".json", ".jsonl"}
                or any(original.startswith(prefix + "/") for prefix in EXCLUDED)
                or original.casefold() in seen):
            raise ValueError(f"Invalid or colliding original path: {original}")
        seen.add(original.casefold())
        if relative(row.get("compressed_path")).as_posix() != compressed_name(original):
            raise ValueError(f"Compressed path does not match original: {original}")
        for prefix in ("original", "compressed"):
            if type(row.get(prefix + "_bytes")) is not int or row[prefix + "_bytes"] < 0:
                raise ValueError(f"Invalid byte count: {original}")
            if not isinstance(row.get(prefix + "_sha256"), str) or not re.fullmatch(
                    r"[0-9a-f]{64}", row[prefix + "_sha256"]):
                raise ValueError(f"Invalid SHA-256: {original}")
    for name in seen:
        if any(parent.as_posix().casefold() in seen for parent in PurePosixPath(name).parents):
            raise ValueError("Manifest file/directory collision")
    normalized = make_manifest(rows)
    if any(type(value.get(key)) is not int or value[key] != normalized[key]
           for key in ("count", "original_bytes", "compressed_bytes")):
        raise ValueError("Manifest totals differ from its rows")
    return normalized


def candidates(tree, threshold, existing):
    selected = []
    for directory, dirs, files, fd in os.fwalk("checks", dir_fd=tree.fd, follow_symlinks=False):
        dirs.sort()
        for name in list(dirs):
            path = PurePosixPath(directory, name).as_posix()
            if stat.S_ISLNK(os.stat(name, dir_fd=fd, follow_symlinks=False).st_mode):
                raise ValueError(f"Symlink forbidden: {path}")
            if path in EXCLUDED:
                dirs.remove(name)
        for name in sorted(files):
            path = relative(PurePosixPath(directory, name).as_posix())
            info = os.stat(name, dir_fd=fd, follow_symlinks=False)
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(f"Nonregular evidence forbidden: {path}")
            if path.suffix.lower() not in {".json", ".jsonl"} or info.st_size < threshold:
                continue
            if path.as_posix() in existing:
                raise ValueError(f"Previously packed original is present; inspect before retry: {path}")
            raw = tree.read(path.as_posix())
            selected.append({"original_path": path.as_posix(), "original_bytes": len(raw),
                             "original_sha256": digest(raw)})
    return sorted(selected, key=lambda row: row["original_path"])


def verify_row(tree, row, sink=None):
    raw = tree.read(row["compressed_path"])
    if len(raw) != row["compressed_bytes"] or digest(raw) != row["compressed_sha256"]:
        raise ValueError(f"Compressed size/hash mismatch: {row['compressed_path']}")
    count, checksum = 0, hashlib.sha256()
    with gzip.GzipFile(fileobj=io.BytesIO(raw), mode="rb") as handle:
        while True:
            chunk = handle.read(min(CHUNK, row["original_bytes"] - count + 1))
            if not chunk:
                break
            count += len(chunk)
            if count > row["original_bytes"]:
                raise ValueError(f"Gzip exceeds declared original size: {row['original_path']}")
            checksum.update(chunk)
            if sink is not None:
                sink.write(chunk)
    if count != row["original_bytes"] or checksum.hexdigest() != row["original_sha256"]:
        raise ValueError(f"Restored size/hash mismatch: {row['original_path']}")


def pack(tree, rows, manifest, backup):
    backup = absolute(backup)
    if backup == tree.path or tree.path in backup.parents:
        raise ValueError("Raw backup must be outside the packet directory")
    for row in rows:
        target = backup / row["original_path"]
        if target == tree.path or tree.path in target.parents:
            raise ValueError(f"Actual raw backup path would reenter the packet: {target}")
    # Validate all planned names before creating backups, gzip files or a map.
    planned = [{**row, "compressed_path": compressed_name(row["original_path"]),
                "compressed_bytes": 0, "compressed_sha256": "0" * 64} for row in rows]
    validate_manifest(make_manifest([*manifest["files"], *planned]))
    for row in manifest["files"]:
        verify_row(tree, row)
    if not rows:
        return {"packed": 0, "manifest": MANIFEST, "note": "No eligible new files"}
    with Tree(backup, create=True) as saved:
        # Reject existing destinations before creating any compressed artifacts.
        for row in rows:
            if tree.exists(compressed_name(row["original_path"])) or saved.exists(row["original_path"]):
                raise FileExistsError(f"Refusing to overwrite evidence/backup: {row['original_path']}")
        added = []
        for candidate in rows:
            original = candidate["original_path"]
            raw = tree.read(original)
            if len(raw) != candidate["original_bytes"] or digest(raw) != candidate["original_sha256"]:
                raise ValueError(f"Evidence changed after listing: {original}")
            memory = io.BytesIO()
            with gzip.GzipFile(filename="", fileobj=memory, mode="wb", mtime=0, compresslevel=9) as archive:
                archive.write(raw)
            compressed = memory.getvalue()
            row = {**candidate, "compressed_path": compressed_name(original),
                   "compressed_bytes": len(compressed), "compressed_sha256": digest(compressed)}
            tree.write_new(row["compressed_path"], compressed)
            verify_row(tree, row)  # Verify the actual stored gzip before retaining/removing raw.
            saved.write_new(original, raw)
            if digest(saved.read(original)) != row["original_sha256"]:
                raise ValueError(f"Raw backup verification failed: {original}")
            added.append(row)
        updated = make_manifest([*manifest["files"], *added])
        if not tree.exists(RESTORE):
            tree.write_new(RESTORE, RESTORE_TEXT.encode())
        tree.replace_manifest((json.dumps(updated, indent=2) + "\n").encode())
        # Mapping, compressed data and independent raw backups are durable first.
        for row in added:
            tree.remove_original(row)
    return {"packed": len(added), "manifest": MANIFEST, "raw_backup": str(backup),
            "original_bytes": sum(row["original_bytes"] for row in added),
            "compressed_bytes": sum(row["compressed_bytes"] for row in added)}


def restore(tree, manifest, destination):
    destination = absolute(destination)
    # Verified staging keeps malformed gzip from producing partial restored files.
    with tempfile.TemporaryDirectory(prefix="evidence-restore-verified-") as staging:
        for index, row in enumerate(manifest["files"]):
            with (Path(staging) / str(index)).open("xb") as handle:
                verify_row(tree, row, handle)
        with Tree(destination, create=True) as target:
            if os.listdir(target.fd):
                raise FileExistsError("Restore destination must be new or empty; nothing overwritten")
            for index, row in enumerate(manifest["files"]):
                with (Path(staging) / str(index)).open("rb") as handle:
                    target.write_new(row["original_path"], handle)
    return {"restored": manifest["count"], "original_bytes": manifest["original_bytes"],
            "destination": str(destination)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", type=Path, default=Path(__file__).resolve().parents[2])
    actions = parser.add_subparsers(dest="action", required=True)
    for name in ("list", "pack"):
        action = actions.add_parser(name)
        action.add_argument("--threshold-bytes", type=int, default=1024 * 1024,
                            help="minimum JSON/JSONL byte count; default 1048576")
        if name == "pack":
            action.add_argument("--dry-run", action="store_true")
            action.add_argument("--raw-backup", type=Path,
                                help="scratch directory outside the packet; required unless --dry-run")
    actions.add_parser("verify")
    extract = actions.add_parser("restore")
    extract.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        with Tree(args.packet_root) as tree:
            manifest = load_manifest(tree, required=args.action in {"restore", "verify"})
            if args.action in {"list", "pack"}:
                if args.threshold_bytes < 1:
                    raise ValueError("threshold-bytes must be positive")
                rows = candidates(tree, args.threshold_bytes,
                                  {row["original_path"] for row in manifest["files"]})
                if args.action == "list" or args.dry_run:
                    result = {"dry_run": True, "count": len(rows), "files": rows,
                              "original_bytes": sum(row["original_bytes"] for row in rows),
                              "threshold_bytes": args.threshold_bytes}
                else:
                    if args.raw_backup is None:
                        raise ValueError("pack requires --raw-backup outside the packet")
                    result = pack(tree, rows, manifest, args.raw_backup)
            elif args.action == "verify":
                for row in manifest["files"]:
                    verify_row(tree, row)
                result = {"verified": manifest["count"], "original_bytes": manifest["original_bytes"]}
            else:
                result = restore(tree, manifest, args.destination)
        print(json.dumps(result, indent=2))
        return 0
    except (OSError, ValueError, EOFError) as exc:
        print(f"Evidence operation rejected: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
