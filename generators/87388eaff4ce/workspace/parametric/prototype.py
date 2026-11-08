#!/usr/bin/env python3
"""Proposed task-local parametric extension for 87388eaff4ce.

This module is intentionally separate from the selected per-puzzle generator.
It chooses one hidden tie-break setting per complete episode and emits the exact
Racket program shared by every demonstration and query in that episode.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve()
TASK_DIR = HERE.parents[2]
GENERATOR_PATH = TASK_DIR / "generator.py"

PARAMETER_NAME = "tie_break"
ALLOWED_SETTINGS = ("color_asc", "color_desc")
DEFAULT_SETTING = "color_asc"
PARAMETER_CONSTRAINTS = {
    "color_asc": "equal-height objects are ordered by increasing color (canonical)",
    "color_desc": "equal-height objects are ordered by decreasing color (proposed)",
}


def _load_generator():
    spec = importlib.util.spec_from_file_location(
        "parametric_base_87388eaff4ce", GENERATOR_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load selected generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_GEN = _load_generator()


def _validate_setting(setting: str) -> None:
    if setting not in ALLOWED_SETTINGS:
        raise ValueError(
            f"{PARAMETER_NAME} must be one of {ALLOWED_SETTINGS}, got {setting!r}"
        )


def _program_body(setting: str) -> str:
    _validate_setting(setting)
    color_cmp = "<" if setting == "color_asc" else ">"
    return f"""(let* ((items (sort (map (lambda (obj)
                             (let ((crop (subgrid g (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj))))
                               (list (rows crop) (obj-color obj) crop)))
                           (objects g 0))
                      (lambda (a b)
                        (if (= (first a) (first b))
                            ({color_cmp} (second a) (second b))
                            (> (first a) (first b))))))
         (shapes (map third items))
         (out-h (+ (apply + (map rows shapes)) (max 0 (- (length shapes) 1))))
         (out-w (apply max (map cols shapes))))
    (let pack ((remaining shapes) (top 0) (out (empty-grid out-h out-w 0)))
      (if (empty? remaining)
          out
          (let* ((shape (first remaining))
                 (next (for*/fold ((acc out))
                                   ((r (in-range (rows shape)))
                                    (c (in-range (cols shape))))
                         (let ((v (at shape r c)))
                           (if (not (= v 0)) (set-cell acc (+ top r) c v) acc)))))
            (pack (rest remaining) (+ top (rows shape) 1) next)))))"""


def program_for(setting: str) -> str:
    """Return the exact executable Racket program for one episode setting."""
    return f"(rule! (lambda (g)\n{_program_body(setting)}))"


def normalized_program_hash(setting: str) -> str:
    normalized = " ".join(program_for(setting).split()).encode()
    return hashlib.sha256(normalized).hexdigest()


def solve(grid, setting: str = DEFAULT_SETTING):
    """Python mirror used only to materialize and test the prototype."""
    _validate_setting(setting)
    if setting == "color_asc":
        key = lambda obj: (-obj.height, obj.color)
    else:
        key = lambda obj: (-obj.height, -obj.color)
    return _GEN._pack(grid, key)


def select_setting(seed: int) -> str:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    return ALLOWED_SETTINGS[seed % len(ALLOWED_SETTINGS)]


def generate_episode(
    seed: int,
    *,
    difficulty: str = "medium",
    setting: str | None = None,
) -> dict[str, Any]:
    """Build a 3-demo/1-query episode with one rule setting fixed throughout."""
    selected = select_setting(seed) if setting is None else setting
    _validate_setting(selected)
    pairs = []
    for index in range(4):
        input_seed = (seed * 1_000_003 + index * 97) & 0xFFFFFFFF
        grid = _GEN.generate(input_seed, index, difficulty=difficulty)
        intended = solve(grid, selected)
        alternative = next(value for value in ALLOWED_SETTINGS if value != selected)
        if intended == solve(grid, alternative):
            raise RuntimeError("episode input failed to distinguish tie-break settings")
        pairs.append({"input": grid, "output": intended})
    program = program_for(selected)
    return {
        "train": pairs[:3],
        "test": pairs[3:],
        "program": program,
        "meta": {
            "prototype": True,
            "task_id": _GEN.TASK_ID,
            "seed": seed,
            "difficulty": difficulty,
            PARAMETER_NAME: selected,
            "allowed_settings": list(ALLOWED_SETTINGS),
            "default_setting": DEFAULT_SETTING,
            "program_sha256": hashlib.sha256(program.encode()).hexdigest(),
            "normalized_program_sha256": normalized_program_hash(selected),
            "input_constraint": (
                "every pair has equal-height objects whose color order changes the output"
            ),
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Remove the hidden setting, program, and query answers."""
    return {
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=40)
    parser.add_argument("--setting", choices=ALLOWED_SETTINGS)
    parser.add_argument("--public", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    episode = generate_episode(args.seed, setting=args.setting)
    payload = public_challenge(episode) if args.public else episode
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
