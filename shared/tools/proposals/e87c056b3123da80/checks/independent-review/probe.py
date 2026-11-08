"""Small source-bound probes for the selected af840d59f24c generator.

Run from packet root:
  python3 review.py run python3 ../checks/independent-review/probe.py

This does not load any blind/private solve file or modify selected sources.
Racket is authoritative for every reported output disagreement.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = "af840d59f24c"
OUT = Path(__file__).resolve().parent
ROOT = find_root(__file__)
GEN, SOURCE, DIGEST = load_selected_generator(TASK, root=ROOT)
BASELINE_SHA = "08d52d130454fad7f5911f32affa1ed215c3666c2f7e99e2d3d6715e3514e8a4"
assert DIGEST == BASELINE_SHA, f"probe requires exact original source; found {DIGEST}"

PROBE_PATH = ROOT / f"generators/{TASK}/workspace/reference_probe.py"
spec = importlib.util.spec_from_file_location("independent_reference_probe", PROBE_PATH)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def digest_grid(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def first_seen_template(grid):
    """Assign ranks by fixed first-seen order; never horizontally sort columns."""
    seen = list(dict.fromkeys(c for row in grid for c, value in enumerate(row) if value == 0))
    n = len(seen)
    full = any(all(row[c] == 0 for row in grid) for c in seen)
    if full:
        middle = n // 2
        sequence = [middle] + [i for i in reversed(range(n)) if i != middle]
    else:
        sequence = [n - 1]
        lo, hi = 0, n - 2
        while lo <= hi:
            sequence.append(lo)
            lo += 1
            if lo <= hi:
                sequence.append(hi)
                hi -= 1
    ranks = {c: rank + 1 for c, rank in zip(seen, sequence, strict=True)}
    return [[ranks[c] if value == 0 else value for c, value in enumerate(row)] for row in grid]


def frequency_template(grid):
    """Recognize fixed count signatures, with horizontal ordering only for ties."""
    counts = Counter(c for row in grid for c, value in enumerate(row) if value == 0)
    sparse = {
        4: (2, 4, 3, 1),
        5: (2, 4, 3, 1, 2),
        6: (2, 5, 4, 1, 3, 2),
        7: (2, 5, 4, 1, 3, 2, 4),
        8: (2, 5, 4, 1, 3, 2, 4, 5),
    }
    template = (3, 5, 2, len(grid), 4, 6) if len(grid) in counts.values() else sparse[len(counts)]
    ranks = {}
    for count in set(template):
        columns = sorted(c for c, actual in counts.items() if actual == count)
        expected_ranks = [i + 1 for i, actual in enumerate(template) if actual == count]
        if len(columns) != len(expected_ranks):
            return deepcopy(grid)
        ranks.update(zip(columns, expected_ranks, strict=True))
    return [[ranks[c] if value == 0 else value for c, value in enumerate(row)] for row in grid]


def erase_nonmodal(grid):
    """Rank zero columns, but wrongly paint all preserved cells with modal color."""
    nonzero = Counter(v for row in grid for v in row if v)
    modal = min(nonzero, key=lambda color: (-nonzero[color], color))
    columns = sorted({c for row in grid for c, value in enumerate(row) if value == 0})
    ranks = {c: i + 1 for i, c in enumerate(columns)}
    return [[ranks[c] if value == 0 else modal for c, value in enumerate(row)] for row in grid]


def changes(actual, expected):
    return [[r, c, actual[r][c], expected[r][c]]
            for r in range(len(expected)) for c in range(len(expected[0]))
            if actual[r][c] != expected[r][c]]


records = []
grids = []
for seed in (0, 17, 99173):
    for band in (None, "easy", "medium", "hard"):
        for index, profile in enumerate(GEN.PROFILES):
            grid = GEN.generate(seed, index, difficulty=band, scene_profile=profile)
            records.append({"seed": seed, "sample_index": index, "difficulty": band,
                            "overrides": {"scene_profile": profile}, "input_sha256": digest_grid(grid)})
            grids.append(grid)

canonical = list(canonical_pairs(TASK, root=ROOT, labeled_only=True))
base = GEN.generate(0, 0)
row_swap = deepcopy(base)
row_swap[0], row_swap[1] = row_swap[1], row_swap[0]
columns = sorted({c for row in base for c, value in enumerate(row) if value == 0})
column_swap = deepcopy(base)
for row in column_swap:
    row[columns[0]], row[columns[1]] = row[columns[1]], row[columns[0]]
lesson_grids = [GEN.generate(0, index) for index in range(8)]

all_grids = grids + [pair["input"] for pair in canonical] + [base, row_swap, column_swap] + lesson_grids
racket = probe.racket_outputs(all_grids)
assert len(racket) == len(all_grids)
offset = len(grids)
generated_outputs = racket[:offset]
canonical_outputs = racket[offset:offset + len(canonical)]
offset += len(canonical)
base_out, row_swap_out, column_swap_out = racket[offset:offset + 3]
lesson_outputs = racket[offset + 3:]

for record, grid, expected in zip(records, grids, generated_outputs, strict=True):
    stats = probe.zero_stats(grid)
    record.update({
        "self_check": GEN.self_check(grid),
        "racket_matches_mirror": expected == GEN.rule_mirror(grid),
        "first_seen_template_matches_racket": first_seen_template(grid) == expected,
        "frequency_template_matches_racket": frequency_template(grid) == expected,
        "zero_column_counts": [stats["counts"][c] for c in stats["columns"]],
    })

witnesses = {
    "base_call": {"seed": 0, "sample_index": 0},
    "base": {"input": base, "racket_output": base_out},
    "swap_rows_0_and_1": {
        "input": row_swap, "racket_output": row_swap_out,
        "self_check": GEN.self_check(row_swap), "strict_canonical_like": GEN.strict_canonical_like(row_swap),
        "observed": GEN.observe_overrides(row_swap),
        "first_seen_template_disagreements": changes(first_seen_template(row_swap), row_swap_out),
        "frequency_template_matches_racket": frequency_template(row_swap) == row_swap_out,
        "racket_is_row_swapped_base_output": row_swap_out == [base_out[1], base_out[0], *base_out[2:]],
    },
    "swap_first_two_zero_columns": {
        "columns_swapped": columns[:2], "input": column_swap, "racket_output": column_swap_out,
        "self_check": GEN.self_check(column_swap), "strict_canonical_like": GEN.strict_canonical_like(column_swap),
        "observed": GEN.observe_overrides(column_swap),
        "frequency_template_disagreements": changes(frequency_template(column_swap), column_swap_out),
    },
}

rotation_records = []
for start in range(4):
    pairs = [{"input": lesson_grids[i], "output": lesson_outputs[i]} for i in range(start, start + 5)]
    for held_out in range(5):
        demos = [pair for i, pair in enumerate(pairs) if i != held_out]
        query = pairs[held_out]
        fits = all(erase_nonmodal(pair["input"]) == pair["output"] for pair in demos)
        changed = changes(erase_nonmodal(query["input"]), query["output"])
        rotation_records.append({
            "seed": 0, "window_start": start, "held_out_offset": held_out,
            "query_sample_index": start + held_out,
            "demo_sample_indices": [start + i for i in range(5) if i != held_out],
            "lesson_identifiable_reasons": GEN.lesson_identifiable(demos, query),
            "erase_nonmodal_fits_demos": fits,
            "query_disagreements": changed if fits else [],
        })

scalar_records = []
for key, values in (("seed", (True, 1.0, "1", None)), ("sample_index", (True, 1.0, 1.9, "1", -1))):
    for value in values:
        kwargs = {"seed": 0, "sample_index": 0, key: value}
        try:
            grid = GEN.generate(**kwargs)
        except Exception as exc:
            scalar_records.append({"key": key, "type": type(value).__name__, "repr": repr(value),
                                   "exception": type(exc).__name__, "message": str(exc)})
        else:
            scalar_records.append({"key": key, "type": type(value).__name__, "repr": repr(value),
                                   "accepted": True, "observed": GEN.observe_overrides(grid),
                                   "input_sha256": digest_grid(grid)})

wide = [row + [5] * 7 for row in base]
tall = base + [[5] * len(base[0]) for _ in range(21)]
domain_records = []
for name, grid in (("10x17_append_background_columns", wide), ("31x10_append_background_rows", tall)):
    try:
        observed = GEN.observe_overrides(grid)
    except Exception as exc:
        observed = {"exception": type(exc).__name__, "message": str(exc)}
    domain_records.append({"name": name, "shape": [len(grid), len(grid[0])],
                           "self_check": GEN.self_check(grid),
                           "strict_canonical_like": GEN.strict_canonical_like(grid), "observed": observed})

report = {
    "schema": "af840d59f24c-independent-review-v1",
    "source_path": str(SOURCE), "source_sha256": DIGEST,
    "rule_hash": GEN.RULE_HASH,
    "reference_probe_path": str(PROBE_PATH),
    "reference_probe_sha256": hashlib.sha256(PROBE_PATH.read_bytes()).hexdigest(),
    "command": "python3 review.py run python3 ../checks/independent-review/probe.py",
    "command_cwd": str(ROOT.parents[1]), "python": sys.version,
    "racket_grids_checked": len(all_grids),
    "rivals": {name: {"generated_matches": sum(rival(grid) == expected for grid, expected in zip(grids, generated_outputs)),
                      "canonical_matches": sum(rival(pair["input"]) == expected for pair, expected in zip(canonical, canonical_outputs))}
               for name, rival in (("first_seen_template", first_seen_template), ("frequency_template", frequency_template),
                                   ("erase_nonmodal", erase_nonmodal))},
    "canonical_reference_agreements": [expected == pair["output"] for pair, expected in zip(canonical, canonical_outputs)],
    "generated_cases": records, "witnesses": witnesses,
    "rotations": rotation_records,
    "rotation_witness": {"demos": [{"input": lesson_grids[i], "output": lesson_outputs[i]} for i in (0, 1, 3, 4)],
                         "query": {"input": lesson_grids[2], "output": lesson_outputs[2]}},
    "invalid_scalars": scalar_records, "domain_boundaries": domain_records,
}
(OUT / "baseline_report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"source_sha256": DIGEST, "racket_grids_checked": len(all_grids),
                  "rivals": report["rivals"], "rotated_ambiguities": sum(row["erase_nonmodal_fits_demos"] and bool(row["query_disagreements"]) for row in rotation_records),
                  "rotation_total": len(rotation_records),
                  "first_seen_row_swap_mismatches": len(witnesses["swap_rows_0_and_1"]["first_seen_template_disagreements"]),
                  "frequency_column_swap_mismatches": len(witnesses["swap_first_two_zero_columns"]["frequency_template_disagreements"]),
                  "report": str(OUT / "baseline_report.json")}, indent=2))
