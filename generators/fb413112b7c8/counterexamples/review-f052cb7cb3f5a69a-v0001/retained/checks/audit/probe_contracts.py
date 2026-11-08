#!/usr/bin/env python3
"""Read-only source-bound probes for the two assigned audit targets."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

REPO = Path.cwd().resolve()
TARGETS = ("fb413112b7c8", "cf6ef609da0d")


def load(task_id: str):
    path = REPO / "generators" / task_id / "generator.py"
    spec = importlib.util.spec_from_file_location(f"audit_{task_id}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def grid_sha(grid) -> str:
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def run_case(gen, label, args, kwargs):
    row = {"label": label, "args": list(args), "kwargs": kwargs}
    try:
        grid = gen.generate(*args, **kwargs)
    except Exception as exc:
        row.update({"status": "rejected", "exception": type(exc).__name__, "message": str(exc)})
        return row
    row.update({
        "status": "accepted",
        "shape": [len(grid), len(grid[0])],
        "grid_sha256": grid_sha(grid),
        "self_check_errors": list(gen.self_check(grid)),
    })
    try:
        row["observed"] = gen.observe_overrides(grid)
    except Exception as exc:
        row["observe_error"] = f"{type(exc).__name__}: {exc}"
    return row


def main() -> int:
    out = {
        "schema": "arcpuzzles-audit-contract-probes-v1",
        "cwd": str(REPO),
        "argv": sys.argv,
        "targets": {},
    }

    fb, fb_path = load("fb413112b7c8")
    fb_cases = [
        run_case(fb, "bool_seed", (True, 0), {}),
        run_case(fb, "string_seed", ("7", 0), {}),
        run_case(fb, "bool_sample_index", (0, True), {}),
        run_case(fb, "string_sample_index", (0, "3"), {}),
        run_case(fb, "negative_sample_index", (0, -1), {}),
        run_case(fb, "unknown_difficulty", (0, 0), {"difficulty": "legendary"}),
        run_case(fb, "float_support_inset", (0, 1), {"difficulty": "hard", "support_inset": 3.75}),
        run_case(fb, "bool_grid_h", (0, 1), {"grid_h": True}),
    ]
    palette_rows = []
    for palette in fb.PALETTE_KINDS:
        grid = fb.generate(
            1234,
            1,
            difficulty="medium",
            grid_h=12,
            grid_w=14,
            palette_kind=palette,
            total_cells=7,
            n_pieces=3,
            n_distinct_colors=3,
            gap_rows=2,
            support_inset=1,
        )
        non_support_colors = sorted({v for row in grid for v in row if v not in (0, 9)})
        palette_rows.append({
            "requested_palette_kind": palette,
            "grid_sha256": grid_sha(grid),
            "non_support_colors": non_support_colors,
            "observed": fb.observe_overrides(grid),
            "observer_reports_palette_kind": "palette_kind" in fb.observe_overrides(grid),
        })
    out["targets"]["fb413112b7c8"] = {
        "generator_path": str(fb_path.relative_to(REPO)),
        "generator_sha256": sha(fb_path),
        "declared_rule_hash": getattr(fb, "RULE_HASH", None),
        "invalid_call_probes": fb_cases,
        "advertised_axes": list(fb.AXES),
        "palette_observability_probe": palette_rows,
        "portable_test_preflight_evidence": "checks/audit/fb413112b7c8-audit-stage/result.json",
    }

    cf, cf_path = load("cf6ef609da0d")
    cf_cases = [
        run_case(cf, "bool_seed", (True, 0), {}),
        run_case(cf, "string_seed", ("7", 0), {}),
        run_case(cf, "bool_sample_index", (0, True), {}),
        run_case(cf, "string_sample_index", (0, "3"), {}),
        run_case(cf, "negative_sample_index", (0, -1), {}),
        run_case(cf, "unknown_difficulty", (0, 0), {"difficulty": "legendary"}),
    ]
    out["targets"]["cf6ef609da0d"] = {
        "generator_path": str(cf_path.relative_to(REPO)),
        "generator_sha256": sha(cf_path),
        "declared_rule_hash": getattr(cf, "RULE_HASH", None),
        "invalid_call_probes": cf_cases,
        "advertised_axes": list(cf.AXES),
    }

    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("../checks/audit/contract-probes.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(output_path),
        "targets": {task: row["generator_sha256"] for task, row in out["targets"].items()},
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
