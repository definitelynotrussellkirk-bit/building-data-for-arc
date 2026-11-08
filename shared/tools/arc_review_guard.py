#!/usr/bin/env python3
"""Resource checks and durable command receipts for ARC review packets.

Python 3.10+, standard library only. This tool never draws an assignment,
changes a generator, finishes a solve, or creates an official intake record.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import zipfile

MIB = 1024 * 1024
CONTRACT_FILES = (
    "ASSIGNMENT.json", "BLIND_ASSIGNMENT.json", "AUDIT_ASSIGNMENT.json",
    "DUTIES.md", "RESULTS.json",
)


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def digest_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(MIB), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data, *, exclusive=False):
    """Publish a complete receipt; never leave half-written JSON at its name."""
    path = Path(path)
    if exclusive and path.exists():
        raise FileExistsError(path)
    temporary = path.with_name(path.name + ".writing")
    with temporary.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    if exclusive:
        # link() fails if another writer acquired the destination in the meantime.
        os.link(temporary, path)
        temporary.unlink()
    else:
        os.replace(temporary, path)
    try:
        fd = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        # Some filesystems do not support directory fsync; file fsync still ran.
        pass


def nearest_existing(path):
    path = Path(path).absolute()
    while not path.exists():
        if path.parent == path:
            raise FileNotFoundError(path)
        path = path.parent
    return path.resolve()


def _unescape_mount(text):
    return re.sub(r"\\([0-7]{3})", lambda m: chr(int(m.group(1), 8)), text)


def mount_for(path, mountinfo=None):
    """Match the longest mountpoint on a path-component boundary."""
    path = Path(path).resolve()
    try:
        lines = (Path("/proc/self/mountinfo").read_text() if mountinfo is None
                 else mountinfo).splitlines()
    except OSError:
        return {"filesystem": "unknown", "mountpoint": None}
    found = None
    for line in lines:
        try:
            left, right = line.split(" - ", 1)
            fields, after = left.split(), right.split()
            point = Path(_unescape_mount(fields[4]))
            if path == point or point in path.parents:
                candidate = {"filesystem": after[0], "mountpoint": str(point)}
                if found is None or len(str(point)) >= len(found["mountpoint"]):
                    found = candidate
        except (ValueError, IndexError):
            continue
    return found or {"filesystem": "unknown", "mountpoint": None}


def memory_snapshot(cgroup_root=Path("/sys/fs/cgroup"), meminfo=None):
    """Record cgroup-v2 limits at the active group and visible ancestors.

    On non-Linux/v1-only hosts the cgroup result is explicitly unknown. Host
    MemAvailable is also retained; it never overrides a tighter cgroup limit.
    """
    cgroup_root = Path(cgroup_root)
    groups = []
    candidates = [cgroup_root]
    if cgroup_root == Path("/sys/fs/cgroup"):
        try:
            for line in Path("/proc/self/cgroup").read_text().splitlines():
                if line.startswith("0::"):
                    relative = PurePosixPath(line[3:].lstrip("/"))
                    if ".." not in relative.parts:
                        active = cgroup_root.joinpath(*relative.parts)
                        if active.is_dir():
                            candidates = [active] + [p for p in active.parents
                                if p == cgroup_root or cgroup_root in p.parents]
        except OSError:
            pass
    for group in dict.fromkeys(candidates):
        try:
            maximum = (group / "memory.max").read_text().strip()
            current = int((group / "memory.current").read_text())
            maximum = None if maximum == "max" else int(maximum)
            high = None
            try:
                high_text = (group / "memory.high").read_text().strip()
                high = None if high_text == "max" else int(high_text)
            except (OSError, ValueError):
                pass
            events = {}
            try:
                events = {k: int(v) for k, v in
                          (line.split() for line in (group / "memory.events").read_text().splitlines())}
            except (OSError, ValueError):
                pass
            groups.append({"path": str(group), "max_bytes": maximum, "high_bytes": high,
                "current_bytes": current,
                "headroom_bytes": None if maximum is None else max(0, maximum-current),
                "events": events})
        except (OSError, ValueError):
            continue
    host_available = None
    try:
        content = Path("/proc/meminfo").read_text() if meminfo is None else meminfo
        for line in content.splitlines():
            if line.startswith("MemAvailable:"):
                host_available = int(line.split()[1]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    limits = [g["headroom_bytes"] for g in groups if g["headroom_bytes"] is not None]
    if host_available is not None:
        limits.append(host_available)
    return {"cgroup_v2": groups, "host_available_bytes": host_available,
            "effective_available_bytes": min(limits) if limits else None,
            "scope_note": "Cgroup events may include other processes; an OOM delta does not identify a victim."}


def filesystem_snapshot(destination):
    ancestor = nearest_existing(destination)
    values = os.statvfs(ancestor)
    info = mount_for(ancestor)
    info.update({"probed_path": str(ancestor), "block_size": values.f_frsize or values.f_bsize,
        "available_bytes": values.f_bavail * (values.f_frsize or values.f_bsize),
        "available_inodes": values.f_favail if values.f_files else None})
    return info


def member_path(info):
    name = info.filename
    original_name = getattr(info, "orig_filename", name)
    if not name or original_name != name or "\x00" in original_name or "\\" in name:
        raise ValueError(f"Unsafe ZIP member name: {name!r}")
    path = PurePosixPath(name)
    if (path.is_absolute() or ".." in path.parts or
            any(part in ("", ".") for part in name.rstrip("/").split("/")) or
            ":" in path.parts[0]):
        raise ValueError(f"Unsafe ZIP member path: {name!r}")
    mode = info.external_attr >> 16
    kind = stat.S_IFMT(mode)
    if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
        raise ValueError(f"Link or special ZIP member: {name!r}")
    if info.is_dir() and kind == stat.S_IFREG:
        raise ValueError(f"Conflicting ZIP directory metadata: {name!r}")
    if info.is_dir() and info.file_size:
        raise ValueError(f"ZIP directory contains payload data: {name!r}")
    if not info.is_dir() and kind == stat.S_IFDIR:
        raise ValueError(f"Conflicting ZIP file metadata: {name!r}")
    if info.flag_bits & 1:
        raise ValueError(f"Encrypted ZIP member: {name!r}")
    if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED,
                                  zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA):
        raise ValueError(f"Unsupported ZIP compression: {info.compress_type}")
    return path


def archive_inventory(archive, block_size=4096):
    """Validate all names and collisions before any extraction writes occur."""
    files, directories, explicit = set(), set(), set()
    sizes, allocated = 0, 0
    with zipfile.ZipFile(archive) as source:
        for info in source.infolist():
            path = member_path(info)
            key = path.as_posix()
            if key in explicit:
                raise ValueError(f"Duplicate ZIP member: {key}")
            explicit.add(key)
            for parent in path.parents:
                if str(parent) != ".":
                    directories.add(parent.as_posix())
            if info.is_dir():
                directories.add(key)
            else:
                files.add(key)
                sizes += info.file_size
                allocated += math.ceil(info.file_size / block_size) * block_size
    collisions = files & directories
    if collisions:
        raise ValueError(f"ZIP file/directory collision: {sorted(collisions)[0]}")
    if "GUARD-EXTRACTION.json" in files or "GUARD-EXTRACTION.json" in directories:
        raise ValueError("ZIP collides with the extraction receipt path")
    return {"status": "inspected", "file_count": len(files),
        "directory_count": len(directories), "uncompressed_bytes": sizes,
        "allocation_estimate_bytes": allocated + (len(directories)+1)*block_size,
        "inode_estimate": len(files)+len(directories)+1,
        "estimate_note": "Block-rounded file sizes plus one block per directory; filesystem metadata and runtime copies need additional reserve."}


def verify_packet_manifest(archive):
    """Stream exact manifest-bound files; return hashes/counts, never puzzle text."""
    with zipfile.ZipFile(archive) as source:
        names = set(source.namelist())
        candidates = [p for p in ("WORK/PACKET-MANIFEST.json", "PACKET-MANIFEST.json") if p in names]
        if len(candidates) != 1:
            raise ValueError("Expected one ARC packet manifest at WORK/PACKET-MANIFEST.json or PACKET-MANIFEST.json")
        path = candidates[0]
        if source.getinfo(path).file_size > 32*MIB:
            raise ValueError("Packet manifest exceeds the 32 MiB guard limit")
        raw = source.read(path)
        manifest = json.loads(raw)
        if manifest.get("schema") != "arcpuzzles-full-packet-v2":
            raise ValueError("Unsupported packet manifest schema")
        prefix = str(PurePosixPath(path).parent)
        prefix = "" if prefix == "." else prefix+"/"
        expected = {prefix+p: h for p, h in manifest["files"].items()}
        expected.update(manifest.get("layout", {}).get("entry_files", {}))
        unlisted = {info.filename for info in source.infolist() if not info.is_dir()} - set(expected) - {path}
        if unlisted:
            raise ValueError(f"Unlisted packet member: {sorted(unlisted)[0]}")
        for name, claimed in expected.items():
            if name not in names:
                raise ValueError(f"Missing manifest member: {name}")
            h = hashlib.sha256()
            with source.open(name) as stream:
                for chunk in iter(lambda: stream.read(MIB), b""):
                    h.update(chunk)
            if h.hexdigest() != claimed:
                raise ValueError(f"Manifest hash mismatch: {name}")
        return {"status": "verified", "manifest_path": path,
                "manifest_sha256": hashlib.sha256(raw).hexdigest(),
                "verified_file_count": len(expected)}


def resource_decision(inventory, filesystem, memory, reserve_bytes, reserve_inodes):
    failures, warnings = [], []
    disk_needed = inventory["allocation_estimate_bytes"] + reserve_bytes
    inodes_needed = inventory["inode_estimate"] + reserve_inodes
    if filesystem["available_bytes"] < disk_needed:
        failures.append("insufficient_disk_bytes")
    available_inodes = filesystem["available_inodes"]
    if available_inodes is None:
        warnings.append("inode_availability_unknown")
    elif available_inodes < inodes_needed:
        failures.append("insufficient_inodes")
    tmpfs = filesystem["filesystem"] in ("tmpfs", "ramfs")
    memory_needed = reserve_bytes + (inventory["allocation_estimate_bytes"] if tmpfs else 0)
    available_memory = memory["effective_available_bytes"]
    if available_memory is None:
        (failures if tmpfs else warnings).append("memory_headroom_unknown")
    elif available_memory < memory_needed:
        failures.append("insufficient_memory_headroom")
    if tmpfs:
        warnings.append("memory_backed_destination_requires_independent_durable_checkpoint")
    return {"status": "blocked" if failures else "ready",
        "failures": failures, "warnings": warnings,
        "required_available_disk_bytes": disk_needed,
        "required_available_inodes": inodes_needed,
        "required_available_memory_bytes": memory_needed}


def preflight(archive, destination, reserve_bytes=512*MIB, reserve_inodes=4096,
              verify_manifest=False):
    archive, destination = Path(archive).resolve(), Path(destination).absolute()
    if not archive.is_file():
        raise FileNotFoundError(archive)
    fs, memory = filesystem_snapshot(destination), memory_snapshot()
    report = {"schema": "arc-review-guard-preflight-v1", "created_at": utc_now(),
        "archive": str(archive), "destination": str(destination),
        "filesystem": fs, "memory": memory, "reserve_bytes": reserve_bytes,
        "reserve_inodes": reserve_inodes,
        "limitations": "A point-in-time capacity check is not a guarantee against concurrent resource use, filesystem quotas, or unknown runtime peaks."}
    # zipfile loads the central directory. Refuse even that allocation when the
    # host is already severely constrained, instead of dying before the receipt.
    available = memory["effective_available_bytes"]
    if available is not None and available < 64*MIB:
        report.update({"status": "blocked", "failures": ["insufficient_memory_for_metadata_inspection"],
            "warnings": [], "inventory": {"status": "not_inspected"}})
    else:
        inventory = archive_inventory(archive, fs["block_size"])
        report["inventory"] = inventory
        report.update(resource_decision(inventory, fs, memory, reserve_bytes, reserve_inodes))
        if verify_manifest and report["status"] == "ready":
            report["manifest_verification"] = verify_packet_manifest(archive)
        elif verify_manifest:
            report["manifest_verification"] = {"status": "not_run_resource_blocked"}
    resolved = destination.resolve()
    if resolved == Path("/dev") or Path("/dev") in resolved.parents:
        if resolved != Path("/dev/shm") and Path("/dev/shm") not in resolved.parents:
            report["status"] = "blocked"
            report["failures"].append("private_dev_destination_not_supported")
    if destination.exists() or destination.is_symlink():
        report["status"] = "blocked"
        report["failures"].append("extraction_destination_already_exists")
    return report


def extract_packet(archive, destination, reserve_bytes=512*MIB, reserve_inodes=4096):
    report = preflight(archive, destination, reserve_bytes, reserve_inodes, verify_manifest=True)
    if report["status"] != "ready":
        return report
    archive, destination = Path(archive).resolve(), Path(destination).absolute()
    if not destination.parent.is_dir():
        raise ValueError("Extraction destination's parent must already exist")
    identity = digest_file(archive)
    destination.mkdir()  # Exclusive: never overwrite an existing checkout.
    report.update({"status": "extracting", "archive_sha256": identity})
    receipt = destination / "GUARD-EXTRACTION.json"
    write_json(receipt, report, exclusive=True)
    try:
        with zipfile.ZipFile(archive) as source:
            for info in source.infolist():
                target = destination.joinpath(*member_path(info).parts)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with source.open(info) as incoming, target.open("xb") as outgoing:
                    shutil.copyfileobj(incoming, outgoing, length=MIB)
        if digest_file(archive) != identity:
            raise ValueError("Archive changed during extraction; partial output is not verified")
        report["status"] = "extracted"
    except BaseException as exc:
        report.update({"status": "failed_partial_preserved", "error": repr(exc)})
        try:
            write_json(receipt, report)
        except OSError:
            pass
        raise
    write_json(receipt, report)
    return report


def checkpoint(work, destination):
    """Save exact assignment bytes BEFORE an expensive command is started."""
    work, destination = Path(work).resolve(), Path(destination).absolute()
    if not (work / "ASSIGNMENT.json").is_file():
        raise ValueError("ASSIGNMENT.json is missing; refusing an empty or reconstructed checkpoint")
    if not (work / "PACKET-MANIFEST.json").is_file():
        raise ValueError("PACKET-MANIFEST.json is missing")
    if (work / "PACKET-MANIFEST.json").is_symlink():
        raise ValueError("PACKET-MANIFEST.json must be a regular file, not a symlink")
    manifest_hash = digest_file(work / "PACKET-MANIFEST.json")
    contents = {}
    for name in CONTRACT_FILES:
        path = work / name
        if path.is_symlink():
            raise ValueError(f"Checkpoint contract must be a regular file: {name}")
        if path.is_file():
            if path.stat().st_size > 4*MIB:
                raise ValueError(f"Checkpoint record too large: {name}")
            contents[name] = path.read_bytes()
    contract = json.loads(contents["ASSIGNMENT.json"])
    if contract.get("packet_id") != manifest_hash:
        raise ValueError("Assignment is not bound to the current packet manifest")
    destination.mkdir(parents=False, exist_ok=False)
    files = {}
    for name, raw in contents.items():
        path = destination / name
        with path.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        files[name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        if (work / name).read_bytes() != raw:
            raise ValueError(f"Contract changed during checkpoint: {name}; partial copy retained")
    if digest_file(work / "PACKET-MANIFEST.json") != manifest_hash:
        raise ValueError("Packet manifest changed during checkpoint; partial copy retained")
    receipt = {"schema": "arc-review-assignment-checkpoint-v1", "status": "checkpointed",
        "created_at": utc_now(), "source_work": str(work),
        "assignment_id": contract.get("assignment_id"), "task_id": contract.get("task_id"),
        "packet_manifest_sha256": manifest_hash, "files": files,
        "scope": "Exact assignment and listed work records only. Source baseline, solve artifacts and check evidence are not included.",
        "recovery_note": "Keep with the original packet. Restore exact records and reconstruct manifest-bound baseline files before using the official packager; never redraw to imitate this assignment."}
    write_json(destination / "CHECKPOINT.json", receipt, exclusive=True)
    return receipt


def restore_checkpoint(saved, work, reserve_bytes=512*MIB):
    """Restore a saved draw into a fresh extraction of exactly its source packet.

    Baseline bytes come from the matching original extraction, not another
    checkout. Existing different records are never overwritten.
    """
    saved, work = Path(saved).resolve(), Path(work).resolve()
    index = json.loads((saved / "CHECKPOINT.json").read_text())
    if index.get("schema") != "arc-review-assignment-checkpoint-v1" or index.get("status") != "checkpointed":
        raise ValueError("Checkpoint is missing its completed inventory")
    manifest_path = work / "PACKET-MANIFEST.json"
    if manifest_path.is_symlink() or digest_file(manifest_path) != index["packet_manifest_sha256"]:
        raise ValueError("Destination packet manifest does not match the checkpoint")
    names = set(index["files"])
    if "ASSIGNMENT.json" not in names or not names <= set(CONTRACT_FILES):
        raise ValueError("Invalid checkpoint record inventory")
    contents = {}
    for name, expected in index["files"].items():
        path = saved / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 4*MIB:
            raise ValueError(f"Invalid checkpoint record: {name}")
        raw = path.read_bytes()
        if len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
            raise ValueError(f"Checkpoint hash mismatch: {name}")
        target = work / name
        if target.is_symlink() or (target.exists() and target.read_bytes() != raw):
            raise ValueError(f"Refusing to overwrite a different existing record: {name}")
        contents[name] = raw
    contract = json.loads(contents["ASSIGNMENT.json"])
    packet_id = index["packet_manifest_sha256"]
    if contract.get("packet_id") != packet_id:
        raise ValueError("Checkpoint assignment does not bind this packet")
    seed = bytes.fromhex(contract["seed"])
    if len(seed) != 32 or contract["assignment_id"] != "review-"+hashlib.sha256(bytes.fromhex(packet_id)+seed).hexdigest()[:16]:
        raise ValueError("Checkpoint assignment identity is inconsistent")
    manifest = json.loads(manifest_path.read_text())
    if contract["task_id"] != manifest["main_ids"][int.from_bytes(seed, "big") % len(manifest["main_ids"])]:
        raise ValueError("Checkpoint task does not match its original draw")
    baseline_root = work / ".review" / "baseline"
    copies = []
    for name, expected in contract["baseline_sha256"].items():
        pure = PurePosixPath(name)
        if (pure.is_absolute() or ".." in pure.parts or "\\" in name or
                not pure.parts or pure.parts[0] != "repo" or str(pure) != name):
            raise ValueError(f"Unsafe baseline path: {name}")
        source, target = work.joinpath(*pure.parts), baseline_root.joinpath(*pure.parts)
        for candidate in (source, target):
            current = candidate
            while current != work and work in current.parents:
                if current.is_symlink():
                    raise ValueError(f"Baseline path traverses a symlink: {name}")
                current = current.parent
        if manifest["files"].get(name) != expected or digest_file(source) != expected:
            raise ValueError(f"Original baseline source mismatch: {name}")
        if target.exists():
            if digest_file(target) != expected:
                raise ValueError(f"Existing baseline source mismatch: {name}")
        else:
            copies.append((source, target, expected))
    fs = filesystem_snapshot(work)
    block = fs["block_size"]
    directories = {str(parent) for _, target, _ in copies for parent in target.parents
                   if not parent.exists() and (parent == work or work in parent.parents)}
    inventory = {"allocation_estimate_bytes": sum(math.ceil(s.stat().st_size/block)*block
        for s, _, _ in copies) + len(directories)*block + sum(math.ceil(len(b)/block)*block for b in contents.values()),
        "inode_estimate": len(copies)+len(directories)+len(contents)}
    decision = resource_decision(inventory, fs, memory_snapshot(), reserve_bytes, 32)
    if decision["status"] != "ready":
        raise ValueError("Cannot restore safely: "+", ".join(decision["failures"]))
    for source, target, expected in copies:
        target.parent.mkdir(parents=True, exist_ok=True)
        with source.open("rb") as incoming, target.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing, length=MIB)
            outgoing.flush()
            os.fsync(outgoing.fileno())
        if digest_file(target) != expected:
            raise ValueError(f"Source changed during baseline restoration: {source}")
        target.chmod(0o444)
    # Publish ASSIGNMENT last. Interrupted baseline copying does not publish a
    # new draw record whose baseline is incomplete. Exact reruns are idempotent.
    ordered = sorted(contents, key=lambda name: name == "ASSIGNMENT.json")
    for name in ordered:
        target = work/name
        if target.exists():
            continue
        with target.open("xb") as stream:
            stream.write(contents[name])
            stream.flush()
            os.fsync(stream.fileno())
    return {"schema": "arc-review-guard-restore-v1", "status": "restored",
        "assignment_id": contract["assignment_id"], "task_id": contract["task_id"],
        "packet_manifest_sha256": packet_id, "baseline_files_restored": len(copies),
        "record_files": sorted(contents), "work": str(work),
        "scope": "The exact saved draw and original baseline were restored. Solve artifacts and check evidence must be restored separately if they were saved."}


def _drain(pipe, path, maximum, metadata):
    """Bounded head/tail retention, with explicit omitted-byte counts."""
    tail_capacity = min(65536, maximum // 2)
    head_capacity = maximum - tail_capacity
    head_written, total, tail = 0, 0, bytearray()
    try:
        with Path(path).open("xb") as stream:
            while True:
                chunk = pipe.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                take = min(head_capacity-head_written, len(chunk))
                if take:
                    stream.write(chunk[:take])
                    head_written += take
                tail.extend(chunk[take:])
                if len(tail) > tail_capacity:
                    del tail[:-tail_capacity]
            omitted = total-head_written-len(tail)
            if omitted:
                stream.write(f"\n[arc-review-guard omitted {omitted} bytes]\n".encode())
            stream.write(tail)
            stream.flush()
            os.fsync(stream.fileno())
        metadata.update({"observed_bytes": total, "omitted_bytes": omitted,
                         "retained_sha256": digest_file(path)})
    except BaseException as exc:
        metadata["capture_error"] = repr(exc)
        # Keep draining so the child cannot deadlock on a full pipe after ENOSPC.
        try:
            while pipe.read(65536):
                pass
        except OSError:
            pass
    finally:
        pipe.close()


def run_guarded(argv, cwd, work, destination, min_memory_bytes=512*MIB,
                timeout=None, max_output_bytes=2*MIB):
    if not argv:
        raise ValueError("A command argument vector is required after --")
    if max_output_bytes < 1024:
        raise ValueError("Output retention must be at least 1024 bytes per stream")
    cwd, destination = Path(cwd).resolve(), Path(destination).absolute()
    saved = checkpoint(work, destination)
    before = memory_snapshot()
    report = {"schema": "arc-review-command-receipt-v1", "status": "running",
        "started_at": utc_now(), "argv": list(argv), "cwd": str(cwd),
        "assignment_id": saved["assignment_id"], "checkpoint": "CHECKPOINT.json",
        "memory_before": before, "returncode": None, "signal": None,
        "stdout": {"path": "stdout.log"}, "stderr": {"path": "stderr.log"},
        "incomplete_receipt_note": "If this remains running, the wrapper did not record completion; do not count it as a pass."}
    receipt = destination / "COMMAND.json"
    available = before["effective_available_bytes"]
    if available is not None and available < min_memory_bytes:
        report.update({"status": "blocked_before_execution",
            "reason": "insufficient_memory_headroom", "required_bytes": min_memory_bytes})
        write_json(receipt, report, exclusive=True)
        return report, 2
    write_json(receipt, report, exclusive=True)
    started = time.monotonic()
    try:
        proc = subprocess.Popen(list(argv), cwd=cwd, shell=False, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=(os.name == "posix"))
    except OSError as exc:
        report.update({"status": "spawn_failed", "error": repr(exc), "finished_at": utc_now()})
        write_json(receipt, report)
        return report, 2
    readers = [threading.Thread(target=_drain, args=(pipe, destination/name,
        max_output_bytes, report[key]), daemon=True)
        for pipe, name, key in [(proc.stdout, "stdout.log", "stdout"), (proc.stderr, "stderr.log", "stderr")]]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        timed_out = True
        if os.name == "posix":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            proc.kill()
        proc.wait()
    for reader in readers:
        remaining = None if timeout is None else max(0, timeout-(time.monotonic()-started))
        reader.join(timeout=remaining)
    if any(reader.is_alive() for reader in readers) and timeout is not None:
        # The direct child may already have exited while a descendant still
        # owns its output pipes. The timeout covers that drain phase too.
        timed_out = True
        if os.name == "posix":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        for reader, key in zip(readers, ("stdout", "stderr")):
            reader.join(timeout=1)
            if reader.is_alive():
                report[key]["capture_error"] = "An output pipe remained open after the command deadline; capture is incomplete."
    after = memory_snapshot()
    before_events = {g["path"]: g["events"] for g in before["cgroup_v2"]}
    deltas = {g["path"]: {k: v-before_events[g["path"]].get(k, 0)
              for k, v in g["events"].items()}
              for g in after["cgroup_v2"] if g["path"] in before_events}
    raw = proc.returncode
    try:
        sig = signal.Signals(-raw).name if raw < 0 else None
    except ValueError:
        sig = f"SIGNAL_{-raw}"
    capture_errors = any("capture_error" in report[key] for key in ("stdout", "stderr"))
    report.update({"status": "timed_out" if timed_out else
            ("capture_failed" if capture_errors else "completed"),
        "finished_at": utc_now(), "duration_seconds": round(time.monotonic()-started, 3),
        "returncode": raw, "signal": sig, "memory_after": after,
        "cgroup_event_deltas": deltas,
        "cgroup_oom_kill_observed": any(d.get("oom_kill", 0) > 0 for d in deltas.values()),
        "passed": raw == 0 and not timed_out and not capture_errors})
    write_json(receipt, report)
    code = 124 if timed_out else (2 if capture_errors else (128-raw if raw < 0 else raw))
    return report, code


def nonnegative_int(value):
    value = int(value)
    if value < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return value


def positive_float(value):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError("must be finite and positive")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("preflight", "extract"):
        command = commands.add_parser(action)
        command.add_argument("archive", type=Path)
        command.add_argument("--destination", required=True, type=Path)
        command.add_argument("--reserve-mib", type=nonnegative_int, default=512)
        command.add_argument("--reserve-inodes", type=nonnegative_int, default=4096)
        command.add_argument("--out", type=Path)
        if action == "preflight":
            command.add_argument("--verify-manifest", action="store_true")
    command = commands.add_parser("checkpoint")
    command.add_argument("--work", required=True, type=Path)
    command.add_argument("--out", required=True, type=Path)
    command = commands.add_parser("restore")
    command.add_argument("--checkpoint", required=True, type=Path)
    command.add_argument("--work", required=True, type=Path)
    command.add_argument("--reserve-mib", type=nonnegative_int, default=512)
    command = commands.add_parser("run")
    command.add_argument("--cwd", required=True, type=Path)
    command.add_argument("--work", required=True, type=Path)
    command.add_argument("--checkpoint", required=True, type=Path)
    command.add_argument("--min-memory-mib", type=nonnegative_int, default=512)
    command.add_argument("--timeout", type=positive_float)
    command.add_argument("--max-output-mib", type=positive_float, default=2)
    command.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.action in ("preflight", "extract"):
            kwargs = dict(reserve_bytes=args.reserve_mib*MIB, reserve_inodes=args.reserve_inodes)
            if args.action == "preflight":
                report = preflight(args.archive, args.destination,
                    verify_manifest=args.verify_manifest, **kwargs)
            else:
                report = extract_packet(args.archive, args.destination, **kwargs)
            code = 0 if report["status"] in ("ready", "extracted") else 2
            if args.out:
                write_json(args.out, report, exclusive=True)
        elif args.action == "checkpoint":
            report, code = checkpoint(args.work, args.out), 0
        elif args.action == "restore":
            report, code = restore_checkpoint(args.checkpoint, args.work, args.reserve_mib*MIB), 0
        else:
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            report, code = run_guarded(command, args.cwd, args.work, args.checkpoint,
                min_memory_bytes=args.min_memory_mib*MIB, timeout=args.timeout,
                max_output_bytes=int(args.max_output_mib*MIB))
        print(json.dumps(report, indent=2, sort_keys=True))
        return code
    except Exception as exc:
        print(json.dumps({"status": "error", "error": type(exc).__name__, "message": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
