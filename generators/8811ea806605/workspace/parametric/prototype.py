"""Opt-in column gravity and full-row clearing, with order taught per episode.

Python outputs are claims. Native qualification and the local evidence builder
independently execute the returned Racket programs through the protected runtime.
The approved production generator is not imported or changed.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import random

from reviewer_support import public_challenge_bytes


HOME = Path(__file__).resolve().parent
MODES = ("fall", "fall_then_clear", "clear_then_fall")
DEFAULT = {"mode": "fall"}

_COMPOSED = """(rule!
 ;; Blue cells fall independently to the bottom of their columns.
 ;; A line clear removes all completely blue rows, preserving the order of
 ;; other rows and adding black rows at the top. The episode fixes the order.
 (lambda (g)
   (let ()
     (define (fall x)
       (grid-from-fn h w (lambda (r c)
         (let ((cnt (count-where (lambda (rr) (= (at x rr c) 1)) (range h))))
           (if (>= r (- h cnt)) 1 0)))))
     (define (clear x)
       (let* ((kept (filter
                     (lambda (row)
                       (< (count-where (lambda (v) (= v 1)) row) w))
                     x))
              (lost (- h (length kept))))
         (append (for/list ((i (range lost))) (make-list w 0)) kept)))
     EXPRESSION)))"""


def _settings(settings):
    if type(settings) is not dict or set(settings) != {"mode"}:
        raise ValueError("settings must contain exactly 'mode'")
    mode = settings["mode"]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    return mode


def _integer(value, low, high, name):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def validate_grid(grid):
    if (type(grid) is not list or not 5 <= len(grid) <= 30
            or type(grid[0]) is not list or not 5 <= len(grid[0]) <= 30):
        raise ValueError("grid must have 5..30 rows and columns")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width
           or any(type(v) is not int or v not in (0, 1) for v in row)
           for row in grid):
        raise ValueError("grid must be rectangular with exact integer binary colors")
    return grid


def program(settings):
    mode = _settings(settings)
    if mode == "fall":
        return (HOME / "canonical.rkt").read_text(encoding="utf-8")
    expression = "(clear (fall g))" if mode == "fall_then_clear" else "(fall (clear g))"
    return _COMPOSED.replace("EXPRESSION", expression)


def fall(grid):
    """Independent Python mirror of the canonical histogram transformation."""
    h, w = len(grid), len(grid[0])
    counts = [sum(row[c] for row in grid) for c in range(w)]
    return [[int(r >= h - counts[c]) for c in range(w)] for r in range(h)]


def clear_rows(grid):
    kept = [row[:] for row in grid if not all(row)]
    return [[0] * len(grid[0]) for _ in range(len(grid) - len(kept))] + kept


def transform(grid, mode):
    validate_grid(grid)
    _settings({"mode": mode})
    if mode == "fall":
        return fall(grid)
    if mode == "fall_then_clear":
        return clear_rows(fall(grid))
    return fall(clear_rows(grid))


def _rng(seed, role, index):
    # No setting, demonstration count, or query count enters the input stream.
    material = f"8811ea806605:line-clear-v1:{seed}:{role}:{index}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _profile(role, index, rng):
    if role == "train":
        if index == 0:
            # k=3 original full rows; m=7 full rows after falling.
            return rng.randint(14, 17), rng.randint(9, 13), 3, 7, 0
        if index == 1:
            # Near-full rows cannot clear while a genuinely empty column remains.
            return rng.randint(10, 13), rng.randint(8, 14), 0, 0, 1
        if index == 2:
            # A second positive k/m defeats fixed-positive-count substitutes.
            return rng.randint(7, 9), rng.randint(6, 10), 1, 2, 0
        return ((18, 22, 0, 3, 0), (24, 20, 2, 5, 0), (28, 26, 0, 0, 3))[index - 3]
    return (
        (5, 5, 0, 1, 0), (12, 17, 0, 0, 2),
        (21, 27, 2, 5, 0), (30, 30, 1, 6, 0),
        (7, 13, 0, 2, 0), (18, 9, 1, 3, 0),
        (25, 25, 3, 7, 0), (30, 18, 0, 0, 3),
    )[index]


def _input(seed, role, index):
    rng = _rng(seed, role, index)
    h, w, original_full, minimum_count, empty_columns = _profile(role, index, rng)
    grid = [[0] * w for _ in range(h)]
    columns = list(range(w))
    rng.shuffle(columns)
    active = columns[empty_columns:]

    if empty_columns:
        # One explicit near-full row, with the missing columns truly empty.
        # At least one single-cell column and one tall column remain observable.
        counts = [rng.randint(1, h - 1) for _ in active]
        counts[0], counts[1], counts[2] = 1, 2, h - 1
        for c, count in zip(active, counts):
            selected = [0] + rng.sample(range(1, h), count - 1)
            for r in selected:
                grid[r][c] = 1
    else:
        full = set(rng.sample(range(h), original_full))
        if role == "train" and index == 0:
            # Teach both border rows as ordinary clearable lines. Otherwise an
            # interior-only clear can fit the demos and fail the top-row query.
            full = {0, h - 1, rng.randrange(1, h - 1)}
        elif h == 30 and original_full:
            # Substantive stress reaches both horizontal edges; the full-height
            # column below also reaches every row and both vertical edges.
            full = {0} | set(rng.sample(range(1, h), original_full - 1))
        remaining = [r for r in range(h) if r not in full]
        extra = minimum_count - original_full
        guards = rng.sample(remaining, 2 * extra)
        counts = [rng.randint(minimum_count, h - 1) for _ in active]
        counts[0] = counts[1] = minimum_count
        counts[2] = h if h == 30 else h - 1
        counts[3] = min(h - 1, minimum_count + 1)
        for j, (c, count) in enumerate(zip(active, counts)):
            if j < 2:
                more = guards[j * extra:(j + 1) * extra]
            else:
                more = rng.sample(remaining, count - original_full)
            for r in full | set(more):
                grid[r][c] = 1
        # The two guards have disjoint extra cells: there are exactly k original
        # full rows, while all column counts are >= m with two attaining m.
    return grid


def teaching_certificate(train, query_inputs, settings):
    """Fit settings to demonstrations only, then compare input-only queries.

    Non-unique settings are harmless only when all survivors agree on every
    query. Native promotion separately requires a unique surviving setting.
    This finite check does not claim uniqueness against arbitrary programs.
    """
    selected = _settings(settings)
    if type(train) is not list or not train or type(query_inputs) is not list or not query_inputs:
        raise ValueError("nonempty demonstration and query-input lists are required")
    for pair in train:
        validate_grid(pair["input"])
        validate_grid(pair["output"])
    for grid in query_inputs:
        validate_grid(grid)
    survivors = [mode for mode in MODES
                 if all(transform(pair["input"], mode) == pair["output"] for pair in train)]
    disagreements = []
    for index, grid in enumerate(query_inputs):
        expected = transform(grid, selected)
        wrong = [mode for mode in survivors if transform(grid, mode) != expected]
        if wrong:
            disagreements.append({"query_index": index, "modes": wrong})
    return {"ok": selected in survivors and not disagreements,
            "unique_setting": survivors == [selected],
            "surviving_modes": survivors, "query_disagreements": disagreements,
            "evidence_scope": "three declared settings, demonstrations only"}


def generate(seed, settings, demos=3, queries=4):
    if type(seed) is not int:
        raise ValueError("seed must be an exact integer")
    mode = _settings(settings)
    _integer(demos, 3, 6, "demos")
    _integer(queries, 1, 8, "queries")
    episode = {"train": [], "test": [], "program_solution": program(settings),
               "settings": dict(settings), "seed": seed}
    for role, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = _input(seed, role, index)
            episode[role].append({"input": grid, "output": transform(grid, mode)})
    # Shapes are disjoint across profile positions, hence inputs cannot repeat.
    seen = set()
    for pair in episode["train"] + episode["test"]:
        key = tuple(tuple(row) for row in pair["input"])
        if key in seen:
            raise RuntimeError("input profile collision")
        seen.add(key)
    certificate = teaching_certificate(
        episode["train"], [pair["input"] for pair in episode["test"]], settings)
    if not certificate["ok"] or not certificate["unique_setting"]:
        raise RuntimeError("constructed demonstrations do not identify the setting")
    episode["teaching_certificate"] = certificate
    return episode


def public_view(episode, query_index=0):
    """One model turn: the demonstrations and one query, no total-count hint."""
    _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return public_challenge_bytes({"train": episode["train"],
                                   "test": [episode["test"][query_index]]})
