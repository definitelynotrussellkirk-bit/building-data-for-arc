"""Source-bound prototype for the 4d0f228177b0 parametric family.

The canonical setting is the exact selected rule.  The alternate setting first
runs that expansion, then follows the produced yellow crossing ray in row order.
The first ray cell adjacent to a 7/9 payload selects a color; every cell of that
color, including remote components, is recolored cyan.  A later hit of the other
payload color is a deliberate distractor.
"""
from __future__ import annotations

from collections import deque
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Any, Callable

SETTINGS = ({"finish": "canonical"}, {"finish": "first_hit_payload"})
PAYLOAD_COLORS = (7, 9)
_NEIGHBORS8 = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),            (0, 1),
    (1, -1),  (1, 0),   (1, 1),
)


def _load_base():
    path = Path(__file__).resolve().parents[2] / "generator.py"
    name = "_base_4d0f228177b0_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_BASE = _load_base()


def _rng(seed: int, label: str) -> random.Random:
    material = f"4d0f228177b0-parametric-v1:{seed}:{label}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(material).digest()[:8], "big"))


def _grid(height: int, width: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _copy(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def validate_input(grid: Any) -> list[list[int]]:
    if type(grid) is not list or not 1 <= len(grid) <= 30:
        raise ValueError("grid must have 1..30 rows")
    if type(grid[0]) is not list or not 1 <= len(grid[0]) <= 30:
        raise ValueError("grid must have 1..30 columns")
    width = len(grid[0])
    for row in grid:
        if type(row) is not list or len(row) != width:
            raise ValueError("grid must be rectangular")
        for cell in row:
            if type(cell) is not int or not 0 <= cell <= 9:
                raise ValueError("grid cells must be exact integers 0..9")
    return _copy(grid)


def _setting(settings: Any) -> dict[str, str]:
    if type(settings) is not dict or set(settings) != {"finish"}:
        raise ValueError("settings must contain exactly finish")
    if settings["finish"] not in {"canonical", "first_hit_payload"}:
        raise ValueError("unknown finish setting")
    return {"finish": settings["finish"]}


def canonical_expand(grid: list[list[int]]) -> list[list[int]]:
    validate_input(grid)
    return _BASE.rule_mirror(grid)


def _payload_neighbor_colors(grid: list[list[int]], row: int, col: int) -> list[int]:
    values: list[int] = []
    height, width = len(grid), len(grid[0])
    for dr, dc in _NEIGHBORS8:
        rr, cc = row + dr, col + dc
        if 0 <= rr < height and 0 <= cc < width and grid[rr][cc] in PAYLOAD_COLORS:
            if grid[rr][cc] not in values:
                values.append(grid[rr][cc])
    return values


def hit_sequence(expanded: list[list[int]]) -> list[int]:
    """Distinct 7/9 colors encountered along row-major yellow ray cells."""
    validate_input(expanded)
    sequence: list[int] = []
    for row, line in enumerate(expanded):
        for col, value in enumerate(line):
            if value != 4:
                continue
            colors = _payload_neighbor_colors(expanded, row, col)
            if len(colors) > 1:
                raise ValueError(f"ambiguous payload hit at {(row, col)}: {colors}")
            if colors and colors[0] not in sequence:
                sequence.append(colors[0])
    return sequence


def _recolor_all(grid: list[list[int]], color: int | None) -> list[list[int]]:
    if color is None:
        return _copy(grid)
    return [[8 if cell == color else cell for cell in row] for row in grid]


def apply(grid: list[list[int]], settings: Any) -> list[list[int]]:
    settings = _setting(settings)
    expanded = canonical_expand(validate_input(grid))
    if settings["finish"] == "canonical":
        return expanded
    sequence = hit_sequence(expanded)
    return _recolor_all(expanded, sequence[0] if sequence else None)


def _occupied(grid: list[list[int]]) -> set[tuple[int, int]]:
    return {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}


def _paint(grid: list[list[int]], cells: list[tuple[int, int]], color: int) -> None:
    height, width = len(grid), len(grid[0])
    for row, col in cells:
        if not (0 <= row < height and 0 <= col < width):
            raise ValueError(f"cell out of bounds: {(row, col)}")
        if grid[row][col] != 0:
            raise ValueError(f"cell collision at {(row, col)}")
    for row, col in cells:
        grid[row][col] = color


def _ray(row: int, col: int, height: int, width: int) -> list[tuple[int, int]]:
    result = []
    k = 0
    while row + k < height and col - k >= 0:
        result.append((row + k, col - k))
        k += 1
    return result


def _contact_shape(ray_cell: tuple[int, int]) -> list[tuple[int, int]]:
    row, col = ray_cell
    # The anchor is adjacent only to this ray cell, not the preceding/following
    # diagonal cells.  The two-cell tail points away from the ray.
    return [(row + 1, col + 1), (row + 2, col + 1), (row + 2, col + 2)]


def _candidate_remote_shapes(height: int, width: int, *, boundary: bool) -> list[list[tuple[int, int]]]:
    right = width - 1 if boundary else width - 2
    return [
        [(1, right - 1), (1, right), (2, right - 1)],
        [(4, width - 4), (4, width - 3), (4, width - 2),
         (5, width - 4), (5, width - 3), (5, width - 2)],
        [(height - 4, width - 4), (height - 4, width - 3),
         (height - 3, width - 4), (height - 3, width - 3)],
        [(height - 2, width - 6), (height - 2, width - 5),
         (height - 2, width - 4), (height - 1, width - 4)],
    ]


def _safe_remote(
    grid: list[list[int]],
    ray_cells: list[tuple[int, int]],
    candidates: list[list[tuple[int, int]]],
    *,
    used: set[tuple[int, int]],
    center_column: int | None = None,
) -> list[tuple[int, int]]:
    forbidden = set(ray_cells)
    for rr, cc in ray_cells:
        forbidden.update((rr + dr, cc + dc) for dr, dc in _NEIGHBORS8)
    height, width = len(grid), len(grid[0])
    for shape in candidates:
        if all(
            0 <= r < height and 0 <= c < width
            and grid[r][c] == 0 and (r, c) not in used and (r, c) not in forbidden
            and (center_column is None or c <= center_column or c > center_column + 2)
            for r, c in shape
        ):
            return shape
    raise ValueError("no safe remote payload placement")


def _active_scene(
    *,
    size: int,
    vertical_color: int,
    selected: int,
    first_k: int,
    later_k: int,
    variant: int,
    include_one: bool = False,
    right_decoy_three: bool = False,
    boundary_payload: bool = False,
    dense: bool = False,
) -> list[list[int]]:
    if vertical_color not in (3, 6) or selected not in PAYLOAD_COLORS:
        raise ValueError("invalid active-scene role")
    if not 12 <= size <= 30 or not 2 <= first_k < later_k:
        raise ValueError("invalid active-scene geometry")
    grid = _grid(size, size)
    later_margin = later_k + 4
    center = min(size - 7, max(later_margin, size // 2 + (variant % 2)))
    if vertical_color == 3:
        top = 1 + (variant % 2)
        crossing_row = top + 1 + (variant % 2)
        grid[top][center] = 3
    else:
        bottom = 7 + (variant % max(1, min(4, size - 11)))
        crossing_row = bottom - 2 - (variant % 2)
        grid[bottom][center] = 6
    grid[crossing_row][center + 2] = 2

    if include_one:
        row1 = min(size - 2, crossing_row + 5)
        col1 = min(size - 3, center + 4)
        grid[row1][col1] = 1
    if right_decoy_three:
        row3 = 1
        col3 = min(size - 1, center + 5)
        if grid[row3][col3] == 0:
            grid[row3][col3] = 3

    ray_cells = _ray(crossing_row, center, size, size)
    if later_k >= len(ray_cells) - 2:
        raise ValueError("ray is too short for requested hits")
    other = 7 if selected == 9 else 9
    selected_local = _contact_shape(ray_cells[first_k])
    other_local = _contact_shape(ray_cells[later_k])
    _paint(grid, selected_local, selected)
    _paint(grid, other_local, other)

    used = set(selected_local) | set(other_local)
    candidates = _candidate_remote_shapes(size, size, boundary=boundary_payload)
    selected_candidates = candidates if variant % 2 == 0 else list(reversed(candidates))
    selected_remote = _safe_remote(
        grid, ray_cells, selected_candidates, used=used, center_column=center
    )
    _paint(grid, selected_remote, selected)
    used.update(selected_remote)
    other_candidates = (
        list(reversed(_candidate_remote_shapes(size, size, boundary=False)))
        if variant % 2 == 0
        else _candidate_remote_shapes(size, size, boundary=False)
    )
    other_remote = _safe_remote(grid, ray_cells, other_candidates, used=used, center_column=center)
    _paint(grid, other_remote, other)
    used.update(other_remote)

    # Make the unselected payload more frequent, defeating global frequency and
    # largest-payload shortcuts while the selected color still has a remote copy.
    extra_candidates = [
        [(size // 2, size - 2), (size // 2 + 1, size - 2), (size // 2 + 2, size - 2)],
        [(size - 7, size - 2), (size - 6, size - 2), (size - 5, size - 2)],
    ]
    try:
        extra_other = _safe_remote(grid, ray_cells, extra_candidates, used=used, center_column=center)
    except ValueError:
        extra_other = []
    if extra_other:
        _paint(grid, extra_other, other)
        used.update(extra_other)

    if dense and size == 30:
        for color, column in ((selected, size - 8), (other, size - 4)):
            cells = []
            for row in range(8, size - 1, 3):
                for dc in (0, 1):
                    cell = (row, column + dc)
                    if grid[cell[0]][cell[1]] == 0:
                        cells.append(cell)
            if cells:
                _paint(grid, cells, color)

    facts = scene_facts(grid)
    if facts["first_hit_color"] != selected or facts["later_hit_color"] != other:
        raise ValueError(f"constructed hit order failed: {facts}")
    return grid


def _inactive_scene(*, size: int, variant: int, boundary_payload: bool = False) -> list[list[int]]:
    if not 9 <= size <= 30:
        raise ValueError("invalid inactive size")
    grid = _grid(size, size)
    col = 2 + (variant % max(1, size - 4))
    row = min(size - 1, 6 + (variant % max(1, size - 6)))
    grid[row][col] = 6
    right = size - 1 if boundary_payload else size - 2
    _paint(grid, [(1, right - 1), (1, right), (2, right)], 7)
    _paint(grid, [(size - 3, right - 2), (size - 2, right - 2), (size - 2, right - 1)], 9)
    facts = scene_facts(grid)
    if facts["active"]:
        raise ValueError("inactive scene unexpectedly has a hit")
    return grid


def build_banks(seed: int) -> dict[str, list[list[list[int]]]]:
    if type(seed) is not int or not 0 <= seed <= 2**63 - 1:
        raise ValueError("seed must be an integer in 0..2^63-1")
    flip = _rng(seed, "roles").randrange(2)
    first = 7 if flip == 0 else 9
    second = 9 if first == 7 else 7
    j = seed % 5
    demos = [
        _active_scene(size=14 + (j % 2), vertical_color=3, selected=first,
                      first_k=2, later_k=5, variant=j),
        _active_scene(size=17 + (j % 3), vertical_color=6, selected=second,
                      first_k=3, later_k=6, variant=j + 1, include_one=True),
        _inactive_scene(size=12 + (j % 3), variant=j),
        _active_scene(size=18 + (j % 2), vertical_color=3, selected=second,
                      first_k=3, later_k=7, variant=j + 2, boundary_payload=True),
        _active_scene(size=21, vertical_color=6, selected=first,
                      first_k=2, later_k=8, variant=j + 3,
                      include_one=True, right_decoy_three=True),
        _inactive_scene(size=16 + (j % 2), variant=j + 4, boundary_payload=True),
    ]
    queries = [
        _active_scene(size=16 + (j % 2), vertical_color=3, selected=second,
                      first_k=2, later_k=6, variant=j + 5, include_one=True),
        _active_scene(size=22, vertical_color=6, selected=first,
                      first_k=4, later_k=9, variant=j + 6, right_decoy_three=True),
        _active_scene(size=30, vertical_color=6, selected=second,
                      first_k=3, later_k=10, variant=j + 7,
                      include_one=True, boundary_payload=True, dense=True),
        _inactive_scene(size=19 + (j % 2), variant=j + 8, boundary_payload=True),
    ]
    order = list(range(4))
    _rng(seed, "query-order").shuffle(order)
    queries = [queries[index] for index in order]
    all_inputs = [json.dumps(grid, separators=(",", ":")) for grid in demos + queries]
    if len(all_inputs) != len(set(all_inputs)):
        raise ValueError("scene bank contains duplicate inputs")
    return {"demos": demos, "queries": queries}


def scene_facts(grid: list[list[int]]) -> dict[str, Any]:
    grid = validate_input(grid)
    height, width = len(grid), len(grid[0])
    expanded = canonical_expand(grid)
    sequence = hit_sequence(expanded)
    vertical = 6 if any(6 in row for row in grid) else (3 if any(3 in row for row in grid) else None)
    payload_cells = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row)
                     if value in PAYLOAD_COLORS]
    return {
        "height": height,
        "width": width,
        "vertical_color": vertical,
        "active": bool(sequence),
        "first_hit_color": sequence[0] if sequence else None,
        "later_hit_color": sequence[1] if len(sequence) > 1 else None,
        "hit_sequence": sequence,
        "boundary_payload": any(r in (0, height - 1) or c in (0, width - 1)
                                for r, c, _ in payload_cells),
        "payload_counts": {color: sum(value == color for _, _, value in payload_cells)
                           for color in PAYLOAD_COLORS},
    }


def _component_recolor(grid: list[list[int]], target: int, seed_cells: set[tuple[int, int]]) -> list[list[int]]:
    if not seed_cells:
        return _copy(grid)
    height, width = len(grid), len(grid[0])
    queue = deque(seed_cells)
    seen = set(seed_cells)
    while queue:
        row, col = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = row + dr, col + dc
            if 0 <= rr < height and 0 <= cc < width and (rr, cc) not in seen and grid[rr][cc] == target:
                seen.add((rr, cc)); queue.append((rr, cc))
    out = _copy(grid)
    for row, col in seen:
        out[row][col] = 8
    return out


def _rival_fixed(color: int) -> Callable[[list[list[int]]], list[list[int]]]:
    return lambda grid: _recolor_all(canonical_expand(grid), color)


def _rival_all(grid: list[list[int]]) -> list[list[int]]:
    out = canonical_expand(grid)
    return [[8 if cell in PAYLOAD_COLORS else cell for cell in row] for row in out]


def _rival_last_hit(grid: list[list[int]]) -> list[list[int]]:
    expanded = canonical_expand(grid)
    sequence = hit_sequence(expanded)
    return _recolor_all(expanded, sequence[-1] if sequence else None)


def _rival_majority(grid: list[list[int]]) -> list[list[int]]:
    expanded = canonical_expand(grid)
    counts = {color: sum(cell == color for row in grid for cell in row) for color in PAYLOAD_COLORS}
    target = max(PAYLOAD_COLORS, key=lambda color: (counts[color], -color))
    return _recolor_all(expanded, target)


def _rival_row_major(grid: list[list[int]]) -> list[list[int]]:
    expanded = canonical_expand(grid)
    target = next((cell for row in grid for cell in row if cell in PAYLOAD_COLORS), None)
    return _recolor_all(expanded, target)


def _rival_local_only(grid: list[list[int]]) -> list[list[int]]:
    expanded = canonical_expand(grid)
    sequence = hit_sequence(expanded)
    if not sequence:
        return expanded
    target = sequence[0]
    seeds = set()
    for row, line in enumerate(expanded):
        for col, value in enumerate(line):
            if value == 4:
                for dr, dc in _NEIGHBORS8:
                    rr, cc = row + dr, col + dc
                    if 0 <= rr < len(expanded) and 0 <= cc < len(expanded[0]) and expanded[rr][cc] == target:
                        seeds.add((rr, cc))
    return _component_recolor(expanded, target, seeds)


def _rival_adjacent_only(grid: list[list[int]]) -> list[list[int]]:
    expanded = canonical_expand(grid)
    sequence = hit_sequence(expanded)
    if not sequence:
        return expanded
    target = sequence[0]
    out = _copy(expanded)
    for row, line in enumerate(expanded):
        for col, value in enumerate(line):
            if value != 4:
                continue
            for dr, dc in _NEIGHBORS8:
                rr, cc = row + dr, col + dc
                if 0 <= rr < len(out) and 0 <= cc < len(out[0]) and out[rr][cc] == target:
                    out[rr][cc] = 8
    return out


RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "canonical_only_or_b_before_a": canonical_expand,
    "fixed_payload_7": _rival_fixed(7),
    "fixed_payload_9": _rival_fixed(9),
    "recolor_both_payload_colors": _rival_all,
    "use_last_ray_hit": _rival_last_hit,
    "use_global_payload_majority": _rival_majority,
    "use_row_major_first_payload": _rival_row_major,
    "recolor_only_local_component": _rival_local_only,
    "recolor_only_cells_adjacent_to_ray": _rival_adjacent_only,
}


def lesson_errors(episode: Any, settings: Any) -> list[str]:
    settings = _setting(settings)
    errors: list[str] = []
    if type(episode) is not dict:
        return ["episode must be a dictionary"]
    train, test = episode.get("train"), episode.get("test")
    if type(train) is not list or not 2 <= len(train) <= 6:
        errors.append("episode must contain 2..6 demonstrations")
        train = []
    if type(test) is not list or not 1 <= len(test) <= 4:
        errors.append("episode must contain 1..4 queries")
        test = []
    seen = set()
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if type(pair) is not dict or set(pair) < {"input", "output"}:
                errors.append(f"{split_name}[{index}] lacks input/output")
                continue
            try:
                inp = validate_input(pair["input"])
                expected = apply(inp, settings)
            except Exception as exc:
                errors.append(f"{split_name}[{index}] invalid: {type(exc).__name__}: {exc}")
                continue
            key = json.dumps(inp, separators=(",", ":"))
            if key in seen:
                errors.append(f"duplicate input at {split_name}[{index}]")
            seen.add(key)
            if pair["output"] != expected:
                errors.append(f"{split_name}[{index}] label disagrees with selected rule")
    if errors:
        return errors

    survivor_settings = []
    for candidate in SETTINGS:
        if all(apply(pair["input"], candidate) == pair["output"] for pair in train):
            survivor_settings.append(candidate)
    if survivor_settings != [settings]:
        errors.append(f"declared settings survivors are {survivor_settings!r}")

    facts = [scene_facts(pair["input"]) for pair in train]
    active = [fact for fact in facts if fact["active"]]
    if len(active) < 2:
        errors.append("minimum lesson needs two active crossing-ray demonstrations")
    if {fact["first_hit_color"] for fact in active[:2]} != {7, 9}:
        errors.append("first two active demonstrations must cross selected colors 7 and 9")
    if {fact["vertical_color"] for fact in active[:2]} != {3, 6}:
        errors.append("first two active demonstrations must cover vertical cues 3 and 6")
    for index, fact in enumerate(active):
        if fact["later_hit_color"] not in PAYLOAD_COLORS or fact["later_hit_color"] == fact["first_hit_color"]:
            errors.append(f"active demo {index} lacks a later opposite-color hit")

    chosen = lambda grid: apply(grid, settings)
    for name, rival in RIVALS.items():
        survives = all(rival(pair["input"]) == pair["output"] for pair in train)
        changes_any = any(rival(pair["input"]) != chosen(pair["input"]) for pair in train + test)
        if survives and changes_any:
            errors.append(f"rival {name!r} fits all demonstrations but changes an admitted pair")
    return errors
