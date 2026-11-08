#!/usr/bin/env python3
"""Save a review WORK directory as one source-bound, verified delta ZIP.

Python standard library only. Run from outside WORK, with a durable output path:

  python checkpoint_workspace.py run --workspace /ephemeral/WORK \
    --source-zip /durable/original.zip --output /durable/checkpoint.zip \
    -- python /ephemeral/review.py start
  python checkpoint_workspace.py verify --checkpoint /durable/checkpoint.zip \
    --source-zip /durable/original.zip
  python checkpoint_workspace.py restore --checkpoint /durable/checkpoint.zip \
    --source-zip /durable/original.zip --destination /new/WORK

Use create with the same workspace/source/output options for later checkpoints;
--replace explicitly permits atomic replacement. The original ZIP is required
for verification and restoration. Restore creates WORK contents only; the
packet's top-level controller remains available in the original ZIP.

All non-excluded regular files are inventoried. Changed/new bytes, including
assignment files and .review/baseline, are stored verbatim. Missing original
files are recorded and are not recreated. No assignment is drawn or repaired.
Known runtime/cache/temp paths and root review_response_*.zip are omitted.
Other evidence ZIPs are retained. Empty directories, timestamps, ACLs and xattrs
are not preserved; ordinary permission bits are. Symbolic links are rejected
outside excluded trees. Restore requires an empty/new destination and leaves
partial output visible if an I/O error interrupts restoration.

Quiesce other writers while capturing/restoring. File/inventory changes are
detected during capture, but this is not a filesystem snapshot or protection
against hostile concurrent writers. run checkpoints in finally after normal
exit, command failure, launch failure or KeyboardInterrupt; SIGKILL, process
loss, storage loss and host failure cannot run finally. Keep the wrapper alive
until it reports success. A checkpoint file needs one inode, plus one temporary
inode while replacing it. Files are fsynced before atomic publication, followed
by a parent-directory fsync. The old checkpoint survives any pre-publication
failure; a failure after publication can make durability uncertain.
"""

import argparse
from contextlib import contextmanager
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import zipfile


SCHEMA = "review-workspace-checkpoint/v1"
MANIFEST = "PACKET-MANIFEST.json"
META = "CHECKPOINT.json"
PREFIX = "WORK/"
EXCLUSIONS = [".review/racket-runtime/**", ".review/tmp/**", "tmp/**",
              "**/__pycache__/**", "**/*.pyc", "review_response_*.zip (root only)"]
MAX_JSON_BYTES = 32 * 1024 * 1024


class CheckpointError(ValueError):
    pass


def _path(name):
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or any(ord(char) < 32 for char in name)
            or any(part in {"", ".", ".."} for part in name.split("/"))):
        raise CheckpointError(f"Unsafe relative path: {name!r}")
    return name


def _excluded(name):
    parts = name.split("/")
    return (name in {".review/racket-runtime", ".review/tmp", "tmp"}
            or name.startswith((".review/racket-runtime/", ".review/tmp/", "tmp/"))
            or "__pycache__" in parts or name.endswith(".pyc")
            or (len(parts) == 1 and fnmatch.fnmatchcase(name, "review_response_*.zip")))


def _fingerprint(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns)


def _copy_stream(reader, writer=None):
    digest, size = hashlib.sha256(), 0
    while True:
        chunk = reader.read(1024 * 1024)
        if not chunk:
            return digest.hexdigest(), size
        digest.update(chunk)
        size += len(chunk)
        if writer is not None:
            writer.write(chunk)


@contextmanager
def _regular_file(path, expected=None):
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise CheckpointError(f"Expected a regular file, not a symlink/device: {path}")
    stamp = _fingerprint(before)
    if expected is not None and stamp != expected:
        raise CheckpointError(f"File changed before capture: {path}")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        if _fingerprint(os.fstat(stream.fileno())) != stamp:
            raise CheckpointError(f"File changed while opening: {path}")
        yield stream
        if (_fingerprint(os.fstat(stream.fileno())) != stamp
                or _fingerprint(path.lstat()) != stamp):
            raise CheckpointError(f"File changed during capture: {path}")


def _scan(workspace):
    files = {}
    for directory, dirs, names in os.walk(workspace, followlinks=False,
                                          onerror=lambda error: (_ for _ in ()).throw(error)):
        for name in sorted(dirs + names):
            target = Path(directory) / name
            relative = _path(target.relative_to(workspace).as_posix())
            if _excluded(relative):
                if name in dirs:
                    dirs.remove(name)
                continue
            info = target.lstat()
            if stat.S_ISREG(info.st_mode):
                files[relative] = _fingerprint(info)
            elif not stat.S_ISDIR(info.st_mode):
                raise CheckpointError(f"Unsupported file or symlink: {relative}")
    return files


def _index(archive):
    entries, types = {}, {}
    for item in archive.infolist():
        name = _path(item.filename[:-1] if item.is_dir() else item.filename)
        if name in types:
            raise CheckpointError(f"Duplicate archive path: {name}")
        kind = stat.S_IFMT(item.external_attr >> 16)
        if kind not in {0, stat.S_IFREG, stat.S_IFDIR} or (kind == stat.S_IFDIR) != item.is_dir() and kind:
            raise CheckpointError(f"Unsupported archive file type: {name}")
        types[name] = item.is_dir()
        if not item.is_dir():
            entries[name] = item
    for name in types:
        parts = name.split("/")
        for length in range(1, len(parts)):
            if types.get("/".join(parts[:length])) is False:
                raise CheckpointError(f"Archive file/directory conflict: {name}")
    return entries


def _json(archive, entries, name):
    if name not in entries or entries[name].file_size > MAX_JSON_BYTES:
        raise CheckpointError(f"Missing or oversized JSON metadata: {name}")

    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise CheckpointError(f"Duplicate JSON key: {key}")
            value[key] = item
        return value

    try:
        return json.loads(archive.read(entries[name]), object_pairs_hook=unique)
    except (UnicodeError, json.JSONDecodeError) as error:
        raise CheckpointError(f"Invalid JSON metadata: {name}") from error


def _digest(value):
    return (isinstance(value, str) and len(value) == 64
            and all(char in "0123456789abcdef" for char in value))


@contextmanager
def _source(path, expected_sha=None):
    with _regular_file(path) as stream:
        source_sha, _ = _copy_stream(stream)
        if expected_sha is not None and source_sha != expected_sha:
            raise CheckpointError("Source ZIP SHA-256 does not match this checkpoint")
        stream.seek(0)
        with zipfile.ZipFile(stream) as archive:
            entries = _index(archive)
            manifest = _json(archive, entries, PREFIX + MANIFEST)
            baseline = manifest.get("files") if isinstance(manifest, dict) else None
            if not isinstance(baseline, dict):
                raise CheckpointError("Packet manifest has no files mapping")
            baseline = dict(baseline)
            for name, digest in baseline.items():
                _path(name)
                if not _digest(digest) or name == MANIFEST or PREFIX + name not in entries:
                    raise CheckpointError(f"Invalid packet manifest entry: {name}")
            manifest_bytes = archive.read(entries[PREFIX + MANIFEST])
            baseline[MANIFEST] = hashlib.sha256(manifest_bytes).hexdigest()
            workspace_names = {name[len(PREFIX):] for name in entries if name.startswith(PREFIX)}
            if workspace_names != set(baseline):
                raise CheckpointError("Packet manifest does not cover every WORK file")
            yield archive, entries, baseline, source_sha


def _validate(archive, source):
    entries = _index(archive)
    metadata = _json(archive, entries, META)
    if not isinstance(metadata, dict) or metadata.get("schema") != SCHEMA:
        raise CheckpointError("Unsupported checkpoint schema")
    source_archive, source_entries, baseline, source_sha = source
    if metadata.get("source_sha256") != source_sha or metadata.get("source_prefix") != PREFIX:
        raise CheckpointError("Checkpoint source binding differs")
    if metadata.get("exclusions") != EXCLUSIONS:
        raise CheckpointError("Unknown checkpoint exclusions")
    files = metadata.get("files")
    if not isinstance(files, dict) or MANIFEST not in files:
        raise CheckpointError("Missing workspace inventory")
    expected_entries = {META}
    for name, record in files.items():
        _path(name)
        if (_excluded(name) or not isinstance(record, dict)
                or not _digest(record.get("sha256"))
                or type(record.get("size")) is not int or record["size"] < 0
                or type(record.get("mode")) is not int or not 0 <= record["mode"] <= 0o777
                or type(record.get("stored")) is not bool):
            raise CheckpointError(f"Invalid inventory entry: {name}")
        if record["stored"]:
            member, reader_archive, reader_entries = "files/" + name, archive, entries
            expected_entries.add(member)
        else:
            if baseline.get(name) != record["sha256"]:
                raise CheckpointError(f"Unstored file differs from source: {name}")
            member, reader_archive, reader_entries = PREFIX + name, source_archive, source_entries
        if member not in reader_entries:
            raise CheckpointError(f"Missing archive payload: {member}")
        with reader_archive.open(reader_entries[member]) as stream:
            digest, size = _copy_stream(stream)
        if (digest, size) != (record["sha256"], record["size"]):
            raise CheckpointError(f"Payload checksum/size mismatch: {name}")
    if set(entries) != expected_entries:
        raise CheckpointError("Unexpected checkpoint archive members")
    if metadata.get("deleted") != sorted(set(baseline) - set(files)):
        raise CheckpointError("Deleted-file inventory does not match source")
    if files[MANIFEST]["sha256"] != baseline[MANIFEST]:
        raise CheckpointError("Workspace packet manifest was modified")
    for name in files:
        pieces = name.split("/")
        if any("/".join(pieces[:length]) in files for length in range(1, len(pieces))):
            raise CheckpointError(f"Inventory file/directory conflict: {name}")
    return metadata


def _workspace(path):
    path = Path(path).absolute()
    if path.is_symlink() or not path.is_dir():
        raise CheckpointError(f"Workspace must be an existing non-symlink directory: {path}")
    return path.resolve()


def _output(workspace, source_zip, output, replace):
    output = Path(output).absolute()
    if not output.parent.is_dir():
        raise CheckpointError("Checkpoint output parent directory must already exist")
    if output.is_symlink() or (output.exists() and not output.is_file()):
        raise CheckpointError("Checkpoint output must not be a symlink/directory")
    output = output.parent.resolve() / output.name
    if output == source_zip.resolve() or output.is_relative_to(workspace):
        raise CheckpointError("Checkpoint output must be outside WORK and differ from source ZIP")
    if output.exists() and not replace:
        raise FileExistsError(f"Checkpoint exists; use --replace explicitly: {output}")
    return output


def create_checkpoint(workspace, source_zip, output, replace=False):
    workspace, source_zip = _workspace(workspace), Path(source_zip).absolute()
    output = _output(workspace, source_zip, output, replace)
    snapshot = _scan(workspace)
    if MANIFEST not in snapshot:
        raise CheckpointError("WORK is missing PACKET-MANIFEST.json")
    temporary = None
    try:
        with _source(source_zip) as source:
            _, _, baseline, source_sha = source
            descriptor, name = tempfile.mkstemp(prefix=".checkpoint-", suffix=".tmp", dir=output.parent)
            temporary = Path(name)
            files = {}
            with os.fdopen(descriptor, "w+b") as stream:
                with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                    for relative, stamp in sorted(snapshot.items()):
                        with _regular_file(workspace / relative, stamp) as current:
                            digest, size = _copy_stream(current)
                            stored = baseline.get(relative) != digest
                            files[relative] = {"sha256": digest, "size": size,
                                               "mode": stat.S_IMODE(stamp[2]) & 0o777, "stored": stored}
                            if stored:
                                current.seek(0)
                                with archive.open("files/" + relative, "w", force_zip64=True) as target:
                                    copied = _copy_stream(current, target)
                                if copied != (digest, size):
                                    raise CheckpointError(f"File changed during copy: {relative}")
                    metadata = {"schema": SCHEMA, "source_sha256": source_sha,
                                "source_prefix": PREFIX, "exclusions": EXCLUSIONS,
                                "files": files, "deleted": sorted(set(baseline) - set(files))}
                    archive.writestr(META, json.dumps(metadata, sort_keys=True, separators=(",", ":")))
                stream.flush()
                os.fsync(stream.fileno())
            with zipfile.ZipFile(temporary) as archive:
                _validate(archive, source)
            if _scan(workspace) != snapshot:
                raise CheckpointError("Workspace changed during checkpoint; quiesce other writers and retry")
        # Source's descriptor/path stability has also been checked before publication.
        if replace:
            os.replace(temporary, output)
        else:
            os.link(temporary, output)  # Atomic no-clobber publication, even with a racing creator.
            temporary.unlink()
        temporary = None
        directory_fd = os.open(output.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return metadata
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def verify_checkpoint(checkpoint, source_zip):
    with _regular_file(Path(checkpoint)) as stream, zipfile.ZipFile(stream) as archive:
        entries = _index(archive)
        metadata = _json(archive, entries, META)
        if not isinstance(metadata, dict) or not _digest(metadata.get("source_sha256")):
            raise CheckpointError("Invalid source binding")
        with _source(Path(source_zip), metadata["source_sha256"]) as source:
            return _validate(archive, source)


def restore_checkpoint(checkpoint, source_zip, destination):
    destination = Path(destination).absolute()
    if destination.is_symlink() or (destination.exists()
            and (not destination.is_dir() or any(destination.iterdir()))):
        raise CheckpointError("Restore destination must be a new or empty non-symlink directory")
    # Validate every byte before creating destination files; keep archives open during restore.
    with _regular_file(Path(checkpoint)) as stream, zipfile.ZipFile(stream) as archive:
        entries = _index(archive)
        metadata = _json(archive, entries, META)
        if not isinstance(metadata, dict) or not _digest(metadata.get("source_sha256")):
            raise CheckpointError("Invalid source binding")
        with _source(Path(source_zip), metadata["source_sha256"]) as source:
            metadata = _validate(archive, source)
            destination.mkdir(mode=0o700, exist_ok=True)
            for relative, record in sorted(metadata["files"].items()):
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                for parent in target.parents:
                    if parent == destination.parent:
                        break
                    if parent.is_symlink():
                        raise CheckpointError(f"Symlink appeared during restoration: {parent}")
                reader = archive if record["stored"] else source[0]
                member = "files/" + relative if record["stored"] else PREFIX + relative
                with reader.open(member) as current, target.open("xb") as output:
                    copied = _copy_stream(current, output)
                if copied != (record["sha256"], record["size"]):
                    raise CheckpointError(f"Restore source changed: {relative}")
                target.chmod(record["mode"])
            return metadata


def run_checkpoint(workspace, source_zip, output, command, replace=False):
    workspace, source_zip = _workspace(workspace), Path(source_zip).absolute()
    _output(workspace, source_zip, output, replace)
    if not command:
        raise CheckpointError("run requires a command after --")
    status, failed = 1, False
    try:
        result = subprocess.run(command, cwd=workspace, check=False)
        status = result.returncode if result.returncode >= 0 else 128 - result.returncode
    except KeyboardInterrupt:
        status = 130
    finally:
        try:
            metadata = create_checkpoint(workspace, source_zip, output, replace=replace)
            print(json.dumps(_summary(metadata, output)), file=sys.stderr)
        except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
            failed = True
            print(f"CHECKPOINT FAILED: {error}", file=sys.stderr)
    return status or int(failed)


def _summary(metadata, output):
    return {"checkpoint": str(output), "files": len(metadata["files"]),
            "stored": sum(record["stored"] for record in metadata["files"].values()),
            "deleted": len(metadata["deleted"]), "source_sha256": metadata["source_sha256"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ["create", "run", "verify", "restore"]:
        child = commands.add_parser(action)
        child.add_argument("--source-zip", required=True, type=Path)
        if action in {"create", "run"}:
            child.add_argument("--workspace", required=True, type=Path)
            child.add_argument("--output", required=True, type=Path)
            child.add_argument("--replace", action="store_true")
            if action == "run":
                child.add_argument("command", nargs=argparse.REMAINDER)
        else:
            child.add_argument("--checkpoint", required=True, type=Path)
            if action == "restore":
                child.add_argument("--destination", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "run":
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            return run_checkpoint(args.workspace, args.source_zip, args.output, command, args.replace)
        if args.action == "create":
            metadata = create_checkpoint(args.workspace, args.source_zip, args.output, args.replace)
            output = args.output
        elif args.action == "verify":
            metadata = verify_checkpoint(args.checkpoint, args.source_zip)
            output = args.checkpoint
        else:
            metadata = restore_checkpoint(args.checkpoint, args.source_zip, args.destination)
            output = args.checkpoint
        print(json.dumps(_summary(metadata, output)))
        return 0
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
