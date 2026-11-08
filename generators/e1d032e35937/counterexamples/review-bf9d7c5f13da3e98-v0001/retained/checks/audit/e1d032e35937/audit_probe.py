"""Findings-only replay for e1d032e35937; no reference runner internals.

Run prepare, then the retained supported arcpuzzles apply command, then compare.
The rival is an intentional diagnostic shortcut, not a model solve attempt.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REPO = ROOT / "repo"
TASK = "e1d032e35937"
sys.path.insert(0, str(REPO / "shared/runtime"))


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def digest_json(value):
    return digest_bytes(json.dumps(value, sort_keys=True, separators=(",", ":")).encode())


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2) + "\n")


def load_generator():
    source = REPO / "generators" / TASK / "generator.py"
    spec = importlib.util.spec_from_file_location("audit_target", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row():
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines()
            if json.loads(line).get("task_id") == TASK]
    assert len(rows) == 1
    return rows[0]


def source_identity(module, canonical):
    paths = ["generators/" + TASK + "/generator.py",
             "shared/runtime/puzzle_generators/base.py",
             "shared/runtime/puzzle_generators/helpers/grid.py"]
    return {
        "task_id": TASK,
        "version": module.VERSION,
        "generator_sha256": digest_bytes((REPO / paths[0]).read_bytes()),
        "rule_sha256": digest_bytes(canonical["program_solution"].encode()),
        "rule_hash_12": digest_bytes(canonical["program_solution"].encode())[:12],
        "canonical_row_sha256": digest_json(canonical),
        "source_files_sha256": {path: digest_bytes((REPO / path).read_bytes()) for path in paths},
        "audit_probe_sha256": digest_bytes(Path(__file__).read_bytes()),
    }


def as_grid(value):
    return [[int(cell) for cell in row] for row in value]


def fixed_horizontal_completion(grid):
    """Ignore the bar: fill each zero with the cell reflected in the canvas."""
    return [[cell or reflected for cell, reflected in zip(row, reversed(row))]
            for row in grid]


def n_source_colors(grid):
    return len({cell for row in grid for cell in row} - {0, 8})


def prepare():
    from puzzle_generators.base import set_ctx_observer

    module = load_generator()
    canonical = canonical_row()
    identity = source_identity(module, canonical)
    inputs = []
    cases = []

    def add(grid, **case):
        index = len(inputs)
        inputs.append(grid)
        cases.append({"case_index": index, "input_sha256": digest_json(grid),
                      "self_check_errors": module.self_check(grid), **case})

    hand = [[0] * 11 for _ in range(7)]
    for row in hand:
        row[4] = 8
    hand[1][1] = 2
    hand[3][2] = 3
    hand[5][0] = 4
    add(hand, origin="hand_constructed", seed=None, sample_index=None,
        overrides=None, difficulty=None,
        domain={"satisfies_declared_INVARIANTS": True,
                "inside_documented_grid_and_source_count_ranges": True,
                "in_actual_helpful_generator_support": False,
                "support_explanation": "The generator always sets b = w // 2; this bar is column 4 in width 11."})

    for split in ("train", "test"):
        for index, pair in enumerate(canonical[split]):
            add(as_grid(pair["input"]), origin="canonical", split=split,
                split_index=index, expected_canonical_output=as_grid(pair["output"]),
                seed=None, sample_index=None, overrides=None)

    for difficulty in ("easy", "medium", "hard"):
        for seed in range(20):
            add(module.generate(seed, 0, difficulty=difficulty), origin="generated",
                seed=seed, sample_index=0, difficulty=difficulty, overrides={},
                domain={"in_actual_helpful_generator_support": True})
    assert len(inputs) == 64

    # Actual declarations are inspected; this target declares no rival functions.
    declarations = {}
    for name in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS"):
        value = getattr(module, name, None)
        declarations[name] = {"present": hasattr(module, name),
                              "declared_names": list(value) if isinstance(value, dict) else None}

    controls = {
        "palette_kind": list(module.PALETTE_KINDS),
        "texture": list(module.HELPFUL_TEXTURES),
        "palette_size": list(range(1, 7)),
        "n_distinct_colors": list(range(1, 7)),
    }
    control_results = {}
    for name, values in controls.items():
        records = []
        for value in values:
            unchanged = 0
            observed_colors = []
            consumed = 0
            for seed in range(30):
                baseline = module.generate(seed, 0, difficulty="medium")
                observed_contexts = []
                set_ctx_observer(observed_contexts.append)
                try:
                    changed = module.generate(seed, 0, difficulty="medium", **{name: value})
                finally:
                    set_ctx_observer(None)
                unchanged += changed == baseline
                observed_colors.append(n_source_colors(changed))
                consumed += name in observed_contexts[0].overrides_used()
            records.append({"requested_value": value, "samples": 30,
                            "equal_to_no_override": unchanged,
                            "override_consumed_in_context": consumed,
                            "observed_source_color_count_min": min(observed_colors),
                            "observed_source_color_count_max": max(observed_colors)})
        control_results[name] = {"difficulty": "medium", "seed_range_inclusive": [0, 29],
                                 "sample_index": 0, "measurements": records}

    override_cases = []
    for difficulty, override in [
        ("medium", {"grid_w": 10}),
        ("medium", {"grid_w": 12}),
        ("hard", {"grid_w": 14}),
        *[(band, {"source_count": 1}) for band in (None, "easy", "medium", "hard")],
        *[(band, {"grid_h": 5}) for band in (None, "easy", "medium", "hard")],
    ]:
        record = {"seed": 0, "sample_index": 0, "difficulty": difficulty, "overrides": override}
        try:
            grid = module.generate(0, 0, difficulty=difficulty, **override)
            record.update({"input": grid, "shape": [len(grid), len(grid[0])],
                           "self_check_errors": module.self_check(grid)})
        except Exception as error:
            record.update({"exception_type": type(error).__name__, "exception": str(error)})
        override_cases.append(record)

    write("input.json", inputs)
    write("probe.json", {
        "phase": "final_unchanged_audit_source",
        "source_identity": identity,
        "rival": {"name": "fixed_horizontal_completion",
                  "intent": "intentional_diagnostic_shortcut",
                  "description": "For each row, keep every nonzero input cell; replace each zero by the cell at the reversed column. It never locates or checks the bar."},
        "declared_rivals": declarations,
        "cases": cases,
        "ignored_control_probes": control_results,
        "control_unique_baseline_inputs": len({digest_json(module.generate(seed, 0, difficulty="medium")) for seed in range(30)}),
        "override_contract_probes": override_cases,
        "actual_generator_support_proof": "Every non-degenerate generate() path increments even w to odd, sets b = w // 2, places only nonzero source colors left of b, and leaves all right cells blank. Therefore fixed_horizontal_completion equals the Racket transformation throughout this actual helpful support.",
        "limits": "The hand witness is accepted by self_check and the declared structural invariants but cannot be emitted by the unchanged helpful generator. This audit is not a repair and does not claim a full battery or lesson census."
    })
    print(json.dumps({"prepared_inputs": len(inputs), "generated_inputs": 60,
                      "ignored_control_measurements": sum(len(v) for v in controls.values()) * 30,
                      "source_identity": identity}))


def compare():
    module = load_generator()
    probe = json.loads((HERE / "probe.json").read_text())
    assert source_identity(module, canonical_row()) == probe["source_identity"]
    inputs = json.loads((HERE / "input.json").read_text())
    authority = json.loads((HERE / "racket.json").read_text())
    assert len(authority["results"]) == len(inputs)
    rows = []
    for grid, case, reference in zip(inputs, probe["cases"], authority["results"]):
        rival = fixed_horizontal_completion(grid)
        actual = reference["output"]
        rows.append({"case_index": case["case_index"], "origin": case["origin"],
                     "seed": case.get("seed"), "sample_index": case.get("sample_index"),
                     "difficulty": case.get("difficulty"), "overrides": case.get("overrides"),
                     "input_sha256": digest_json(grid),
                     "racket_error": reference["error"],
                     "rival_matches_racket": rival == actual,
                     "rival_matches_canonical": rival == case["expected_canonical_output"] if case["origin"] == "canonical" else None,
                     "racket_matches_canonical": actual == case["expected_canonical_output"] if case["origin"] == "canonical" else None,
                     "self_check_errors": module.self_check(grid)})

    generated = [row for row in rows if row["origin"] == "generated"]
    canonicals = [row for row in rows if row["origin"] == "canonical"]
    hand_output = authority["results"][0]["output"]
    hand_rival = fixed_horizontal_completion(inputs[0])
    witness = {
        "task_id": TASK, **probe["source_identity"],
        "input": inputs[0], "actual_racket_output": hand_output, "rival_output": hand_rival,
        "origin": "hand_constructed", "seed": None, "sample_index": None, "overrides": None,
        "domain": probe["cases"][0]["domain"], "self_check_errors": module.self_check(inputs[0]),
        "changed_cells_between_rival_and_racket": [[r, c] for r in range(len(hand_output))
                                                   for c in range(len(hand_output[0]))
                                                   if hand_output[r][c] != hand_rival[r][c]],
        "command": ["python3", "run_with_racket.py", "python3", "-m", "arcpuzzles", "apply", TASK,
                    "--input", "../checks/audit/" + TASK + "/input.json",
                    "--out", "../checks/audit/" + TASK + "/racket.json"],
        "cwd": "packet_root", "effective_payload_cwd": "repo", "racket_result_index": 0,
    }
    write("counterexample.json", witness)
    result = {
        "phase": "final_unchanged_audit_source", "source_identity": probe["source_identity"],
        "racket_report_sha256": digest_bytes((HERE / "racket.json").read_bytes()),
        "canonical_counts": {"usable_pairs": len(canonicals),
                             "rival_fits": sum(row["rival_matches_canonical"] for row in canonicals),
                             "racket_fits": sum(row["racket_matches_canonical"] for row in canonicals),
                             "validator_accepts": sum(not row["self_check_errors"] for row in canonicals)},
        "generated_counts": {"seed_range_inclusive": [0, 19], "sample_index": 0,
                             "difficulty_bands": ["easy", "medium", "hard"], "overrides": {},
                             "samples": len(generated), "unique_inputs": len({row["input_sha256"] for row in generated}),
                             "rival_fits_racket": sum(row["rival_matches_racket"] for row in generated),
                             "validator_accepts": sum(not row["self_check_errors"] for row in generated)},
        "hand_counterexample_count": 1,
        "authority_errors": sum(row["racket_error"] is not None for row in rows),
        "all_results": rows,
    }
    write("comparison.json", result)
    assert len(canonicals) == 3 and all(row["rival_matches_canonical"] and row["racket_matches_canonical"] for row in canonicals)
    assert all(row["rival_matches_racket"] and not row["self_check_errors"] for row in generated)
    assert not rows[0]["rival_matches_racket"] and not rows[0]["self_check_errors"]
    assert not any(row["racket_error"] for row in rows)
    print(json.dumps({key: result[key] for key in ("canonical_counts", "generated_counts", "hand_counterexample_count", "authority_errors")}))


if __name__ == "__main__":
    {"prepare": prepare, "compare": compare}[sys.argv[1]]()
