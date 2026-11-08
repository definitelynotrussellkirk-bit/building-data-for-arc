"""Findings-only, source-bound audit. Run from packet_root; no source writes."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
TASK = "2534c7164e36"
GEN = ROOT / "repo" / "generators" / TASK / "generator.py"
sys.path.insert(0, str(ROOT / "repo" / "shared" / "runtime"))
spec = importlib.util.spec_from_file_location("audit_generator_2534c7164e36", GEN)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n")


def masks(grid):
    return tuple(sum(1 << (r * 4 + c) for r in range(4) for c in range(4)
                     if grid[r][o + c]) for o in (0, 5, 10))


def transformed(grid, symmetry):
    result = copy.deepcopy(grid)
    if symmetry >= 4:
        result = [row[::-1] for row in result]
    for _ in range(symmetry % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def transform_panels(grid, symmetry):
    panels = [transformed([row[o:o + 4] for row in grid], symmetry)
              for o in (0, 5, 10)]
    return [panels[0][r] + [grid[r][4]] + panels[1][r] + [grid[r][9]] + panels[2][r]
            for r in range(4)]


rows = []
for line in (ROOT / "repo/shared/data/canonical/puzzles.jsonl").open():
    row = json.loads(line)
    if row.get("task_id") == TASK:
        rows.append(row)
assert len(rows) == 2
training = next(row for row in rows if row["source"] == "training")
pairs = training["train"] + training["test"]
assert len(pairs) == 6
canonical_rule = training["program_solution"]
assert all(row["program_solution"] == canonical_rule for row in rows)
binding = {
    "task_id": TASK,
    "generator_sha256": digest(GEN.read_bytes()),
    "generator_version": module.VERSION,
    "rule_sha256": digest(" ".join(canonical_rule.split()).encode()),
    "rule_raw_sha256": digest(canonical_rule.encode()),
    "declared_rule_hash": module.RULE_HASH,
    "rule_hash_normalization": "SHA256 of whitespace-normalized program_solution",
    "canonical_selected_rows": [{"source": row["source"], "train_pairs": len(row["train"]),
                                 "test_pairs": len(row["test"])} for row in rows],
}
assert binding["generator_sha256"] == "eab765a3418f667520bfac6419a2730a4666dcb1e3fb54508c5cc117ef051ac5"

# A finite geometry lookup, deliberately using all six published labels; zero
# output on any unknown geometry. It does not implement the overlay law.
lookup = {}
for pair in pairs:
    for symmetry in range(8):
        lookup[masks(transform_panels(pair["input"], symmetry))] = transformed(pair["output"], symmetry)


def lookup_rival(grid):
    output = lookup.get(masks(grid))
    if output is None:
        return [[0] * 4 for _ in range(4)]
    colors = [next(value for row in grid for value in row[o:o + 4] if value)
              for o in (0, 5, 10)]
    role_map = dict(zip((0, 4, 9, 1), (0, *colors)))
    return [[role_map[value] for value in row] for row in output]


all_usable_pairs = [pair for row in rows for split in ("train", "test") for pair in row[split]]
assert len(all_usable_pairs) == 12
assert len({json.dumps(pair["input"]) for pair in all_usable_pairs}) == 6
assert all(lookup_rival(pair["input"]) == pair["output"] for pair in all_usable_pairs)


def sparse_boundary():
    grid = [[0] * 14 for _ in range(4)]
    for row in grid:
        row[4] = row[9] = 2
    for index, code in enumerate((0, 1, 2, 3, 4, 5, 6, 0, 0, 0, 0, 0, 0, 0, 0, 0)):
        r, c = divmod(index, 4)
        for offset, color, bit in ((0, 4, 4), (5, 9, 2), (10, 1, 1)):
            if code & bit:
                grid[r][offset + c] = color
    return grid


cases = []
for name, seed, sample_index, difficulty, overrides in (
    ("published_test_geometry_replay", 0, 17, "medium", {}),
    ("generalized_lookup_counterexample", 0, 0, "medium", {"scene_family": "generalized"}),
):
    cases.append({"name": name, "origin": "generated", "seed": seed,
                  "sample_index": sample_index, "difficulty": difficulty,
                  "overrides": overrides,
                  "input": module.generate(seed, sample_index, difficulty=difficulty, **overrides)})
cases.append({"name": "seven_state_boundary", "origin": "hand-constructed",
              "seed": None, "sample_index": None, "difficulty": None, "overrides": None,
              "input": sparse_boundary()})
for i, pair in enumerate(pairs):
    cases.append({"name": f"canonical_unique_{i}", "origin": "canonical",
                  "canonical_split": "train" if i < 5 else "test",
                  "canonical_index": i if i < 5 else 0,
                  "input": pair["input"], "published_output": pair["output"]})

for case in cases:
    grid = case["input"]
    case["masks"] = list(masks(grid))
    case["validator_errors"] = module.self_check(grid)
    case["validator_pass"] = case["validator_errors"] == []
    case["observed_overrides"] = module.observe_overrides(grid)
    case["documented_generator_domain"] = case["validator_pass"]
    case["rival_output"] = lookup_rival(grid)
    case["reference_expected_by_independent_overlay"] = [
        [next((grid[r][c + o] for o in (0, 5, 10) if grid[r][c + o]), 0)
         for c in range(4)] for r in range(4)]

replay_matches = []
for i, pair in enumerate(pairs):
    for symmetry in range(8):
        if masks(transform_panels(pair["input"], symmetry)) == masks(cases[0]["input"]):
            replay_matches.append({"canonical_unique_index": i, "split": "train" if i < 5 else "test",
                                   "symmetry": symmetry})

forced = []
for band in ("easy", "medium", "hard"):
    for family in ("linked", "generalized"):
        grids = [module.generate(2534, i, difficulty=band, scene_family=family) for i in range(20)]
        checks = [module.self_check(g) for g in grids]
        observations = [module.observe_overrides(g) for g in grids]
        forced.append({"seed": 2534, "sample_index_range": [0, 20], "range_end": "exclusive",
                       "difficulty": band, "overrides": {"scene_family": family}, "denominator": 20,
                       "validator_pass_count": sum(not errors for errors in checks),
                       "exact_observer_count": sum(o == {"scene_family": family} for o in observations),
                       "unique_inputs": len({json.dumps(g) for g in grids}),
                       "rival_overlay_disagreements": sum(lookup_rival(g) != module.rule_mirror(g) for g in grids),
                       "oracle_for_these_counts": "Python rule_mirror; not an extra Racket batch"})

summary = {
    **binding,
    "audit_status": "source unchanged; findings only",
    "prior_lead": {"return_id": "review-080665b9e70e6cd0:v0001",
                   "retained_index": "repo/generators/2534c7164e36/evidence/review_index.json",
                   "retained_source_sha256": binding["generator_sha256"],
                   "prior_return_zip_sha256": None},
    "rival": {"name": "published_geometry_lookup_else_zero", "published_label_pairs": len(pairs),
              "independent_symmetry_enumerations": len(pairs) * 8,
              "unique_lookup_geometry_triples": len(lookup),
              "canonical_fit_count": sum(lookup_rival(p["input"]) == p["output"] for p in pairs),
              "canonical_unique_denominator": len(pairs),
              "all_usable_canonical_pair_fit_count": sum(lookup_rival(p["input"]) == p["output"] for p in all_usable_pairs),
              "all_usable_canonical_pair_denominator": len(all_usable_pairs),
              "canonical_shortcuts_declared": getattr(module, "CANONICAL_SHORTCUTS", None),
              "lesson_competitors_declared": getattr(module, "LESSON_COMPETITORS", None)},
    "replay_geometry_matches": replay_matches,
    "replay_canonical_test_in_augmented_train": any(
        p["input"] == pairs[-1]["input"] for row in rows if row["source"] == "augmented" for p in row["train"]),
    "forced_controls": forced,
    "cases": cases,
    "reproduction": {"cwd": "packet_root",
        "prepare_argv": ["python3", "checks/audit/2534c7164e36/probe.py"],
        "reference_argv": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                           "--input", "../checks/audit/2534c7164e36/input.json",
                           "--out", "../checks/audit/2534c7164e36/racket.json"],
        "wrapper_changes_cwd_to": "repo"},
}
write("input.json", [case["input"] for case in cases])
write("probe.json", summary)
print(json.dumps({"binding": binding, "replay_matches": replay_matches,
                  "cases": [{"name": c["name"], "masks": c["masks"], "validator_errors": c["validator_errors"]}
                            for c in cases[:3]], "forced_controls": forced}, indent=2))
