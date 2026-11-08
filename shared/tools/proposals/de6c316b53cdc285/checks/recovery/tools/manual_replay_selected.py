#!/usr/bin/env python3
"""Authenticate and manually replay a return into a NEW direct-test source subset.

This is deliberately narrower than official --runtime-closure. It does not run
tests, returned code, Racket, installation, or the official task_tests stage.
Unselected original payload verification is inherited from a hash-bound full
archive verification receipt. Selected payloads are streamed and checked afresh.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import zipfile

PREFIX = "WORK/"
MANIFEST = PREFIX + "PACKET-MANIFEST.json"
HEX = re.compile(r"[0-9a-f]{64}\Z")
CHUNK = 1024 * 1024


def sha_file(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def safe_name(name):
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or any(ord(c) < 32 or ord(c) == 127 for c in name)
            or PurePosixPath(name).is_absolute()
            or any(part in ("", ".", "..") for part in name.split("/"))):
        raise ValueError("Unsafe path: " + repr(name))


def no_symlinks(path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise ValueError("Symlink path or ancestor: " + str(part))


def identity(path):
    s = path.stat()
    return (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def original_inventory(archive):
    files, seen = {}, set()
    for info in archive.infolist():
        name = info.filename.rstrip("/") if info.is_dir() else info.filename
        safe_name(name)
        if info.orig_filename != info.filename or name in seen:
            raise ValueError("Duplicate or altered archive path: " + repr(info.orig_filename))
        seen.add(name)
        kind = stat.S_IFMT(info.external_attr >> 16)
        if (kind not in (0, stat.S_IFREG, stat.S_IFDIR) or info.flag_bits & 1
                or (kind == stat.S_IFDIR and not info.is_dir())
                or (kind == stat.S_IFREG and info.is_dir())
                or (info.is_dir() and info.file_size)):
            raise ValueError("Unsafe archive member type: " + info.filename)
        if not info.is_dir():
            files[info.filename] = info
    raw = archive.read(MANIFEST)
    manifest = json.loads(raw)
    if (manifest.get("schema") != "arcpuzzles-full-packet-v2"
            or manifest.get("layout", {}).get("workspace") != "WORK"
            or raw != canonical(manifest)):
        raise ValueError("Expected the original canonical WORK-layout packet manifest")
    expected = {MANIFEST: hashlib.sha256(raw).hexdigest()}
    for mapping, prefix in ((manifest["files"], PREFIX), (manifest["layout"]["entry_files"], "")):
        for name, digest in mapping.items():
            safe_name(name)
            if not isinstance(digest, str) or not HEX.fullmatch(digest) or prefix + name in expected:
                raise ValueError("Invalid or overlapping source manifest inventory")
            expected[prefix + name] = digest
    if set(files) != set(expected):
        raise ValueError("Original ZIP inventory differs from original manifest")
    return files, manifest, raw, expected


def checked_json(archive, expected, name):
    raw = archive.read(name)
    if hashlib.sha256(raw).hexdigest() != expected.get(name):
        raise ValueError("Original manifest mismatch: " + name)
    return json.loads(raw)


def select_members(archive, expected, manifest, checked):
    task = checked["task_id"]
    rule_task = manifest["generators"][task].get("rule_task_id") or task
    roots = tuple(PREFIX + p for p in (
        f"repo/generators/{task}/", "repo/src/arcpuzzles/", "repo/catalog/", "repo/shared/runtime/"))
    singles = {MANIFEST, PREFIX + "repo/shared/data/canonical/puzzles.jsonl"}
    singles.update(PREFIX + "repo/" + p for p in ("AGENTS.md", "README.md", "pyproject.toml", "setup.py", "requirements.txt"))
    selected = {name for name in expected if name in singles or name.startswith(roots)}
    mapping = checked_json(archive, expected, PREFIX + "repo/catalog/runtime_files.json")
    authorities = checked_json(archive, expected, PREFIX + "repo/catalog/authority_files.json")
    for item in mapping:
        if authorities.get(item["target"]) in {task, rule_task}:
            name = PREFIX + "repo/" + item["path"]
            safe_name(name)
            if name not in expected:
                raise ValueError("Missing selected authority source: " + name)
            selected.add(name)
    for path in checked["patch_paths"]:
        safe_name(path)
        if PREFIX + path in expected:
            selected.add(PREFIX + path)
    for required in (MANIFEST, PREFIX + "repo/shared/data/canonical/puzzles.jsonl",
                     PREFIX + "repo/shared/runtime/reviewer_support.py",
                     PREFIX + f"repo/generators/{task}/generator.py"):
        if required not in selected:
            raise ValueError("Missing focused-test dependency: " + required)
    return selected


def official_validator(owner, manifest, out):
    api_prefix = "repo/src/arcpuzzles/"
    originals = {p: digest for p, digest in manifest["files"].items() if p.startswith(api_prefix)}
    if api_prefix + "review_full_return.py" not in originals:
        raise ValueError("Original official return validator is unavailable")
    for path, expected in originals.items():
        target = owner / path
        no_symlinks(target)
        if not target.is_file() or sha_file(target) != expected:
            raise ValueError("Official API source differs from the original manifest: " + path)
    if any(n == "arcpuzzles" or n.startswith("arcpuzzles.") for n in sys.modules):
        raise ValueError("Use a fresh process; arcpuzzles was imported before authentication")
    # -B alone does not prevent reading stale .pyc files. This nonexistent
    # prefix forces fresh source compilation without creating any cache files.
    sys.dont_write_bytecode = True
    sys.pycache_prefix = str(out / "never-created-python-cache")
    sys.path.insert(0, str(owner / "repo/src"))
    from arcpuzzles.review_full_return import validate_full_return
    return validate_full_return, originals


def replay(args):
    source, returned, owner, verification, out = (Path(p).absolute() for p in (
        args.source_zip, args.return_zip, args.compare_work, args.source_verification, args.out))
    for path in (source, returned, owner, verification, out):
        no_symlinks(path)
    if out.exists():
        raise FileExistsError("Destination must be new: " + str(out))
    if owner == out or owner in out.parents or out in owner.parents:
        raise ValueError("Fresh destination must be separate from the reviewed WORK")
    source_id, return_id = identity(source), identity(returned)
    source_sha, return_sha = sha_file(source), sha_file(returned)
    inherited = json.loads(verification.read_bytes())
    with zipfile.ZipFile(source) as original, zipfile.ZipFile(returned) as delta:
        files, manifest, manifest_raw, expected = original_inventory(original)
        manifest_sha = hashlib.sha256(manifest_raw).hexdigest()
        if (inherited.get("ok") is not True or inherited.get("archive_sha256") != source_sha
                or inherited.get("manifest_sha256") != manifest_sha
                or inherited.get("archive_files") != len(files)
                or inherited.get("streamed_files") != len(files)
                or inherited.get("verified_workspace_files") != len(manifest["files"])
                or inherited.get("verified_entry_files") != len(manifest["layout"]["entry_files"])
                or inherited.get("actual_uncompressed_bytes") != sum(i.file_size for i in files.values())
                or any(inherited.get(k) for k in ("duplicate_paths", "unsafe_paths", "malformed_members", "missing_paths", "extra_paths", "hash_mismatches", "errors"))):
            raise ValueError("Full original-source verification receipt does not bind this archive")
        if (owner / "PACKET-MANIFEST.json").read_bytes() != manifest_raw:
            raise ValueError("Reviewed WORK manifest differs from the original ZIP")
        validate, authenticated_api = official_validator(owner, manifest, out)
        checked = validate(delta, manifest)  # Unmodified complete official validation.
        paths = checked["patch_paths"]
        if not paths:
            raise ValueError("No changed source paths to replay")
        comparisons = {}
        for path in paths:
            safe_name(path)
            target = owner / path
            no_symlinks(target)
            if not target.is_file():
                raise ValueError("Missing reviewed comparison file: " + path)
            comparisons[path] = sha_file(target)
        selected = select_members(original, expected, manifest, checked)
        patches = {n: delta.read(n) for n in sorted(delta.namelist()) if n.startswith("patches/")}
        work = out / "checkout/WORK"
        receipt = {
            "schema": "arcpuzzles-manual-selected-test-replay-v1", "status": "planned" if args.plan else "running",
            "extraction_mode": "manual_selected_task_direct_test_source_subset",
            "scope": "Manual fresh patch replay for direct selected-task pytest only; not the official runtime closure or task_tests stage.",
            "official_runtime_closure": False, "official_task_test_stage_satisfied": False,
            "full_original_packet_extracted": False, "tests_run": False, "training_admitted": False,
            "packet_id": checked["packet_id"], "assignment_id": checked["assignment_id"], "task_id": checked["task_id"],
            "source_zip_sha256": source_sha, "return_zip_sha256": return_sha, "manifest_sha256": manifest_sha,
            "source_verification_receipt_sha256": sha_file(verification),
            "unselected_payload_verification": "Inherited full verification receipt; the entire compressed source archive SHA-256 was checked again.",
            "official_validator_source_sha256": authenticated_api["repo/src/arcpuzzles/review_full_return.py"],
            "authenticated_api_files": len(authenticated_api), "api_bytecode_policy": "fresh nonexistent pycache prefix; cache writes disabled",
            "original_files": len(files), "extracted_files": len(selected),
            "extracted_bytes": sum(files[n].file_size for n in selected),
            "patch_sha256": {n: hashlib.sha256(raw).hexdigest() for n, raw in patches.items()},
            "changed_paths": paths, "new_paths": sorted(p for p in paths if PREFIX + p not in expected),
            "work_root": str(work), "commands": [], "changed_files": [],
            "test_prerequisites": ["fresh Python environment with pytest", "separately supplied Racket executable", "PYTHONPATH=fresh_repo/src:fresh_repo/shared/runtime"],
            "direct_test_argv": ["python", "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", f"generators/{checked['task_id']}/tests"],
        }
        if identity(source) != source_id or identity(returned) != return_id:
            raise ValueError("An input archive changed during preflight")
        if args.plan:
            return receipt
        out.mkdir(parents=True, exist_ok=False)
        def save():
            (out / "replay.json").write_bytes(canonical(receipt) + b"\n")
        save()
        try:
            inventory = []
            for name in sorted(selected):
                target = out / "checkout" / name
                target.parent.mkdir(parents=True, exist_ok=True)
                digest, size = hashlib.sha256(), 0
                with original.open(files[name]) as src, target.open("xb") as dst:
                    while block := src.read(CHUNK):
                        dst.write(block); digest.update(block); size += len(block)
                if digest.hexdigest() != expected[name] or size != files[name].file_size:
                    raise ValueError("Extracted original source differs: " + name)
                inventory.append({"path": name, "sha256": digest.hexdigest(), "bytes": size})
            inventory_raw = canonical(inventory) + b"\n"
            inventory_file = out / "extraction-manifest.json.gz"
            inventory_file.write_bytes(gzip.compress(inventory_raw, mtime=0))
            receipt["extraction_inventory"] = {"path": "extraction-manifest.json.gz", "sha256": sha_file(inventory_file),
                                               "raw_sha256": hashlib.sha256(inventory_raw).hexdigest()}
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
            def run(argv):
                process = subprocess.run(argv, cwd=work, env=env, capture_output=True, text=True, timeout=30)
                receipt["commands"].append({"argv": argv, "cwd": str(work), "exit_code": process.returncode,
                                             "stdout": process.stdout, "stderr": process.stderr})
                save()
                if process.returncode:
                    raise ValueError("Replay command failed: " + repr(argv) + ": " + process.stderr[:500])
                return process.stdout
            run(["git", "init", "-q", "--template="])
            top = Path(run(["git", "rev-parse", "--show-toplevel"]).strip()).resolve()
            if top != work.resolve():
                raise ValueError("Git root is not the exact fresh WORK directory")
            receipt["git_top_level"] = str(top)
            git_paths, patch_files = [], []
            for index, (name, raw) in enumerate(patches.items()):
                patch = out / f"source-{index:03d}.patch"
                patch.write_bytes(raw); patch_files.append(str(patch))
                for row in run(["git", "apply", "--numstat", "-z", str(patch)]).split("\0"):
                    if not row:
                        continue
                    fields = row.split("\t", 2)
                    if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
                        raise ValueError("Unsupported binary or renamed Git patch entry")
                    safe_name(fields[2]); git_paths.append(fields[2])
            if sorted(git_paths) != sorted(paths):
                raise ValueError("Git's complete patch inventory differs from official validated paths")
            for patch in patch_files:
                run(["git", "apply", "--check", patch])
                run(["git", "apply", patch])
            for path in paths:
                target = work / path
                no_symlinks(target)
                digest = sha_file(target)
                if digest != comparisons[path] or sha_file(owner / path) != comparisons[path]:
                    raise ValueError("Applied source differs from reviewed final bytes: " + path)
                receipt["changed_files"].append({"path": path, "sha256": digest, "bytes": target.stat().st_size,
                                                 "new": path in receipt["new_paths"]})
            if identity(source) != source_id or identity(returned) != return_id:
                raise ValueError("An input archive changed during replay")
            receipt["generator_sha256"] = sha_file(work / f"repo/generators/{checked['task_id']}/generator.py")
            receipt["status"] = "manual_patch_replay_passed_tests_pending"
            save()
            return receipt
        except BaseException as exc:
            receipt.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            save()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-zip", "return-zip", "compare-work", "source-verification", "out"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--plan", action="store_true", help="authenticate and print exact selected counts/bytes; write nothing")
    args = parser.parse_args()
    try:
        report = replay(args)
    except Exception as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
