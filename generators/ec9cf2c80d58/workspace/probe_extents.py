"""Reproduce exact-rule witnesses and audit the finite teaching family.

Run via the packet's review.py run wrapper so src and shared/runtime are on
PYTHONPATH and the selected Racket runtime is available. This is authoring-only
code: it reads canonical labels and must stay closed during visible-only solves.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK = "ec9cf2c80d58"


def load_generator(root):
    source = root / "generators" / TASK / "generator.py"
    if not source.is_file():
        source = root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("band_authoring_probe", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, source


def geometry_census(module):
    """All coordinate choices, using closed-form expected output, not the model."""
    total = 0
    failures = []
    for m in range(7, 11):
        for p, q, k, reflected in itertools.product(range(1, m - 1), range(m),
                                                   range(m), (False, True)):
            grid = [[1] * m + [2] * m for _ in range(m + 1)]
            for r, c in ((p, q), (p + 1, q), (p, m + k)):
                grid[r][c] = 0
            expected = [[1] * m + [2] * m for _ in range(m + 1)]
            for row in expected:
                row[q] = row[m + k] = 0
            expected[p + 1][:m] = [0] * m
            if reflected:
                grid = [row[::-1] for row in grid]
                expected = [row[::-1] for row in expected]
            reasons = module.self_check(grid)
            if module.rule_model(grid) != expected:
                reasons.append("analysis model differs from closed-form output")
            reasons += [f"unrefuted rival: {name}"
                        for name, rival in module.LESSON_COMPETITORS.items()
                        if rival(grid) == expected]
            total += 1
            if reasons:
                failures.append({"m": m, "p": p, "q": q, "k": k,
                                 "reflected": reflected, "reasons": reasons})
    return {"evidence_basis": "Python plus independent closed-form teaching output; not per-grid Racket",
            "m": [7, 8, 9, 10], "p": "1..m-2", "q_and_k": "0..m-1",
            "reflections": [False, True], "total": total,
            "failed": len(failures), "failures": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=17)
    args = parser.parse_args()
    if args.out.exists():
        raise ValueError("choose a new output path; evidence is never overwritten")
    root = find_root(__file__)
    gen, source = load_generator(root)
    canonical = canonical_pairs(TASK, root=root)
    samples = [
        {"kind": "sequential_minimal", "input": [[1, 1, 1], [0, 1, 1], [2, 2, 2], [0, 2, 2]]},
        {"kind": "zero_extent_minimal", "input": [[1, 1, 2, 2], [0, 1, 2, 2], [0, 1, 2, 2]]},
        {"kind": "combined_minimal", "input": [[0, 1, 0, 2], [0, 1, 2, 2], [1, 1, 2, 2]]},
    ]
    samples.extend({"kind": "canonical", **pair} for pair in canonical)
    for difficulty in ("easy", "medium", "hard"):
        for index in range(8):
            samples.append({"kind": "generated", "seed": args.seed,
                            "sample_index": index, "difficulty": difficulty,
                            "input": gen.generate(args.seed, index, difficulty=difficulty)})
    authority = Catalog(root).apply(TASK, [sample["input"] for sample in samples], timeout=180)
    failures = []
    for sample, actual in zip(samples, authority["results"], strict=True):
        sample["racket_output"] = actual["output"]
        sample["self_check"] = gen.self_check(sample["input"])
        sample["analysis_model_matches_racket"] = gen.rule_model(sample["input"]) == actual["output"]
        sample["refuted_rivals"] = [name for name, rival in gen.LESSON_COMPETITORS.items()
                                    if rival(sample["input"]) != actual["output"]]
        if sample["self_check"] or not sample["analysis_model_matches_racket"]:
            failures.append({"sample": len([s for s in samples if "racket_output" in s])-1,
                             "kind": sample["kind"], "self_check": sample["self_check"]})
        if "output" in sample and sample["output"] != actual["output"]:
            failures.append({"kind": "canonical label mismatch", "sample": sample})
    fit = {name: {"passed": sum(rival(pair["input"]) == pair["output"] for pair in canonical),
                  "total": len(canonical)} for name, rival in gen.CANONICAL_SHORTCUTS.items()}
    geometry = geometry_census(gen)
    report = {
        "schema": "ec9cf2c80d58-source-bound-extents-probe-v1",
        "argv": list(sys.argv), "cwd": str(Path.cwd()),
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "canonical_rule_hash": gen.RULE_HASH,
        "racket_input_count": len(samples), "racket_model_mismatches": len(failures),
        "canonical_labeled_pairs": len(canonical),
        "canonical_unique_inputs": len({json.dumps(p["input"]) for p in canonical}),
        "canonical_shortcut_fit": fit,
        "samples": samples, "authority_receipt": authority,
        "teaching_geometry_census": geometry,
        "failures": failures,
        "passed": not failures and geometry["failed"] == 0,
        "limits": "Racket covers the retained samples; geometry enumeration covers listed coordinates and colors 1/2. No universal identifiability claim.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("generator_sha256", "racket_input_count",
        "racket_model_mismatches", "canonical_shortcut_fit", "passed")}))
    print(json.dumps({"teaching_geometries": geometry["total"], "failed": geometry["failed"]}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
