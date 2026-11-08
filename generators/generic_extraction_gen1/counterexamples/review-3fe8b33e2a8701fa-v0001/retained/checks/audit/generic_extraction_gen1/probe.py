from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.generic.concepts.extraction import _program_body

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "repo" / "generators" / "generic_extraction_gen1" / "generator.py"
OUT = Path(__file__).with_name("report.json")

spec = importlib.util.spec_from_file_location("audit_generic_extraction_gen1", SOURCE)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def bbox_area(grid, color):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1)


def smallest_bbox_rival(grid):
    colors = sorted({value for row in grid for value in row if value != 0})
    target = min(colors, key=lambda color: (bbox_area(grid, color), color))
    return module._apply(grid, target), target


medium_tasks = 0
medium_pairs = 0
medium_fit_tasks = 0
medium_fit_pairs = 0
for seed in range(500):
    task = module.generate_task(seed, difficulty="medium")
    medium_tasks += 1
    task_ok = True
    for pair in task["train"] + task["test"]:
        medium_pairs += 1
        rival, _ = smallest_bbox_rival(pair["input"])
        fit = rival == pair["output"]
        medium_fit_pairs += int(fit)
        task_ok &= fit
    medium_fit_tasks += int(task_ok)

counterexample = None
for seed in range(100):
    task = module.generate_task(seed, difficulty="easy")
    for split in ("train", "test"):
        for pair_index, pair in enumerate(task[split]):
            rival, selected = smallest_bbox_rival(pair["input"])
            if rival == pair["output"]:
                continue
            body = _program_body(task["program"])
            bridge = RacketBridge()
            try:
                bridge.define_grid("g", pair["input"])
                actual = bridge.eval_text(body)
            finally:
                bridge.shutdown()
            assert actual == pair["output"]
            counterexample = {
                "seed": seed,
                "difficulty": "easy",
                "split": split,
                "pair_index": pair_index,
                "declared_target": task["meta"]["target"],
                "rival_selected_color": selected,
                "program": task["program"],
                "program_normalized_sha256": hashlib.sha256(
                    " ".join(task["program"].split()).encode()
                ).hexdigest(),
                "input": pair["input"],
                "racket_output": actual,
                "rival_output": rival,
                "bbox_areas": {
                    str(color): bbox_area(pair["input"], color)
                    for color in sorted({v for row in pair["input"] for v in row if v})
                },
            }
            break
        if counterexample:
            break
    if counterexample:
        break
assert counterexample is not None

report = {
    "schema": "arcpuzzles-audit-shortcut-v1",
    "task_id": "generic_extraction_gen1",
    "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    "has_self_check": hasattr(module, "self_check"),
    "rival": "For each input independently, select the nonzero color with the smallest bounding-box area, keep only it, then crop.",
    "default_medium_census": {
        "seed_range": "0..499",
        "tasks": medium_tasks,
        "pairs": medium_pairs,
        "rival_fit_tasks": medium_fit_tasks,
        "rival_fit_pairs": medium_fit_pairs,
    },
    "generated_counterexample": counterexample,
    "limits": [
        "Finite census of one declared rival, not proof about all hypotheses.",
        "This generic family has a per-task generated Racket program rather than a fixed catalog authority.",
    ],
}
OUT.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({
    "out": str(OUT),
    "medium_fit_tasks": f"{medium_fit_tasks}/{medium_tasks}",
    "medium_fit_pairs": f"{medium_fit_pairs}/{medium_pairs}",
    "counterexample_seed": counterexample["seed"],
    "counterexample_split": counterexample["split"],
    "counterexample_pair_index": counterexample["pair_index"],
}, indent=2))
