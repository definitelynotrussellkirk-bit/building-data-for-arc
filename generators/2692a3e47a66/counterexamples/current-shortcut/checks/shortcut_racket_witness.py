from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT / "repo"
TASK_ID = "2692a3e47a66"
GENERATOR_PATH = REPO / "generators" / TASK_ID / "generator.py"
CANONICAL_PATH = REPO / "shared/data/canonical/puzzles.jsonl"

sys.path.insert(0, str(REPO / "shared/runtime"))
scripts_pkg = types.ModuleType("scripts")
scripts_pkg.__path__ = [str(REPO / "shared/tools")]
sys.modules.setdefault("scripts", scripts_pkg)
from puzzle_generators import runner


def load_generator():
    spec = importlib.util.spec_from_file_location(f"witness_{TASK_ID}", GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row():
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise KeyError(TASK_ID)


def pairs(row):
    result = []
    for split in ("train", "test"):
        value = row.get(split) or []
        if isinstance(value, dict):
            value = [value]
        result.extend(item for item in value if isinstance(item, dict))
    return result


def diff_cells(left, right):
    return [
        {"row": r, "col": c, "intended": a, "rival": b}
        for r, (left_row, right_row) in enumerate(zip(left, right))
        for c, (a, b) in enumerate(zip(left_row, right_row))
        if a != b
    ]


def main():
    gen = load_generator()
    row = canonical_row()
    seed = 71
    sample_index = 3
    overrides = {
        "grid_h": 17,
        "grid_w": 19,
        "scene_profile": "two_pairs_mixed",
    }
    grid = gen.generate(seed, sample_index, difficulty="medium", **overrides)
    rival_name = "move_only_modal_object_color"
    rival = gen.CANONICAL_SHORTCUTS[rival_name]
    rival_output = rival(grid)
    mirror_output = gen.rule_mirror(grid)

    source = row["program_solution"]
    bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(source))
    try:
        racket_output = runner._apply_rule(bridge, name, grid)
    finally:
        bridge.shutdown()

    canonical = pairs(row)
    canonical_matches = sum(
        rival(pair["input"]) == pair["output"] for pair in canonical
    )
    payload = {
        "schema": "arcpuzzles-shortcut-counterexample-v1",
        "task_id": TASK_ID,
        "generator_sha256": hashlib.sha256(GENERATOR_PATH.read_bytes()).hexdigest(),
        "rule_hash": hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12],
        "seed": seed,
        "sample_index": sample_index,
        "difficulty": "medium",
        "overrides": overrides,
        "observed_overrides": gen.observe_overrides(grid),
        "validator_errors": gen.self_check(grid),
        "strict_errors": gen.strict_canonical_like(grid),
        "input": grid,
        "actual_racket_output": racket_output,
        "python_rule_mirror_output": mirror_output,
        "racket_equals_python_mirror": racket_output == mirror_output,
        "rival_name": rival_name,
        "rival_description": "Move only the foreground color with the greatest number of disconnected objects; break ties by lowest color.",
        "rival_output": rival_output,
        "rival_disagrees": rival_output != racket_output,
        "differing_cells": diff_cells(racket_output, rival_output),
        "canonical_fit": {
            "matches": canonical_matches,
            "pairs": len(canonical),
            "fits_all": canonical_matches == len(canonical),
        },
        "generator_emits_case": True,
        "schedule_note": "two_pairs_mixed is one of four cyclic default profiles, so every four consecutive default samples include this semantic case",
        "command": [
            "python3",
            "run_with_racket.py",
            "python3",
            "../checks/shortcut_racket_witness.py",
        ],
        "cwd": "packet_root",
    }
    out = ROOT / "checks/shortcut-counterexample.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(out.relative_to(ROOT))
    print(json.dumps({
        "racket_equals_python_mirror": payload["racket_equals_python_mirror"],
        "rival_disagrees": payload["rival_disagrees"],
        "canonical_fit": payload["canonical_fit"],
        "differing_cells": len(payload["differing_cells"]),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
