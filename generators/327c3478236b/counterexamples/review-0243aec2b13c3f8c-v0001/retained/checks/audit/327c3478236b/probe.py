from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs

TASK = "327c3478236b"
ROOT = Path(__file__).resolve().parents[3] / "repo"
GEN_PATH = ROOT / "generators" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location(f"audit_{TASK}", GEN_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)


def geometry(grid):
    h, w = len(grid), len(grid[0])
    src = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3)
    dst = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 4)
    template = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2]
    vector = (dst[0] - src[0], dst[1] - src[1])
    translated = [(r + vector[0], c + vector[1]) for r, c in template]
    in_bounds = [(r, c) for r, c in translated if 0 <= r < h and 0 <= c < w]
    out_of_bounds = [(r, c) for r, c in translated if not (0 <= r < h and 0 <= c < w)]
    return {
        "src": list(src),
        "dst": list(dst),
        "vector": list(vector),
        "template_cells": [list(cell) for cell in template],
        "translated_cells": [list(cell) for cell in translated],
        "in_bounds": [list(cell) for cell in in_bounds],
        "out_of_bounds": [list(cell) for cell in out_of_bounds],
    }


def minimal_shift_full_copy(grid):
    h, w = len(grid), len(grid[0])
    info = geometry(grid)
    dst = tuple(info["dst"])
    translated = [tuple(cell) for cell in info["translated_cells"]]
    rows = [r for r, _ in translated]
    cols = [c for _, c in translated]
    shift_r = max(0, -min(rows)) + min(0, h - 1 - max(rows))
    shift_c = max(0, -min(cols)) + min(0, w - 1 - max(cols))
    output = [[0] * w for _ in range(h)]
    for r, c in translated:
        output[r + shift_r][c + shift_c] = 8
    output[dst[0]][dst[1]] = 4
    return output


canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
canonical_rows = []
for index, pair in enumerate(canonical):
    rival = minimal_shift_full_copy(pair["input"])
    canonical_rows.append({
        "index": index,
        "split": pair.get("split"),
        "input": pair["input"],
        "authority_output": pair["output"],
        "rival_output": rival,
        "rival_matches": rival == pair["output"],
        "geometry": geometry(pair["input"]),
    })

exact_input = GEN.generate(0, 0, difficulty=None)
exact_self_check = GEN.self_check(exact_input, difficulty=None)

bands = ("easy", "medium", "hard")
grids = []
metadata = []
for band in bands:
    for sample_index in range(100):
        grid = GEN.generate(20261012, sample_index, difficulty=band)
        info = geometry(grid)
        grids.append(grid)
        metadata.append({
            "difficulty": band,
            "sample_index": sample_index,
            "self_check": GEN.self_check(grid, difficulty=band),
            "geometry": info,
        })

catalog = Catalog(ROOT)
all_inputs = [exact_input] + grids
results = []
rule_hash_matches_catalog = True
executed_rule_hash = None
rule_text_sha256 = None
for start in range(0, len(all_inputs), 64):
    receipt = catalog.apply(TASK, all_inputs[start:start + 64], reference="canonical", timeout=900)
    rule_hash_matches_catalog = rule_hash_matches_catalog and receipt["rule_hash_matches_catalog"]
    executed_rule_hash = executed_rule_hash or receipt.get("executed_rule_hash")
    rule_text_sha256 = rule_text_sha256 or receipt.get("rule_text_sha256")
    results.extend(receipt["results"])
assert rule_hash_matches_catalog
assert len(results) == len(all_inputs)
exact_result = results[0]
census_results = results[1:]

census_rows = []
for grid, meta, result in zip(grids, metadata, census_results):
    info = meta["geometry"]
    authority = result["output"]
    input_template_count = len(info["template_cells"])
    authority_eights = sum(value == 8 for row in authority for value in row)
    census_rows.append({
        "difficulty": meta["difficulty"],
        "sample_index": meta["sample_index"],
        "self_check_passes": meta["self_check"] == [],
        "valid_output": result["valid_output"],
        "error": result["error"],
        "template_cells": input_template_count,
        "out_of_bounds_cells": len(info["out_of_bounds"]),
        "has_clipping": bool(info["out_of_bounds"]),
        "authority_color8_cells": authority_eights,
        "authority_drops_cells": authority_eights < input_template_count,
    })

summary = {
    "draws": len(census_rows),
    "valid_outputs": sum(row["valid_output"] and row["error"] is None for row in census_rows),
    "self_check_passes": sum(row["self_check_passes"] for row in census_rows),
    "draws_with_out_of_bounds_translation": sum(row["has_clipping"] for row in census_rows),
    "draws_where_authority_drops_template_cells": sum(row["authority_drops_cells"] for row in census_rows),
    "template_cells": sum(row["template_cells"] for row in census_rows),
    "out_of_bounds_template_cells": sum(row["out_of_bounds_cells"] for row in census_rows),
    "per_band": {
        band: {
            "draws": sum(row["difficulty"] == band for row in census_rows),
            "draws_with_out_of_bounds_translation": sum(
                row["difficulty"] == band and row["has_clipping"] for row in census_rows
            ),
            "out_of_bounds_template_cells": sum(
                row["out_of_bounds_cells"] for row in census_rows if row["difficulty"] == band
            ),
        }
        for band in bands
    },
}

exact_info = geometry(exact_input)
exact_authority = exact_result["output"]
exact_rival = minimal_shift_full_copy(exact_input)
report = {
    "schema": "arcpuzzles-audit-probe-v1",
    "task_id": TASK,
    "source_sha256": hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    "generator_version": GEN.VERSION,
    "rule_hash_matches_catalog": rule_hash_matches_catalog,
    "executed_rule_hash": executed_rule_hash,
    "rule_text_sha256": rule_text_sha256,
    "finding": (
        "Ordinary generator outputs can translate every template cell outside the canvas even though "
        "the declared invariant says translated cells are in-bounds. The validator does not inspect "
        "the translated geometry. A minimal-shift full-copy rival fits every labeled canonical pair "
        "but disagrees with the clipping authority on the retained default sample."
    ),
    "canonical": {
        "usable_pairs": len(canonical_rows),
        "rival_fits": sum(row["rival_matches"] for row in canonical_rows),
        "pairs": canonical_rows,
    },
    "exact_reproduction": {
        "seed": 0,
        "sample_index": 0,
        "difficulty": None,
        "input": exact_input,
        "self_check_errors": exact_self_check,
        "geometry": exact_info,
        "authority_valid_output": exact_result["valid_output"],
        "authority_error": exact_result["error"],
        "authority_output": exact_authority,
        "minimal_shift_full_copy_output": exact_rival,
        "authority_color8_cells": sum(value == 8 for row in exact_authority for value in row),
        "rival_color8_cells": sum(value == 8 for row in exact_rival for value in row),
        "outputs_differ": exact_authority != exact_rival,
    },
    "generated_census": summary,
    "prior_retained_audit": (
        "generators/327c3478236b/counterexamples/review-c5fe8719feedc568-v0001/"
        "retained/checks/audit/327c3478236b/counterexample.json"
    ),
}
path = Path(__file__).with_name("clipping_repro.json")
path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "canonical_rival_fit": [report["canonical"]["rival_fits"], report["canonical"]["usable_pairs"]],
    "exact_self_check_errors": exact_self_check,
    "exact_out_of_bounds": len(exact_info["out_of_bounds"]),
    "exact_outputs_differ": exact_authority != exact_rival,
    "census": summary,
}, indent=2))
print(path)
