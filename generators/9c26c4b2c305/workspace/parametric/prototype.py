"""Parametric alignment-policy family for ARC task 9c26c4b2c305.

The input grammar is shared across settings.  Only the panel-alignment policy
changes: canonical alignment, unconditional bottom reflection, or a genuine
count-derived gate that reflects exactly when the top panel is more occupied.
"""
from __future__ import annotations

from functools import cache
import hashlib
import json
import random
from pathlib import Path
from typing import Any

from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "9c26c4b2c305"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)

Grid = list[list[int]]
POLICIES = (
    "aligned",
    "reflect_bottom",
    "top_heavier_reflect_bottom",
)
DEFAULT_POLICY = "aligned"
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 8
_DEMO_WIDTHS = (4, 4, 7, 14, 9, 13)
_QUERY_WIDTHS = (18, 21, 27, 30, 16, 23, 26, 29)

_REFLECT_PROGRAM = """(rule! (lambda (g)
         (let ((w (cols g)))
           (grid-from-fn 4
                         w
                         (lambda (r c)
                           (if (or (!= 0 (at g r c)) (!= 0 (at g (+ r 5) (- w c 1)))) 3 0))))))"""

_GATED_PROGRAM = """(rule! (lambda (g)
         (let* ((w (cols g))
                (top-count
                 (for/sum ((r (in-range 4)))
                   (for/sum ((c (in-range w)))
                     (if (!= 0 (at g r c)) 1 0))))
                (bottom-count
                 (for/sum ((r (in-range 4)))
                   (for/sum ((c (in-range w)))
                     (if (!= 0 (at g (+ r 5) c)) 1 0))))
                (reflect? (> top-count bottom-count)))
           (grid-from-fn 4
                         w
                         (lambda (r c)
                           (if (or (!= 0 (at g r c))
                                   (!= 0 (at g (+ r 5) (if reflect? (- w c 1) c))))
                               3
                               0))))))"""


@cache
def _generator():
    return load_selected_generator(TASK_ID, root=ROOT)[0]


def _validate_policy(policy: Any) -> str:
    if type(policy) is not str:
        raise TypeError("alignment policy must be an exact string")
    if policy not in POLICIES:
        raise ValueError(f"unknown alignment policy: {policy!r}")
    return policy


@cache
def canonical_program() -> str:
    matches: list[dict[str, Any]] = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            matches.append(row)
    if len(matches) != 1:
        raise ValueError(f"expected one canonical row for {TASK_ID}, found {len(matches)}")
    source = matches[0].get("program_solution")
    if type(source) is not str or not source:
        raise ValueError(f"canonical row for {TASK_ID} has no program_solution")
    return source


def program_for(policy: str) -> str:
    policy = _validate_policy(policy)
    if policy == "aligned":
        return canonical_program()
    if policy == "reflect_bottom":
        return _REFLECT_PROGRAM
    return _GATED_PROGRAM


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer")
    if not 0 <= seed < 2**63:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_count(value: Any, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")
    return value


def _make_input(
    seed: int,
    *,
    split: str,
    slot: int,
    width: int,
    top_heavy: bool,
) -> Grid:
    generator = _generator()
    profile = "top_heavy" if top_heavy else "bottom_heavy"
    palette_names = tuple(generator.PALETTE_PROFILES)
    if split == "demo" and slot < 2:
        # Keep the two minimum teaching examples palette-matched so color cues
        # cannot stand in for the count-derived alignment decision.
        palette_name = palette_names[seed % len(palette_names)]
    else:
        offset = slot - 1 if split == "demo" else slot + 2
        palette_name = palette_names[(seed + offset) % len(palette_names)]
    top_color, bottom_color, separator_color = generator.PALETTES[palette_name]
    labels: list[str] = []
    for relation, count in generator._relation_counts(width, profile).items():
        labels.extend([relation] * count)

    for attempt in range(256):
        material = (
            f"{TASK_ID}|alignment-policy-v1|{seed}|{split}|{slot}|{attempt}|"
            f"{width}|{profile}|{palette_name}"
        ).encode("utf-8")
        rng = random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))
        shuffled = labels[:]
        rng.shuffle(shuffled)
        grid = [[0 for _ in range(width)] for _ in range(9)]
        grid[4] = [separator_color for _ in range(width)]
        for index, relation in enumerate(shuffled):
            row, col = divmod(index, width)
            if relation[0] == "1":
                grid[row][col] = top_color
            if relation[1] == "1":
                grid[5 + row][col] = bottom_color
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError("constructed invalid panel input: " + "; ".join(errors))
        if apply_policy(grid, "aligned") != apply_policy(grid, "reflect_bottom"):
            return grid
    raise RuntimeError(
        f"could not construct reflection-sensitive {split} input {slot} at width {width}"
    )


def episode_inputs(seed: int, demos: int, queries: int) -> list[Grid]:
    seed = _validate_seed(seed)
    demos = _validate_count(demos, "demos", MIN_DEMOS, MAX_DEMOS)
    queries = _validate_count(queries, "queries", MIN_QUERIES, MAX_QUERIES)
    rows = [
        _make_input(
            seed,
            split="demo",
            slot=slot,
            width=_DEMO_WIDTHS[slot],
            top_heavy=slot % 2 == 0,
        )
        for slot in range(demos)
    ]
    rows.extend(
        _make_input(
            seed,
            split="query",
            slot=slot,
            width=_QUERY_WIDTHS[slot],
            top_heavy=slot % 2 == 1,
        )
        for slot in range(queries)
    )
    frozen = {tuple(tuple(row) for row in grid) for grid in rows}
    if len(frozen) != len(rows):
        raise AssertionError("episode inputs must be distinct")
    return rows


def apply_policy(grid: Grid, policy: str) -> Grid:
    policy = _validate_policy(policy)
    info, errors = _generator()._analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    normalized = info["grid"]
    width = info["grid_w"]
    top_count = sum(bool(normalized[row][col]) for row in range(4) for col in range(width))
    bottom_count = sum(
        bool(normalized[5 + row][col]) for row in range(4) for col in range(width)
    )
    reflect = policy == "reflect_bottom" or (
        policy == "top_heavier_reflect_bottom" and top_count > bottom_count
    )
    return [
        [
            3
            if normalized[row][col]
            or normalized[5 + row][width - 1 - col if reflect else col]
            else 0
            for col in range(width)
        ]
        for row in range(4)
    ]


def generate_episode(
    seed: int,
    alignment_policy: str,
    demos: int,
    queries: int,
) -> dict[str, Any]:
    alignment_policy = _validate_policy(alignment_policy)
    inputs = episode_inputs(seed, demos, queries)
    train_inputs = inputs[:demos]
    test_inputs = inputs[demos:]
    return {
        "train": [
            {"input": grid, "output": apply_policy(grid, alignment_policy)}
            for grid in train_inputs
        ],
        "test": [
            {"input": grid, "output": apply_policy(grid, alignment_policy)}
            for grid in test_inputs
        ],
        "program_solution": program_for(alignment_policy),
    }
