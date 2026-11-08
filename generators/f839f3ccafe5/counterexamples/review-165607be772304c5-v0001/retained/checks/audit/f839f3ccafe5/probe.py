"""Read-only, source-bound audit of f839f3ccafe5; labels come from Catalog.apply."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root


TASK = "f839f3ccafe5"
EXPECTED_SOURCE = "bd9f4d0f2ce61e472e3f17df2a4c9c4fba55a4b1a3d6a50c81d044e5b9c34bc6"
ROOT = find_root(Path.cwd())
OUT = Path(__file__).resolve().parent
SOURCE = ROOT / "generators" / TASK / "generator.py"


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, separators=(",", ":")) + "\n")


def period_of(grid):
    height, width = len(grid), len(grid[0])
    for period in range(2, 12):
        if all(grid[r][c] == 1 or grid[r + period][c] == 1
               or grid[r][c] == grid[r + period][c]
               for r in range(height - period) for c in range(width)):
            return period
    return height


def no_blue_rival(grid):
    """Reconstruct residues, assuming blue cannot be a legitimate tile value.

    The only difference from the canonical reconstruction is its nonblue
    fallback for a residue having no nonblue representative.
    """
    height, width = len(grid), len(grid[0])
    period = period_of(grid)
    fallback = next(v for row in grid for v in row if v != 1)
    tile = []
    for rr in range(period):
        row = []
        for cc in range(period):
            row.append(next((grid[r][c] for r in range(rr, height, period)
                             for c in range(cc, width, period) if grid[r][c] != 1),
                            fallback))
        tile.append(row)
    return [[tile[r % period][c % period] for c in range(width)]
            for r in range(height)]


def differences(left, right):
    return [[r, c, left[r][c], right[r][c]]
            for r in range(len(left)) for c in range(len(left[0]))
            if left[r][c] != right[r][c]]


source_sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
assert source_sha == EXPECTED_SOURCE
spec = importlib.util.spec_from_file_location("f839f3ccafe5_audit_subject", SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
pairs = canonical_pairs(TASK, root=ROOT)
cases = []
for pair in pairs:
    cases.append({"kind": "canonical", "variant": pair["variant"],
                  "split": pair["split"], "pair_index": pair["pair_index"],
                  "seed": None, "sample_index": None, "overrides": {},
                  "input": pair["input"], "canonical_output": pair["output"]})
for band in ("easy", "medium", "hard"):
    for index in range(4):
        cases.append({"kind": "normal_draw", "difficulty": band,
                      "seed": 193, "sample_index": index, "overrides": {},
                      "input": gen.generate(193, index, difficulty=band)})
for name, overrides in (("period_2", {"period": 2}),
                        ("palette_2", {"palette_size": 2}),
                        ("anchor_false", {"anchor_corner": False}),
                        ("anchor_true", {"anchor_corner": True})):
    cases.append({"kind": "override", "name": name, "difficulty": None,
                  "seed": 37, "sample_index": 0, "overrides": overrides,
                  "input": gen.generate(37, 0, **overrides)})

save("input.json", pairs[0]["input"])
applied = Catalog(root=ROOT).apply(TASK, [case["input"] for case in cases], timeout=120)
assert applied["executed_rule_hash"] == "7af34bc80f8b"
assert applied["rule_hash_matches_catalog"] is True
assert applied["generator_sha256"] == source_sha
save("racket.json", applied)

observations = []
for position, (case, result) in enumerate(zip(cases, applied["results"], strict=True)):
    grid, output = case["input"], result["output"]
    assert output is not None
    rival = no_blue_rival(grid)
    diffs = differences(rival, output)
    row = {k: value for k, value in case.items() if k not in ("input", "canonical_output")}
    row.update({"racket_result_index": position,
                "input_sha256": digest(grid), "output_sha256": digest(output),
                "shape": [len(grid), len(grid[0])],
                "detected_vertical_period": period_of(grid),
                "nonblue_input_colors": sorted({v for line in grid for v in line if v != 1}),
                "self_check": gen.self_check(grid, difficulty=case.get("difficulty")),
                "output_blue_cells": sum(v == 1 for line in output for v in line),
                "rival_blue_cells": sum(v == 1 for line in rival for v in line),
                "rival_differing_cells": len(diffs), "first_rival_differences": diffs[:12]})
    if "canonical_output" in case:
        row["racket_matches_canonical_output"] = output == case["canonical_output"]
        assert row["racket_matches_canonical_output"]
    observations.append(row)

assert observations[0]["self_check"] == ["a period residue class is fully corrupted"]
assert observations[0]["output_blue_cells"] == 75
assert observations[0]["rival_differing_cells"] == 75
normal = [row for row in observations if row["kind"] == "normal_draw"]
assert len(normal) == 12 and all(row["self_check"] == [] for row in normal)
assert all(row["rival_differing_cells"] == 0 and row["output_blue_cells"] == 0 for row in normal)
by_name = {row["name"]: row for row in observations if row["kind"] == "override"}
assert by_name["period_2"]["detected_vertical_period"] == 6
assert len(by_name["palette_2"]["nonblue_input_colors"]) == 5
assert by_name["anchor_false"]["input_sha256"] == by_name["anchor_true"]["input_sha256"]
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_sha

save("rival_output.json", no_blue_rival(pairs[0]["input"]))
finding = {"schema": "arcpuzzles-focused-audit-v1", "task_id": TASK,
           "classification": "reproduced defect", "generator_sha256": source_sha,
           "canonical_rule_hash": applied["executed_rule_hash"],
           "canonical_file_sha256": hashlib.sha256((ROOT / "shared/data/canonical/puzzles.jsonl").read_bytes()).hexdigest(),
           "prior_lead": "Current review_index audit review-8a3e94839dba574b:v0001, independently reproduced against unchanged source",
           "declared_axes": {key: gen.AXES[key] for key in ("period", "palette_size", "anchor_corner")},
           "observations": observations,
           "normal_rival_agreement": {"tested": 12, "matched_actual_racket": 12},
           "limits": "Four labeled canonical pairs and twelve normal draws were measured. Rival is refuted by canonical examples, so this is a domain mismatch, not a rival fitting the canonical demonstrations. Override observations use one specified seed/index each. No full battery or universal lesson-identifiability claim.",
           "source_unchanged": True}
save("finding.json", finding)
print(json.dumps({"source_sha256": source_sha, "executed_rule_hash": applied["executed_rule_hash"],
                  "canonical": [{key: row[key] for key in ("split", "pair_index", "self_check", "output_blue_cells", "rival_differing_cells")}
                                for row in observations if row["kind"] == "canonical"],
                  "normal_rival_matches": 12,
                  "period_2_observed": by_name["period_2"]["detected_vertical_period"],
                  "palette_2_observed": len(by_name["palette_2"]["nonblue_input_colors"]),
                  "anchor_false_true_same_grid": True}, indent=2))
