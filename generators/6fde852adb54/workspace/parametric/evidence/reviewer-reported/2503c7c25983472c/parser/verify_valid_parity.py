"""Bounded valid-input parity and parser rejection-surface evidence."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time
from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "repo/generators/6fde852adb54/generator.py"
BASELINE = ROOT / ".review/baseline/repo/generators/6fde852adb54/generator.py"
EXPECTED_BASELINE = "314ce0e1b7bd29351ba96728529143a22a63cc6787af981c03bef2eaee3077de"
EXPECTED_SOURCE = "f7a534e4c744da6f32b2576f5831721a01f71a7ec0df48694fd97c52bbd176db"

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def grid_hash(grid):
    return sha(json.dumps(grid, separators=(",", ":")).encode())

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

assert sha(BASELINE.read_bytes()) == EXPECTED_BASELINE
assert sha(SOURCE.read_bytes()) == EXPECTED_SOURCE
old = load(BASELINE, "parser_frozen_baseline")
new = load(SOURCE, "parser_repaired_selected")
assert new.VERSION == old.VERSION == "4.0.0"
assert new.RULE_HASH == old.RULE_HASH == "4a2e9b9f15bf"
configs = [{"seed": seed, "sample_index": 0, "difficulty": difficulty, "scene_family": family}
           for seed in [0, 41] for difficulty in ["easy", "medium", "hard"]
           for family in ["public", "generalized"]]
records, retained = [], []
for index, config in enumerate(configs):
    before = old.generate(**config)
    after = new.generate(**config)
    assert before == after, ("Generated input changed", config)
    original = deepcopy(after)
    assert old.self_check(before) == new.self_check(after) == []
    assert old.observe_overrides(before) == new.observe_overrides(after)
    expected = old.rule_mirror(before)
    assert new.rule_mirror(after) == expected
    assert after == original, ("Validation mutated input", config)
    records.append({"config": config, "height": len(after), "width": len(after[0]),
                    "input_sha256": grid_hash(after), "output_sha256": grid_hash(expected),
                    "generated_input_unchanged": True, "public_api_results_unchanged": True})
    if index in [0, 3, 8, 11]:
        retained.append({"config_index": index, "input": after, "expected": expected})

canonical_path = ROOT / "repo/shared/data/canonical/puzzles.jsonl"
row = next(json.loads(line) for line in canonical_path.read_text().splitlines()
           if json.loads(line).get("task_id") == "6fde852adb54")
program = row["program_solution"]
wrapped = wrap_rule(program)
bridge = RacketBridge(timeout=10.0, max_calls_before_restart=64)
try:
    for case in retained:
        bridge.define_grid("g", case["input"])
        actual = bridge.eval_text(f"({wrapped} g)")
        assert actual == case.pop("expected"), ("Canonical Racket differs", case["config_index"])
        case["racket_output"] = actual
        case["racket_output_sha256"] = grid_hash(actual)
        case["matched_frozen_and_repaired_mirrors"] = True
finally:
    bridge.shutdown()

# Bounded adversarial checks: dimension limits and structural/type rejection.
adversarial_start = time.perf_counter()
adversarial_started = datetime.now(timezone.utc).isoformat()
def dimension_case(height, width):
    grid = [[7] * width for _ in range(height)]
    for col, value in enumerate([9, 9, 9, 1, 5]):
        if col < width:
            grid[0][col] = value
    return grid

boundary_cases = [(f"dimensions_{h}x{w}", dimension_case(h, w), True)
                  for h, w in [(1, 14), (2, 14), (3, 14), (13, 14), (25, 14),
                               (14, 1), (14, 13), (14, 25)]]
boundary_cases += [("empty_grid", [], False), ("empty_row", [[]], False),
                   ("ragged_rows", [[7] * 14, [7] * 13], False),
                   ("boolean_cell", [[True] + [7] * 13] + [[7] * 14 for _ in range(13)], False)]
boundary_results = []
for name, grid, dimension_error in boundary_cases:
    original = deepcopy(grid)
    errors = new.self_check(grid)
    assert errors, name
    if dimension_error:
        assert any("dimensions" in error for error in errors), name
    assert new.observe_overrides(grid) == {}, name
    try:
        new.rule_mirror(grid)
    except ValueError:
        pass
    else:
        raise AssertionError("rule_mirror accepted " + name)
    assert grid == original, name
    boundary_results.append({"case": name, "self_check_errors": errors,
                             "observe_overrides": {}, "rule_mirror_raised": "ValueError",
                             "input_unchanged": True})

print(json.dumps({"schema": "selected-parser-valid-parity-v1", "status": "pass",
                  "task_id": "6fde852adb54", "baseline_generator_sha256": EXPECTED_BASELINE,
                  "repaired_generator_sha256": EXPECTED_SOURCE, "version": new.VERSION,
                  "rule_hash": new.RULE_HASH, "canonical_program_sha256": sha(program.encode()),
                  "canonical_collection_sha256": sha(canonical_path.read_bytes()),
                  "valid_configurations": records, "racket_cases": retained,
                  "bounded_adversarial": {"started_at_utc": adversarial_started,
                      "elapsed_seconds": time.perf_counter() - adversarial_start,
                      "surfaces": ["dimension bounds before row indexing", "structural/type rejection and input purity"],
                      "cases": boundary_results},
                  "limits": ["Twelve deterministic configurations are representative parity evidence, not exhaustive generator coverage.",
                             "Canonical Racket was executed on exactly four valid examples; malformed grids were tested only against the Python validation APIs.",
                             "No sampler, version, canonical rule, or shared runtime changes were made."]}, indent=2, sort_keys=True))
