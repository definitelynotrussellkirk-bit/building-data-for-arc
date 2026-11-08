"""Verify the passive proposal on synthetic packets. Does not edit or draw from REPO."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_counts(path):
    root = ET.parse(path).getroot()
    cases = list(root.iter("testcase"))
    failed = sum(case.find("failure") is not None for case in cases)
    errors = sum(case.find("error") is not None for case in cases)
    skipped = sum(case.find("skipped") is not None for case in cases)
    return {"cases": len(cases), "passed": len(cases) - failed - errors - skipped,
            "failed": failed, "errors": errors, "skipped": skipped}


def run(repo, output):
    repo = repo.resolve()
    output = output.resolve()
    if not output.is_relative_to(HERE) or output == HERE:
        raise ValueError("Evidence output must be a new child directory of this proposal")
    output.mkdir(parents=True, exist_ok=False)
    original = repo / "src/arcpuzzles/review_full_draw.py"
    candidate = HERE / "candidate_review_full_draw.py"
    binding = json.loads((HERE / "source-binding.json").read_text())
    if digest(original) != binding["original_sha256"] or digest(candidate) != binding["candidate_sha256"]:
        raise ValueError("Original or candidate source changed; rebuild/review before verification")
    records = []
    for label, source, selector in (
        ("legacy", original, "partial_copy_has or retry_does or retry_finishes or journal_publish_failure or changed_copy"),
        ("proposal", candidate, None),
    ):
        junit = output / f"{label}-junit.xml"
        argv = [sys.executable, "-B", "-m", "pytest", "test_draw_journal.py", "-q",
                "-p", "no:cacheprovider", f"--rootdir={HERE}", f"--confcutdir={HERE}",
                f"--basetemp={output / (label + '-tmp')}", f"--junitxml={junit}"]
        if selector:
            argv += ["-k", selector]
        overrides = {"PYTHONDONTWRITEBYTECODE": "1", "DRAW_SOURCE": str(source), "DRAW_REPO": str(repo)}
        with (output / f"{label}.log").open("w") as log:
            result = subprocess.run(argv, cwd=HERE, env=dict(os.environ, **overrides),
                                    stdout=log, stderr=subprocess.STDOUT, timeout=60)
        records.append({"label": label, "argv": argv, "cwd": str(HERE),
                        "environment": overrides, "exit_code": result.returncode,
                        "counts": test_counts(junit), "source_sha256": digest(source)})
    witnesses = {}
    for label in ("legacy", "proposal"):
        folder = output / (label + "-tmp")
        for packet in sorted(folder.glob("*/synthetic-packet")):
            if packet.parent.is_symlink():
                continue
            test_name = packet.parent.name
            if not (test_name.startswith("test_partial_copy_has") or test_name.startswith("test_retry_does")):
                continue
            row = {"test": test_name, "assignment_exists": (packet / "ASSIGNMENT.json").exists(),
                   "pending_exists": (packet / ".review/pending-main-draw.json").exists()}
            for name in ("ASSIGNMENT.json", ".review/pending-main-draw.json"):
                if (packet / name).is_file():
                    value = json.loads((packet / name).read_text())
                    contract = value.get("contract", value)
                    row[name] = {key: contract[key] for key in ("seed", "task_id", "assignment_id", "packet_id")}
            witnesses.setdefault(label, []).append(row)
    (output / "fault-witnesses.json").write_text(json.dumps(witnesses, indent=2) + "\n")
    # The fixture builder is retained; avoid shipping disposable pytest trees
    # and their convenience symlinks as if they were independent evidence.
    for label in ("legacy", "proposal"):
        shutil.rmtree(output / (label + "-tmp"))
    report = {
        "schema": "passive-draw-journal-verification-v1",
        "status": "pass" if records[0]["exit_code"] == 1 and records[0]["counts"]["failed"] == 5
                  and records[0]["counts"]["errors"] == 0 and records[1]["exit_code"] == 0 else "fail",
        "runtime": {"python": sys.executable, "version": sys.version},
        "binding": binding, "tests_sha256": digest(HERE / "test_draw_journal.py"),
        "verification_runner_sha256": digest(Path(__file__)),
        "patch_sha256": digest(HERE / "proposal.patch"), "runs": records,
        "scope": "Synthetic fixtures only; no live assignment, baseline, generator, or shared source writes.",
    }
    (output / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"status": report["status"], "runs": [{"label": r["label"], "counts": r["counts"]} for r in records]}, indent=2))
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=HERE.parents[2] / "repo")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.repo, args.out))
