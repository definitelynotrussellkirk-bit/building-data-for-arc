"""Native matched-input rectangle-fill cascade family for ``e3a2ff6ea587``.

``canonical`` is the exact archival program.  ``triggered_cascade`` preserves
that Stage A and adds one stateful Stage B: two-point colors bridge their bbox
iff exactly one endpoint lies on a cell still showing the *first qualifying
rectangle's color in the completed Stage-A grid*.  Overlapping rectangles make
that intermediate materially different from raw bbox coverage.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

TASK_ID = "e3a2ff6ea587"
PARAMETER = "cascade_mode"
MODES = ("canonical", "triggered_cascade")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_ROOT = _HOME.parents[3]
_CANONICAL_PATH = _HOME / "canonical.rkt"
_TRIGGERED_PATH = _HOME / "triggered_cascade.rkt"
_CANONICAL = _CANONICAL_PATH.read_text(encoding="utf-8")
_TRIGGERED = _TRIGGERED_PATH.read_text(encoding="utf-8")

_TRAIN_PROFILES = ((12, 15), (13, 17), (15, 18), (18, 20), (21, 24), (24, 27))
_QUERY_PROFILES = ((14, 16), (17, 21), (24, 28), (30, 30))

Grid = list[list[int]]
Cell = tuple[int, int]
Box = tuple[int, int, int, int]


def digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _strict_int(name: str, value: object, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _settings(value: object) -> str:
    if type(value) is not dict or set(value) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    mode = value[PARAMETER]
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"{PARAMETER} must be one of {MODES!r}")
    return mode


def _grid(value: object, *, name: str = "grid") -> Grid:
    if type(value) is not list or not 1 <= len(value) <= 30:
        raise ValueError(f"{name} must have 1..30 rows")
    if type(value[0]) is not list or not 1 <= len(value[0]) <= 30:
        raise ValueError(f"{name} must have 1..30 columns")
    width = len(value[0])
    result: Grid = []
    for row in value:
        if type(row) is not list or len(row) != width:
            raise ValueError(f"{name} must be rectangular")
        if any(type(cell) is not int or not 0 <= cell <= 9 for cell in row):
            raise ValueError(f"{name} cells must be exact integer ARC colors 0..9")
        result.append(list(row))
    return result


def _canonical_from_catalog() -> str:
    programs = []
    path = _ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            programs.append(row["program_solution"])
    if len(set(programs)) != 1:
        raise RuntimeError(f"expected one canonical program for {TASK_ID}, got {len(programs)}")
    return programs[0]


if _CANONICAL != _canonical_from_catalog():
    raise RuntimeError("canonical.rkt is not byte-for-byte the archival program")
if "anchor-hits" not in _TRIGGERED or "(at stage" not in _TRIGGERED:
    raise RuntimeError("triggered_cascade.rkt lost its Stage-A dependency")


def program(settings: object) -> str:
    mode = _settings(settings)
    return _CANONICAL if mode == "canonical" else _TRIGGERED


def _colors(grid: Grid) -> list[int]:
    seen: set[int] = set()
    result: list[int] = []
    for row in grid:
        for value in row:
            if value and value not in seen:
                seen.add(value)
                result.append(value)
    return result


def _cells_by_color(grid: Grid) -> dict[int, list[Cell]]:
    result: dict[int, list[Cell]] = defaultdict(list)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value:
                result[value].append((r, c))
    return dict(result)


def _bbox(cells: Iterable[Cell]) -> Box:
    points = tuple(cells)
    rows = [r for r, _ in points]
    columns = [c for _, c in points]
    return min(rows), min(columns), max(rows), max(columns)


def _corners(box: Box) -> set[Cell]:
    r1, c1, r2, c2 = box
    return {(r1, c1), (r1, c2), (r2, c1), (r2, c2)}


def _qualifying(cells: Iterable[Cell]) -> bool:
    points = tuple(cells)
    if len(points) != 4:
        return False
    box = _bbox(points)
    return box[0] < box[2] and box[1] < box[3] and set(points) == _corners(box)


def _paint(out: Grid, box: Box, color: int) -> None:
    r1, c1, r2, c2 = box
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            out[r][c] = color


def _stage(grid: Grid, *, reverse: bool = False) -> tuple[Grid, list[int]]:
    h, w = len(grid), len(grid[0])
    cells = _cells_by_color(grid)
    qualifiers = [color for color in _colors(grid) if _qualifying(cells[color])]
    paint_order = list(reversed(qualifiers)) if reverse else qualifiers
    stage = [[0 for _ in range(w)] for _ in range(h)]
    for color in paint_order:
        _paint(stage, _bbox(cells[color]), color)
    return stage, qualifiers


def intermediate(grid: object) -> Grid:
    checked = _grid(grid)
    return _stage(checked)[0]


def _cascade_from_stage(grid: Grid, stage: Grid, qualifiers: list[int]) -> Grid:
    out = copy.deepcopy(stage)
    if not qualifiers:
        return out
    anchor = qualifiers[0]
    cells = _cells_by_color(grid)
    for color in _colors(grid):
        points = cells[color]
        if len(points) != 2:
            continue
        hits = sum(stage[r][c] == anchor for r, c in points)
        if hits == 1:
            _paint(out, _bbox(points), color)
    return out


def apply_rule(grid: object, mode: str) -> Grid:
    checked = _grid(grid)
    if type(mode) is not str or mode not in MODES:
        raise ValueError(f"mode must be one of {MODES!r}")
    stage, qualifiers = _stage(checked)
    if mode == "canonical":
        return stage
    return _cascade_from_stage(checked, stage, qualifiers)


def apply_counterfactual(grid: object, kind: str) -> Grid:
    checked = _grid(grid)
    stage, qualifiers = _stage(checked)
    h, w = len(checked), len(checked[0])
    if kind == "skip_stage_a":
        return _cascade_from_stage(checked, [[0 for _ in range(w)] for _ in range(h)], qualifiers)
    if kind == "reverse_stage_order":
        reversed_stage, _ = _stage(checked, reverse=True)
        return _cascade_from_stage(checked, reversed_stage, qualifiers)
    if kind == "coverage_only":
        if not qualifiers:
            return stage
        cells = _cells_by_color(checked)
        anchor = qualifiers[0]
        hit_stage = copy.deepcopy(stage)
        r1, c1, r2, c2 = _bbox(cells[anchor])
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                hit_stage[r][c] = anchor
        # Keep the true Stage-A colors in the output; only the Stage-B predicate
        # is incorrectly driven by raw anchor-bbox coverage.
        out = copy.deepcopy(stage)
        for color in _colors(checked):
            points = cells[color]
            if len(points) == 2 and sum(hit_stage[r][c] == anchor for r, c in points) == 1:
                _paint(out, _bbox(points), color)
        return out
    raise ValueError("kind must be skip_stage_a, reverse_stage_order, or coverage_only")


def _rng(seed: int, split: str, index: int) -> random.Random:
    raw = f"{TASK_ID}|triggered-cascade-v1|{seed}|{split}|{index}".encode("utf-8")
    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:16], "big"))


def _set(grid: Grid, occupied: set[Cell], cell: Cell, color: int) -> None:
    r, c = cell
    if not (0 <= r < len(grid) and 0 <= c < len(grid[0])):
        raise RuntimeError(f"cell {cell} is out of bounds")
    if cell in occupied:
        raise RuntimeError(f"scene role collision at {cell}")
    grid[r][c] = color
    occupied.add(cell)


def _paint_points(grid: Grid, occupied: set[Cell], cells: Iterable[Cell], color: int) -> None:
    for cell in cells:
        _set(grid, occupied, cell, color)


def _free_pattern_slot(grid: Grid, occupied: set[Cell], rng: random.Random, pattern: tuple[Cell, ...]) -> tuple[Cell, ...]:
    h, w = len(grid), len(grid[0])
    max_r = max(r for r, _ in pattern)
    max_c = max(c for _, c in pattern)
    origins = [(r, c) for r in range(h - max_r) for c in range(w - max_c)]
    rng.shuffle(origins)
    origins.sort(key=lambda p: (-(p[0] + p[1]), p[0], p[1]))
    for r0, c0 in origins:
        cells = tuple((r0 + r, c0 + c) for r, c in pattern)
        if all(cell not in occupied for cell in cells):
            return cells
    raise RuntimeError("could not place distractor pattern")


def _add_nuisance(grid: Grid, occupied: set[Cell], color: int, rng: random.Random) -> None:
    """Use every row and column while remaining a many-cell nonqualifier."""
    h, w = len(grid), len(grid[0])
    nuisance: set[Cell] = set()

    def add_for_row(row: int) -> None:
        start = (row * 7 + rng.randrange(w)) % w
        for delta in range(w):
            cell = (row, (start + delta) % w)
            if cell not in occupied and cell not in nuisance:
                nuisance.add(cell)
                return
        raise RuntimeError("no free cell for nuisance row coverage")

    def add_for_column(column: int) -> None:
        start = (column * 5 + rng.randrange(h)) % h
        for delta in range(h):
            cell = ((start + delta) % h, column)
            if cell not in occupied and cell not in nuisance:
                nuisance.add(cell)
                return
        raise RuntimeError("no free cell for nuisance column coverage")

    for row in range(h):
        add_for_row(row)
    for column in range(w):
        add_for_column(column)

    # Four explicit boundary witnesses survive even when row/column choices
    # happened to use interior cells.
    for candidates in (
        [(0, c) for c in range(w)],
        [(h - 1, c) for c in range(w)],
        [(r, 0) for r in range(h)],
        [(r, w - 1) for r in range(h)],
    ):
        for cell in candidates:
            if cell not in occupied and cell not in nuisance:
                nuisance.add(cell)
                break

    if len(nuisance) < 6:
        raise RuntimeError("nuisance color must remain an obvious nonqualifier")
    _paint_points(grid, occupied, sorted(nuisance), color)


def _sample_input(seed: int, split: str, index: int) -> Grid:
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    h, w = profiles[index]
    rng = _rng(seed, split, index)
    roles = rng.sample(range(1, 10), 9)
    (
        qualifier_a,
        qualifier_b,
        positive_a,
        positive_b,
        overlap_decoy,
        two_anchor_decoy,
        three_corner,
        misplaced_four,
        nuisance,
    ) = roles

    # Build one overlapping pair, then mirror it by profile position.  Stage A
    # itself determines which rectangle is the first/anchor qualifier; trigger
    # roles are sampled only after that intermediate exists.
    row_shift = rng.randrange(2) if h >= 16 else 0
    col_shift = rng.randrange(2) if w >= 18 else 0
    r1, c1 = 1 + row_shift, 1 + col_shift
    a_height = min(h - r1 - 5, max(6, h // 3 + 3 + rng.randrange(2)))
    a_width = min(w - c1 - 5, max(7, w // 3 + 4 + rng.randrange(2)))
    a_box = (r1, c1, r1 + a_height - 1, c1 + a_width - 1)
    b_box = (
        r1 + 2,
        c1 + 3,
        min(h - 3, a_box[2] + 3 + rng.randrange(2)),
        min(w - 3, a_box[3] + 3 + rng.randrange(2)),
    )
    if not (b_box[0] < a_box[2] and b_box[1] < a_box[3]
            and b_box[2] > a_box[2] and b_box[3] > a_box[3]):
        raise RuntimeError("profile cannot realize an overlapping ordered pair")

    orientation = index % 4

    def transform(cell: Cell) -> Cell:
        row, column = cell
        if orientation & 1:
            column = w - 1 - column
        if orientation & 2:
            row = h - 1 - row
        return row, column

    def transformed_corners(box: Box) -> tuple[Cell, ...]:
        return tuple(sorted(transform(cell) for cell in _corners(box)))

    base = [[0 for _ in range(w)] for _ in range(h)]
    base_occupied: set[Cell] = set()
    _paint_points(base, base_occupied, transformed_corners(a_box), qualifier_a)
    _paint_points(base, base_occupied, transformed_corners(b_box), qualifier_b)

    stage, qualifiers = _stage(base)
    if len(qualifiers) != 2:
        raise RuntimeError("qualifier construction did not preserve two exact rectangles")
    anchor = qualifiers[0]
    cells = _cells_by_color(base)
    anchor_box = _bbox(cells[anchor])
    ar1, ac1, ar2, ac2 = anchor_box

    anchor_visible = [
        (row, column)
        for row in range(h)
        for column in range(w)
        if stage[row][column] == anchor and (row, column) not in base_occupied
    ]
    overwritten = [
        (row, column)
        for row in range(ar1, ar2 + 1)
        for column in range(ac1, ac2 + 1)
        if stage[row][column] not in (0, anchor) and (row, column) not in base_occupied
    ]
    outside = [
        (row, column)
        for row in range(h)
        for column in range(w)
        if stage[row][column] == 0 and (row, column) not in base_occupied
    ]
    boundary_outside = [
        cell for cell in outside
        if cell[0] in (0, h - 1) or cell[1] in (0, w - 1)
    ]
    interior_outside = [
        cell for cell in outside
        if cell[0] not in (0, h - 1) and cell[1] not in (0, w - 1)
    ]
    if len(anchor_visible) < 4 or not overwritten or len(boundary_outside) < 3 or len(interior_outside) < 3:
        raise RuntimeError("profile lacks trigger candidate diversity")

    # The first two training examples deliberately cross boundary profile:
    # index 0 uses boundary outside endpoints; index 1 uses interior endpoints.
    # Later profiles mix both.  Which outside position belongs to a positive or
    # overlap decoy is shuffled independently, defeating fixed-corner/rank rules.
    profile = index % 3

    def outside_sample() -> list[Cell]:
        if profile == 0:
            return rng.sample(boundary_outside, 3)
        if profile == 1:
            return rng.sample(interior_outside, 3)
        selected = rng.sample(boundary_outside, 1) + rng.sample(interior_outside, 2)
        rng.shuffle(selected)
        return selected

    chosen = None
    for _ in range(1024):
        anchors = rng.sample(anchor_visible, 4)
        overlap_point = rng.choice(overwritten)
        outs = outside_sample()
        rng.shuffle(outs)
        pairs = (
            (anchors[0], outs[0]),
            (anchors[1], outs[1]),
            (overlap_point, outs[2]),
            (anchors[2], anchors[3]),
        )
        if any(a[0] == b[0] or a[1] == b[1] for a, b in pairs):
            continue
        if len({_bbox(pair) for pair in pairs}) != 4:
            continue

        trial = copy.deepcopy(base)
        occupied = set(base_occupied)
        for pair, color in zip(
            pairs,
            (positive_a, positive_b, overlap_decoy, two_anchor_decoy),
        ):
            _paint_points(trial, occupied, pair, color)
        actual = apply_rule(trial, "triggered_cascade")
        if any(
            actual == apply_counterfactual(trial, kind)
            for kind in ("skip_stage_a", "reverse_stage_order", "coverage_only")
        ):
            continue
        chosen = trial, occupied
        break
    if chosen is None:
        raise RuntimeError("could not place causally distinguishing trigger roles")
    grid, occupied = chosen

    three_pattern = ((0, 0), (0, 2), (2, 0))
    misplaced_pattern = ((0, 0), (0, 2), (2, 0), (1, 1))
    _paint_points(grid, occupied, _free_pattern_slot(grid, occupied, rng, three_pattern), three_corner)
    _paint_points(grid, occupied, _free_pattern_slot(grid, occupied, rng, misplaced_pattern), misplaced_four)
    _add_nuisance(grid, occupied, nuisance, rng)

    analysis = analyze_scene(grid)
    if analysis["qualifying_colors"] != 2:
        raise RuntimeError(f"scene lost its two qualifiers: {analysis}")
    if analysis["positive_triggers"] != 2 or analysis["overlap_decoys"] < 1:
        raise RuntimeError(f"scene lost its trigger witnesses: {analysis}")
    actual = apply_rule(grid, "triggered_cascade")
    for kind in ("skip_stage_a", "reverse_stage_order", "coverage_only"):
        if actual == apply_counterfactual(grid, kind):
            raise RuntimeError(f"scene does not distinguish counterfactual {kind}")
    return grid


def generate(seed: object, settings: object, demos: object, queries: object) -> dict[str, object]:
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    mode = _settings(settings)

    train_inputs = [_sample_input(seed, "train", index) for index in range(MAX_DEMOS)]
    query_inputs = [_sample_input(seed, "test", index) for index in range(MAX_QUERIES)]
    selected = train_inputs[:demos] + query_inputs[:queries]
    hashes = [digest(grid) for grid in selected]
    if len(hashes) != len(set(hashes)):
        raise RuntimeError("episode inputs must be distinct")

    return {
        "train": [
            {"input": copy.deepcopy(grid), "output": apply_rule(grid, mode)}
            for grid in train_inputs[:demos]
        ],
        "test": [
            {"input": copy.deepcopy(grid), "output": apply_rule(grid, mode)}
            for grid in query_inputs[:queries]
        ],
        "program_solution": program({PARAMETER: mode}),
    }


def execute_rule(source: object, value: object, bridge=None) -> Grid:
    if type(source) is not str or not source.strip():
        raise ValueError("source must be nonempty Racket text")
    grid = _grid(value)
    from puzzle_generators.rule_wrap import wrap_rule
    from arc_repl.racket_bridge import RacketBridge

    literal = "'(" + " ".join(
        "(" + " ".join(str(cell) for cell in row) + ")" for row in grid
    ) + ")"
    expression = f"({wrap_rule(source)} {literal})"
    if bridge is not None:
        return _grid(bridge.eval_text(expression), name="Racket output")
    with RacketBridge(timeout=60) as owned:
        return _grid(owned.eval_text(expression), name="Racket output")


def analyze_scene(value: object) -> dict[str, int]:
    grid = _grid(value)
    h, w = len(grid), len(grid[0])
    cells = _cells_by_color(grid)
    colors = _colors(grid)
    stage, qualifiers = _stage(grid)
    anchor = qualifiers[0] if qualifiers else None
    anchor_box = _bbox(cells[anchor]) if anchor is not None else None

    positive = 0
    overlap = 0
    two_point = 0
    for color in colors:
        points = cells[color]
        if len(points) != 2:
            continue
        two_point += 1
        hits = sum(stage[r][c] == anchor for r, c in points) if anchor is not None else 0
        if hits == 1:
            positive += 1
        elif hits == 0 and anchor_box is not None:
            r1, c1, r2, c2 = anchor_box
            if any(r1 <= r <= r2 and c1 <= c <= c2 and stage[r][c] not in (0, anchor) for r, c in points):
                overlap += 1

    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    boundary = sum(r in (0, h - 1) or c in (0, w - 1) for r, c in nonzero)
    return {
        "height": h,
        "width": w,
        "input_nonzero": len(nonzero),
        "occupied_rows": len({r for r, _ in nonzero}),
        "occupied_columns": len({c for _, c in nonzero}),
        "boundary_nonzero": boundary,
        "qualifying_colors": len(qualifiers),
        "nonqualifying_colors": len(colors) - len(qualifiers),
        "two_point_colors": two_point,
        "positive_triggers": positive,
        "overlap_decoys": overlap,
    }


def public_turn(episode: object, query_index: object) -> dict[str, object]:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    query_index = _strict_int("query_index", query_index, 0, MAX_QUERIES - 1)
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or type(test) is not list or query_index >= len(test):
        raise ValueError("episode does not contain the requested query")
    return {
        "train": [
            {"input": _grid(pair["input"]), "output": _grid(pair["output"])}
            for pair in train
        ],
        "test": [{"input": _grid(test[query_index]["input"])}],
    }


def mutate_nuisance(value: object) -> Grid:
    """Change only a many-cell nonqualifier while preserving Stage A exactly."""
    grid = _grid(value)
    cells = _cells_by_color(grid)
    nuisance_candidates = [color for color, points in cells.items() if len(points) >= 8 and not _qualifying(points)]
    if not nuisance_candidates:
        raise ValueError("grid has no mutable nuisance color")
    color = max(nuisance_candidates, key=lambda c: len(cells[c]))
    before = _stage(grid)[0]
    old = cells[color][-1]
    grid[old[0]][old[1]] = 0
    replacement = None
    for r in reversed(range(len(grid))):
        for c in reversed(range(len(grid[0]))):
            if grid[r][c] == 0 and (r, c) != old:
                replacement = (r, c)
                break
        if replacement is not None:
            break
    if replacement is None:
        raise RuntimeError("no replacement nuisance cell")
    grid[replacement[0]][replacement[1]] = color
    if _stage(grid)[0] != before:
        raise RuntimeError("nuisance mutation changed Stage A")
    return grid
