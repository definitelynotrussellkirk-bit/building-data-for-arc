#!/usr/bin/env python3
"""Prototype: choose chamber seed priority direction once per episode.

This module is deliberately separate from the selected canonical generator and
Racket authority.  ``left_to_right`` is the canonical/default setting;
``right_to_left`` is a proposed variant that preserves wall parsing while
reversing which present legend colour wins.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

ALLOWED_PRIORITY_DIRECTIONS = ("left_to_right", "right_to_left")
DEFAULT_PRIORITY_DIRECTION = "left_to_right"
PROTOTYPE_VERSION = "1.0.0"
TASK_ID = "e03758508612"
ROOT = Path(__file__).resolve().parent
TASK_ROOT = ROOT.parents[1]
RULE_DIR = ROOT / "rules"
_CARDINALS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _validate_direction(priority_direction: str) -> str:
    if type(priority_direction) is not str or priority_direction not in ALLOWED_PRIORITY_DIRECTIONS:
        raise ValueError(
            "priority_direction must be one of "
            f"{ALLOWED_PRIORITY_DIRECTIONS}, got {priority_direction!r}"
        )
    return priority_direction


def choose_priority_direction(seed: int) -> str:
    """Choose one hidden parameter value for the complete episode."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    return ALLOWED_PRIORITY_DIRECTIONS[seed % len(ALLOWED_PRIORITY_DIRECTIONS)]


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be literal ARC colour integers 0..9")
    return len(grid), width


def _chambers(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = _validate_grid(grid)
    seen: set[tuple[int, int]] = set()
    rooms: list[list[tuple[int, int]]] = []
    for row in range(1, height):
        for column in range(width):
            start = (row, column)
            if start in seen or grid[row][column] == 8:
                continue
            stack = [start]
            seen.add(start)
            room: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                room.append((r, c))
                for dr, dc in _CARDINALS:
                    nr, nc = r + dr, c + dc
                    neighbour = (nr, nc)
                    if (
                        1 <= nr < height
                        and 0 <= nc < width
                        and neighbour not in seen
                        and grid[nr][nc] != 8
                    ):
                        seen.add(neighbour)
                        stack.append(neighbour)
            rooms.append(sorted(room))
    return rooms


def python_fill(grid: list[list[int]], priority_direction: str) -> list[list[int]]:
    """Independent mirror used as a secondary assertion around Racket runs."""
    direction = _validate_direction(priority_direction)
    _validate_grid(grid)
    priority = [value for value in grid[0] if value not in (0, 8)]
    if direction == "right_to_left":
        priority.reverse()
    output = deepcopy(grid)
    for room in _chambers(grid):
        present = {grid[row][column] for row, column in room}
        winner = next((value for value in priority if value in present), None)
        if winner is not None:
            for row, column in room:
                output[row][column] = winner
    return output


def racket_program(priority_direction: str) -> str:
    """Materialize a standalone exact Racket program for one parameter value."""
    direction = _validate_direction(priority_direction)
    reverse_literal = "#t" if direction == "right_to_left" else "#f"
    return f'''#lang racket
(require json racket/list)

(define REVERSE-PRIORITY? {reverse_literal})
(define DIRS (list (cons -1 0) (cons 1 0) (cons 0 -1) (cons 0 1)))

(define (grid-rows grid) (length grid))
(define (grid-cols grid) (length (first grid)))
(define (cell grid row column) (list-ref (list-ref grid row) column))
(define (inside-room-domain? grid row column)
  (and (<= 1 row) (< row (grid-rows grid))
       (<= 0 column) (< column (grid-cols grid))))

(define (solve grid)
  (define base-priority
    (filter (lambda (value) (and (not (= value 0)) (not (= value 8))))
            (first grid)))
  (define priority (if REVERSE-PRIORITY? (reverse base-priority) base-priority))
  (define seen (make-hash))
  (define fills (make-hash))

  (define (room-from start)
    (hash-set! seen start #t)
    (let loop ([queue (list start)] [cells '()])
      (if (empty? queue)
          (reverse cells)
          (let* ([point (first queue)]
                 [row (car point)]
                 [column (cdr point)]
                 [new-neighbours
                  (for/list ([delta (in-list DIRS)]
                             #:do [(define next-row (+ row (car delta)))
                                   (define next-column (+ column (cdr delta)))
                                   (define next-point (cons next-row next-column))]
                             #:when (and (inside-room-domain? grid next-row next-column)
                                         (not (= (cell grid next-row next-column) 8))
                                         (not (hash-has-key? seen next-point))))
                    (hash-set! seen next-point #t)
                    next-point)])
            (loop (append (rest queue) new-neighbours) (cons point cells))))))

  (for* ([row (in-range 1 (grid-rows grid))]
         [column (in-range (grid-cols grid))])
    (define start (cons row column))
    (when (and (not (= (cell grid row column) 8))
               (not (hash-has-key? seen start)))
      (define room (room-from start))
      (define present
        (remove-duplicates
         (for/list ([point (in-list room)])
           (cell grid (car point) (cdr point)))))
      (define winner
        (for/first ([value (in-list priority)] #:when (member value present)) value))
      (when winner
        (for ([point (in-list room)])
          (hash-set! fills point winner)))))

  (for/list ([row (in-range (grid-rows grid))])
    (for/list ([column (in-range (grid-cols grid))])
      (define point (cons row column))
      (if (hash-has-key? fills point)
          (hash-ref fills point)
          (cell grid row column)))))

(define input-grid (read-json))
(write-json (solve input-grid))
(newline)
'''


def rule_path(priority_direction: str) -> Path:
    direction = _validate_direction(priority_direction)
    return RULE_DIR / f"priority_{direction}.rkt"


def racket_sha256(priority_direction: str) -> str:
    return hashlib.sha256(racket_program(priority_direction).encode("utf-8")).hexdigest()


def _load_selected_generator():
    path = TASK_ROOT / "generator.py"
    spec = importlib.util.spec_from_file_location("e03758508612_parametric_base", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load selected generator: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _episode_inputs(seed: int) -> list[list[list[int]]]:
    generator = _load_selected_generator()
    requests = (
        {"grid_h": 9, "grid_w": 11, "layout": "grid", "seed_pattern": "double"},
        {"grid_h": 9, "grid_w": 9, "layout": "horizontal", "seed_pattern": "double"},
        {"grid_h": 10, "grid_w": 12, "layout": "vertical", "seed_pattern": "double"},
    )
    return [
        generator.generate(seed + index * 997, index, difficulty="medium", **request)
        for index, request in enumerate(requests)
    ]


def build_episode(
    seed: int,
    priority_direction: str | None = None,
) -> dict[str, Any]:
    """Build two labelled demonstrations and one private labelled query."""
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    direction = (
        choose_priority_direction(seed)
        if priority_direction is None
        else _validate_direction(priority_direction)
    )
    pairs = [
        {"input": deepcopy(grid), "output": python_fill(grid, direction)}
        for grid in _episode_inputs(seed)
    ]
    return {
        "schema": "arcpuzzles-parametric-priority-direction-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter": {"priority_direction": direction},
        "train": pairs[:2],
        "test": pairs[2:],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Mask the hidden parameter and query answer for a public challenge."""
    return {
        "schema": "arcpuzzles-parametric-priority-direction-public-v1",
        "train": deepcopy(episode["train"]),
        "test": [{"input": deepcopy(pair["input"])} for pair in episode["test"]],
    }


def run_racket(priority_direction: str, grid: list[list[int]]) -> list[list[int]]:
    """Execute the exact retained Racket setting on one grid."""
    direction = _validate_direction(priority_direction)
    _validate_grid(grid)
    executable = shutil.which("racket")
    if executable is None:
        raise RuntimeError("racket executable not found; run through review.py run")
    path = rule_path(direction)
    expected = racket_program(direction)
    if not path.is_file() or path.read_text() != expected:
        raise RuntimeError(f"retained Racket source does not match materialized setting: {path}")
    proc = subprocess.run(
        [executable, str(path)],
        input=json.dumps(grid, separators=(",", ":")) + "\n",
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Racket failed ({proc.returncode}): {proc.stderr.strip()}")
    result = json.loads(proc.stdout)
    _validate_grid(result)
    return result


def build_evidence(seed: int) -> dict[str, Any]:
    """Execute both settings and test their episode-level distinguishability."""
    source_sha = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    settings: dict[str, Any] = {}
    for direction in ALLOWED_PRIORITY_DIRECTIONS:
        alternative = next(
            value for value in ALLOWED_PRIORITY_DIRECTIONS if value != direction
        )
        episode = build_episode(seed, priority_direction=direction)
        executions = []
        for split in ("train", "test"):
            for pair_index, pair in enumerate(episode[split]):
                actual = run_racket(direction, pair["input"])
                alternative_output = run_racket(alternative, pair["input"])
                mirror = python_fill(pair["input"], direction)
                if actual != pair["output"] or actual != mirror:
                    raise AssertionError(
                        f"Racket/Python/episode mismatch for {direction} {split}[{pair_index}]"
                    )
                executions.append(
                    {
                        "split": split,
                        "pair_index": pair_index,
                        "input": pair["input"],
                        "racket_output": actual,
                        "alternative_priority_direction": alternative,
                        "alternative_racket_output": alternative_output,
                        "settings_disagree": actual != alternative_output,
                    }
                )
        demo_results = [
            entry["settings_disagree"] for entry in executions if entry["split"] == "train"
        ]
        settings[direction] = {
            "priority_direction": direction,
            "is_canonical_default": direction == DEFAULT_PRIORITY_DIRECTION,
            "racket_path": str(rule_path(direction).relative_to(ROOT)),
            "racket_text": racket_program(direction),
            "racket_sha256": racket_sha256(direction),
            "episode": episode,
            "public_challenge": public_challenge(episode),
            "executions": executions,
            "all_pairs_match_racket": True,
            "every_demo_refutes_alternative_setting": bool(demo_results) and all(demo_results),
        }
    return {
        "schema": "arcpuzzles-parametric-priority-direction-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "seed": seed,
        "parameter": {
            "name": "priority_direction",
            "allowed_values": list(ALLOWED_PRIORITY_DIRECTIONS),
            "canonical_default": DEFAULT_PRIORITY_DIRECTION,
            "selection": "ALLOWED_PRIORITY_DIRECTIONS[seed % 2], once per episode",
            "dependent_input_constraint": (
                "each retained demonstration uses two distinct legend-colour seeds per "
                "chamber so opposite priority directions produce different labels"
            ),
        },
        "prototype_source_sha256": source_sha,
        "settings": settings,
        "limits": [
            "Prototype only: the selected canonical generator and RULE_HASH remain unchanged.",
            "Bounded evidence covers two settings at one seed, not production approval.",
            "The demonstrations distinguish only the declared opposite-direction rival.",
        ],
    }


def _write_rule_files() -> None:
    RULE_DIR.mkdir(parents=True, exist_ok=True)
    for direction in ALLOWED_PRIORITY_DIRECTIONS:
        rule_path(direction).write_text(racket_program(direction))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--write-public", type=Path)
    args = parser.parse_args()
    _write_rule_files()
    evidence = build_evidence(args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    if args.write_public is not None:
        args.write_public.mkdir(parents=True, exist_ok=True)
        for direction, setting in evidence["settings"].items():
            path = args.write_public / f"priority_{direction}_public.json"
            path.write_text(
                json.dumps(setting["public_challenge"], indent=2, sort_keys=True) + "\n"
            )
    print(
        json.dumps(
            {
                "status": evidence["status"],
                "seed": evidence["seed"],
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
