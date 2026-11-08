"""Replay a full-packet return without executing tests or modifying owner sources.

Based on the fresh_replay.py utility returned by review-97ba56f407991aee.
Uses the official return validator; dependency-only extraction is explicit.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import zipfile

from .review_full_return import validate_full_return, _canonical_only_task
from .review_targets import MULTI_SCHEMA, assignment_targets, target_ids, rule_task_ids


def _sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _safe_name(name: str) -> None:
    if (not name or "\\" in name or ":" in name or "\0" in name
            or PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts
            or str(PurePosixPath(name)) != name.rstrip("/")):
        raise ValueError(f"Unsafe archive path: {name!r}")


def _no_symlinks(path: Path) -> None:
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise ValueError(f"Symlink path or ancestor: {parent}")


def _runtime_members(archive, expected, prefix, task, identity):
    """Use only manifest-checked official mapping and bootstrap paths."""
    def read(relative):
        name = prefix + relative
        raw = archive.read(name)
        if hashlib.sha256(raw).hexdigest() != expected.get(name):
            raise ValueError(f"Original manifest mismatch: {name}")
        return json.loads(raw)
    mapping = read("repo/catalog/runtime_files.json")
    authorities = read("repo/catalog/authority_files.json")
    required = set()
    for item in mapping:
        relative, target = item["path"], item["target"]
        _safe_name(relative)
        if relative.startswith("generators/") and PurePosixPath(relative).parts[1] not in {task, identity}:
            continue
        if target.startswith("data/base/solutions/") and authorities.get(target) not in {task, identity}:
            continue
        required.add(prefix + "repo/" + relative)
    if missing := required - set(expected):
        raise ValueError(f"Missing declared runtime sources: {sorted(missing)}")
    roots = {prefix + "repo/" + n for n in ("AGENTS.md", "README.md", "pyproject.toml", "setup.py", "requirements.txt")}
    for name in expected:
        relative = name.removeprefix(prefix)
        if (name in roots or "/" not in relative
                or name.startswith(tuple(prefix + p for p in ("repo/src/arcpuzzles/", "repo/catalog/", "vendor/")))
                or any(name.startswith(prefix + f"repo/generators/{tid}/") for tid in {task, identity})
                or not name.startswith(prefix)):
            required.add(name)
    return required


def replay_return(source_zip: Path, return_zip: Path, compare_work: Path, out: Path,
                  *, runtime_closure: bool = False) -> dict:
    """Extract, validate and apply the exact delta, then compare every changed byte.

    ``compare_work`` is the reviewed WORK directory containing ``repo/``.
    ``out`` must be new; it receives checkout/, replay.json and a compressed
    extraction inventory. No returned Python/Racket programs are executed.
    """
    source_zip, return_zip = Path(source_zip).resolve(), Path(return_zip).resolve()
    owner, out = Path(compare_work).absolute(), Path(out).absolute()
    _no_symlinks(owner)
    _no_symlinks(out)
    if out.exists():
        raise FileExistsError(f"Destination must be new: {out}")
    if owner == out or owner in out.parents or out in owner.parents:
        raise ValueError("Fresh destination must be separate from the working review")
    with zipfile.ZipFile(source_zip) as original, zipfile.ZipFile(return_zip) as returned:
        files, seen = {}, set()
        for info in original.infolist():
            _safe_name(info.filename)
            key = info.filename.rstrip("/")
            if key in seen:
                raise ValueError(f"Duplicate archive member: {info.filename}")
            seen.add(key)
            kind = stat.S_IFMT(info.external_attr >> 16)
            if kind not in {0, stat.S_IFREG, stat.S_IFDIR} or info.flag_bits & 1:
                raise ValueError(f"Unsafe archive member type: {info.filename}")
            if not info.is_dir():
                if kind == stat.S_IFDIR:
                    raise ValueError(f"Nonregular archive member: {info.filename}")
                files[info.filename] = info
        prefix = "WORK/" if "WORK/PACKET-MANIFEST.json" in files else ""
        manifest_name = prefix + "PACKET-MANIFEST.json"
        raw_manifest = original.read(manifest_name)
        manifest = json.loads(raw_manifest)
        expected = {prefix + n: digest for n, digest in manifest["files"].items()}
        expected.update(manifest.get("layout", {}).get("entry_files", {}))
        expected[manifest_name] = hashlib.sha256(raw_manifest).hexdigest()
        if set(files) != set(expected):
            raise ValueError("Original archive inventory differs from packet manifest")
        checked = validate_full_return(returned, manifest)
        task, paths = checked["task_id"], checked["patch_paths"]
        contract = json.loads(returned.read('ASSIGNMENT.json'))
        targets = assignment_targets(contract)
        multi = contract.get('schema') == MULTI_SCHEMA
        if multi:
            from .review_full_collect import _reproduce
            _reproduce(contract, manifest, original)
        if not paths:
            raise ValueError("Return has no changed paths to replay")
        patches = {n: returned.read(n) for n in returned.namelist() if n.startswith("patches/")}
        comparisons = {}
        for path in paths:
            target = owner / path
            _no_symlinks(target)
            if not target.is_file():
                raise ValueError(f"Missing working-review comparison file: {path}")
            comparisons[path] = _sha(target)
        selected = set(expected)
        if runtime_closure:
            selected = set()
            for target_row in targets:
                tid = target_row['task_id']
                selected.update(_runtime_members(original, expected, prefix, tid,
                    target_row['generator'].get('rule_task_id') or tid))
        # An authority patch can require a source absent from the ordinary runtime mapping.
        selected.update(prefix + path for path in paths if prefix + path in expected)
        out.mkdir(parents=True, exist_ok=False)
        checkout = out / "checkout"
        work = checkout / "WORK" if prefix else checkout
        receipt = {"schema": "arcpuzzles-return-replay-v1", "status": "running",
            "packet_id": checked["packet_id"], "assignment_id": checked["assignment_id"], "task_id": task,
            "source_zip_sha256": _sha(source_zip), "return_zip_sha256": _sha(return_zip),
            "patch_sha256": {n: hashlib.sha256(raw).hexdigest() for n, raw in patches.items()},
            "extraction_mode": "declared_runtime_dependency_closure" if runtime_closure else "full_packet",
            "full_original_packet_extracted": not runtime_closure,
            "original_files": len(files), "extracted_files": len(selected),
            "work_root": str(work), "receipt_path": str(out / "replay.json"),
            "tests_run": False, "training_admitted": False, "commands": [], "changed_files": []}
        if multi:
            receipt.update(task_ids=target_ids(contract), repair_targets=targets)
        def save():
            (out / "replay.json").write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n")
        save()
        try:
            inventory = []
            for name in sorted(selected):
                raw = original.read(name)
                digest = hashlib.sha256(raw).hexdigest()
                if digest != expected[name]:
                    raise ValueError(f"Original manifest mismatch: {name}")
                target = checkout / name
                target.parent.mkdir(parents=True, exist_ok=True)
                # Exclusive creation also detects case aliases on filesystems
                # that cannot represent the packet's distinct source names.
                with target.open("xb") as stream:
                    stream.write(raw)
                inventory.append({"path": name, "sha256": digest, "bytes": len(raw)})
            raw_inventory = (json.dumps(inventory, sort_keys=True) + "\n").encode()
            compressed = out / "extraction-manifest.json.gz"
            compressed.write_bytes(gzip.compress(raw_inventory, mtime=0))
            receipt["extraction_inventory"] = {"path": str(compressed),
                "sha256": _sha(compressed), "raw_sha256": hashlib.sha256(raw_inventory).hexdigest()}
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
            def run(argv):
                process = subprocess.run(argv, cwd=work, env=env, capture_output=True, text=True, timeout=120)
                receipt["commands"].append({"argv": argv, "cwd": str(work), "exit_code": process.returncode,
                    "stdout": process.stdout, "stderr": process.stderr})
                save()
                if process.returncode:
                    raise ValueError(f"Replay command failed: {argv}: {process.stderr[:500]}")
                return process.stdout
            run(["git", "init", "-q"])
            top = run(["git", "rev-parse", "--show-toplevel"]).strip()
            if Path(top).resolve() != work.resolve():
                raise ValueError("Git top-level differs from exact fresh patch root")
            receipt["git_top_level"] = str(Path(top))
            git_paths = []
            for index, (name, raw) in enumerate(sorted(patches.items())):
                patch = out / f"source-{index:03d}.patch"
                patch.write_bytes(raw)
                for row in run(["git", "apply", "--numstat", "-z", str(patch)]).split("\0"):
                    if not row:
                        continue
                    fields = row.split("\t", 2)
                    if len(fields) != 3 or not fields[0].isdigit() or not fields[1].isdigit():
                        raise ValueError("Unsupported binary or renamed patch entry")
                    _safe_name(fields[2])
                    git_paths.append(fields[2])
            if sorted(git_paths) != sorted(paths):
                raise ValueError("Complete Git patch inventory differs from validated paths")
            for index in range(len(patches)):
                patch = str(out / f"source-{index:03d}.patch")
                run(["git", "apply", "--check", patch])
                run(["git", "apply", patch])
            canonical = 'repo/shared/data/canonical/puzzles.jsonl'
            if multi and canonical in paths:
                _canonical_only_task(original.read(prefix + canonical), (work / canonical).read_bytes(),
                                     rule_task_ids(contract))
            for path in paths:
                target = work / path
                _no_symlinks(target)
                digest = _sha(target)
                if digest != comparisons[path] or _sha(owner / path) != comparisons[path]:
                    raise ValueError(f"Applied path differs from reviewed final source: {path}")
                receipt["changed_files"].append({"path": path, "sha256": digest, "bytes": target.stat().st_size})
            receipt["generator_sha256"] = _sha(work / f"repo/generators/{task}/generator.py")
            if multi:
                receipt['generator_sha256_by_task'] = {
                    target_row['task_id']: _sha(work / ('repo/' + target_row['generator']['generator']))
                    for target_row in targets}
            receipt["status"] = "patch_replay_passed_tests_pending"
            save()
            return receipt
        except BaseException as exc:
            receipt.update(status="failed", error=f"{type(exc).__name__}: {exc}")
            save()
            raise
