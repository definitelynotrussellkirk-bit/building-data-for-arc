"""Replay the optional patch in a disposable copy and retain bounded evidence.

Run from the packet root:
    python3 -B repo/generators/547c45a21db1/workspace/tooling_proposal/verify_proposal.py

Only this proposal's checks directory is written. The shared source is copied,
never patched in place. Temporary runtime copies are removed after their source
manifests, commands, results, JUnit reports and complete logs have been saved.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


PROPOSAL = Path(__file__).resolve().parent
REPO = PROPOSAL.parents[3]
PACKET = REPO.parent
BASE_SOURCE_SHA256 = "e6213a5bde35eaecf5f97eaa070604398bbe0af0be9c7f0fef9a2227b8dbd569"
PATCHED_SOURCE_SHA256 = "e6bbaf38c0d1bbc68a0035126c8a938e953fa2c8a936eef908907fd2162f1d59"
SOURCE = Path("shared/tools/generator_semantic_gate.py")
TEST = Path("shared/tests/test_generator_semantic_gate.py")
REGRESSIONS = Path("shared/tests/test_generator_semantic_gate_declared_rivals.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_file(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)


def runtime(candidate, target, *, baseline=False):
    """Copy the exact gate, established test dependencies, and one canonical row."""
    copied = []

    def copy(relative, destination, owner=REPO):
        source = owner / relative
        copy_file(source, target / destination)
        copied.append({"source": str(source.relative_to(PACKET)),
                       "destination": str(destination), "sha256": sha(source)})

    copy(SOURCE, Path("scripts/generator_semantic_gate.py"), candidate)
    copy(TEST, Path("tests/test_generator_semantic_gate.py"), candidate)
    if baseline:
        copy_file(PROPOSAL / "proposal_regressions.py", target / "tests" / REGRESSIONS.name)
        copied.append({"source": str((PROPOSAL / "proposal_regressions.py").relative_to(PACKET)),
                       "destination": "tests/" + REGRESSIONS.name,
                       "sha256": sha(PROPOSAL / "proposal_regressions.py")})
    for name in ("canonical_profile_gate.py", "coder_synth_verify.py"):
        copy(Path("shared/tools") / name, Path("scripts") / name)
    for package, names in {
        "arc_repl": ("__init__.py", "racket_bridge.py"),
        "puzzle_generators": ("__init__.py", "base.py", "runner.py", "rule_wrap.py"),
    }.items():
        for name in names:
            copy(Path("shared/runtime") / package / name, Path(package) / name)
    for source in sorted((REPO / "shared/runtime/puzzle_generators/helpers").glob("*.py")):
        copy(source.relative_to(REPO), Path("puzzle_generators/helpers") / source.name)
    canonical = REPO / "shared/data/canonical/puzzles.jsonl"
    # The established suite has one corpus-reader regression, for this exact
    # task. Other cases install explicit synthetic canonical data via pytest.
    selected = [line for line in canonical.read_text().splitlines(True)
                if line.strip() and json.loads(line).get("task_id") == "7d09ccad28c8"]
    if not selected:
        raise RuntimeError("Missing canonical row needed by established reader regression")
    destination = target / "data/canonical/puzzles.jsonl"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("".join(selected))
    copied.append({"source": str(canonical.relative_to(PACKET)),
                   "source_sha256": sha(canonical), "destination": "data/canonical/puzzles.jsonl",
                   "selection": {"task_id": "7d09ccad28c8", "rows": len(selected)},
                   "sha256": sha(destination)})
    return copied


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", default="run-001", help="new evidence directory name")
    args = parser.parse_args()
    if not args.run or Path(args.run).name != args.run:
        parser.error("--run must be one directory name")
    output = PACKET / "checks/tooling-proposal" / args.run
    output.mkdir(parents=True, exist_ok=False)
    patch = PROPOSAL / "semantic_gate_declared_rivals.patch"
    originals = {str(path): sha(REPO / path) for path in (SOURCE, TEST)}
    if originals[str(SOURCE)] != BASE_SOURCE_SHA256:
        raise RuntimeError("Shared source changed; this proposal is bound to its recorded baseline")
    result = {"schema_version": 1, "started_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "optional proposal; shared source not modified", "commands": [],
              "invocation": {"cwd": str(Path.cwd()), "argv": sys.orig_argv},
              "verification_driver_sha256": sha(Path(__file__)),
              "original_source_hashes": originals, "patch_sha256": sha(patch),
              "patch": str(patch.relative_to(PACKET)), "evidence_dir": str(output.relative_to(PACKET)),
              "fixture_note": "Synthetic labelled lessons test gate control flow; no Racket labels claimed.",
              "source_manifests": {}}

    def command(name, argv, cwd, *, expected=None):
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONPATH"] = str(cwd)
        env["TMPDIR"] = str(output / "temporary")
        Path(env["TMPDIR"]).mkdir(exist_ok=True)
        completed = subprocess.run(argv, cwd=cwd, env=env, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log = output / (name + ".log")
        log.write_text(completed.stdout)
        record = {"name": name, "cwd": str(cwd.relative_to(PACKET)), "argv": argv,
                  "environment": {key: env[key] for key in ("PYTHONDONTWRITEBYTECODE", "PYTHONPATH", "TMPDIR")},
                  "exit_code": completed.returncode, "log": str(log.relative_to(PACKET)),
                  "log_sha256": sha(log)}
        result["commands"].append(record)
        print(f"{name}: exit={completed.returncode}", flush=True)
        if completed.stdout.strip():
            print(completed.stdout.splitlines()[-1], flush=True)
        if expected is not None and completed.returncode != expected:
            raise RuntimeError(f"{name}: expected exit {expected}, got {completed.returncode}; see {log}")
        return completed.returncode

    def pytest(name, target, tests, expected):
        junit = output / (name + ".xml")
        argv = [sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider",
                "--basetemp", str(output / (name + "-temp")), "--junitxml", str(junit), *tests]
        code = command(name, argv, target, expected=expected)
        result["commands"][-1]["junit"] = str(junit.relative_to(PACKET))
        result["commands"][-1]["junit_sha256"] = sha(junit)
        report = ET.parse(junit).getroot()
        suites = [report] if report.tag == "testsuite" else list(report)
        totals = {key: sum(int(suite.attrib.get(key, 0)) for suite in suites)
                  for key in ("tests", "failures", "errors", "skipped")}
        totals["passed"] = totals["tests"] - sum(totals[key] for key in ("failures", "errors", "skipped"))
        result["commands"][-1]["test_counts"] = totals
        shutil.rmtree(output / (name + "-temp"), ignore_errors=True)
        return code

    try:
        with tempfile.TemporaryDirectory(prefix="disposable-", dir=output) as temporary:
            temporary = Path(temporary)
            candidate = temporary / "repo"
            for path in (SOURCE, TEST):
                copy_file(REPO / path, candidate / path)
            before = temporary / "before-runtime"
            result["source_manifests"]["before"] = runtime(candidate, before, baseline=True)
            pytest("before-regressions", before, ["tests/" + REGRESSIONS.name], expected=1)
            command("patch-check", ["git", "apply", "--check", str(patch)], candidate, expected=0)
            command("patch-apply", ["git", "apply", str(patch)], candidate, expected=0)
            actual = sha(candidate / SOURCE)
            result["patched_source_sha256"] = actual
            if actual != PATCHED_SOURCE_SHA256:
                raise RuntimeError("Patched source differs from the reviewed proposal")
            after = temporary / "after-runtime"
            result["source_manifests"]["after"] = runtime(candidate, after)
            selected = "declared_query_changing or hookless or no_lesson_contract or malformed_lesson_declaration"
            pytest("after-regressions", after, ["tests/test_generator_semantic_gate.py", "-k", selected], expected=0)
            pytest("after-semantic-suite", after, ["tests/test_generator_semantic_gate.py"], expected=0)
        result["status"] = "PASS"
    except Exception as exc:
        result["status"] = "FAIL"
        result["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        result["final_shared_source_hashes"] = {str(path): sha(REPO / path) for path in (SOURCE, TEST)}
        result["shared_sources_unchanged"] = originals == result["final_shared_source_hashes"]
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (output / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
        shutil.rmtree(output / "temporary", ignore_errors=True)
        print(f"Evidence: {output / 'verification.json'}", flush=True)


if __name__ == "__main__":
    main()
