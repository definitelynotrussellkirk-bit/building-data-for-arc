#!/usr/bin/env python3
"""Rebuild concrete AXES/override contract failures for 3511f98c7b84."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = "3511f98c7b84"
EXPECTED_GENERATOR_SHA256 = "bd16b2fc7e86fcbe69994d2fb70da49935fef7c1efd731f750321ee8ca29d1fc"
HERE = Path(__file__).resolve().parent
WORK = HERE.parents[2]
REPO = WORK / "repo"


def load_generator():
    helper = REPO / "shared/runtime/reviewer_support.py"
    spec = importlib.util.spec_from_file_location("selected_support_3511", helper)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {helper}")
    support = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = support
    spec.loader.exec_module(support)
    return support.load_selected_generator(TASK, root=REPO)


def sha_json(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def main() -> None:
    module, source_path, source_sha = load_generator()
    if source_sha != EXPECTED_GENERATOR_SHA256:
        raise RuntimeError(f"selected source changed: {source_sha}")

    base = {"seed": 0, "sample_index": 3, "difficulty": "easy"}
    default_grid = module.generate(**base, palette_kind="default")
    warm_grid = module.generate(**base, palette_kind="warm")
    default_errors = module.self_check(default_grid, difficulty="easy", meta={})
    warm_errors = module.self_check(warm_grid, difficulty="easy", meta={})
    if default_errors or warm_errors:
        raise RuntimeError(f"lawful override probe failed self_check: {default_errors}, {warm_errors}")
    if default_grid != warm_grid:
        raise RuntimeError("palette_kind counterexample no longer reproduces")

    red_count_error = None
    try:
        module.generate(**base, red_count=5)
    except Exception as error:  # Exact public generate() rejection is the evidence.
        red_count_error = f"{type(error).__name__}: {error}"
    if red_count_error is None:
        raise RuntimeError("declared red_count=5 easy-band rejection no longer reproduces")

    report_path = WORK / "checks/audit/3511f98c7b84-override/checks/3511f98c7b84_audit_override_results.json"
    report = json.loads(report_path.read_text())
    if report["source_sha256"] != source_sha or report["status"] != "FAIL":
        raise RuntimeError("override report is not bound to the expected failing source")
    palette_findings = [
        row["message"] for row in report["findings"]
        if row.get("category") == "axis_effect"
        and row.get("axis") == "palette_kind"
        and "all 90 band/seed sweeps" in row.get("message", "")
    ]
    if not palette_findings:
        raise RuntimeError("aggregate inert palette_kind finding missing")

    payload = {
        "schema": "arcpuzzles-audit-override-counterexample-v1",
        "task_id": TASK,
        "generator_path": str(source_path.relative_to(REPO)),
        "generator_sha256": source_sha,
        "declared_axes": module.AXES,
        "probe": base,
        "reproduced_defects": [
            {
                "kind": "advertised_axis_inert",
                "axis": "palette_kind",
                "calls": [
                    {**base, "overrides": {"palette_kind": "default"}},
                    {**base, "overrides": {"palette_kind": "warm"}},
                ],
                "outputs_equal": True,
                "output_sha256": sha_json(default_grid),
                "self_check_errors": [default_errors, warm_errors],
                "aggregate_override_evidence": palette_findings[0],
                "note": "The canonical rule uses fixed semantic colors 2, 3, and 8, so palette_kind should be removed/diagnostic or explicitly rejected rather than advertised as an effective control.",
            },
            {
                "kind": "declared_valid_override_rejected_by_band",
                "axis": "red_count",
                "call": {**base, "overrides": {"red_count": 5}},
                "declared_valid": module.AXES["red_count"]["valid"],
                "error": red_count_error,
                "note": "AXES declares 1..5 globally, but the easy branch passes draw_int bounds 1..2 and has no declared incompatibility.",
            },
        ],
        "grids": {
            "palette_kind_default": default_grid,
            "palette_kind_warm": warm_grid,
        },
        "override_report": "checks/audit/3511f98c7b84-override/checks/3511f98c7b84_audit_override_results.json",
        "reproduction": {
            "cwd": "repo",
            "argv": ["python3", "../checks/audit/3511f98c7b84/build_override_counterexample.py"],
        },
    }
    out = HERE / "override_counterexample.json"
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps({
        "task_id": TASK,
        "generator_sha256": source_sha,
        "palette_outputs_equal": True,
        "red_count_error": red_count_error,
        "counterexample": str(out),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
