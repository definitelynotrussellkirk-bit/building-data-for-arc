"""Reproduce the never-empty-right-quadrant shortcut in b25434a1b56e."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import importlib.util
import sys

TASK_ID = "b25434a1b56e"
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "repo"
sys.path.insert(0, str(ROOT / "shared/runtime"))

from reviewer_support import canonical_pairs


def load_generator():
    source = ROOT / f"generators/{TASK_ID}/generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{TASK_ID}_generator", source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


gen = load_generator()


def quadrant_values(grid):
    h, w = len(grid), len(grid[0])
    hh, hw = h // 2, w // 2
    bounds = ((0, 0, hh, hw), (0, hw, hh, w), (hh, 0, h, hw), (hh, hw, h, w))
    return [
        [grid[r][c] for r in range(r1, r2) for c in range(c1, c2)]
        for r1, c1, r2, c2 in bounds
    ]


def empty_indices(grid):
    return [i for i, values in enumerate(quadrant_values(grid)) if not any(values)]


def global_mode(grid):
    counts = Counter(value for row in grid for value in row if value)
    return max(counts, key=lambda color: (counts[color], color))


def right_empty_fill_rival(grid):
    out = gen.rule_mirror(grid)
    fill = global_mode(grid)
    for index in empty_indices(grid):
        if index in (1, 3):
            out[index // 2][index % 2] = fill
    return out


def swap_halves(grid):
    half = len(grid[0]) // 2
    return [row[half:] + row[:half] for row in grid]


def main():
    generated_total = 0
    generated_matches = 0
    empty_hist = Counter()
    generated_errors = []
    unique = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(200):
            seed = 810_000 + band_index * 10_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            issues = gen.self_check(grid)
            if issues:
                generated_errors.append({"band": band, "seed": seed, "sample_index": index, "issues": issues})
                continue
            key = ",".join(map(str, empty_indices(grid))) or "none"
            empty_hist[key] += 1
            generated_matches += right_empty_fill_rival(grid) == gen.rule_mirror(grid)
            generated_total += 1
            unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())

    canonical_rows = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_checks = []
    for pair in canonical_rows:
        pred = right_empty_fill_rival(pair["input"])
        canonical_checks.append({
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "empty_quadrants": empty_indices(pair["input"]),
            "matches": pred == pair["output"],
        })

    # sample_index 0 has an empty left quadrant. Horizontal reflection moves it
    # to the corresponding right quadrant while preserving the teaching grammar.
    base = gen.generate(812_345, 0, difficulty="medium")
    counterexample = swap_halves(base)
    issues = gen.self_check(counterexample)
    if issues:
        raise AssertionError(f"constructed counterexample rejected: {issues}")
    intended = gen.rule_mirror(counterexample)
    rival = right_empty_fill_rival(counterexample)
    if intended == rival:
        raise AssertionError("constructed right-empty scene did not refute rival")

    source = ROOT / f"generators/{TASK_ID}/generator.py"
    input_path = HERE / "right_empty_input.json"
    input_path.write_text(json.dumps({"input": counterexample}, indent=2) + "\n")
    report = {
        "schema": "arc-audit-right-empty-shortcut-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "rival": "Use the true quadrant mode except replace an empty right quadrant with the global nonzero mode.",
        "generated": {
            "draws": generated_total,
            "matches": generated_matches,
            "mismatches": generated_total - generated_matches,
            "self_check_errors": generated_errors,
            "unique_inputs": len(unique),
            "empty_quadrant_histogram": dict(sorted(empty_hist.items())),
        },
        "canonical": {
            "pairs": len(canonical_checks),
            "matches": sum(row["matches"] for row in canonical_checks),
            "checks": canonical_checks,
        },
        "counterexample": {
            "construction": "Horizontal half-swap of generated seed 812345, sample_index 0, medium.",
            "self_check": issues,
            "empty_quadrants": empty_indices(counterexample),
            "input": counterexample,
            "python_mirror_output": intended,
            "rival_output": rival,
            "input_file": "right_empty_input.json",
        },
        "finding": (
            "Across the production schedule, empty quadrants occur only at indices 0 or 2. "
            "The rival matches every sampled generated and canonical label but fails a lawful "
            "right-empty scene accepted by self_check."
        ),
    }
    out = HERE / "right_empty_shortcut.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "out": str(out),
        "input": str(input_path),
        "generated_matches": f"{generated_matches}/{generated_total}",
        "empty_histogram": report["generated"]["empty_quadrant_histogram"],
        "canonical_matches": f"{report['canonical']['matches']}/{len(canonical_checks)}",
        "counterexample_empty_quadrants": report["counterexample"]["empty_quadrants"],
    }, indent=2))


if __name__ == "__main__":
    main()
