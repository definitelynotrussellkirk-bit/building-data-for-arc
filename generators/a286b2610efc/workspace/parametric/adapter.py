"""Native repeated-completion lessons for ARC task a286b2610efc.

The default setting is the exact canonical one-pass Racket program.  The
alternative applies that same simultaneous completion pass twice: step A
creates an intermediate grid, then step B scans the newly completed grid.
Inputs are independent of the private episode setting and are prefix-stable
for independently requested demonstration/query counts.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import random
from typing import Any


HERE = Path(__file__).resolve().parent
CANONICAL = (HERE / "canonical.rkt").read_text(encoding="utf-8")
ROUNDS = (1, 2)
MIN_SIDE = 14
MAX_SIDE = 30
DEMO_DIMS = ((14, 16), (16, 14), (17, 19), (19, 17), (21, 23), (23, 21))
QUERY_DIMS = ((24, 26), (26, 24), (28, 30), (30, 30))

# The conditions inside each pass read only ``src``.  Horizontal and vertical
# writes accumulate in ``out``, exactly as in the canonical program.  A second
# call therefore sees cells produced by the first call, but never cascades
# within either individual call.
TWO_PASS = """(rule! (let ((pass (lambda (src) (let ((after-h (for*/fold ((out src)) ((r (in-range (rows src))) (c (in-range (- (cols src) 2)))) (let ((a (at src r c)) (b (at src r (+ c 1))) (d (at src r (+ c 2)))) (cond ((and (= a 0) (not (= b 0)) (= b d)) (set-cell out r c b)) ((and (not (= a 0)) (= a b) (= d 0)) (set-cell out r (+ c 2) a)) (else out)))))) (for*/fold ((out after-h)) ((r (in-range (- (rows src) 2))) (c (in-range (cols src)))) (let ((a (at src r c)) (b (at src (+ r 1) c)) (d (at src (+ r 2) c))) (cond ((and (= a 0) (not (= b 0)) (= b d)) (set-cell out r c b)) ((and (not (= a 0)) (= a b) (= d 0)) (set-cell out (+ r 2) c a)) (else out)))))))) (pass (pass g))))"""


def _integer(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _rounds(settings: dict[str, Any]) -> int:
    if type(settings) is not dict:
        raise TypeError("settings must be an exact dictionary")
    if set(settings) != {"rounds"}:
        raise ValueError("settings must name exactly rounds")
    value = settings["rounds"]
    if type(value) is not int or value not in ROUNDS:
        raise ValueError("rounds must be the exact integer 1 or 2")
    return value


def program(settings: dict[str, Any]) -> str:
    """Return the exact Racket program for one declared setting."""
    return CANONICAL if _rounds(settings) == 1 else TWO_PASS


def _grid(value: Any) -> list[list[int]]:
    if (type(value) is not list or not 1 <= len(value) <= 30
            or type(value[0]) is not list or not 1 <= len(value[0]) <= 30):
        raise ValueError("grid must have 1..30 rows and columns")
    width = len(value[0])
    if any(type(row) is not list or len(row) != width
           or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
           for row in value):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return [row[:] for row in value]


def complete_once(grid: list[list[int]]) -> list[list[int]]:
    """Apply one simultaneous canonical completion pass in Python.

    This is a private label claim only.  Native qualification re-executes every
    demonstration/query label through the protected Racket runtime.
    """
    source = _grid(grid)
    output = [row[:] for row in source]
    height, width = len(source), len(source[0])

    for row in range(height):
        for col in range(max(0, width - 2)):
            first, middle, last = source[row][col:col + 3]
            if first == 0 and middle != 0 and middle == last:
                output[row][col] = middle
            elif first != 0 and first == middle and last == 0:
                output[row][col + 2] = first

    for row in range(max(0, height - 2)):
        for col in range(width):
            first = source[row][col]
            middle = source[row + 1][col]
            last = source[row + 2][col]
            if first == 0 and middle != 0 and middle == last:
                output[row][col] = middle
            elif first != 0 and first == middle and last == 0:
                output[row + 2][col] = first
    return output


def transform(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    result = _grid(grid)
    for _ in range(_rounds(settings)):
        result = complete_once(result)
    return result


def _rng(seed: int, purpose: str) -> random.Random:
    material = f"a286b2610efc/repeated-completion-v1/{seed}/{purpose}".encode("ascii")
    return random.Random(int.from_bytes(hashlib.sha256(material).digest(), "big"))


def _candidate(kind: str, cells: tuple[tuple[int, int], tuple[int, int]],
               footprint: frozenset[tuple[int, int]]) -> dict[str, Any]:
    return {"kind": kind, "cells": cells, "footprint": footprint}


def _candidates(height: int, width: int) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in range(height):
        left = _candidate(
            "h_left_top" if row < height / 2 else "h_left_bottom",
            ((row, 0), (row, 1)),
            frozenset((row, col) for col in range(4)),
        )
        right = _candidate(
            "h_right_bottom" if row >= height / 2 else "h_right_top",
            ((row, width - 2), (row, width - 1)),
            frozenset((row, col) for col in range(width - 4, width)),
        )
        result.extend((left, right))
        for col in range(2, width - 3):
            result.append(_candidate(
                "h_interior",
                ((row, col), (row, col + 1)),
                frozenset((row, c) for c in range(col - 2, col + 4)),
            ))

    for col in range(width):
        top = _candidate(
            "v_top_right" if col >= width / 2 else "v_top_left",
            ((0, col), (1, col)),
            frozenset((row, col) for row in range(4)),
        )
        bottom = _candidate(
            "v_bottom_left" if col < width / 2 else "v_bottom_right",
            ((height - 2, col), (height - 1, col)),
            frozenset((row, col) for row in range(height - 4, height)),
        )
        result.extend((top, bottom))
        for row in range(2, height - 3):
            result.append(_candidate(
                "v_interior",
                ((row, col), (row + 1, col)),
                frozenset((r, col) for r in range(row - 2, row + 4)),
            ))
    return result


def _compatible(candidate: dict[str, Any], selected: list[dict[str, Any]]) -> bool:
    cells = candidate["footprint"]
    for other in selected:
        if min(
            max(abs(r0 - r1), abs(c0 - c1))
            for r0, c0 in cells
            for r1, c1 in other["footprint"]
        ) <= 1:
            return False
    return True


def _required_candidates(candidates: list[dict[str, Any]], rng: random.Random) -> list[dict[str, Any]]:
    required = (
        "h_left_top",
        "h_right_bottom",
        "v_top_right",
        "v_bottom_left",
        "h_interior",
        "v_interior",
    )
    choices = {kind: [row for row in candidates if row["kind"] == kind] for kind in required}
    for rows in choices.values():
        rng.shuffle(rows)

    def search(index: int, selected: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
        if index == len(required):
            return selected
        for row in choices[required[index]]:
            if _compatible(row, selected):
                found = search(index + 1, selected + [row])
                if found is not None:
                    return found
        return None

    selected = search(0, [])
    if selected is None:
        raise AssertionError("could not construct the six required completion motifs")
    return selected


def _select_motifs(height: int, width: int, rng: random.Random) -> list[dict[str, Any]]:
    candidates = _candidates(height, width)
    selected = _required_candidates(candidates, rng)
    target = min(15, max(6, height * width // 60))
    remainder = candidates[:]
    rng.shuffle(remainder)
    for row in remainder:
        if len(selected) >= target:
            break
        if row in selected or not _compatible(row, selected):
            continue
        selected.append(row)
    if len(selected) < target:
        raise AssertionError(f"constructed only {len(selected)} of {target} requested motifs")
    return selected


def _add_distractors(grid: list[list[int]], occupied: set[tuple[int, int]],
                     rng: random.Random, palette: list[int]) -> int:
    height, width = len(grid), len(grid[0])
    target = max(1, height * width // 225)
    candidates = [(r, c) for r in range(height) for c in range(width)]
    rng.shuffle(candidates)
    selected: list[tuple[int, int]] = []
    for row, col in candidates:
        if grid[row][col] != 0:
            continue
        if any(max(abs(row - rr), abs(col - cc)) <= 2 for rr, cc in occupied):
            continue
        if any(max(abs(row - rr), abs(col - cc)) <= 2 for rr, cc in selected):
            continue
        grid[row][col] = palette[(len(selected) + 5) % len(palette)]
        selected.append((row, col))
        if len(selected) == target:
            break
    return len(selected)


def sample_input(seed: int, split: str, index: int, *, height: int | None = None,
                 width: int | None = None) -> list[list[int]]:
    """Construct a deterministic scene independent of the private round count."""
    _integer(seed, 0, 2**63 - 1, "seed")
    if type(split) is not str or split not in ("train", "test"):
        raise ValueError("split must be 'train' or 'test'")
    maximum = 5 if split == "train" else 3
    _integer(index, 0, maximum, "index")
    if height is None and width is None:
        height, width = (DEMO_DIMS if split == "train" else QUERY_DIMS)[index]
    elif height is None or width is None:
        raise ValueError("height and width must be supplied together")
    else:
        _integer(height, MIN_SIDE, MAX_SIDE, "height")
        _integer(width, MIN_SIDE, MAX_SIDE, "width")
    assert height is not None and width is not None

    rng = _rng(seed, f"{split}/{index}/{height}x{width}")
    motifs = _select_motifs(height, width, rng)
    palette = list(range(1, 10))
    rng.shuffle(palette)
    grid = [[0] * width for _ in range(height)]
    occupied: set[tuple[int, int]] = set()
    for motif_index, motif in enumerate(motifs):
        color = palette[motif_index % len(palette)]
        for row, col in motif["cells"]:
            if grid[row][col] != 0:
                raise AssertionError("constructed motifs overlap")
            grid[row][col] = color
        occupied.update(motif["footprint"])
    _add_distractors(grid, occupied, rng, palette)
    return grid


def generate(seed: int, settings: dict[str, Any], demos: int, queries: int) -> dict[str, Any]:
    """Build one private episode with independent count prefixes."""
    _integer(seed, 0, 2**63 - 1, "seed")
    _rounds(settings)
    _integer(demos, 2, 6, "demos")
    _integer(queries, 1, 4, "queries")

    result: dict[str, Any] = {"program_solution": program(settings)}
    for split, count in (("train", demos), ("test", queries)):
        pairs = []
        for index in range(count):
            grid = sample_input(seed, split, index)
            pairs.append({"input": grid, "output": transform(grid, settings)})
        result[split] = pairs
    return deepcopy(result)
