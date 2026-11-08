#!/usr/bin/env python3
"""Bounded protected-Racket probe for the symmetric-key successor family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_edf83166c155_probe_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def _quadrant(component, height, width):
    return (
        "top" if component["top"] < height // 2 else "bottom",
        "left" if component["left"] < width // 2 else "right",
    )


def run_probe(seeds=(0, 1, 17), demo_counts=(2, 6)):
    checked = 0
    first_object_disagreements = 0
    first_successor_disagreements = 0
    key_regions = set()
    partner_regions = set()
    max_shape = [0, 0]
    with prototype.RacketBridge() as bridge:
        for seed in seeds:
            for demos in demo_counts:
                for mode in prototype.ALLOWED_MODES:
                    episode = prototype.make_episode(
                        seed, output_mode=mode, demos=demos, queries=4
                    )
                    for pair in episode["train"] + episode["test"]:
                        actual = prototype.execute_rule(
                            episode["program"], pair["input"], bridge=bridge
                        )
                        if actual != pair["output"]:
                            raise AssertionError(f"Racket mismatch for {seed=} {demos=} {mode=}")
                        h, w = len(pair["input"]), len(pair["input"][0])
                        max_shape = [max(max_shape[0], h), max(max_shape[1], w)]
                    if mode == "successor_of_symmetric":
                        for pair in episode["train"]:
                            grid = pair["input"]
                            objects = prototype.components(grid)
                            key = prototype.find_symmetric_component(grid)
                            partner = prototype.find_successor_component(grid, key)
                            key_regions.add(_quadrant(key, len(grid), len(grid[0])))
                            partner_regions.add(_quadrant(partner, len(grid), len(grid[0])))
                            first_object_disagreements += (
                                prototype.crop_component(grid, objects[0]) != pair["output"]
                            )
                            wanted = prototype.successor_color(objects[0]["color"])
                            hit = next((obj for obj in objects if obj["color"] == wanted), None)
                            shortcut = [] if hit is None else prototype.crop_component(grid, hit)
                            first_successor_disagreements += shortcut != pair["output"]
                    checked += 1
    expected = len(tuple(seeds)) * len(tuple(demo_counts)) * len(prototype.ALLOWED_MODES)
    if checked != expected:
        raise AssertionError("bounded episode coverage was incomplete")
    if first_object_disagreements < 12 or first_successor_disagreements < 12:
        raise AssertionError("shortcut-disagreement coverage was incomplete")
    if len(key_regions) != 4 or len(partner_regions) != 4:
        raise AssertionError("quadrant coverage was incomplete")
    return {
        "status": "pass",
        "task_id": prototype.TASK_ID,
        "settings": list(prototype.ALLOWED_MODES),
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "episodes_checked": checked,
        "first_object_shortcut_disagreements": first_object_disagreements,
        "first_successor_shortcut_disagreements": first_successor_disagreements,
        "key_quadrants": sorted("-".join(region) for region in key_regions),
        "partner_quadrants": sorted("-".join(region) for region in partner_regions),
        "max_input_shape": max_shape,
        "racket": {"backend": "racket", "protected": True},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = run_probe()
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
