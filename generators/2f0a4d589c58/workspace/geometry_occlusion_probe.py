#!/usr/bin/env python3
"""Measure whether geometry alone predicts the crossing-bars occluder.

The task rule depends on the observed overlap color. A training distribution is
shortcut-prone when a rival can ignore that overlap and infer the front bar from
thickness/placement geometry. This probe evaluates that rival over consecutive
three-demo lessons and records whether counterfactual geometry twins occur.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

TASK_ID = "2f0a4d589c58"
BANDS = ("easy", "medium", "hard")

# The pre-repair six-phase schedule assigned one fixed occluder to each geometry.
# This rival deliberately ignores the visible overlap and uses that correlation.
GEOMETRY_OCCLUDER_LOOKUP = {
    (1, 1, "center", "center"): "horizontal",
    (1, 1, "top", "right"): "vertical",
    (2, 1, "bottom", "left"): "horizontal",
    (1, 2, "center", "center"): "vertical",
    (3, 2, "top", "right"): "horizontal",
    (2, 2, "bottom", "left"): "vertical",
}
PAIR_AXES = (
    "grid_h",
    "grid_w",
    "horizontal_thickness",
    "vertical_thickness",
    "horizontal_position",
    "vertical_position",
    "horizontal_color",
    "vertical_color_offset",
)


def _load_generator(path: Path):
    repo_root = path.resolve().parents[2]
    runtime = repo_root / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    spec = importlib.util.spec_from_file_location("geometry_probe_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _geometry_key(info: dict[str, Any]) -> tuple[Any, ...]:
    return (
        info["horizontal_thickness"],
        info["vertical_thickness"],
        info["horizontal_position"],
        info["vertical_position"],
    )


def geometry_only_rival(module, grid: list[list[int]]) -> list[list[int]]:
    """Apply the old distribution shortcut, ignoring the overlap's actual color."""
    info = module._analyze(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    predicted_occluder = GEOMETRY_OCCLUDER_LOOKUP.get(
        _geometry_key(info), "horizontal"
    )
    predicted_back_color = (
        info["vertical_color"]
        if predicted_occluder == "horizontal"
        else info["horizontal_color"]
    )
    output = copy.deepcopy(info["grid"])
    for row in info["horizontal_rows"]:
        for col in info["vertical_cols"]:
            output[row][col] = predicted_back_color
    return output


def _pair_signature(module, grid: list[list[int]]) -> tuple[Any, ...]:
    observed = module.observe_overrides(grid)
    return tuple(observed[name] for name in PAIR_AXES)


def probe(generator_path: Path, lessons_per_band: int) -> dict[str, Any]:
    module = _load_generator(generator_path)
    source = generator_path.read_bytes()
    report: dict[str, Any] = {
        "schema": "arc-crossing-bars-geometry-shortcut-probe-v1",
        "task_id": TASK_ID,
        "generator_path": str(generator_path),
        "generator_sha256": hashlib.sha256(source).hexdigest(),
        "version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "lessons_per_band": lessons_per_band,
        "lesson_shape": {"demos": 3, "queries": 1},
        "rival": "geometry_only_occluder_lookup_from_pre_repair_schedule",
        "bands": {},
    }

    for band_index, band in enumerate(BANDS):
        grid_count = 0
        rival_agreements = 0
        rival_survives_demo_windows = 0
        windows_refuting_rival = 0
        windows_with_counterfactual_demo_pair = 0
        unique_inputs: set[tuple[tuple[int, ...], ...]] = set()

        for start in range(lessons_per_band):
            seed = 910_000 + band_index * 10_000 + start
            sample_start = 113 + start
            episodes = []
            for offset in range(4):
                grid = module.generate(
                    seed, sample_start + offset, difficulty=band
                )
                truth = module.rule_mirror(grid)
                rival = geometry_only_rival(module, grid)
                observed = module.observe_overrides(grid)
                episodes.append(
                    {
                        "grid": grid,
                        "truth": truth,
                        "rival": rival,
                        "observed": observed,
                        "pair_signature": _pair_signature(module, grid),
                    }
                )
                grid_count += 1
                rival_agreements += int(rival == truth)
                unique_inputs.add(tuple(tuple(row) for row in grid))

            demos = episodes[:3]
            survives = all(item["rival"] == item["truth"] for item in demos)
            rival_survives_demo_windows += int(survives)
            windows_refuting_rival += int(not survives)

            has_counterfactual_pair = any(
                left["pair_signature"] == right["pair_signature"]
                and left["observed"]["occluder"]
                != right["observed"]["occluder"]
                for index, left in enumerate(demos)
                for right in demos[index + 1 :]
            )
            windows_with_counterfactual_demo_pair += int(has_counterfactual_pair)

        report["bands"][band] = {
            "grid_count": grid_count,
            "unique_input_count": len(unique_inputs),
            "rival_truth_agreements": rival_agreements,
            "rival_accuracy": rival_agreements / grid_count,
            "lesson_windows": lessons_per_band,
            "rival_survives_all_demos": rival_survives_demo_windows,
            "windows_refuting_rival": windows_refuting_rival,
            "windows_with_counterfactual_demo_pair": (
                windows_with_counterfactual_demo_pair
            ),
        }

    report["pass_condition"] = {
        "all_windows_refute_rival": all(
            row["windows_refuting_rival"] == lessons_per_band
            for row in report["bands"].values()
        ),
        "all_windows_have_counterfactual_demo_pair": all(
            row["windows_with_counterfactual_demo_pair"] == lessons_per_band
            for row in report["bands"].values()
        ),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--generator",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "generator.py",
    )
    parser.add_argument("--lessons", type=int, default=100)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.lessons <= 0:
        parser.error("--lessons must be positive")

    report = probe(args.generator.resolve(), args.lessons)
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if all(report["pass_condition"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
