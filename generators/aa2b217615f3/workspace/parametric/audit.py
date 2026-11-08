"""Reusable bounded source-bound audit for the stacking-order family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
HOME = HERE.parents[1]
ROOT = HOME.parents[1]
TASK_ID = HOME.name


def _load_adapter():
    path = HERE / "adapter.py"
    spec = importlib.util.spec_from_file_location("_aa2_stack_audit_adapter", path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load adjacent adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _independent_slide(adapter, grid):
    """Cheap rival: every object ignores other moved objects."""
    source = copy.deepcopy(grid)
    direction = adapter._direction(source)
    h, w = len(source), len(source[0])
    out = [[2 if source[r][c] == 2 else 0 for c in range(w)] for r in range(h)]
    red = {(r, c) for r in range(h) for c in range(w) if source[r][c] == 2}
    dr, dc = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}[direction]
    objects = sorted(adapter._objects(source), key=lambda obj: adapter._depth_key(obj, direction))
    for obj in objects:
        distance = 0
        while all(0 <= r + dr * (distance + 1) < h and 0 <= c + dc * (distance + 1) < w
                  and (r + dr * (distance + 1), c + dc * (distance + 1)) not in red
                  for r, c in obj["cells"]):
            distance += 1
        for r, c in obj["cells"]:
            out[r + dr * distance][c + dc * distance] = obj["color"]
    return out


def run(out: Path) -> dict:
    if out.exists():
        raise FileExistsError(f"choose a fresh path: {out}")
    if not out.resolve().is_relative_to((HERE / "evidence").resolve()):
        raise ValueError("audit output must stay under task-local evidence")
    adapter = _load_adapter()
    from arcpuzzles.parametric_worker import evaluate_contract
    contract = json.loads((HERE / "promotion.json").read_text())
    settings = [{"stack_order": "near_first"}, {"stack_order": "far_first"}]
    jobs = [
        {"seed": seed, "settings": setting, "demos": demos, "queries": 4}
        for seed in (0, 17) for setting in settings for demos in (2, 6)
    ]
    execution = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    if execution["racket"].get("backend") != "racket" or execution["racket"].get("protected") is not True:
        raise AssertionError("audit did not use protected Racket")

    seed_rows = []
    independent_refutations = 0
    for seed in range(64):
        near = adapter.generate(seed, settings[0], 2, 4)
        far = adapter.generate(seed, settings[1], 2, 4)
        assert [p["input"] for p in near["train"] + near["test"]] == [p["input"] for p in far["train"] + far["test"]]
        assert all(a["output"] != b["output"] for a, b in zip(near["train"], far["train"]))
        for pair in near["train"]:
            assert adapter.has_stacking_witness(pair["input"])
            if _independent_slide(adapter, pair["input"]) != pair["output"]:
                independent_refutations += 1
        seed_rows.append({
            "seed": seed,
            "distinct_inputs": len({json.dumps(p["input"]) for p in near["train"] + near["test"]}),
            "first_demo_order_disagreement": near["train"][0]["output"] != far["train"][0]["output"],
        })

    large = adapter.sample_input(17, "test", 3)
    nonzero = [(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value]
    report = {
        "schema": "arcpuzzles-task-local-authoring-audit-v1",
        "task_id": TASK_ID,
        "status": "pass",
        "source_hashes": {
            str(path.relative_to(ROOT)): _sha(path)
            for path in (
                HOME / "generator.py", HERE / "adapter.py", HERE / "canonical.rkt",
                HERE / "far_first.rkt", HERE / "promotion.json",
                HOME / "tests/test_native_parametric.py",
            )
        },
        "protected_execution": {
            "jobs": len(execution["episodes"]),
            "racket_evaluations": execution["racket_evaluations"],
            "runtime": execution["racket"],
            "settings": settings,
            "demo_counts": [2, 6],
            "queries": 4,
        },
        "bounded_sampling": {
            "seeds": 64,
            "episodes": 128,
            "all_first_two_demos_distinguish_orders": True,
            "independent_slide_demo_refutations": independent_refutations,
            "rows": seed_rows,
        },
        "stress_30x30": {
            "nonzero_cells": len(nonzero),
            "row_extent": [min(r for r, _ in nonzero), max(r for r, _ in nonzero)],
            "column_extent": [min(c for _, c in nonzero), max(c for _, c in nonzero)],
            "stacking_witness": adapter.has_stacking_witness(large),
            "settings_disagree": adapter.transform(large, settings[0]) != adapter.transform(large, settings[1]),
        },
        "limits": "Finite declared-setting and independent-slide audit; not universal uniqueness, owner acceptance, learning benefit, or training admission.",
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = run(args.out)
    print(json.dumps({k: report[k] for k in ("task_id", "status", "protected_execution", "stress_30x30")}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
