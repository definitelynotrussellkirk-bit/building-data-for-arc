from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "repo"
OUT = ROOT / "checks" / "audit"


def load(task: str):
    path = REPO / "generators" / task / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dims(grid: Any) -> list[int]:
    return [len(grid), len(grid[0]) if grid else 0]


def outcome(call):
    try:
        value = call()
        return {"accepted": True, "dims": dims(value), "grid": value}
    except Exception as exc:  # evidence: preserve exact public exception contract
        return {"accepted": False, "exception_type": type(exc).__name__, "message": str(exc)}


# 9e2802ee78bd: advertised controls and validator degenerates.
task = "9e2802ee78bd"
g, path = load(task)
seed, sample_index = 20261020, 7
base = g.generate(seed, sample_index)
override_cases = {
    "grid_h_30": {"grid_h": 30},
    "grid_w_30": {"grid_w": 30},
    "panel_h_8": {"panel_h": 8},
    "panel_w_2": {"panel_w": 2},
    "palette_size_5": {"palette_size": 5},
    "unknown_typo_axis": {"panel_height_typo": 8},
}
case_results = {}
for name, kwargs in override_cases.items():
    result = outcome(lambda kwargs=kwargs: g.generate(seed, sample_index, **kwargs))
    if result.get("accepted"):
        result["identical_to_baseline"] = result["grid"] == base
        del result["grid"]
    case_results[name] = result

validator_cases = {
    "ordinary": base,
    "no_separator": g.generate(seed, sample_index, texture="no_separator"),
    "blank_panel": g.generate(seed, sample_index, texture="blank_panel"),
    "full_grid": g.generate(seed, sample_index, texture="full_grid"),
    "all_zero_4x9": [[0] * 9 for _ in range(4)],
}
validator_results = {
    name: {"dims": dims(grid), "errors": g.self_check(grid)}
    for name, grid in validator_cases.items()
}
report_9e = {
    "schema": "audit_witness/1",
    "task_id": task,
    "generator_sha256": sha256(path),
    "version": getattr(g, "VERSION", None),
    "seed": seed,
    "sample_index": sample_index,
    "baseline_dims": dims(base),
    "advertised_axis_cases": case_results,
    "validator_cases": validator_results,
    "finding": (
        "Five advertised controls and one unknown typo override are accepted but do not change "
        "the generated grid; self_check also returns no errors for no-separator, blank-panel, "
        "full-grid, and all-zero inputs."
    ),
}
out = OUT / task / "contract_witness.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report_9e, indent=2, sort_keys=True) + "\n")

# b636461d71b8: scalar boundary probes, separate from semantic-gate receipt.
task = "b636461d71b8"
g, path = load(task)
scalar_cases = {
    "seed_bool": (True, 0, {}),
    "seed_float": (1.0, 0, {}),
    "seed_string": ("1", 0, {}),
    "sample_index_bool": (1, True, {}),
    "sample_index_float": (1, 1.0, {}),
    "sample_index_negative": (1, -1, {}),
}
scalar_results = {}
for name, (seed_value, index_value, kwargs) in scalar_cases.items():
    result = outcome(lambda seed_value=seed_value, index_value=index_value, kwargs=kwargs: g.generate(seed_value, index_value, **kwargs))
    if result.get("accepted"):
        del result["grid"]
    scalar_results[name] = result
report_b = {
    "schema": "audit_witness/1",
    "task_id": task,
    "generator_sha256": sha256(path),
    "version": getattr(g, "VERSION", None),
    "rule_hash": getattr(g, "RULE_HASH", None),
    "scalar_call_cases": scalar_results,
    "semantic_gate_evidence": "checks/audit/b636461d71b8/combined/checks/b636461d71b8_audit_semantic_gate.log",
    "finding": (
        "The semantic gate reports 9/12 sampled lessons unidentifiable. The public call "
        "boundary also accepts bool/float/string seeds and bool/float/negative sample indices."
    ),
}
out = OUT / task / "strict_scalar_witness.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report_b, indent=2, sort_keys=True) + "\n")

print(json.dumps({"9e2802ee78bd": report_9e, "b636461d71b8": report_b}, indent=2, sort_keys=True))
