#!/usr/bin/env python3
"""Replay an exact return delta on a new extraction of its original packet.

Standard library only. Never draws an assignment, deletes a checkout, imports
predecessor sources, or restores unrelated evidence/solve files from the return.
The source manifest is reviewer-authored and hash-bound by the return builder.
"""
from __future__ import annotations

import argparse
import hashlib
import io
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
import tarfile
import time
import zipfile
from xml.etree import ElementTree


DEFAULT_METADATA = "checks/packaging/source-manifest.json"
BUNDLE, BUNDLE_MANIFEST = "EVIDENCE-BUNDLE.tar.gz", "EVIDENCE-BUNDLE.json"
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
DIFF = re.compile(r"diff --git a/(repo/[^\s]+) b/(repo/[^\s]+)\Z")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def sha(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def safe_name(name):
    if not isinstance(name, str) or not name or "\\" in name or "\0" in name:
        raise ValueError(f"Unsafe member/path: {name!r}")
    path = PurePosixPath(name)
    if not path.parts or path.is_absolute() or path.as_posix() != name or any(p in {"..", ".git"} for p in path.parts):
        raise ValueError(f"Unsafe member/path: {name!r}")
    return path


def zip_inventory(archive):
    files, names = [], set()
    for info in archive.infolist():
        name = info.filename[:-1] if info.is_dir() else info.filename
        safe_name(name)
        if name.casefold() in names:
            raise ValueError(f"Repeated ZIP path: {name}")
        names.add(name.casefold())
        mode = info.external_attr >> 16
        if stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR}:
            raise ValueError(f"Nonregular ZIP member: {name}")
        if info.flag_bits & 1:
            raise ValueError(f"Encrypted ZIP member: {name}")
        files.append(info)
    ordinary = {i.filename.casefold() for i in files if not i.is_dir()}
    if any(parent.as_posix().casefold() in ordinary for name in ordinary
           for parent in PurePosixPath(name).parents):
        raise ValueError("ZIP contains a file/directory path conflict")
    return files


def bound_zip_bytes(archive, intake, name):
    safe_name(name)
    raw = archive.read(name)
    if intake.get("evidence_sha256", {}).get(name) != digest(raw):
        raise ValueError(f"INTAKE evidence hash differs: {name}")
    return raw


def read_bound_member(archive, intake, member):
    """Read one selected evidence file; never extract the complete nested tar."""
    safe_name(member)
    names = set(archive.namelist())
    if member in names:
        raw = bound_zip_bytes(archive, intake, member)
        return raw, {"member": member, "location": "zip", "sha256": digest(raw)}
    if not member.startswith("checks/") or not {BUNDLE, BUNDLE_MANIFEST} <= names:
        raise ValueError(f"Missing return evidence member: {member}")
    manifest_raw = bound_zip_bytes(archive, intake, BUNDLE_MANIFEST)
    bundle_raw = bound_zip_bytes(archive, intake, BUNDLE)
    manifest = json.loads(manifest_raw)
    rows = manifest.get("files", [])
    if (manifest.get("schema") != "arcpuzzles-evidence-bundle-v1"
            or manifest.get("archive") != BUNDLE or manifest.get("archive_sha256") != digest(bundle_raw)
            or not isinstance(rows, list) or not rows or manifest.get("count") != len(rows)):
        raise ValueError("Invalid evidence bundle identity")
    expected, folded = {}, set()
    for row in rows:
        name = row.get("path")
        safe_name(name)
        if (not name.startswith("checks/") or name.casefold() in folded
                or type(row.get("bytes")) is not int or row["bytes"] < 0
                or not isinstance(row.get("sha256"), str) or not SHA256.fullmatch(row["sha256"])):
            raise ValueError("Invalid evidence bundle entry")
        expected[name] = row
        folded.add(name.casefold())
    if manifest.get("expanded_bytes") != sum(row["bytes"] for row in rows) or member not in expected:
        raise ValueError("Evidence member/expanded size differs from manifest")
    if any(parent.as_posix().casefold() in folded for name in folded
           for parent in PurePosixPath(name).parents):
        raise ValueError("Evidence bundle contains conflicting paths")
    selected, seen = None, set()
    with tarfile.open(fileobj=io.BytesIO(bundle_raw), mode="r|gz") as nested:
        for info in nested:
            safe_name(info.name)
            row = expected.get(info.name)
            if row is None or info.name in seen or not info.isreg() or info.size != row["bytes"]:
                raise ValueError(f"Unlisted, repeated, or nonregular evidence member: {info.name}")
            seen.add(info.name)
            if info.name == member:
                handle = nested.extractfile(info)
                selected = handle.read(info.size + 1) if handle else b""
                if len(selected) != row["bytes"] or digest(selected) != row["sha256"]:
                    raise ValueError(f"Selected evidence member hash differs: {member}")
    if seen != set(expected) or selected is None:
        raise ValueError("Evidence bundle inventory differs from manifest")
    return selected, {"member": member, "location": BUNDLE, "sha256": digest(selected),
                      "bundle_sha256": digest(bundle_raw), "bundle_manifest_sha256": digest(manifest_raw),
                      "other_evidence_restored": False}


def source_contract(assignment, intake, source_hashes, patch):
    task = assignment.get("task_id")
    if not isinstance(task, str) or not re.fullmatch(r"[0-9a-f]{12}", task) or intake.get("task_id") != task:
        raise ValueError("Assignment/intake task identity differs")
    home = f"repo/generators/{task}/"
    def allowed(path):
        return (path in {home + "generator.py", home + "notes.md", home + "SUMMARY.md"}
                or path.startswith((home + "tests/", home + "workspace/", home + "counterexamples/"))
                or path == "repo/shared/data/canonical/puzzles.jsonl"
                or path.startswith("repo/shared/data/base/") and path in assignment.get("baseline_sha256", {}))
    paths, current, in_hunk = [], None, False
    for line in patch.splitlines():
        if line.startswith("diff --git "):
            header = DIFF.fullmatch(line)
            if header is None or header[1] != header[2]:
                raise ValueError("Unsupported or renamed patch path")
            current = header[1]
            safe_name(current)
            if not allowed(current) or current in paths:
                raise ValueError(f"Patch outside selected task or repeated: {current}")
            paths.append(current)
            in_hunk = False
        elif line.startswith(("GIT binary patch", "Binary files ", "rename from ", "rename to ",
                              "copy from ", "copy to ", "old mode ", "new mode ", "deleted file mode ")):
            raise ValueError("Binary, rename, mode, or deletion patch is unsupported")
        elif line.startswith("new file mode ") and line != "new file mode 100644":
            raise ValueError("Only regular nonexecutable new files are supported")
        elif line.startswith("@@ "):
            in_hunk = True
        elif not in_hunk and line.startswith(("--- ", "+++ ")):
            value = line[4:].split("\t", 1)[0]
            prefix = "a/" if line.startswith("--- ") else "b/"
            if value != prefix + str(current) and not (line.startswith("--- ") and value == "/dev/null"):
                raise ValueError("Patch file header differs from its declared path")
        if (current == "repo/shared/data/canonical/puzzles.jsonl" and in_hunk
                and line.startswith(("+", "-")) and not line.startswith(("+++", "---"))):
            changed_row = json.loads(line[1:])
            rule_task = assignment.get("generator", {}).get("rule_task_id", task)
            if not isinstance(changed_row, dict) or changed_row.get("task_id") != rule_task:
                raise ValueError("Canonical patch changes an unrelated task row")
    changed = intake.get("changed_paths")
    if (not paths or not isinstance(changed, list) or len(changed) != len(set(changed))
            or not isinstance(source_hashes, dict) or set(paths) != set(changed) or set(paths) != set(source_hashes)):
        raise ValueError("Patch, INTAKE.changed_paths and reviewer source manifest must have identical path sets")
    if any(not isinstance(value, str) or not SHA256.fullmatch(value) for value in source_hashes.values()):
        raise ValueError("Invalid reviewer-authored source digest")
    generator = home + "generator.py"
    expected = source_hashes.get(generator, assignment.get("generator", {}).get("generator_sha256"))
    if not isinstance(expected, str) or not SHA256.fullmatch(expected):
        raise ValueError("Missing final generator identity")
    return {"task_id": task, "paths": sorted(paths), "generator_sha256": expected}


def check_sources(work, source_hashes, task, expected_generator):
    actual = {}
    for relative, expected in source_hashes.items():
        safe_name(relative)
        target = work / relative
        if target.is_symlink() or not target.is_file() or not target.resolve().is_relative_to(work.resolve()):
            raise ValueError(f"Missing/unsafe replayed source: {relative}")
        actual[relative] = sha(target)
        if actual[relative] != expected:
            raise ValueError(f"Replayed source hash differs: {relative}")
    generator = work / f"repo/generators/{task}/generator.py"
    if sha(generator) != expected_generator:
        raise ValueError("Replayed task generator differs from the final declared bytes")
    return actual


def grid_from_file(path, key):
    value = json.loads(path.read_text())
    if isinstance(value, dict):
        if key in value:
            value = value[key]
        elif key + "s" in value and len(value[key + "s"]) == 1:
            value = value[key + "s"][0]
        else:
            raise ValueError(f"{path} must hold one grid or a single {key!r} entry")
    if (not isinstance(value, list) or not value or not isinstance(value[0], list) or not value[0]
            or any(not isinstance(row, list) or len(row) != len(value[0])
                   or any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in value)):
        raise ValueError(f"Invalid ARC grid: {path}")
    return value


def check_reference(receipt, task, generator_hash, reference_input, expected_output):
    results = receipt.get("results", [])
    if (receipt.get("task_id") != task or receipt.get("generator_sha256") != generator_hash
            or receipt.get("rule_hash_matches_catalog") is not True or len(results) != 1):
        raise ValueError("Fresh public apply receipt has a different source/rule/task identity")
    row = results[0]
    if (row.get("error") is not None or row.get("valid_output") is not True
            or row.get("input") != reference_input or row.get("output") != expected_output):
        raise ValueError("Fresh Racket input/output differs from the separately retained public reference")
    return {"matched_expected_output": True, "rule_hash": receipt["executed_rule_hash"],
            "rule_text_sha256": receipt["rule_text_sha256"], "input_sha256": row["input_sha256"],
            "output_sha256": row["output_sha256"]}


def check_counts(counts, expected=None):
    keys = ("tests", "passed", "failed", "errors", "skipped")
    if (not isinstance(counts, dict) or any(type(counts.get(k)) is not int or counts[k] < 0 for k in keys)
            or counts["passed"] <= 0 or counts["failed"] or counts["errors"]
            or counts["tests"] != sum(counts[k] for k in keys[1:])
            or expected is not None and counts["passed"] != expected):
        raise ValueError(f"Test counts do not establish the required pass: {counts!r}; expected passed={expected!r}")
    return counts


def junit_counts(path):
    root = ElementTree.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else root.findall("testsuite")
    if not suites:
        raise ValueError("Focused pytest did not retain a usable JUnit report")
    counts = {key: sum(int(s.get(attr, "0")) for s in suites) for key, attr in
              (("tests", "tests"), ("failed", "failures"), ("errors", "errors"), ("skipped", "skipped"))}
    counts["passed"] = counts["tests"] - counts["failed"] - counts["errors"] - counts["skipped"]
    return counts


def clean_environment(python, temporary):
    env = dict(os.environ)
    removed = []
    for name in list(env):
        if (name.startswith(("GIT_", "ARCPUZZLES_", "PYTEST_"))
                or name.startswith("PYTHON") and name != "PYTHONHASHSEED"
                or name in {"VIRTUAL_ENV", "CONDA_PREFIX", "RACKET_PATH"}):
            removed.append(name)
            env.pop(name)
    env.update(PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1",
               GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               TMPDIR=str(temporary), PATH=str(Path(python).parent) + os.pathsep + os.defpath)
    return env, sorted(removed)


class Recorder:
    def __init__(self, directory, fresh, report, env, timeout):
        if not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("Command timeout must be finite and positive")
        self.directory, self.fresh, self.report = directory, fresh, report
        self.env, self.timeout = env, timeout

    def save(self):
        temporary = self.directory / "report.json.tmp"
        temporary.write_bytes(json_bytes(self.report))
        temporary.replace(self.directory / "report.json")

    def run(self, label, argv, cwd, *, effective_cwd=None):
        argv = [str(a) for a in argv]
        log = self.directory / f"{label}.log"
        started = time.monotonic()
        row = {"label": label, "argv": argv, "actual_cwd": str(cwd),
               "cwd": cwd.relative_to(self.fresh).as_posix() if cwd.is_relative_to(self.fresh) else str(cwd),
               "effective_cwd": str(effective_cwd or cwd), "exit_code": None, "timed_out": False,
               "log": log.name, "status": "running"}
        self.report["commands"].append(row)
        self.save()
        print(json.dumps({"step": label, "status": "running"}), flush=True)
        process = None
        try:
            with log.open("xb") as handle:
                process = subprocess.Popen(argv, cwd=cwd, env=self.env, stdout=handle,
                                           stderr=subprocess.STDOUT, start_new_session=True)
                while True:
                    remaining = self.timeout - (time.monotonic() - started)
                    if remaining <= 0:
                        row["timed_out"] = True
                        raise TimeoutError(f"{label} exceeded {self.timeout} seconds")
                    try:
                        process.wait(timeout=min(30, remaining))
                        break
                    except subprocess.TimeoutExpired:
                        print(json.dumps({"step": label, "status": "running",
                                          "elapsed_seconds": round(time.monotonic() - started)}), flush=True)
                row["exit_code"] = process.returncode
        except BaseException as exc:
            row["error"] = repr(exc)
            if process is not None and process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=5)
                row["exit_code"] = process.returncode
            raise
        finally:
            row["elapsed_seconds"] = round(time.monotonic() - started, 3)
            row["status"] = "passed" if row["exit_code"] == 0 and not row["timed_out"] and "error" not in row else "failed"
            if log.exists():
                row["log_sha256"] = sha(log)
            self.save()
            print(json.dumps({"step": label, "exit_code": row["exit_code"], "status": row["status"]}), flush=True)
        if row["exit_code"] != 0:
            raise RuntimeError(f"{label} failed; see {log}")
        return log.read_text(errors="replace")


DEPENDENCY_PROBE = '''import importlib, importlib.util, json, sys
for name in ("arcpuzzles", "puzzle_generators", "arc_repl", "reviewer_support"):
    if importlib.util.find_spec(name) is not None:
        raise RuntimeError("Independent Python already exposes source package: " + name)
for name in ("pytest", "numpy", "PIL"):
    importlib.import_module(name)
print(json.dumps({"executable": sys.executable, "prefix": sys.prefix,
                  "version": sys.version, "third_party": ["pytest", "numpy", "PIL"],
                  "preinstalled_project_sources": False}))
'''


IMPORT_PROBE = '''import importlib, json, os, pathlib, sys
root = pathlib.Path(sys.argv[1]).resolve()
if pathlib.Path.cwd().resolve() != root:
    raise RuntimeError("Public wrapper did not select the fresh repository cwd")
origins = {}
for name in ("arcpuzzles", "puzzle_generators", "arc_repl", "reviewer_support"):
    module = importlib.import_module(name)
    origin = pathlib.Path(module.__file__).resolve()
    if not origin.is_relative_to(root):
        raise RuntimeError("Source imported outside fresh repository: " + str(origin))
    origins[name] = str(origin)
pathlib.Path(sys.argv[2]).write_text(json.dumps({"repo": str(root), "actual_cwd": os.getcwd(), "origins": origins}, indent=2) + "\\n")
'''


def extract_original(archive, fresh, report):
    members = zip_inventory(archive)
    if not {"review.py", "WORK/PACKET-MANIFEST.json"} <= set(archive.namelist()):
        raise ValueError("Original ZIP is not the expected outer-root/WORK packet layout")
    capacity = os.statvfs(fresh.parent)
    block = capacity.f_frsize
    blocks = sum(((m.file_size + block - 1) // block) * block for m in members if not m.is_dir())
    directories = {p.as_posix() for m in members for p in PurePosixPath(m.filename).parents
                   if p.as_posix() != "."}
    count = sum(not m.is_dir() for m in members)
    report["extraction"] = {"members": len(members), "files": count,
                            "uncompressed_bytes": sum(m.file_size for m in members),
                            "estimated_file_blocks": blocks, "available_bytes": capacity.f_bavail * block,
                            "estimated_inodes": count + len(directories), "available_inodes": capacity.f_favail,
                            "estimate_excludes_later_racket_and_portable_runtime": True}
    if blocks > capacity.f_bavail * block:
        raise OSError("Insufficient file-block capacity for original extraction")
    if capacity.f_favail and count + len(directories) > capacity.f_favail:
        raise OSError("Insufficient inodes for original extraction")
    fresh.mkdir()
    for info in members:
        target = fresh / info.filename
        if info.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target.open("xb") as destination:
                shutil.copyfileobj(source, destination, length=1024 * 1024)


def validate_packet_assignment(work, assignment):
    manifest = json.loads((work / "PACKET-MANIFEST.json").read_bytes())
    canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    task = assignment["task_id"]
    if (assignment.get("schema") != "arcpuzzles-full-assignment-v2"
            or assignment.get("packet_id") != digest(canonical)
            or task not in manifest.get("main_ids", [])
            or assignment.get("generator") != manifest.get("generators", {}).get(task)
            or assignment.get("question") not in manifest.get("questions", [])):
        raise ValueError("Returned assignment does not belong to the verified original packet")
    for path, expected in assignment.get("baseline_sha256", {}).items():
        if manifest["files"].get(path) != expected:
            raise ValueError(f"Assignment baseline differs from original packet: {path}")


def main(args):
    fresh = args.fresh_root.expanduser().resolve()
    receipts = args.receipts.expanduser().resolve()
    if fresh.exists() or args.fresh_root.is_symlink():
        raise FileExistsError(f"Fresh root must not exist: {fresh}")
    if receipts.exists() or args.receipts.is_symlink():
        raise FileExistsError(f"Receipt directory must not exist: {receipts}")
    if receipts.is_relative_to(fresh) or fresh.is_relative_to(receipts):
        raise ValueError("Fresh root and receipt directory must be separate trees")
    if not fresh.parent.is_dir():
        raise FileNotFoundError(f"Fresh root parent must already exist: {fresh.parent}")
    original = args.original_zip.expanduser().resolve(strict=True)
    returned = args.return_zip.expanduser().resolve(strict=True)
    reference = args.reference_input.expanduser().resolve(strict=True)
    expected = args.expected_output.expanduser().resolve(strict=True)
    if reference == expected:
        raise ValueError("Reference input and expected output must be separately saved files")
    python = args.python.expanduser().absolute()  # Preserve the independent venv entry point, including its symlink.
    if not python.is_file() or not os.access(python, os.X_OK):
        raise ValueError(f"Independent Python is not executable: {python}")
    temporary = Path(args.tmpdir or os.environ.get("TMPDIR", "/tmp")).expanduser().resolve()
    if temporary.is_relative_to(fresh):
        raise ValueError("Temporary runtime parent must exist outside the new extraction")
    temporary.mkdir(parents=True, exist_ok=True)
    receipts.mkdir(parents=True)
    env, removed = clean_environment(python, temporary)
    report = {"schema": "fresh-packet-patch-replay-v2", "status": "running",
              "driver_argv": sys.argv, "driver_cwd": str(Path.cwd()), "driver_sha256": sha(Path(__file__)),
              "original_zip": str(original), "original_zip_sha256": sha(original),
              "return_zip": str(returned), "return_zip_sha256": sha(returned), "fresh_root": str(fresh),
              "receipt_directory": str(receipts), "python": str(python), "commands": [],
              "environment": {"removed": removed, "TMPDIR": str(temporary), "PATH": env["PATH"],
                              "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
                              "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                              "GIT_CONFIG_NOSYSTEM": "1", "PYTHONHASHSEED": env.get("PYTHONHASHSEED")},
              "reference_files": {"input": str(reference), "input_file_sha256": sha(reference),
                                  "expected_output": str(expected), "expected_output_file_sha256": sha(expected)},
              "source_manifest_author": "reviewer; hash-bound by return builder metadata",
              "deletes_checkouts": False, "draws_assignments": False}
    recorder = Recorder(receipts, fresh, report, env, args.timeout)
    recorder.save()
    try:
        input_grid = grid_from_file(reference, "input")
        expected_grid = grid_from_file(expected, "output")
        with zipfile.ZipFile(returned) as archive:
            zip_inventory(archive)
            intake_raw = archive.read("INTAKE.json")
            intake = json.loads(intake_raw)
            results = json.loads(archive.read("RESULTS.json"))
            artifacts = {row["path"]: row["sha256"] for row in results.get("artifacts", [])}
            if (len(artifacts) != len(results.get("artifacts", []))
                    or artifacts.get("INTAKE.json") != digest(intake_raw)):
                raise ValueError("INTAKE is not bound by RESULTS artifacts")
            assignment_raw = bound_zip_bytes(archive, intake, "ASSIGNMENT.json")
            assignment = json.loads(assignment_raw)
            patch_raw = bound_zip_bytes(archive, intake, "patches/source.patch")
            if artifacts.get("patches/source.patch") != digest(patch_raw):
                raise ValueError("Source patch is not bound by RESULTS artifacts")
            for key in ("task_id", "assignment_id", "packet_id"):
                if intake.get(key) != assignment.get(key):
                    raise ValueError(f"Assignment/INTAKE identity differs: {key}")
            if results.get("assignment_id") != assignment.get("assignment_id"):
                raise ValueError("RESULTS assignment differs")
            metadata_raw, binding = read_bound_member(archive, intake, args.metadata_member)
            source_hashes = json.loads(metadata_raw)
            identity = source_contract(assignment, intake, source_hashes, patch_raw.decode("utf-8"))
        task, generator_hash = identity["task_id"], identity["generator_sha256"]
        if args.generator_sha256 is not None and args.generator_sha256 != generator_hash:
            raise ValueError("CLI final generator pin differs from the return's source manifest")
        report.update(task_id=task, assignment_id=assignment["assignment_id"],
                      assignment_sha256=digest(assignment_raw), source_patch_sha256=digest(patch_raw),
                      source_manifest_binding=binding, expected_source_sha256=source_hashes,
                      expected_generator_sha256=generator_hash)
        (receipts / "source.patch").write_bytes(patch_raw)
        (receipts / "source-manifest.json").write_bytes(metadata_raw)
        (receipts / "ASSIGNMENT.json").write_bytes(assignment_raw)
        (receipts / "INTAKE.json").write_bytes(intake_raw)
        shutil.copyfile(reference, receipts / "reference-input.json")
        shutil.copyfile(expected, receipts / "expected-output.json")
        recorder.save()
        dependency = recorder.run("independent-python", [python, "-I", "-c", DEPENDENCY_PROBE], receipts)
        report["independent_python"] = json.loads(dependency)

        with zipfile.ZipFile(original) as archive:
            extract_original(archive, fresh, report)
        recorder.save()
        recorder.run("original-verify", [python, "review.py", "verify"], fresh)
        work, repo = fresh / "WORK", fresh / "WORK/repo"
        validate_packet_assignment(work, assignment)
        assigned = work / "ASSIGNMENT.json"
        if assigned.exists() and assigned.read_bytes() != assignment_raw:
            raise ValueError("Original extraction contains a different assignment; refusing to redraw or replace it")
        assigned.write_bytes(assignment_raw)
        if sha(assigned) != digest(assignment_raw):
            raise ValueError("Copied assignment bytes differ from exact return assignment")
        recorder.run("git-init", ["git", "init", "-q"], work)
        actual_root = recorder.run("git-root", ["git", "rev-parse", "--show-toplevel"], work).strip()
        if Path(actual_root).resolve() != work or not (work / ".git").is_dir():
            raise ValueError("Git root is not the isolated fresh WORK root")
        report["git_root"] = actual_root
        patch_file = receipts / "source.patch"
        recorder.run("apply-check", ["git", "apply", "--check", patch_file], work)
        recorder.run("apply", ["git", "apply", patch_file], work)
        report["replayed_source_sha256"] = check_sources(work, source_hashes, task, generator_hash)
        recorder.save()

        recorder.run("racket-setup", [python, "review.py", "setup"], fresh, effective_cwd=work)
        replay = work / "checks/fresh-replay"
        replay.mkdir(parents=True, exist_ok=False)
        probe_path = replay / "source-imports.json"
        recorder.run("fresh-source-imports", [python, "review.py", "run", python, "-c", IMPORT_PROBE,
                                             repo, probe_path], fresh, effective_cwd=repo)
        report["fresh_source_imports"] = json.loads(probe_path.read_text())
        shutil.copyfile(probe_path, receipts / "source-imports.json")
        junit = replay / "focused-tests.xml"
        recorder.run("focused-tests", [python, "review.py", "run", python, "-m", "pytest", "-q",
                                       "--import-mode=importlib", "-p", "no:cacheprovider",
                                       f"generators/{task}/tests", f"--junitxml={junit}"], fresh, effective_cwd=repo)
        report["focused_test_counts"] = check_counts(junit_counts(junit), args.expected_focused_tests)
        shutil.copyfile(junit, receipts / "focused-tests.xml")
        check_output = work / "checks/fresh-task-tests"
        recorder.run("portable-task-tests", [python, "review.py", "run", python, "-m", "arcpuzzles", "check",
                                             task, "--stage", "task_tests", "--phase", "after", "--timeout",
                                             str(args.timeout), "--out", "../checks/fresh-task-tests"],
                     fresh, effective_cwd=repo)
        task_report = json.loads((check_output / "result.json").read_text())
        if (task_report.get("task_id") != task or task_report.get("stage") != "task_tests"
                or task_report.get("phase") != "after" or task_report.get("passed") is not True
                or task_report.get("exit_code") != 0 or task_report.get("timed_out") is not False
                or task_report.get("test_status") != "executed"):
            raise ValueError("Portable task_tests did not execute successfully")
        report["portable_test_counts"] = check_counts(task_report.get("test_counts"), args.expected_portable_tests)
        runtime_path = Path(task_report["runtime_path"])
        if not runtime_path.is_absolute() or not runtime_path.is_relative_to(temporary) or runtime_path.is_relative_to(repo):
            raise ValueError("Portable tests did not use an independent temporary runtime")
        report["portable_runtime_path"] = str(runtime_path)
        manifest_rows = task_report["runtime_manifest"]["files"]
        generator_rows = [row for row in manifest_rows if row["library_path"] == f"generators/{task}/generator.py"]
        if not generator_rows or any(row["sha256"] != generator_hash for row in generator_rows):
            raise ValueError("Portable runtime's selected generator differs from the replayed bytes")
        covered = []
        for relative, expected_hash in source_hashes.items():
            rows = [row for row in manifest_rows if row["library_path"] == relative.removeprefix("repo/")]
            if any(row["sha256"] != expected_hash for row in rows):
                raise ValueError(f"Portable runtime has different patched source bytes: {relative}")
            if rows:
                covered.append(relative)
        report["portable_manifest_covered_patch_paths"] = sorted(covered)
        report["portable_manifest_unmapped_patch_paths"] = sorted(set(source_hashes) - set(covered))
        kept = receipts / "portable-task-tests"
        kept.mkdir()
        for relative in ("result.json", "RUNTIME_MANIFEST.json", "progress.log", "checks/task_tests.xml"):
            source = check_output / relative
            if source.is_file():
                destination = kept / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
        recorder.save()

        (replay / "input.json").write_bytes(json_bytes(input_grid))
        recorder.run("public-racket-apply", [python, "review.py", "run", python, "-m", "arcpuzzles", "apply", task,
                                             "--input", "../checks/fresh-replay/input.json", "--out",
                                             "../checks/fresh-replay/racket.json", "--timeout", str(args.timeout)],
                     fresh, effective_cwd=repo)
        racket = json.loads((replay / "racket.json").read_text())
        shutil.copyfile(replay / "racket.json", receipts / "racket.json")
        report["reference_execution"] = check_reference(racket, task, generator_hash, input_grid, expected_grid)
        report["final_source_sha256"] = check_sources(work, source_hashes, task, generator_hash)
        if sha(assigned) != digest(assignment_raw):
            raise ValueError("Assignment bytes changed during replay")
        report["status"] = "passed"
        recorder.save()
        print(json.dumps({"status": "passed", "report": str(receipts / "report.json")}), flush=True)
        return 0
    except BaseException as exc:
        report["status"] = "failed"
        report["error"] = repr(exc)
        report["fresh_root_retained"] = fresh.exists()
        recorder.save()
        raise


def parser():
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("--original-zip", "--packet", dest="original_zip", type=Path, required=True)
    command.add_argument("--return-zip", type=Path, required=True)
    command.add_argument("--fresh-root", "--destination", dest="fresh_root", type=Path, required=True)
    command.add_argument("--python", type=Path, required=True, help="absolute path to independent Python with pytest, NumPy, Pillow")
    command.add_argument("--receipts", "--evidence", dest="receipts", type=Path, required=True, help="new directory outside fresh root")
    command.add_argument("--reference-input", type=Path, required=True, help="one saved generated input grid; no solve-private data")
    command.add_argument("--expected-output", type=Path, required=True, help="separately saved public Racket output grid")
    command.add_argument("--metadata-member", default=DEFAULT_METADATA, help="reviewer-authored changed-path to final-SHA map in return")
    command.add_argument("--generator-sha256", help="optional independent final generator pin")
    command.add_argument("--expected-focused-tests", type=int, help="optional exact focused passed-test count")
    command.add_argument("--expected-portable-tests", type=int, help="optional exact portable passed-test count")
    command.add_argument("--tmpdir", type=Path, help="runtime parent; defaults to TMPDIR or /tmp")
    command.add_argument("--timeout", type=float, default=900, help="seconds per subprocess/check, default 900")
    return command


if __name__ == "__main__":
    args = parser().parse_args()
    if not math.isfinite(args.timeout) or args.timeout <= 0 or any(value is not None and value <= 0 for value in
                                (args.expected_focused_tests, args.expected_portable_tests)):
        raise SystemExit("Timeout and any expected test counts must be positive")
    try:
        raise SystemExit(main(args))
    except Exception as error:
        print(f"Replay failed: {error}", file=sys.stderr)
        raise SystemExit(1)
