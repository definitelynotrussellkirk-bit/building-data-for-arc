"""Bounded independent confirmation of the frozen compact-schedule repair."""
from collections import Counter
from copy import deepcopy
from itertools import permutations
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import load_selected_generator

ROOT = Path.cwd()
OUT = ROOT.parent / "checks/final-code-review"
TASK = "33c7c507a8ef"
EXPECTED_SHA = "1e0fba152cbbdc340d753d076450a3004ce7b519417bf7d1c4970ae475c622b2"
gen, source, source_sha = load_selected_generator(TASK, root=ROOT)
assert source_sha == EXPECTED_SHA


def inner(grid):
    gray = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 5]
    top, bottom = min(r for r, _ in gray), max(r for r, _ in gray)
    left, right = min(c for _, c in gray), max(c for _, c in gray)
    return [list(row[left+1:right]) for row in grid[top+1:bottom]]


def rotate(grid, turns):
    result = deepcopy(grid)
    for _ in range(turns):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def rival(grid):
    crop = inner(grid)
    gray = any(value == 5 for row in crop for value in row)
    turns = 2 if (len(grid), len(grid[0])) == (5, 6) and gray else grid[0][0] - 1
    return rotate(crop, turns)


representatives = {}
for seed in range(512):
    order = [None] * 4
    for index in range(4):
        grid = gen.generate(seed, index, difficulty="easy")
        order[gen.schedule_profile(seed, index) % 4] = grid[0][0]
    representatives.setdefault(tuple(order), seed)
    if len(representatives) == 24:
        break
assert set(representatives) == set(permutations((1, 2, 3, 4)))
order_results = []
for order, seed in sorted(representatives.items()):
    grids = [gen.generate(seed, index, difficulty="easy") for index in range(23)]
    first_cycle = grids[:16]
    compact = [grid for grid in first_cycle if (len(grid), len(grid[0])) == (5, 6)]
    canonical_count = sum(gen.canonical_profile_signature(grid) is not None for grid in first_cycle)
    assert len(compact) == 10 and canonical_count == 3
    states = {code: set() for code in (1, 2, 3, 4)}
    for grid in compact:
        observed = gen.observe_overrides(grid)
        states[observed["code"]].add(observed["include_frame_color"])
    assert all(state == {False, True} for state in states.values())
    labels = [rotate(inner(grid), grid[0][0]-1) for grid in grids]
    assert all(gen.self_check(grid) == [] and gen.rule_mirror(grid) == label
               for grid, label in zip(grids, labels))
    compact_refutations = [rival(grid) != label for grid, label in zip(grids, labels)]
    fixed_crop_refutations = [gen.SEMANTIC_RIVALS["fixed_public_crop"](grid) != label
                             for grid, label in zip(grids, labels)]
    for start in range(16):
        window = grids[start:start+8]
        assert Counter(grid[0][0] for grid in window) == {1:2, 2:2, 3:2, 4:2}
        for code in (1, 2, 3, 4):
            assert {gen.observe_overrides(grid)["include_frame_color"]
                    for grid in window if grid[0][0] == code} == {False, True}
        assert sum(compact_refutations[start:start+8]) >= 2
        assert sum(fixed_crop_refutations[start:start+8]) >= 2
    order_results.append({"order": order, "seed": seed, "compact_count": len(compact),
                          "canonical_count": canonical_count,
                          "minimum_compact_rival_refutations_per_eight": min(sum(compact_refutations[s:s+8]) for s in range(16)),
                          "minimum_fixed_crop_refutations_per_eight": min(sum(fixed_crop_refutations[s:s+8]) for s in range(16))})

intermediate = json.loads((OUT / "compact-support.json").read_text())
negative = intermediate["negative_query_input"]
inputs = [gen.generate(17, index, difficulty="easy") for index in range(8)] + [negative]
reference = Catalog(ROOT).apply(TASK, inputs, check_generator_domain=True)
assert reference["generator_sha256"] == source_sha
assert all(row["valid_output"] and row["error"] is None
           and row["generator_domain"] == {"status": "valid", "errors": []}
           for row in reference["results"])
outputs = [row["output"] for row in reference["results"]]
assert outputs[-1] == intermediate["negative_racket_output"]
assert all(gen.rule_mirror(grid) == output for grid, output in zip(inputs, outputs))
declared_rival = gen.SEMANTIC_RIVALS["compact_gray_implies_half_turn"]
assert all(declared_rival(grid) == rival(grid) for grid in inputs)
refutations = [index for index in range(8) if rival(inputs[index]) != outputs[index]]
assert len(refutations) >= 2
assert any(index < 7 for index in refutations)
assert rival(negative) != outputs[-1]
assert len(gen.SEMANTIC_RIVALS) == 16
assert "compact_gray_implies_half_turn" in gen.LESSON_COMPETITORS
assert "compact_gray_implies_half_turn" in gen.CANONICAL_SHORTCUTS
assert "compact_gray_implies_half_turn" in gen.SEMANTIC_WITNESSES
assert gen.WITNESS_RIVALS["compact_gray_implies_half_turn"] == ["compact_gray_implies_half_turn"]
override = intermediate["explicit_override"]
override_grid = gen.generate(17, 0, difficulty="easy", **override)
assert gen.observe_overrides(override_grid) == intermediate["explicit_override_observed"]
assert [len(override_grid), len(override_grid[0])] == intermediate["explicit_override_shape"]
assert gen.generate(17, 0, difficulty="easy", **{name:None for name in gen.AXES}) == inputs[0]
assert hashlib.sha256(source.read_bytes()).hexdigest() == source_sha

report = {"generator_sha256": source_sha,
          "issue_status": "closed_on_this_source_by_independent_bounded_confirmation",
          "all_code_orders": len(order_results), "python_checked_grids": 24*23,
          "default_live_racket_draws": 8, "negative_live_racket_draws": 1,
          "live_refuting_default_indices": refutations,
          "seven_demo_rival_survives": False,
          "negative_racket_output_preserved": True,
          "exact_override_observations_preserved": True,
          "known_none_override_omission_preserved": True,
          "declared_rivals": 16,
          "executed_rule_hash": reference["executed_rule_hash"],
          "executed_rule_text_sha256": reference["rule_text_sha256"],
          "order_results": order_results,
          "limits": "Grid checks cover all 24 order representatives in easy; separate compact tests cover all 12 position pairs across three bands. Fresh live labels cover the original eight-default lesson and one legal negative query. No universal arbitrary-geometry claim."}
(OUT / "final-racket.json").write_text(json.dumps(reference, indent=2) + "\n")
(OUT / "final-confirmation.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({key:value for key,value in report.items() if key != "order_results"}, indent=2))
