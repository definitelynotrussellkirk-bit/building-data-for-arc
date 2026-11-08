"""Bounded adversarial audit for the e282a664f807 native family."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Callable

_HOME = Path(__file__).resolve().parent
_ADAPTER_PATH = _HOME / "adapter.py"
_SPEC = importlib.util.spec_from_file_location(
    "_audit_e282_" + hashlib.sha256(str(_ADAPTER_PATH).encode()).hexdigest(),
    _ADAPTER_PATH,
)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("cannot load adjacent adapter")
ADAPTER = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = ADAPTER
_SPEC.loader.exec_module(ADAPTER)

Grid = list[list[int]]
Rival = Callable[[Grid], Grid]


def _slope(grid: Grid) -> str:
    colors = ADAPTER._pair_colors(grid)
    color = colors[0]
    a, b = ADAPTER._positions(grid, color)
    return "positive" if (a[0] - b[0]) * (a[1] - b[1]) > 0 else "negative"


def _positive_slope_only(grid: Grid) -> Grid:
    if _slope(grid) != "positive":
        return [[0 for _ in row] for row in grid]
    return ADAPTER.predict(grid, "single_box")


def _preserve_distractors(grid: Grid) -> Grid:
    output = [row[:] for row in grid]
    colors = ADAPTER._pair_colors(grid)
    ADAPTER._fill_bbox(output, ADAPTER._positions(grid, colors[0]), colors[0])
    return output


def _outline_only(grid: Grid) -> Grid:
    colors = ADAPTER._pair_colors(grid)
    color = colors[0]
    points = ADAPTER._positions(grid, color)
    r1, r2 = sorted((points[0][0], points[1][0]))
    c1, c2 = sorted((points[0][1], points[1][1]))
    out = [[0 for _ in row] for row in grid]
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            if r in (r1, r2) or c in (c1, c2):
                out[r][c] = color
    return out


def _fill_all_without_selection(grid: Grid) -> Grid:
    return ADAPTER.intermediate(grid)


def _fits(rival: Rival, pairs: list[dict[str, Grid]]) -> bool:
    return all(rival(pair["input"]) == pair["output"] for pair in pairs)


def run(seed_count: int = 64) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    survivors: list[dict[str, Any]] = []
    counts = Counter()
    selected_colors: set[int] = set()
    selected_anchors: set[tuple[int, int]] = set()
    base_slopes: set[str] = set()

    # The repaired ordinary sampler must expose both corner orientations in every
    # two-example window, including the two preflight difficulty values.
    generator_path = _HOME.parents[1] / "generator.py"
    gen_spec = importlib.util.spec_from_file_location("_base_e282_audit", generator_path)
    if gen_spec is None or gen_spec.loader is None:
        raise RuntimeError("cannot load base generator")
    generator = importlib.util.module_from_spec(gen_spec)
    gen_spec.loader.exec_module(generator)
    for difficulty in (None, "medium"):
        for seed in range(min(seed_count, 32)):
            window = [generator.generate(seed, i, difficulty=difficulty) for i in range(2)]
            slopes = {_slope(grid) for grid in window}
            base_slopes.update(slopes)
            counts["base_windows"] += 1
            if slopes != {"positive", "negative"}:
                findings.append({"seed": seed, "difficulty": difficulty, "finding": "base_slope_window", "slopes": sorted(slopes)})

    for seed in range(seed_count):
        for policy in ("single_box", "largest_completed"):
            setting = {"completion_policy": policy}
            episode = ADAPTER.generate(seed, setting, 3, 4)
            short = ADAPTER.generate(seed, setting, 2, 1)
            long = ADAPTER.generate(seed, setting, 6, 4)
            counts["episodes"] += 1
            if short["train"] != long["train"][:2] or short["test"] != long["test"][:1]:
                findings.append({"seed": seed, "policy": policy, "finding": "prefix_instability"})
            pairs = episode["train"] + episode["test"]
            if len({repr(pair["input"]) for pair in pairs}) != len(pairs):
                findings.append({"seed": seed, "policy": policy, "finding": "duplicate_inputs"})
            for pair in pairs:
                counts["pairs"] += 1
                expected = ADAPTER.predict(pair["input"], policy)
                if expected != pair["output"]:
                    findings.append({"seed": seed, "policy": policy, "finding": "label_mismatch"})
                other = "largest_completed" if policy == "single_box" else "single_box"
                if ADAPTER.predict(pair["input"], other) == pair["output"]:
                    findings.append({"seed": seed, "policy": policy, "finding": "setting_not_distinguished"})
                else:
                    counts["setting_differences"] += 1
                if policy == "largest_completed":
                    areas = ADAPTER.completed_areas(ADAPTER.intermediate(pair["input"]))
                    selected = max(areas, key=lambda item: item[1])[0]
                    selected_colors.add(selected)
                    points = [(r, c) for r, row in enumerate(pair["output"]) for c, value in enumerate(row) if value == 9]
                    selected_anchors.add(min(points))
                    if ADAPTER.wrong_order_predict(pair["input"]) == pair["output"]:
                        findings.append({"seed": seed, "policy": policy, "finding": "wrong_order_matches"})
                    else:
                        counts["wrong_order_refutations"] += 1
            last = episode["test"][-1]["input"]
            if (len(last), len(last[0])) != (30, 30):
                findings.append({"seed": seed, "policy": policy, "finding": "missing_30x30"})
            elif sum(value != 0 for row in last for value in row) < 80:
                findings.append({"seed": seed, "policy": policy, "finding": "thin_30x30"})
            else:
                counts["substantive_30x30"] += 1

            rivals: dict[str, Rival]
            if policy == "single_box":
                rivals = {
                    "positive_slope_only": _positive_slope_only,
                    "preserve_distractors": _preserve_distractors,
                    "outline_only": _outline_only,
                }
            else:
                rivals = {
                    "wrong_order_min_pair": ADAPTER.wrong_order_predict,
                    "fill_all_without_selection": _fill_all_without_selection,
                    "single_box": lambda grid: ADAPTER.predict(grid, "single_box"),
                }
            for name, rival in rivals.items():
                if _fits(rival, episode["train"]):
                    survivors.append({"seed": seed, "policy": policy, "rival": name})

    if len(selected_colors) < 3:
        findings.append({"finding": "selected_color_does_not_vary", "values": sorted(selected_colors)})
    if len(selected_anchors) < 3:
        findings.append({"finding": "selected_location_does_not_vary", "values": sorted(selected_anchors)})

    status = "passed" if not findings and not survivors else "failed"
    return {
        "schema": "arcpuzzles-parametric-self-audit-v1",
        "task_id": "e282a664f807",
        "status": status,
        "seed_count": seed_count,
        "counts": dict(sorted(counts.items())),
        "base_slopes": sorted(base_slopes),
        "selected_colors": sorted(selected_colors),
        "selected_anchor_count": len(selected_anchors),
        "surviving_rivals": survivors,
        "findings": findings,
        "limitations": [
            "Finite named-rival audit; it does not prove unrestricted uniqueness or learning benefit.",
            "Protected Racket execution is established separately by authoring preflight and causal replay.",
        ],
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    report = run(args.seeds)
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
