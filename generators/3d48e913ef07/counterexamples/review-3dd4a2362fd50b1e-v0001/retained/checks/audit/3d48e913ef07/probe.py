#!/usr/bin/env python3
"""Contract audit probe for 3d48e913ef07 without modifying its source."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
PACKET = HERE.parents[2]
GEN_PATH = PACKET / "repo" / "generators" / "3d48e913ef07" / "generator.py"
OUT_PATH = HERE / "contract_probe.json"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("audit_generator_3d48", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture(fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        value = fn()
    except Exception as exc:  # precise evidence is serialized below
        return {"ok": False, "exception_type": type(exc).__name__, "message": str(exc)}
    return {"ok": True, "value": value}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    module = load_module(GEN_PATH)
    base_args = (1729, 4)
    easy_grid_h_boundary = capture(
        lambda: module.generate(*base_args, difficulty="easy", grid_h=18)
    )
    easy_grid_w_boundary = capture(
        lambda: module.generate(*base_args, difficulty="easy", grid_w=20)
    )
    hard_n_objs_boundary = capture(
        lambda: module.generate(*base_args, difficulty="hard", n_objs=5)
    )
    unknown_override = capture(
        lambda: module.generate(*base_args, difficulty="medium", definitely_unknown="sentinel")
    )

    comparisons = {}
    for name, left, right in (
        ("palette_kind_warm_vs_cool", {"palette_kind": "warm"}, {"palette_kind": "cool"}),
        ("texture_warm_vs_cool", {"texture": "warm"}, {"texture": "cool"}),
        ("density_sparse_vs_omitted", {"density": "sparse"}, {}),
    ):
        same_count = 0
        samples = []
        for seed in range(8):
            g_left = module.generate(seed, seed, difficulty="medium", **left)
            g_right = module.generate(seed, seed, difficulty="medium", **right)
            same = g_left == g_right
            same_count += int(same)
            samples.append({"seed": seed, "sample_index": seed, "equal": same})
        comparisons[name] = {
            "equal_outputs": same_count,
            "denominator": len(samples),
            "samples": samples,
        }

    degenerate = {}
    for texture in module.DEGENERATE_TEXTURES:
        grid = module.generate(0, 0, difficulty="medium", texture=texture)
        degenerate[texture] = {
            "self_check_errors": module.self_check(
                grid, difficulty="medium", meta={"texture": texture}
            ),
            "palette_markers": sum(cell not in (0, 3) for row in grid for cell in row[:1]),
        }

    report = {
        "schema": "arcpuzzles-generator-contract-audit-v1",
        "task_id": "3d48e913ef07",
        "generator_sha256": sha256(GEN_PATH),
        "declared_axes": module.AXES,
        "legal_boundary_override_probes": {
            "easy_grid_h_18": easy_grid_h_boundary,
            "easy_grid_w_20": easy_grid_w_boundary,
            "hard_n_objs_5": hard_n_objs_boundary,
        },
        "unknown_override_probe": unknown_override,
        "dead_axis_comparisons": comparisons,
        "degenerate_self_check_probes": degenerate,
        "conclusion": (
            "Reproduced contract defects: multiple values declared legal by AXES are rejected by "
            "difficulty-local draw ranges; palette_kind, helpful texture, and density do not affect "
            "pixels in 8/8 paired probes; and an unknown override is accepted rather than rejected."
        ),
        "command": [
            "python3", "run_with_racket.py", "python3",
            "../checks/audit/3d48e913ef07/probe.py"
        ],
        "cwd": "packet_root",
    }
    if report["generator_sha256"] != "5f92643d05a2150f787a1eca9717345f60ed6cf2064e703f63adea4ff1656c01":
        raise SystemExit("unexpected generator bytes")
    required_failures = [easy_grid_h_boundary, easy_grid_w_boundary, hard_n_objs_boundary]
    if any(item["ok"] for item in required_failures):
        raise SystemExit("expected legal AXES boundary override to fail, but one succeeded")
    if not unknown_override["ok"]:
        raise SystemExit("unknown override was rejected; expected reproduced acceptance defect")
    if any(item["equal_outputs"] != item["denominator"] for item in comparisons.values()):
        raise SystemExit("one purported dead-axis comparison changed pixels")
    OUT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "output": str(OUT_PATH),
        "boundary_failures": required_failures,
        "unknown_override_accepted": unknown_override["ok"],
        "dead_axis_equalities": {
            key: f"{value['equal_outputs']}/{value['denominator']}"
            for key, value in comparisons.items()
        },
    }, indent=2))


if __name__ == "__main__":
    main()
