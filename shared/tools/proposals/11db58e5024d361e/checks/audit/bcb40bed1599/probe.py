#!/usr/bin/env python3
"""Reproduce ignored-axis and advertised-range defects in bcb40bed1599."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
TASK = "bcb40bed1599"
SOURCE = ROOT / "WORK" / "repo" / "generators" / TASK / "generator.py"
SPEC = importlib.util.spec_from_file_location("audited_bcb40bed1599", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def main() -> int:
    paired = {
        "palette_kind_warm_vs_cool": ({"palette_kind": "warm"}, {"palette_kind": "cool"}),
        "blob_choice_0_vs_2": ({"blob_choice": 0}, {"blob_choice": 2}),
        "helpful_texture_warm_vs_cool": ({"texture": "warm"}, {"texture": "cool"}),
    }
    paired_results = {}
    for name, (left_overrides, right_overrides) in paired.items():
        identical = 0
        examples = []
        for seed in range(100):
            left = GEN.generate(seed, 0, difficulty="medium", **left_overrides)
            right = GEN.generate(seed, 0, difficulty="medium", **right_overrides)
            identical += left == right
            if seed == 0:
                examples.append({
                    "seed": seed,
                    "left_overrides": left_overrides,
                    "right_overrides": right_overrides,
                    "left": left,
                    "right": right,
                })
        paired_results[name] = {
            "seeds": [0, 99],
            "pairs": 100,
            "identical_pairs": identical,
            "first_pair": examples[0],
        }

    boundary_cases = []
    for band in ("easy", "medium", "hard"):
        for overrides in (
            {"grid_h": 3},
            {"grid_h": 10},
            {"grid_w": 6},
            {"grid_w": 14},
        ):
            try:
                grid = GEN.generate(0, 0, difficulty=band, **overrides)
            except Exception as exc:
                boundary_cases.append({
                    "difficulty": band,
                    "overrides": overrides,
                    "status": "rejected",
                    "error": f"{type(exc).__name__}: {exc}",
                })
            else:
                boundary_cases.append({
                    "difficulty": band,
                    "overrides": overrides,
                    "status": "accepted",
                    "shape": [len(grid), len(grid[0])],
                })

    warm = GEN.generate(0, 0, difficulty="medium", palette_kind="warm")
    cool = GEN.generate(0, 0, difficulty="medium", palette_kind="cool")
    assert warm == cool
    assert GEN.self_check(warm) == []
    report = {
        "schema": "arcpuzzles-adversarial-audit-v1",
        "task_id": TASK,
        "finding": "advertised exact controls are ignored or reject advertised-valid values",
        "generator_version": GEN.VERSION,
        "generator_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "paired_default_probe": paired_results,
        "advertised_boundary_probe": {
            "cases": len(boundary_cases),
            "rejected": sum(case["status"] == "rejected" for case in boundary_cases),
            "details": boundary_cases,
        },
        "selected_input": warm,
        "selected_input_self_check_errors": GEN.self_check(warm),
        "interpretation": (
            "palette_kind, blob_choice, and nondegenerate texture never influence "
            "generation: every paired medium draw was byte-identical. AXES advertises "
            "grid_h=3..10 and grid_w=6..14, but each difficulty calls draw_int with "
            "a narrower band range, rejecting all tested advertised endpoints."
        ),
        "limits": "Finite paired seeds 0..99 at sample_index 0; source inspection confirms the three named controls are not read by the ordinary generation path.",
    }
    out = Path(__file__).with_name("probe.json")
    out.write_text(json.dumps(report, indent=2) + "\n")
    Path(__file__).with_name("input.json").write_text(
        json.dumps({"input": warm}, indent=2) + "\n"
    )
    print(json.dumps({
        "generator_sha256": report["generator_sha256"],
        "identical_pairs": {name: value["identical_pairs"] for name, value in paired_results.items()},
        "boundary_rejected": report["advertised_boundary_probe"]["rejected"],
        "boundary_cases": report["advertised_boundary_probe"]["cases"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
