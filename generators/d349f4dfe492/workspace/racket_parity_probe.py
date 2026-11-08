#!/usr/bin/env python3
"""Compare the task's Python rule mirror with the selected Racket authority.

Run through the packet wrapper from the packet root or repository root:

    python3 run_with_racket.py python3 \
      generators/d349f4dfe492/workspace/racket_parity_probe.py \
      --out ../checks/racket-parity.json

The probe uses only the supported public ``arcpuzzles apply`` command.  It sends
one batch (up to 64 grids), retains exact replay inputs and authority metadata,
and exits nonzero on any pixel mismatch or rule-hash mismatch.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

TASK_ID = "d349f4dfe492"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "shared" / "runtime"))


def load_generator():
    spec = importlib.util.spec_from_file_location(f"parity_{TASK_ID}", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--per-profile", type=int, default=3)
    args = parser.parse_args()
    if args.per_profile < 1:
        parser.error("--per-profile must be positive")

    gen = load_generator()
    cases = []
    for difficulty in ("easy", "medium", "hard"):
        for profile_index, profile in enumerate(gen.SCHEDULE_PROFILES):
            for repeat in range(args.per_profile):
                sample_index = profile_index + repeat * len(gen.SCHEDULE_PROFILES)
                seed = 710_000 + 10_000 * profile_index + 100 * repeat + len(cases)
                grid = gen.generate(seed, sample_index, difficulty=difficulty)
                cases.append(
                    {
                        "difficulty": difficulty,
                        "profile": profile,
                        "seed": seed,
                        "sample_index": sample_index,
                        "input": grid,
                        "python_output": gen.rule_mirror(grid),
                    }
                )
    if len(cases) > 64:
        parser.error("public apply accepts at most 64 grids; lower --per-profile")

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}_parity_") as tmp:
        tmpdir = Path(tmp)
        input_path = tmpdir / "inputs.json"
        authority_path = tmpdir / "authority.json"
        input_path.write_text(
            json.dumps({"inputs": [case["input"] for case in cases]}),
            encoding="utf-8",
        )
        command = [
            sys.executable,
            "-m",
            "arcpuzzles",
            "apply",
            TASK_ID,
            "--input",
            str(input_path),
            "--out",
            str(authority_path),
        ]
        completed = subprocess.run(
            command,
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
        )
        authority = json.loads(authority_path.read_text(encoding="utf-8")) if authority_path.exists() else None

    mismatches = []
    if completed.returncode == 0 and authority is not None:
        results = authority.get("results", [])
        if len(results) != len(cases):
            mismatches.append(
                {
                    "kind": "result_count",
                    "expected": len(cases),
                    "actual": len(results),
                }
            )
        for index, case in enumerate(cases[: len(results)]):
            racket_output = results[index].get("output")
            case["racket_output"] = racket_output
            case["matches"] = racket_output == case["python_output"]
            if not case["matches"]:
                mismatches.append(
                    {
                        "kind": "pixel_mismatch",
                        "index": index,
                        "difficulty": case["difficulty"],
                        "profile": case["profile"],
                        "seed": case["seed"],
                        "sample_index": case["sample_index"],
                    }
                )
    else:
        mismatches.append(
            {
                "kind": "apply_failed",
                "exit_code": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )

    metadata_ok = bool(
        authority
        and authority.get("executed_rule_hash") == gen.RULE_HASH
        and authority.get("rule_hash_matches_catalog") is True
        and authority.get("generator_sha256")
        == hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest()
    )
    if not metadata_ok:
        mismatches.append(
            {
                "kind": "authority_metadata",
                "expected_rule_hash": gen.RULE_HASH,
                "authority": {
                    key: authority.get(key) if authority else None
                    for key in (
                        "executed_rule_hash",
                        "catalog_rule_hash",
                        "rule_hash_matches_catalog",
                        "generator_sha256",
                    )
                },
            }
        )

    report = {
        "schema": "d349f4dfe492-racket-parity-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "declared_rule_hash": gen.RULE_HASH,
        "command": command,
        "command_cwd": str(REPO),
        "apply_exit_code": completed.returncode,
        "authority_metadata": {
            key: authority.get(key) if authority else None
            for key in (
                "schema",
                "reference",
                "rule_file",
                "executed_rule_hash",
                "catalog_rule_hash",
                "rule_hash_matches_catalog",
                "rule_text_sha256",
                "generator_sha256",
                "elapsed_seconds",
            )
        },
        "cases": cases,
        "mismatches": mismatches,
        "passed": not mismatches,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if mismatches:
        print(f"FAIL: {len(mismatches)} parity/metadata mismatch(es)", file=sys.stderr)
        return 1
    print(f"PASS: {len(cases)} generated grids match Racket", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
