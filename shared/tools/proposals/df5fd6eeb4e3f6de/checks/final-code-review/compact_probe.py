"""Independent read-only review of default compact support in 33c7c507a8ef."""
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, load_selected_generator

ROOT = Path.cwd()
WORK = ROOT.parent
OUT = WORK / "checks/final-code-review"
TASK = "33c7c507a8ef"
gen, source, source_sha = load_selected_generator(TASK, root=ROOT)


def crop(grid):
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
    inner = crop(grid)
    gray_inside = any(value == 5 for row in inner for value in row)
    turns = 2 if (len(grid), len(grid[0])) == (5, 6) and gray_inside else grid[0][0] - 1
    return rotate(inner, turns)


census = []
compact_states = Counter()
for band in ("easy", "medium", "hard"):
    for seed in (0, 17, 918):
        for index in range(16):
            grid = gen.generate(seed, index, difficulty=band)
            observed = gen.observe_overrides(grid)
            compact = (len(grid), len(grid[0])) == (5, 6)
            row = {"seed": seed, "sample_index": index, "difficulty": band,
                   "compact": compact, "observed": observed,
                   "self_check": gen.self_check(grid), "rival_equals_mirror": rival(grid) == gen.rule_mirror(grid)}
            census.append(row)
            if compact:
                compact_states[(observed["code"], observed["include_frame_color"])] += 1

pairs = canonical_pairs(TASK, root=ROOT)
original_gray = next(pair for pair in pairs if pair["input"][0][0] == 3)
negative = deepcopy(original_gray["input"])
negative[0][0] = 2
inputs = [gen.generate(17, index, difficulty="easy") for index in range(8)] + [negative]
reference = Catalog(ROOT).apply(TASK, inputs, check_generator_domain=True)
assert source_sha == hashlib.sha256(source.read_bytes()).hexdigest()
assert reference["generator_sha256"] == source_sha
outputs = [row["output"] for row in reference["results"]]
assert all(row["valid_output"] and row["error"] is None for row in reference["results"])
assert all(row["generator_domain"] == {"status": "valid", "errors": []} for row in reference["results"])
demos = [{"input": inputs[i], "output": outputs[i]} for i in range(7)]
query = {"input": negative, "output": outputs[-1]}
differences = [[r, c, outputs[-1][r][c], rival(negative)[r][c]]
               for r, row in enumerate(outputs[-1]) for c in range(len(row))
               if len(rival(negative)) == len(outputs[-1])
               and len(rival(negative)[r]) == len(row)
               and outputs[-1][r][c] != rival(negative)[r][c]]
override = {"scene_family": "generalized", "code": 2, "include_frame_color": True,
            "interior_h": 2, "interior_w": 3, "frame_top": 1, "frame_left": 1,
            "n_content_colors": 2}
override_grid = gen.generate(17, 0, difficulty="easy", **override)
observed_override = gen.observe_overrides(override_grid)
assert all(observed_override[key] == value for key, value in override.items())
assert gen.generate(17, 0, difficulty="easy", **{key: None for key in gen.AXES}) == inputs[0]

proof = {
    "generator_sha256": source_sha,
    "executed_rule_text_sha256": reference["rule_text_sha256"],
    "executed_rule_hash": reference["executed_rule_hash"],
    "census_draws": len(census),
    "census_compact_code_gray_counts": [{"code": key[0], "include_frame_color": key[1], "count": value}
                                         for key, value in sorted(compact_states.items())],
    "census_self_check_failures": sum(bool(row["self_check"]) for row in census),
    "census_rival_mirror_mismatches": sum(not row["rival_equals_mirror"] for row in census),
    "live_default_cases": 8,
    "rival_matches_live_default": [rival(grid) == output for grid, output in zip(inputs[:8], outputs[:8])],
    "negative_query_input": negative,
    "negative_self_check": gen.self_check(negative),
    "negative_canonical_signature": gen.canonical_profile_signature(negative),
    "negative_racket_output": outputs[-1],
    "negative_rival_output": rival(negative),
    "negative_racket_shape": [len(outputs[-1]), len(outputs[-1][0])],
    "negative_rival_shape": [len(rival(negative)), len(rival(negative)[0])],
    "negative_equal": outputs[-1] == rival(negative),
    "seven_demo_seed": 17,
    "seven_demo_difficulty": "easy",
    "seven_demo_indices": list(range(7)),
    "seven_demo_overrides": {},
    "rival_fits_all_seven_demos": all(rival(pair["input"]) == pair["output"] for pair in demos),
    "negative_lesson_identifiable": gen.lesson_identifiable(demos, query),
    "explicit_override": override,
    "explicit_override_observed": observed_override,
    "explicit_override_shape": [len(override_grid), len(override_grid[0])],
    "known_none_overrides_equal_default": True,
    "census": census,
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "compact-racket.json").write_text(json.dumps(reference, indent=2) + "\n")
(OUT / "compact-support.json").write_text(json.dumps(proof, indent=2) + "\n")
print(json.dumps({key: value for key, value in proof.items() if key not in ("census", "negative_query_input", "negative_racket_output", "negative_rival_output")}, indent=2))
