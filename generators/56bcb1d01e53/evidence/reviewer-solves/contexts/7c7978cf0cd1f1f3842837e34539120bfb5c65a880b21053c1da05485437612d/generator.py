"""Generator for complete-icon symmetry task 56bcb1d01e53.

The selected rule first joins 8-connected foreground components separated by a
single cardinal background cell.  It then completes each logical icon: square
boxes receive 90-degree rotational closure (including half-integer centers),
rectangular boxes are expanded to an odd box around the rounded center and
receive horizontal/vertical closure, and a supported odd-square center is filled.

The curriculum alternates exact canonical shape/palette profiles with a teaching
mixture that contains a counterexample for every easy shortcut: no bridge merge,
odd-square-only completion, square-rotation applied to rectangles, and omission
of the special center fill.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from itertools import permutations
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "56bcb1d01e53"
TASK_ID = GENERATOR_ID
RULE_HASH = "a66a93e7a5d4"
VERSION = "3.0.0"
SUMMARY = (
    "Complete partial monochrome icons after 8-connectivity plus one-cell cardinal "
    "bridge clustering. Squares use 4-fold rotation, rectangles use LR/UD reflection "
    "in an expanded odd box, and supported odd-square centers are filled. The "
    "two-slot curriculum alternates canonical dimension/palette profiles with a "
    "four-branch teaching mixture that refutes the principal shortcut rules."
)

INVARIANTS = [
    "the modal background is a strict majority and every logical icon has its own color",
    "logical icons are formed by 8-components closed under one-cell cardinal bridges",
    "every icon has a 4..7 cell bounding-box dimension and the selected rule changes it",
    "teaching_mix contains bridge, rectangular, even-square, and center-fill witnesses",
]

AXES = {
    "background": {
        "type": "color",
        "default": "keyed draw over 1..9",
        "valid": "1..9",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.45
LESSON_SCHEDULE_PERIOD = 2
SCHEDULE_PROFILES = ("canonical_core", "teaching_mix")

_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIR8 = tuple(
    (dr, dc)
    for dr in (-1, 0, 1)
    for dc in (-1, 0, 1)
    if (dr, dc) != (0, 0)
)

# (height, width, palette-size) exactly matches every linked canonical input.
_CANONICAL_PROFILES = (
    (11, 19, 3),
    (11, 19, 4),
    (19, 19, 5),
    (20, 18, 4),
    (22, 22, 5),
)
_CANONICAL_PROFILE_SET = frozenset(_CANONICAL_PROFILES)

# Templates occupy a square reserved canvas.  The cells are intentionally
# incomplete; applying the selected rule adds at least one cell in every case.
_ODD5_FULL = (
    {(2, c) for c in range(5)}
    | {(r, 2) for r in range(5)}
    | {(0, 1), (1, 4), (4, 3), (3, 0)}
    | {(0, 3), (3, 4), (4, 1), (1, 0)}
)
_CENTER5 = ({(2, c) for c in range(5)} | {(r, 2) for r in range(5)}) - {(2, 2)}
_BORDER5 = {
    (r, c)
    for r in range(5)
    for c in range(5)
    if r in (0, 4) or c in (0, 4)
}
_BRIDGE5 = _BORDER5 - {(2, 0), (2, 4), (4, 2)}
_EVEN6_FULL = (
    {(r, c) for r in (2, 3) for c in range(6)}
    | {(r, c) for c in (2, 3) for r in range(6)}
    | {(0, 1), (1, 5), (5, 4), (4, 0), (0, 4), (4, 5), (5, 1), (1, 0)}
)
_RECT5_TARGET = (
    {(2, c) for c in range(5)}
    | {(1, 0), (1, 4), (3, 0), (3, 4)}
    | {(0, 1), (0, 3), (4, 1), (4, 3)}
    | {(1, 1), (1, 3), (3, 1), (3, 3)}
)
_TEMPLATES: dict[str, tuple[int, frozenset[tuple[int, int]]]] = {
    "odd5": (5, frozenset(_ODD5_FULL - {(1, 4)})),
    "center5": (5, frozenset(_CENTER5)),
    "bridge5": (5, frozenset(_BRIDGE5)),
    "even6": (6, frozenset(_EVEN6_FULL - {(1, 5)})),
    # Removing the target's final column leaves a connected 5x4 input.  The
    # rounded-center rectangular branch expands it back to a 5x5 reflection box.
    "rect5x4": (5, frozenset(point for point in _RECT5_TARGET if point[1] != 4)),
}
_TEACHING_TEMPLATES = ("bridge5", "rect5x4", "even6", "center5")
_CORE_TEMPLATES = (
    ("even6", "rect5x4"),
    ("bridge5", "rect5x4", "center5"),
    _TEACHING_TEMPLATES,
    ("odd5", "even6", "bridge5"),
    _TEACHING_TEMPLATES,
)


def _clone(grid: Iterable[Iterable[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


def _background(grid: list[list[int]]) -> int:
    return Counter(value for row in grid for value in row).most_common(1)[0][0]


def _objects8(grid: list[list[int]], bg: int) -> list[list[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != bg
    }
    components: list[list[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for dr, dc in _DIR8:
                point = (r + dr, c + dc)
                if point in remaining:
                    remaining.remove(point)
                    stack.append(point)
        components.append(sorted(cells))
    return components


def _bridged(
    first: Iterable[tuple[int, int]],
    second: Iterable[tuple[int, int]],
    grid: list[list[int]],
    bg: int,
) -> bool:
    second_set = set(second)
    for r, c in first:
        for dr, dc in _DIR4:
            far = (r + 2 * dr, c + 2 * dc)
            middle = (r + dr, c + dc)
            if far in second_set and grid[middle[0]][middle[1]] == bg:
                return True
    return False


def _clusters(
    grid: list[list[int]], bg: int, *, bridge: bool = True
) -> list[list[tuple[int, int]]]:
    groups = _objects8(grid, bg)
    if not bridge:
        return groups
    changed = True
    while changed:
        changed = False
        for index in range(len(groups)):
            partner = next(
                (
                    other
                    for other in range(index + 1, len(groups))
                    if _bridged(groups[index], groups[other], grid, bg)
                ),
                None,
            )
            if partner is not None:
                groups[index] = sorted(groups[index] + groups[partner])
                del groups[partner]
                changed = True
                break
    return groups


def _iround(value: float) -> int:
    # Racket's round and Python's round both use ties-to-even here.
    return int(round(value))


def _apply_rule(
    grid: list[list[int]],
    *,
    bridge: bool = True,
    rectangular: bool = True,
    even_squares: bool = True,
    center_fill: bool = True,
) -> list[list[int]]:
    """Pure mirror with switches used by the declared semantic rivals."""
    h, w = len(grid), len(grid[0])
    bg = _background(grid)
    output = _clone(grid)
    for cluster in _clusters(grid, bg, bridge=bridge):
        rs = [r for r, _ in cluster]
        cs = [c for _, c in cluster]
        r1, r2, c1, c2 = min(rs), max(rs), min(cs), max(cs)
        bh, bw = r2 - r1 + 1, c2 - c1 + 1
        square = bh == bw
        if square and not even_squares and bh % 2 == 0:
            continue
        cri = _iround((r1 + r2) / 2.0)
        cci = _iround((c1 + c2) / 2.0)
        if square or not rectangular:
            sr1, sr2, sc1, sc2 = r1, r2, c1, c2
        else:
            row_radius = max(cri - r1, r2 - cri)
            col_radius = max(cci - c1, c2 - cci)
            sr1, sr2 = max(0, cri - row_radius), min(h - 1, cri + row_radius)
            sc1, sc2 = max(0, cci - col_radius), min(w - 1, cci + col_radius)
        cr = (r1 + r2) / 2.0 if square else cri
        cc = (c1 + c2) / 2.0 if square else cci
        for r in range(sr1, sr2 + 1):
            for c in range(sc1, sc2 + 1):
                if output[r][c] != bg:
                    continue
                if square or not rectangular:
                    partners = (
                        (_iround(cr + (c - cc)), _iround(cc - (r - cr))),
                        (_iround(cr - (r - cr)), _iround(cc - (c - cc))),
                        (_iround(cr - (c - cc)), _iround(cc + (r - cr))),
                    )
                else:
                    partners = (
                        (r, _iround(2 * cc - c)),
                        (_iround(2 * cr - r), c),
                        (_iround(2 * cr - r), _iround(2 * cc - c)),
                    )
                value = next(
                    (
                        grid[rr][cc2]
                        for rr, cc2 in partners
                        if 0 <= rr < h and 0 <= cc2 < w and grid[rr][cc2] != bg
                    ),
                    None,
                )
                if value is not None:
                    output[r][c] = value
        if center_fill and square and bh % 2 == 1 and output[cri][cci] == bg:
            fill = grid[cluster[0][0]][cluster[0][1]]

            def painted(rr: int, cc2: int) -> bool:
                return (
                    sr1 <= rr <= sr2
                    and sc1 <= cc2 <= sc2
                    and output[rr][cc2] == fill
                )

            cardinal_support = (
                cri > sr1
                and cri < sr2
                and cci > sc1
                and cci < sc2
                and painted(cri, cci - 1)
                and painted(cri, cci + 1)
                and painted(cri - 1, cci)
                and painted(cri + 1, cci)
            )
            diagonal_support = (
                bh >= 7
                and bw >= 7
                and painted(cri - 1, cci - 1)
                and painted(cri - 1, cci + 1)
                and painted(cri + 1, cci - 1)
                and painted(cri + 1, cci + 1)
                and painted(sr1, cci)
                and painted(sr2, cci)
                and painted(cri, sc1)
                and painted(cri, sc2)
            )
            if cardinal_support or diagonal_support:
                output[cri][cci] = fill
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror; the selected Racket program remains authority."""
    errors = _basic_grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _apply_rule(grid)


def _no_bridge_merge(grid):
    return _apply_rule(grid, bridge=False)


def _square_rotation_only(grid):
    return _apply_rule(grid, rectangular=False)


def _odd_squares_only(grid):
    return _apply_rule(grid, even_squares=False)


def _no_center_fill(grid):
    return _apply_rule(grid, center_fill=False)


def _transform(
    cells: Iterable[tuple[int, int]], size: int, code: int
) -> frozenset[tuple[int, int]]:
    transformed = set()
    for row, col in cells:
        if code >= 4:
            col = size - 1 - col
        for _ in range(code % 4):
            row, col = col, size - 1 - row
        transformed.add((row, col))
    return frozenset(transformed)


def _row_partitions(count: int):
    """Every ordered partition of ``range(count)`` into nonempty rows."""
    for mask in range(1 << max(0, count - 1)):
        rows = [[]]
        for index in range(count):
            rows[-1].append(index)
            if index < count - 1 and mask & (1 << index):
                rows.append([])
        yield rows


def _pack(
    templates: list[tuple[str, int, frozenset[tuple[int, int]]]],
    h: int,
    w: int,
    rng,
) -> list[tuple[str, int, frozenset[tuple[int, int]], int, int]]:
    """Exhaustively choose a fitting row packing; no rejection-loop fallback."""
    candidates = []
    count = len(templates)
    for order in permutations(range(count)):
        ordered = [templates[index] for index in order]
        for rows in _row_partitions(count):
            row_widths = [sum(ordered[i][1] for i in row) + 2 * (len(row) - 1) for row in rows]
            row_heights = [max(ordered[i][1] for i in row) for row in rows]
            total_height = sum(row_heights) + 2 * (len(rows) - 1)
            if total_height <= h and max(row_widths) <= w:
                candidates.append((ordered, rows, row_widths, row_heights, total_height))
    if not candidates:
        sizes = [item[1] for item in templates]
        raise ValueError(f"templates {sizes} do not fit {h}x{w} with two-cell gaps")
    ordered, rows, row_widths, row_heights, total_height = rng.choice(candidates)
    top = rng.randint(0, h - total_height)
    placements = []
    for row, row_width, row_height in zip(rows, row_widths, row_heights):
        left = rng.randint(0, w - row_width)
        for ordered_index in row:
            name, size, cells = ordered[ordered_index]
            item_top = top + rng.randint(0, row_height - size)
            placements.append((name, size, cells, item_top, left))
            left += size + 2
        top += row_height + 2
    return placements


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _profile(seed: int, sample_index: int, difficulty: str | None):
    profile = schedule_profile(seed, sample_index, difficulty)
    if profile == "canonical_core":
        slot = (sample_index // LESSON_SCHEDULE_PERIOD) % len(_CANONICAL_PROFILES)
        h, w, palette_size = _CANONICAL_PROFILES[slot]
        return profile, h, w, _CORE_TEMPLATES[slot], palette_size - 1
    ranges = {
        None: ((18, 26), (20, 28)),
        "easy": ((16, 20), (18, 22)),
        "medium": ((19, 23), (20, 25)),
        "hard": ((22, 26), (24, 28)),
    }
    hrange, wrange = ranges[difficulty]
    # Shape draws are keyed but intentionally not advertised as exact controls.
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides={},
    )
    shape_rng = ctx.draw_rng("teaching_shape")
    h = shape_rng.randint(*hrange)
    w = shape_rng.randint(*wrange)
    return profile, h, w, _TEACHING_TEMPLATES, 4


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    if "background" in overrides and overrides["background"] is not None:
        value = overrides["background"]
        if type(value) is not int:
            raise TypeError("background override must be an integer color, not bool/float/string")
        if not 1 <= value <= 9:
            raise ValueError("background override must be in 1..9; color 0 is reserved by the authority object extractor")

    profile, h, w, names, n_icons = _profile(seed, int(sample_index), difficulty)
    del profile
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # The authority calls objects-8(..., 0); a literal zero scene background
    # collides with that sentinel and is outside the canonical domain.
    bg = ctx.draw_color("background", exclude={0})
    colors = ctx.draw_distinct_colors("icon_colors", n=n_icons, exclude={bg})
    templates = []
    for index, name in enumerate(names):
        size, cells = _TEMPLATES[name]
        code = ctx.draw_rng(f"icon_transform_{index}").randrange(8)
        templates.append((name, size, _transform(cells, size, code)))
    placements = _pack(templates, h, w, ctx.draw_rng("icon_placement"))
    grid = full_grid(h, w, bg)
    # Placement order and color order are independently keyed.  Colors remain
    # one-per-logical-icon, which makes the emitted control observable.
    color_order = list(colors)
    ctx.draw_rng("color_order").shuffle(color_order)
    for color, (_, _size, cells, top, left) in zip(color_order, placements):
        for row, col in cells:
            if grid[top + row][left + col] != bg:
                raise RuntimeError("constructive packing overlap")
            grid[top + row][left + col] = color
    return grid


def _basic_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, list) or not grid:
        return ["grid must be a nonempty list of rows"]
    if not isinstance(grid[0], list) or not grid[0]:
        return ["grid rows must be nonempty lists"]
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    invalid = [
        value
        for row in grid
        for value in row
        if type(value) is not int or not 0 <= value <= 9
    ]
    return ["grid colors must be integer values in 0..9"] if invalid else []


def _grid_facts(grid: Any) -> dict[str, Any]:
    errors = _basic_grid_errors(grid)
    facts: dict[str, Any] = {"errors": errors}
    if errors:
        return facts
    h, w = len(grid), len(grid[0])
    counts = Counter(value for row in grid for value in row)
    bg, bg_count = counts.most_common(1)[0]
    facts.update({"h": h, "w": w, "counts": counts, "background": bg})
    if not 7 <= h <= 30 or not 7 <= w <= 30:
        errors.append("canvas dimensions must each be in 7..30")
    if len(counts) < 2:
        errors.append("at least one foreground icon is required")
        return facts
    if bg_count * 2 <= h * w:
        errors.append("modal background must be a strict majority")

    raw = _objects8(grid, bg)
    clusters = _clusters(grid, bg)
    facts["raw_components"] = raw
    facts["clusters"] = clusters
    if not 1 <= len(clusters) <= 4:
        errors.append(f"expected 1..4 logical icons, found {len(clusters)}")
    foreground = set(counts) - {bg}
    if not 1 <= len(foreground) <= 4:
        errors.append(f"expected 1..4 foreground colors, found {len(foreground)}")

    color_owners: Counter[int] = Counter()
    cluster_rows = []
    raw_sets = [set(obj) for obj in raw]
    for cluster in clusters:
        colors = {grid[r][c] for r, c in cluster}
        rs = [r for r, _ in cluster]
        cs = [c for _, c in cluster]
        bh, bw = max(rs) - min(rs) + 1, max(cs) - min(cs) + 1
        raw_count = sum(bool(set(cluster) & obj) for obj in raw_sets)
        cluster_rows.append(
            {
                "cells": tuple(cluster),
                "colors": tuple(sorted(colors)),
                "bbox": (min(rs), max(rs), min(cs), max(cs)),
                "height": bh,
                "width": bw,
                "raw_components": raw_count,
            }
        )
        if len(colors) != 1:
            errors.append("every bridge-merged icon must be monochrome")
        else:
            color_owners[next(iter(colors))] += 1
        if len(cluster) < 8:
            errors.append("logical icons need at least eight observed cells")
        if not (4 <= bh <= 7 and 4 <= bw <= 7):
            errors.append("logical icon bounding boxes must be 4..7 cells per dimension")
        if not 1 <= raw_count <= 4:
            errors.append("logical icons may contain only 1..4 bridged 8-components")
    facts["cluster_facts"] = cluster_rows
    if set(color_owners) != foreground or any(count != 1 for count in color_owners.values()):
        errors.append("each logical icon must use a distinct foreground color")

    if not errors:
        transformed = _apply_rule(grid)
        facts["output"] = transformed
        if transformed == grid:
            errors.append("selected rule must add at least one symmetry cell")
    return facts


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_grid_facts(grid)["errors"])


def observe_overrides(grid) -> dict[str, int]:
    """Recover every exact public control from returned pixels."""
    facts = _grid_facts(grid)
    if facts["errors"]:
        raise ValueError("cannot observe malformed grid: " + "; ".join(facts["errors"]))
    return {"background": facts["background"]}


def canonical_profile_signature(grid):
    facts = _grid_facts(grid)
    if facts["errors"]:
        return None
    signature = (facts["h"], facts["w"], len(facts["counts"]))
    return signature if signature in _CANONICAL_PROFILE_SET else None


def strict_canonical_like(grid) -> list[str]:
    """Accept the five linked canonical dimension/palette profiles."""
    facts = _grid_facts(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    signature = (facts["h"], facts["w"], len(facts["counts"]))
    if signature not in _CANONICAL_PROFILE_SET:
        reasons.append(
            f"dimension/palette profile {signature} is outside the five canonical profiles"
        )
    return reasons


def _witness_flags(grid) -> dict[str, bool]:
    facts = _grid_facts(grid)
    flags = {
        "bridge_merge": False,
        "rectangular_expansion": False,
        "even_square": False,
        "center_completion": False,
    }
    if facts["errors"]:
        return flags
    bg = facts["background"]
    for cluster in facts["cluster_facts"]:
        r1, r2, c1, c2 = cluster["bbox"]
        height, width = cluster["height"], cluster["width"]
        flags["bridge_merge"] |= cluster["raw_components"] > 1
        flags["rectangular_expansion"] |= height != width
        flags["even_square"] |= height == width and height % 2 == 0
        if height == width and height % 2 == 1:
            cr, cc = (r1 + r2) // 2, (c1 + c2) // 2
            color = cluster["colors"][0]
            flags["center_completion"] |= grid[cr][cc] == bg and all(
                grid[cr + dr][cc + dc] == color for dr, dc in _DIR4
            )
    return flags


def semantic_observables(grid) -> dict[str, Any]:
    facts = _grid_facts(grid)
    if facts["errors"]:
        return {"errors": list(facts["errors"])}
    return {
        "profile": canonical_profile_signature(grid),
        "background": facts["background"],
        "logical_icons": len(facts["clusters"]),
        "palette_size": len(facts["counts"]),
        "witnesses": _witness_flags(grid),
        "changed_cells": sum(
            before != after
            for before_row, after_row in zip(grid, facts["output"])
            for before, after in zip(before_row, after_row)
        ),
    }


def lesson_identifiable(demos, query) -> list[str]:
    reasons = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demonstration {index} is missing input/output")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            reasons.append(f"declared rival {name!r} survives every demonstration")
    return reasons


SEMANTIC_WITNESSES = {
    "bridge_merge": lambda grid: _witness_flags(grid)["bridge_merge"],
    "rectangular_expansion": lambda grid: _witness_flags(grid)["rectangular_expansion"],
    "even_square": lambda grid: _witness_flags(grid)["even_square"],
    "center_completion": lambda grid: _witness_flags(grid)["center_completion"],
}
SEMANTIC_RIVALS = {
    "no_bridge_merge": _no_bridge_merge,
    "square_rotation_only": _square_rotation_only,
    "odd_squares_only": _odd_squares_only,
    "no_center_fill": _no_center_fill,
}
WITNESS_RIVALS = {
    "bridge_merge": ["no_bridge_merge"],
    "rectangular_expansion": ["square_rotation_only"],
    "even_square": ["odd_squares_only"],
    "center_completion": ["no_center_fill"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS: dict[str, Any] = {}
