#!/usr/bin/env python3
"""Hash-guarded installer for the 351de765e33f ARCpuzzles repair payload."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PACKAGE_ROOT / "payload-manifest.json"
PAYLOAD_ROOT = PACKAGE_ROOT / "payload"
TASK_ID = "351de765e33f"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def within(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath((str(root.resolve()), str(candidate.resolve(strict=False)))) == str(root.resolve())
    except ValueError:
        return False


def inspect(repo: Path, manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    states: list[dict[str, Any]] = []
    errors: list[str] = []
    for rel, entry in sorted(manifest["files"].items()):
        destination = repo / Path(rel)
        if not within(repo, destination):
            errors.append(f"unsafe payload path escapes repository: {rel}")
            continue
        if destination.is_symlink():
            errors.append(f"refusing symlink destination: {rel}")
            continue
        repaired = entry["repaired_sha256"]
        baseline = entry.get("baseline_sha256")
        if destination.exists():
            if not destination.is_file():
                errors.append(f"destination is not a regular file: {rel}")
                continue
            current = sha256(destination)
            if current == repaired:
                state = "repaired"
            elif baseline is not None and current == baseline:
                state = "baseline"
            else:
                state = "unknown"
                errors.append(
                    f"unexpected bytes for {rel}: {current}; expected baseline={baseline} or repaired={repaired}"
                )
        else:
            current = None
            if baseline is None:
                state = "absent"
            else:
                state = "missing"
                errors.append(f"required baseline file is missing: {rel}")
        states.append({"path": rel, "state": state, "current_sha256": current})
    return states, errors


def apply(repo: Path, manifest: dict[str, Any], states: list[dict[str, Any]]) -> list[str]:
    changed: list[str] = []
    state_by_path = {item["path"]: item["state"] for item in states}
    for rel, entry in sorted(manifest["files"].items()):
        if state_by_path[rel] == "repaired":
            continue
        source = PAYLOAD_ROOT / Path(rel)
        if sha256(source) != entry["repaired_sha256"]:
            raise RuntimeError(f"payload hash mismatch before write: {rel}")
        destination = repo / Path(rel)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary_name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(source.read_bytes())
                handle.flush()
                os.fsync(handle.fileno())
            shutil.copymode(source, temporary)
            os.replace(temporary, destination)
        finally:
            temporary.unlink(missing_ok=True)
        changed.append(rel)
    return changed


def runtime_environment(repo: Path, bridge: Path) -> dict[str, str]:
    package = bridge / "puzzle_generators"
    per_puzzle = package / "per_puzzle"
    selected = per_puzzle / TASK_ID
    selected.mkdir(parents=True)
    namespace = "from pkgutil import extend_path\n__path__ = extend_path(__path__, __name__)\n"
    (package / "__init__.py").write_text(namespace)
    (per_puzzle / "__init__.py").write_text(namespace)
    (selected / "__init__.py").write_text("")
    source = repo / "generators" / TASK_ID / "generator.py"
    try:
        (selected / "generator.py").symlink_to(source)
    except OSError:
        shutil.copy2(source, selected / "generator.py")
    paths = [bridge, repo, repo / "shared" / "runtime"]
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = os.pathsep.join(str(path) for path in paths if path.exists())
    if existing:
        env["PYTHONPATH"] += os.pathsep + existing
    return env


def run_command(command: list[str], *, cwd: Path, env: dict[str, str]) -> dict[str, Any]:
    print("+", " ".join(command), file=sys.stderr)
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    return {
        "argv": command,
        "cwd": str(cwd),
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def verify(repo: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    compile_failures = []
    for rel in sorted(manifest["files"]):
        if rel.endswith(".py"):
            path = repo / rel
            try:
                compile(path.read_text(), str(path), "exec")
            except (SyntaxError, UnicodeError) as exc:
                compile_failures.append({"path": rel, "error": str(exc)})
    if compile_failures:
        return {"status": "FAIL", "compile_failures": compile_failures, "commands": []}

    commands = []
    with tempfile.TemporaryDirectory(prefix="arc-repair-verify-") as temp_name:
        temp = Path(temp_name)
        bridge = temp / "bridge"
        env = runtime_environment(repo, bridge)

        # The inherited fixture opens data/canonical/puzzles.jsonl relative to cwd.
        canonical_candidates = [
            repo / "data" / "canonical",
            repo / "shared" / "data" / "canonical",
        ]
        canonical = next((path for path in canonical_candidates if path.exists()), None)
        test_cwd = temp / "test-cwd"
        (test_cwd / "data").mkdir(parents=True)
        if canonical is not None:
            try:
                (test_cwd / "data" / "canonical").symlink_to(canonical, target_is_directory=True)
            except OSError:
                shutil.copytree(canonical, test_cwd / "data" / "canonical")

        test_command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            str(repo / "generators" / TASK_ID / "tests"),
        ]
        commands.append(run_command(test_command, cwd=test_cwd, env=env))
        verifier_command = [
            sys.executable,
            str(repo / "generators" / TASK_ID / "workspace" / "verify_repair.py"),
            "--repo",
            str(repo),
        ]
        commands.append(run_command(verifier_command, cwd=repo, env=env))

    return {
        "status": "PASS" if all(item["exit_code"] == 0 for item in commands) else "FAIL",
        "compile_failures": compile_failures,
        "commands": commands,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("--check", action="store_true", help="inspect hashes (default when --apply is absent)")
    parser.add_argument("--apply", action="store_true", help="write baseline/absent payload files atomically")
    parser.add_argument("--verify", action="store_true", help="run compile checks, target tests, and semantic verifier")
    parser.add_argument("--json-out", type=Path)
    args = parser.parse_args()

    repo = args.repository.resolve()
    if not repo.is_dir():
        parser.error(f"repository directory does not exist: {repo}")
    manifest = json.loads(MANIFEST_PATH.read_text())
    states, errors = inspect(repo, manifest)
    receipt: dict[str, Any] = {
        "format": "arc-generator-repair-install-v1",
        "task_id": TASK_ID,
        "repository": str(repo),
        "preflight": states,
        "changed": [],
        "verification": None,
        "errors": errors,
    }
    if errors:
        receipt["status"] = "REFUSED"
    else:
        if args.apply:
            receipt["changed"] = apply(repo, manifest, states)
            post_states, post_errors = inspect(repo, manifest)
            receipt["post_apply"] = post_states
            receipt["errors"].extend(post_errors)
        else:
            receipt["post_apply"] = states
        if not receipt["errors"] and args.verify:
            if any(item["state"] != "repaired" for item in receipt["post_apply"]):
                receipt["errors"].append("--verify requires an already-repaired tree or --apply")
            else:
                receipt["verification"] = verify(repo, manifest)
                if receipt["verification"]["status"] != "PASS":
                    receipt["errors"].append("verification command failed")
        receipt["status"] = "PASS" if not receipt["errors"] else "FAIL"

    text = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    print(text, end="")
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(text)
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
