"""Native vector-copy family with an input-derived repeat count.

The canonical setting makes one red-to-green vector copy.  The alternate first
identifies the irrelevant color-6/7 component, counts its occupied cells, and
then uses that count as the number of successive vector translations to paint.
The repeated-copy stage therefore consumes a measured input intermediate.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
from typing import Any, Iterable

TASK_ID = "a4f0ea66fd65"
HERE = Path(__file__).resolve().parent
MODES = ("single", "decoy_size")
DEFAULT_MODE = "single"
DEMO_LIMITS = (2, 6)
QUERY_LIMITS = (1, 4)
_DIMS = (
    (16, 18), (18, 20), (20, 22), (22, 24), (24, 26), (26, 28),
    (18, 22), (22, 26), (28, 30), (30, 30),
)
_VECTORS = (
    (3, 2), (2, 3), (4, 1), (1, 4), (-3, 2), (3, -2),
    (0, 4), (4, 0), (-4, -3), (6, 6),
)
_DECOY_SIZES = (3, 4, 3, 4, 4, 3, 4, 3, 3, 4)
_DECOY_COLORS = (6, 6, 7, 7, 6, 7, 7, 6, 7, 6)
_SOURCE_SIZES = (5, 6, 7, 8, 6, 5, 8, 7, 6, 8)
_BASE_SHAPES = {
    5: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    6: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    7: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)),
    8: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1), (2, 2)),
}
_DECOY_SHAPES = {
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (0, 2), (1, 1)),
}
_RIVAL_NAMES = (
    "other_setting",
    "fixed_2",
    "fixed_3",
    "fixed_4",
    "decoy_bbox_area",
    "source_size_capped_4",
    "decoy_color_map",
    "reverse_color_map",
    "until_edge",
)


def _text(name: str) -> str:
    return (HERE / name).read_text(encoding="utf-8")


def _mode(settings: object) -> str:
    if type(settings) is not dict or set(settings) != {"copy_extent"}:
        raise ValueError("settings must contain exactly copy_extent")
    value = settings["copy_extent"]
    if type(value) is not str or value not in MODES:
        raise ValueError(f"copy_extent must be one of {MODES}")
    return value


def _integer(value: object, low: int, high: int, name: str) -> int:
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{name} must be an exact integer in {low}..{high}")
    return value


def program(settings: object) -> str:
    return _text("canonical.rkt" if _mode(settings) == DEFAULT_MODE else "decoy-size-repeat.rkt")


def _neighbors4(row: int, col: int) -> Iterable[tuple[int, int]]:
    yield row - 1, col
    yield row + 1, col
    yield row, col - 1
    yield row, col + 1


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    values = tuple(cells)
    r0 = min(r for r, _ in values)
    c0 = min(c for _, c in values)
    return tuple(sorted((r - r0, c - c0) for r, c in values))


def _orient(cells: Iterable[tuple[int, int]], code: int) -> tuple[tuple[int, int], ...]:
    def xf(r: int, c: int) -> tuple[int, int]:
        if code == 0: return r, c
        if code == 1: return c, -r
        if code == 2: return -r, -c
        if code == 3: return -c, r
        if code == 4: return r, -c
        if code == 5: return -r, c
        if code == 6: return c, r
        return -c, -r
    return _normalize(xf(r, c) for r, c in cells)


def _connected(cells: set[tuple[int, int]]) -> bool:
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        cell = stack.pop()
        for nb in _neighbors4(*cell):
            if nb in cells and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return seen == cells


def validate_grid(grid: object) -> tuple[int, int]:
    if type(grid) is not list or not 12 <= len(grid) <= 30:
        raise ValueError("grid height must be 12..30")
    if not grid or type(grid[0]) is not list or not 12 <= len(grid[0]) <= 30:
        raise ValueError("grid width must be 12..30")
    height, width = len(grid), len(grid[0])
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(value) is not int or not 0 <= value <= 9 for value in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact integer colors 0..9")
    palette = {value for row in grid for value in row}
    if not palette <= {0, 2, 3, 6, 7, 8}:
        raise ValueError("input palette must be 0,2,3,6/7,8")
    positions = {color: {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color} for color in (2, 3, 6, 7, 8)}
    if len(positions[2]) != 1 or len(positions[3]) != 1:
        raise ValueError("input needs exactly one red and one green marker")
    if not 5 <= len(positions[8]) <= 8 or not _connected(positions[8]):
        raise ValueError("cyan source must be one connected 5..8-cell object")
    decoy_colors = [color for color in (6, 7) if positions[color]]
    if len(decoy_colors) != 1:
        raise ValueError("input needs exactly one decoy color")
    decoy = positions[decoy_colors[0]]
    if len(decoy) not in (3, 4) or not _connected(decoy):
        raise ValueError("decoy must be one connected 3- or 4-cell object")
    red = next(iter(positions[2]))
    green = next(iter(positions[3]))
    dr, dc = green[0] - red[0], green[1] - red[1]
    if (dr, dc) == (0, 0):
        raise ValueError("marker vector must be nonzero")
    source = positions[8]
    copies: list[set[tuple[int, int]]] = []
    for k in range(1, len(decoy) + 1):
        target = {(r + k * dr, c + k * dc) for r, c in source}
        if any(not (0 <= r < height and 0 <= c < width) for r, c in target):
            raise ValueError("all decoy-sized translations must stay in bounds")
        if source & target or any(previous & target for previous in copies):
            raise ValueError("source and successive copies must be disjoint")
        if target & (positions[2] | positions[3]):
            raise ValueError("copy targets may not overwrite markers")
        copies.append(target)
    return height, width


def _facts(grid: list[list[int]]) -> dict[str, Any]:
    height, width = validate_grid(grid)
    positions = {color: {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color} for color in (2, 3, 6, 7, 8)}
    red = next(iter(positions[2]))
    green = next(iter(positions[3]))
    vector = green[0] - red[0], green[1] - red[1]
    decoy_color = 6 if positions[6] else 7
    decoy = positions[decoy_color]
    rows = [r for r, _ in decoy]
    cols = [c for _, c in decoy]
    source = positions[8]
    max_repeats = 0
    for k in range(1, 20):
        target = {(r + k * vector[0], c + k * vector[1]) for r, c in source}
        if all(0 <= r < height and 0 <= c < width for r, c in target):
            max_repeats = k
        else:
            break
    return {
        "height": height,
        "width": width,
        "red": red,
        "green": green,
        "vector": vector,
        "source": source,
        "source_size": len(source),
        "decoy_color": decoy_color,
        "decoy": decoy,
        "decoy_size": len(decoy),
        "decoy_bbox_area": (max(rows) - min(rows) + 1) * (max(cols) - min(cols) + 1),
        "max_repeats": max_repeats,
    }


def _apply_count(grid: list[list[int]], repeats: int, *, reverse: bool = False) -> list[list[int]]:
    facts = _facts(grid)
    dr, dc = facts["vector"]
    if reverse:
        dr, dc = -dr, -dc
    out = deepcopy(grid)
    height, width = facts["height"], facts["width"]
    for k in range(1, repeats + 1):
        for row, col in facts["source"]:
            nr, nc = row + k * dr, col + k * dc
            if 0 <= nr < height and 0 <= nc < width:
                out[nr][nc] = 1
    return out


def apply_python(grid: list[list[int]], mode: str) -> list[list[int]]:
    if mode not in MODES:
        raise ValueError(mode)
    facts = _facts(grid)
    repeats = 1 if mode == "single" else facts["decoy_size"]
    return _apply_count(grid, repeats)


def _rng(seed: int, index: int, label: str) -> random.Random:
    digest = hashlib.sha256(f"{TASK_ID}|{seed}|{index}|{label}".encode()).digest()
    return random.Random(int.from_bytes(digest[:16], "big"))


def _translated(source: set[tuple[int, int]], vector: tuple[int, int], k: int) -> set[tuple[int, int]]:
    return {(r + k * vector[0], c + k * vector[1]) for r, c in source}


def _source_candidates(height: int, width: int, shape: tuple[tuple[int, int], ...], vector: tuple[int, int], required: int) -> list[tuple[int, int, int]]:
    box_h = max(r for r, _ in shape) + 1
    box_w = max(c for _, c in shape) + 1
    rows = range(0, height - box_h + 1)
    cols = range(0, width - box_w + 1)
    result = []
    for row0 in rows:
        for col0 in cols:
            source = {(row0 + r, col0 + c) for r, c in shape}
            copies = []
            valid = True
            for k in range(1, required + 1):
                target = _translated(source, vector, k)
                if any(not (0 <= r < height and 0 <= c < width) for r, c in target) or source & target or any(old & target for old in copies):
                    valid = False
                    break
                copies.append(target)
            if not valid:
                continue
            max_repeats = required
            for k in range(required + 1, 20):
                target = _translated(source, vector, k)
                if all(0 <= r < height and 0 <= c < width for r, c in target):
                    max_repeats = k
                else:
                    break
            result.append((row0, col0, max_repeats))
    return result


def _choose_source_origin(height: int, width: int, shape: tuple[tuple[int, int], ...], vector: tuple[int, int], required: int, rng: random.Random, index: int) -> tuple[int, int]:
    if index == 9:
        return 3, 3
    candidates = _source_candidates(height, width, shape, vector, required)
    if not candidates:
        raise ValueError("no legal source origin")
    best_margin = max(value[2] for value in candidates)
    best = [(r, c) for r, c, margin in candidates if margin == best_margin]
    return rng.choice(best)


def _marker_candidates(height: int, width: int, vector: tuple[int, int], blocked: set[tuple[int, int]]) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    result = []
    for row in range(height):
        for col in range(width):
            green = row + vector[0], col + vector[1]
            red = row, col
            if 0 <= green[0] < height and 0 <= green[1] < width and red not in blocked and green not in blocked:
                result.append((red, green))
    return result


def _place_decoy(height: int, width: int, size: int, last_copy: set[tuple[int, int]], blocked: set[tuple[int, int]], rng: random.Random) -> set[tuple[int, int]]:
    variants = [_orient(_DECOY_SHAPES[size], code) for code in range(8)]
    candidates = []
    for shape in variants:
        for local_target in shape:
            for target in sorted(last_copy):
                row0, col0 = target[0] - local_target[0], target[1] - local_target[1]
                cells = {(row0 + r, col0 + c) for r, c in shape}
                if all(0 <= r < height and 0 <= c < width for r, c in cells) and not (cells & blocked) and cells & last_copy:
                    candidates.append(cells)
    if not candidates:
        raise ValueError("no legal decoy placement")
    return rng.choice(candidates)


def make_input(seed: int, index: int) -> list[list[int]]:
    height, width = _DIMS[index]
    vector = _VECTORS[index]
    decoy_size = _DECOY_SIZES[index]
    decoy_color = _DECOY_COLORS[index]
    rng = _rng(seed, index, "scene")
    shape = _orient(_BASE_SHAPES[_SOURCE_SIZES[index]], rng.randrange(8))
    row0, col0 = _choose_source_origin(height, width, shape, vector, decoy_size, rng, index)
    source = {(row0 + r, col0 + c) for r, c in shape}
    copies = [_translated(source, vector, k) for k in range(1, decoy_size + 1)]
    if index == 9:
        red, green = (0, 0), (6, 6)
    else:
        blocked = source | set().union(*copies)
        marker_pairs = _marker_candidates(height, width, vector, blocked)
        if not marker_pairs:
            raise ValueError("no legal marker pair")
        # Prefer a marker pair far from the source so the whole scene is distributed.
        marker_pairs.sort(key=lambda pair: min(abs(pair[0][0] - r) + abs(pair[0][1] - c) for r, c in source), reverse=True)
        top_distance = min(abs(marker_pairs[0][0][0] - r) + abs(marker_pairs[0][0][1] - c) for r, c in source)
        best = [pair for pair in marker_pairs if min(abs(pair[0][0] - r) + abs(pair[0][1] - c) for r, c in source) == top_distance]
        red, green = rng.choice(best)
    blocked_for_decoy = source | {red, green}
    if index == 9:
        # Keep the canonical one-copy setting boundary-relevant too: the decoy
        # itself occupies the lower/right edge and is overwritten only by the
        # fourth repeated copy in the alternate setting.
        decoy = {(28, 29), (29, 27), (29, 28), (29, 29)}
        if decoy & blocked_for_decoy or not decoy <= copies[-1]:
            raise ValueError("fixed 30x30 decoy no longer matches the last copy")
    else:
        decoy = _place_decoy(height, width, decoy_size, copies[-1], blocked_for_decoy, rng)
    grid = [[0 for _ in range(width)] for _ in range(height)]
    for row, col in source:
        grid[row][col] = 8
    grid[red[0]][red[1]] = 2
    grid[green[0]][green[1]] = 3
    for row, col in decoy:
        grid[row][col] = decoy_color
    validate_grid(grid)
    return grid


def _pair(seed: int, index: int, mode: str) -> dict[str, list[list[int]]]:
    grid = make_input(seed, index)
    return {"input": grid, "output": apply_python(grid, mode)}


def generate(seed: object, settings: object, demos: object = 3, queries: object = 4) -> dict[str, Any]:
    seed_i = _integer(seed, 0, 2**63 - 1, "seed")
    demos_i = _integer(demos, *DEMO_LIMITS, "demos")
    queries_i = _integer(queries, *QUERY_LIMITS, "queries")
    mode = _mode(settings)
    episode = {
        "train": [_pair(seed_i, index, mode) for index in range(demos_i)],
        "test": [_pair(seed_i, 6 + index, mode) for index in range(queries_i)],
        "program_solution": program({"copy_extent": mode}),
        "meta": {"copy_extent": mode, "seed": seed_i},
    }
    return deepcopy(episode)


def rival_output(grid: list[list[int]], name: str, chosen_mode: str) -> list[list[int]]:
    facts = _facts(grid)
    if name == "other_setting":
        other = next(mode for mode in MODES if mode != chosen_mode)
        return apply_python(grid, other)
    if name.startswith("fixed_"):
        return _apply_count(grid, int(name.rsplit("_", 1)[1]))
    if name == "decoy_bbox_area":
        return _apply_count(grid, facts["decoy_bbox_area"])
    if name == "source_size_capped_4":
        return _apply_count(grid, min(facts["source_size"], 4))
    if name == "decoy_color_map":
        return _apply_count(grid, 3 if facts["decoy_color"] == 6 else 4)
    if name == "reverse_color_map":
        return _apply_count(grid, 4 if facts["decoy_color"] == 6 else 3)
    if name == "until_edge":
        return _apply_count(grid, facts["max_repeats"])
    raise ValueError(name)


def teaching_report(episode: dict[str, Any], chosen_mode: str) -> dict[str, Any]:
    if chosen_mode not in MODES:
        raise ValueError(chosen_mode)
    survivors = []
    rows = []
    for name in _RIVAL_NAMES:
        mismatches = [index for index, pair in enumerate(episode["train"]) if rival_output(pair["input"], name, chosen_mode) != pair["output"]]
        query_disagrees = any(rival_output(pair["input"], name, chosen_mode) != pair["output"] for pair in episode["test"])
        if not mismatches and query_disagrees:
            survivors.append(name)
        rows.append({"name": name, "demonstration_mismatches": mismatches, "query_disagrees": query_disagrees})
    return {"mode": chosen_mode, "rivals": rows, "surviving_harmful_rivals": survivors}


def public_turn(episode: dict[str, Any], query_index: object) -> dict[str, Any]:
    index = _integer(query_index, 0, len(episode["test"]) - 1, "query_index")
    return {"train": deepcopy(episode["train"]), "test": [{"input": deepcopy(episode["test"][index]["input"])}]}


def public_bytes(episode: dict[str, Any], query_index: int) -> bytes:
    return json.dumps(public_turn(episode, query_index), sort_keys=True, separators=(",", ":")).encode()


def public_filename(episode: dict[str, Any], query_index: int) -> str:
    return "challenge-" + hashlib.sha256(public_bytes(episode, query_index)).hexdigest() + ".json"


def causal_state(grid: list[list[int]]) -> dict[str, Any]:
    facts = _facts(grid)
    return {
        "decoy_color": facts["decoy_color"],
        "decoy_size": facts["decoy_size"],
        "repeat_count": facts["decoy_size"],
        "counterfactual_repeat_count": 3,
        "vector": list(facts["vector"]),
        "source_size": facts["source_size"],
    }
