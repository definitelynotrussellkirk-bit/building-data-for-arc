"""Deterministic teaching generator for ARC task a23328d45092.

The canonical rule overlays four equal-coordinate quadrant patches with the
priority TL > TR > BL > BR, treating zero as transparent.  Ordinary lessons
cycle through three explicit conflict roles.  Every consecutive three-example
window therefore proves all adjacent comparisons in that priority chain.
"""
from __future__ import annotations

from itertools import permutations
import hashlib
import random
from typing import Any, Iterable

GENERATOR_ID = "a23328d45092"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
SUMMARY = (
    "A full row and column of 1s split the input into four quadrants. "
    "Overlay aligned quadrant cells with zero transparent and priority "
    "TL, then TR, then BL, then BR."
)
EXAMPLES_NEEDED = 3

SCHEDULE_PROFILES = ("tl_over_tr", "tr_over_bl", "bl_over_br")
PALETTE_KINDS = ("warm", "cool", "broad", "primary")
DENSITY_KINDS = ("sparse", "medium", "dense", "varied")
SEP_POSITIONS = ("center", "off_center", "near_top_left", "near_bot_right")
ALLOWED_OVERRIDES = {
    "grid_h",
    "grid_w",
    "palette_kind",
    "quadrant_density",
    "sep_position",
    "anchor_corner",
    "include_overlap",
}
AXES = {
    "grid_h": {"type": "int", "default": "difficulty-fixed", "valid": "5..30"},
    "grid_w": {"type": "int", "default": "difficulty-fixed", "valid": "5..30"},
    "palette_kind": {"type": "str", "default": "deterministic", "valid": "|".join(PALETTE_KINDS)},
    "quadrant_density": {"type": "str", "default": "varied", "valid": "|".join(DENSITY_KINDS)},
    "sep_position": {"type": "str", "default": "center", "valid": "|".join(SEP_POSITIONS)},
    "anchor_corner": {"type": "bool", "default": "false", "valid": "true|false"},
    "include_overlap": {"type": "bool", "default": "true", "valid": "true|false"},
}
INVARIANTS = [
    "exactly one full-width row and one full-height column of 1s",
    "four aligned nonempty quadrants, each with one distinct own color",
    "ordinary three-example windows demonstrate TL>TR, TR>BL, and BL>BR",
]

_CANONICAL_ORDER = (0, 1, 2, 3)
_ORDER_NAMES = ("TL", "TR", "BL", "BR")


def _exact_int(value: Any, *, name: str, low: int, high: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an exact integer")
    if not low <= value <= high:
        raise ValueError(f"{name} must be in {low}..{high}")
    return value


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
    _exact_int(seed, name="seed", low=0, high=2**63 - 1)
    _exact_int(sample_index, name="sample_index", low=0, high=2**31 - 1)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, easy, medium, or hard")
    unknown = set(overrides) - ALLOWED_OVERRIDES
    if unknown:
        raise KeyError(f"unknown override(s): {', '.join(sorted(unknown))}")


def _rng(seed: int, sample_index: int, stream: str) -> random.Random:
    digest = hashlib.sha256(
        f"{TASK_ID}:{VERSION}:{seed}:{sample_index}:{stream}".encode("utf-8")
    ).digest()
    return random.Random(int.from_bytes(digest, "big"))


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    _validate_call(seed, sample_index, difficulty, {})
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _dimension(difficulty: str | None) -> int:
    return {"easy": 7, "hard": 13}.get(difficulty, 9)


def _choice(value: Any, allowed: tuple[str, ...], *, name: str) -> str:
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if value not in allowed:
        raise ValueError(f"{name} must be one of {', '.join(allowed)}")
    return value


def _bool(value: Any, *, name: str) -> bool:
    if type(value) is not bool:
        raise TypeError(f"{name} must be boolean")
    return value


def _palette(kind: str, rng: random.Random) -> list[int]:
    pools = {
        "warm": [2, 3, 4, 6, 9],
        "cool": [5, 7, 8, 4, 6],
        "primary": [2, 3, 4, 6],
        "broad": [2, 3, 4, 5, 6, 7, 8, 9],
    }
    pool = list(pools[kind])
    rng.shuffle(pool)
    return pool[:4]


def _separator(h: int, w: int, position: str, rng: random.Random) -> tuple[int, int]:
    max_r, max_c = (h - 1) // 2, (w - 1) // 2
    if max_r < 2 or max_c < 2:
        raise ValueError("grid must leave at least 2x2 aligned quadrants")
    if position == "center" or position == "near_bot_right":
        return max_r, max_c
    if position == "near_top_left":
        return max(2, max_r - 2), max(2, max_c - 2)
    # Off-centre stays within the canonical rule's aligned-access bounds.
    return max(2, max_r - rng.randrange(0, 2)), max(2, max_c - rng.randrange(0, 2))


def _density_range(name: str) -> tuple[float, float]:
    return {
        "sparse": (0.16, 0.27),
        "medium": (0.31, 0.46),
        "dense": (0.58, 0.76),
        "varied": (0.18, 0.68),
    }[name]


def _put_local(grid: list[list[int]], sr: int, sc: int, q: int, r: int, c: int, value: int) -> None:
    offsets = ((0, 0), (0, sc + 1), (sr + 1, 0), (sr + 1, sc + 1))
    ro, co = offsets[q]
    grid[ro + r][co + c] = value


def _get_local(grid: list[list[int]], sr: int, sc: int, q: int, r: int, c: int) -> int:
    offsets = ((0, 0), (0, sc + 1), (sr + 1, 0), (sr + 1, sc + 1))
    ro, co = offsets[q]
    return grid[ro + r][co + c]


def _force_role(
    grid: list[list[int]],
    sr: int,
    sc: int,
    colors: list[int],
    role: str,
    rng: random.Random,
) -> tuple[int, int]:
    # Choose a non-anchor coordinate where possible and clear all four aligned
    # cells before installing exactly the comparison that the lesson role owns.
    coords = [(r, c) for r in range(sr) for c in range(sc)]
    r, c = coords[(rng.randrange(len(coords)) + 1) % len(coords)]
    for q in range(4):
        _put_local(grid, sr, sc, q, r, c, 0)
    if role == "tl_over_tr":
        active = (0, 1)
    elif role == "tr_over_bl":
        active = (1, 2)
    elif role == "bl_over_br":
        active = (2, 3)
    else:  # defensive: schedule_profile is the only caller
        raise ValueError(f"unknown role {role}")
    for q in active:
        _put_local(grid, sr, sc, q, r, c, colors[q])
    return r, c


def generate(seed: int, sample_index: int, *, difficulty: str | None = None, **overrides: Any) -> list[list[int]]:
    """Generate one deterministic teaching input.

    Defaults use fixed dimensions by difficulty so neighboring examples vary in
    evidence rather than in irrelevant size.  Explicit dimensions and all
    declared axes remain functional.
    """
    _validate_call(seed, sample_index, difficulty, overrides)
    default_dim = _dimension(difficulty)
    h = _exact_int(overrides.get("grid_h", default_dim), name="grid_h", low=5, high=30)
    w = _exact_int(overrides.get("grid_w", default_dim), name="grid_w", low=5, high=30)
    rng = _rng(seed, sample_index, "layout")
    palette_kind = _choice(
        overrides.get("palette_kind", PALETTE_KINDS[rng.randrange(len(PALETTE_KINDS))]),
        PALETTE_KINDS,
        name="palette_kind",
    )
    density_name = _choice(
        overrides.get("quadrant_density", "varied"), DENSITY_KINDS, name="quadrant_density"
    )
    sep_position = _choice(
        overrides.get("sep_position", "center"), SEP_POSITIONS, name="sep_position"
    )
    anchor_corner = _bool(overrides.get("anchor_corner", False), name="anchor_corner")
    include_overlap = _bool(overrides.get("include_overlap", True), name="include_overlap")
    sr, sc = _separator(h, w, sep_position, rng)
    colors = _palette(palette_kind, rng)

    grid = [[0 for _ in range(w)] for _ in range(h)]
    for c in range(w):
        grid[sr][c] = 1
    for r in range(h):
        grid[r][sc] = 1

    lo, hi = _density_range(density_name)
    if include_overlap:
        for q in range(4):
            density = rng.uniform(lo, hi)
            for r in range(sr):
                for c in range(sc):
                    if rng.random() < density:
                        _put_local(grid, sr, sc, q, r, c, colors[q])
    else:
        # Allocate each occupied aligned coordinate to at most one quadrant.
        for r in range(sr):
            for c in range(sc):
                if rng.random() < hi:
                    q = rng.randrange(4)
                    _put_local(grid, sr, sc, q, r, c, colors[q])

    # Give each quadrant an own-color witness.  With overlap disabled the four
    # witnesses use different aligned coordinates.
    anchors = [(0, 0), (0, max(0, sc - 1)), (max(0, sr - 1), 0), (max(0, sr - 1), max(0, sc - 1))]
    if not anchor_corner:
        anchors = [((q * 2 + sample_index) % sr, (q * 3 + seed + sample_index) % sc) for q in range(4)]
    for q, (r, c) in enumerate(anchors):
        if not include_overlap:
            for other in range(4):
                _put_local(grid, sr, sc, other, r, c, 0)
        _put_local(grid, sr, sc, q, r, c, colors[q])

    role_coordinate: tuple[int, int] | None = None
    if include_overlap:
        role_coordinate = _force_role(
            grid, sr, sc, colors, schedule_profile(seed, sample_index, difficulty), rng
        )

    # A forced role can have overwritten the sole witness of an uninvolved
    # quadrant in tiny grids. Repair empty quadrants away from the designated
    # comparison coordinate, otherwise a higher-priority repair can mask the
    # very relation this example is scheduled to teach.
    repair_candidates = [
        coordinate
        for coordinate in anchors + [(r, c) for r in range(sr) for c in range(sc)]
        if coordinate != role_coordinate
    ]
    for q in range(4):
        if not any(_get_local(grid, sr, sc, q, r, c) == colors[q] for r in range(sr) for c in range(sc)):
            r, c = repair_candidates[q % len(repair_candidates)]
            _put_local(grid, sr, sc, q, r, c, colors[q])
    return grid


def _separators(grid: list[list[int]]) -> tuple[int, int]:
    if type(grid) is not list or not grid or type(grid[0]) is not list or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("cells must be exact integer ARC colors")
    rows = [r for r, row in enumerate(grid) if all(value == 1 for value in row)]
    cols = [c for c in range(w) if all(grid[r][c] == 1 for r in range(h))]
    if len(rows) != 1 or len(cols) != 1:
        raise ValueError(f"expected exactly one full separator row/column, got rows={rows}, cols={cols}")
    return rows[0], cols[0]


def _overlay_order(grid: list[list[int]], order: Iterable[int]) -> list[list[int]]:
    sr, sc = _separators(grid)
    h, w = len(grid), len(grid[0])
    if sr < 1 or sc < 1 or sr + 1 + sr > h or sc + 1 + sc > w:
        raise ValueError("separator does not leave four aligned output-sized quadrants")
    output = [[0 for _ in range(sc)] for _ in range(sr)]
    for r in range(sr):
        for c in range(sc):
            values = (
                grid[r][c],
                grid[r][sc + 1 + c],
                grid[sr + 1 + r][c],
                grid[sr + 1 + r][sc + 1 + c],
            )
            output[r][c] = next((values[q] for q in order if values[q] != 0), 0)
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Python mirror of the canonical TL > TR > BL > BR overlay."""
    return _overlay_order(grid, _CANONICAL_ORDER)


def surviving_priority_rivals(demos: list[dict[str, Any]]) -> list[str]:
    """Return noncanonical quadrant orders still consistent with all labels."""
    survivors: list[str] = []
    for order in permutations(range(4)):
        if order == _CANONICAL_ORDER:
            continue
        if all(_overlay_order(pair["input"], order) == pair["output"] for pair in demos):
            survivors.append(">".join(_ORDER_NAMES[index] for index in order))
    return survivors


def self_check(grid: list[list[int]], *, difficulty: str | None = None, meta: Any = None) -> list[str]:
    errors: list[str] = []
    try:
        sr, sc = _separators(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]
    h, w = len(grid), len(grid[0])
    if sr < 2 or sc < 2 or sr + 1 + sr > h or sc + 1 + sc > w:
        errors.append("separator must leave four aligned quadrants at least 2x2")
        return errors
    quads = (
        (0, 0, sr, sc),
        (0, sc + 1, sr, sc + 1 + sc),
        (sr + 1, 0, sr + 1 + sr, sc),
        (sr + 1, sc + 1, sr + 1 + sr, sc + 1 + sc),
    )
    own_colors: list[int] = []
    for r0, c0, r1, c1 in quads:
        values = {grid[r][c] for r in range(r0, r1) for c in range(c0, c1)} - {0}
        if len(values) != 1:
            errors.append("each aligned quadrant must expose exactly one nonzero own color")
        else:
            own_colors.append(next(iter(values)))
    if len(own_colors) == 4 and len(set(own_colors)) != 4:
        errors.append("the four quadrant colors must be distinct")
    return errors
