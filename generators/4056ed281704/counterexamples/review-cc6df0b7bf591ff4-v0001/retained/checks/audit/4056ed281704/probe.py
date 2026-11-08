#!/usr/bin/env python3
"""Bounded public-helper audit of 4056ed281704; no Racket execution."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
import sys

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK = "4056ed281704"
GEN, SOURCE, SOURCE_SHA = load_selected_generator(TASK, root=ROOT)

def sha(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()

def write_json(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")

def parity(grid):
    h, w = len(grid), len(grid[0])
    return [[0 if r % 2 == 1 and c % 2 == 1 else 1 for c in range(w)] for r in range(h)]

def square_by_height(grid):
    h = len(grid)
    return [[0 if r % 2 == 1 and c % 2 == 1 else 1 for c in range(h)] for r in range(h)]

def closed_border_lattice(grid):
    output = parity(grid)
    h, w = len(grid), len(grid[0])
    for r in range(h):
        output[r][0] = output[r][w - 1] = 1
    for c in range(w):
        output[0][c] = output[h - 1][c] = 1
    return output

rivals = {"square_by_height": square_by_height, "closed_border_lattice": closed_border_lattice}
canonical = canonical_pairs(TASK, root=ROOT)
assert len(canonical) == 4, len(canonical)
canonical_checks = []
for pair in canonical:
    expected = parity(pair["input"])
    fits = {name: fn(pair["input"]) == pair["output"] for name, fn in rivals.items()}
    assert expected == pair["output"]
    assert all(fits.values())
    canonical_checks.append({
        "variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
        "shape": [len(pair["input"]), len(pair["input"][0])],
        "input_sha256": sha(pair["input"]), "output_sha256": sha(pair["output"]),
        "formula_matches": True, "rival_fits": fits,
    })

records = []
state = random.getstate()
chosen = None
for seed in range(16):
    grid = GEN.generate(seed, 0, difficulty=None)
    normalize_grid(grid)
    errors = GEN.self_check(grid)
    h, w = len(grid), len(grid[0])
    records.append({
        "kind": "bounded_default_draw", "call": {"seed": seed, "sample_index": 0, "difficulty": None},
        "shape": [h, w], "input_sha256": sha(grid), "self_check": errors,
    })
    assert errors == [], records[-1]
    if h != w and (h % 2 == 0 or w % 2 == 0):
        chosen = (seed, grid)
        break
assert chosen is not None, "No rectangular/even witness in the bounded 16-seed search"
seed, grid = chosen
assert GEN.generate(seed, 0, difficulty=None) == grid
base_sha = sha(grid)
controls = {}
for side in (5, 13):
    actual = GEN.generate(seed, 0, difficulty=None, side=side)
    errors = GEN.self_check(actual)
    controls[f"side_{side}"] = {
        "call": {"seed": seed, "sample_index": 0, "difficulty": None, "side": side},
        "advertised_legal_value": str(side) in GEN.AXES["side"]["valid"].split("|"),
        "shape": [len(actual), len(actual[0])],
        "self_check": errors, "input_sha256": sha(actual),
        "equals_unoverridden_draw": actual == grid,
        "honors_requested_square_side": len(actual) == side and len(actual[0]) == side,
    }
assert all(row["advertised_legal_value"] and row["self_check"] == [] for row in controls.values())
assert all(row["equals_unoverridden_draw"] for row in controls.values())
assert not all(row["honors_requested_square_side"] for row in controls.values())

texture_controls = {}
for texture in GEN.HELPFUL_TEXTURES:
    actual = GEN.generate(seed, 0, difficulty=None, texture=texture)
    texture_controls[texture] = {
        "call": {"seed": seed, "sample_index": 0, "difficulty": None, "texture": texture},
        "shape": [len(actual), len(actual[0])], "input_sha256": sha(actual),
        "self_check": GEN.self_check(actual),
        "equals_unoverridden_draw": actual == grid,
    }
assert len(texture_controls) == 5
assert all(row["equals_unoverridden_draw"] and row["self_check"] == [] for row in texture_controls.values())
assert random.getstate() == state

selected_row = []
with canonical_path(ROOT).open() as stream:
    for line in stream:
        if line.strip():
            row = json.loads(line)
            if row.get("task_id") == TASK:
                selected_row.append(row)
assert len(selected_row) == 1
program = selected_row[0]["program_solution"]
program_sha = hashlib.sha256(program.encode()).hexdigest()
rule_hash = hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]
with (HERE / "canonical-program.rkt").open("x") as stream:
    stream.write(program)
write_json("input.json", {"input": grid})
write_json("python_formula_output.json", {
    "label": "diagnostic Python evaluation of the selected formula; pending Racket confirmation",
    "input_sha256": base_sha, "output": parity(grid),
})
write_json("rival_outputs.json", {
    "input_sha256": base_sha,
    "rivals": {
        name: {"description": (
            "Assume output width equals input height, as in every canonical odd-square example."
            if name == "square_by_height" else
            "Make a parity lattice but force every perimeter cell to 1, as in every canonical odd-square example."
        ), "output": fn(grid), "canonical_pairs_fit": 4}
        for name, fn in rivals.items()
    },
})
write_json("probe.json", {
    "task_id": TASK, "status": "python_probe_complete_racket_confirmation_pending",
    "source": str(SOURCE.relative_to(ROOT)), "generator_sha256": SOURCE_SHA,
    "generator_version": GEN.VERSION, "canonical_program_sha256": program_sha,
    "canonical_normalized_rule_hash": rule_hash,
    "canonical_checks": canonical_checks,
    "scope": {
        "maximum_default_seed_search": 16,
        "actual_default_draws": len(records),
        "settings": "sample_index=0; difficulty=None",
        "side_override_controls": 2,
        "helpful_texture_controls": 5,
        "rivals": list(rivals),
        "no_runtime_execution": True,
    },
    "default_draws": records,
    "selected_input": {
        "call": {"seed": seed, "sample_index": 0, "difficulty": None},
        "shape": [len(grid), len(grid[0])], "input_sha256": base_sha,
        "self_check": GEN.self_check(grid),
        "all_literal_arc_colors": all(type(v) is int and 0 <= v <= 9 for row in grid for v in row),
        "colors": dict(Counter(v for row in grid for v in row)),
        "lawfulness_basis": "Generated by selected source; normalized by public normalize_grid; accepted by selected self_check. The source's odd-square metadata is stale relative to its explicit rectangular draw implementation.",
    },
    "side_override_controls": controls,
    "helpful_texture_controls": texture_controls,
    "findings": [
        {"id": "ignored_side_axis", "classification": "public_override_contract",
         "status": "confirmed_python",
         "source_lines": [31, 39, 56, 74],
         "details": "Both advertised side=5 and side=13 produce the same unoverridden rectangular grid. The selected implementation never reads the side override."},
        {"id": "dead_helpful_textures", "classification": "public_override_contract_warning",
         "status": "confirmed_python",
         "source_lines": [27, 29, 61, 74],
         "details": "All five advertised HELPFUL_TEXTURES return the byte-identical untextured draw. The only texture dispatch is for DEGENERATE_TEXTURES."},
    ],
    "semantic_conclusion": "No semantic output failure established. Both exploratory canonical-fit rivals are predicted to be refuted by this generator-produced, self-check-accepted input; one canonical Racket application remains pending.",
    "limitations": [
        "Bounded audit, not an exhaustive seed/difficulty battery.",
        "No defect is inferred from a missing or evicted file.",
        "Degenerate structured texture rejection is not reported as a defect because the specification allows diagnostic degenerate branches to fail self_check.",
        "The canonical rule intentionally ignores cell content; input independence is task semantics, not a discovered shortcut.",
    ],
})
print(json.dumps({
    "task_id": TASK, "generator_sha256": SOURCE_SHA,
    "selected_seed": seed, "shape": [len(grid), len(grid[0])],
    "self_check": GEN.self_check(grid), "input_sha256": base_sha,
    "canonical_pairs_checked": len(canonical), "rivals_fitting_all_canonical_pairs": list(rivals),
    "actual_default_draws": len(records), "ignored_side_controls": 2,
    "dead_helpful_texture_controls": len(texture_controls),
    "status": "ready_for_one_racket_apply",
}, sort_keys=True))
