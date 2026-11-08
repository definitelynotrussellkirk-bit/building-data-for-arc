"""Plan/replay an explicitly provisional ARCpuzzles RECOVERY bundle.

This helper is not an alternative return validator. It reconstructs the original
packet and ultimately uses that packet's unchanged native return builder.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import sys
import zipfile

from zip_capacity_preflight import preflight


DOCS = {"REVIEW.md", "DECISIONS.md", "QUESTION_ANSWER.md", "FEEDBACK_TO_CODEX.md", "RESULTS.json"}
CONTRACTS = {"ASSIGNMENT.json", "BLIND_ASSIGNMENT.json", "AUDIT_ASSIGNMENT.json"}
PROVENANCE = "provenance/scoped_extraction_receipt.json"
RECEIPT = "checks/recovery-finalization/receipt.json"


class RecoveryError(ValueError):
    pass


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def read_json(path: Path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise RecoveryError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def safe_path(root: Path, name: str) -> Path:
    if (not isinstance(name, str) or not name or "\\" in name or ":" in name
            or any(ord(character) < 32 for character in name)
            or any(part in {"", ".", ".."} for part in name.split("/"))):
        raise RecoveryError(f"Unsafe relative path: {name!r}")
    current = root
    for part in PurePosixPath(name).parts:
        current = current / part
        if current.is_symlink():
            raise RecoveryError(f"Symlink in recovery path: {name}")
    if not current.resolve().is_relative_to(root.resolve()):
        raise RecoveryError(f"Recovery path escapes its root: {name}")
    return current


def valid_hash(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def patch_paths(raw: bytes, contract: dict) -> list[str]:
    """Conservative guard before Git; the unchanged native builder checks again."""
    if b"\0" in raw:
        raise RecoveryError("Binary patch is forbidden")
    text = raw.decode("utf-8")
    home = f"repo/generators/{contract['task_id']}/"
    paths = []
    current = None
    hunk = False
    canonical_changes = {"+": 0, "-": 0}
    for line in text.splitlines():
        if line.startswith(("GIT binary patch", "Binary files ", "rename from ", "rename to ",
                            "copy from ", "copy to ", "old mode ", "new mode ", "deleted file mode ")):
            raise RecoveryError("Binary/rename/copy/mode/deletion patches are forbidden")
        if line.startswith("new file mode ") and line != "new file mode 100644":
            raise RecoveryError("New files must be regular non-executable files")
        if line.startswith("diff "):
            match = re.fullmatch(r"diff --git a/(repo/[^\s]+) b/(repo/[^\s]+)", line)
            if not match or match[1] != match[2]:
                raise RecoveryError("Patch needs identical repo-rooted Git paths")
            current = match[1]
            safe_path(Path("/"), current)
            allowed = (current in {home + "generator.py", home + "notes.md", home + "SUMMARY.md"}
                       or current.startswith((home + "tests/", home + "workspace/", home + "counterexamples/"))
                       or current == "repo/shared/data/canonical/puzzles.jsonl"
                       or current.startswith("repo/shared/data/base/") and current in contract["baseline_sha256"])
            if not allowed or current in paths:
                raise RecoveryError(f"Repeated or out-of-scope patch path: {current}")
            paths.append(current)
            hunk = False
        elif line.startswith("@@ "):
            if current is None:
                raise RecoveryError("Patch hunk has no Git path header")
            hunk = True
        elif not hunk and line.startswith(("--- ", "+++ ")):
            expected = ("a/" if line.startswith("--- ") else "b/") + str(current)
            actual = line[4:].split("\t", 1)[0]
            if actual != expected and not (line.startswith("--- ") and actual == "/dev/null"):
                raise RecoveryError("Patch file header escapes its declared path")
        elif hunk and current == "repo/shared/data/canonical/puzzles.jsonl" and line.startswith(("+", "-")):
            if json.loads(line[1:]).get("task_id") != contract["generator"]["rule_task_id"]:
                raise RecoveryError("Canonical patch changes an unrelated task")
            canonical_changes[line[0]] += 1
    if not paths or canonical_changes["+"] != canonical_changes["-"]:
        raise RecoveryError("Patch is empty or changes the canonical row count")
    return paths


def load_recovery(root: Path) -> tuple[dict, dict]:
    config = read_json(safe_path(root, "recovery.json"))
    if config.get("schema") != "arcpuzzles-recovery-v1":
        raise RecoveryError("Unknown recovery manifest schema")
    for key in ("original_archive_sha256", "patch_sha256", "final_generator_sha256", "packet_id"):
        if not valid_hash(config.get(key)):
            raise RecoveryError(f"Invalid SHA-256 field: {key}")
    files = config.get("files")
    if not isinstance(files, dict):
        raise RecoveryError("Recovery files must be a path-to-SHA-256 map")
    required = {"contracts/ASSIGNMENT.json", PROVENANCE, *("payload/" + name for name in DOCS)}
    if not required <= files.keys():
        raise RecoveryError(f"Missing recovery files: {sorted(required - files.keys())}")
    spellings = set()
    for name, expected in files.items():
        path = safe_path(root, name)
        allowed = (name in {"contracts/" + item for item in CONTRACTS} or name == PROVENANCE
                   or name in {"payload/" + item for item in DOCS | {"AUDIT.md"}}
                   or name.startswith(("payload/checks/", "payload/solve/", "payload/solve-blind/")))
        if (not allowed or ".review" in PurePosixPath(name).parts
                or name.startswith(("payload/checks/recovery-finalization/", "payload/checks/recovery-task-tests/"))
                or name.casefold() in spellings or not valid_hash(expected)):
            raise RecoveryError(f"Forbidden, repeated or invalid recovery file: {name}")
        spellings.add(name.casefold())
        if not path.is_file() or sha256(path) != expected:
            raise RecoveryError(f"Recovery file hash differs: {name}")
    for folder in ("contracts", "payload", "provenance"):
        for path in safe_path(root, folder).rglob("*"):
            if path.is_symlink() or path.is_file() and path.relative_to(root).as_posix() not in files:
                raise RecoveryError(f"Undeclared or linked recovery payload: {path.relative_to(root)}")
    original = read_json(safe_path(root, PROVENANCE))
    if original.get("archive_sha256") != config["original_archive_sha256"]:
        raise RecoveryError("Original archive identity differs from the scoped extraction receipt")
    contract = read_json(safe_path(root, "contracts/ASSIGNMENT.json"))
    if contract.get("schema") != "arcpuzzles-full-assignment-v2":
        raise RecoveryError("Unsupported original assignment contract")
    for key in ("packet_id", "assignment_id", "task_id"):
        if contract.get(key) != config.get(key):
            raise RecoveryError(f"Recovery identity differs from original assignment: {key}")
    if not valid_hash(contract.get("seed")):
        raise RecoveryError("Original assignment seed must be 32 hexadecimal bytes")
    patch = safe_path(root, "source.patch")
    if not patch.is_file() or sha256(patch) != config["patch_sha256"]:
        raise RecoveryError("Source patch hash differs")
    config["validated_patch_paths"] = patch_paths(patch.read_bytes(), contract)
    commands = config.get("focused_tests")
    if not isinstance(commands, list) or not commands:
        raise RecoveryError("At least one exact focused-test command is required")
    for command in commands:
        if not isinstance(command, dict) or command.get("cwd") not in {"WORK", "WORK/repo"}:
            raise RecoveryError("Focused-test cwd must be WORK or WORK/repo")
        argv = command.get("argv")
        if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or not arg or "\0" in arg for arg in argv):
            raise RecoveryError("Focused tests need a nonempty argv array")
        timeout = command.get("timeout_seconds", 900)
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
            raise RecoveryError("Command timeout must be finite and positive")
    return config, contract


def save_report(path: Path, report: dict) -> None:
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    os.replace(temporary, path)


def replay(recovery: Path, archive: Path, destination: Path, config: dict, contract: dict,
           report: dict, python: str) -> dict:
    destination.mkdir(parents=True, exist_ok=False)
    receipt_path = destination / "RECOVERY-FINALIZATION.json"
    environment = dict(os.environ)
    for name in ("PYTHONPATH", "PYTHONHOME", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE",
                 "GIT_COMMON_DIR", "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
                 "GIT_CONFIG", "GIT_CONFIG_COUNT"):
        environment.pop(name, None)
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTHONNOUSERSITE="1")

    def run(phase, argv, cwd, timeout=900):
        command = {"phase": phase, "argv": [str(arg) for arg in argv], "cwd": str(cwd),
                   "started_at_utc": datetime.now(timezone.utc).isoformat(), "exit_code": None,
                   "timed_out": False, "environment": {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}}
        report["commands"].append(command)
        save_report(receipt_path, report)
        try:
            process = subprocess.Popen(command["argv"], cwd=cwd, env=environment,
                                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                       start_new_session=True)
            try:
                stdout, stderr = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                command["timed_out"] = True
                os.killpg(process.pid, signal.SIGKILL)
                stdout, stderr = process.communicate()
            command.update(exit_code=process.returncode, stdout=stdout, stderr=stderr)
        except OSError as error:
            command["error"] = str(error)
        save_report(receipt_path, report)
        if command["exit_code"] != 0 or command["timed_out"]:
            raise RecoveryError(f"Command failed: {phase}; see retained receipt")
        return command

    try:
        report["status"] = "replaying"
        save_report(receipt_path, report)
        with zipfile.ZipFile(archive) as source:
            source.extractall(destination)
        work = destination / "WORK"
        if sha256(work / "PACKET-MANIFEST.json") != config["packet_id"]:
            raise RecoveryError("Extracted packet ID differs from the saved assignment")
        run("native_verify", [python, "-B", "review.py", "verify"], destination)
        script = ("from pathlib import Path; import sys; root=Path(sys.argv[1]); "
                  "sys.path.insert(0,str(root/'repo/src')); "
                  "from arcpuzzles.review_full_draw import draw_main,draw_audit; "
                  "draw_main(root,seed=bytes.fromhex(sys.argv[2])); "
                  "draw_audit(root,seed=bytes.fromhex(sys.argv[3])) if sys.argv[3] else None")
        audit_name = "contracts/AUDIT_ASSIGNMENT.json"
        audit = read_json(recovery / audit_name) if audit_name in config["files"] else None
        run("native_draw", [python, "-B", "-c", script, str(work), contract["seed"], audit["seed"] if audit else ""], destination)
        contracts = {}
        for name in CONTRACTS:
            expected = recovery / "contracts" / name
            actual = work / name
            if expected.exists() != actual.exists() or expected.exists() and sha256(expected) != sha256(actual):
                raise RecoveryError(f"Native draw did not recreate exact contract: {name}")
            if actual.exists():
                contracts[name] = read_json(actual)
        canonical = work / "repo/shared/data/canonical/puzzles.jsonl"
        original_canonical = sha256(canonical)
        run("git_init", ["git", "init", "-q"], work)
        top = run("git_root", ["git", "rev-parse", "--show-toplevel"], work)
        if Path(top["stdout"].strip()).resolve() != work.resolve():
            raise RecoveryError("Git root is not the fresh WORK directory")
        patch = recovery / "source.patch"
        run("git_apply_check", ["git", "apply", "--check", str(patch)], work)
        run("git_apply", ["git", "apply", str(patch)], work)
        generator = safe_path(work / "repo", contract["generator"]["generator"])
        if sha256(generator) != config["final_generator_sha256"]:
            raise RecoveryError("Replayed generator differs from the reported final source")
        for name, expected in config["files"].items():
            if not name.startswith("payload/"):
                continue
            source = safe_path(recovery, name)
            target = safe_path(work, name.removeprefix("payload/"))
            if sha256(source) != expected:
                raise RecoveryError(f"Recovery overlay changed during replay: {name}")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for folder, contract_name, private in (("solve", "ASSIGNMENT.json", "solve-private"),
                                               ("solve-blind", "BLIND_ASSIGNMENT.json", "solve-private-blind")):
            summary_path = work / folder / "summary.json"
            if not summary_path.is_file():
                continue
            summary = read_json(summary_path)
            if summary.get("status") == "blocked":
                continue
            bound = contracts[contract_name]
            source = safe_path(work / "repo", bound["generator"]["generator"])
            expected_canonical = sha256(canonical) if folder == "solve" else original_canonical
            if (summary.get("task_id") != bound["task_id"]
                    or sha256(source) != summary.get("generator_hash")
                    or summary.get("canonical_sha256") != expected_canonical
                    or folder == "solve-blind" and sha256(source) != bound["generator"]["generator_sha256"]):
                raise RecoveryError(f"Recovered source/canonical binding differs for {folder}")
            private_source = work / ".review" / private / "generator.py"
            if private_source.exists() and (private_source.is_symlink() or sha256(private_source) != sha256(source)):
                raise RecoveryError(f"Conflicting private source snapshot for {folder}")
            snapshot = safe_path(work, folder + "/source/generator.py")
            if snapshot.exists() and sha256(snapshot) != sha256(source):
                raise RecoveryError(f"Conflicting public source snapshot for {folder}")
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            if not snapshot.exists():
                shutil.copyfile(source, snapshot)
        run("native_setup", [python, "-B", "setup_racket.py"], work)
        verification = [run("native_task_tests", [python, "-B", "run_with_racket.py", python, "-B", "-m", "arcpuzzles",
                            "check", contract["task_id"], "--stage", "task_tests", "--phase", "after", "--timeout", "600",
                            "--out", "../checks/recovery-task-tests"], work, timeout=660)]
        for index, command in enumerate(config["focused_tests"], 1):
            argv = [python if arg == "{python}" else arg for arg in command["argv"]]
            verification.append(run(f"focused_{index}", argv, safe_path(destination, command["cwd"]),
                                    command.get("timeout_seconds", 900)))
        if sha256(generator) != config["final_generator_sha256"]:
            raise RecoveryError("Focused tests changed the final generator bytes")
        for name, expected in config["files"].items():
            if name.startswith("payload/"):
                retained = safe_path(work, name.removeprefix("payload/"))
            elif name.startswith("contracts/"):
                retained = safe_path(work, name.removeprefix("contracts/"))
            else:
                continue
            if not retained.is_file() or sha256(retained) != expected:
                raise RecoveryError(f"Focused commands changed retained recovery evidence: {name}")
        for folder in ("solve", "solve-blind"):
            summary = work / folder / "summary.json"
            if summary.is_file() and read_json(summary).get("status") != "blocked":
                if sha256(safe_path(work, folder + "/source/generator.py")) != read_json(summary).get("generator_hash"):
                    raise RecoveryError(f"Focused commands changed the {folder} source snapshot")
        results_path = work / "RESULTS.json"
        results = read_json(results_path)
        commands = results.setdefault("verification_commands", [])
        for command in verification:
            cwd = Path(command["cwd"])
            commands.append({"cwd": "packet_root" if cwd == work else cwd.relative_to(work).as_posix(),
                             "argv": command["argv"], "exit_code": command["exit_code"],
                             "source_sha256": config["final_generator_sha256"], "evidence_paths": [RECEIPT]})
        results_path.write_text(json.dumps(results, indent=2, sort_keys=True) + "\n")
        evidence = safe_path(work, RECEIPT)
        evidence.parent.mkdir(parents=True, exist_ok=False)
        report["status"] = "focused_tests_passed"
        save_report(evidence, report)
        output = work / f"review_response_{contract['assignment_id']}.zip"
        run("native_package_return", [python, "-B", "package_return.py", "--out", str(output)], work)
        with zipfile.ZipFile(output) as final:
            if hashlib.sha256(final.read("patches/source.patch")).hexdigest() != config["patch_sha256"]:
                raise RecoveryError("Native final delta differs from the exact patch replayed")
        report.update(status="official_return_built", exit_code=0, official_return_created=True,
                      return_zip=str(output), return_zip_sha256=sha256(output),
                      completion_state=results.get("completion_state"),
                      note="Native builder succeeded; reported completion state and solve history were not upgraded.")
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        report.update(status="replay_failed", exit_code=1, error=str(error))
    save_report(receipt_path, report)
    return report


def finalize(recovery: Path, archive: Path, destination: Path, *, execute: bool = False,
             python: str | None = None) -> dict:
    report = {"schema": "arcpuzzles-recovery-finalization-v1", "official_return_created": False,
              "mode": "execute" if execute else "plan", "commands": []}
    try:
        if ".." in Path(destination).parts:
            raise RecoveryError("Destination must not contain '..'")
        recovery = Path(os.path.abspath(recovery))
        destination = Path(os.path.abspath(destination))
        if recovery.is_symlink() or destination.exists() or destination.is_symlink():
            raise RecoveryError("Recovery root must be real and destination must not already exist")
        if destination.resolve().is_relative_to(recovery.resolve()):
            raise RecoveryError("Destination must be outside the recovery bundle")
        selected_python = python or sys.executable
        selected_python = os.path.abspath(shutil.which(selected_python) or selected_python)
        if not Path(selected_python).is_file():
            raise RecoveryError("Selected Python interpreter does not exist")
        report["python"] = selected_python
        config, contract = load_recovery(recovery)
        if sha256(archive) != config["original_archive_sha256"]:
            raise RecoveryError("Original ZIP SHA-256 differs from the preserved packet")
        capacity = preflight(archive, destination, reserve_bytes=config.get("reserve_bytes", 536870912),
                             reserve_inodes=config.get("reserve_inodes", 4096))
        report.update(capacity=capacity, assignment_id=contract["assignment_id"], packet_id=contract["packet_id"],
                      original_archive_sha256=config["original_archive_sha256"], patch_sha256=config["patch_sha256"],
                      final_generator_sha256=config["final_generator_sha256"], patch_paths=config["validated_patch_paths"],
                      focused_tests=config["focused_tests"], destination=str(destination))
        if capacity["exit_code"]:
            return {**report, "status": "capacity_blocked", "exit_code": capacity["exit_code"]}
        if not execute:
            return {**report, "status": "ready_to_replay", "exit_code": 0,
                    "steps": ["Extract exact original ZIP", "Run native packet verification", "Recreate fixed-seed native assignments and frozen baseline",
                              "Check/apply allowed Git patch", "Restore hash-bound public reports and solve records",
                              "Run focused tests", "Invoke unchanged native package_return.py"]}
        return replay(recovery, archive, destination, config, contract, report, selected_python)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {**report, "status": "invalid_recovery", "exit_code": 2, "error": str(error)}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recovery", type=Path, required=True, help="extracted, provisional RECOVERY directory")
    parser.add_argument("--archive", type=Path, required=True, help="exact original review ZIP")
    parser.add_argument("--destination", type=Path, required=True, help="new directory; existing directories are refused")
    parser.add_argument("--python", default=sys.executable, help="Python 3.12+ with pytest, NumPy and Pillow available in isolation")
    parser.add_argument("--execute", action="store_true", help="perform the displayed recovery workflow; default is read-only planning")
    arguments = parser.parse_args(argv)
    report = finalize(arguments.recovery, arguments.archive, arguments.destination,
                      execute=arguments.execute, python=arguments.python)
    print(json.dumps(report, indent=2, sort_keys=True))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
