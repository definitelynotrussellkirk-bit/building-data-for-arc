from __future__ import annotations

import json
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parents[2]
REPO = WORK / "repo"
sys.path.insert(0, str(REPO / "shared" / "runtime"))
from reviewer_support import load_selected_generator  # noqa: E402


def outcome(fn):
    try:
        value = fn()
    except Exception as exc:
        return {"status": "error", "type": type(exc).__name__, "message": str(exc)}
    if isinstance(value, list) and value and isinstance(value[0], list):
        return {
            "status": "returned",
            "height": len(value),
            "width": len(value[0]),
            "self_check": None,
        }
    return {"status": "returned", "value": value}


def run_eed():
    task = "eed263bf30fc"
    module, source, digest = load_selected_generator(task, root=REPO)
    cases = []
    specs = [
        ("easy_panel_n_8", lambda: module.generate(7, 11, difficulty="easy", panel_n=8)),
        ("medium_panel_n_8", lambda: module.generate(7, 11, difficulty="medium", panel_n=8)),
        ("hard_panel_n_8", lambda: module.generate(7, 11, difficulty="hard", panel_n=8)),
        ("unknown_override", lambda: module.generate(7, 11, difficulty="medium", bogus=1)),
        ("negative_sample_index", lambda: module.generate(7, -1, difficulty="medium")),
        ("boolean_sample_index", lambda: module.generate(7, True, difficulty="medium")),
    ]
    for name, fn in specs:
        result = outcome(fn)
        if result.get("status") == "returned" and "height" in result:
            grid = fn()
            result["self_check"] = module.self_check(grid)
            result["observed_panel_n"] = len(grid) // 2
        cases.append({"case": name, "outcome": result})
    report = {
        "schema": "arcpuzzles-audit-contract-reproducer-v1",
        "task_id": task,
        "generator_path": str(source.relative_to(REPO)),
        "generator_sha256": digest,
        "declared_axes": module.AXES,
        "cases": cases,
    }
    out = WORK / "checks" / "audit" / task / "contract_reproducer.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    return report


def run_19ba():
    task = "19ba16363b7f"
    module, source, digest = load_selected_generator(task, root=REPO)
    cases = []
    for name, value in [
        ("negative_sample_index", -1),
        ("boolean_true_sample_index", True),
        ("boolean_false_sample_index", False),
    ]:
        result = outcome(lambda value=value: module.generate(7, value, difficulty="medium"))
        if result.get("status") == "returned" and "height" in result:
            grid = module.generate(7, value, difficulty="medium")
            result["self_check"] = module.self_check(grid)
            result["schedule_profile"] = module.schedule_profile(7, value, "medium")
        cases.append({"case": name, "outcome": result})
    report = {
        "schema": "arcpuzzles-audit-contract-reproducer-v1",
        "task_id": task,
        "generator_path": str(source.relative_to(REPO)),
        "generator_sha256": digest,
        "cases": cases,
    }
    out = WORK / "checks" / "audit" / task / "contract_reproducer.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    return report


print(json.dumps({"eed263bf30fc": run_eed(), "19ba16363b7f": run_19ba()}, indent=2))
