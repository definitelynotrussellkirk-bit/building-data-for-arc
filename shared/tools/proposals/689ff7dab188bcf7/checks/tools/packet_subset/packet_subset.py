#!/usr/bin/env python3
"""Optional stdlib extractor for canonical ARC full packets; prints metadata only."""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tempfile
import zipfile


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def safe_name(name):
    if (not isinstance(name, str) or not name or any(c in name for c in "\\:\0")
            or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
            or not PurePosixPath(name).parts
            or str(PurePosixPath(name)) + ("/" if name.endswith("/") else "") != name):
        raise ValueError(f"Unsafe archive path: {name!r}")


def no_symlinks(path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError(f"Symlink destination: {part}")


def file_sha(path):
    no_symlinks(path)
    if not path.is_file():
        raise ValueError(f"Not a regular file: {path}")
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def save(path, value, *, immutable=False):
    """Durably publish metadata; only mutable helper receipts may be replaced."""
    no_symlinks(path)
    # Match review_full_draw._draw_json exactly for pending-main-draw.json.
    raw = (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    if immutable and path.exists():
        if json.loads(path.read_bytes()) != value:
            raise ValueError(f"Existing journal conflicts: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=".subset-", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path) if immutable else os.replace(temporary, path)
        sync_directory(path.parent)
    finally:
        temporary.unlink(missing_ok=True)  # This invocation's own staging file only.


class Packet:
    def __init__(self, source):
        self.zip = zipfile.ZipFile(source)
        try:
            self.files, seen = {}, set()
            for info in self.zip.infolist():
                safe_name(info.orig_filename)
                if info.orig_filename != info.filename:
                    raise ValueError("Truncated archive filename")
                key = info.filename.rstrip("/")
                if key in seen:
                    raise ValueError(f"Duplicate archive member: {info.filename}")
                seen.add(key)
                kind = stat.S_IFMT(info.external_attr >> 16)
                if (kind not in {0, stat.S_IFREG, stat.S_IFDIR} or info.flag_bits & 1
                        or (kind == stat.S_IFDIR and not info.is_dir())
                        or (kind == stat.S_IFREG and info.is_dir())):
                    raise ValueError(f"Unsafe member type: {info.filename}")
                if not info.is_dir():
                    self.files[info.filename] = info
            for name in seen:
                if any(str(p) in self.files for p in PurePosixPath(name).parents):
                    raise ValueError(f"File used as archive directory: {name}")
            self.prefix = "WORK/" if "WORK/PACKET-MANIFEST.json" in self.files else ""
            manifest_name = self.prefix + "PACKET-MANIFEST.json"
            raw = self.zip.read(manifest_name)
            self.manifest, self.packet_id = json.loads(raw), sha(raw)
            if self.manifest.get("schema") != "arcpuzzles-full-packet-v2" or canonical(self.manifest) != raw:
                raise ValueError("Noncanonical or unsupported packet manifest")
            self.expected = {self.prefix + n: d for n, d in self.manifest["files"].items()}
            for name, digest in self.manifest.get("layout", {}).get("entry_files", {}).items():
                if name in self.expected:
                    raise ValueError(f"Conflicting manifest path: {name}")
                self.expected[name] = digest
            if manifest_name in self.expected:
                raise ValueError("Manifest cannot hash itself")
            self.expected[manifest_name] = self.packet_id
            for name, digest in self.expected.items():
                safe_name(name)
                if name.split("/")[0] == ".packet-subset" or not re.fullmatch("[0-9a-f]{64}", digest):
                    raise ValueError(f"Invalid manifest entry: {name}")
            if set(self.files) != set(self.expected):
                raise ValueError("Archive inventory differs from packet manifest")
        except BaseException:
            self.zip.close()
            raise

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.zip.close()

    def read(self, name):
        raw = self.zip.read(name)
        if sha(raw) != self.expected[name]:
            raise ValueError(f"Original hash mismatch: {name}")
        return raw

    def verify(self, name):
        with self.zip.open(name) as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() != self.expected[name]:
                raise ValueError(f"Original hash mismatch: {name}")

    def mapping(self):
        return (json.loads(self.read(self.prefix + "repo/catalog/" + name))
                for name in ("runtime_files.json", "authority_files.json"))

    def selection(self, seed):
        """Exact review_full_draw v2 formulas, including its pending contract."""
        if not isinstance(seed, bytes) or len(seed) != 32:
            raise ValueError("Draw seed must be exactly 32 bytes")
        manifest = self.manifest
        task = manifest["main_ids"][int.from_bytes(seed, "big") % len(manifest["main_ids"])]
        row = manifest["generators"][task]
        baseline = {n for n in manifest["files"] if n.startswith(f"repo/generators/{task}/")}
        baseline.add("repo/shared/data/canonical/puzzles.jsonl")
        mapping, authorities = self.mapping()
        baseline.update("repo/" + item["path"] for item in mapping
            if item["target"].startswith("data/base/solutions/")
            and authorities.get(item["target"]) in {task, row["rule_task_id"]})
        questions = sorted(manifest["questions"], key=lambda q: q["id"])
        question = questions[int.from_bytes(hashlib.sha256(seed + b":question").digest(), "big") % len(questions)]
        contract = {"schema": "arcpuzzles-full-assignment-v2", "packet_id": self.packet_id,
            "assignment_id": "review-" + sha(bytes.fromhex(self.packet_id) + seed)[:16],
            "seed": seed.hex(), "task_id": task, "generator": row, "question": question,
            "baseline_sha256": {n: manifest["files"][n] for n in sorted(baseline)}}
        tasks = {task}
        if manifest.get("reviewer_solve", {}).get("blind", {}).get("required"):
            pool = sorted(t for t, r in manifest["generators"].items() if r.get("approved") and t != task)
            pool = pool or sorted(t for t in manifest["all_ids"] if t != task)
            tasks.add(pool[int.from_bytes(hashlib.sha256(seed + b":blind").digest(), "big") % len(pool)])
        return contract, tasks

    def members(self, tasks):
        """Port of review_replay._runtime_members, unioned across selected tasks."""
        manifest, prefix = self.manifest, self.prefix
        for task in tasks:
            if task not in manifest["generators"]:
                raise ValueError(f"Unknown task: {task}")
        bound = set(tasks) | {manifest["generators"][t]["rule_task_id"] for t in tasks}
        mapping, authorities = self.mapping()
        selected = set()
        for item in mapping:
            relative, target = item["path"], item["target"]
            safe_name(relative)
            if relative.startswith("generators/") and PurePosixPath(relative).parts[1] not in bound:
                continue
            if target.startswith("data/base/solutions/") and authorities.get(target) not in bound:
                continue
            selected.add(prefix + "repo/" + relative)
        roots = {prefix + "repo/" + n for n in ("AGENTS.md", "README.md", "pyproject.toml", "setup.py", "requirements.txt")}
        starts = tuple(prefix + n for n in ("repo/src/arcpuzzles/", "repo/catalog/", "vendor/",
                       "repo/REVIEW/questions/", "repo/docs/", "repo/GUIDE/"))
        homes = tuple(prefix + f"repo/generators/{task}/" for task in bound)
        selected.update(n for n in self.expected if n in roots or "/" not in n.removeprefix(prefix)
                        or not n.startswith(prefix) or n.startswith(starts + homes))
        selected.add(prefix + "repo/shared/data/canonical/puzzles.jsonl")
        if selected - self.expected.keys():
            raise ValueError("Missing declared runtime sources")
        return selected


def install(packet, name, target, staging):
    """Stream-verify before exclusive publication; never replace a checkout file."""
    no_symlinks(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, filename = tempfile.mkstemp(prefix="member-", dir=staging)
    temporary = Path(filename)
    try:
        digest = hashlib.sha256()
        with os.fdopen(descriptor, "wb") as output, packet.zip.open(name) as source:
            while chunk := source.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
            output.flush()
            os.fsync(output.fileno())
        if digest.hexdigest() != packet.expected[name]:
            raise ValueError(f"Original hash mismatch: {name}")
        temporary.chmod(0o644)
        os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def locked(destination):
    no_symlinks(destination)
    state = destination / ".packet-subset"
    no_symlinks(state / "lock")
    state.mkdir(parents=True, exist_ok=True)
    with (state / "lock").open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        yield state


def complete(packet, destination, *, deduplicate, dry_run):
    """Hydrate missing originals; hardlinks refer only to newly restored files."""
    no_symlinks(destination)
    work = destination / packet.prefix
    if file_sha(work / "PACKET-MANIFEST.json") != packet.packet_id:
        raise ValueError("Completion requires the matching existing packet manifest")
    for name in packet.manifest.get("layout", {}).get("entry_files", {}):
        if file_sha(destination / name) != packet.expected[name]:
            raise ValueError(f"Entry file changed: {name}")
    assignment = work / "ASSIGNMENT.json"
    no_symlinks(assignment)
    if assignment.exists():
        contract = json.loads(assignment.read_bytes())
    else:
        pending = work / ".review/pending-main-draw.json"
        no_symlinks(pending)
        contract = json.loads(pending.read_bytes())["contract"]
    if packet.selection(bytes.fromhex(contract["seed"]))[0] != contract:
        raise ValueError("Completion assignment differs from original packet/seed")
    directories = {str(parent) for name in packet.files for parent in PurePosixPath(name).parents if str(parent) != "."}
    for name in directories:
        path = destination / name
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            raise ValueError(f"Unsafe destination directory: {name}")
    missing = []
    for name in sorted(packet.files):
        path = destination / name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"Unsafe destination file: {name}")
        if not path.exists():
            missing.append(name)
    plan = {"schema": "arcpuzzles-packet-completion-v1", "status": "planned",
        "packet_id": packet.packet_id, "deduplicate": deduplicate,
        "archive_files": len(packet.files), "archive_unique_hashes": len(set(packet.expected.values())),
        "archive_parent_directories": len(directories), "missing_files": len(missing),
        "missing_unique_hashes": len({packet.expected[n] for n in missing}),
        "missing_parent_directories": sum(not (destination / n).exists() for n in directories)}
    if dry_run:
        return plan
    state, representatives, restored = destination / ".packet-subset", {}, 0
    staging = state / "staging"
    no_symlinks(staging)
    staging.mkdir(exist_ok=True)
    for name in missing:
        target, digest = destination / name, packet.expected[name]
        if deduplicate and digest in representatives:
            packet.verify(name)
            no_symlinks(target)
            target.parent.mkdir(parents=True, exist_ok=True)
            os.link(representatives[digest], target)
        else:
            install(packet, name, target, staging)
            target.chmod(0o444)
            representatives[digest if deduplicate else name] = target
        restored += 1
    # Stream the exact complete inventory; never include reviewer-created paths.
    inventory = state / "completion-inventory.jsonl.gz"
    no_symlinks(inventory)
    descriptor, filename = tempfile.mkstemp(prefix="inventory-", dir=staging)
    os.close(descriptor)
    temporary, changed = Path(filename), []
    try:
        with gzip.open(temporary, "wb") as output:
            for name, original in sorted(packet.expected.items()):
                path = destination / name
                actual = file_sha(path)
                if actual != original:
                    changed.append(name)
                output.write(canonical({"path": name, "sha256": actual,
                    "original_sha256": original, "bytes": path.stat().st_size}) + b"\n")
        os.replace(temporary, inventory)
    finally:
        temporary.unlink(missing_ok=True)
    plan.update(status="complete", restored_files=restored, new_payload_inodes=len(representatives),
        created_hardlinks=restored - len(representatives), preserved_modified=changed,
        inventory={"path": str(inventory), "sha256": file_sha(inventory), "files": len(packet.files)})
    save(state / "completion.json", plan)
    return plan


def run(command, source, destination=None, *, seed=None, tasks=(), deduplicate=False, dry_run=False):
    if command not in {"verify", "extract", "add", "complete"}:
        raise ValueError(f"Unknown command: {command}")
    if seed is not None and (not isinstance(seed, bytes) or len(seed) != 32):
        raise ValueError("Draw seed must be exactly 32 bytes")
    with Packet(source) as packet:
        if command == "verify":
            for name in packet.files:
                packet.verify(name)
            return {"schema": "arcpuzzles-packet-verify-v1", "packet_id": packet.packet_id,
                    "verified_files": len(packet.files), "verified_bytes": sum(i.file_size for i in packet.files.values())}
        destination = Path(destination).absolute()
        if command == "complete" and dry_run:
            return complete(packet, destination, deduplicate=deduplicate, dry_run=True)
        with locked(destination) as state:
            if command == "complete":
                return complete(packet, destination, deduplicate=deduplicate, dry_run=False)
            work = destination / packet.prefix
            journal = state / "selection.json"
            no_symlinks(journal)
            contract_path = work / "ASSIGNMENT.json"
            no_symlinks(contract_path)
            existing = json.loads(contract_path.read_bytes()) if contract_path.exists() else None
            pending_path = work / ".review/pending-main-draw.json"
            no_symlinks(pending_path)
            pending = json.loads(pending_path.read_bytes())["contract"] if pending_path.exists() else None
            if journal.exists():
                saved = json.loads(journal.read_bytes())
                if saved.get("schema") != "arcpuzzles-subset-selection-v1" or saved.get("packet_id") != packet.packet_id:
                    raise ValueError("Invalid or foreign selection journal")
                selected_seed = bytes.fromhex(saved["seed"])
            elif command == "add":
                if not existing or file_sha(work / "PACKET-MANIFEST.json") != packet.packet_id:
                    raise ValueError("add needs an existing valid packet and assignment")
                for name in packet.manifest.get("layout", {}).get("entry_files", {}):
                    if file_sha(destination / name) != packet.expected[name]:
                        raise ValueError(f"Entry file changed: {name}")
                selected_seed = bytes.fromhex(existing["seed"])
            else:
                if existing:
                    raise ValueError("Existing assignment: adopt with add, never draw again")
                selected_seed = bytes.fromhex(pending["seed"]) if pending else seed
            if seed is not None and selected_seed is not None and seed != selected_seed:
                raise ValueError("Explicit seed conflicts with saved draw; resume without a new seed")
            if not journal.exists():
                # Reserve before randomness. A torn/empty journal blocks rerolling.
                with journal.open("xb") as stream:
                    sync_directory(journal.parent)
                    selected_seed = selected_seed if selected_seed is not None else os.urandom(32)
                    stream.write(canonical({"schema": "arcpuzzles-subset-selection-v1",
                        "packet_id": packet.packet_id, "seed": selected_seed.hex()}) + b"\n")
                    stream.flush()
                    os.fsync(stream.fileno())
            contract, initial = packet.selection(selected_seed)
            if any(value is not None and value != contract for value in (existing, pending)):
                raise ValueError("Existing assignment differs from exact packet/seed contract")
            if existing is None:
                save(pending_path,
                     {"schema": "arcpuzzles-pending-main-draw-v1", "contract": contract}, immutable=True)
            receipt = state / "inventory.json"
            no_symlinks(receipt)
            previous = json.loads(receipt.read_bytes()) if receipt.exists() else {}
            selected_tasks = initial | set(tasks) | set(previous.get("tasks", []))
            selected = packet.members(selected_tasks)
            staging = state / "staging"
            no_symlinks(staging)
            staging.mkdir(exist_ok=True)
            for name in sorted(selected):
                target = destination / name
                no_symlinks(target)
                if target.exists():
                    digest = file_sha(target)
                    if digest != packet.expected[name] and command != "add":
                        raise ValueError(f"Existing file differs; preserved unchanged: {name}")
                    packet.verify(name)
                else:
                    install(packet, name, target, staging)
            inventory = []
            for path in sorted(destination.rglob("*")):
                name = path.relative_to(destination).as_posix()
                if name in packet.expected:
                    inventory.append({"path": name, "sha256": file_sha(path), "bytes": path.stat().st_size,
                                      "original_sha256": packet.expected[name]})
            if selected - {row["path"] for row in inventory}:
                raise ValueError("Destination cannot represent all selected filenames distinctly")
            result = {"schema": "arcpuzzles-packet-subset-v1", "packet_id": packet.packet_id,
                "seed": selected_seed.hex(), "assignment_id": contract["assignment_id"],
                "task_id": contract["task_id"], "tasks": sorted(selected_tasks),
                "blind_task_id": next(iter(initial - {contract["task_id"]}), None),
                "archive_files": len(packet.files), "selected_files": len(selected),
                "present_original_files": len(inventory), "present_bytes": sum(r["bytes"] for r in inventory),
                "preserved_modified": [r["path"] for r in inventory if r["sha256"] != r["original_sha256"]],
                "inventory": inventory}
            save(receipt, result)
            return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("verify", "extract", "add", "complete"):
        child = commands.add_parser(command)
        child.add_argument("zip", type=Path)
        if command != "verify":
            child.add_argument("destination", type=Path)
        if command == "complete":
            child.add_argument("--deduplicate", action="store_true", help="Hardlink only newly restored identical files; mark them read-only")
            child.add_argument("--dry-run", action="store_true", help="Report archive/missing counts without filesystem changes")
        elif command != "verify":
            child.add_argument("--seed", help="Exactly 64 hex digits; omit to create or resume one random seed")
            child.add_argument("--task", action="append", default=[], required=command == "add")
    args = parser.parse_args()
    try:
        seed = bytes.fromhex(args.seed) if getattr(args, "seed", None) else None
        result = run(args.command, args.zip, getattr(args, "destination", None),
                     seed=seed, tasks=getattr(args, "task", ()),
                     deduplicate=getattr(args, "deduplicate", False), dry_run=getattr(args, "dry_run", False))
        print(json.dumps({k: v for k, v in result.items() if k != "inventory"}, sort_keys=True))
        return 0
    except (ValueError, KeyError, OSError, zipfile.BadZipFile) as error:
        print(f"{type(error).__name__}: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
