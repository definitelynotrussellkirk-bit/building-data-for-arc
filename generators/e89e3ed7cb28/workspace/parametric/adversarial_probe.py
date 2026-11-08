#!/usr/bin/env python3
"""Bounded protected-Racket probe for the bottom-survivor family."""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

_HOME = Path(__file__).resolve().parent
_SPEC = importlib.util.spec_from_file_location(
    "parametric_e89e3ed7cb28_probe_prototype", _HOME / "prototype.py"
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError("cannot load task-local prototype")
prototype = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(prototype)


def run_probe(seeds=(0, 1, 17), demo_counts=(2, 6)):
    checked = 0
    shortcut_disagreements = 0
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
                    if mode == "modal_survivor_color":
                        for pair in episode["train"]:
                            raw_mode = prototype.whole_grid_modal_color(pair["input"])
                            shortcut = prototype.filter_to_color(pair["input"], raw_mode)
                            shortcut_disagreements += shortcut != pair["output"]
                    checked += 1
    expected = len(tuple(seeds)) * len(tuple(demo_counts)) * 2
    if checked != expected or shortcut_disagreements < expected // 2:
        raise AssertionError("bounded shortcut coverage was incomplete")
    return {
        "status": "pass",
        "task_id": prototype.TASK_ID,
        "settings": list(prototype.ALLOWED_MODES),
        "seeds": list(seeds),
        "demo_counts": list(demo_counts),
        "episodes_checked": checked,
        "shortcut_disagreements": shortcut_disagreements,
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
