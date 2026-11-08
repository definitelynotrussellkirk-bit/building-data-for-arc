"""Matched-input crop family with a crop-created perimeter selector.

The exact canonical default emits the tight non-zero crop.  The alternate first
creates that crop, then counts non-zero colors on its newly created perimeter,
selects the unique perimeter mode, and recolors every occurrence of that color
to 8.  Lessons make the perimeter mode disagree with the global mode, top-row
mode, left-column mode, first non-zero color, and corner color.
"""
from __future__ import annotations

from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any

TASK_ID = "26cfe7595a4a"
BORDER_RULES = ("crop_only", "highlight_perimeter_mode")
DEFAULT_BORDER_RULE = "crop_only"
HIGHLIGHT = 8
CANDIDATE_RULES = (
    *BORDER_RULES,
    "highlight_global_mode",
    "highlight_top_row_mode",
    "highlight_left_column_mode",
    "highlight_first_nonzero",
    "highlight_corner_color",
    "highlight_least_perimeter_mode",
)
ROOT = Path(__file__).resolve().parents[4]

_TRAIN_PROFILES = (
    (8, 10, 3, 4),
    (10, 9, 5, 4),
    (14, 16, 8, 9),
    (18, 17, 12, 11),
    (24, 25, 18, 20),
    (28, 27, 22, 21),
)
_TEST_PROFILES = (
    (9, 13, 4, 8),
    (16, 19, 10, 13),
    (24, 28, 18, 22),
    (30, 30, 24, 26),
)

Grid = list[list[int]]


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in [{low}, {high}]")
    return value


def validate_border_rule(value: Any) -> str:
    if type(value) is not str or value not in BORDER_RULES:
        raise ValueError(f"border_rule must be one of {BORDER_RULES}")
    return value


def validate_settings(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"border_rule"}:
        raise ValueError("settings must contain exactly border_rule")
    return validate_border_rule(settings["border_rule"])


def validate_request(seed: Any, demos: Any, queries: Any) -> None:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 1, 4)


def _grid(grid: Any) -> Grid:
    if (
        type(grid) is not list
        or not 1 <= len(grid) <= 30
        or type(grid[0]) is not list
        or not 1 <= len(grid[0]) <= 30
        or any(
            type(row) is not list
            or len(row) != len(grid[0])
            or any(type(value) is not int or not 0 <= value <= 9 for value in row)
            for row in grid
        )
    ):
        raise ValueError("grid must be rectangular 1..30 with exact integer colors 0..9")
    return [row[:] for row in grid]


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("require one exact canonical program")
    return programs.pop()


_HIGHLIGHT_PROGRAM = r"""(rule!
  (let* ((cells
           (filter (lambda (p) (not (= (cell-at g (fst p) (snd p)) 0)))
                   (grid-positions g)))
         (bb (bbox-of-cells cells))
         (cropped (subgrid g (first bb) (second bb) (third bb) (fourth bb)))
         (positions (grid-positions cropped))
         (colors
           (remove-duplicates
             (filter (lambda (v) (!= v 0))
                     (map (lambda (p) (cell-at cropped (fst p) (snd p))) positions))))
         (perimeter-values
           (filter
             (lambda (v) (!= v 0))
             (map
               (lambda (p)
                 (if (or (= (fst p) 0)
                         (= (snd p) 0)
                         (= (fst p) (- (rows cropped) 1))
                         (= (snd p) (- (cols cropped) 1)))
                     (cell-at cropped (fst p) (snd p))
                     0))
               positions)))
         (count-value
           (lambda (color)
             (length (filter (lambda (v) (= v color)) perimeter-values))))
         (winner
           (for/fold ([best (first colors)]) ([color (in-list (rest colors))])
             (if (> (count-value color) (count-value best)) color best))))
    (cellmap cropped (r c v) (if (= v winner) 8 v))))"""


def program_for(border_rule: str) -> str:
    border_rule = validate_border_rule(border_rule)
    return canonical_program() if border_rule == "crop_only" else _HIGHLIGHT_PROGRAM


def crop(grid: Grid) -> Grid:
    g = _grid(grid)
    cells = [(r, c) for r, row in enumerate(g) for c, value in enumerate(row) if value != 0]
    if not cells:
        raise ValueError("cannot crop an all-zero grid")
    r0, r1 = min(r for r, _ in cells), max(r for r, _ in cells)
    c0, c1 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c0 : c1 + 1] for row in g[r0 : r1 + 1]]


def _mode(values: list[int], *, least: bool = False) -> int:
    counts = Counter(value for value in values if value != 0)
    if not counts:
        raise ValueError("mode needs a non-zero color")
    target = min(counts.values()) if least else max(counts.values())
    return min(color for color, count in counts.items() if count == target)


def _perimeter_values(grid: Grid) -> list[int]:
    g = _grid(grid)
    h, w = len(g), len(g[0])
    return [
        g[r][c]
        for r in range(h)
        for c in range(w)
        if r in (0, h - 1) or c in (0, w - 1)
    ]


def perimeter_mode(grid: Grid) -> int:
    return _mode(_perimeter_values(grid))


def global_mode(grid: Grid) -> int:
    g = _grid(grid)
    return _mode([value for row in g for value in row])


def _highlight(grid: Grid, color: int) -> Grid:
    g = _grid(grid)
    return [[HIGHLIGHT if value == color else value for value in row] for row in g]


def evaluate(grid: Grid, border_rule: str = "crop_only") -> Grid:
    border_rule = validate_border_rule(border_rule)
    intermediate = crop(grid)
    if border_rule == "crop_only":
        return intermediate
    return _highlight(intermediate, perimeter_mode(intermediate))


def evaluate_candidate(grid: Grid, name: str) -> Grid:
    if name in BORDER_RULES:
        return evaluate(grid, name)
    intermediate = crop(grid)
    nonzero = [value for row in intermediate for value in row if value != 0]
    if name == "highlight_global_mode":
        color = global_mode(intermediate)
    elif name == "highlight_top_row_mode":
        color = _mode(intermediate[0])
    elif name == "highlight_left_column_mode":
        color = _mode([row[0] for row in intermediate])
    elif name == "highlight_first_nonzero":
        color = nonzero[0]
    elif name == "highlight_corner_color":
        color = intermediate[0][0]
    elif name == "highlight_least_perimeter_mode":
        color = _mode(_perimeter_values(intermediate), least=True)
    else:
        raise ValueError(f"unknown candidate {name!r}")
    return _highlight(intermediate, color)


def teaching_survivors(train: list[dict[str, Grid]]) -> list[str]:
    return [
        name
        for name in CANDIDATE_RULES
        if all(evaluate_candidate(pair["input"], name) == pair["output"] for pair in train)
    ]


def _rng(seed: int, split: str, index: int) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{split}|{index}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _base_crop(height: int, width: int, colors: tuple[int, int, int], salt: int) -> Grid:
    winner, global_color, third = colors
    crop_grid = [[global_color for _ in range(width)] for _ in range(height)]

    # New crop perimeter: bottom and right favor the winner; top favors the
    # global mode; left and the first/corner cue favor the third color.
    for c in range(width):
        crop_grid[0][c] = global_color
        crop_grid[height - 1][c] = winner
    for r in range(height):
        crop_grid[r][0] = third
        crop_grid[r][width - 1] = winner
    crop_grid[0][0] = third
    crop_grid[0][width - 1] = global_color
    crop_grid[height - 1][0] = third
    crop_grid[height - 1][width - 1] = winner

    # Interior holes and minority texture preserve crop geometry while making
    # the global mode disagree with the perimeter mode.
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            code = (r * 11 + c * 7 + salt) % 13
            if code == 0:
                crop_grid[r][c] = 0
            elif code == 1:
                crop_grid[r][c] = third
            else:
                crop_grid[r][c] = global_color

    if perimeter_mode(crop_grid) != winner:
        raise ValueError("perimeter winner construction failed")
    if global_mode(crop_grid) == winner:
        # Small edge cases: reinforce the interior/global distinction.
        for r in range(1, height - 1):
            for c in range(1, width - 1):
                crop_grid[r][c] = global_color
        if global_mode(crop_grid) == winner:
            raise ValueError("global/perimeter distinction failed")
    return crop_grid


def _transform(grid: Grid, code: int) -> Grid:
    if code == 0:
        return [row[:] for row in grid]
    if code == 1:
        return [list(reversed(row)) for row in grid]
    if code == 2:
        return [row[:] for row in reversed(grid)]
    if code == 3:
        return [list(reversed(row)) for row in reversed(grid)]
    if code == 4:
        return [list(row) for row in zip(*grid)]
    if code == 5:
        return [list(reversed(row)) for row in zip(*grid)]
    raise ValueError(code)


def _embed(crop_grid: Grid, full_h: int, full_w: int, rng: random.Random) -> Grid:
    ch, cw = len(crop_grid), len(crop_grid[0])
    if ch > full_h - 2 or cw > full_w - 2:
        raise ValueError("crop needs a one-cell padding margin")
    top = rng.randint(1, full_h - ch - 1)
    left = rng.randint(1, full_w - cw - 1)
    out = [[0] * full_w for _ in range(full_h)]
    for r in range(ch):
        for c in range(cw):
            out[top + r][left + c] = crop_grid[r][c]
    return out


def _scene(seed: int, split: str, index: int, profile: tuple[int, int, int, int]) -> Grid:
    full_h, full_w, crop_h, crop_w = profile
    rng = _rng(seed, split, index)
    colors = tuple(rng.sample([1, 2, 3, 4, 5, 6, 7, 9], 3))
    crop_grid = _base_crop(crop_h, crop_w, colors, index + seed % 17)
    # Preserve the first two teaching contrasts exactly; later scenes cover
    # orientation changes without encoding the hidden setting.
    if split == "train" and index < 2:
        transform = 0
    else:
        valid_transforms = []
        for code in range(6):
            candidate = _transform(crop_grid, code)
            if len(candidate) <= full_h - 2 and len(candidate[0]) <= full_w - 2:
                valid_transforms.append(code)
        if not valid_transforms:
            raise ValueError("no lawful crop transform fits the padded canvas")
        transform = rng.choice(valid_transforms)
    crop_grid = _transform(crop_grid, transform)
    grid = _embed(crop_grid, full_h, full_w, rng)
    if evaluate(grid, "crop_only") == evaluate(grid, "highlight_perimeter_mode"):
        raise ValueError("settings must differ on every scene")
    return grid


def _bank(seed: int, split: str, profiles: tuple[tuple[int, int, int, int], ...]) -> list[Grid]:
    return [_scene(seed, split, index, profile) for index, profile in enumerate(profiles)]


def generate_episode(seed: int, border_rule: str, *, demos: int, queries: int) -> dict[str, Any]:
    validate_request(seed, demos, queries)
    border_rule = validate_border_rule(border_rule)
    train_inputs = _bank(seed, "train", _TRAIN_PROFILES)
    test_inputs = _bank(seed, "test", _TEST_PROFILES)
    train = [
        {"input": grid, "output": evaluate(grid, border_rule)}
        for grid in train_inputs[:demos]
    ]
    test = [
        {"input": grid, "output": evaluate(grid, border_rule)}
        for grid in test_inputs[:queries]
    ]
    if teaching_survivors(train) != [border_rule]:
        raise RuntimeError("teaching bank does not uniquely identify the requested rule")
    return {
        "train": train,
        "test": test,
        "program_solution": program_for(border_rule),
        "settings": {"border_rule": border_rule},
        "metadata": {
            "source": "matched full-bank prefix",
            "sequential": "crop, read the new perimeter, then recolor its mode",
        },
    }


def rival_program(name: str) -> str:
    if name in BORDER_RULES:
        return program_for(name)
    if name == "highlight_global_mode":
        return r"""(rule!
  (let* ((cells
           (filter (lambda (p) (not (= (cell-at g (fst p) (snd p)) 0)))
                   (grid-positions g)))
         (bb (bbox-of-cells cells))
         (cropped (subgrid g (first bb) (second bb) (third bb) (fourth bb)))
         (values (filter (lambda (v) (!= v 0)) (apply append cropped)))
         (colors (remove-duplicates values))
         (count-value (lambda (color)
                        (length (filter (lambda (v) (= v color)) values))))
         (winner
           (for/fold ([best (first colors)]) ([color (in-list (rest colors))])
             (if (> (count-value color) (count-value best)) color best))))
    (cellmap cropped (r c v) (if (= v winner) 8 v))))"""
    if name == "highlight_first_nonzero":
        return r"""(rule!
  (let* ((cells
           (filter (lambda (p) (not (= (cell-at g (fst p) (snd p)) 0)))
                   (grid-positions g)))
         (bb (bbox-of-cells cells))
         (cropped (subgrid g (first bb) (second bb) (third bb) (fourth bb)))
         (winner (cell-at cropped 0 0)))
    (cellmap cropped (r c v) (if (= v winner) 8 v))))"""
    raise ValueError(f"no standalone Racket rival for {name}")
