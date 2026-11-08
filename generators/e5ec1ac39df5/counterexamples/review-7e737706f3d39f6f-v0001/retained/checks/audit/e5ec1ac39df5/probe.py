"""Findings-only, source-bound audit of canonical coverage and dimension controls."""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import sys


HERE = Path(__file__).resolve().parent

# Locate the public helper without relying on a fixed parent depth. This also
# supports the documented WORK/checks/... and WORK/repo sibling layout.
for ancestor in (HERE, *HERE.parents):
    candidates = (ancestor, ancestor / "shared/runtime", ancestor / "repo/shared/runtime")
    helper_dir = next((p for p in candidates if (p / "reviewer_support.py").is_file()), None)
    if helper_dir is not None:
        sys.path.insert(0, str(helper_dir))
        break
else:
    raise RuntimeError("Cannot locate the public reviewer_support helper")

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

ROOT = find_root(__file__)
sys.path.insert(0, str(ROOT / "src"))
from arcpuzzles import Catalog

TASK = "e5ec1ac39df5"
EXPECTED_SOURCE = "9e8fb059476e5ace3bca8092f92a395bca20c549c446e672599f63238a2f84d2"
gen, source, source_hash = load_selected_generator(TASK, root=ROOT)
assert source_hash == EXPECTED_SOURCE, (source_hash, EXPECTED_SOURCE)
from puzzle_generators.base import set_ctx_observer


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha_grid(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def geometry(grid):
    h, w = len(grid), len(grid[0])
    wall_rows = [r for r, row in enumerate(grid) if all(v == 1 for v in row)]
    wall_cols = [c for c in range(w) if all(grid[r][c] == 1 for r in range(h))]
    heights = [b - a - 1 for a, b in zip(wall_rows, wall_rows[1:])]
    widths = [b - a - 1 for a, b in zip(wall_cols, wall_cols[1:])]
    seeds = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 2]
    expected_centers = {
        (ra + 1 + (rb - ra - 1) // 2, ca + 1 + (cb - ca - 1) // 2)
        for ra, rb in zip(wall_rows, wall_rows[1:])
        for ca, cb in zip(wall_cols, wall_cols[1:])
    }
    return {
        "shape": [h, w], "wall_rows": wall_rows, "wall_columns": wall_cols,
        "room_rows": len(heights), "room_columns": len(widths),
        "room_heights": heights, "room_widths": widths,
        "uniform_room_dimensions": bool(heights and widths) and len(set(heights)) == 1 and len(set(widths)) == 1,
        "seed_count": len(seeds), "seed_cells": [list(p) for p in seeds],
        "all_seeds_centered": bool(seeds) and all(p in expected_centers for p in seeds),
        "off_center_seed_cells": [list(p) for p in seeds if p not in expected_centers],
    }


def draw_with_provenance(seed, sample_index, difficulty, overrides):
    observed = []
    set_ctx_observer(observed.append)
    try:
        grid = gen.generate(seed, sample_index, difficulty=difficulty, **overrides)
    finally:
        set_ctx_observer(None)
    assert len(observed) == 1, len(observed)
    ctx = observed[0]
    return {
        "seed": seed, "sample_index": sample_index, "difficulty": difficulty,
        "overrides": overrides, "input": grid, "input_sha256": sha_grid(grid),
        "shape": [len(grid), len(grid[0])],
        "self_check": gen.self_check(grid, difficulty=difficulty),
        "recorded_draws": ctx.recorded_draws(), "overrides_used": ctx.overrides_used(),
    }


canonical = canonical_pairs(TASK, root=ROOT, labeled_only=True)
assert len(canonical) == 3, len(canonical)
canonical_records = []
for pair in canonical:
    canonical_records.append({
        **pair, "input_sha256": sha_grid(pair["input"]),
        "self_check": gen.self_check(pair["input"]),
        "geometry": geometry(pair["input"]),
    })

sample_records = []
sample_inputs = {}
for band in ("easy", "medium", "hard"):
    for seed in range(1, 101):
        grid = gen.generate(seed, seed, difficulty=band)
        record = {
            "difficulty": band, "seed": seed, "sample_index": seed,
            "input_sha256": sha_grid(grid), "geometry": geometry(grid),
            "self_check": gen.self_check(grid, difficulty=band),
        }
        sample_records.append(record)
        sample_inputs[(band, seed)] = grid

sample_summary = {}
for band in ("easy", "medium", "hard", "all"):
    selected = [r for r in sample_records if band == "all" or r["difficulty"] == band]
    sample_summary[band] = {
        "draws": len(selected),
        "unique_inputs": len({r["input_sha256"] for r in selected}),
        "uniform_room_dimensions": sum(r["geometry"]["uniform_room_dimensions"] for r in selected),
        "all_seeds_centered": sum(r["geometry"]["all_seeds_centered"] for r in selected),
        "self_check_accepted": sum(not r["self_check"] for r in selected),
        "shape_counts": dict(sorted(Counter("x".join(map(str, r["geometry"]["shape"])) for r in selected).items())),
    }

# An observed size prevents interpreting the sole failure as an unsupported-30 issue.
medium = [r for r in sample_records if r["difficulty"] == "medium"]
requested_observed_shape = [13, 13]
observed_shape_witnesses = [r for r in medium if r["geometry"]["shape"] == requested_observed_shape]
assert observed_shape_witnesses, "The intended 13x13 support witness was absent"
base_record = next(r for r in medium if r["geometry"]["shape"] != requested_observed_shape)
seed = base_record["seed"]
controls = [
    draw_with_provenance(seed, seed, "medium", {}),
    draw_with_provenance(seed, seed, "medium", {"grid_h": 30, "grid_w": 30}),
    draw_with_provenance(seed, seed, "medium", {"grid_h": 13, "grid_w": 13}),
]
for item in controls[1:]:
    item["identical_to_default"] = item["input"] == controls[0]["input"]
    item["requested_shape"] = [item["overrides"]["grid_h"], item["overrides"]["grid_w"]]
    item["requested_shape_honored"] = item["shape"] == item["requested_shape"]

prior_path = ROOT / f"generators/{TASK}/evidence/review_index.json"
prior = json.loads(prior_path.read_text())
prior_records = [{k: a.get(k) for k in ("return_id", "resolution", "source_sha256", "verification_status")}
                 for a in prior.get("audits", []) if a.get("source_sha256") == source_hash]
assert prior_records, "Expected same-source prior audit is absent"

inputs = [r["input"] for r in canonical_records] + [r["input"] for r in controls]
receipt = Catalog(ROOT).apply(TASK, inputs, allow_unapproved=True, timeout=150,
                              check_generator_domain=True)
(HERE / "racket.json").write_text(json.dumps(receipt, indent=2) + "\n")
assert receipt["generator_sha256"] == source_hash
assert receipt["rule_hash_matches_catalog"]
assert len(receipt["results"]) == len(inputs)
for index, result in enumerate(receipt["results"]):
    assert result["error"] is None, result
    if index < len(canonical_records):
        item = canonical_records[index]
        item["racket_matches_canonical_output"] = result["output"] == item["output"]
        assert item["racket_matches_canonical_output"], index
    else:
        item = controls[index - len(canonical_records)]
    item["racket_receipt_index"] = index
    item["racket_output"] = result["output"]
    item["racket_input_sha256"] = result["input_sha256"]
    item["racket_output_sha256"] = result["output_sha256"]

assert sha_file(source) == source_hash, "Audited source changed during the probe"
contract_path = ROOT / "docs/reference/PUZZLE_GENERATOR_SPEC.md"
evidence = {
    "schema": "e5ec1ac39df5-findings-only-audit-v1", "task_id": TASK,
    "generator_version": gen.VERSION, "generator_sha256": source_hash,
    "generator_path": str(source.relative_to(ROOT)),
    "rule_hash": receipt["executed_rule_hash"],
    "rule_text_sha256": receipt["rule_text_sha256"],
    "rule_hash_matches_catalog": receipt["rule_hash_matches_catalog"],
    "canonical_ledger_sha256": sha_file(canonical_path(ROOT)),
    "probe_sha256": sha_file(Path(__file__)), "python_version": platform.python_version(),
    "scope": "Read-only findings audit; no battery, generator/rule edits, training admission, or lesson-identifiability claim.",
    "prior_same_source_audits": prior_records,
    "findings": [
        {"id": "E5-F1", "kind": "existing_reproduced_canonical_coverage_defect",
         "canonical_inputs_rejected": sum(bool(r["self_check"]) for r in canonical_records),
         "canonical_inputs_total": len(canonical_records),
         "novel": False,
         "qualification": "The restricted generated domain is not a canonical-fitting rival: its restriction excludes authoritative canonical inputs."},
        {"id": "E5-F2", "kind": "inert_advertised_full_grid_dimension_controls",
         "novel_relative_to_retained_same_source_audit": True,
         "paired_requests": len(controls) - 1,
         "identical_to_default": sum(r["identical_to_default"] for r in controls[1:]),
         "requested_shape_not_honored": sum(not r["requested_shape_honored"] for r in controls[1:]),
         "qualification": "The 30x30 request has no declared numeric validity range; the additional 13x13 request is witnessed in normal generated support. Both are silently accepted and ignored."},
    ],
    "dimension_contract": {
        "path": str(contract_path.relative_to(ROOT)), "sha256": sha_file(contract_path),
        "section": "Reserved full-grid dimension axes",
        "meaning": "grid_h must equal len(returned_grid); grid_w must equal len(returned_grid[0]).",
        "advertised_axes": {axis: gen.AXES[axis] for axis in ("grid_h", "grid_w")},
        "range_caveat": "Both AXES entries say valid=varied and give no numeric range or incompatible-setting behavior.",
    },
    "canonical": canonical_records,
    "sampling": {"seed_range_inclusive": [1, 100], "sample_index_policy": "sample_index = seed",
                 "difficulty_bands": ["easy", "medium", "hard"],
                 "summary": sample_summary, "records": sample_records,
                 "racket_checked_for_this_sample": False,
                 "limitation": "Finite structural and validator census only; no claim that all possible draws or their labels were checked."},
    "controls": controls,
    "observed_13x13_support_witness": {k: observed_shape_witnesses[0][k] for k in ("difficulty", "seed", "sample_index", "input_sha256", "geometry")},
    "racket_receipt": "checks/audit/e5ec1ac39df5/racket.json",
    "racket_input_order": [f"canonical:{r['split']}:{r['pair_index']}" for r in canonical_records]
        + ["default-medium", "grid_h=30,grid_w=30", "grid_h=13,grid_w=13"],
    "racket_outputs_checked": len(receipt["results"]),
    "source_unchanged_after_probe": True,
}
(HERE / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n")
print(json.dumps({
    "task_id": TASK, "generator_sha256": source_hash, "rule_hash": receipt["executed_rule_hash"],
    "rule_text_sha256": receipt["rule_text_sha256"], "findings": evidence["findings"],
    "sampling_summary": sample_summary,
    "control_calls": [{k: r[k] for k in ("seed", "sample_index", "difficulty", "overrides", "shape", "overrides_used")} for r in controls],
    "racket_outputs_checked": len(receipt["results"]),
}, indent=2))
