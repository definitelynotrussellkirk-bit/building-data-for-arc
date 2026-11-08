"""Matched-input wall-scope family for task 85d01dd02c6d.

The canonical setting treats every color-9 cell as a ray blocker.  The nearby
alternative first identifies color-9 cells that belong to an axis-spanning full
row or column and uses only that input-derived mask as blockers.  Both settings
then cast the original inclusive cardinal rays, count visible seeds per cell,
and paint color 8 where the count reaches two.

Every generated scene contains three independent witnesses:

* a clear aligned seed pair that creates positive overlap under both settings;
* a pair separated by an axis-spanning divider, blocked under both settings;
* a pair separated by a short orthogonal wall, blocked only by ``every_wall``.

Inputs are independent of the hidden setting, demonstrations and queries have
stable prefixes, and the fourth query is a substantive 30x30 construction.
Python labels are authoring claims; native qualification re-executes every label
through protected Racket.
"""
from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable


TASK_ID = "85d01dd02c6d"
HERE = Path(__file__).resolve().parent
WALL_SCOPES = ("every_wall", "axis_dividers")
CANONICAL_PROGRAM = (HERE / "canonical.rkt").read_text(encoding="utf-8")
AXIS_DIVIDERS_PROGRAM = (HERE / "axis_dividers.rkt").read_text(encoding="utf-8")


class SceneSpec:
    __slots__ = ("full_orientation", "height", "width", "partial_side", "distractors")

    def __init__(self, full_orientation: str, height: int, width: int, partial_side: str, distractors: int):
        self.full_orientation = full_orientation
        self.height = height
        self.width = width
        self.partial_side = partial_side
        self.distractors = distractors


_TRAIN_SPECS = (
    SceneSpec("vertical", 11, 13, "left", 1),
    SceneSpec("horizontal", 13, 11, "left", 1),
    SceneSpec("vertical", 15, 17, "right", 2),
    SceneSpec("horizontal", 17, 15, "right", 2),
    SceneSpec("vertical", 21, 23, "left", 3),
    SceneSpec("horizontal", 23, 21, "right", 3),
)
_QUERY_SPECS = (
    SceneSpec("vertical", 12, 14, "right", 2),
    SceneSpec("horizontal", 14, 12, "left", 2),
    SceneSpec("vertical", 19, 25, "left", 3),
    SceneSpec("horizontal", 30, 30, "right", 4),
)


def _exact_int(value: Any, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an integer in {low}..{high}; bool is forbidden")
    return value


def normalize_settings(settings: dict[str, Any]) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"wall_scope"}:
        raise ValueError("settings must contain exactly wall_scope")
    scope = settings["wall_scope"]
    if type(scope) is not str or scope not in WALL_SCOPES:
        raise ValueError(f"wall_scope must be one of {WALL_SCOPES}")
    return {"wall_scope": scope}


def program(settings: dict[str, Any]) -> str:
    scope = normalize_settings(settings)["wall_scope"]
    return CANONICAL_PROGRAM if scope == "every_wall" else AXIS_DIVIDERS_PROGRAM


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"{TASK_ID}:wall-scope-v1:{seed}:{split}:{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _frame(height: int, width: int) -> list[list[int]]:
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for col in range(width):
        grid[0][col] = 9
        grid[height - 1][col] = 9
    for row in range(height):
        grid[row][0] = 9
        grid[row][width - 1] = 9
    return grid


def _segment_cells(center: tuple[int, int], orientation: str) -> tuple[tuple[int, int], ...]:
    row, col = center
    if orientation == "vertical":
        return ((row - 1, col), (row, col), (row + 1, col))
    if orientation == "horizontal":
        return ((row, col - 1), (row, col), (row, col + 1))
    raise ValueError(f"unknown segment orientation: {orientation}")


def _line(a: tuple[int, int], b: tuple[int, int]) -> set[tuple[int, int]]:
    if a[0] == b[0]:
        return {(a[0], col) for col in range(min(a[1], b[1]), max(a[1], b[1]) + 1)}
    if a[1] == b[1]:
        return {(row, a[1]) for row in range(min(a[0], b[0]), max(a[0], b[0]) + 1)}
    raise ValueError("witness endpoints must be cardinally aligned")


def _quadrant_centers(height: int, width: int) -> list[tuple[int, int]]:
    return [
        (max(2, height // 4), max(2, width // 4)),
        (max(2, height // 4), min(width - 3, 3 * width // 4)),
        (min(height - 3, 3 * height // 4), max(2, width // 4)),
        (min(height - 3, 3 * height // 4), min(width - 3, 3 * width // 4)),
    ]


def _add_distractors(
    grid: list[list[int]],
    reserved: set[tuple[int, int]],
    count: int,
    rng: random.Random,
) -> None:
    """Add short, non-spanning wall segments away from the causal corridors."""
    height, width = len(grid), len(grid[0])
    centers = _quadrant_centers(height, width)
    if count < 4:
        offset = rng.randrange(4)
        centers = centers[offset:] + centers[:offset]
    added = 0
    for target_index in range(count):
        base_row, base_col = centers[target_index % len(centers)]
        candidates: list[tuple[int, int, str]] = []
        for radius in range(0, 5):
            for dr, dc in (
                (0, 0), (-radius, 0), (radius, 0), (0, -radius), (0, radius),
                (-radius, -radius), (-radius, radius), (radius, -radius), (radius, radius),
            ):
                row, col = base_row + dr, base_col + dc
                orientations = ["vertical", "horizontal"]
                if rng.randrange(2):
                    orientations.reverse()
                candidates.extend((row, col, orientation) for orientation in orientations)
        placed = False
        for row, col, orientation in candidates:
            cells = _segment_cells((row, col), orientation)
            if any(not (1 <= r < height - 1 and 1 <= c < width - 1) for r, c in cells):
                continue
            if any((r, c) in reserved or grid[r][c] != 0 for r, c in cells):
                continue
            for r, c in cells:
                grid[r][c] = 9
            reserved.update(cells)
            added += 1
            placed = True
            break
        if not placed:
            raise RuntimeError(f"could not place distractor segment {target_index + 1}/{count}")
    if added != count:
        raise AssertionError("distractor accounting error")


def _vertical_scene(spec: SceneSpec, rng: random.Random) -> list[list[int]]:
    height, width = spec.height, spec.width
    if height < 9 or width < 11:
        raise ValueError("vertical scene needs at least 9 rows and 11 columns")
    grid = _frame(height, width)

    low, high = 5, width - 6
    divider_col = min(max(width // 2 + rng.choice((-1, 0, 1)), low), high)
    for row in range(height):
        grid[row][divider_col] = 9

    segment_row = min(max(height // 2 + rng.choice((-1, 0, 1)), 4), height - 5)
    if spec.partial_side == "left":
        segment_options = sorted({2, divider_col - 2})
        segment_col = rng.choice(segment_options)
        clear_col = divider_col - 1 if abs((divider_col - 1) - segment_col) >= 2 else 1
        far_col = min(width - 2, divider_col + 2)
    elif spec.partial_side == "right":
        segment_options = sorted({divider_col + 2, width - 3})
        segment_col = rng.choice(segment_options)
        clear_col = divider_col + 1 if abs((divider_col + 1) - segment_col) >= 2 else width - 2
        far_col = max(1, divider_col - 2)
    else:
        raise ValueError("partial_side must be left or right")

    partial_cells = _segment_cells((segment_row, segment_col), "horizontal")
    for row, col in partial_cells:
        if grid[row][col] != 0:
            raise AssertionError("partial wall overlaps a structural wall")
        grid[row][col] = 9

    near = (segment_row - 2, segment_col)
    across_partial = (segment_row + 2, segment_col)
    clear_partner = (segment_row - 2, clear_col)
    across_divider = (segment_row - 2, far_col)
    seed_cells = (near, across_partial, clear_partner, across_divider)
    if len(set(seed_cells)) != 4 or any(grid[row][col] != 0 for row, col in seed_cells):
        raise AssertionError("seed layout is not disjoint from walls")
    colors = rng.sample((1, 2, 3, 4, 5, 6, 7), 4)
    for (row, col), color in zip(seed_cells, colors, strict=True):
        grid[row][col] = color

    reserved = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    reserved.update(_line(near, across_partial))
    reserved.update(_line(near, clear_partner))
    reserved.update(_line(clear_partner, across_divider))
    _add_distractors(grid, reserved, spec.distractors, rng)
    return grid


def _transpose(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid, strict=True)]


def sample_input(seed: int, index: int, *, split: str) -> list[list[int]]:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    if split == "train":
        specs = _TRAIN_SPECS
    elif split == "test":
        specs = _QUERY_SPECS
    else:
        raise ValueError("split must be train or test")
    _exact_int(index, 0, len(specs) - 1, "index")
    spec = specs[index]
    rng = _rng(seed, split, index)
    if spec.full_orientation == "vertical":
        grid = _vertical_scene(spec, rng)
    elif spec.full_orientation == "horizontal":
        base = SceneSpec("vertical", spec.width, spec.height, spec.partial_side, spec.distractors)
        grid = _transpose(_vertical_scene(base, rng))
    else:
        raise AssertionError("invalid scene specification")
    analysis = analyze_scene(grid)
    required = (
        analysis["clear_overlap_witness"],
        analysis["full_divider_blocked_witness"],
        analysis["partial_wall_setting_witness"],
    )
    if not all(required):
        raise RuntimeError(f"constructed scene lost a required witness: {analysis}")
    if solve_python(grid, {"wall_scope": "every_wall"}) == solve_python(
        grid, {"wall_scope": "axis_dividers"}
    ):
        raise RuntimeError("constructed scene does not distinguish wall_scope")
    return grid


def _seeds(grid: list[list[int]]) -> list[tuple[int, int, int]]:
    return [
        (row, col, value)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value not in (0, 9)
    ]


def _axis_divider_blockers(grid: list[list[int]]) -> set[tuple[int, int]]:
    height, width = len(grid), len(grid[0])
    full_rows = {row for row in range(height) if all(grid[row][col] == 9 for col in range(width))}
    full_cols = {col for col in range(width) if all(grid[row][col] == 9 for row in range(height))}
    return {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 9 and (row in full_rows or col in full_cols)
    }


def _blocking_cells(grid: list[list[int]], scope: str) -> set[tuple[int, int]]:
    if scope == "every_wall":
        return {
            (row, col)
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
            if value == 9
        }
    if scope == "axis_dividers":
        return _axis_divider_blockers(grid)
    if scope == "no_walls":
        return set()
    raise ValueError(f"unknown wall scope: {scope}")


def _visible(
    blockers: set[tuple[int, int]],
    seed: tuple[int, int, int],
    row: int,
    col: int,
) -> bool:
    seed_row, seed_col, _ = seed
    if seed_row == row:
        return not any(
            (row, scan_col) in blockers
            for scan_col in range(min(seed_col, col), max(seed_col, col) + 1)
        )
    if seed_col == col:
        return not any(
            (scan_row, col) in blockers
            for scan_row in range(min(seed_row, row), max(seed_row, row) + 1)
        )
    return False


def solve_with_scope(grid: list[list[int]], scope: str, *, threshold: int = 2) -> list[list[int]]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty rectangular list")
    width = len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    _exact_int(threshold, 1, 9, "threshold")
    blockers = _blocking_cells(grid, scope)
    seeds = _seeds(grid)
    return [
        [
            9
            if grid[row][col] == 9
            else 8
            if sum(_visible(blockers, seed, row, col) for seed in seeds) >= threshold
            else 0
            for col in range(width)
        ]
        for row in range(len(grid))
    ]


def solve_python(grid: list[list[int]], settings: dict[str, Any]) -> list[list[int]]:
    return solve_with_scope(grid, normalize_settings(settings)["wall_scope"])


def _between(a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
    points = sorted(_line(a, b))
    return [point for point in points if point not in {a, b}]


def analyze_scene(grid: list[list[int]]) -> dict[str, Any]:
    height, width = len(grid), len(grid[0])
    full_cols = [
        col for col in range(1, width - 1) if all(grid[row][col] == 9 for row in range(height))
    ]
    full_rows = [
        row for row in range(1, height - 1) if all(grid[row][col] == 9 for col in range(width))
    ]
    orientation = "vertical" if len(full_cols) == 1 and not full_rows else "horizontal" if len(full_rows) == 1 and not full_cols else None
    seeds = [(row, col) for row, col, _ in _seeds(grid)]
    axis = _axis_divider_blockers(grid)
    clear = False
    full = False
    partial = False
    partial_orientation = None
    for left_index, left in enumerate(seeds):
        for right in seeds[left_index + 1 :]:
            if left[0] != right[0] and left[1] != right[1]:
                continue
            between = _between(left, right)
            wall_cells = {point for point in between if grid[point[0]][point[1]] == 9}
            if not wall_cells:
                clear = True
            elif wall_cells & axis:
                full = True
            else:
                partial = True
                partial_orientation = "vertical" if left[0] == right[0] else "horizontal"
    return {
        "shape": [height, width],
        "seed_count": len(seeds),
        "full_divider_orientation": orientation,
        "partial_wall_orientation": partial_orientation,
        "clear_overlap_witness": clear,
        "full_divider_blocked_witness": full,
        "partial_wall_setting_witness": partial,
        "axis_blocker_count": len(axis),
        "wall_count": sum(value == 9 for row in grid for value in row),
    }


def generate(
    seed: int,
    settings: dict[str, Any],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    _exact_int(seed, 0, 2**63 - 1, "seed")
    normalized = normalize_settings(settings)
    _exact_int(demos, 2, 6, "demos")
    _exact_int(queries, 1, 4, "queries")
    result: dict[str, Any] = {"train": [], "test": [], "program_solution": program(normalized)}
    seen: set[str] = set()
    for split, count in (("train", demos), ("test", queries)):
        for index in range(count):
            grid = sample_input(seed, index, split=split)
            key = json.dumps(grid, separators=(",", ":"))
            if key in seen:
                raise RuntimeError(f"duplicate input at {split}[{index}]")
            seen.add(key)
            result[split].append({"input": grid, "output": solve_python(grid, normalized)})
    result["sampling"] = {"draws": demos + queries, "duplicate_rejections": 0}
    return result


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    from reviewer_support import public_challenge_bytes

    return json.loads(public_challenge_bytes(episode))


def public_turn(episode: dict[str, Any], query_index: int) -> dict[str, Any]:
    public = public_challenge(episode)
    if type(query_index) is not int or not 0 <= query_index < len(public["test"]):
        raise IndexError("query_index is outside this episode")
    return {
        "train": copy.deepcopy(public["train"]),
        "test": [copy.deepcopy(public["test"][query_index])],
    }


def controller_turns(episode: dict[str, Any]) -> list[dict[str, Any]]:
    public = public_challenge(episode)
    return [public_turn(public, index) for index in range(len(public["test"]))]


def _racket_program(scope: str, threshold: int) -> str:
    if scope == "every_wall":
        blocker = "(= (at g r c) 9)"
    elif scope == "axis_dividers":
        blocker = """(and (= (at g r c) 9)
           (or (for/and ([rr (in-range (rows g))]) (= (at g rr c) 9))
               (for/and ([cc (in-range (cols g))]) (= (at g r cc) 9))))"""
    elif scope == "no_walls":
        blocker = "#f"
    else:
        raise ValueError(f"unknown Racket wall scope: {scope}")
    _exact_int(threshold, 1, 9, "threshold")
    return f"""(rule!
  (let ((seeds (filter (lambda (cell)
                         (let ((v (third cell))) (and (not (= v 0)) (not (= v 9)))))
                       (grid-cells g))))
    (define (blocking-wall? r c)
      {blocker})
    (define (clear-row? r c1 c2)
      (for/and ([c (in-range (min c1 c2) (+ (max c1 c2) 1))])
        (not (blocking-wall? r c))))
    (define (clear-col? c r1 r2)
      (for/and ([r (in-range (min r1 r2) (+ (max r1 r2) 1))])
        (not (blocking-wall? r c))))
    (define (visible? seed r c)
      (let ((sr (first seed)) (sc (second seed)))
        (or (and (= sr r) (clear-row? r sc c))
            (and (= sc c) (clear-col? c sr r)))))
    (grid-from-fn (rows g) (cols g)
      (lambda (r c)
        (cond [(= (at g r c) 9) 9]
              [(>= (count-where (lambda (seed) (visible? seed r c)) seeds) {threshold}) 8]
              [else 0])))))"""


def rival_programs(settings: dict[str, Any]) -> dict[str, str]:
    scope = normalize_settings(settings)["wall_scope"]
    other = "axis_dividers" if scope == "every_wall" else "every_wall"
    return {
        "other_wall_scope": program({"wall_scope": other}),
        "ignore_all_internal_walls": _racket_program("no_walls", 2),
        "one_seed_suffices": _racket_program(scope, 1),
    }
