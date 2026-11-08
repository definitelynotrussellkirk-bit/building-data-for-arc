#!/usr/bin/env python3
"""Reproduce the 4a2900e320da override and requested-frame audit."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Callable

PACKET_ROOT = Path(__file__).resolve().parents[3]
RUNTIME = PACKET_ROOT / "repo/shared/runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
SOURCE = PACKET_ROOT / "repo/generators/4a2900e320da/generator.py"
OUT = Path(__file__).with_name("reproduced.json")
EXPECTED_SHA256 = "1fca1521bd8530ea2fee9cc59860b6cd5e1b3194b980f081d8154351cd8f9777"


def load_module():
    spec = importlib.util.spec_from_file_location("task_4a2900e320da_audit", SOURCE)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SOURCE}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def capture(gen, fn: Callable[[], Any]) -> dict[str, Any]:
    try:
        grid = fn()
        return {
            "accepted": True,
            "shape": [len(grid), len(grid[0])],
            "self_check": gen.self_check(grid),
        }
    except Exception as exc:
        return {"accepted": False, "error": f"{type(exc).__name__}: {exc}"}


def frame_counts(gen, grid: list[list[int]]) -> tuple[int, int]:
    counts = {2: 0, 3: 0}
    for color, cells in gen._components_for_self_check(grid):
        if color in counts and gen._rect_frame_for_self_check(cells):
            counts[color] += 1
    return counts[2], counts[3]


def main() -> int:
    sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if sha != EXPECTED_SHA256:
        raise RuntimeError(f"source hash mismatch: {sha}")
    gen = load_module()
    contracts = {
        "easy_grid_h_18_declared_valid": capture(gen, lambda: gen.generate(0, 0, difficulty="easy", grid_h=18)),
        "easy_n_frame2_2_declared_valid": capture(gen, lambda: gen.generate(0, 0, difficulty="easy", n_frame2=2)),
        "hard_n_frame3_1_declared_valid": capture(gen, lambda: gen.generate(0, 0, difficulty="hard", n_frame3=1)),
        "unknown_key": capture(gen, lambda: gen.generate(0, 0, difficulty="medium", unknown_key=1)),
        "invalid_palette_size_5": capture(gen, lambda: gen.generate(0, 0, difficulty="medium", palette_size=5)),
        "invalid_texture": capture(gen, lambda: gen.generate(0, 0, difficulty="medium", texture="not_declared")),
    }
    frame_report: dict[str, Any] = {}
    requested_by_band = {"easy": (1, 1), "medium": (2, 2), "hard": (2, 2)}
    for difficulty, requested in requested_by_band.items():
        hist: Counter[tuple[int, int]] = Counter()
        errors: list[str] = []
        examples: list[dict[str, Any]] = []
        for seed in range(200):
            try:
                grid = gen.generate(
                    seed,
                    0,
                    difficulty=difficulty,
                    n_frame2=requested[0],
                    n_frame3=requested[1],
                )
                observed = frame_counts(gen, grid)
                hist[observed] += 1
                if observed != requested and len(examples) < 3:
                    examples.append({"seed": seed, "requested": list(requested), "observed": list(observed), "grid": grid})
            except Exception as exc:
                errors.append(f"seed {seed}: {type(exc).__name__}: {exc}")
        exact = hist[requested]
        draws = 200
        frame_report[difficulty] = {
            "seed_range": "0..199",
            "sample_index": 0,
            "draws": draws,
            "requested": list(requested),
            "exact": exact,
            "short": draws - exact - len(errors),
            "errors": errors,
            "observed_hist": {f"{a},{b}": n for (a, b), n in sorted(hist.items())},
            "examples": examples,
        }
    report = {
        "schema": "arc-audit-reproducer-v1",
        "target": "4a2900e320da",
        "source_sha256": sha,
        "classification": "reproduced override-contract defect and requested-count shortening defect",
        "contract_probes": contracts,
        "frame_count_probe": frame_report,
        "root_causes": [
            "Difficulty-specific draw_int bounds contradict the wider AXES domains.",
            "Unknown and undrawn overrides are not rejected.",
            "Generation returns when placed >= 1 instead of requiring every requested frame.",
        ],
        "generator_domain": "All 600 draws use advertised n_frame2/n_frame3 values for their selected difficulty; shortened outputs pass self_check because it checks only that some frame exists.",
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    ok = (
        contracts["easy_grid_h_18_declared_valid"]["accepted"] is False
        and contracts["easy_n_frame2_2_declared_valid"]["accepted"] is False
        and contracts["hard_n_frame3_1_declared_valid"]["accepted"] is False
        and contracts["unknown_key"]["accepted"] is True
        and contracts["invalid_palette_size_5"]["accepted"] is True
        and contracts["invalid_texture"]["accepted"] is True
        and frame_report["easy"]["exact"] == 21
        and frame_report["medium"]["exact"] == 0
        and frame_report["hard"]["exact"] == 24
    )
    print(json.dumps({
        "status": "pass" if ok else "fail",
        "easy": {k: frame_report["easy"][k] for k in ("exact", "short")},
        "medium": {k: frame_report["medium"][k] for k in ("exact", "short")},
        "hard": {k: frame_report["hard"][k] for k in ("exact", "short")},
    }, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
