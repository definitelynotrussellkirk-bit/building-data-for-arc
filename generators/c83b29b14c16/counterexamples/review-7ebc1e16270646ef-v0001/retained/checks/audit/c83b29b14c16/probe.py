"""Reproduce the even-endpoint-distance shortcut in c83b29b14c16."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import importlib.util
import sys

TASK_ID = "c83b29b14c16"
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


def positions(grid):
    out = {}
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                out.setdefault(value, []).append((r, c))
    return out


def distance(cells):
    if len(cells) != 2:
        return None
    (r1, c1), (r2, c2) = cells
    if r1 == r2:
        return abs(c2 - c1)
    if c1 == c2:
        return abs(r2 - r1)
    return None


def even_distance_rival(grid):
    out = deepcopy(grid)
    for color, cells in positions(grid).items():
        d = distance(cells)
        if d is None or d % 2:
            continue
        (r1, c1), (r2, c2) = cells
        if r1 == r2:
            for c in range(min(c1, c2), max(c1, c2) + 1):
                out[r1][c] = color
        else:
            for r in range(min(r1, r2), max(r1, r2) + 1):
                out[r][c1] = color
    return out


def main():
    generated_matches = 0
    generated_total = 0
    generated_errors = []
    distance_hist = Counter()
    unique = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(200):
            seed = 730_000 + band_index * 10_000 + index
            grid = gen.generate(seed, index, difficulty=band)
            issues = gen.self_check(grid)
            if issues:
                generated_errors.append({"band": band, "seed": seed, "sample_index": index, "issues": issues})
                continue
            for cells in positions(grid).values():
                d = distance(cells)
                if d is not None:
                    distance_hist[str(d)] += 1
            expected = gen.rule_mirror(grid)
            generated_matches += even_distance_rival(grid) == expected
            generated_total += 1
            unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())

    canonical_rows = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    canonical_checks = []
    for pair in canonical_rows:
        pred = even_distance_rival(pair["input"])
        canonical_checks.append({
            "variant": pair["variant"],
            "split": pair["split"],
            "pair_index": pair["pair_index"],
            "matches": pred == pair["output"],
            "aligned_pair_distances": sorted(
                d for cells in positions(pair["input"]).values()
                if (d := distance(cells)) is not None
            ),
            "input": pair["input"],
            "authoritative_output": pair["output"],
            "rival_output": pred,
        })
    first_counterexample = next(row for row in canonical_checks if not row["matches"])

    source = ROOT / f"generators/{TASK_ID}/generator.py"
    report = {
        "schema": "arc-audit-even-distance-shortcut-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "rule_hash": gen.RULE_HASH,
        "rival": "Connect exact-two aligned colors only when endpoint distance is even.",
        "generated": {
            "draws": generated_total,
            "matches": generated_matches,
            "mismatches": generated_total - generated_matches,
            "self_check_errors": generated_errors,
            "unique_inputs": len(unique),
            "aligned_endpoint_distance_histogram": dict(sorted(distance_hist.items())),
        },
        "canonical": {
            "pairs": len(canonical_checks),
            "matches": sum(row["matches"] for row in canonical_checks),
            "checks": canonical_checks,
        },
        "counterexample": first_counterexample,
        "finding": (
            "The production sampler emits aligned endpoint distances 2 and 4 only. "
            "The even-distance rival matched every sampled generated label but fails a labeled "
            "canonical input containing an aligned distance-3 pair."
        ),
    }
    out = HERE / "even_distance_shortcut.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "out": str(out),
        "generated_matches": f"{generated_matches}/{generated_total}",
        "distance_histogram": report["generated"]["aligned_endpoint_distance_histogram"],
        "canonical_matches": f"{report['canonical']['matches']}/{len(canonical_checks)}",
        "counterexample": {k:first_counterexample[k] for k in ("split", "pair_index", "aligned_pair_distances")},
    }, indent=2))


if __name__ == "__main__":
    main()
