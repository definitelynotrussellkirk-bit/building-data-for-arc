#!/usr/bin/env python3
"""Proposed ARC startup capacity and opaque pending checkpoint helper.

Python 3.10+, standard library only. Never invokes a draw, edits WORK, reads
puzzle/source contents, or restores assignment records. JSON output is aggregate.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile

try:
    import fcntl
except ImportError:  # Reporting still works; checkpoints require this lock API.
    fcntl = None

MIB = 1024 * 1024
MANIFEST_LIMIT = 32 * MIB
RECORD_LIMIT = 4 * MIB
CANONICAL = "repo/shared/data/canonical/puzzles.jsonl"
PENDING = ".review/pending-main-draw.json"
SHA = re.compile(r"[0-9a-f]{64}\Z")


class GuardError(ValueError):
    """A stable, content-free failure code suitable for JSON output."""


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def reject_links(path):
    for part in reversed((path, *path.parents)):
        if part.is_symlink():
            raise GuardError("symlink_path_not_supported")


def metadata_stat(path, *, missing=False, directory=False):
    reject_links(path)
    try:
        value = path.lstat()
    except FileNotFoundError:
        if missing:
            return None
        raise GuardError("required_path_missing") from None
    if not (stat.S_ISDIR(value.st_mode) if directory else stat.S_ISREG(value.st_mode)):
        raise GuardError("nonregular_metadata_or_source_path")
    return value


def regular_bytes(path, limit):
    """Read bounded control metadata only, refusing symlinks and special files."""
    initial = metadata_stat(path)
    if initial.st_size > limit:
        raise GuardError("metadata_size_limit_exceeded")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (initial.st_dev, initial.st_ino) != (opened.st_dev, opened.st_ino):
            raise GuardError("metadata_changed_while_opening")
        raw = stream.read(limit + 1)
        final = os.fstat(stream.fileno())
    if len(raw) > limit:
        raise GuardError("metadata_size_limit_exceeded")
    if (opened.st_size, opened.st_mtime_ns) != (final.st_size, final.st_mtime_ns):
        raise GuardError("metadata_changed_during_read")
    return raw


def parse_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise GuardError("duplicate_json_metadata_key")
            value[key] = item
        return value
    try:
        result = json.loads(raw, object_pairs_hook=pairs)
    except (ValueError, UnicodeError) as error:
        if isinstance(error, GuardError):
            raise
        raise GuardError("invalid_json_metadata") from None
    if not isinstance(result, dict):
        raise GuardError("metadata_object_required")
    return result


def baseline_name(name):
    if not isinstance(name, str):
        raise GuardError("unsafe_baseline_path")
    value = PurePosixPath(name)
    if (not name or value.is_absolute() or len(value.parts) < 2 or
            value.parts[0] != "repo" or ".." in value.parts or
            str(value) != name or "\\" in name or ":" in name or "\x00" in name):
        raise GuardError("unsafe_baseline_path")
    return value


def validate_manifest(raw):
    manifest = parse_json(raw)
    if manifest.get("schema") != "arcpuzzles-full-packet-v2" or not isinstance(manifest.get("files"), dict):
        raise GuardError("unsupported_packet_manifest")
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False,
                           separators=(",", ":")).encode()
    if raw != canonical:
        raise GuardError("noncanonical_packet_manifest")
    for name, expected in manifest["files"].items():
        if not isinstance(name, str) or not isinstance(expected, str) or not SHA.fullmatch(expected):
            raise GuardError("invalid_manifest_file_inventory")
    return manifest


def validate_contract(contract, manifest, packet_hash):
    if (not isinstance(contract, dict) or
            contract.get("schema") != "arcpuzzles-full-assignment-v2" or
            contract.get("packet_id") != packet_hash):
        raise GuardError("assignment_packet_binding_mismatch")
    seed = contract.get("seed")
    if not isinstance(seed, str) or not SHA.fullmatch(seed):
        raise GuardError("invalid_pending_seed_encoding")
    identity = "review-" + digest(bytes.fromhex(packet_hash) + bytes.fromhex(seed))[:16]
    if contract.get("assignment_id") != identity:
        raise GuardError("assignment_identity_mismatch")
    baseline = contract.get("baseline_sha256")
    if not isinstance(baseline, dict) or not baseline:
        raise GuardError("invalid_baseline_inventory")
    for name, expected in baseline.items():
        baseline_name(name)
        if not isinstance(expected, str) or not SHA.fullmatch(expected) or manifest["files"].get(name) != expected:
            raise GuardError("baseline_manifest_binding_mismatch")
    return baseline


def validate_records(records):
    manifest_raw = records["PACKET-MANIFEST.json"]
    manifest = validate_manifest(manifest_raw)
    packet_hash = digest(manifest_raw)
    pending = records.get("pending-main-draw.json")
    assigned = records.get("ASSIGNMENT.json")
    contract = None
    if pending is not None:
        journal = parse_json(pending)
        if journal.get("schema") != "arcpuzzles-pending-main-draw-v1":
            raise GuardError("unsupported_pending_journal")
        contract = journal.get("contract")
        validate_contract(contract, manifest, packet_hash)
    if assigned is not None:
        assignment = parse_json(assigned)
        validate_contract(assignment, manifest, packet_hash)
        if contract is not None and assignment != contract:
            raise GuardError("conflicting_assignment_and_pending")
        contract = assignment
    state = ("pending_finalization" if assigned is not None else "pending_only") if pending is not None else (
        "completed" if assigned is not None else "unstarted")
    return state, manifest, contract, packet_hash


def read_records(work):
    records = {"PACKET-MANIFEST.json": regular_bytes(work / "PACKET-MANIFEST.json", MANIFEST_LIMIT)}
    for filename, relative in (("pending-main-draw.json", PENDING), ("ASSIGNMENT.json", "ASSIGNMENT.json")):
        path = work / relative
        if metadata_stat(path, missing=True) is not None:
            records[filename] = regular_bytes(path, RECORD_LIMIT)
    return records


@contextmanager
def draw_lock(work, *, required=False):
    """Join the official flock protocol without creating or writing its lock."""
    path = work / ".review/main-draw.lock"
    info = metadata_stat(path, missing=True)
    if info is None or fcntl is None:
        if required:
            raise GuardError("existing_posix_draw_lock_required")
        yield "absent" if info is None else "unsupported"
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino):
            raise GuardError("draw_lock_changed")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            raise GuardError("draw_in_progress") from None
        try:
            yield "shared_official_flock"
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def work_path(path):
    path = Path(path).absolute()
    metadata_stat(path, directory=True)
    return path.resolve()


def nearest_existing(path):
    path = Path(path).absolute()
    while not path.exists():
        if path.parent == path:
            raise GuardError("filesystem_probe_path_missing")
        path = path.parent
    return path


def filesystem_snapshot(path):
    path = nearest_existing(path)
    filesystem, mountpoint = "unknown", None
    try:
        for line in Path("/proc/self/mountinfo").read_text().splitlines():
            left, right = line.split(" - ", 1)
            point = Path(re.sub(r"\\([0-7]{3})", lambda match: chr(int(match[1], 8)), left.split()[4]))
            if path == point or point in path.parents:
                if mountpoint is None or len(str(point)) > len(mountpoint):
                    filesystem, mountpoint = right.split()[0], str(point)
    except (OSError, ValueError, IndexError):
        pass
    if hasattr(os, "statvfs"):
        values = os.statvfs(path)
        block = values.f_frsize or values.f_bsize
        available = values.f_bavail * block
        free = values.f_bfree * block
        inodes = values.f_favail if values.f_files else None
    else:
        block, inodes = 4096, None
        available = free = shutil.disk_usage(path).free
    return {"filesystem": filesystem, "mountpoint": mountpoint,
            "probed_path": str(path), "block_size": block,
            "available_bytes": available, "free_bytes_including_reserved": free,
            "available_inodes": inodes}


def memory_snapshot(cgroup_root=Path("/sys/fs/cgroup"), meminfo=Path("/proc/meminfo"),
                    membership=Path("/proc/self/cgroup")):
    cgroup_root = Path(cgroup_root)
    candidates = [cgroup_root]
    warnings, groups = [], []
    membership_found = False
    try:
        for line in Path(membership).read_text().splitlines():
            if line.startswith("0::"):
                membership_found = True
                relative = PurePosixPath(line[3:].lstrip("/"))
                if line[3:].startswith("/") and ".." not in relative.parts:
                    active = cgroup_root.joinpath(*relative.parts)
                    if active.is_dir():
                        candidates = [active] + [p for p in active.parents
                                                if p == cgroup_root or cgroup_root in p.parents]
                    else:
                        warnings.append("cgroup_membership_unresolved")
                else:
                    warnings.append("cgroup_membership_unresolved")
        if not membership_found:
            warnings.append("cgroup_v2_membership_not_found")
    except (OSError, UnicodeError, ValueError):
        warnings.append("cgroup_membership_unreadable_or_invalid")
    for group in dict.fromkeys(candidates):
        try:
            raw_max = (group / "memory.max").read_text().strip()
            maximum = None if raw_max == "max" else int(raw_max)
            current = int((group / "memory.current").read_text())
            if current < 0 or (maximum is not None and maximum < 0):
                raise ValueError
            groups.append({"path": str(group), "max_bytes": maximum,
                           "current_bytes": current,
                           "headroom_bytes": None if maximum is None else max(0, maximum - current)})
        except (OSError, ValueError):
            warnings.append("cgroup_level_unreadable_or_invalid")
    host = None
    try:
        for line in Path(meminfo).read_text().splitlines():
            if line.startswith("MemAvailable:"):
                host = int(line.split()[1]) * 1024
                if host < 0:
                    host = None
    except (OSError, ValueError, IndexError):
        pass
    limits = [group["headroom_bytes"] for group in groups if group["headroom_bytes"] is not None]
    if host is not None:
        limits.append(host)
    return {"host_available_bytes": host, "cgroup_v2": groups,
            "cgroup_v2_complete": bool(groups) and not warnings,
            "effective_available_bytes": min(limits) if limits else None,
            "warnings": sorted(set(warnings)),
            "scope": "Visible cgroup-v2 levels and host MemAvailable only; hidden limits and other processes are not attributable."}


def estimate_start(work, state, manifest, contract, block):
    baseline = work / ".review/baseline"
    if state == "unstarted":
        existing = metadata_stat(baseline, missing=True, directory=True)
        if existing is not None and next(baseline.iterdir(), None) is not None:
            raise GuardError("unjournaled_baseline")
        names = [name for name in manifest["files"] if name.startswith("repo/")]
        scope = "all_manifest_repo_files_selection_unknown"
    elif state == "completed":
        names, scope = [], "idempotent_start_no_baseline_copy"
    else:
        names = list(contract["baseline_sha256"])
        scope = "pending_manifest_bound_baseline"
    staging = work / ".review/main-draw-staging"
    staging_device = nearest_existing(staging).stat().st_dev
    missing_bytes = upper_bytes = largest = existing_count = mismatch_count = missing_count = 0
    directories = set()
    for name in names:
        pure = baseline_name(name)
        source = work.joinpath(*pure.parts)
        source_stat = metadata_stat(source)
        target = baseline.joinpath(*pure.parts)
        target_stat = metadata_stat(target, missing=True)
        if nearest_existing(target.parent).stat().st_dev != staging_device:
            raise GuardError("split_baseline_and_staging_filesystems_unsupported")
        allocation = ((source_stat.st_size + block - 1) // block) * block
        upper_bytes += allocation
        largest = max(largest, source_stat.st_size, target_stat.st_size if target_stat else 0)
        if target_stat is None:
            missing_count += 1
            if state != "unstarted" or name == CANONICAL:
                missing_bytes += allocation
        else:
            existing_count += 1
            mismatch_count += target_stat.st_size != source_stat.st_size
        for parent in target.parents:
            if parent == work:
                break
            if metadata_stat(parent, missing=True, directory=True) is None:
                directories.add(parent)
    if names:
        for parent in (staging, staging.parent):
            if metadata_stat(parent, missing=True, directory=True) is None:
                directories.add(parent)
    directory_bytes = len(directories) * block
    # Atomic rename reuses the staged file allocation; do not double its bytes.
    # A single temporary inode plus five small control records are budgeted.
    overhead_inodes = 6 if names else 0
    return {"scope": scope, "candidate_baseline_files": len(names),
            "missing_baseline_bytes": missing_bytes,
            "copy_bytes_upper_bound": upper_bytes,
            "existing_unverified_files": existing_count,
            "existing_size_mismatch_files": mismatch_count,
            "missing_candidate_files": missing_count,
            "missing_directory_count_upper_bound": len(directories),
            "directory_bytes_upper_bound": directory_bytes,
            "allocation_bytes_upper_bound": upper_bytes + directory_bytes,
            "inode_count_upper_bound": missing_count + len(directories) + overhead_inodes,
            "largest_whole_file_hash_buffer_bytes": largest,
            "model": "Dense copies rounded to destination blocks, one block per missing directory; all existing baselines remain unverified candidates."}


def report(work, reserve_bytes=512*MIB, reserve_inodes=128):
    if reserve_bytes < 0 or reserve_inodes < 0:
        raise GuardError("negative_reserve")
    work = work_path(work)
    with draw_lock(work) as locking:
        records = read_records(work)
        state, manifest, contract, packet_hash = validate_records(records)
        fs = filesystem_snapshot(work / ".review/main-draw-staging")
        memory = memory_snapshot()
        estimate = estimate_start(work, state, manifest, contract, fs["block_size"])
        if read_records(work) != records:
            raise GuardError("workspace_metadata_changed_during_report")
    disk_needed = estimate["allocation_bytes_upper_bound"] + reserve_bytes
    inode_needed = estimate["inode_count_upper_bound"] + reserve_inodes
    tmpfs = fs["filesystem"] in ("tmpfs", "ramfs")
    memory_needed = estimate["largest_whole_file_hash_buffer_bytes"] + reserve_bytes
    if tmpfs or fs["filesystem"] == "unknown":
        memory_needed += estimate["allocation_bytes_upper_bound"]
    failures, warnings = [], list(memory.get("warnings", []))
    if fs["available_bytes"] < disk_needed:
        failures.append("insufficient_disk_bytes")
    if fs["available_inodes"] is None:
        warnings.append("inode_availability_unknown")
    elif fs["available_inodes"] < inode_needed:
        failures.append("insufficient_inodes")
    if memory["effective_available_bytes"] is None:
        warnings.append("memory_headroom_unknown")
    elif memory["effective_available_bytes"] < memory_needed:
        failures.append("insufficient_memory_headroom")
    if fs["filesystem"] == "unknown":
        warnings.append("filesystem_type_unknown_memory_backed_cost_included")
    if tmpfs:
        warnings.append("memory_backed_storage_is_volatile")
    if locking != "shared_official_flock":
        warnings.append("official_draw_lock_not_held")
    unknown = (fs["available_inodes"] is None or memory["effective_available_bytes"] is None
               or fs["filesystem"] == "unknown" or not memory.get("cgroup_v2_complete", True))
    return {"schema": "arc-start-capacity-report-v1", "status": "blocked" if failures else "indeterminate" if unknown else "ready",
            "created_at": datetime.now(timezone.utc).isoformat(), "work": str(work),
            "draw_state": state, "review_completion_assessed": False,
            "packet_manifest_sha256": packet_hash, "locking": locking,
            "filesystem": fs, "memory": memory, "estimate": estimate,
            "requirements": {"available_disk_bytes": disk_needed, "available_inodes": inode_needed,
                             "available_memory_bytes": memory_needed},
            "reserves": {"bytes": reserve_bytes, "inodes": reserve_inodes},
            "failures": failures, "warnings": sorted(set(warnings)),
            "limitations": [
                "This is an advisory modeled estimate, not an enforced quota or a guarantee against concurrent use.",
                "Source and existing baseline content hashes are not verified; only metadata, paths and manifest bindings are checked.",
                "Upper bounds refer to the declared dense-copy model; filesystem metadata, control-file bytes, allocator behavior and runtime overhead rely on the configured reserve.",
                "Existing tmpfs storage is already charged to observed memory; only additional modeled allocation is added to required headroom.",
                "The hash buffer models the current whole-file reads in review.py/review_full_draw.py; Python/JSON and other runtime peaks are not measured.",
                "Completed means the startup journal is absent and an assignment exists; no review duties or semantic gates are assessed.",
                "The original packet must be independently verified; this tool neither authenticates issued metadata nor validates task selection semantics."
            ]}


def sync_directory(path):
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        return True
    except OSError:
        return False


def write_exclusive(path, raw):
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def publish_receipt(destination, receipt):
    descriptor, name = tempfile.mkstemp(prefix=".receipt-", dir=destination)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(json_bytes(receipt))
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, destination / "CHECKPOINT.json")
    finally:
        temporary.unlink(missing_ok=True)
    sync_directory(destination)


def checkpoint_pending(work, destination):
    work = work_path(work)
    destination = Path(destination).absolute()
    resolved_destination = destination.resolve()
    if resolved_destination == work or work in resolved_destination.parents:
        raise GuardError("checkpoint_destination_inside_work")
    if destination.exists() or destination.is_symlink():
        raise GuardError("checkpoint_destination_exists")
    metadata_stat(destination.parent, directory=True)
    if metadata_stat(work / PENDING, missing=True) is None:
        raise GuardError("pending_journal_required")
    with draw_lock(work, required=True):
        records = read_records(work)
        state, _, _, packet_hash = validate_records(records)
        if "pending-main-draw.json" not in records:
            raise GuardError("pending_journal_required")
        destination.mkdir(mode=0o700)  # Exclusive; partial failures are retained.
        parent_synced = sync_directory(destination.parent)
        files = {}
        for name, raw in records.items():
            path = destination / name
            write_exclusive(path, raw)
            limit = MANIFEST_LIMIT if name == "PACKET-MANIFEST.json" else RECORD_LIMIT
            saved = regular_bytes(path, limit)
            if saved != raw:
                raise GuardError("checkpoint_copy_verification_failed")
            files[name] = {"bytes": len(raw), "sha256": digest(saved)}
        if read_records(work) != records:
            raise GuardError("workspace_metadata_changed_during_checkpoint")
        synced = sync_directory(destination)
        receipt = {"schema": "arc-start-pending-checkpoint-v1", "status": "checkpointed",
                   "created_at": datetime.now(timezone.utc).isoformat(),
                   "source_state": state, "packet_manifest_sha256": packet_hash,
                   "files": files, "directory_fsync_supported": synced,
                   "parent_directory_fsync_supported": parent_synced,
                   "scope": "Exact control metadata only; no baseline, source, solve or check artifacts.",
                   "restore_supported": False,
                   "limitations": "Helper-only checkpoint, incompatible with resource_guard.py restore. No replay certification. Storage durability is independent; tmpfs is volatile."}
        publish_receipt(destination, receipt)
        # Verify saved bytes and their relationships before reporting success.
        try:
            verify_checkpoint(destination)
        except BaseException:
            # This directory and receipt were created exclusively by this call.
            (destination / "CHECKPOINT.json").unlink(missing_ok=True)
            sync_directory(destination)
            raise
    return receipt


def verify_checkpoint(destination):
    destination = work_path(destination)
    receipt = parse_json(regular_bytes(destination / "CHECKPOINT.json", RECORD_LIMIT))
    if receipt.get("schema") != "arc-start-pending-checkpoint-v1" or receipt.get("status") != "checkpointed":
        raise GuardError("unsupported_checkpoint_receipt")
    inventory = receipt.get("files")
    required = {"PACKET-MANIFEST.json", "pending-main-draw.json"}
    permitted = required | {"ASSIGNMENT.json"}
    if not isinstance(inventory, dict) or not required <= set(inventory) <= permitted:
        raise GuardError("invalid_checkpoint_inventory")
    if {path.name for path in destination.iterdir()} != set(inventory) | {"CHECKPOINT.json"}:
        raise GuardError("unexpected_checkpoint_entry")
    records = {}
    for name, expected in inventory.items():
        limit = MANIFEST_LIMIT if name == "PACKET-MANIFEST.json" else RECORD_LIMIT
        raw = regular_bytes(destination / name, limit)
        if not isinstance(expected, dict) or expected.get("bytes") != len(raw) or expected.get("sha256") != digest(raw):
            raise GuardError("checkpoint_hash_mismatch")
        records[name] = raw
    state, _, _, packet_hash = validate_records(records)
    if receipt.get("packet_manifest_sha256") != packet_hash or receipt.get("source_state") != state:
        raise GuardError("checkpoint_record_binding_mismatch")
    return {"schema": "arc-start-checkpoint-verification-v1", "status": "verified",
            "packet_manifest_sha256": packet_hash, "source_state": state,
            "verified_file_count": len(records), "restore_supported": False}


def nonnegative(value):
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    command = commands.add_parser("report", help="read-only metadata and startup capacity estimate")
    command.add_argument("--work", required=True, type=Path)
    command.add_argument("--reserve-mib", type=nonnegative, default=512)
    command.add_argument("--reserve-inodes", type=nonnegative, default=128)
    command = commands.add_parser("checkpoint-pending", help="copy exact pending control metadata outside WORK")
    command.add_argument("--work", required=True, type=Path)
    command.add_argument("--out", required=True, type=Path)
    command = commands.add_parser("verify-checkpoint", help="verify helper-only checkpoint bytes and bindings")
    command.add_argument("--checkpoint", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "report":
            result = report(args.work, args.reserve_mib * MIB, args.reserve_inodes)
        elif args.action == "checkpoint-pending":
            result = checkpoint_pending(args.work, args.out)
        else:
            result = verify_checkpoint(args.checkpoint)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0 if result["status"] in ("ready", "checkpointed", "verified") else 2
    except GuardError as error:
        print(json.dumps({"status": "error", "error": str(error)}))
    except OSError as error:
        print(json.dumps({"status": "error", "error": "operating_system_error", "errno": error.errno}))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
