"""Generator for 11221f58af4b — fill rings by repeated corner color.

Read the four corner cells, ignore zero corners, and select the unique strict
majority color. Fill every zero-valued interior cell of every complete color-3
rectangular frame with that color; preserve frame borders and corner markers.

Four consecutive ordinary samples form a discriminative lesson. Three samples
are exact canonical-manifold anchors. The fourth has zero at top-left and
bottom-right plus three frames, refuting fixed-corner, count-zero-as-a-color,
and single-frame shortcuts. Every four-sample sliding window contains all four
profiles.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "11221f58af4b"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"  # canonical anchors, semantic schedule, structural contract
# sha256[:12] under the repository's normalized-rule hashing convention.
RULE_HASH = "c50c7ca7e3d6"

SUMMARY = (
    "Ignore zero corners, take the unique strict-majority nonzero corner color, "
    "and fill every zero interior cell of every complete color-3 rectangular "
    "frame. Three ordinary profiles match exact canonical dimension/palette/"
    "frame/corner signatures; a fourth profile supplies zero-corner and "
    "three-frame counterexamples to fixed-corner and single-frame shortcuts."
)

INVARIANTS = [
    "background is 0; all nonzero cells are corner markers or color-3 frame borders",
    "the nonzero corners have one strict-majority color and never use frame color 3",
    "there are 1..3 pairwise separated complete color-3 rectangular frames",
    "every frame is at least 3x3 and has a zero-valued interior in the input",
    "the output fills every frame interior with the nonzero corner majority color",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.50

_COLORS = (1, 2, 4, 5, 6, 7, 8, 9)
_CORNER_NAMES = ("tl", "tr", "bl", "br")
_CORNER_PATTERNS = (
    "minority_tl",
    "minority_tr",
    "minority_bl",
    "minority_br",
    "zeros_tl_br",
    "zeros_tr_bl",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "four-profile lesson schedule with exact canonical anchors",
        "valid": "9..18",
    },
    "grid_w": {
        "type": "int",
        "default": "four-profile lesson schedule with exact canonical anchors",
        "valid": "11..20",
    },
    "n_frames": {
        "type": "int",
        "default": "schedule 2,1,2,3",
        "valid": "1..3",
    },
    "fill_color": {
        "type": "color",
        "default": "keyed rng",
        "valid": "1|2|4|5|6|7|8|9",
    },
    "corner_pattern": {
        "type": "str",
        "default": "canonical anchor pattern or zeros_tl_br adversary",
        "valid": "|".join(_CORNER_PATTERNS),
    },
}

# Every Cartesian override combination in the declared finite domains is
# supported. Declaring the empty set opts into strict rejection classification.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Exact linked canonical input signatures. Positions and color names are
# nuisance variables; dimensions, palette size, corner role, frame count, and
# frame bbox morphology remain linked exactly as demonstrated.
_CANONICAL_PROFILES = (
    {
        "grid_h": 10,
        "grid_w": 12,
        "n_frames": 2,
        "corner_pattern": "minority_br",
        "frame_dims": ((5, 4), (5, 3)),
    },
    {
        "grid_h": 10,
        "grid_w": 12,
        "n_frames": 2,
        "corner_pattern": "minority_bl",
        "frame_dims": ((6, 4), (4, 4)),
    },
    {
        "grid_h": 9,
        "grid_w": 11,
        "n_frames": 1,
        "corner_pattern": "minority_tr",
        "frame_dims": ((5, 5),),
    },
    {
        "grid_h": 11,
        "grid_w": 13,
        "n_frames": 2,
        "corner_pattern": "minority_bl",
        "frame_dims": ((7, 4), (6, 4)),
    },
)


def _validate_overrides(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")
    ranges = {"grid_h": (9, 18), "grid_w": (11, 20), "n_frames": (1, 3)}
    for name, (lo, hi) in ranges.items():
        if overrides.get(name) is not None:
            value = int(overrides[name])
            if not lo <= value <= hi:
                raise ValueError(f"{name}={value} outside {lo}..{hi}")
    if overrides.get("fill_color") is not None:
        value = int(overrides["fill_color"])
        if value not in _COLORS:
            raise ValueError(f"fill_color={value} not in {_COLORS}")
    if overrides.get("corner_pattern") is not None:
        value = str(overrides["corner_pattern"])
        if value not in _CORNER_PATTERNS:
            raise ValueError(f"unknown corner_pattern {value!r}")


def _schedule_profile(seed: int, sample_index: int, difficulty: Any) -> dict[str, Any]:
    slot = int(sample_index) % 4
    if slot == 0:
        # Both 10x12 canonical morphologies remain reachable while the slot's
        # semantics (two frames and a one-corner minority) stay fixed.
        profile = _CANONICAL_PROFILES[seed % 2]
        return dict(profile)
    if slot == 1:
        return dict(_CANONICAL_PROFILES[2])
    if slot == 2:
        return dict(_CANONICAL_PROFILES[3])
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    general_dims = {
        "easy": (12, 14),
        "medium": (14, 16),
        "hard": (16, 18),
    }[band]
    return {
        "grid_h": general_dims[0],
        "grid_w": general_dims[1],
        "n_frames": 3,
        "corner_pattern": "zeros_tl_br",
        "frame_dims": None,
    }


def _effective_axes(
    seed: int,
    sample_index: int,
    difficulty: Any,
    overrides: dict[str, Any],
) -> tuple[dict[str, Any], tuple[tuple[int, int], ...] | None]:
    profile = _schedule_profile(seed, sample_index, difficulty)
    effective = {
        key: value
        for key, value in profile.items()
        if key in AXES and value is not None
    }
    effective.update({key: value for key, value in overrides.items() if value is not None})
    geometry_explicit = any(
        overrides.get(key) is not None for key in ("grid_h", "grid_w", "n_frames")
    )
    fixed_dims = None if geometry_explicit else profile.get("frame_dims")
    return effective, fixed_dims


def _frame_outline(
    grid: list[list[int]], top: int, left: int, height: int, width: int
) -> None:
    bottom = top + height - 1
    right = left + width - 1
    for col in range(left, right + 1):
        grid[top][col] = 3
        grid[bottom][col] = 3
    for row in range(top, bottom + 1):
        grid[row][left] = 3
        grid[row][right] = 3


def _expanded_overlap(
    first: tuple[int, int, int, int],
    second: tuple[int, int, int, int],
    gap: int = 1,
) -> bool:
    a_top, a_left, a_bottom, a_right = first
    b_top, b_left, b_bottom, b_right = second
    return not (
        a_bottom + gap < b_top
        or b_bottom + gap < a_top
        or a_right + gap < b_left
        or b_right + gap < a_left
    )


def _placement_candidates(
    h: int, w: int, frame_dim: tuple[int, int]
) -> list[tuple[int, int, int, int]]:
    fh, fw = frame_dim
    if fh < 3 or fw < 3 or fh > h - 2 or fw > w - 2:
        return []
    return [
        (top, left, top + fh - 1, left + fw - 1)
        for top in range(1, h - fh)
        for left in range(1, w - fw)
    ]


def _place_frame_dims(
    h: int,
    w: int,
    dims: tuple[tuple[int, int], ...],
    rng,
) -> list[tuple[int, int, int, int]]:
    catalogs = [_placement_candidates(h, w, dim) for dim in dims]
    if any(not catalog for catalog in catalogs):
        raise ValueError(f"frame dimensions {dims} do not fit in {h}x{w}")
    for catalog in catalogs:
        rng.shuffle(catalog)

    placed: list[tuple[int, int, int, int]] = []

    def search(index: int) -> bool:
        if index == len(catalogs):
            return True
        for box in catalogs[index]:
            if any(_expanded_overlap(box, prior) for prior in placed):
                continue
            placed.append(box)
            if search(index + 1):
                return True
            placed.pop()
        return False

    if not search(0):
        raise ValueError(f"cannot place separated frames {dims} in {h}x{w}")
    return list(placed)


def _general_frame_dims(h: int, w: int, n_frames: int, rng) -> tuple[tuple[int, int], ...]:
    if n_frames == 1:
        return ((rng.randint(3, min(8, h - 2)), rng.randint(3, min(8, w - 2))),)
    if n_frames == 2:
        max_width = max(3, min(6, (w - 3) // 2))
        return tuple(
            (rng.randint(3, min(8, h - 2)), rng.randint(3, max_width))
            for _ in range(2)
        )
    # Three 3x3 frames fit even at the public lower boundary 9x11. Larger
    # canvases gain one deterministic size perturbation for morphology spread.
    dims = [(3, 3), (3, 3), (3, 3)]
    if h >= 12 and w >= 14:
        index = rng.randrange(3)
        dims[index] = (rng.randint(3, 4), rng.randint(3, 4))
    return tuple(dims)


def _corner_cells(h: int, w: int) -> dict[str, tuple[int, int]]:
    return {"tl": (0, 0), "tr": (0, w - 1), "bl": (h - 1, 0), "br": (h - 1, w - 1)}


def _paint_corners(
    grid: list[list[int]], pattern: str, fill_color: int, minority_color: int
) -> None:
    cells = _corner_cells(len(grid), len(grid[0]))
    values = {name: fill_color for name in _CORNER_NAMES}
    if pattern.startswith("minority_"):
        values[pattern.removeprefix("minority_")] = minority_color
    elif pattern == "zeros_tl_br":
        values["tl"] = 0
        values["br"] = 0
    elif pattern == "zeros_tr_bl":
        values["tr"] = 0
        values["bl"] = 0
    else:
        raise ValueError(f"unsupported corner pattern {pattern!r}")
    for name, (row, col) in cells.items():
        grid[row][col] = values[name]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    effective, fixed_frame_dims = _effective_axes(
        seed, sample_index, difficulty, overrides
    )
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )
    h = ctx.draw_int("grid_h", 9, 18)
    w = ctx.draw_int("grid_w", 11, 20)
    n_frames = ctx.draw_int("n_frames", 1, 3)
    fill_color = ctx.draw_choice("fill_color", _COLORS)
    corner_pattern = ctx.draw_choice("corner_pattern", _CORNER_PATTERNS)
    minority_color = ctx.draw_choice(
        "minority_color", tuple(color for color in _COLORS if color != fill_color)
    )

    layout_rng = ctx.draw_rng("layout")
    dims = (
        tuple(tuple(dim) for dim in fixed_frame_dims)
        if fixed_frame_dims is not None and len(fixed_frame_dims) == n_frames
        else _general_frame_dims(h, w, n_frames, layout_rng)
    )
    boxes = _place_frame_dims(h, w, dims, layout_rng)
    grid = full_grid(h, w, 0)
    for top, left, bottom, right in boxes:
        _frame_outline(grid, top, left, bottom - top + 1, right - left + 1)
    _paint_corners(grid, corner_pattern, fill_color, minority_color)
    return grid


def _grid_errors(grid: Any) -> tuple[list[str], list[list[int]] | None]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence of rows"], None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"], None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], None
    converted = [list(row) for row in grid]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in converted
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"], None
    return [], converted


def _components_of_color(
    grid: list[list[int]], color: int
) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    components.sort(key=lambda cells: min(cells))
    return components


def _border_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = box
    return {
        (row, col)
        for row in range(top, bottom + 1)
        for col in range(left, right + 1)
        if row in (top, bottom) or col in (left, right)
    }


def _mode_reading_order(values: list[int]) -> int:
    counts = Counter(values)
    best = values[0]
    best_count = -1
    for value in values:
        count = counts[value]
        if count > best_count:
            best = value
            best_count = count
    return best


def _infer_corner_pattern(corner_values: dict[str, int], fill_color: int) -> str | None:
    nonfill = [name for name, value in corner_values.items() if value not in (0, fill_color)]
    zeros = [name for name, value in corner_values.items() if value == 0]
    if len(nonfill) == 1 and not zeros:
        return f"minority_{nonfill[0]}"
    if set(zeros) == {"tl", "br"} and not nonfill:
        return "zeros_tl_br"
    if set(zeros) == {"tr", "bl"} and not nonfill:
        return "zeros_tr_bl"
    return None


def semantic_observables(grid: Any) -> dict[str, Any]:
    errors, converted = _grid_errors(grid)
    if converted is None:
        return {"errors": errors}
    h, w = len(converted), len(converted[0])
    if not 9 <= h <= 18 or not 11 <= w <= 20:
        errors.append(f"dimensions {h}x{w} outside 9..18 by 11..20")

    corner_cells = _corner_cells(h, w)
    corner_values = {name: converted[row][col] for name, (row, col) in corner_cells.items()}
    if any(value == 3 for value in corner_values.values()):
        errors.append("corner markers may not use frame color 3")
    nonzero_corners = [value for value in corner_values.values() if value != 0]
    fill_color = None
    if len(nonzero_corners) < 2:
        errors.append("need at least two nonzero corner markers")
    else:
        counts = Counter(nonzero_corners)
        top_count = max(counts.values())
        winners = [color for color, count in counts.items() if count == top_count]
        if len(winners) != 1 or top_count * 2 <= len(nonzero_corners):
            errors.append("nonzero corners need one strict-majority color")
        else:
            fill_color = winners[0]

    frame_records: list[dict[str, Any]] = []
    components = _components_of_color(converted, 3)
    if not 1 <= len(components) <= 3:
        errors.append(f"expected 1..3 color-3 frame components, found {len(components)}")
    for index, cells in enumerate(components):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        box = (min(rows), min(cols), max(rows), max(cols))
        top, left, bottom, right = box
        fh, fw = bottom - top + 1, right - left + 1
        border = _border_cells(box)
        if fh < 3 or fw < 3:
            errors.append(f"frame {index} bbox {fh}x{fw} is smaller than 3x3")
        if cells != border:
            errors.append(f"frame {index} is not exactly a complete rectangular border")
        interior = [
            (row, col)
            for row in range(top + 1, bottom)
            for col in range(left + 1, right)
        ]
        nonzero_interior = [cell for cell in interior if converted[cell[0]][cell[1]] != 0]
        if nonzero_interior:
            errors.append(f"frame {index} interior must be zero in the input")
        frame_records.append(
            {
                "bbox": box,
                "height": fh,
                "width": fw,
                "border": border,
                "interior": tuple(interior),
                "interior_area": len(interior),
            }
        )

    allowed_nonzero = set(corner_cells.values())
    for record in frame_records:
        allowed_nonzero.update(record["border"])
    stray = [
        (row, col)
        for row in range(h)
        for col in range(w)
        if converted[row][col] != 0 and (row, col) not in allowed_nonzero
    ]
    if stray:
        errors.append(f"found {len(stray)} nonzero cell(s) outside corners and frame borders")

    frame_records.sort(key=lambda record: record["bbox"])
    pattern = _infer_corner_pattern(corner_values, fill_color) if fill_color is not None else None
    return {
        "errors": errors,
        "grid": converted,
        "grid_h": h,
        "grid_w": w,
        "corner_values": corner_values,
        "nonzero_corners": tuple(nonzero_corners),
        "fill_color": fill_color,
        "corner_pattern": pattern,
        "frames": frame_records,
        "n_frames": len(frame_records),
        "frame_dims": tuple((record["height"], record["width"]) for record in frame_records),
        "palette_size": len({value for row in converted for value in row}),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Recognize the complete authority-valid input grammar and reject impostors."""
    del difficulty, meta
    return list(semantic_observables(grid).get("errors", []))


def observe_overrides(grid: Any) -> dict[str, Any]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    if facts.get("corner_pattern") not in _CORNER_PATTERNS:
        raise ValueError("returned grid does not encode a declared corner_pattern")
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "n_frames": facts["n_frames"],
        "fill_color": facts["fill_color"],
        "corner_pattern": facts["corner_pattern"],
    }


def strict_canonical_like(grid: Any) -> list[str]:
    """Exact linked empirical manifold, quotienting only color names/positions."""
    facts = semantic_observables(grid)
    reasons = list(facts.get("errors", []))
    if reasons:
        return reasons
    signature = (
        facts["grid_h"],
        facts["grid_w"],
        facts["palette_size"],
        facts["n_frames"],
        facts["corner_pattern"],
        tuple(sorted(facts["frame_dims"])),
    )
    lawful = {
        (10, 12, 4, 2, "minority_br", tuple(sorted(((5, 4), (5, 3))))),
        (10, 12, 4, 2, "minority_bl", tuple(sorted(((6, 4), (4, 4))))),
        (9, 11, 4, 1, "minority_tr", ((5, 5),)),
        (11, 13, 4, 2, "minority_bl", tuple(sorted(((7, 4), (6, 4))))),
    }
    if signature not in lawful:
        reasons.append(
            "linked dimensions/palette/frame-count/corner-role/frame-morphology profile is not canonical"
        )
    return reasons


def _fill_selected_frames(
    grid: Any,
    fill_color: int,
    selector: Callable[[list[dict[str, Any]]], set[int]] | None = None,
) -> list[list[int]]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    out = [row[:] for row in facts["grid"]]
    frames = facts["frames"]
    selected = set(range(len(frames))) if selector is None else selector(frames)
    for index, record in enumerate(frames):
        if index not in selected:
            continue
        for row, col in record["interior"]:
            if out[row][col] == 0:
                out[row][col] = fill_color
    return out


def rule_mirror(grid: Any) -> list[list[int]]:
    """Test-only mirror of the selected Racket rule; never an output authority."""
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    return _fill_selected_frames(grid, int(facts["fill_color"]))


def _fixed_corner_rule(name: str) -> Callable[[Any], list[list[int]]]:
    def solve(grid: Any) -> list[list[int]]:
        facts = semantic_observables(grid)
        if facts.get("errors"):
            raise ValueError("; ".join(facts["errors"]))
        return _fill_selected_frames(grid, int(facts["corner_values"][name]))
    return solve


def _count_all_corners(grid: Any) -> list[list[int]]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    values = [facts["corner_values"][name] for name in _CORNER_NAMES]
    return _fill_selected_frames(grid, _mode_reading_order(values))


def _first_frame_only(grid: Any) -> list[list[int]]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    return _fill_selected_frames(grid, int(facts["fill_color"]), lambda frames: {0})


def _largest_frame_only(grid: Any) -> list[list[int]]:
    facts = semantic_observables(grid)
    if facts.get("errors"):
        raise ValueError("; ".join(facts["errors"]))
    best = max(range(len(facts["frames"])), key=lambda i: facts["frames"][i]["interior_area"])
    return _fill_selected_frames(grid, int(facts["fill_color"]), lambda frames: {best})


def _identity(grid: Any) -> list[list[int]]:
    return [list(row) for row in grid]


SEMANTIC_RIVALS = {
    "fixed_top_left": _fixed_corner_rule("tl"),
    "fixed_top_right": _fixed_corner_rule("tr"),
    "fixed_bottom_left": _fixed_corner_rule("bl"),
    "fixed_bottom_right": _fixed_corner_rule("br"),
    "count_zero_as_corner_color": _count_all_corners,
    "first_frame_only": _first_frame_only,
    "largest_frame_only": _largest_frame_only,
    "identity": _identity,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS


def _facts(grid: Any) -> dict[str, Any]:
    return semantic_observables(grid)


SEMANTIC_WITNESSES = {
    "top_left_is_not_fill": lambda grid: _facts(grid).get("corner_values", {}).get("tl") != _facts(grid).get("fill_color"),
    "top_right_is_not_fill": lambda grid: _facts(grid).get("corner_values", {}).get("tr") != _facts(grid).get("fill_color"),
    "bottom_left_is_not_fill": lambda grid: _facts(grid).get("corner_values", {}).get("bl") != _facts(grid).get("fill_color"),
    "bottom_right_is_not_fill": lambda grid: _facts(grid).get("corner_values", {}).get("br") != _facts(grid).get("fill_color"),
    "zero_corner_pair": lambda grid: sum(value == 0 for value in _facts(grid).get("corner_values", {}).values()) == 2,
    "multiple_frames": lambda grid: _facts(grid).get("n_frames", 0) >= 2,
    "unequal_multiple_frames": lambda grid: len(set(_facts(grid).get("frame_dims", ()))) >= 2,
}

WITNESS_RIVALS = {
    "top_left_is_not_fill": ["fixed_top_left"],
    "top_right_is_not_fill": ["fixed_top_right"],
    "bottom_left_is_not_fill": ["fixed_bottom_left"],
    "bottom_right_is_not_fill": ["fixed_bottom_right"],
    "zero_corner_pair": ["count_zero_as_corner_color"],
    "multiple_frames": ["first_frame_only", "identity"],
    "unequal_multiple_frames": ["largest_frame_only"],
}


def _grid_tuple(grid: Any) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(value) for value in row) for row in grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo window to kill the named shortcut family."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"lesson needs at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    surviving = set(LESSON_COMPETITORS)
    saw_nonfill = {name: False for name in _CORNER_NAMES}
    saw_zero_pair = False
    saw_single_frame = False
    saw_multiple_frames = False

    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demo {index} is malformed"]
        facts = semantic_observables(pair["input"])
        if facts.get("errors"):
            return [f"demo {index} input invalid: {facts['errors'][0]}"]
        official = _grid_tuple(pair["output"])
        if _grid_tuple(rule_mirror(pair["input"])) != official:
            reasons.append(f"demo {index} does not match the selected rule")
        for name in _CORNER_NAMES:
            saw_nonfill[name] |= facts["corner_values"][name] != facts["fill_color"]
        saw_zero_pair |= sum(value == 0 for value in facts["corner_values"].values()) == 2
        saw_single_frame |= facts["n_frames"] == 1
        saw_multiple_frames |= facts["n_frames"] >= 2
        surviving &= {
            name
            for name in surviving
            if _grid_tuple(LESSON_COMPETITORS[name](pair["input"])) == official
        }

    for name, present in saw_nonfill.items():
        if not present:
            reasons.append(f"demos never refute the fixed-{name} corner shortcut")
    if not saw_zero_pair:
        reasons.append("demos never distinguish ignoring zero corners from counting zero")
    if not saw_single_frame or not saw_multiple_frames:
        reasons.append("demos do not show both one-frame and multi-frame branches")

    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        reasons.append("query is malformed")
        return reasons
    query_official = _grid_tuple(query["output"])
    if _grid_tuple(rule_mirror(query["input"])) != query_official:
        reasons.append("query does not match the selected rule")
    confounders = sorted(
        name
        for name in surviving
        if _grid_tuple(LESSON_COMPETITORS[name](query["input"])) != query_official
    )
    if confounders:
        reasons.append(
            "surviving shortcut(s) predict a different query answer: "
            + ", ".join(confounders)
        )
    return reasons


def mutation_fixtures():
    """Task-semantic near-misses that the structural self-check must reject."""
    base = generate(314159, 0, difficulty="easy")

    open_frame = [row[:] for row in base]
    facts = semantic_observables(base)
    row, col = min(facts["frames"][0]["border"])
    open_frame[row][col] = 0

    filled_frame = [row[:] for row in base]
    interior_cell = facts["frames"][0]["interior"][0]
    filled_frame[interior_cell[0]][interior_cell[1]] = facts["fill_color"]

    tied_corners = [row[:] for row in base]
    h, w = len(base), len(base[0])
    tied_corners[0][0] = 1
    tied_corners[0][w - 1] = 1
    tied_corners[h - 1][0] = 2
    tied_corners[h - 1][w - 1] = 2

    stray_marker = [row[:] for row in base]
    stray_marker[1][1] = 9 if base[1][1] == 0 else 8

    no_frame = full_grid(9, 11, 0)
    no_frame[0][0] = 4
    no_frame[0][-1] = 4
    no_frame[-1][0] = 4
    no_frame[-1][-1] = 8

    return [
        ("open_rectangular_border", open_frame),
        ("prefilled_frame_interior", filled_frame),
        ("tied_corner_modes", tied_corners),
        ("stray_noncorner_marker", stray_marker),
        ("absent-feature_no-frame_recombination", no_frame),
    ]
