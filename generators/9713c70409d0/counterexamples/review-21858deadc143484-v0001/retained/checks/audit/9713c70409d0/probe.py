#!/usr/bin/env python3
"""Findings-only audit; generator is read through its selected source path.

No private reference runner is imported. Actual reference labels are obtained
separately through the documented arcpuzzles apply CLI.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "9713c70409d0"
HERE = Path(__file__).resolve().parent
REPO = find_root(Path.cwd())
SOURCE = REPO / "generators" / TASK_ID / "generator.py"
spec = importlib.util.spec_from_file_location("audit_selected_generator", SOURCE)
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def digest(data):
    if not isinstance(data, bytes):
        data = json.dumps(data, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(data).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def points(grid):
    by_color = defaultdict(set)
    for row, values in enumerate(grid):
        for col, color in enumerate(values):
            if color:
                by_color[color].add((row, col))
    return dict(by_color)


def row_close(cells):
    occupied = defaultdict(list)
    for row, col in cells:
        occupied[row].append(col)
    return {(row, col) for row, cols in occupied.items()
            for col in range(min(cols), max(cols) + 1)}


def col_close(cells):
    occupied = defaultdict(list)
    for row, col in cells:
        occupied[col].append(row)
    return {(row, col) for col, rows in occupied.items()
            for row in range(min(rows), max(rows) + 1)}


def reverse_order(grid):
    by_color = points(grid)
    colors = sorted(by_color)
    closures = {color: row_close(col_close(cells))
                for color, cells in by_color.items()}
    return [[5 if a == b else (8 if closures[a] & closures[b] else 0)
             for b in colors] for a in colors]


def object_shape(cells):
    rows = defaultdict(list)
    for row, col in cells:
        rows[row].append(col)
    assert len(rows) == 2
    intervals = [set(range(min(cols), max(cols) + 1)) for cols in rows.values()]
    if intervals[0] == intervals[1]:
        return "identical_row_intervals"
    if not intervals[0] & intervals[1]:
        return "disjoint_row_intervals"
    return "partially_overlapping_distinct_row_intervals"


def build_counterexample():
    # Rows 1 and 5 of color 2 have overlapping intervals but no equal endpoints.
    # Row-then-column creates an interior bridge, which intersects color 4.
    # Column-then-row creates only the two original horizontal bars for color 2.
    grid = [[0] * 12 for _ in range(7)]
    endpoints = {
        2: [(1, 1), (1, 5), (5, 3), (5, 7)],
        4: [(2, 4), (2, 6), (4, 4), (4, 6)],
        7: [(0, 9), (0, 10), (1, 9), (1, 10)],
    }
    for color, cells in endpoints.items():
        for row, col in cells:
            assert grid[row][col] == 0
            grid[row][col] = color
    return grid


def main():
    canonical = canonical_pairs(TASK_ID, root=REPO, labeled_only=True)
    ledger_rows = []
    with canonical_path(REPO).open() as handle:
        for line in handle:
            item = json.loads(line)
            if item.get("task_id") == TASK_ID:
                ledger_rows.append(item)
    assert len(ledger_rows) == 1
    program = ledger_rows[0]["program_solution"]
    hashes = {
        "generator_sha256": digest(SOURCE.read_bytes()),
        "catalog_rule_hash": hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12],
        "canonical_program_exact_text_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "canonical_ledger_record_sha256": digest(ledger_rows[0]),
        "canonical_pairs_sha256": digest(canonical),
    }
    canonical_checks = []
    for pair in canonical:
        inp, expected = pair["input"], pair["output"]
        canonical_checks.append({
            "variant": pair["variant"], "split": pair["split"],
            "pair_index": pair["pair_index"],
            "input": inp, "canonical_output": expected,
            "self_check": gen.self_check(inp),
            "reverse_order_output": reverse_order(inp),
            "reverse_order_matches": reverse_order(inp) == expected,
            "mirror_matches": gen.rule_mirror(inp) == expected,
            "declared_canonical_shortcut_matches": {
                name: rival(inp) == expected
                for name, rival in gen.CANONICAL_SHORTCUTS.items()
            },
        })

    draws = []
    profile_counts, shape_counts = Counter(), Counter()
    reverse_matches = 0
    declared_rival_matches = Counter()
    invalid = []
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(80):
            seed = 973000 + band_index * 1000 + sample_index
            inp = gen.generate(seed, sample_index, difficulty=band)
            errors = gen.self_check(inp)
            profile = gen.observe_overrides(inp)["scene_profile"]
            expected = gen.rule_mirror(inp)
            rival_output = reverse_order(inp)
            profile_counts[profile] += 1
            shape_counts.update(object_shape(cells) for cells in points(inp).values())
            reverse_matches += rival_output == expected
            matches = {name: rival(inp) == expected
                       for name, rival in gen.LESSON_COMPETITORS.items()}
            declared_rival_matches.update(name for name, match in matches.items() if match)
            if errors:
                invalid.append({"seed": seed, "sample_index": sample_index,
                                "difficulty": band, "errors": errors})
            draws.append({"seed": seed, "sample_index": sample_index,
                          "difficulty": band, "overrides": {},
                          "profile": profile, "input": inp,
                          "input_sha256": digest(inp),
                          "self_check": errors,
                          "python_mirror_output": expected,
                          "reverse_order_output": rival_output,
                          "reverse_order_matches_python_mirror": rival_output == expected,
                          "declared_rival_matches_python_mirror": matches})

    fixture = build_counterexample()
    fixture_check = gen.self_check(fixture)
    strict_check = gen.strict_canonical_like(fixture)
    expected = gen.rule_mirror(fixture)
    reverse = reverse_order(fixture)
    assert not fixture_check
    assert not strict_check
    assert expected != reverse
    write("input.json", fixture)
    write("rival.json", {"task_id": TASK_ID, **hashes,
                         "rival_name": "column_then_row",
                         "input": fixture,
                         "rival_output": reverse,
                         "python_mirror_output": expected,
                         "self_check": fixture_check,
                         "strict_canonical_like": strict_check,
                         "observed_profile": gen.observe_overrides(fixture),
                         "generated": False,
                         "domain_status": {
                             "documented_endpoint_grammar": True,
                             "documented_signature": True,
                             "mixed_overlap_relations": True,
                             "literal_template_support": False,
                             "explanation": "7x12, 3 colors, each with four endpoints on exactly two rows; contains one overlap and two non-overlaps. Accepted by self_check and strict_canonical_like. It is outside literal fixed templates because one object has distinct, partially overlapping row intervals."
                         }})
    report = {
        "schema": "arcpuzzles-findings-only-audit/1",
        "task_id": TASK_ID,
        "phase": "audit_unchanged_source",
        "version": gen.VERSION,
        **hashes,
        "rival_name": "column_then_row",
        "canonical": canonical_checks,
        "counts": {
            "generated_draws": len(draws),
            "unique_generated_inputs": len({row["input_sha256"] for row in draws}),
            "unique_python_mirror_outputs": len({digest(row["python_mirror_output"]) for row in draws}),
            "valid_generated_draws": len(draws) - len(invalid),
            "reverse_order_matches_python_mirror": reverse_matches,
            "profile_counts": dict(profile_counts),
            "object_shape_counts": dict(shape_counts),
            "declared_rival_matches_python_mirror": {
                name: declared_rival_matches[name] for name in gen.LESSON_COMPETITORS
            },
            "canonical_pairs": len(canonical),
            "canonical_reverse_order_matches": sum(row["reverse_order_matches"] for row in canonical_checks),
        },
        "ranges": [
            {"difficulty": band, "seed_min": 973000 + bi * 1000,
             "seed_max": 973079 + bi * 1000, "sample_index_min": 0,
             "sample_index_max": 79, "denominator": 80,
             "seed_formula": "973000 + band_index*1000 + sample_index",
             "overrides": {}}
            for bi, band in enumerate(("easy", "medium", "hard"))
        ],
        "invalid_draws": invalid,
        "draws": draws,
        "counterexample": {
            "input_path": "checks/audit/9713c70409d0/input.json",
            "rival_path": "checks/audit/9713c70409d0/rival.json",
            "input_sha256": digest(fixture),
            "self_check": fixture_check,
            "strict_canonical_like": strict_check,
            "python_mirror_output": expected,
            "reverse_order_output": reverse,
            "actual_racket_output_status": "pending_public_apply",
        },
        "reference_scope": "Canonical labels are retained authored data. Generated-draw comparisons in this report use the generator Python mirror, not new Racket executions. The counterexample is labeled separately through public CLI apply.",
    }
    write("probe.json", report)
    print(json.dumps({"hashes": hashes, "counts": report["counts"],
                      "counterexample": report["counterexample"]}, indent=2))


if __name__ == "__main__":
    main()
