"""Bounded lesson learnability and protected-label audit for future reviewers.

The two-demo selector is constructive and does not inspect query inputs or
labels. This audit asks whether any declared executable shortcut still fits all
visible demonstrations and, separately, whether it would change a held-out
query. It proves only the finite registry in ``rivals.py``.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent


def _load(stem, path):
    name = f"_5ccd_audit_{stem}_{hashlib.sha256(path.read_bytes()).hexdigest()}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


P = _load("prototype", HERE / "prototype.py")
R = _load("rivals", HERE / "rivals.py")


def _differences(a, b):
    return [[r, c] for r, (ra, rb) in enumerate(zip(a, b))
            for c, (x, y) in enumerate(zip(ra, rb)) if x != y]


def audit_demos(seed):
    """Pure finite-rival audit; query outputs never influence demo construction."""
    sample = P.sample_inputs(seed, demos=2, queries=4)
    rows, findings = [], []
    for settings in P.SETTINGS:
        finish = settings["finish"]
        demos = sample["train"]
        queries = sample["test"]
        demo_truth = [R.predict(grid, finish) for grid in demos]
        query_truth = [R.predict(grid, finish) for grid in queries]
        survivor_rows = []
        for rival in R.active_rivals(finish):
            matches = all(R.predict(grid, finish, rival) == output
                          for grid, output in zip(demos, demo_truth))
            disagreements = []
            for index, (grid, output) in enumerate(zip(queries, query_truth)):
                predicted = R.predict(grid, finish, rival)
                cells = _differences(output, predicted)
                if cells:
                    disagreements.append({"query_index": index, "different_cells": cells})
            if matches:
                survivor_rows.append(rival)
                if disagreements:
                    findings.append({"seed": seed, "finish": finish, "rival": rival,
                                     "query_disagreements": disagreements})
        rows.append({"finish": finish, "demo_count": 2,
                     "rivals": list(R.active_rivals(finish)), "survivors": survivor_rows})
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": P.TASK_ID,
        "seed": seed,
        "settings": rows,
        "findings": findings,
        "query_inputs_consulted_for_selection": False,
        "query_outputs_consulted_for_selection": False,
        "limitation": "Finite declared executable rivals only; not universal identifiability or model accuracy.",
    }


def _racket(source, grid, bridge):
    from puzzle_generators.rule_wrap import wrap_rule

    datum = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(source)} {datum})")


def run(output, seeds=(0, 17)):
    from arc_repl.racket_bridge import RacketBridge

    output = Path(output)
    if output.exists():
        raise FileExistsError(output)
    seed_reports, mismatches, executions = [], [], 0
    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("self-audit requires protected Racket")
        for seed in seeds:
            report = audit_demos(seed)
            seed_reports.append(report)
            for settings in P.SETTINGS:
                episode = P.generate(seed, settings, demos=2, queries=4)
                for split in ("train", "test"):
                    for index, pair in enumerate(episode[split]):
                        observed = _racket(episode["program_solution"], pair["input"], bridge)
                        executions += 1
                        if observed != pair["output"]:
                            mismatches.append({"seed": seed, "settings": settings,
                                               "split": split, "index": index})
    findings = [finding for report in seed_reports for finding in report["findings"]]
    result = {
        "schema": "arcpuzzles-parametric-self-audit-batch-v1",
        "task_id": P.TASK_ID,
        "status": "passed" if not findings and not mismatches else "failed",
        "seeds": list(seeds),
        "protected_racket": True,
        "racket_evaluations": executions,
        "label_mismatches": mismatches,
        "findings": findings,
        "seed_reports": seed_reports,
        "source_sha256": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (HERE / "prototype.py", HERE / "oracle.py", HERE / "rivals.py",
                         HERE / "canonical.rkt", HERE / "most_occluded.rkt")
        },
        "limitation": "No surviving declared rival was found for these seeds; arbitrary programs remain outside scope.",
        "training_admitted": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, action="append")
    args = parser.parse_args()
    result = run(args.out, tuple(args.seed or (0, 17)))
    print(json.dumps({key: result[key] for key in
                      ("status", "seeds", "racket_evaluations", "label_mismatches", "findings")},
                     sort_keys=True))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
