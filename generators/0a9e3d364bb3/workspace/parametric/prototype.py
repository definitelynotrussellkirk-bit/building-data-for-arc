"""Native parametric prototype for the quadrant-key marker task.

The canonical setting scans forward and is byte-exact with the selected ARC
rule.  The alternate scans the same lawful input in reading order but keeps the
last eligible body color.  In both settings the scan result is an input-derived
intermediate: only cells of that selected color are then mapped through the
2x2 corner key according to their body-bounding-box quadrant.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Callable

TASK_ID = "0a9e3d364bb3"
PARAMETER = "marker_scan"
SETTINGS = ("forward", "reverse")
MIN_DEMOS = 2
MAX_DEMOS = 6
MIN_QUERIES = 1
MAX_QUERIES = 4
MAX_SEED = 2**63 - 1

_HOME = Path(__file__).resolve().parent
_PROGRAM_FILES = {
    "forward": _HOME / "canonical.rkt",
    "reverse": _HOME / "reverse.rkt",
}
_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_CORNERS = ("tl", "tr", "bl", "br")

# (height, width, base corner, number of body colors, target counts for
# first-scan, last-scan, and optional middle color).  The first two training
# profiles are constructive teaching witnesses: scan order, numeric order,
# frequency, key membership, midpoint convention, and recolor-all shortcuts all
# disagree across them.  Prefixes are stable because profiles never depend on
# requested totals.
_TRAIN_PROFILES = (
    (11, 11, "tl", 2, (9, 15, 0)),
    (12, 13, "tr", 2, (16, 8, 0)),
    (15, 14, "bl", 3, (18, 13, 10)),
    (18, 20, "br", 3, (24, 17, 14)),
    (22, 24, "tl", 3, (31, 25, 20)),
    (26, 28, "tr", 3, (39, 30, 26)),
)
_QUERY_PROFILES = (
    (9, 11, "br", 2, (8, 12, 0)),
    (16, 19, "tl", 3, (21, 14, 12)),
    (24, 27, "tr", 3, (34, 29, 24)),
    (30, 30, "bl", 3, (40, 38, 30)),
)


def _strict_int(name: str, value: Any, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer; bool is forbidden")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")
    return value


def _validate_settings(settings: Any) -> str:
    if not isinstance(settings, dict) or set(settings) != {PARAMETER}:
        raise ValueError(f"settings must contain exactly {PARAMETER!r}")
    selected = settings[PARAMETER]
    if type(selected) is not str or selected not in SETTINGS:
        raise ValueError(f"{PARAMETER} must be one of {SETTINGS!r}")
    return selected


def program(settings: dict[str, str]) -> str:
    """Return the exact Racket source for one declared setting."""
    selected = _validate_settings(settings)
    return _PROGRAM_FILES[selected].read_text(encoding="utf-8")


def _rng(seed: int, split: str, index: int) -> random.Random:
    payload = f"{TASK_ID}|marker-scan-inputs-v1|{seed}|{split}|{index}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(payload).digest()[:16], "big"))


def _geometry(height: int, width: int, corner: str) -> tuple[int, int, int, int]:
    if corner == "tl":
        return 0, 0, 2, 2
    if corner == "tr":
        return 0, width - 2, 2, 0
    if corner == "bl":
        return height - 2, 0, 0, 2
    if corner == "br":
        return height - 2, width - 2, 0, 0
    raise ValueError(f"unknown corner: {corner!r}")


def _corner_slots(height: int, width: int):
    return (
        ("tl", 0, 0),
        ("tr", 0, width - 2),
        ("bl", height - 2, 0),
        ("br", height - 2, width - 2),
    )


def _quadrant(
    row: int,
    col: int,
    bbox: tuple[int, int, int, int],
    *,
    midpoint_top_left: bool = False,
) -> tuple[int, int]:
    r1, c1, r2, c2 = bbox
    if midpoint_top_left:
        return (0 if 2 * row <= r1 + r2 else 1, 0 if 2 * col <= c1 + c2 else 1)
    return (0 if 2 * row < r1 + r2 else 1, 0 if 2 * col < c1 + c2 else 1)


def _validate_grid(grid: Any) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    height, width = len(grid), len(grid[0])
    if not 1 <= height <= 30 or not 1 <= width <= 30:
        raise ValueError("grid dimensions must be in 1..30")
    if any(
        type(row) is not list
        or len(row) != width
        or any(type(cell) is not int or not 0 <= cell <= 9 for cell in row)
        for row in grid
    ):
        raise ValueError("grid must be rectangular with exact ARC integer colors")
    return height, width


def analyze_input(grid: list[list[int]]) -> dict[str, Any]:
    """Recover the exact key, body, scan endpoints, and teaching properties."""
    height, width = _validate_grid(grid)
    candidates = []
    for name, row, col in _corner_slots(height, width):
        if (
            grid[row][col] not in (0, 8)
            and grid[row][col + 1] not in (0, 8)
        ):
            candidates.append((name, row, col))
    if len(candidates) != 1:
        raise ValueError(f"expected one authority key candidate, found {len(candidates)}")
    corner, key_row, key_col = candidates[0]
    key_cells = {
        (key_row + dr, key_col + dc) for dr in (0, 1) for dc in (0, 1)
    }
    key_colors = (
        grid[key_row][key_col],
        grid[key_row][key_col + 1],
        grid[key_row + 1][key_col],
        grid[key_row + 1][key_col + 1],
    )
    if any(color in (0, 8) for color in key_colors) or len(set(key_colors)) != 4:
        raise ValueError("key must contain four distinct non-0/8 colors")

    body_cells = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] != 8 and (row, col) not in key_cells
    }
    if not body_cells:
        raise ValueError("body may not be empty")
    rows = [row for row, _ in body_cells]
    cols = [col for _, col in body_cells]
    bbox = (min(rows), min(cols), max(rows), max(cols))
    r1, c1, r2, c2 = bbox
    expected_body = {
        (row, col) for row in range(r1, r2 + 1) for col in range(c1, c2 + 1)
    }
    if body_cells != expected_body:
        raise ValueError("non-separator body cells must form one full rectangle")

    body_nonzero = [
        (row, col, grid[row][col])
        for row, col in sorted(body_cells)
        if grid[row][col] != 0
    ]
    if len(body_nonzero) < 2:
        raise ValueError("body needs at least two nonzero cells")
    first_color = body_nonzero[0][2]
    last_color = body_nonzero[-1][2]
    if first_color == last_color:
        raise ValueError("teaching grammar requires distinct scan endpoint colors")

    positions: dict[int, list[tuple[int, int]]] = {}
    for row, col, color in body_nonzero:
        positions.setdefault(color, []).append((row, col))
    key_map = {
        (0, 0): key_colors[0],
        (0, 1): key_colors[1],
        (1, 0): key_colors[2],
        (1, 1): key_colors[3],
    }

    def quadrants(color: int) -> set[tuple[int, int]]:
        return {_quadrant(row, col, bbox) for row, col in positions[color]}

    def changed(color: int) -> int:
        return sum(
            key_map[_quadrant(row, col, bbox)] != color
            for row, col in positions[color]
        )

    midline_colors = {
        color
        for color, cells in positions.items()
        if any(2 * row == r1 + r2 or 2 * col == c1 + c2 for row, col in cells)
    }
    touches = any(
        row in (r1, r2) or col in (c1, c2)
        for row, col, _color in body_nonzero
    )
    return {
        "height": height,
        "width": width,
        "corner": corner,
        "key_cells": key_cells,
        "key_colors": key_colors,
        "key_map": key_map,
        "body_cells": body_cells,
        "bbox": bbox,
        "body_nonzero": body_nonzero,
        "body_nonzero_count": len(body_nonzero),
        "body_colors": tuple(positions),
        "body_color_count": len(positions),
        "color_positions": positions,
        "color_counts": {color: len(cells) for color, cells in positions.items()},
        "first_color": first_color,
        "last_color": last_color,
        "first_quadrants": quadrants(first_color),
        "last_quadrants": quadrants(last_color),
        "changed_by_setting": {
            "forward": changed(first_color),
            "reverse": changed(last_color),
        },
        "touches_body_boundary": touches,
        "midline_color_count": len(midline_colors),
        "midline_colors": midline_colors,
    }


def selected_marker(grid: list[list[int]], marker_scan: str) -> int:
    if type(marker_scan) is not str or marker_scan not in SETTINGS:
        raise ValueError(f"marker_scan must be one of {SETTINGS!r}")
    analysis = analyze_input(grid)
    return analysis["first_color"] if marker_scan == "forward" else analysis["last_color"]


def _select_policy(analysis: dict[str, Any], policy: str) -> int | None:
    counts = analysis["color_counts"]
    body_order = [color for _row, _col, color in analysis["body_nonzero"]]
    first_index = {color: body_order.index(color) for color in counts}
    if policy == "forward":
        return analysis["first_color"]
    if policy == "reverse":
        return analysis["last_color"]
    if policy == "numeric_min":
        return min(counts)
    if policy == "numeric_max":
        return max(counts)
    if policy == "most_frequent":
        return min(counts, key=lambda color: (-counts[color], first_index[color]))
    if policy == "least_frequent":
        return min(counts, key=lambda color: (counts[color], first_index[color]))
    if policy == "key_top_left":
        return analysis["key_colors"][0]
    raise ValueError(f"unknown marker policy: {policy!r}")


def _apply(
    grid: list[list[int]],
    policy: str,
    *,
    recolor_all: bool = False,
    midpoint_top_left: bool = False,
    require_key: bool = False,
) -> list[list[int]]:
    analysis = analyze_input(grid)
    marker = _select_policy(analysis, policy)
    if require_key and marker not in analysis["key_colors"]:
        return [list(row) for row in grid]
    output = [list(row) for row in grid]
    for row, col in analysis["body_cells"]:
        value = grid[row][col]
        if value == 0:
            continue
        if not recolor_all and value != marker:
            continue
        quadrant = _quadrant(
            row,
            col,
            analysis["bbox"],
            midpoint_top_left=midpoint_top_left,
        )
        output[row][col] = analysis["key_map"][quadrant]
    return output


def apply_rule(grid: list[list[int]], marker_scan: str) -> list[list[int]]:
    """Independent Python claim; protected Racket remains authoritative."""
    if type(marker_scan) is not str or marker_scan not in SETTINGS:
        raise ValueError(f"marker_scan must be one of {SETTINGS!r}")
    return _apply(grid, marker_scan)


def _banned_key_probe_cells(
    height: int, width: int, key_corner: str
) -> set[tuple[int, int]]:
    banned: set[tuple[int, int]] = set()
    for name, row, col in _corner_slots(height, width):
        if name == key_corner:
            continue
        banned.add((row, col))
        banned.add((row, col + 1))
    return banned


def _relation_pair(
    rng: random.Random,
    profile_index: int,
) -> tuple[list[int], int, int, int | None]:
    # The first two profiles deliberately reverse numeric/frequency/key-member
    # correlations, so two demonstrations cannot reveal the hidden setting from
    # an incidental cue.
    patterns = (
        ("key", "outside", ">"),
        ("outside", "key", "<"),
        ("outside", "outside", ">"),
        ("key", "key", "<"),
        ("key", "outside", "<"),
        ("outside", "key", ">"),
    )
    first_pool_name, last_pool_name, relation = patterns[profile_index % len(patterns)]
    for _attempt in range(128):
        key_colors = rng.sample(list(_COLORS), 4)
        outside = [color for color in _COLORS if color not in key_colors]
        pools = {"key": key_colors, "outside": outside}
        pairs = [
            (first, last)
            for first in pools[first_pool_name]
            for last in pools[last_pool_name]
            if first != last and ((first < last) if relation == "<" else (first > last))
        ]
        if pairs:
            first, last = rng.choice(pairs)
            remaining = [color for color in _COLORS if color not in (first, last)]
            middle = rng.choice(remaining)
            return key_colors, first, last, middle
    raise RuntimeError("could not construct the requested color-role relation")


def _pick_cell(
    rng: random.Random,
    candidates: list[tuple[int, int]],
    used: set[tuple[int, int]],
) -> tuple[int, int]:
    available = [cell for cell in candidates if cell not in used]
    if not available:
        raise RuntimeError("constructive sampler exhausted a required placement class")
    return rng.choice(available)


def _sample_input(seed: int, split: str, index: int) -> list[list[int]]:
    profiles = _TRAIN_PROFILES if split == "train" else _QUERY_PROFILES
    height, width, base_corner, color_count, targets = profiles[index]
    profile_index = index if split == "train" else len(_TRAIN_PROFILES) + index
    rng = _rng(seed, split, index)
    base = _CORNERS.index(base_corner)
    corner = _CORNERS[(base + rng.randrange(len(_CORNERS))) % len(_CORNERS)]
    key_row, key_col, body_row, body_col = _geometry(height, width, corner)
    key_colors, first_color, last_color, middle_color = _relation_pair(
        rng, profile_index
    )
    active_colors = [first_color, last_color]
    if color_count == 3:
        assert middle_color is not None
        active_colors.append(middle_color)

    grid = [[8 for _ in range(width)] for _ in range(height)]
    body_cells = [
        (row, col)
        for row in range(body_row, body_row + height - 2)
        for col in range(body_col, body_col + width - 2)
    ]
    for row, col in body_cells:
        grid[row][col] = 0
    grid[key_row][key_col] = key_colors[0]
    grid[key_row][key_col + 1] = key_colors[1]
    grid[key_row + 1][key_col] = key_colors[2]
    grid[key_row + 1][key_col + 1] = key_colors[3]

    banned = _banned_key_probe_cells(height, width, corner)
    eligible = sorted(cell for cell in body_cells if cell not in banned)
    if len(eligible) < sum(targets[:color_count]):
        raise RuntimeError("profile requests more colored cells than fit")
    bbox = (body_row, body_col, body_row + height - 3, body_col + width - 3)
    assignments: dict[tuple[int, int], int] = {
        eligible[0]: first_color,
        eligible[-1]: last_color,
    }
    used = set(assignments)

    # Every active color spans all four quadrants.  This makes the selected
    # intermediate consequential and keeps the nonselected colors as genuine
    # distractors rather than tiny annotations.
    for color in active_colors:
        for quadrant in ((0, 0), (0, 1), (1, 0), (1, 1)):
            if any(
                assignments.get(cell) == color and _quadrant(*cell, bbox) == quadrant
                for cell in used
            ):
                continue
            candidates = [
                cell for cell in eligible if _quadrant(*cell, bbox) == quadrant
            ]
            cell = _pick_cell(rng, candidates, used)
            assignments[cell] = color
            used.add(cell)

    # On profiles with an exact body midpoint, both scan-end colors receive a
    # midpoint witness.  Canonical strict comparison assigns it bottom/right.
    r1, c1, r2, c2 = bbox
    midpoint_cells = [
        cell
        for cell in eligible
        if 2 * cell[0] == r1 + r2 or 2 * cell[1] == c1 + c2
    ]
    if midpoint_cells:
        for color in (first_color, last_color):
            if not any(
                assignments.get(cell) == color and cell in midpoint_cells for cell in used
            ):
                cell = _pick_cell(rng, midpoint_cells, used)
                assignments[cell] = color
                used.add(cell)

    target_by_color = {
        first_color: targets[0],
        last_color: targets[1],
    }
    if color_count == 3:
        target_by_color[middle_color] = targets[2]
    for color in active_colors:
        current = sum(value == color for value in assignments.values())
        need = target_by_color[color] - current
        if need < 0:
            raise RuntimeError("profile target is below its constructive witnesses")
        available = [cell for cell in eligible if cell not in used]
        rng.shuffle(available)
        if len(available) < need:
            raise RuntimeError("insufficient free body cells for requested density")
        for cell in available[:need]:
            assignments[cell] = color
            used.add(cell)

    for (row, col), color in assignments.items():
        grid[row][col] = color

    summary = analyze_input(grid)
    all_quadrants = {(0, 0), (0, 1), (1, 0), (1, 1)}
    if (
        summary["first_color"] != first_color
        or summary["last_color"] != last_color
        or summary["first_quadrants"] != all_quadrants
        or summary["last_quadrants"] != all_quadrants
        or any(summary["changed_by_setting"][setting] == 0 for setting in SETTINGS)
    ):
        raise RuntimeError("constructed scene failed marker-scan teaching invariants")
    return grid


def generate(
    seed: int,
    settings: dict[str, str],
    demos: int = 3,
    queries: int = 4,
) -> dict[str, Any]:
    """Generate one setting-fixed episode with independent count prefixes."""
    seed = _strict_int("seed", seed, 0, MAX_SEED)
    demos = _strict_int("demos", demos, MIN_DEMOS, MAX_DEMOS)
    queries = _strict_int("queries", queries, MIN_QUERIES, MAX_QUERIES)
    selected = _validate_settings(settings)

    train = []
    for index in range(demos):
        grid = _sample_input(seed, "train", index)
        train.append({"input": grid, "output": apply_rule(grid, selected)})
    test = []
    for index in range(queries):
        grid = _sample_input(seed, "test", index)
        test.append({"input": grid, "output": apply_rule(grid, selected)})

    serialized = [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in [*train, *test]
    ]
    if len(serialized) != len(set(serialized)):
        raise RuntimeError("all demonstration and query inputs must be distinct")
    return {
        "train": train,
        "test": test,
        "program_solution": program(settings),
    }


def _identity(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def audit_episode(episode: dict[str, Any], selected_setting: str) -> dict[str, Any]:
    """Bounded demonstration-only audit against explicit plausible shortcuts."""
    if type(selected_setting) is not str or selected_setting not in SETTINGS:
        raise ValueError(f"selected_setting must be one of {SETTINGS!r}")
    if not isinstance(episode, dict) or not all(
        isinstance(episode.get(split), list) for split in ("train", "test")
    ):
        raise ValueError("episode must contain train/test lists")

    rivals: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
        "forward": lambda grid: _apply(grid, "forward"),
        "reverse": lambda grid: _apply(grid, "reverse"),
        "identity": _identity,
        "recolor_all_nonzero_body": lambda grid: _apply(
            grid, selected_setting, recolor_all=True
        ),
        "midpoint_top_left": lambda grid: _apply(
            grid, selected_setting, midpoint_top_left=True
        ),
        "selected_marker_must_be_key": lambda grid: _apply(
            grid, selected_setting, require_key=True
        ),
        "numeric_min_body_color": lambda grid: _apply(grid, "numeric_min"),
        "numeric_max_body_color": lambda grid: _apply(grid, "numeric_max"),
        "most_frequent_body_color": lambda grid: _apply(grid, "most_frequent"),
        "least_frequent_body_color": lambda grid: _apply(grid, "least_frequent"),
        "top_left_key_color": lambda grid: _apply(grid, "key_top_left"),
    }
    survivors = []
    harmful = []
    query_disagreements: dict[str, list[int]] = {}
    for name, rival in rivals.items():
        if all(rival(pair["input"]) == pair["output"] for pair in episode["train"]):
            survivors.append(name)
            differing = [
                index
                for index, pair in enumerate(episode["test"])
                if rival(pair["input"]) != pair["output"]
            ]
            query_disagreements[name] = differing
            if differing:
                harmful.append(name)
    return {
        "schema": "0a9e3d364bb3-finite-teaching-audit-v1",
        "selected_setting": selected_setting,
        "demonstrations_checked": len(episode["train"]),
        "queries_checked": len(episode["test"]),
        "finite_rivals": list(rivals),
        "survivors": survivors,
        "query_disagreements": query_disagreements,
        "harmful_survivors": harmful,
        "limits": "Finite named rivals only; this is not a universal uniqueness proof.",
    }
