"""Bounded findings-only probes; reference labels come from public apply."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator


TASK = "7d970a1ea99b"
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, SOURCE_HASH = load_selected_generator(TASK, root=ROOT)


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode()).hexdigest()


def conflicts(grid):
    return [{"a": [r, c, grid[r][c]], "b": [c, r, grid[c][r]]}
            for r in range(len(grid)) for c in range(r + 1, len(grid))
            if grid[r][c] and grid[c][r] and grid[r][c] != grid[c][r]]


def shape_summary(grid):
    return {
        "height": len(grid), "width": len(grid[0]),
        "nonzero_cells": sum(value != 0 for row in grid for value in row),
        "nonzero_colors": sorted({value for row in grid for value in row if value}),
        "nonzero_diagonal": sum(grid[r][r] != 0 for r in range(len(grid))),
        "conflicting_pairs": conflicts(grid),
        "self_check_errors": GEN.self_check(grid),
        "input_sha256": digest(grid),
    }


def dump(name, value):
    path = OUT / name
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()
            if line.strip() and json.loads(line).get("task_id") == TASK]
    pairs = canonical_pairs(TASK, root=ROOT)
    rule = rows[0]["program_solution"]
    sources = {
        "generator_sha256": SOURCE_HASH,
        "generator_path": str(SOURCE.relative_to(ROOT)),
        "rule_text_sha256": hashlib.sha256(rule.encode()).hexdigest(),
        "canonical_ledger_sha256": hashlib.sha256(canonical_path(ROOT).read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "review_index_sha256": hashlib.sha256((ROOT / "generators" / TASK / "evidence/review_index.json").read_bytes()).hexdigest(),
        "base_helper_sha256": hashlib.sha256((ROOT / "shared/runtime/puzzle_generators/base.py").read_bytes()).hexdigest(),
        "prior_audit_lead": "review-10afcda5143660c3:v0001",
    }
    sample_counts = {}
    first_by_band = {}
    all_hashes = set()
    for band in ("easy", "medium", "hard"):
        counts = Counter()
        for seed in range(10):
            for index in range(20):
                grid = GEN.generate(seed, index, difficulty=band)
                info = shape_summary(grid)
                counts["draws"] += 1
                counts["self_check_rejections"] += bool(info["self_check_errors"])
                counts["conflicting_transpose_inputs"] += bool(info["conflicting_pairs"])
                counts["nonzero_diagonal_inputs"] += bool(info["nonzero_diagonal"])
                counts["fewer_than_declared_3_distinct_nonzero_colors"] += len(info["nonzero_colors"]) < 3
                all_hashes.add(info["input_sha256"])
                if info["conflicting_pairs"] and band not in first_by_band:
                    first_by_band[band] = {"seed": seed, "sample_index": index, "difficulty": band,
                                           "input": grid, **info}
        sample_counts[band] = dict(counts)

    reproduction = GEN.generate(1, 4, difficulty="easy")
    retained_path = ROOT / "generators" / TASK / "counterexamples/review-10afcda5143660c3-v0001/retained/checks/audit/7d970a1ea99b/input.json"
    retained = json.loads(retained_path.read_text())
    prior_reproduction = {
        "seed": 1, "sample_index": 4, "difficulty": "easy", "overrides": {},
        "matches_retained_counterexample": reproduction == retained,
        "input": reproduction, **shape_summary(reproduction),
    }

    controls = [
        ("legal_side_4", {"side": 4}), ("legal_side_16", {"side": 16}),
        ("legal_side_8", {"side": 8}), ("legal_n_cells_1", {"n_cells": 1}),
        ("legal_n_cells_12", {"n_cells": 12}), ("legal_n_cells_3", {"n_cells": 3}),
        *[(f"palette_{kind}", {"palette_kind": kind}) for kind in GEN.PALETTE_KINDS],
        *[(f"texture_{kind}", {"texture": kind}) for kind in GEN.HELPFUL_TEXTURES],
        ("invalid_palette_kind", {"palette_kind": "not_a_palette"}),
        ("invalid_texture", {"texture": "not_a_texture"}),
        ("invalid_palette_size", {"palette_size": 1}),
        ("invalid_n_distinct_colors", {"n_distinct_colors": 1}),
        ("invalid_position_bias", {"position_bias": "diagonal"}),
        ("invalid_density", {"density": "dense"}),
        ("unknown_axis", {"audit_unknown_axis": 1}),
        ("fractional_side", {"side": 8.9}), ("string_side", {"side": "8"}),
        ("fractional_n_cells", {"n_cells": 3.9}),
    ]
    baseline = GEN.generate(1, 4, difficulty="medium")
    override_results = []
    for name, kwargs in controls:
        row = {"name": name, "seed": 1, "sample_index": 4, "difficulty": "medium", "overrides": kwargs}
        try:
            grid = GEN.generate(1, 4, difficulty="medium", **kwargs)
            row.update(status="returned", input=grid, equal_to_baseline=grid == baseline, **shape_summary(grid))
        except Exception as error:
            row.update(status="raised", error_type=type(error).__name__, error=str(error))
        override_results.append(row)

    degenerates = []
    for name in GEN.DEGENERATE_TEXTURES:
        grid = GEN.generate(1, 4, difficulty="medium", texture=name)
        degenerates.append({"texture": name, "input": grid, **shape_summary(grid)})
    determinism_checks = []
    for band in ("easy", "medium", "hard"):
        for seed in range(10):
            first = GEN.generate(seed, seed, difficulty=band)
            second = GEN.generate(seed, seed, difficulty=band)
            determinism_checks.append({"difficulty": band, "seed": seed, "sample_index": seed, "equal": first == second})
    canonical_checks = [{"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
                         **shape_summary(pair["input"])} for pair in pairs]

    reference_cases = [{"kind": "retained_reproduction", "input": reproduction},
                       *[{"kind": "first_conflict_by_band", "difficulty": band, "input": value["input"]}
                         for band, value in first_by_band.items()],
                       *[{"kind": "canonical", "variant": pair["variant"], "split": pair["split"],
                           "pair_index": pair["pair_index"], "input": pair["input"], "expected_output": pair["output"]}
                         for pair in pairs],
                       *[{"kind": "degenerate", "texture": value["texture"], "input": value["input"]}
                         for value in degenerates]]
    report = {
        "task_id": TASK, "sources": sources, "sampling": {"bands": ["easy", "medium", "hard"],
        "seeds": list(range(10)), "sample_indices": list(range(20)), "total_draws": 600,
        "unique_inputs": len(all_hashes), "counts_by_band": sample_counts},
        "canonical_inputs": canonical_checks, "prior_reproduction": prior_reproduction,
        "first_conflict_by_band": first_by_band,
        "override_baseline": {"input": baseline, **shape_summary(baseline)},
        "override_cases": override_results, "degenerate_cases": degenerates,
        "determinism_checks": determinism_checks,
        "contract_inventory": {key: hasattr(GEN, key) for key in (
            "strict_canonical_like", "SEMANTIC_WITNESSES", "lesson_identifiable", "LESSON_COMPETITORS",
            "SEMANTIC_RIVALS", "CANONICAL_SHORTCUTS", "RULE_HASH")},
        "focused_test_files": [str(path.relative_to(ROOT)) for path in
                               sorted((ROOT / "generators" / TASK / "tests").glob("test*.py"))],
        "limits": "600 deterministic input draws; 30 duplicate-call checks; 24 single-axis probes; three declared degenerates; no exhaustive support or lesson-identifiability claim. Racket labels are checked separately through public apply.",
    }
    dump("probe_report.json", report)
    dump("input.json", reproduction)
    dump("reference_cases.json", reference_cases)
    dump("reference_inputs.json", [case["input"] for case in reference_cases])
    print(json.dumps({"generator_sha256": SOURCE_HASH, "rule_text_sha256": sources["rule_text_sha256"],
                      "counts_by_band": sample_counts, "canonical_pairs": len(pairs),
                      "canonical_diagonal_inputs": sum(row["nonzero_diagonal"] > 0 for row in canonical_checks),
                      "prior_reproduction": prior_reproduction["matches_retained_counterexample"],
                      "override_cases": len(override_results), "reference_cases": len(reference_cases),
                      "determinism_failures": sum(not row["equal"] for row in determinism_checks),
                      "focused_test_files": report["focused_test_files"]}, indent=2))


if __name__ == "__main__":
    main()
