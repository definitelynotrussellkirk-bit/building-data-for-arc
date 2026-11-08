"""Reusable bounded source-bound audit for the column-selection family."""
from __future__ import annotations

import argparse
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
    spec = importlib.util.spec_from_file_location("_a53_column_audit_adapter", path)
    if spec is None or spec.loader is None:
        raise ImportError("cannot load adjacent adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(out: Path) -> dict:
    if out.exists():
        raise FileExistsError(f"choose a fresh path: {out}")
    if not out.resolve().is_relative_to((HERE / "evidence").resolve()):
        raise ValueError("audit output must stay under task-local evidence")
    adapter = _load_adapter()
    from arcpuzzles.parametric_worker import evaluate_contract

    contract = json.loads((HERE / "promotion.json").read_text())
    settings = [{"column_mode": "explicit_mask"}, {"column_mode": "merged_component"}]
    jobs = [
        {"seed": seed, "settings": setting, "demos": demos, "queries": 4}
        for seed in (0, 17) for setting in settings for demos in (2, 6)
    ]
    execution = evaluate_contract(ROOT, TASK_ID, contract, jobs)
    if execution["racket"].get("backend") != "racket" or execution["racket"].get("protected") is not True:
        raise AssertionError("audit did not use protected Racket")

    rows = []
    setting_refutations = 0
    raw_component_refutations = 0
    for seed in range(64):
        explicit = adapter.generate(seed, settings[0], 2, 4)
        merged = adapter.generate(seed, settings[1], 2, 4)
        assert [p["input"] for p in explicit["train"] + explicit["test"]] == [
            p["input"] for p in merged["train"] + merged["test"]
        ]
        for explicit_pair, merged_pair in zip(explicit["train"], merged["train"]):
            grid = explicit_pair["input"]
            if explicit_pair["output"] != merged_pair["output"]:
                setting_refutations += 1
            if merged_pair["output"] != adapter.transform_with_raw_component(grid):
                raw_component_refutations += 1
            recolored = adapter.recolor_body(grid)
            raw = [row[:] for row in grid[3:]]
            assert adapter.largest_component_columns(recolored) != adapter.largest_component_columns(raw)
        rows.append({
            "seed": seed,
            "distinct_inputs": len({json.dumps(p["input"]) for p in explicit["train"] + explicit["test"]}),
            "first_demo_setting_disagreement": explicit["train"][0]["output"] != merged["train"][0]["output"],
            "first_demo_raw_counterfactual_refuted": merged["train"][0]["output"] != adapter.transform_with_raw_component(merged["train"][0]["input"]),
        })

    large = adapter.sample_input(17, "test", 3)
    nonzero = [(r, c) for r, row in enumerate(large) for c, value in enumerate(row) if value]
    keep = adapter.keep_columns(large)
    recolored_columns = adapter.largest_component_columns(adapter.recolor_body(large))
    raw_columns = adapter.largest_component_columns([row[:] for row in large[3:]])
    report = {
        "schema": "arcpuzzles-task-local-authoring-audit-v1",
        "task_id": TASK_ID,
        "status": "pass",
        "source_hashes": {
            str(path.relative_to(ROOT)): _sha(path)
            for path in (
                HOME / "generator.py", HERE / "adapter.py", HERE / "canonical.rkt",
                HERE / "merged_component.rkt", HERE / "promotion.json",
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
            "first_two_demo_setting_refutations": setting_refutations,
            "first_two_demo_raw_component_refutations": raw_component_refutations,
            "all_first_two_demos_distinguish_settings": setting_refutations == 128,
            "all_first_two_demos_refute_raw_component_selection": raw_component_refutations == 128,
            "rows": rows,
        },
        "stress_30x30": {
            "nonzero_cells": len(nonzero),
            "row_extent": [min(r for r, _ in nonzero), max(r for r, _ in nonzero)],
            "column_extent": [min(c for _, c in nonzero), max(c for _, c in nonzero)],
            "keep_columns": keep,
            "recolored_winner_columns": recolored_columns,
            "raw_winner_columns": raw_columns,
            "settings_disagree": adapter.transform(large, settings[0]) != adapter.transform(large, settings[1]),
            "raw_counterfactual_refuted": adapter.transform(large, settings[1]) != adapter.transform_with_raw_component(large),
        },
        "limits": "Finite declared-setting and raw-component audit; not universal uniqueness, owner acceptance, learning benefit, or training admission.",
    }
    if not report["bounded_sampling"]["all_first_two_demos_distinguish_settings"]:
        raise AssertionError("a sampled minimum lesson failed to distinguish settings")
    if not report["bounded_sampling"]["all_first_two_demos_refute_raw_component_selection"]:
        raise AssertionError("a sampled minimum lesson failed to refute the raw-body counterfactual")
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
