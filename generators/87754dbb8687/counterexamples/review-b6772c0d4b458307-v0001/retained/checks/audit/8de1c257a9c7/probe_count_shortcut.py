"""Findings-only, source-bound audit of the finite cyan-template family.

Run from the outer extraction with the command retained in commands.json.
All audit outputs stay beside this script. No target sources are modified.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK = "8de1c257a9c7"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
SEEDS = (0, 1, 2, 3, 50000, 50001, 50002, 50003)
BANDS = ("easy", "medium", "hard")

# This rival inspects only the number of cyan cells and the red destinations.
# It never reads the green position or any cyan coordinate. Distinct counts
# identify every template in the issued generator's finite bank.
COUNT_OFFSETS = {
    4: ((-1, 0), (0, -1), (0, 1), (1, 0)),
    6: ((-2, 0), (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 2)),
    8: ((-2, -1), (-1, -1), (-1, 0), (0, -1), (1, -1), (1, 0), (1, 1), (2, 1)),
    9: ((-2, -1), (-2, 1), (-1, -2), (-1, -1), (-1, 1), (-1, 2), (0, -1), (0, 1), (1, 0)),
    10: ((-2, 0), (-1, -1), (-1, 0), (-1, 1), (0, -2), (0, 2), (1, -1), (1, 0), (1, 1), (2, 0)),
    14: ((-3, 0), (-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2), (-1, -2), (-1, -1), (-1, 1), (-1, 2), (0, -2), (0, -1), (0, 1), (0, 2)),
}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def save(name, value):
    (HERE / name).write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")


def positions(grid, color):
    return [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]


def stamp(grid, offsets):
    h, w = len(grid), len(grid[0])
    output = [[0] * w for _ in range(h)]
    for rr, rc in positions(grid, 2):
        for dr, dc in offsets:
            nr, nc = rr + dr, rc + dc
            if 0 <= nr < h and 0 <= nc < w:
                output[nr][nc] = 8
    return output


def count_only_rival(grid):
    count = sum(value == 8 for row in grid for value in row)
    return stamp(grid, COUNT_OFFSETS[count])


def independent_rule(grid):
    greens = positions(grid, 3)
    if len(greens) != 1:
        raise ValueError("independent oracle requires one green anchor")
    gr, gc = greens[0]
    return stamp(grid, [(r - gr, c - gc) for r, c in positions(grid, 8)])


def handmade_hook(mirror):
    grid = [[0] * 13 for _ in range(13)]
    grid[6][6] = 3
    for dr, dc in COUNT_OFFSETS[6]:
        grid[6 + dr][6 + (-dc if mirror else dc)] = 8
    for r, c in ((3, 3), (9, 9)):
        grid[r][c] = 2
    return grid


def main():
    started = utc()
    generator, source, source_hash = load_selected_generator(TASK, root=ROOT)
    catalog = Catalog(ROOT)
    test_paths = [
        f"generators/{TASK}/tests/test_generator_{TASK}.py",
        f"generators/{TASK}/tests/test_public_scalar_contract_{TASK}.py",
        f"generators/{TASK}/tests/test_control_probe_{TASK}.py",
    ]
    test_argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *test_paths]
    t0 = time.monotonic()
    test_run = subprocess.run(test_argv, cwd=ROOT, text=True, capture_output=True,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    (HERE / "focused-tests.log").write_text(test_run.stdout + test_run.stderr)
    test_receipt = {"argv": test_argv, "cwd": str(ROOT), "exit_code": test_run.returncode,
                    "elapsed_seconds": round(time.monotonic() - t0, 3),
                    "source_sha256": source_hash, "log": "focused-tests.log"}
    save("focused-tests.receipt.json", test_receipt)

    canonical = canonical_pairs(TASK, root=ROOT)
    records, all_inputs = [], []
    failures = []
    for index, pair in enumerate(canonical):
        grid = pair["input"]
        checks = {"independent_equals_published": independent_rule(grid) == pair["output"],
                  "count_rival_equals_published": count_only_rival(grid) == pair["output"],
                  "generator_self_check": generator.self_check(grid)}
        record = {"kind": "canonical", "record_index": index,
                  **{key: pair[key] for key in ("variant", "split", "pair_index")},
                  "input": grid, "expected_output": pair["output"], "checks": checks}
        if not checks["independent_equals_published"] or not checks["count_rival_equals_published"] or checks["generator_self_check"]:
            failures.append(record)
        records.append(record)

    default_grids = {}
    for seed, band, index in product(SEEDS, BANDS, range(8)):
        grid = generator.generate(seed, index, difficulty=band)
        expected = independent_rule(grid)
        checks = {"generator_self_check": generator.self_check(grid),
                  "generator_mirror_equals_independent": generator.rule_mirror(grid) == expected,
                  "count_rival_equals_independent": count_only_rival(grid) == expected}
        record = {"kind": "default", "seed": seed, "difficulty": band, "sample_index": index,
                  "input_sha256": digest(grid), "output_sha256": digest(expected), "checks": checks}
        if checks["generator_self_check"] or not checks["generator_mirror_equals_independent"] or not checks["count_rival_equals_independent"]:
            failures.append(record)
        default_grids[seed, band, index] = grid
        records.append(record)
        all_inputs.append(grid)

    control_records = []
    for h, w, template, n_reds in product((10, 22), (10, 22), generator._TEMPLATES, (1, 5)):
        controls = {"grid_h": h, "grid_w": w, "template": template, "n_reds": n_reds}
        try:
            grid = generator.generate(77, 1, difficulty="hard", **controls)
            expected = independent_rule(grid)
            actual = generator.observe_overrides(grid)
            record = {"kind": "exact_controls", "seed": 77, "sample_index": 1,
                      "difficulty": "hard", "overrides": controls, "observed": actual,
                      "input_sha256": digest(grid), "output_sha256": digest(expected),
                      "count_rival_equals_independent": count_only_rival(grid) == expected,
                      "generator_self_check": generator.self_check(grid)}
            if actual != controls or record["generator_self_check"] or not record["count_rival_equals_independent"]:
                failures.append(record)
        except Exception as exc:
            record = {"kind": "exact_controls", "overrides": controls,
                      "exception": type(exc).__name__, "message": str(exc)}
            failures.append(record)
        control_records.append(record)

    # The eight stored slots form a cyclic semantic schedule. This bounded
    # check uses those exact stored inputs; it does not claim production draws
    # from sample indices 8+ are byte-identical to the stored slots.
    rotations = []
    for seed, band, start in product(SEEDS, BANDS, range(8)):
        pairs = [{"input": default_grids[seed, band, (start + k) % 8],
                  "output": independent_rule(default_grids[seed, band, (start + k) % 8])}
                 for k in range(5)]
        for query in range(5):
            demos = [pair for i, pair in enumerate(pairs) if i != query]
            survivors = []
            rival_errors = []
            for name, rival in generator.LESSON_COMPETITORS.items():
                try:
                    if all(rival(pair["input"]) == pair["output"] for pair in demos):
                        survivors.append(name)
                except Exception as exc:
                    rival_errors.append({"rival": name, "exception": type(exc).__name__, "message": str(exc)})
            count_survives = all(count_only_rival(pair["input"]) == pair["output"] for pair in demos)
            record = {"seed": seed, "difficulty": band, "cyclic_start": start, "query_index": query,
                      "declared_rival_survivors": survivors, "declared_rival_errors": rival_errors,
                      "count_lookup_rival_survives": count_survives}
            rotations.append(record)

    # Execute the canonical Racket source on all eight ledger records, every
    # slot in every band for seed 0 (24 grids), and a same-histogram pair that
    # exposes the count shortcut. 34 <= Catalog.apply's 64-grid limit.
    witness_inputs = [handmade_hook(False), handmade_hook(True)]
    executed_inputs = [p["input"] for p in canonical]
    executed_inputs.extend(default_grids[0, band, index] for band, index in product(BANDS, range(8)))
    executed_inputs.extend(witness_inputs)
    applied = catalog.apply(TASK, executed_inputs, reference="canonical", check_generator_domain=True, timeout=120)
    save("canonical-racket-execution.json", applied)
    racket_mismatches = []
    for i, (grid, row) in enumerate(zip(executed_inputs, applied["results"], strict=True)):
        expected = independent_rule(grid)
        if row["output"] != expected:
            racket_mismatches.append({"input_index": i, "actual": row["output"], "expected": expected})
    witnesses = []
    for i, grid in enumerate(witness_inputs):
        actual = applied["results"][-2 + i]["output"]
        rival = count_only_rival(grid)
        witnesses.append({"name": "hook" if i == 0 else "reflected_hook",
                          "input": grid, "input_sha256": digest(grid), "cyan_count": 6,
                          "color_histogram": dict(sorted(Counter(v for row in grid for v in row).items())),
                          "generator_self_check": generator.self_check(grid),
                          "canonical_racket_output": actual, "count_lookup_rival_output": rival,
                          "rival_different_cells": sum(a != b for ra, rb in zip(actual, rival) for a, b in zip(ra, rb))})
    save("same-count-witness.json", {"status": "reproduced_distribution_shortcut",
        "qualification": "The reflected hook is valid for the canonical offset-stamping rule, but lies outside the generator's explicitly declared finite template bank.",
        "same_color_histogram": witnesses[0]["color_histogram"] == witnesses[1]["color_histogram"],
        "source_sha256": source_hash, "executed_rule_hash": applied["executed_rule_hash"], "witnesses": witnesses})

    end_hash = sha(source)
    summary = {
        "schema": "independent-generator-audit-v1", "task_id": TASK,
        "status": "findings_only", "started_utc": started, "finished_utc": utc(),
        "source_sha256": source_hash, "source_sha256_after": end_hash,
        "source_unchanged": source_hash == end_hash,
        "canonical_rule_hash": generator.RULE_HASH, "executed_rule_hash": applied["executed_rule_hash"],
        "seed_ranges": [[0, 3], [50000, 50003]], "default_seeds": list(SEEDS), "bands": list(BANDS),
        "canonical_pairs": len(canonical), "canonical_unique_inputs": len({digest(p["input"]) for p in canonical}),
        "default_inputs": len(default_grids), "exact_control_cases": len(control_records),
        "cyclic_lessons": len(SEEDS) * len(BANDS) * 8, "query_rotations": len(rotations),
        "rotations_with_declared_rival_survivor": sum(bool(r["declared_rival_survivors"]) for r in rotations),
        "rotations_with_declared_rival_error": sum(bool(r["declared_rival_errors"]) for r in rotations),
        "rotations_with_count_lookup_survivor": sum(r["count_lookup_rival_survives"] for r in rotations),
        "racket_executions": len(executed_inputs), "racket_mismatches": racket_mismatches,
        "focused_tests": test_receipt, "probe_failures": failures,
        "template_counts": {name: len(offsets) for name, offsets in generator._TEMPLATES.items()},
        "findings": [{"classification": "reproduced_shortcut_and_domain_question", "severity": "medium",
            "summary": "Distinct cyan cardinalities identify every finite template. A count-only lookup ignores green position and cyan geometry while matching all generated support.",
            "correctness_qualification": "No wrong generated label found. The distinguishing reflected template is excluded by the current declared finite-bank domain.",
            "suggested_change": "Consider adding at least two same-cardinality, geometrically distinct templates and a count-lookup rival to the lesson checks; preserve full-fit and overlap witnesses.",
            "witness": "same-count-witness.json"}],
        "limits": ["Findings-only audit; no target source or authority edits.",
            "Finite generation probes do not establish universal model performance or absence of other shortcuts.",
            "Count aliasing follows from the six unique template cardinalities, not just the sampled seeds.",
            "All rotations use four demonstrations and one query from five cyclic stored slots.",
            "Prototype code was not audited or modified in this target audit.",
            "Only public canonical authoring examples and public rule execution were used; no solve labels were inspected."]}
    save("probe-records.json", {"default_and_canonical": records, "exact_controls": control_records, "rotations": rotations})
    save("summary.json", summary)
    commands = [{"purpose": "Independent focused tests and source-bound shortcut audit",
        "cwd": "outer extraction directory",
        "argv": ["WORK/.venv-review/bin/python", "review.py", "run", "env", "PYTHONDONTWRITEBYTECODE=1",
                 "../.venv-review/bin/python", "../checks/audit/8de1c257a9c7/probe_count_shortcut.py"],
        "exit_code": 0 if not failures and not racket_mismatches and test_run.returncode == 0 else 1,
        "generator_sha256": source_hash, "probe_sha256": sha(__file__),
        "evidence": ["WORK/checks/audit/8de1c257a9c7/summary.json", "WORK/checks/audit/8de1c257a9c7/canonical-racket-execution.json",
                     "WORK/checks/audit/8de1c257a9c7/same-count-witness.json", "WORK/checks/audit/8de1c257a9c7/focused-tests.log"]},
        {"purpose": "Nested focused pytest invocation", **test_receipt}]
    save("commands.json", commands)
    print(json.dumps({key: summary[key] for key in ("source_sha256", "source_unchanged", "canonical_pairs", "default_inputs", "exact_control_cases", "query_rotations", "rotations_with_declared_rival_survivor", "rotations_with_declared_rival_error", "rotations_with_count_lookup_survivor", "racket_executions", "racket_mismatches", "probe_failures")}, indent=2))
    if failures or racket_mismatches or test_run.returncode or source_hash != end_hash:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
