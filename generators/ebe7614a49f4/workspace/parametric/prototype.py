"""Episode-fixed point/ray variants for ``ebe7614a49f4``.

``points`` is the exact canonical row/column activation rule.  ``rays`` first
computes the same active-row × active-column intersection coordinates, then
uses those coordinates as an input-dependent selector: direction codes at the
selected cells launch obstacle-bounded rays.  Direction codes elsewhere are
explicit decoys, so the second stage cannot be performed correctly without the
first-stage intermediate.

The sampler is independent of the private setting.  Every episode supports
2..6 demonstrations and exactly four distinct private queries; labels are
replayed by protected Racket during native authoring preflight.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Callable

from reviewer_support import canonical_path, find_root

TASK_ID = "ebe7614a49f4"
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent
PARAMETERS = {"render": ["points", "rays"]}
DEFAULT = {"render": "points"}
SETTINGS = [{"render": value} for value in PARAMETERS["render"]]
DEMO_LIMITS = (2, 6)
QUERY_COUNT = 4
DIRECTIONS = {4: (-1, 0), 5: (0, 1), 6: (1, 0), 7: (0, -1)}

# h, w, frame top/left/bottom/right, active-row count, active-column count,
# geometry pattern.  The final query is a substantive 30x30 boundary case.
_DEMO_PROFILES = (
    (11, 13, 1, 1, 9, 11, 2, 3, 0),
    (13, 11, 1, 1, 11, 9, 3, 2, 1),
    (15, 17, 2, 2, 12, 14, 3, 4, 2),
    (18, 20, 2, 2, 15, 17, 4, 3, 3),
    (22, 24, 2, 2, 19, 21, 4, 5, 4),
    (26, 28, 2, 2, 23, 25, 5, 5, 5),
)
_QUERY_PROFILES = (
    (12, 14, 1, 1, 10, 12, 3, 3, 6),
    (17, 19, 2, 2, 14, 16, 4, 3, 7),
    (24, 27, 2, 2, 21, 24, 4, 5, 8),
    (30, 30, 0, 0, 29, 29, 5, 5, 9),
)


def _canonical_program() -> str:
    matches: list[str] = []
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            program_value = row.get("program_solution")
            if isinstance(program_value, str):
                matches.append(program_value)
    if not matches or len(set(matches)) != 1:
        raise RuntimeError(f"expected one exact canonical program for {TASK_ID}")
    return matches[0]


CANONICAL_PROGRAM = _canonical_program()
RAYS_PROGRAM = (HERE / "rays.rkt").read_text(encoding="utf-8")
ALL_DIRECTION_TOKENS_PROGRAM = (HERE / "all_direction_tokens.rkt").read_text(encoding="utf-8")


def _integer(value: Any, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _settings(value: object) -> dict[str, str]:
    if type(value) is not dict or set(value) != {"render"}:
        raise ValueError("settings must contain exactly render")
    render = value["render"]
    if type(render) is not str or render not in PARAMETERS["render"]:
        raise ValueError("render must be points or rays")
    return {"render": render}


def program(settings: object) -> str:
    selected = _settings(settings)
    return CANONICAL_PROGRAM if selected["render"] == "points" else RAYS_PROGRAM


def _grid(value: object) -> list[list[int]]:
    if (
        type(value) is not list
        or not 1 <= len(value) <= 30
        or type(value[0]) is not list
        or not 1 <= len(value[0]) <= 30
    ):
        raise ValueError("grid must be a rectangular 1..30 list")
    width = len(value[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in value
    ):
        raise ValueError("grid cells must be exact ARC integers in a rectangle")
    return copy.deepcopy(value)


def digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def active_rows(grid: object, marker: int = 1) -> tuple[int, ...]:
    checked = _grid(grid)
    return tuple(row for row, values in enumerate(checked) if marker in values)


def active_cols(grid: object, marker: int = 2) -> tuple[int, ...]:
    checked = _grid(grid)
    return tuple(
        col
        for col in range(len(checked[0]))
        if any(row[col] == marker for row in checked)
    )


def intersections(grid: object) -> frozenset[tuple[int, int]]:
    checked = _grid(grid)
    rows = tuple(row for row, values in enumerate(checked) if 1 in values)
    cols = tuple(
        col
        for col in range(len(checked[0]))
        if any(row[col] == 2 for row in checked)
    )
    return frozenset((row, col) for row in rows for col in cols)


def _trace(
    grid: list[list[int]],
    start: tuple[int, int],
    *,
    direction: tuple[int, int] | None = None,
    obstacles: bool = True,
) -> tuple[tuple[int, int], ...]:
    row, col = start
    delta = direction if direction is not None else DIRECTIONS.get(grid[row][col])
    if delta is None:
        return ()
    dr, dc = delta
    result = [(row, col)]
    while True:
        nr, nc = row + dr, col + dc
        if not (0 <= nr < len(grid) and 0 <= nc < len(grid[0])):
            break
        if obstacles and grid[nr][nc] == 8:
            break
        result.append((nr, nc))
        row, col = nr, nc
    return tuple(result)


def _paint(height: int, width: int, cells: set[tuple[int, int]] | frozenset[tuple[int, int]]) -> list[list[int]]:
    output = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in cells:
        output[row][col] = 3
    return output


def route_cells(grid: object, starts: object | None = None, *, obstacles: bool = True) -> frozenset[tuple[int, int]]:
    checked = _grid(grid)
    if starts is None:
        selected = intersections(checked)
    else:
        try:
            selected = frozenset((int(row), int(col)) for row, col in starts)
        except Exception as exc:  # pragma: no cover - defensive API boundary
            raise ValueError("starts must be row/column pairs") from exc
    result: set[tuple[int, int]] = set()
    for start in sorted(selected):
        result.update(_trace(checked, start, obstacles=obstacles))
    return frozenset(result)


def transform(grid: object, settings: object) -> list[list[int]]:
    checked = _grid(grid)
    selected = _settings(settings)
    starts = intersections(checked)
    cells = starts if selected["render"] == "points" else route_cells(checked, starts)
    return _paint(len(checked), len(checked[0]), set(cells))


def _rng(seed: int, split: str, index: int) -> random.Random:
    _integer(seed, "seed", 0, 2**63 - 1)
    payload = json.dumps([TASK_ID, seed, split, index], separators=(",", ":")).encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest(), "big"))


def _profile(split: str, index: int) -> tuple[int, ...]:
    if split not in {"train", "test"}:
        raise ValueError("split must be train or test")
    profiles = _DEMO_PROFILES if split == "train" else _QUERY_PROFILES
    _integer(index, "index", 0, len(profiles) - 1)
    return profiles[index]


def _stratified(values: list[int], count: int, rng: random.Random) -> list[int]:
    if count < 1 or len(values) < count:
        raise ValueError("profile cannot support requested active positions")
    selected: list[int] = []
    for index in range(count):
        lo = index * len(values) // count
        hi = (index + 1) * len(values) // count
        bucket = values[lo:hi]
        selected.append(rng.choice(bucket))
    if len(set(selected)) != count:
        raise RuntimeError("stratified selection collapsed")
    return sorted(selected)


def _perimeter(top: int, left: int, bottom: int, right: int) -> set[tuple[int, int]]:
    return (
        {(top, col) for col in range(left, right + 1)}
        | {(bottom, col) for col in range(left, right + 1)}
        | {(row, left) for row in range(top, bottom + 1)}
        | {(row, right) for row in range(top, bottom + 1)}
    )


def _gap_for(start: tuple[int, int], code: int, frame: tuple[int, int, int, int]) -> tuple[int, int]:
    row, col = start
    top, left, bottom, right = frame
    if code == 4:
        return (top, col)
    if code == 5:
        return (row, right)
    if code == 6:
        return (bottom, col)
    if code == 7:
        return (row, left)
    raise ValueError(code)


def _place(grid: list[list[int]], cell: tuple[int, int], color: int) -> None:
    row, col = cell
    if grid[row][col] != 0:
        raise RuntimeError(f"scene roles overlap at {cell}: {grid[row][col]} vs {color}")
    grid[row][col] = color


def _choose_free(
    candidates: list[tuple[int, int]],
    count: int,
    occupied: set[tuple[int, int]],
    rng: random.Random,
) -> list[tuple[int, int]]:
    choices = list(candidates)
    rng.shuffle(choices)
    selected = []
    for cell in choices:
        if cell not in occupied:
            occupied.add(cell)
            selected.append(cell)
            if len(selected) == count:
                return selected
    raise RuntimeError("profile ran out of free cells")


def sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    h, w, top, left, bottom, right, n_rows, n_cols, pattern = _profile(split, index)
    rng = _rng(seed, split, index)
    inner_rows = list(range(top + 1, bottom))
    inner_cols = list(range(left + 1, right))
    rows = _stratified(inner_rows, n_rows, rng)
    cols = _stratified(inner_cols, n_cols, rng)
    inactive_rows = [row for row in inner_rows if row not in rows]
    inactive_cols = [col for col in inner_cols if col not in cols]
    if not inactive_rows or not inactive_cols:
        raise RuntimeError("profile needs inactive rows and columns for markers/decoys")

    grid = [[0 for _ in range(w)] for _ in range(h)]
    frame = (top, left, bottom, right)
    frame_cells = _perimeter(*frame)

    starts = [(row, col) for row in rows for col in cols]
    codes: dict[tuple[int, int], int] = {}
    for order, cell in enumerate(starts):
        codes[cell] = 4 + ((order + pattern) % 4)

    # Open one route of every present direction.  The remaining routes stop at
    # the visible obstacle frame; the opened routes continue to the real grid
    # boundary.  This gives the obstacle/boundary branch to the minimum lesson.
    opened: set[int] = set()
    gaps: set[tuple[int, int]] = set()
    for cell in starts:
        code = codes[cell]
        if code not in opened:
            gaps.add(_gap_for(cell, code, frame))
            opened.add(code)
    frame_cells -= gaps
    for cell in sorted(frame_cells):
        _place(grid, cell, 8)

    occupied = set(frame_cells)
    for row in rows:
        redundancy = 2 if (row + pattern) % 3 == 0 else 1
        candidates = [(row, col) for col in inactive_cols]
        for cell in _choose_free(candidates, redundancy, occupied, rng):
            _place(grid, cell, 1)
    for col in cols:
        redundancy = 2 if (col + pattern) % 3 == 1 else 1
        candidates = [(row, col) for row in inactive_rows]
        for cell in _choose_free(candidates, redundancy, occupied, rng):
            _place(grid, cell, 2)

    for cell in starts:
        occupied.add(cell)
        _place(grid, cell, codes[cell])

    # Decoy direction tokens cover row-only, column-only, and neither-role
    # coordinates.  The first anchor lies on an inactive row and points right,
    # guaranteeing that an all-direction-token shortcut paints cells that the
    # selected-intersection rule cannot reach by the same horizontal route.
    anchor = (inactive_rows[0], inactive_cols[0])
    occupied.add(anchor)
    _place(grid, anchor, 5)
    decoy_target = len(starts)
    decoys = [anchor]
    categories = [
        [(row, col) for row in rows for col in inactive_cols],
        [(row, col) for row in inactive_rows for col in cols],
        [(row, col) for row in inactive_rows for col in inactive_cols],
        [
            (row, col)
            for row in range(h)
            for col in range(w)
            if not (top <= row <= bottom and left <= col <= right)
        ],
    ]
    category_index = 0
    empty_categories = 0
    while len(decoys) < decoy_target:
        candidates = categories[category_index % len(categories)]
        category_index += 1
        available = [cell for cell in candidates if cell not in occupied]
        if not available:
            empty_categories += 1
            if empty_categories >= len(categories):
                raise RuntimeError("could not place required direction decoys")
            continue
        empty_categories = 0
        cell = rng.choice(available)
        occupied.add(cell)
        decoys.append(cell)
        _place(grid, cell, 4 + ((len(decoys) + pattern) % 4))

    # Non-direction distractors defeat any generic nonzero-row/column shortcut.
    distractor_count = min(6, max(2, len(starts) // 3))
    free = [
        (row, col)
        for row in range(h)
        for col in range(w)
        if (row, col) not in occupied
    ]
    for cell in _choose_free(free, distractor_count, occupied, rng):
        _place(grid, cell, 9)

    info = profile(grid)
    if not info["sequentially_decisive"]:
        raise RuntimeError("constructed scene did not require the intersection selector")
    return grid


def _all_direction_tokens(grid: object, *, obstacles: bool = True) -> list[list[int]]:
    checked = _grid(grid)
    starts = {
        (row, col)
        for row, values in enumerate(checked)
        for col, value in enumerate(values)
        if value in DIRECTIONS
    }
    cells: set[tuple[int, int]] = set()
    for start in starts:
        cells.update(_trace(checked, start, obstacles=obstacles))
    return _paint(len(checked), len(checked[0]), cells)


def _wrong_roles(grid: object) -> list[list[int]]:
    checked = _grid(grid)
    rows = [row for row, values in enumerate(checked) if 2 in values]
    cols = [
        col
        for col in range(len(checked[0]))
        if any(row[col] == 1 for row in checked)
    ]
    cells: set[tuple[int, int]] = set()
    for start in ((row, col) for row in rows for col in cols):
        cells.update(_trace(checked, start))
    return _paint(len(checked), len(checked[0]), cells)


def _row_or_column_tokens(grid: object) -> list[list[int]]:
    checked = _grid(grid)
    rows = set(active_rows(checked))
    cols = set(active_cols(checked))
    starts = {
        (row, col)
        for row, values in enumerate(checked)
        for col, value in enumerate(values)
        if value in DIRECTIONS and (row in rows or col in cols)
    }
    cells: set[tuple[int, int]] = set()
    for start in starts:
        cells.update(_trace(checked, start))
    return _paint(len(checked), len(checked[0]), cells)


def _all_direction_points(grid: object) -> list[list[int]]:
    checked = _grid(grid)
    cells = {
        (row, col)
        for row, values in enumerate(checked)
        for col, value in enumerate(values)
        if value in DIRECTIONS
    }
    return _paint(len(checked), len(checked[0]), cells)


def _ignore_obstacles(grid: object) -> list[list[int]]:
    checked = _grid(grid)
    cells: set[tuple[int, int]] = set()
    for start in intersections(checked):
        cells.update(_trace(checked, start, obstacles=False))
    return _paint(len(checked), len(checked[0]), cells)


def _fixed_up(grid: object) -> list[list[int]]:
    checked = _grid(grid)
    cells: set[tuple[int, int]] = set()
    for start in intersections(checked):
        cells.update(_trace(checked, start, direction=(-1, 0)))
    return _paint(len(checked), len(checked[0]), cells)


def _crosses(grid: object) -> list[list[int]]:
    checked = _grid(grid)
    cells: set[tuple[int, int]] = set()
    for row, col in intersections(checked):
        cells.update((row, c) for c in range(len(checked[0])))
        cells.update((r, col) for r in range(len(checked)))
    return _paint(len(checked), len(checked[0]), cells)


def _nonzero_activation_points(grid: object) -> list[list[int]]:
    checked = _grid(grid)
    rows = [row for row, values in enumerate(checked) if any(value != 0 for value in values)]
    cols = [
        col
        for col in range(len(checked[0]))
        if any(row[col] != 0 for row in checked)
    ]
    return _paint(len(checked), len(checked[0]), {(row, col) for row in rows for col in cols})


_RIVALS: dict[str, Callable[[object], list[list[int]]]] = {
    "all_direction_tokens": _all_direction_tokens,
    "all_direction_points": _all_direction_points,
    "row_or_column_tokens": _row_or_column_tokens,
    "swapped_marker_roles": _wrong_roles,
    "ignore_obstacles": _ignore_obstacles,
    "fixed_up_direction": _fixed_up,
    "intersection_crosses": _crosses,
    "all_nonzero_activation": _nonzero_activation_points,
}
RIVAL_NAMES = tuple(_RIVALS)


def _certificate(pairs: list[dict], settings: dict[str, str]) -> dict:
    survivors = [
        candidate
        for candidate in SETTINGS
        if all(transform(pair["input"], candidate) == pair["output"] for pair in pairs)
    ]
    extra_refutations = {
        name: [
            index
            for index, pair in enumerate(pairs)
            if rival(pair["input"]) != pair["output"]
        ]
        for name, rival in _RIVALS.items()
    }
    return {
        "survivors": survivors,
        "extra_refutations": extra_refutations,
        "demonstration_count": len(pairs),
        "selected": settings,
    }


def profile(grid: object) -> dict[str, object]:
    checked = _grid(grid)
    starts = intersections(checked)
    selected_codes = {cell for cell in starts if checked[cell[0]][cell[1]] in DIRECTIONS}
    all_codes = {
        (row, col)
        for row, values in enumerate(checked)
        for col, value in enumerate(values)
        if value in DIRECTIONS
    }
    routes = route_cells(checked, starts)
    all_routes_grid = _all_direction_tokens(checked)
    selected_grid = _paint(len(checked), len(checked[0]), set(routes))
    occupied = {
        (row, col)
        for row, values in enumerate(checked)
        for col, value in enumerate(values)
        if value != 0
    }
    return {
        "dimensions": (len(checked), len(checked[0])),
        "active_rows": active_rows(checked),
        "active_cols": active_cols(checked),
        "intersection_count": len(starts),
        "selected_direction_count": len(selected_codes),
        "decoy_direction_count": len(all_codes - starts),
        "route_cell_count": len(routes),
        "touches_all_boundaries": (
            any(row == 0 for row, _ in occupied)
            and any(row == len(checked) - 1 for row, _ in occupied)
            and any(col == 0 for _, col in occupied)
            and any(col == len(checked[0]) - 1 for _, col in occupied)
        ),
        "sequentially_decisive": (
            len(starts) > 0
            and len(selected_codes) == len(starts)
            and len(all_codes - starts) > 0
            and selected_grid != all_routes_grid
        ),
    }


def change_decoy_codes(grid: object) -> list[list[int]]:
    checked = _grid(grid)
    starts = intersections(checked)
    for row, values in enumerate(checked):
        for col, value in enumerate(values):
            if value in DIRECTIONS and (row, col) not in starts:
                checked[row][col] = 4 + ((value - 4 + 1) % 4)
                return checked
    raise ValueError("grid has no direction decoy")


def change_selected_code(grid: object) -> list[list[int]]:
    checked = _grid(grid)
    original = transform(checked, {"render": "rays"})
    for row, col in sorted(intersections(checked)):
        value = checked[row][col]
        if value not in DIRECTIONS:
            continue
        for offset in (1, 2, 3):
            changed = copy.deepcopy(checked)
            changed[row][col] = 4 + ((value - 4 + offset) % 4)
            if transform(changed, {"render": "rays"}) != original:
                return changed
    raise ValueError("no selected code mutation changed the output")


def certify(episode: object) -> dict:
    if type(episode) is not dict:
        raise ValueError("episode must be an object")
    settings = _settings(episode.get("settings"))
    program_solution = episode.get("program_solution")
    if program_solution != program(settings):
        raise ValueError("program_solution differs from selected setting")
    train = episode.get("train")
    test = episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        raise ValueError("episode must contain 2..6 demonstrations")
    if type(test) is not list or len(test) != 4:
        raise ValueError("episode must contain exactly four queries")
    normalized: list[dict] = []
    for pair in [*train, *test]:
        if type(pair) is not dict or set(pair) != {"input", "output"}:
            raise ValueError("each pair must contain exactly input and output")
        input_grid = _grid(pair["input"])
        output_grid = _grid(pair["output"])
        expected = transform(input_grid, settings)
        if output_grid != expected:
            raise ValueError("pair output differs from the selected rule")
        normalized.append({"input": input_grid, "output": output_grid})
    identities = [digest(pair["input"]) for pair in normalized]
    if len(identities) != len(set(identities)):
        raise ValueError("all demonstration and query inputs must be distinct")
    expected_certificate = _certificate(normalized[: len(train)], settings)
    if expected_certificate["survivors"] != [settings]:
        raise ValueError("demonstrations do not identify the declared setting")
    if any(not indices for indices in expected_certificate["extra_refutations"].values()):
        raise ValueError("minimum lesson leaves an authored shortcut unrefuted")
    if episode.get("certificate") != expected_certificate:
        raise ValueError("saved certificate differs from recomputation")
    return expected_certificate


def generate(seed: int, settings: object, demos: int, queries: int) -> dict:
    seed = _integer(seed, "seed", 0, 2**63 - 1)
    selected = _settings(settings)
    demos = _integer(demos, "demos", *DEMO_LIMITS)
    queries = _integer(queries, "queries", QUERY_COUNT, QUERY_COUNT)

    train = []
    for index in range(demos):
        input_grid = sample_input(seed, "train", index)
        train.append({"input": input_grid, "output": transform(input_grid, selected)})
    test = []
    for index in range(queries):
        input_grid = sample_input(seed, "test", index)
        test.append({"input": input_grid, "output": transform(input_grid, selected)})
    episode = {
        "settings": selected,
        "train": train,
        "test": test,
        "program_solution": program(selected),
    }
    episode["certificate"] = _certificate(train, selected)
    certify(episode)
    return episode
