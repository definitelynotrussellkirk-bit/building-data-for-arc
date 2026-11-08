#!/usr/bin/env python3
"""Streaming checkpoints. Keep source, ZIPs, and destination quiescent during use."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tempfile
import zipfile

MEMBER = "CHECKPOINT.json"
SCHEMA = "arcpuzzles-checkpoint-v1"
CONTRACTS = {"ASSIGNMENT.json", "BLIND_ASSIGNMENT.json", "AUDIT_ASSIGNMENT.json"}


def digest(stream, output=None):
    checksum, size = hashlib.sha256(), 0
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        checksum.update(block)
        size += len(block)
        if output is not None:
            output.write(block)
    return {"sha256": checksum.hexdigest(), "size": size}


def safe(name):
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
            or any(p in {"", ".", ".."} for p in name.split("/"))):
        raise ValueError(f"Unsafe relative path: {name!r}")
    return name


def covered(name, roots):
    return any(name == root or name.startswith(root + "/") for root in roots)


def protected(name):
    return any(name in {prefix + item for item in CONTRACTS}
               or covered(name, [prefix + ".review/baseline"]) for prefix in ("", "WORK/"))


def exclusions(names):
    names = sorted({safe(name) for name in names})
    guards = [prefix + item for prefix in ("", "WORK/")
              for item in [*CONTRACTS, ".review/baseline"]]
    if any(covered(guard, names) for guard in guards) or any(protected(n) for n in names):
        raise ValueError("Exclusion covers an assignment contract or frozen baseline")
    return names


def clean_path(path):
    path = Path(os.path.abspath(path))
    for item in (path, *path.parents):
        if item.is_symlink():
            raise ValueError(f"Symlink in filesystem path: {item}")
    return path


def unique(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def index(archive):
    files, seen = {}, set()
    for info in archive.infolist():
        name = safe(info.filename[:-1] if info.is_dir() else info.filename)
        kind = stat.S_IFMT(info.external_attr >> 16)
        if (info.orig_filename != info.filename or name.casefold() in seen
                or kind not in {0, stat.S_IFREG, stat.S_IFDIR}
                or (kind == stat.S_IFDIR and not info.is_dir())
                or (kind == stat.S_IFREG and info.is_dir())
                or info.flag_bits & 1
                or info.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}):
            raise ValueError(f"Unsafe or duplicate ZIP member: {name}")
        seen.add(name.casefold())
        if not info.is_dir():
            files[name] = info
    folded = {name.casefold() for name in files}
    if any(str(parent).casefold() in folded for name in seen
           for parent in PurePosixPath(name).parents):
        raise ValueError("ZIP file/directory collision")
    return files


def original(path):
    with open(path, "rb") as stream:
        identity = digest(stream)["sha256"]
        stream.seek(0)
        with zipfile.ZipFile(stream) as archive:
            baseline = {}
            for name, info in index(archive).items():
                with archive.open(info) as source:
                    baseline[name] = digest(source)
            manifests = {}
            for name in ("PACKET-MANIFEST.json", "WORK/PACKET-MANIFEST.json"):
                if name not in baseline:
                    continue
                value = json.loads(archive.read(name), object_pairs_hook=unique)
                if not isinstance(value, dict) or not isinstance(value.get("files"), dict):
                    raise ValueError(f"Invalid original packet manifest: {name}")
                prefix = name[:-len("PACKET-MANIFEST.json")]
                declarations = {prefix + safe(k): v for k, v in value["files"].items()}
                declarations.update(value.get("layout", {}).get("entry_files", {}))
                for declared, expected in declarations.items():
                    if baseline.get(safe(declared), {}).get("sha256") != expected:
                        raise ValueError(f"Original packet manifest mismatch: {declared}")
                manifests[name] = baseline[name]["sha256"]
    return identity, baseline, manifests


def walk_error(error):
    raise error


def inventory(root, omitted=()):
    result = {}
    for parent, dirs, files in os.walk(root, followlinks=False, onerror=walk_error):
        for item in list(dirs) + files:
            path = Path(parent) / item
            name = safe(path.relative_to(root).as_posix())
            if covered(name, omitted):
                if item in dirs:
                    dirs.remove(item)
                continue
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise ValueError(f"Unsupported filesystem object: {name}")
            if stat.S_ISREG(mode):
                with path.open("rb") as stream:
                    result[name] = {**digest(stream), "mode": stat.S_IMODE(mode) & 0o777}
    return result


def same(row, baseline):
    return baseline is not None and all(row.get(k) == baseline[k] for k in ("sha256", "size"))


def create(original_zip, tree, output, exclude=()):
    root, output = clean_path(tree), clean_path(output)
    if not root.is_dir() or root == output or root in output.parents:
        raise ValueError("Source must be a directory; checkpoint destination must be outside it")
    if output.exists():
        raise FileExistsError(output)
    omitted = exclusions(exclude)
    for name in omitted:
        path = clean_path(root / name)
        if path.exists() and not path.is_dir():
            raise ValueError(f"Excluded path is not a directory: {name}")
    identity, baseline, manifests = original(original_zip)
    current = inventory(root, omitted)
    if any(not same(current.get(n, {}), row) for n, row in baseline.items()
           if n in manifests or protected(n)):
        raise ValueError("Original packet manifest, contract, or baseline changed or is missing")
    saved = {n: row for n, row in current.items()
             if protected(n) or not same(row, baseline.get(n))}
    deleted = sorted(n for n in baseline if n not in current and not covered(n, omitted))
    if any(protected(n) for n in deleted):
        raise ValueError("An original protected contract or baseline file is missing")
    manifest = {"schema": SCHEMA, "original_zip_sha256": identity,
                "packet_manifest_sha256": manifests, "files": saved,
                "deletions": deleted, "exclusions": omitted}
    fd, temporary = tempfile.mkstemp(prefix=".checkpoint-", dir=output.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, row in sorted(saved.items()):
                with (root / name).open("rb") as source, archive.open("files/" + name, "w") as target:
                    if not same(digest(source, target), row):
                        raise ValueError(f"Source changed while checkpointing: {name}")
            archive.writestr(MEMBER, json.dumps(manifest, sort_keys=True, indent=2) + "\n")
        with zipfile.ZipFile(temporary) as archive:
            index(archive)
        os.link(temporary, output)  # Exclusive installation: never replace an existing checkpoint.
    finally:
        Path(temporary).unlink(missing_ok=True)
    return {"checkpoint": str(output), "saved_files": len(saved),
            "deletions": deleted, "exclusions": omitted}


def validate(archive, identity, baseline, manifests):
    members = index(archive)
    if MEMBER not in members or members[MEMBER].file_size > 32 * 1024 * 1024:
        raise ValueError("Missing or oversized checkpoint manifest")
    with archive.open(MEMBER) as source:
        data = json.load(source, object_pairs_hook=unique)
    fields = {"schema", "original_zip_sha256", "packet_manifest_sha256",
              "files", "deletions", "exclusions"}
    if (not isinstance(data, dict) or set(data) != fields or data["schema"] != SCHEMA
            or data["original_zip_sha256"] != identity
            or data["packet_manifest_sha256"] != manifests
            or not isinstance(data["files"], dict)
            or not isinstance(data["deletions"], list)
            or not isinstance(data["exclusions"], list)):
        raise ValueError("Invalid checkpoint manifest or original ZIP identity")
    if exclusions(data["exclusions"]) != data["exclusions"]:
        raise ValueError("Exclusions must be normalized, sorted, and unique")
    if sorted({safe(n) for n in data["deletions"]}) != data["deletions"]:
        raise ValueError("Deletion inventory must be sorted and unique")
    if any(n not in baseline or n in data["files"] or protected(n) or covered(n, data["exclusions"])
           for n in data["deletions"]):
        raise ValueError("Invalid deletion inventory")
    if (set(members) != {MEMBER, *("files/" + safe(n) for n in data["files"])}
            or len(members) != len(archive.infolist())):
        raise ValueError("Checkpoint member inventory differs from manifest")
    if any(n not in data["files"] for n in baseline if protected(n)):
        raise ValueError("Checkpoint omits an original protected contract or baseline file")
    for name, row in data["files"].items():
        if (not isinstance(row, dict) or set(row) != {"sha256", "size", "mode"}
                or type(row["size"]) is not int or row["size"] < 0
                or type(row["mode"]) is not int or not 0 <= row["mode"] <= 0o777
                or covered(name, data["exclusions"])):
            raise ValueError(f"Invalid checkpoint file metadata: {name}")
        if (name in manifests or protected(name)) and name in baseline and not same(row, baseline[name]):
            raise ValueError(f"Checkpoint changes an original protected file: {name}")
        with archive.open("files/" + name) as stream:
            if not same(digest(stream), row):
                raise ValueError(f"Checkpoint member hash/size mismatch: {name}")
    return data


def restore(original_zip, checkpoint, destination, mode=None):
    if mode not in {"fresh", "empty"}:
        raise ValueError("Select fresh-extraction or empty-checkpoint-area mode explicitly")
    root = clean_path(destination)
    identity, baseline, manifests = original(original_zip)
    with zipfile.ZipFile(checkpoint) as archive:
        data = validate(archive, identity, baseline, manifests)
        if mode == "fresh":
            current = inventory(root) if root.is_dir() else {}
            if set(current) != set(baseline) or any(not same(current[n], row)
                                                    for n, row in baseline.items()):
                raise ValueError("Destination is not a fresh original extraction; conflicting files")
        elif root.exists() and (not root.is_dir() or any(root.iterdir())):
            raise ValueError("Explicit checkpoint area must be empty")
        for name in data["files"]:
            target = clean_path(root / name)
            if target.is_dir() or any(p.is_file() for p in target.parents):
                raise ValueError(f"Destination file/directory collision: {name}")
        root.mkdir(parents=True, exist_ok=True)
        written = []
        try:
            for name, row in sorted(data["files"].items()):
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                clean_path(target)
                expected = baseline.get(name) if mode == "fresh" else None
                fd, temporary = tempfile.mkstemp(prefix=".checkpoint-", dir=target.parent)
                try:
                    with os.fdopen(fd, "wb") as output, archive.open("files/" + name) as source:
                        if not same(digest(source, output), row):
                            raise ValueError(f"Checkpoint changed during restore: {name}")
                    os.chmod(temporary, row["mode"])
                    if expected is None:
                        os.link(temporary, target)  # Fails if any leaf appeared after preflight.
                    else:
                        clean_path(target)
                        with target.open("rb") as existing:
                            if not same(digest(existing), expected):
                                raise ValueError(f"Destination changed during restore: {name}")
                        os.replace(temporary, target)
                    written.append(name)
                finally:
                    Path(temporary).unlink(missing_ok=True)
        except Exception as exc:
            raise RuntimeError(f"Restore stopped; installed={written!r}; error={exc}") from exc
    return {"restored_files": written, "deletions_not_applied": data["deletions"],
            "exclusions": data["exclusions"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("create")
    make.add_argument("original_zip"); make.add_argument("tree"); make.add_argument("output")
    make.add_argument("--exclude", action="append", default=[], metavar="RELATIVE_DIRECTORY")
    apply = commands.add_parser("restore")
    apply.add_argument("original_zip"); apply.add_argument("checkpoint"); apply.add_argument("destination")
    modes = apply.add_mutually_exclusive_group(required=True)
    modes.add_argument("--fresh-extraction", dest="mode", action="store_const", const="fresh")
    modes.add_argument("--empty-checkpoint-area", dest="mode", action="store_const", const="empty")
    args = vars(parser.parse_args())
    command = args.pop("command")
    try:
        print(json.dumps((create if command == "create" else restore)(**args), sort_keys=True))
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, zipfile.BadZipFile) as exc:
        parser.exit(2, f"Checkpoint failed: {exc}\n")


if __name__ == "__main__":
    main()
