#!/usr/bin/env python3
"""Recover an unchanged ARCpuzzles packet sparsely after extraction ENOSPC.

Reads task bytes only as opaque hashes/copies. Default never draws or runs tasks.
This does not replace the official full-tree verify or return-package checks.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import zipfile

SCHEMA = "arcpuzzles-full-packet-v2"
VENDOR = "vendor/racket-minimal-8.10-x86_64-linux-cs.tgz"
VENDOR_SHA = "2c5fdc02787ba569f03d89cad6086a5c3be49045d58281e2db7fe31b43650eb7"
BLOCK = 1024 * 1024


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def stream_hash(stream):
    digest = hashlib.sha256()
    while block := stream.read(BLOCK):
        digest.update(block)
    return digest.hexdigest()


def file_hash(path):
    with path.open("rb") as stream:
        return stream_hash(stream)


def safe_name(name):
    if (not isinstance(name, str) or not name or "\\" in name or "\x00" in name
            or name.startswith("/") or any(p in {"", ".", ".."} for p in name.split("/"))
            or ":" in name.split("/")[0]):
        raise ValueError(f"Unsafe archive or manifest path: {name!r}")
    return name


def mkdir_safe(path):
    """Reject symlinks in every destination ancestor, including an existing root."""
    path = Path(path).absolute()
    if path.is_symlink():
        raise ValueError(f"Unsafe symlink directory: {path}")
    if path.exists():
        if not path.is_dir():
            raise ValueError(f"Not a directory: {path}")
        if path != path.parent:
            mkdir_safe(path.parent)
        return
    mkdir_safe(path.parent)
    path.mkdir(exist_ok=True)
    sync_dir(path.parent)


def sync_dir(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def atomic_bytes(path, raw, *, replace=False, mode=0o600):
    mkdir_safe(path.parent)
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError(f"Unsafe metadata destination: {path}")
    descriptor, temporary = tempfile.mkstemp(prefix=".recovery-write-", dir=path.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fchmod(stream.fileno(), mode)
            os.fsync(stream.fileno())
        if replace:
            os.replace(temporary, path)
        else:
            os.link(temporary, path)  # No replacement, including a concurrent writer.
        sync_dir(path.parent)
    finally:
        temporary.unlink(missing_ok=True)


def verify_archive(archive):
    """Verify all sources streaming, without decoding/displaying task content."""
    members = {}
    for info in archive.infolist():
        name = safe_name(info.filename[:-1] if info.is_dir() else info.filename)
        kind = stat.S_IFMT(info.external_attr >> 16)
        if kind not in {0, stat.S_IFDIR if info.is_dir() else stat.S_IFREG} or info.flag_bits & 1:
            raise ValueError(f"Unsafe archive member type: {name}")
        if info.filename in members:
            raise ValueError(f"Duplicate archive member: {name}")
        members[info.filename] = info
    raw = archive.read("WORK/PACKET-MANIFEST.json")
    manifest = json.loads(raw)
    if manifest.get("schema") != SCHEMA or canonical(manifest) != raw:
        raise ValueError("Manifest schema or canonical encoding differs")
    layout = manifest.get("layout", {})
    if layout.get("workspace") != "WORK" or set(layout.get("entry_files", {})) != {"START-HERE.md", "review.py"}:
        raise ValueError("Unsupported packet workspace layout")
    expected = {"WORK/" + safe_name(n): h for n, h in manifest["files"].items()}
    expected.update({safe_name(n): h for n, h in layout["entry_files"].items()})
    expected["WORK/PACKET-MANIFEST.json"] = hashlib.sha256(raw).hexdigest()
    actual = {n for n, info in members.items() if not info.is_dir()}
    if set(expected) != actual:
        raise ValueError("Archive members differ from manifest inventory")
    for name, digest in expected.items():
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError(f"Invalid manifest hash: {name}")
        with archive.open(name) as stream:
            if stream_hash(stream) != digest:
                raise ValueError(f"Hash mismatch in archive: {name}")
    if VENDOR in manifest["files"] and manifest["files"][VENDOR] != VENDOR_SHA:
        raise ValueError("Bundled Racket hash differs from pinned upstream archive")
    return manifest, expected


def selections(manifest, seed):
    pool = manifest["main_ids"]
    if not pool:
        raise ValueError("Empty main task pool")
    main = pool[int.from_bytes(seed, "big") % len(pool)]
    pool = sorted(t for t, r in manifest["generators"].items() if r.get("approved") and t != main)
    pool = pool or sorted(t for t in manifest["all_ids"] if t != main)
    if not pool:
        raise ValueError("No blind task available")
    blind = pool[int.from_bytes(hashlib.sha256(seed + b":blind").digest(), "big") % len(pool)]
    questions = sorted(manifest["questions"], key=lambda row: row["id"])
    question = questions[int.from_bytes(hashlib.sha256(seed + b":question").digest(), "big") % len(questions)]["id"]
    return main, blind, question


def closure(archive, manifest, main, blind, question, tasks):
    all_files = manifest["files"]
    for tid in tasks:
        if tid not in manifest["generators"]:
            raise ValueError(f"Unknown task ID: {tid}")
    task_ids = {main, blind, *tasks}
    wanted = task_ids | {manifest["generators"][t]["rule_task_id"] for t in task_ids}
    selected = {"WORK/PACKET-MANIFEST.json", *manifest["layout"]["entry_files"]}
    prefixes = ("repo/catalog/", "repo/src/", "repo/docs/", "repo/GUIDE/", "repo/tests/", "repo/tools/")
    for name in all_files:
        parts = name.split("/")
        if ("/" not in name or name.startswith(prefixes)
                or (len(parts) == 2 and parts[0] == "repo")
                or any(name.startswith(f"repo/generators/{t}/") for t in task_ids)):
            selected.add("WORK/" + name)
    for name in ["repo/shared/data/canonical/puzzles.jsonl", f"repo/REVIEW/questions/{question}.json"]:
        selected.add("WORK/" + name)
    if VENDOR in all_files:
        selected.add("WORK/" + VENDOR)
    mappings = json.loads(archive.read("WORK/repo/catalog/runtime_files.json"))
    authorities = json.loads(archive.read("WORK/repo/catalog/authority_files.json"))
    for row in mappings:
        relative, target = safe_name(row["path"]), safe_name(row["target"])
        if relative.startswith("generators/") and relative.split("/")[1] not in wanted:
            continue
        if target.startswith("data/base/solutions/") and authorities.get(target) not in wanted:
            continue
        selected.add("WORK/repo/" + relative)
    return sorted(selected)


def editable_baseline(archive, manifest, main):
    """Exact draw baseline: only these prior sources may change before hydration."""
    paths = {"WORK/" + n for n in manifest["files"] if n.startswith(f"repo/generators/{main}/")}
    paths.add("WORK/repo/shared/data/canonical/puzzles.jsonl")
    wanted = {main, manifest["generators"][main]["rule_task_id"]}
    authorities = json.loads(archive.read("WORK/repo/catalog/authority_files.json"))
    for row in json.loads(archive.read("WORK/repo/catalog/runtime_files.json")):
        if row["target"].startswith("data/base/solutions/") and authorities.get(row["target"]) in wanted:
            paths.add("WORK/repo/" + row["path"])
    return paths


def load_receipt(state_dir, binding):
    """Check the immutable hash chain before trusting previously materialized paths."""
    pointer = state_dir / "extraction.json"
    if pointer.is_symlink():
        raise ValueError("Unsafe extraction receipt pointer")
    if not pointer.exists():
        return None, None
    if not pointer.is_file():
        raise ValueError("Unsafe extraction receipt pointer type")
    reference = json.loads(pointer.read_bytes())
    latest = reference
    receipt = None
    successor_files = None
    seen = set()
    while reference:
        name = reference["filename"]
        if not re.fullmatch(r"materialization-[0-9]{6}.json", name) or name in seen:
            raise ValueError("Invalid extraction receipt history")
        seen.add(name)
        path = state_dir / name
        if path.is_symlink() or not path.is_file() or file_hash(path) != reference["sha256"]:
            raise ValueError("Extraction receipt history hash differs")
        event = json.loads(path.read_bytes())
        if event.get("schema") != "arcpuzzles-sparse-extraction-v1" or not isinstance(event.get("files"), dict):
            raise ValueError("Invalid extraction receipt schema")
        if any(event.get(k) != binding[k] for k in ("archive_sha256", "manifest_sha256")):
            raise ValueError("Extraction receipt archive/manifest binding differs")
        if successor_files is not None and any(successor_files.get(n) != h for n, h in event["files"].items()):
            raise ValueError("Extraction receipt inventory is not cumulative")
        successor_files = event["files"]
        if receipt is None:
            receipt = event
        reference = event["previous_receipt"]
    return receipt, latest


def validate_draw_bindings(work, seed, main, blind, packet_id):
    completed = False
    for name, pending in [("ASSIGNMENT.json", False), (".review/pending-main-draw.json", True)]:
        path = work / name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise ValueError(f"Unsafe existing draw contract: {name}")
        if path.exists():
            value = json.loads(path.read_bytes())
            value = value["contract"] if pending else value
            if (value.get("seed") != seed.hex() or value.get("task_id") != main
                    or value.get("packet_id") != packet_id):
                raise ValueError("Existing draw contract differs from saved recovery seed binding")
            completed |= not pending
    path = work / "BLIND_ASSIGNMENT.json"
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("Unsafe blind assignment path")
    if path.exists():
        value = json.loads(path.read_bytes())
        if value.get("task_id") != blind or value.get("packet_id") != packet_id:
            raise ValueError("Existing blind contract differs from saved recovery seed binding")
    return completed


def extract_one(archive, name, destination, digest):
    mkdir_safe(destination.parent)
    if destination.is_symlink() or (destination.exists() and not destination.is_file()):
        raise ValueError(f"Unsafe extraction destination: {destination}")
    if destination.is_file():
        if file_hash(destination) != digest:
            raise ValueError(f"Changed local source; refusing overwrite: {destination}")
        return
    descriptor, temporary = tempfile.mkstemp(prefix=".recovery-extract-", dir=destination.parent)
    temporary = Path(temporary)
    try:
        checksum = hashlib.sha256()
        with os.fdopen(descriptor, "wb") as output, archive.open(name) as source:
            while block := source.read(BLOCK):
                checksum.update(block)
                output.write(block)
            output.flush()
            os.fchmod(output.fileno(), 0o644)
            os.fsync(output.fileno())
        if checksum.hexdigest() != digest:
            raise ValueError(f"Hash mismatch during extraction: {name}")
        os.link(temporary, destination)  # Publish without replacing existing data.
        sync_dir(destination.parent)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def recovery_lock(target):
    state_dir = target / ".recovery"
    mkdir_safe(state_dir)
    lock = state_dir / "lock"
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "a+b") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ValueError("Unsafe recovery lock type")
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield state_dir
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


@contextmanager
def official_module(work):
    source = work / "repo/src"
    sys.path.insert(0, str(source))
    try:
        import arcpuzzles
        if not Path(arcpuzzles.__file__).resolve().is_relative_to(source.resolve()):
            raise ValueError("Different arcpuzzles package already loaded")
        from arcpuzzles import review_full_draw
        yield review_full_draw
    finally:
        sys.path.pop(0)


def official_draw(work, seed, main, blind):
    with official_module(work) as module:
        contract = module.draw_main(work, seed=seed)
        if contract["seed"] != seed.hex() or contract["task_id"] != main:
            raise ValueError("Official draw differs from persisted recovery selection")
        blind_path = work / "BLIND_ASSIGNMENT.json"
        if blind_path.exists() and json.loads(blind_path.read_bytes())["task_id"] != blind:
            raise ValueError("Official blind task differs from recovery selection")
        return contract["assignment_id"]


def saved_audit_seed(state_dir, binding, work):
    path = state_dir / "audit-seed.json"
    expected = {**binding, "schema": "arcpuzzles-sparse-recovery-audit-seed-v1"}
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("Unsafe saved audit seed path")
    if path.exists():
        value = json.loads(path.read_bytes())
        if any(value.get(k) != v for k, v in expected.items()):
            raise ValueError("Saved audit seed archive/manifest binding differs")
        seed = bytes.fromhex(value["seed"])
        if len(seed) != 32:
            raise ValueError("Invalid persisted audit seed length")
        return seed
    if (work / "AUDIT_ASSIGNMENT.json").exists() or (work / "AUDIT_ASSIGNMENT.json").is_symlink():
        raise ValueError("Existing audit assignment without saved audit seed; refusing a new audit seed")
    seed = os.urandom(32)
    atomic_bytes(path, canonical({**expected, "seed": seed.hex()}) + b"\n")
    return seed


def audit_selection(work, manifest, blind, seed):
    pool = [tid for tid in manifest["all_ids"] if tid != blind]
    if len(pool) < 2:
        raise ValueError("Audit draw needs two tasks besides the blind assignment")
    with official_module(work) as module:
        ids = module.audit_ids_for_seed(pool, seed)
    if len(ids) != 2 or len(set(ids)) != 2 or any(tid not in pool for tid in ids):
        raise ValueError("Invalid official audit task selection")
    return ids


def expected_audit_contract(manifest, packet_id, seed, ids):
    return {"schema": "arcpuzzles-full-audit-v3", "packet_id": packet_id, "seed": seed.hex(),
            "targets": [{"task_id": tid, "generator_sha256": manifest["files"][
                "repo/" + manifest["generators"][tid]["generator"]]} for tid in ids]}


def verify_audit_contract(work, expected, *, required=False):
    path = work / "AUDIT_ASSIGNMENT.json"
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("Unsafe audit assignment path")
    if path.exists():
        if json.loads(path.read_bytes()) != expected:
            raise ValueError("Existing audit assignment differs from saved audit seed binding")
        return file_hash(path)
    if required:
        raise ValueError("Official audit assignment was not persisted")
    return None


def recover(archive_path, target, *, tasks=(), draw=False, audit_draw=False, verify_only=False):
    if (draw and audit_draw) or (audit_draw and tasks) or (verify_only and (draw or audit_draw or tasks)):
        raise ValueError("Use audit-draw, main draw, task hydration, and archive verification as separate operations")
    archive_path, target = Path(archive_path).absolute(), Path(target).absolute()
    if archive_path.is_symlink() or not archive_path.is_file():
        raise ValueError("Archive must be a regular file, not a symlink")
    archive_sha = file_hash(archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        manifest, expected = verify_archive(archive)
        # Detect replacement/mutation during verification before writing any state.
        if file_hash(archive_path) != archive_sha:
            raise ValueError("Archive changed during verification")
        manifest_sha = expected["WORK/PACKET-MANIFEST.json"]
        if verify_only:
            return {"archive_sha256": archive_sha, "manifest_sha256": manifest_sha,
                    "verified_files": len(expected), "mode": "verify-archive"}
        with recovery_lock(target) as state_dir:
            seed_path = state_dir / "seed.json"
            binding = {"schema": "arcpuzzles-sparse-recovery-seed-v1", "archive_sha256": archive_sha,
                       "manifest_sha256": manifest_sha}
            if seed_path.is_symlink() or (seed_path.exists() and not seed_path.is_file()):
                raise ValueError("Unsafe saved seed path")
            if seed_path.exists():
                state = json.loads(seed_path.read_bytes())
                if {k: state.get(k) for k in binding} != binding:
                    raise ValueError("Saved seed archive/manifest binding differs; refusing a new draw")
                seed = bytes.fromhex(state["seed"])
                if len(seed) != 32:
                    raise ValueError("Invalid persisted seed length")
            else:
                if any((target / "WORK" / n).exists() for n in (
                        "ASSIGNMENT.json", "BLIND_ASSIGNMENT.json", ".review/pending-main-draw.json")):
                    raise ValueError("Existing draw without recovery seed; refusing a new seed")
                seed = os.urandom(32)
                atomic_bytes(seed_path, canonical({**binding, "seed": seed.hex()}) + b"\n")
            # IDs are deliberately derived only after the seed's durable publication.
            main, blind, question = selections(manifest, seed)
            completed_draw = validate_draw_bindings(target / "WORK", seed, main, blind, manifest_sha)
            previous, previous_reference = load_receipt(state_dir, binding)
            audit_ids = []
            audit_expected = None
            if audit_draw:
                if not completed_draw or previous is None:
                    raise ValueError("Audit recovery requires a completed main draw and its extraction receipt")
                if not (target / "WORK/BLIND_ASSIGNMENT.json").is_file():
                    raise ValueError("Audit recovery requires the persisted blind assignment to exclude its task")
                # Selection imports the official helper before target hydration;
                # verify its complete local source package before executing it.
                for name, digest in manifest["files"].items():
                    if name.startswith("repo/src/"):
                        path = target / "WORK" / name
                        if (any(p.is_symlink() for p in (path, *path.parents))
                                or not path.is_file() or file_hash(path) != digest):
                            raise ValueError("Changed or missing official helper source: " + name)
                audit_seed = saved_audit_seed(state_dir, binding, target / "WORK")
                # The independent audit seed is durable before calling the
                # official selection function or materializing either target.
                audit_ids = audit_selection(target / "WORK", manifest, blind, audit_seed)
                audit_expected = expected_audit_contract(manifest, manifest_sha, audit_seed, audit_ids)
                verify_audit_contract(target / "WORK", audit_expected)
            additional = set(tasks) | set(previous["additional_task_ids"] if previous else [])
            additional.update(audit_ids)
            names = closure(archive, manifest, main, blind, question, additional)
            missing = set(names) - expected.keys()
            if missing:
                raise ValueError("Required extraction sources absent from manifest: " + ", ".join(sorted(missing)))
            old_files = previous["files"] if previous else {}
            if any(expected.get(n) != digest for n, digest in old_files.items()):
                raise ValueError("Previous materialization inventory differs from manifest")
            # Only explicit later --task hydration preserves edits. Ordinary resume
            # remains strict, so accidental pre-draw local changes never disappear.
            preserved = (editable_baseline(archive, manifest, main) & old_files.keys()
                         if previous and (tasks or audit_draw) and completed_draw else set())
            for name in names:
                if name in preserved:
                    path = target / name
                    mkdir_safe(path.parent)
                    if path.is_symlink() or not path.is_file():
                        raise ValueError(f"Missing or unsafe previously materialized baseline: {path}")
                    continue
                extract_one(archive, name, target / name, expected[name])
            receipt = {**binding, "schema": "arcpuzzles-sparse-extraction-v1",
                       "main_task_id": main, "blind_task_id": blind, "question_id": question,
                       "additional_task_ids": sorted(additional), "workspace": str(target / "WORK"),
                       "seed_file": str(seed_path), "files": {**old_files, **{n: expected[n] for n in names}},
                       "previous_receipt": previous_reference,
                       "preserved_baseline_paths": sorted(preserved),
                       "materialized_files": len(names), "verified_files": len(expected),
                       "materialized_bytes": sum(archive.getinfo(n).file_size for n in names),
                       "full_tree_verify_supported": False}
            if audit_draw:
                receipt.update(audit_task_ids=audit_ids, audit_seed_file=str(state_dir / "audit-seed.json"))
            if draw:
                receipt["assignment_id"] = official_draw(target / "WORK", seed, main, blind)
            number = 1
            while (state_dir / f"materialization-{number:06d}.json").exists():
                number += 1
            receipt_path = state_dir / f"materialization-{number:06d}.json"
            raw = canonical(receipt) + b"\n"
            atomic_bytes(receipt_path, raw, mode=0o444)
            atomic_bytes(state_dir / "extraction.json", canonical({"filename": receipt_path.name,
                         "sha256": hashlib.sha256(raw).hexdigest()}) + b"\n", replace=True)
            if audit_draw:
                # Source inventory is committed first, so a later draw failure
                # never loses the fact that these original paths were hydrated.
                with official_module(target / "WORK") as module:
                    contract = module.draw_audit(target / "WORK", seed=audit_seed)
                if contract != audit_expected:
                    raise ValueError("Official audit result differs from saved audit seed binding")
                receipt["audit_assignment_sha256"] = verify_audit_contract(target / "WORK", audit_expected, required=True)
                receipt["audit_assignment_file"] = str(target / "WORK/AUDIT_ASSIGNMENT.json")
            return {**{k: v for k, v in receipt.items() if k not in {
                "files", "schema", "preserved_baseline_paths", "previous_receipt"}},
                "preserved_baseline_files": len(preserved), "receipt_file": str(receipt_path),
                "receipt_sha256": hashlib.sha256(raw).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("target", type=Path, nargs="?", default=Path("packet"))
    parser.add_argument("--task", action="append", default=[], help="Hydrate an additional task; never draws audit targets")
    parser.add_argument("--draw", action="store_true", help="Explicitly invoke official draw_main with the persisted seed")
    parser.add_argument("--audit-draw", action="store_true", help="Persist one audit seed, hydrate its two targets, then invoke official draw_audit")
    parser.add_argument("--verify-archive", action="store_true", help="Verify the complete original ZIP without creating files")
    args = parser.parse_args()
    if ((args.verify_archive and (args.draw or args.audit_draw or args.task))
            or (args.audit_draw and (args.draw or args.task))):
        parser.error("Use --audit-draw separately from --draw, --task, and --verify-archive")
    try:
        result = recover(args.archive, args.target, tasks=args.task, draw=args.draw,
                         audit_draw=args.audit_draw, verify_only=args.verify_archive)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(2, f"Recovery stopped: {error}\nReuse the same target and original archive to resume; do not replace its seed.\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
