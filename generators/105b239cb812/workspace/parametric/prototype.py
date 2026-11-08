"""Parametric direct-versus-inverse transform family for ARC task 105b239cb812.

The private episode setting controls how the transform inferred from panels A
and B is applied to panel C.  ``direct`` is the exact canonical rule;
``inverse`` applies the inverse transform.  Input generation is independent of
that setting.
"""
from __future__ import annotations

import copy
import functools
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable

from reviewer_support import canonical_path, find_root


TASK_ID = "105b239cb812"
FAMILY_VERSION = "1.0.0"
APPLICATIONS = ("direct", "inverse")
DEMO_LIMITS = (2, 6)
QUERY_COUNT = 4
DIVIDER_COLOR = 5
BACKGROUND_COLOR = 0
ALLOWED_COLORS = (1, 2, 3, 4, 6, 7, 8, 9)
TRANSFORM_NAMES = ("cw", "180", "ccw", "lr", "ud", "transpose")
INVERSE_TRANSFORM = {
    "cw": "ccw",
    "180": "180",
    "ccw": "cw",
    "lr": "lr",
    "ud": "ud",
    "transpose": "transpose",
}
RACKET_TRANSFORM = {
    "id": "id",
    "cw": "rot90",
    "180": "rot180",
    "ccw": "rot270",
    "lr": "flip-h",
    "ud": "flip-v",
    "transpose": "transpose",
}

# Every supported demonstration count starts with both transform directions;
# each individual demonstration also distinguishes direct from inverse.
DEMO_PROFILES = (
    (4, "cw"),
    (5, "ccw"),
    (6, "cw"),
    (7, "ccw"),
    (8, "cw"),
    (9, "ccw"),
)
QUERY_PROFILES = (
    (4, "cw"),
    (6, "180"),
    (8, "ccw"),
    (9, "cw"),
)


@functools.lru_cache(maxsize=1)
def canonical_program() -> str:
    """Read the unique exact canonical Racket authority from this source tree."""
    root = find_root(__file__)
    programs: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                program = row.get("program_solution")
                if not isinstance(program, str) or not program.strip():
                    raise ValueError("canonical task row has no nonempty program_solution")
                programs.add(program)
    if len(programs) != 1:
        raise ValueError(f"expected one exact canonical program, found {len(programs)}")
    return next(iter(programs))


def _validate_application(application: Any) -> str:
    if type(application) is not str or application not in APPLICATIONS:
        raise ValueError(f"application must be one of {list(APPLICATIONS)}")
    return application


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an exact integer (bool is forbidden)")
    if not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be in 0..2**63-1")
    return seed


def _validate_counts(demos: Any, queries: Any) -> tuple[int, int]:
    for name, value in (("demos", demos), ("queries", queries)):
        if type(value) is not int:
            raise TypeError(f"{name} must be an exact integer (bool is forbidden)")
    if not DEMO_LIMITS[0] <= demos <= DEMO_LIMITS[1]:
        raise ValueError(f"demos must be in {DEMO_LIMITS[0]}..{DEMO_LIMITS[1]}")
    if queries != QUERY_COUNT:
        raise ValueError(f"queries must equal {QUERY_COUNT}")
    return demos, queries


def inverse_program() -> str:
    source = canonical_program()
    split_anchor = "(define (e15-split-panels-row grid n count)"
    apply_anchor = "(apply-transform-name name (third panels))"
    if source.count(split_anchor) != 1 or source.count(apply_anchor) != 1:
        raise RuntimeError("canonical program no longer has the expected transform sites")
    helper = (
        "(define (inverse-transform-name name) "
        "(cond ((equal? name 'rot90) 'rot270) "
        "((equal? name 'rot270) 'rot90) (else name))) "
    )
    return source.replace(split_anchor, helper + split_anchor, 1).replace(
        apply_anchor,
        "(apply-transform-name (inverse-transform-name name) (third panels))",
        1,
    )


def program_for(application: str) -> str:
    application = _validate_application(application)
    return canonical_program() if application == "direct" else inverse_program()


def _copy_grid(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def transform_panel(panel: list[list[int]], name: str) -> list[list[int]]:
    if name == "id":
        return _copy_grid(panel)
    if name == "cw":
        return [list(row) for row in zip(*panel[::-1])]
    if name == "180":
        return [row[::-1] for row in panel[::-1]]
    if name == "ccw":
        return [list(row) for row in zip(*panel)][::-1]
    if name == "lr":
        return [row[::-1] for row in panel]
    if name == "ud":
        return [row[:] for row in panel[::-1]]
    if name == "transpose":
        return [list(row) for row in zip(*panel)]
    raise ValueError(f"unsupported transform: {name!r}")


def _grid_key(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _orbit_unique(panel: list[list[int]]) -> bool:
    orbit = {_grid_key(panel)}
    orbit.update(_grid_key(transform_panel(panel, name)) for name in TRANSFORM_NAMES)
    return len(orbit) == len(TRANSFORM_NAMES) + 1


def _stream_rng(seed: int, split: str, index: int, role: str, attempt: int) -> random.Random:
    material = f"{TASK_ID}|{FAMILY_VERSION}|{seed}|{split}|{index}|{role}|{attempt}".encode()
    digest = hashlib.sha256(material).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _box_positions(
    size: int,
    *,
    touch_all_boundaries: bool,
    rng: random.Random,
) -> tuple[list[tuple[int, int]], list[tuple[int, int]]]:
    if touch_all_boundaries:
        top = left = 0
        height = width = size
    else:
        # A strict sub-box makes a crop-local transform observably wrong while
        # preserving dense, asymmetric content.  The offset is seed-dependent.
        height = size - 1
        width = size - 2
        top = rng.randrange(size - height + 1)
        left = rng.randrange(size - width + 1)

    bottom = top + height - 1
    right = left + width - 1
    proposed = [
        (top, left),
        (top, right),
        (bottom, left),
        (bottom, right),
        (top, left + width // 2),
        (bottom, left + width // 2),
        (top + height // 2, left),
        (top + height // 2, right),
        (top + height // 2, left + width // 2),
    ]
    seen: set[tuple[int, int]] = set()
    required = []
    for position in proposed:
        if position not in seen:
            seen.add(position)
            required.append(position)
    available = [
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
    ]
    return required, available


def _make_panel(
    seed: int,
    split: str,
    index: int,
    size: int,
    role: str,
    *,
    touch_all_boundaries: bool,
) -> list[list[int]]:
    if role not in {"a", "c"}:
        raise ValueError("role must be a or c")

    for attempt in range(128):
        rng = _stream_rng(seed, split, index, role, attempt)
        required, available = _box_positions(
            size,
            touch_all_boundaries=touch_all_boundaries,
            rng=rng,
        )
        density = 0.55 if role == "a" else 0.70
        if touch_all_boundaries:
            density = 0.50
        target = min(len(available), max(len(required), round(len(available) * density)))
        required_set = set(required)
        remaining = [position for position in available if position not in required_set]
        rng.shuffle(remaining)
        positions = required + remaining[: max(0, target - len(required))]
        palette = tuple(rng.sample(ALLOWED_COLORS, 4 if size >= 6 else 3))
        panel = [[BACKGROUND_COLOR for _ in range(size)] for _ in range(size)]
        for offset, (row, col) in enumerate(positions):
            # Mix a deterministic cycle with random phase so every palette color
            # appears while the spatial pattern remains strongly asymmetric.
            panel[row][col] = palette[(offset + rng.randrange(len(palette))) % len(palette)]
        if _orbit_unique(panel):
            return panel
    raise RuntimeError(f"could not build an asymmetric {role} panel of size {size}")


def build_input(seed: int, split: str, index: int, size: int, transform_name: str) -> list[list[int]]:
    seed = _validate_seed(seed)
    if split not in {"demo", "query"}:
        raise ValueError("split must be demo or query")
    if type(index) is not int or index < 0:
        raise ValueError("index must be a nonnegative exact integer")
    if type(size) is not int or not 4 <= size <= 9:
        raise ValueError("size must be an exact integer in 4..9")
    if transform_name not in TRANSFORM_NAMES:
        raise ValueError(f"transform_name must be one of {TRANSFORM_NAMES}")

    panel_a = _make_panel(
        seed,
        split,
        index,
        size,
        "a",
        touch_all_boundaries=False,
    )
    panel_b = transform_panel(panel_a, transform_name)
    panel_c = _make_panel(
        seed,
        split,
        index,
        size,
        "c",
        touch_all_boundaries=(split == "query" and index == len(QUERY_PROFILES) - 1),
    )
    width = 3 * size + 2
    sep1, sep2 = size, 2 * size + 1
    grid = [[BACKGROUND_COLOR for _ in range(width)] for _ in range(size)]
    for row in range(size):
        grid[row][:size] = panel_a[row]
        grid[row][sep1] = DIVIDER_COLOR
        grid[row][sep1 + 1 : sep2] = panel_b[row]
        grid[row][sep2] = DIVIDER_COLOR
        grid[row][sep2 + 1 :] = panel_c[row]
    return grid


def split_panels(grid: list[list[int]]) -> tuple[list[list[int]], list[list[int]], list[list[int]]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be exact integer ARC colors")
    size = len(grid)
    if not 4 <= size <= 9 or width != 3 * size + 2:
        raise ValueError("grid must have shape n x (3n+2) for n in 4..9")
    sep1, sep2 = size, 2 * size + 1
    if any(grid[row][sep1] != DIVIDER_COLOR or grid[row][sep2] != DIVIDER_COLOR for row in range(size)):
        raise ValueError("expected full color-5 separator columns")
    if any(
        grid[row][col] == DIVIDER_COLOR
        for row in range(size)
        for col in range(width)
        if col not in (sep1, sep2)
    ):
        raise ValueError("color 5 may appear only in separator columns")
    return (
        [row[:size] for row in grid],
        [row[sep1 + 1 : sep2] for row in grid],
        [row[sep2 + 1 :] for row in grid],
    )


def infer_transform(grid: list[list[int]]) -> str:
    panel_a, panel_b, _ = split_panels(grid)
    matches = [name for name in TRANSFORM_NAMES if transform_panel(panel_a, name) == panel_b]
    if len(matches) != 1:
        raise ValueError(f"expected one authoritative A-to-B transform, got {matches}")
    return matches[0]


def solve(grid: list[list[int]], application: str) -> list[list[int]]:
    application = _validate_application(application)
    _panel_a, _panel_b, panel_c = split_panels(grid)
    inferred = infer_transform(grid)
    applied = inferred if application == "direct" else INVERSE_TRANSFORM[inferred]
    return transform_panel(panel_c, applied)


def _sides(panel: list[list[int]]) -> list[str]:
    size = len(panel)
    occupied = [(row, col) for row in range(size) for col in range(size) if panel[row][col] != 0]
    sides = []
    if any(row == 0 for row, _ in occupied):
        sides.append("top")
    if any(row == size - 1 for row, _ in occupied):
        sides.append("bottom")
    if any(col == 0 for _, col in occupied):
        sides.append("left")
    if any(col == size - 1 for _, col in occupied):
        sides.append("right")
    return sorted(sides)


def input_metrics(grid: list[list[int]]) -> dict[str, Any]:
    panel_a, panel_b, panel_c = split_panels(grid)
    inferred = infer_transform(grid)
    return {
        "panel_size": len(panel_a),
        "input_shape": [len(grid), len(grid[0])],
        "inferred_transform": inferred,
        "panel_a_active": sum(cell != 0 for row in panel_a for cell in row),
        "panel_b_active": sum(cell != 0 for row in panel_b for cell in row),
        "panel_c_active": sum(cell != 0 for row in panel_c for cell in row),
        "panel_a_colors": sorted({cell for row in panel_a for cell in row if cell != 0}),
        "panel_c_colors": sorted({cell for row in panel_c for cell in row if cell != 0}),
        "panel_c_boundary_sides": _sides(panel_c),
        "all_orbits_unique": _orbit_unique(panel_a) and _orbit_unique(panel_c),
    }


def generate_episode(seed: int, *, application: str, demos: int = 3, queries: int = 4) -> dict[str, Any]:
    seed = _validate_seed(seed)
    application = _validate_application(application)
    demos, queries = _validate_counts(demos, queries)

    train = []
    for index, (size, transform_name) in enumerate(DEMO_PROFILES[:demos]):
        grid = build_input(seed, "demo", index, size, transform_name)
        train.append({"input": grid, "output": solve(grid, application)})

    test = []
    for index, (size, transform_name) in enumerate(QUERY_PROFILES[:queries]):
        grid = build_input(seed, "query", index, size, transform_name)
        test.append({"input": grid, "output": solve(grid, application)})

    serialized = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in train + test
    ]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("episode sampler produced duplicate visible inputs")
    return {
        "train": copy.deepcopy(train),
        "test": copy.deepcopy(test),
        "program_solution": program_for(application),
    }


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    """Project exactly one query without exposing counts, settings, code or answers."""
    if type(query_index) is not int:
        raise TypeError("query_index must be an exact integer")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or not 0 <= query_index < len(test):
        raise ValueError("episode/query_index is invalid")
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in train
        ],
        "test": [{"input": copy.deepcopy(test[query_index]["input"])}],
    }


def fixed_transform_program(transform_name: str) -> str:
    """Racket rival that skips A→B inference and applies one fixed transform to C."""
    if transform_name not in RACKET_TRANSFORM:
        raise ValueError(f"fixed transform must be one of {tuple(RACKET_TRANSFORM)}")
    racket_name = RACKET_TRANSFORM[transform_name]
    return f"""(rule! (let ((dummy 0))
  (define (anti-transpose-grid grid) (rotate-180 (transpose grid)))
  (define (apply-transform-name name grid)
    (cond ((equal? name 'id) grid)
          ((equal? name 'rot90) (rotate-cw grid))
          ((equal? name 'rot180) (rotate-180 grid))
          ((equal? name 'rot270) (rotate-ccw grid))
          ((equal? name 'flip-h) (flip-lr grid))
          ((equal? name 'flip-v) (flip-ud grid))
          ((equal? name 'transpose) (transpose grid))
          (else (anti-transpose-grid grid))))
  (define (split-panels grid n count)
    (for/list ((i (in-range count)))
      (let ((left (* i (+ n 1))))
        (subgrid grid 0 left (- (rows grid) 1) (+ left n -1)))))
  (let* ((n (rows g))
         (panels (split-panels g n 3))
         (name '{racket_name}))
    (apply-transform-name name (third panels)))))"""


def local_crop_program(application: str) -> str:
    """Racket rival that transforms C's tight crop at its original top-left."""
    application = _validate_application(application)
    selected = "name" if application == "direct" else "(inverse-transform-name name)"
    return f"""(rule! (let ((dummy 0))
  (define (anti-transpose-grid grid) (rotate-180 (transpose grid)))
  (define (apply-transform-name name grid)
    (cond ((equal? name 'id) grid)
          ((equal? name 'rot90) (rotate-cw grid))
          ((equal? name 'rot180) (rotate-180 grid))
          ((equal? name 'rot270) (rotate-ccw grid))
          ((equal? name 'flip-h) (flip-lr grid))
          ((equal? name 'flip-v) (flip-ud grid))
          ((equal? name 'transpose) (transpose grid))
          (else (anti-transpose-grid grid))))
  (define (inverse-transform-name name)
    (cond ((equal? name 'rot90) 'rot270)
          ((equal? name 'rot270) 'rot90)
          (else name)))
  (define (split-panels grid n count)
    (for/list ((i (in-range count)))
      (let ((left (* i (+ n 1))))
        (subgrid grid 0 left (- (rows grid) 1) (+ left n -1)))))
  (define (transform-order)
    (list 'rot90 'rot180 'rot270 'flip-h 'flip-v 'transpose))
  (let* ((n (rows g))
         (panels (split-panels g n 3))
         (a (first panels))
         (b (second panels))
         (panel (third panels))
         (name (first (filter (lambda (nm)
                                (equal? (apply-transform-name nm a) b))
                              (transform-order))))
         (selected {selected})
         (rs (filter (lambda (r)
                       (for/or ((c (range 0 n))) (!= (at panel r c) 0)))
                     (range 0 n)))
         (cs (filter (lambda (c)
                       (for/or ((r (range 0 n))) (!= (at panel r c) 0)))
                     (range 0 n)))
         (top (first rs))
         (bottom (last rs))
         (left (first cs))
         (right (last cs))
         (crop (subgrid panel top left bottom right))
         (turned (apply-transform-name selected crop)))
    (grid-from-fn n n
      (lambda (r c)
        (if (and (>= r top)
                 (< r (+ top (rows turned)))
                 (>= c left)
                 (< c (+ left (cols turned))))
            (at turned (- r top) (- c left))
            0))))))"""

