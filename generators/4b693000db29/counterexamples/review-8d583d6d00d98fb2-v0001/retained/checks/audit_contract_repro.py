from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

CASES = [
    {
        "task_id": "4b693000db29",
        "generator_sha256": "76a96b47a949aac59d20555b12b271cae254ce41534da68906e8500c6601727c",
        "seed": 1,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"shape_cells": 8},
    },
    {
        "task_id": "de83dfd70673",
        "generator_sha256": "0eabeb17d17760051b41a97c1b7bf400b2f9aee71b20e668e0d9fbd9a7a24a84",
        "seed": 0,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"grid_h": 10},
    },
    {
        "task_id": "de83dfd70673",
        "generator_sha256": "0eabeb17d17760051b41a97c1b7bf400b2f9aee71b20e668e0d9fbd9a7a24a84",
        "seed": 0,
        "sample_index": 0,
        "difficulty": "easy",
        "overrides": {"__override_contract_unknown_axis__": 1},
    },
]

rows = []
for case in CASES:
    path = Path("generators") / case["task_id"] / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{case['task_id']}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    raw = path.read_bytes()
    observed_sha = hashlib.sha256(raw).hexdigest()
    row = dict(case)
    row["runtime_generator_sha256"] = observed_sha
    assert observed_sha == case["generator_sha256"], (case["task_id"], observed_sha)
    try:
        grid = module.generate(
            case["seed"],
            case["sample_index"],
            difficulty=case["difficulty"],
            **case["overrides"],
        )
    except Exception as exc:
        row.update({
            "outcome": "raised",
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "input_grid": None,
            "racket_output": None,
            "note": "Generation failed before an input existed, so no Racket output applies.",
        })
    else:
        row.update({
            "outcome": "returned",
            "shape": [len(grid), len(grid[0])],
            "input_grid": grid,
            "racket_output": None,
            "note": "This case probes override-key acceptance, not rule semantics.",
        })
    rows.append(row)

print(json.dumps({
    "schema": "arcpuzzles-audit-contract-repro-v1",
    "cwd": "packet_root",
    "argv": ["python3", "run_with_racket.py", "python3", "../checks/audit_contract_repro.py"],
    "cases": rows,
}, indent=2, sort_keys=True))
