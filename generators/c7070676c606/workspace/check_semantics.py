"""Replay frozen semantic boundaries through the selected Racket authority.

Example, from packet root (payload/output paths are relative to repo):
  WORK/.venv/bin/python review.py run /absolute/WORK/.venv/bin/python \
    generators/c7070676c606/workspace/check_semantics.py \
    --out ../checks/semantic-boundaries-reference.json

This deliberately uses one ArcExecutor(use_racket=True) rather than
Catalog.apply: the public apply implementation copies a full runtime, which is
unsuitable for the current storage-constrained review. It uses the same bridge,
selected canonical source and REPL step interface, without any copied runtime.
Result-grid extraction follows arc_repl.sandbox's existing ArcExecutor pattern.
No Python oracle or generator helper supplies an expected label.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arc_repl.builtins import _unwrap
from arc_repl.executor import ArcExecutor
from reviewer_support import canonical_pairs, canonical_path, find_root


TASK = "c7070676c606"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="New report path; omit to print the full report")
    args = parser.parse_args()
    root = find_root(__file__)
    homes = (root / "generators" / TASK,
             root / "puzzle_generators" / "per_puzzle" / TASK)
    source = next(home / "generator.py" for home in homes if (home / "generator.py").is_file())
    fixture_path = next(home / "counterexamples" / "semantic_boundaries.json"
                        for home in homes if (home / "counterexamples" / "semantic_boundaries.json").is_file())
    fixtures = json.loads(fixture_path.read_text())
    with canonical_path(root).open() as handle:
        rows = (json.loads(line) for line in handle if line.strip())
        records = [row for row in rows if row.get("task_id") == TASK]
    if len(records) != 1:
        raise ValueError("Expected one selected canonical record")
    program = records[0]["program_solution"]
    rule_hash = hashlib.sha256(program.encode()).hexdigest()
    if rule_hash != fixtures["reference"]["rule_text_sha256"]:
        raise ValueError("Frozen boundaries belong to different selected-rule bytes")
    canonical = canonical_pairs(TASK, root=root, labeled_only=True)
    cases = fixtures["cases"]
    task = {"train": [{"input": pair["input"], "output": pair["output"]} for pair in canonical],
            "test": [{"input": case["input"]} for case in cases]}
    report = {"schema": "c7070676c606-semantic-boundary-replay-v1", "task_id": TASK,
              "generator_sha256": digest(source), "rule_text_sha256": rule_hash,
              "fixture_sha256": digest(fixture_path), "checker_sha256": digest(Path(__file__)),
              "authority": "selected canonical Racket rule; one ArcExecutor bridge; no runtime snapshot",
              "canonical_checks": [], "cases": []}
    with ArcExecutor(task, use_racket=True) as executor:
        load = executor.step(program)
        if load.startswith("ERROR"):
            raise RuntimeError(load)
        report["rule_load"] = load
        for index, pair in enumerate(canonical):
            observation = executor.step(f"(test! {index})")
            report["canonical_checks"].append({"variant": pair["variant"], "split": pair["split"],
                                                "pair_index": pair["pair_index"], "observation": observation,
                                                "passed": "PASS" in observation and "FAIL" not in observation})
        for index, case in enumerate(cases):
            observation = executor.step(f"(apply! {index})")
            output = None
            for token in observation.split():
                if token.startswith("_") and token[1:].isdigit() and token in executor._results:
                    output = _unwrap(executor._results[token])
                    break
            # The pinned rule reaches obj-cells with #f when rank lookup has
            # no target. An unrelated bridge or missing-rule error is not
            # successful evidence for this semantic boundary.
            missing_target_error = (
                observation.startswith("ERROR: Racket error: hash-ref: contract violation")
                and all(part in observation for part in
                        ("expected: hash?", "given: #f", "'cells")))
            passed = (output == case["output"] if case["valid_rank"]
                      else output is None and missing_target_error)
            report["cases"].append({"id": case["id"], "valid_rank": case["valid_rank"],
                                     "input": case["input"], "output": output,
                                     "observation": observation, "passed": passed})
        report["runtime"] = executor._bridge.runtime_identity
    report["generator_sha256_after"] = digest(source)
    report["generator_source_stable"] = report["generator_sha256"] == report["generator_sha256_after"]
    report["passed"] = (report["generator_source_stable"]
                        and all(row["passed"] for row in report["canonical_checks"])
                        and all(row["passed"] for row in report["cases"]))
    report["note"] = "This verifies fixed reference boundaries, not generated coverage or approval."
    rendered = json.dumps(report, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        with args.out.open("x") as handle:
            handle.write(rendered)
        print(json.dumps({"report": str(args.out), "passed": report["passed"],
                          "canonical_passes": sum(row["passed"] for row in report["canonical_checks"]),
                          "fixture_passes": sum(row["passed"] for row in report["cases"]),
                          "generator_sha256": report["generator_sha256"],
                          "generator_source_stable": report["generator_source_stable"],
                          "rule_text_sha256": rule_hash}, indent=2))
    else:
        print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
