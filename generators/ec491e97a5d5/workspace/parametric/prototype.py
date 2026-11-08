#!/usr/bin/env python3
"""Standalone border-thickness prototype for ec491e97a5d5.

This is deliberately separate from the selected canonical generator and rule.
``border_thickness`` is chosen once per episode from {1, 2}; the canonical
setting is 1.  Prototype inputs use one solid rectangle per foreground colour,
with every side at least five, so the two settings are visibly distinguishable.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import shutil
import subprocess
from pathlib import Path
from typing import Any


TASK_ID = "ec491e97a5d5"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_BORDER_THICKNESSES = (1, 2)
DEFAULT_BORDER_THICKNESS = 1
ROOT = Path(__file__).resolve().parent
RULE_DIR = ROOT / "rules"


def validate_border_thickness(value: int) -> int:
    if type(value) is not int or value not in ALLOWED_BORDER_THICKNESSES:
        raise ValueError(
            "border_thickness must be one of "
            f"{ALLOWED_BORDER_THICKNESSES}, got {value!r}"
        )
    return value


def choose_border_thickness(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    return ALLOWED_BORDER_THICKNESSES[seed % len(ALLOWED_BORDER_THICKNESSES)]


def _validate_grid(grid: list[list[int]]) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be exact integer ARC colours 0..9")
    return len(grid), width


def _boxes_by_colour(grid: list[list[int]]) -> dict[int, tuple[int, int, int, int]]:
    height, width = _validate_grid(grid)
    cells: dict[int, list[tuple[int, int]]] = {}
    for row in range(height):
        for col in range(width):
            colour = grid[row][col]
            if colour:
                cells.setdefault(colour, []).append((row, col))
    if not cells:
        raise ValueError("prototype inputs require foreground rectangles")
    boxes: dict[int, tuple[int, int, int, int]] = {}
    for colour, coords in cells.items():
        rows = [row for row, _ in coords]
        cols = [col for _, col in coords]
        top, bottom = min(rows), max(rows)
        left, right = min(cols), max(cols)
        if bottom - top + 1 < 5 or right - left + 1 < 5:
            raise ValueError("every prototype rectangle side must be at least five")
        if len(coords) != (bottom - top + 1) * (right - left + 1):
            raise ValueError("each foreground colour must form one solid rectangle")
        if any(
            grid[row][col] != colour
            for row in range(top, bottom + 1)
            for col in range(left, right + 1)
        ):
            raise ValueError("each foreground colour must form one solid rectangle")
        boxes[colour] = (top, left, bottom, right)
    return boxes


def python_hollow(grid: list[list[int]], border_thickness: int) -> list[list[int]]:
    """Independent Python mirror used as a secondary assertion around Racket."""
    thickness = validate_border_thickness(border_thickness)
    height, width = _validate_grid(grid)
    output = [[0] * width for _ in range(height)]
    for colour, (top, left, bottom, right) in _boxes_by_colour(grid).items():
        for row in range(top, bottom + 1):
            for col in range(left, right + 1):
                edge_distance = min(
                    row - top,
                    bottom - row,
                    col - left,
                    right - col,
                )
                if edge_distance < thickness:
                    output[row][col] = colour
    return output


def racket_program(border_thickness: int) -> str:
    thickness = validate_border_thickness(border_thickness)
    return f'''#lang racket
(require json racket/list)

(define BORDER-THICKNESS {thickness})

(define grid (read-json))
(define height (length grid))
(define width (length (first grid)))
(define colours
  (remove-duplicates
   (filter positive? (apply append grid))))
(define output
  (for/vector ([r (in-range height)])
    (make-vector width 0)))

(define (cell r c)
  (list-ref (list-ref grid r) c))

(for ([colour (in-list colours)])
  (define coords
    (for*/list ([r (in-range height)]
                [c (in-range width)]
                #:when (= (cell r c) colour))
      (cons r c)))
  (define rows (map car coords))
  (define cols (map cdr coords))
  (define top (apply min rows))
  (define bottom (apply max rows))
  (define left (apply min cols))
  (define right (apply max cols))
  (for* ([r (in-range top (+ bottom 1))]
         [c (in-range left (+ right 1))]
         #:when (< (min (- r top)
                        (- bottom r)
                        (- c left)
                        (- right c))
                   BORDER-THICKNESS))
    (vector-set! (vector-ref output r) c colour)))

(write-json
 (for/list ([row (in-vector output)])
   (vector->list row)))
(newline)
'''


def rule_path(border_thickness: int) -> Path:
    return RULE_DIR / f"border_thickness_{validate_border_thickness(border_thickness)}.rkt"


def racket_sha256(border_thickness: int) -> str:
    return hashlib.sha256(racket_program(border_thickness).encode("utf-8")).hexdigest()


def materialize_rules() -> None:
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    for thickness in ALLOWED_BORDER_THICKNESSES:
        rule_path(thickness).write_text(racket_program(thickness))


def _paint(grid, top, left, rect_h, rect_w, colour):
    for row in range(top, top + rect_h):
        for col in range(left, left + rect_w):
            grid[row][col] = colour


def _episode_inputs(seed: int) -> list[list[list[int]]]:
    rng = random.Random(seed)
    palettes = [rng.sample(range(1, 10), 2) for _ in range(3)]
    specifications = [
        (12, 16, (1, 1, 5, 5), (6, 9, 5, 6)),
        (13, 17, (1, 2, 6, 5), (7, 9, 5, 7)),
        (14, 18, (2, 1, 5, 8), (6, 12, 7, 5)),
    ]
    inputs = []
    for (height, width, first, second), (colour_a, colour_b) in zip(specifications, palettes):
        grid = [[0] * width for _ in range(height)]
        _paint(grid, *first, colour_a)
        _paint(grid, *second, colour_b)
        _boxes_by_colour(grid)  # assert the prototype grammar now, not later.
        inputs.append(grid)
    return inputs


def build_episode(seed: int, border_thickness: int | None = None) -> dict[str, Any]:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    thickness = (
        choose_border_thickness(seed)
        if border_thickness is None
        else validate_border_thickness(border_thickness)
    )
    pairs = []
    for grid in _episode_inputs(seed):
        pairs.append(
            {
                "input": copy.deepcopy(grid),
                "output": python_hollow(grid, thickness),
                "border_thickness": thickness,
            }
        )
    return {
        "schema": "arcpuzzles-parametric-hollow-frame-episode-v1",
        "prototype_version": PROTOTYPE_VERSION,
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {"border_thickness": thickness},
        "train": pairs[:2],
        "test": pairs[2:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "arcpuzzles-parametric-hollow-frame-public-v1",
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def run_racket(border_thickness: int, grid: list[list[int]]) -> list[list[int]]:
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError("racket executable not found; run through review.py run")
    materialize_rules()
    path = rule_path(border_thickness)
    expected_text = racket_program(border_thickness)
    if path.read_text() != expected_text:
        raise RuntimeError(f"retained Racket source mismatch: {path}")
    process = subprocess.run(
        [executable, str(path)],
        input=json.dumps(grid, separators=(",", ":")) + "\n",
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if process.returncode != 0:
        raise RuntimeError(
            f"Racket failed ({process.returncode}): {process.stderr.strip()}"
        )
    result = json.loads(process.stdout)
    _validate_grid(result)
    return result


def build_evidence(seed: int) -> dict[str, Any]:
    materialize_rules()
    source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    settings: dict[str, Any] = {}
    for thickness in ALLOWED_BORDER_THICKNESSES:
        alternative = 3 - thickness
        episode = build_episode(seed, border_thickness=thickness)
        executed_pairs = []
        for split in ("train", "test"):
            for pair_index, pair in enumerate(episode[split]):
                actual = run_racket(thickness, pair["input"])
                alternative_output = run_racket(alternative, pair["input"])
                mirror = python_hollow(pair["input"], thickness)
                if actual != pair["output"] or actual != mirror:
                    raise AssertionError(
                        f"Racket/Python/episode mismatch for thickness={thickness} "
                        f"{split}[{pair_index}]"
                    )
                executed_pairs.append(
                    {
                        "split": split,
                        "pair_index": pair_index,
                        "input": pair["input"],
                        "racket_output": actual,
                        "alternative_border_thickness": alternative,
                        "alternative_racket_output": alternative_output,
                        "settings_disagree": actual != alternative_output,
                    }
                )
        settings[str(thickness)] = {
            "border_thickness": thickness,
            "is_canonical_default": thickness == DEFAULT_BORDER_THICKNESS,
            "racket_path": str(rule_path(thickness).relative_to(ROOT)),
            "racket_text": racket_program(thickness),
            "racket_sha256": racket_sha256(thickness),
            "episode": episode,
            "public_challenge": public_challenge(episode),
            "executed_pairs": executed_pairs,
            "all_pairs_match_racket": True,
            "every_demo_refutes_alternative_setting": all(
                item["settings_disagree"]
                for item in executed_pairs
                if item["split"] == "train"
            ),
        }
    return {
        "schema": "arcpuzzles-parametric-hollow-frame-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {
            "name": "border_thickness",
            "allowed_values": list(ALLOWED_BORDER_THICKNESSES),
            "canonical_default": DEFAULT_BORDER_THICKNESS,
            "selection": "ALLOWED_BORDER_THICKNESSES[seed % 2], once per episode",
            "input_constraints": (
                "one solid rectangle per foreground colour; every side at least five"
            ),
        },
        "prototype_source_sha256": source_sha,
        "settings": settings,
        "limits": [
            "Prototype only; the selected generator and canonical rule remain thickness 1.",
            "Bounded execution evidence covers two settings at one seed.",
            "Distinct-colour rectangles make the standalone Racket concise; production repeated-colour object semantics are not generalized here.",
            "The two demonstrations refute only the retained thickness alternative, not all possible rules.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path)
    args = parser.parse_args()

    evidence = build_evidence(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for key, setting in evidence["settings"].items():
            (args.write_public / f"border_thickness_{key}_public.json").write_text(
                json.dumps(setting["public_challenge"], indent=2, sort_keys=True) + "\n"
            )

    print(
        json.dumps(
            {
                "status": evidence["status"],
                "seed": seed if (seed := evidence["seed"]) is not None else args.seed,
                "settings": {
                    key: {
                        "racket_sha256": value["racket_sha256"],
                        "all_pairs_match_racket": value["all_pairs_match_racket"],
                        "every_demo_refutes_alternative_setting": value[
                            "every_demo_refutes_alternative_setting"
                        ],
                    }
                    for key, value in evidence["settings"].items()
                },
                "out": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
