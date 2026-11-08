"""Native gravity-policy prototype for ``22304ccc509c``.

The default ``down`` setting returns the selected canonical Racket program
byte-for-byte.  The alternative ``edge_directed`` setting has a genuine
input-dependent dependency: locate the unique color-1 border anchor, convert its
edge into an intermediate gravity direction, then stable-pack every affected
row or column in that direction.  Inputs are identical across settings.
"""
from __future__ import annotations

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from reviewer_support import canonical_path, find_root


TASK_ID = "22304ccc509c"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
POLICIES = ("down", "edge_directed")
DIRECTIONS = ("up", "down", "left", "right")

EDGE_DIRECTED_PROGRAM = """(rule!
  (let* ((anchor (find-anchor g 1))
         (r (first anchor))
         (c (second anchor))
         (direction
           (cond
             ((= r 0) \"up\")
             ((= r (- (rows g) 1)) \"down\")
             ((= c 0) \"left\")
             (else \"right\"))))
    (gravity g direction)))"""


def _exact_int(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def _policy(settings: Any) -> str:
    if type(settings) is not dict or set(settings) != {"gravity_policy"}:
        raise ValueError("settings must contain only gravity_policy")
    value = settings["gravity_policy"]
    if type(value) is not str or value not in POLICIES:
        raise ValueError("gravity_policy must be down or edge_directed")
    return value


def _grid(value: Any) -> list[list[int]]:
    if (
        type(value) is not list
        or not 6 <= len(value) <= 30
        or type(value[0]) is not list
        or not 6 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must have 6..30 rows and columns")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    return value


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line))["task_id"] == TASK_ID
    }
    if len(programs) != 1:
        raise ValueError("expected one exact canonical authority program")
    return programs.pop()


def program(settings: Any) -> str:
    policy = _policy(settings)
    return canonical_program() if policy == "down" else EDGE_DIRECTED_PROGRAM


def _gravity(value: list[list[int]], direction: str, *, sort_values: bool = False) -> list[list[int]]:
    if direction not in DIRECTIONS:
        raise ValueError(f"unknown gravity direction: {direction!r}")
    h, w = len(value), len(value[0])
    output = [[0] * w for _ in range(h)]
    if direction in ("up", "down"):
        for column in range(w):
            cells = [value[row][column] for row in range(h) if value[row][column] != 0]
            if sort_values:
                cells = sorted(cells)
            start = 0 if direction == "up" else h - len(cells)
            for offset, cell in enumerate(cells):
                output[start + offset][column] = cell
    else:
        for row in range(h):
            cells = [cell for cell in value[row] if cell != 0]
            if sort_values:
                cells = sorted(cells)
            start = 0 if direction == "left" else w - len(cells)
            for offset, cell in enumerate(cells):
                output[row][start + offset] = cell
    return output


def transform_with_direction(value: Any, direction: str) -> list[list[int]]:
    grid = _grid(value)
    return _gravity(grid, direction)


def _edge_direction(anchor: tuple[int, int], h: int, w: int) -> str:
    row, column = anchor
    sides = []
    if row == 0:
        sides.append("up")
    if row == h - 1:
        sides.append("down")
    if column == 0:
        sides.append("left")
    if column == w - 1:
        sides.append("right")
    if len(sides) != 1:
        raise ValueError("color-1 anchor must lie on exactly one edge, not a corner")
    return sides[0]


def _column_values(grid: list[list[int]], column: int) -> list[int]:
    return [row[column] for row in grid if row[column] != 0]


def _row_values(grid: list[list[int]], row: int) -> list[int]:
    return [cell for cell in grid[row] if cell != 0]


def observe(value: Any) -> dict[str, Any]:
    grid = _grid(value)
    h, w = len(grid), len(grid[0])
    anchors = [
        (row, column)
        for row in range(h)
        for column in range(w)
        if grid[row][column] == 1
    ]
    if len(anchors) != 1:
        raise ValueError("grid must contain exactly one color-1 anchor")
    anchor = anchors[0]
    anchor_direction = _edge_direction(anchor, h, w)
    occupied = [
        (row, column)
        for row in range(h)
        for column in range(w)
        if grid[row][column] != 0
    ]
    if len(occupied) < 12:
        raise ValueError("scene is too sparse to teach directional gravity")
    if {min(row for row, _ in occupied), max(row for row, _ in occupied)} != {0, h - 1}:
        raise ValueError("scene must touch top and bottom boundaries")
    if {min(column for _, column in occupied), max(column for _, column in occupied)} != {0, w - 1}:
        raise ValueError("scene must touch left and right boundaries")
    if not any(
        len(cells := _column_values(grid, column)) >= 2 and cells != sorted(cells)
        for column in range(w)
    ):
        raise ValueError("scene needs a vertical order-preservation witness")
    if not any(
        len(cells := _row_values(grid, row)) >= 2 and cells != sorted(cells)
        for row in range(h)
    ):
        raise ValueError("scene needs a horizontal order-preservation witness")
    rendered = {
        direction: json.dumps(_gravity(grid, direction), separators=(",", ":"))
        for direction in DIRECTIONS
    }
    if len(set(rendered.values())) != 4:
        raise ValueError("all four gravity directions must yield distinct outputs")
    return {
        "height": h,
        "width": w,
        "anchor": [anchor[0], anchor[1]],
        "anchor_direction": anchor_direction,
        "anchor_color_count": len(anchors),
        "nonzero_count": len(occupied),
        "touches_all_boundaries": True,
        "directional_outputs_distinct": True,
    }


def direction(value: Any, policy: str) -> str:
    if type(policy) is not str or policy not in POLICIES:
        raise ValueError("policy must be down or edge_directed")
    return "down" if policy == "down" else observe(value)["anchor_direction"]


def transform(value: Any, policy: str) -> list[list[int]]:
    grid = _grid(value)
    return _gravity(grid, direction(grid, policy))


def _seeded_rng(seed: int, split: str, index: int, salt: int) -> random.Random:
    body = f"22304ccc509c-edge-gravity-v1:{seed}:{split}:{index}:{salt}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(body).digest(), "big"))


def _free_on_edge(
    rng: random.Random,
    occupied: set[tuple[int, int]],
    direction: str,
    h: int,
    w: int,
) -> tuple[int, int]:
    if direction in ("up", "down"):
        row = 0 if direction == "up" else h - 1
        candidates = [(row, column) for column in range(1, w - 1)]
    else:
        column = 0 if direction == "left" else w - 1
        candidates = [(row, column) for row in range(1, h - 1)]
    rng.shuffle(candidates)
    for cell in candidates:
        if cell not in occupied:
            return cell
    raise ValueError(f"no free non-corner cell on {direction} edge")


def _construct_grid(
    seed: int,
    split: str,
    index: int,
    h: int,
    w: int,
    anchor_direction: str,
    target_nonzero: int,
    salt: int,
) -> list[list[int]]:
    rng = _seeded_rng(seed, split, index, salt)
    grid = [[0] * w for _ in range(h)]
    occupied: set[tuple[int, int]] = set()

    anchor = _free_on_edge(rng, occupied, anchor_direction, h, w)
    grid[anchor[0]][anchor[1]] = 1
    occupied.add(anchor)

    interior_rows = [row for row in range(1, h - 1) if row != anchor[0]]
    interior_columns = [column for column in range(1, w - 1) if column != anchor[1]]
    rng.shuffle(interior_rows)
    rng.shuffle(interior_columns)
    witness_row = interior_rows.pop()
    witness_column = interior_columns.pop()

    vertical_rows = sorted(interior_rows[:2])
    horizontal_columns = sorted(interior_columns[:2])
    if len(vertical_rows) != 2 or len(horizontal_columns) != 2:
        raise ValueError("grid too small for order witnesses")
    for (row, column), color in (
        ((vertical_rows[0], witness_column), 9),
        ((vertical_rows[1], witness_column), 2),
        ((witness_row, horizontal_columns[0]), 8),
        ((witness_row, horizontal_columns[1]), 3),
    ):
        grid[row][column] = color
        occupied.add((row, column))

    for edge, color in zip(DIRECTIONS, (4, 5, 6, 7), strict=True):
        if edge == anchor_direction:
            continue
        row, column = _free_on_edge(rng, occupied, edge, h, w)
        grid[row][column] = color
        occupied.add((row, column))

    # Keep the two witness lines exact so sorting alternatives remain visible.
    candidates = [
        (row, column)
        for row in range(h)
        for column in range(w)
        if (row, column) not in occupied
        and row != witness_row
        and column != witness_column
    ]
    rng.shuffle(candidates)
    target_nonzero = min(target_nonzero, len(candidates) + len(occupied))
    while len(occupied) < target_nonzero:
        row, column = candidates.pop()
        grid[row][column] = rng.randrange(2, 10)
        occupied.add((row, column))
    return grid


_TRAIN_DIRECTIONS = ("up", "left", "right", "down", "up", "left")
_QUERY_DIRECTIONS = ("right", "down", "up", "left")
_TRAIN_PROFILES = (
    (7, 8, 18),
    (9, 9, 24),
    (11, 13, 34),
    (13, 12, 40),
    (15, 16, 52),
    (18, 18, 64),
)
_QUERY_PROFILES = (
    (10, 12, 30),
    (16, 17, 52),
    (22, 24, 76),
    (30, 30, 96),
)


def _scene(
    seed: int,
    split: str,
    index: int,
    profile: tuple[int, int, int],
    anchor_direction: str,
) -> list[list[int]]:
    h, w, count = profile
    last_error: Exception | None = None
    for salt in range(64):
        grid = _construct_grid(
            seed, split, index, h, w, anchor_direction, count, salt
        )
        try:
            observed = observe(grid)
        except ValueError as error:
            last_error = error
            continue
        if observed["anchor_direction"] == anchor_direction:
            return grid
    raise ValueError(f"could not construct valid {split} scene: {last_error}")


def _pair(grid: list[list[int]], policy: str) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": transform(grid, policy)}


def generate(seed: Any, settings: Any, demos: Any, queries: Any) -> dict[str, Any]:
    _exact_int(seed, "seed", 0, 2**63 - 1)
    _exact_int(demos, "demos", 2, 6)
    _exact_int(queries, "queries", 4, 4)
    policy = _policy(settings)

    train = [
        _pair(
            _scene(
                seed,
                "train",
                index,
                _TRAIN_PROFILES[index],
                _TRAIN_DIRECTIONS[index],
            ),
            policy,
        )
        for index in range(demos)
    ]
    test = [
        _pair(
            _scene(
                seed,
                "test",
                index,
                _QUERY_PROFILES[index],
                _QUERY_DIRECTIONS[index],
            ),
            policy,
        )
        for index in range(queries)
    ]
    inputs = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in train + test
    ]
    if len(inputs) != len(set(inputs)):
        raise ValueError("generated inputs must be distinct within an episode")
    episode = {
        "train": train,
        "test": test,
        "program_solution": program(settings),
    }
    certificate(train, [pair["input"] for pair in test])
    return episode


def _opposite(direction_name: str) -> str:
    return {"up": "down", "down": "up", "left": "right", "right": "left"}[direction_name]


def _clockwise(direction_name: str) -> str:
    return {"up": "right", "right": "down", "down": "left", "left": "up"}[direction_name]


HYPOTHESES = POLICIES + (
    "fixed_up",
    "fixed_left",
    "fixed_right",
    "opposite_edge",
    "clockwise_edge",
    "vertical_only",
    "sort_then_down",
    "sort_then_edge_directed",
    "remove_anchor_then_down",
    "remove_anchor_then_edge_directed",
    "copy_input",
)


def predict(value: Any, hypothesis: str) -> list[list[int]]:
    grid = _grid(value)
    observed = observe(grid)
    edge = observed["anchor_direction"]
    if hypothesis == "down":
        return _gravity(grid, "down")
    if hypothesis == "edge_directed":
        return _gravity(grid, edge)
    if hypothesis in ("fixed_up", "fixed_left", "fixed_right"):
        return _gravity(grid, hypothesis.removeprefix("fixed_"))
    if hypothesis == "opposite_edge":
        return _gravity(grid, _opposite(edge))
    if hypothesis == "clockwise_edge":
        return _gravity(grid, _clockwise(edge))
    if hypothesis == "vertical_only":
        return _gravity(grid, edge if edge in ("up", "down") else "down")
    if hypothesis == "sort_then_down":
        return _gravity(grid, "down", sort_values=True)
    if hypothesis == "sort_then_edge_directed":
        return _gravity(grid, edge, sort_values=True)
    if hypothesis in ("remove_anchor_then_down", "remove_anchor_then_edge_directed"):
        stripped = [row[:] for row in grid]
        row, column = observed["anchor"]
        stripped[row][column] = 0
        selected = "down" if hypothesis.endswith("then_down") else edge
        return _gravity(stripped, selected)
    if hypothesis == "copy_input":
        return [row[:] for row in grid]
    raise ValueError(f"unknown declared hypothesis: {hypothesis!r}")


def certificate(train: Any, query_inputs: Any) -> dict[str, Any]:
    """Infer from demonstrations only; query answers are deliberately absent."""
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("certificate requires 2..6 demonstrations")
    if type(query_inputs) is not list or len(query_inputs) != 4:
        raise ValueError("certificate requires exactly four query inputs")
    for pair in train:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each demonstration needs exactly input and output")
        _grid(pair["input"])
        _grid(pair["output"])
        observe(pair["input"])
    for value in query_inputs:
        observe(value)
    survivors = [
        name
        for name in HYPOTHESES
        if all(predict(pair["input"], name) == pair["output"] for pair in train)
    ]
    if len(survivors) != 1 or survivors[0] not in POLICIES:
        raise ValueError(
            "demonstrations do not identify exactly one policy against declared rivals: "
            + repr(survivors)
        )
    predictions = [predict(value, survivors[0]) for value in query_inputs]
    return {
        "declared_hypotheses": list(HYPOTHESES),
        "survivors": survivors,
        "demos": len(train),
        "queries": len(query_inputs),
        "demo_anchor_directions": [
            observe(pair["input"])["anchor_direction"] for pair in train
        ],
        "predicted_query_sha256": [
            hashlib.sha256(
                json.dumps(value, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            for value in predictions
        ],
        "scope": (
            "Finite declared-rival certificate from demonstrations only; it is "
            "not a proof of unique induction against every possible rule."
        ),
    }
