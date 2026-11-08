#!/usr/bin/env python3
"""Episode-fixed phase-anchor prototype for ARC task bca4f37ec5e9.

``source`` is the canonical rule: the observed nonzero row block keeps its
original phase while being tiled over the canvas. ``grid_top`` is a nearby
variant that starts row zero with the first observed source row.  The input
grammar is shared, and every generated lesson contains direct evidence that
separates the two rules.
"""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any

TASK_ID = "bca4f37ec5e9"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DEFAULT = {"phase_anchor": "source"}
SETTINGS = (
    {"phase_anchor": "source"},
    {"phase_anchor": "grid_top"},
)
Grid = list[list[int]]

_GRID_TOP_PROGRAM = """(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (first-row (let loop
                                  ((r 0))
                                  (if (or
                                        (>= r hh)
                                        (for/or ((c (range 0 ww))) (!= (at g r c) 0)))
                                      r
                                      (loop (+ r 1)))))
                  (last-row (let loop
                                 ((r (- hh 1)))
                                 (if (or
                                       (< r 0)
                                       (for/or ((c (range 0 ww))) (!= (at g r c) 0)))
                                     r
                                     (loop (- r 1)))))
                  (period (+ 1 (- last-row first-row))))
             (build-grid hh
                         ww
                         (r c)
                         (at g
                             (+ first-row (remainder r period))
                             c))))))"""


def _canonical_program() -> str:
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if isinstance(source, str) and source.strip():
                    return source
    raise RuntimeError(f"canonical program not found for {TASK_ID}")


_CANONICAL_PROGRAM = _canonical_program()


def _integer(value: Any, lower: int, upper: int, name: str) -> int:
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be an exact integer in {lower}..{upper}")
    return value


def _settings(value: Any) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {"phase_anchor"}:
        raise ValueError("settings must contain exactly phase_anchor")
    anchor = value["phase_anchor"]
    if type(anchor) is not str or anchor not in ("source", "grid_top"):
        raise ValueError("phase_anchor must be 'source' or 'grid_top'")
    return {"phase_anchor": anchor}


def program(settings: Any) -> str:
    chosen = _settings(settings)
    return _CANONICAL_PROGRAM if chosen["phase_anchor"] == "source" else _GRID_TOP_PROGRAM


def digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _validate_grid(value: Any) -> tuple[Grid, int, int, list[list[int]]]:
    if type(value) is not list or not 2 <= len(value) <= 30:
        raise ValueError("grid must have 2..30 rows")
    if type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact ARC colors")
    grid = [row[:] for row in value]
    occupied = [r for r, row in enumerate(grid) if any(cell != 0 for cell in row)]
    if not occupied:
        raise ValueError("grid must contain a nonzero row block")
    first, last = occupied[0], occupied[-1]
    if occupied != list(range(first, last + 1)):
        raise ValueError("nonzero rows must form one contiguous block")
    if first == 0 or last == len(grid) - 1:
        raise ValueError("row block must have background above and below")
    period = last - first + 1
    if not 2 <= period <= 5:
        raise ValueError("row block height must be 2..5")
    rows = [row[:] for row in grid[first : last + 1]]
    colors = {cell for row in rows for cell in row if cell != 0}
    if len(colors) != 1 or any(not any(row) for row in rows):
        raise ValueError("row block must use one color and every row must be nonempty")
    if len({tuple(row) for row in rows}) < 2:
        raise ValueError("row block must contain at least two row masks")
    return grid, first, period, rows


def transform(grid: Any, settings: Any) -> Grid:
    chosen = _settings(settings)
    source, first, period, rows = _validate_grid(grid)
    if chosen["phase_anchor"] == "source":
        return [rows[(r - first) % period][:] for r in range(len(source))]
    return [rows[r % period][:] for r in range(len(source))]


def _rng(seed: int, label: str, index: int) -> random.Random:
    material = f"{TASK_ID}|{seed}|{label}|{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:16], "big"))


def _geometry(index: int, *, query: bool) -> tuple[int, int, int]:
    if query:
        profiles = ((12, 13, 2), (18, 21, 4), (24, 17, 5), (30, 30, 3))
        return profiles[index % 4]
    profiles = ((10, 12, 3), (13, 16, 2), (17, 15, 4), (20, 19, 5), (14, 18, 3), (22, 20, 4))
    return profiles[index % len(profiles)]


def _candidate(seed: int, index: int, *, query: bool = False) -> Grid:
    rng = _rng(seed, "query" if query else "demo", index)
    height, width, period = _geometry(index, query=query)
    legal = [first for first in range(1, height - period) if first % period != 0]
    if not legal:
        raise RuntimeError("no phase-distinguishing placement for selected geometry")
    first = legal[rng.randrange(len(legal))]
    color = rng.randrange(1, 10)
    grid = [[0] * width for _ in range(height)]
    masks: list[list[int]] = []
    for row_index in range(period):
        mask = [
            1
            if ((column * (row_index + 2) + row_index + rng.randrange(0, 5)) % 7) in (0, 1, 3)
            else 0
            for column in range(width)
        ]
        mask[(3 * row_index + index) % width] = 1
        if all(mask):
            mask[(row_index + 1) % width] = 0
        masks.append(mask)
    if len({tuple(mask) for mask in masks}) < 2:
        masks[-1][(index + 2) % width] ^= 1
        if not any(masks[-1]):
            masks[-1][0] = 1
    for offset, mask in enumerate(masks):
        grid[first + offset] = [color if cell else 0 for cell in mask]
    _validate_grid(grid)
    if transform(grid, SETTINGS[0]) == transform(grid, SETTINGS[1]):
        raise RuntimeError("candidate failed to distinguish phase settings")
    return grid


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    seed = _integer(seed, -(2**63), 2**63 - 1, "seed")
    demos = _integer(demos, 2, 6, "demos")
    queries = _integer(queries, 1, 8, "queries")
    chosen = _settings(settings)
    train = []
    test = []
    seen: set[str] = set()
    for index in range(demos):
        grid = _candidate(seed, index, query=False)
        key = digest(grid)
        if key in seen:
            raise RuntimeError("duplicate teaching input")
        seen.add(key)
        train.append({"input": grid, "output": transform(grid, chosen)})
    other = SETTINGS[1] if chosen == SETTINGS[0] else SETTINGS[0]
    if not any(transform(pair["input"], other) != pair["output"] for pair in train):
        raise RuntimeError("teaching set does not identify the phase setting")
    for index in range(queries):
        grid = _candidate(seed, index, query=True)
        key = digest(grid)
        if key in seen:
            raise RuntimeError("duplicate query input")
        seen.add(key)
        test.append({"input": grid, "output": transform(grid, chosen)})
    return {"train": train, "test": test, "program_solution": program(chosen)}


class RacketRunner:
    """One protected bundled-Racket process reused for a bounded batch."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge()
        identity = self.bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self.bridge.close()
            raise RuntimeError("live protected Racket backend required")
        self.cache: dict[str, str] = {}
        return self

    def __call__(self, source: str, grid: Any) -> Grid:
        from puzzle_generators.rule_wrap import wrap_rule

        clean, *_ = _validate_grid(grid)
        if source not in self.cache:
            self.cache[source] = wrap_rule(source)
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in clean
        ) + ")"
        return self.bridge.eval_text(f"({self.cache[source]} {literal})")

    def __exit__(self, *exc):
        self.bridge.close()


def certify(episode: dict[str, Any]) -> dict[str, Any]:
    chosen = next(setting for setting in SETTINGS if program(setting) == episode["program_solution"])
    with RacketRunner() as execute:
        for pair in episode["train"] + episode["test"]:
            actual = execute(episode["program_solution"], pair["input"])
            if actual != pair["output"]:
                raise ValueError("Racket label disagreement")
    other = SETTINGS[1] if chosen == SETTINGS[0] else SETTINGS[0]
    refuting = [
        index
        for index, pair in enumerate(episode["train"])
        if transform(pair["input"], other) != pair["output"]
    ]
    if not refuting:
        raise ValueError("demonstrations do not refute alternate phase setting")
    return {"racket_checked": True, "alternate_refuted_by_demos": refuting}
