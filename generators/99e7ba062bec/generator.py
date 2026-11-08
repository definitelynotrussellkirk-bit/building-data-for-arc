"""Generator for ARC task 99e7ba062bec — cropped transform analogy.

A 5x17 zero-background canvas contains three content bands separated by one
or more all-zero columns.  Crop the bands to panels A, B, and C.  The first
allowed transform in code order

    1 identity, 2 rotate-cw, 3 rotate-180, 4 rotate-ccw,
    5 flip-lr, 6 flip-ud, 7 transpose

that maps A's mask to B's mask is applied to C; the transformed C is returned
cropped.  A and B share one color while C uses another, matching the canonical
role palette and making color preservation observable.
"""
from __future__ import annotations

import copy
from functools import lru_cache
from itertools import combinations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "99e7ba062bec"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "e3f7daceeedf"

CODES = (1, 2, 3, 4, 5, 6, 7)
SCHEDULE_PROFILES = CODES
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A 5x17 zero-background grid contains three cropped shape panels separated "
    "by blank columns. Panels A and B share one color; panel C uses a distinct "
    "color. Infer the first transform in code order {identity, rotate-cw, "
    "rotate-180, rotate-ccw, flip-lr, flip-ud, transpose} that maps A to B, "
    "then apply it to C and preserve C's color. Ordinary generated examples "
    "make the A->B transform unique, make C discriminate all seven transforms, "
    "vary connectedness, and cover every branch in each seven-sample window."
)

INVARIANTS = [
    "the canvas is exactly 5x17 with background color 0",
    "exactly three nonempty content bands are separated by all-zero columns",
    "each cropped panel is 2..4 cells tall/wide and contains 4..7 cells",
    "A and B use one shared nonzero color while C uses a second nonzero color",
    "at least one allowed transform maps A's mask to B's mask",
    "ordinary generated A and C masks distinguish all seven allowed transforms",
    "ordinary generated C does not reuse A's transform orbit",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

AXES = {
    "command": {
        "type": "int",
        "default": "seven-sample cyclic schedule",
        "valid": "1..7",
        "doc": "first matching transform code applied to C",
    },
    "a_active_count": {
        "type": "int",
        "default": "difficulty-banded schedule",
        "valid": "4..7",
        "doc": "number of nonzero cells in panel A and panel B",
    },
    "c_active_count": {
        "type": "int",
        "default": "difficulty-banded schedule",
        "valid": "4..7",
        "doc": "number of nonzero cells in panel C",
    },
}

_CODE_NAMES = {
    1: "identity",
    2: "rotate_cw",
    3: "rotate_180",
    4: "rotate_ccw",
    5: "flip_lr",
    6: "flip_ud",
    7: "transpose",
}
_SHAPE_DIMS = ((2, 3), (3, 2), (2, 4), (4, 2), (3, 3), (3, 4), (4, 3))
_COMPONENT_PROFILES = ((1, 1), (1, 2), (2, 1), (2, 2), (3, 1))


def _normalize_band(difficulty: Any) -> str:
    if difficulty in (None, "default", "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    del difficulty
    return CODES[(sample_index + int(seed)) % len(CODES)]


def _scheduled_count(
    label: str,
    ctx,
    sample_index: int,
    band: str,
    overrides: dict[str, Any],
) -> int:
    if label in overrides:
        return ctx.draw_int(label, 4, 7)
    schedules = {
        "a_active_count": {
            "easy": (4, 5, 5, 4, 5, 4, 5),
            "medium": (5, 6, 5, 6, 5, 6, 5),
            "hard": (6, 7, 6, 7, 6, 7, 6),
        },
        "c_active_count": {
            "easy": (4, 5, 4, 5, 5, 4, 5),
            "medium": (5, 5, 6, 5, 6, 5, 6),
            "hard": (7, 6, 7, 6, 7, 6, 7),
        },
    }
    scheduled = schedules[label][band][sample_index % len(CODES)]
    return ctx.draw_choice(label, [scheduled])


def _apply_grid(grid: list[list[int]], code: int) -> list[list[int]]:
    if code == 1:
        return [row[:] for row in grid]
    if code == 2:
        return [list(column) for column in zip(*grid[::-1])]
    if code == 3:
        return [row[::-1] for row in grid[::-1]]
    if code == 4:
        return [list(column) for column in zip(*grid)][::-1]
    if code == 5:
        return [row[::-1] for row in grid]
    if code == 6:
        return [row[:] for row in grid[::-1]]
    if code == 7:
        return [list(column) for column in zip(*grid)]
    raise ValueError(f"unknown transform code: {code!r}")


def _norm_cells(cells) -> tuple[tuple[int, int], ...]:
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _apply_cells(cells, code: int) -> tuple[tuple[int, int], ...]:
    if code == 1:
        transformed = list(cells)
    elif code == 2:
        transformed = [(col, -row) for row, col in cells]
    elif code == 3:
        transformed = [(-row, -col) for row, col in cells]
    elif code == 4:
        transformed = [(-col, row) for row, col in cells]
    elif code == 5:
        transformed = [(row, -col) for row, col in cells]
    elif code == 6:
        transformed = [(-row, col) for row, col in cells]
    elif code == 7:
        transformed = [(col, row) for row, col in cells]
    else:
        raise ValueError(f"unknown transform code: {code!r}")
    return _norm_cells(transformed)


def _frozen(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def _mask(panel: list[list[int]]) -> list[list[int]]:
    return [[int(value != 0) for value in row] for row in panel]


def _cells_from_mask(mask: list[list[int]]) -> tuple[tuple[int, int], ...]:
    return tuple(
        (row, col)
        for row, values in enumerate(mask)
        for col, value in enumerate(values)
        if value
    )


def _component_count_cells(cells) -> int:
    remaining = set(cells)
    components = 0
    while remaining:
        components += 1
        stack = [remaining.pop()]
        while stack:
            row, col = stack.pop()
            for neighbor in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return components


def _component_count(panel: list[list[int]]) -> int:
    return _component_count_cells(_cells_from_mask(_mask(panel)))


def _transform_image_count(cells) -> int:
    return len({_apply_cells(cells, code) for code in CODES})


def _same_transform_orbit(left, right) -> bool:
    right_key = _norm_cells(right)
    return any(_apply_cells(left, code) == right_key for code in CODES)


@lru_cache(maxsize=None)
def _shape_candidates(
    active_count: int,
    component_target: int | None,
) -> tuple[tuple[tuple[int, int], ...], ...]:
    candidates: set[tuple[tuple[int, int], ...]] = set()
    for height, width in _SHAPE_DIMS:
        if not (max(height, width) <= active_count <= height * width):
            continue
        universe = tuple((row, col) for row in range(height) for col in range(width))
        for chosen in combinations(universe, active_count):
            if {row for row, _ in chosen} != set(range(height)):
                continue
            if {col for _, col in chosen} != set(range(width)):
                continue
            if _transform_image_count(chosen) != len(CODES):
                continue
            if component_target is not None and _component_count_cells(chosen) != component_target:
                continue
            candidates.add(_norm_cells(chosen))
    return tuple(sorted(candidates))


def _nearest_component_target(active_count: int, desired: int) -> int | None:
    available = [target for target in range(1, 6) if _shape_candidates(active_count, target)]
    if not available:
        return None
    return min(available, key=lambda target: (abs(target - desired), target))


def _sample_shape(
    rng,
    active_count: int,
    desired_components: int,
    *,
    forbidden_orbit=None,
) -> tuple[tuple[int, int], ...]:
    target = _nearest_component_target(active_count, desired_components)
    candidates = list(_shape_candidates(active_count, target))
    if forbidden_orbit is not None:
        candidates = [
            cells for cells in candidates if not _same_transform_orbit(forbidden_orbit, cells)
        ]
    if not candidates:
        candidates = list(_shape_candidates(active_count, None))
        if forbidden_orbit is not None:
            candidates = [
                cells for cells in candidates if not _same_transform_orbit(forbidden_orbit, cells)
            ]
    if not candidates:
        raise ValueError(
            f"could not sample {active_count}-cell transform-discriminative shape"
        )
    return rng.choice(candidates)


def _shape_size(cells) -> tuple[int, int]:
    return (
        max(row for row, _ in cells) + 1,
        max(col for _, col in cells) + 1,
    )


def _assemble(
    a,
    b,
    c,
    a_color: int,
    c_color: int,
    rng,
) -> list[list[int]]:
    panels = (a, b, c)
    heights = [_shape_size(panel)[0] for panel in panels]
    widths = [_shape_size(panel)[1] for panel in panels]
    slots = [0, 1, 1, 0]  # left margin, two mandatory separators, right margin
    extra = 17 - sum(widths) - sum(slots)
    if extra < 0:
        raise ValueError(f"panels do not fit 5x17 canvas: widths={widths!r}")
    for _ in range(extra):
        slots[rng.randrange(len(slots))] += 1

    grid = full_grid(5, 17, 0)
    column = slots[0]
    colors = (a_color, a_color, c_color)
    for index, (panel, color) in enumerate(zip(panels, colors)):
        row_offset = rng.randint(0, 5 - heights[index])
        for row, col in panel:
            grid[row_offset + row][column + col] = color
        column += widths[index]
        if index < 2:
            column += slots[index + 1]
    if column + slots[3] != 17:
        raise RuntimeError("internal layout width mismatch")
    return grid


def _validate_grid(grid: Any) -> tuple[list[str], list[list[int]] | None]:
    if not isinstance(grid, (list, tuple)) or len(grid) != 5:
        return ["expected an exact 5x17 grid"], None
    normalized: list[list[int]] = []
    errors: list[str] = []
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != 17:
            return ["expected an exact 5x17 grid"], None
        clean_row: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                errors.append("grid colors must be integers in 0..9")
                break
            clean_row.append(value)
        normalized.append(clean_row)
    if errors:
        return errors, None
    return [], normalized


def _content_bands(grid: list[list[int]]) -> list[tuple[int, int]]:
    bands: list[tuple[int, int]] = []
    column = 0
    while column < len(grid[0]):
        while column < len(grid[0]) and all(row[column] == 0 for row in grid):
            column += 1
        if column >= len(grid[0]):
            break
        start = column
        while column < len(grid[0]) and any(row[column] != 0 for row in grid):
            column += 1
        bands.append((start, column))
    return bands


def _crop_content(grid: list[list[int]]) -> list[list[int]]:
    cells = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        return []
    row0 = min(row for row, _ in cells)
    row1 = max(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    col1 = max(col for _, col in cells)
    return [row[col0 : col1 + 1] for row in grid[row0 : row1 + 1]]


def _split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    return [
        _crop_content([row[start:stop] for row in grid])
        for start, stop in _content_bands(grid)
    ]


def _single_nonzero_color(
    panel: list[list[int]],
    name: str,
    errors: list[str],
) -> int | None:
    colors = {value for row in panel for value in row if value != 0}
    if len(colors) != 1:
        errors.append(f"{name} must use exactly one nonzero color, found {sorted(colors)}")
        return None
    return next(iter(colors))


def _analyze(grid: Any) -> dict[str, Any]:
    errors, normalized = _validate_grid(grid)
    result: dict[str, Any] = {"errors": errors, "facts": {}}
    if errors or normalized is None:
        return result

    panels = _split_panels(normalized)
    if len(panels) != 3:
        errors.append(f"expected exactly three content panels, found {len(panels)}")
        return result
    a, b, c = panels

    for name, panel in zip(("panel A", "panel B", "panel C"), panels):
        height = len(panel)
        width = len(panel[0]) if panel else 0
        active = sum(value != 0 for row in panel for value in row)
        if not (2 <= height <= 4 and 2 <= width <= 4):
            errors.append(f"{name} crop must be 2..4 by 2..4, got {height}x{width}")
        if not 4 <= active <= 7:
            errors.append(f"{name} must contain 4..7 cells, found {active}")

    a_color = _single_nonzero_color(a, "panel A", errors)
    b_color = _single_nonzero_color(b, "panel B", errors)
    c_color = _single_nonzero_color(c, "panel C", errors)
    if a_color is not None and b_color is not None and a_color != b_color:
        errors.append(f"panels A and B must share a color, got {a_color} and {b_color}")
    if a_color is not None and c_color is not None and a_color == c_color:
        errors.append("panel C must use a color distinct from panels A/B")
    palette = {value for row in normalized for value in row}
    if len(palette) != 3 or 0 not in palette:
        errors.append(f"expected background plus two role colors, found {sorted(palette)}")

    a_mask, b_mask, c_mask = _mask(a), _mask(b), _mask(c)
    matches = tuple(code for code in CODES if _apply_grid(a_mask, code) == b_mask)
    if not matches:
        errors.append("panel B matches no allowed transform of panel A")
    command = matches[0] if matches else None
    answer = _apply_grid(c, command) if command is not None else None

    a_cells = _cells_from_mask(a_mask)
    c_cells = _cells_from_mask(c_mask)
    same_orbit = bool(a_cells and c_cells and _same_transform_orbit(a_cells, c_cells))
    if same_orbit:
        errors.append("panel C must not reuse panel A's transform orbit")

    facts = {
        "grid": normalized,
        "panels": panels,
        "a": a,
        "b": b,
        "c": c,
        "a_color": a_color,
        "b_color": b_color,
        "c_color": c_color,
        "matches": matches,
        "command": command if len(matches) == 1 else None,
        "first_command": command,
        "answer": answer,
        "a_active_count": sum(value != 0 for row in a for value in row),
        "c_active_count": sum(value != 0 for row in c for value in row),
        "a_components": _component_count(a),
        "b_components": _component_count(b),
        "c_components": _component_count(c),
        "total_components": sum(_component_count(panel) for panel in panels),
        "a_transform_discriminative": _transform_image_count(a_cells) == len(CODES),
        "c_transform_discriminative": _transform_image_count(c_cells) == len(CODES),
        "same_transform_orbit": same_orbit,
    }
    result["facts"] = facts
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - set(AXES)
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        if not errors:
            facts = analysis["facts"]
            for name in AXES:
                if name in overrides and facts[name] != int(overrides[name]):
                    errors.append(
                        f"requested {name} {int(overrides[name])}, observed {facts[name]}"
                    )
    return errors


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    facts = analysis["facts"]
    if facts["command"] is None:
        raise ValueError(f"command is not uniquely observable: {facts['matches']!r}")
    return {name: int(facts[name]) for name in AXES}


def rule_mirror(grid) -> list[list[int]]:
    """Input-pure Python mirror for tests; the pinned Racket rule is authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return copy.deepcopy(analysis["facts"]["answer"])


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    band = _normalize_band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    command = (
        ctx.draw_choice("command", CODES)
        if "command" in overrides
        else ctx.draw_choice("command", [schedule_profile(seed, sample_index, band)])
    )
    a_active_count = _scheduled_count(
        "a_active_count", ctx, sample_index, band, overrides
    )
    c_active_count = _scheduled_count(
        "c_active_count", ctx, sample_index, band, overrides
    )

    desired_a, desired_c = _COMPONENT_PROFILES[sample_index % len(_COMPONENT_PROFILES)]
    a = _sample_shape(
        ctx.draw_rng("panel_a"), a_active_count, desired_a
    )
    b = _apply_cells(a, command)
    c = _sample_shape(
        ctx.draw_rng("panel_c"),
        c_active_count,
        desired_c,
        forbidden_orbit=a,
    )
    color_rng = ctx.draw_rng("role_colors")
    a_color, c_color = color_rng.sample(range(1, 10), 2)
    grid = _assemble(a, b, c, a_color, c_color, ctx.draw_rng("layout"))

    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    facts = analysis["facts"]
    if not errors and not facts["a_transform_discriminative"]:
        errors.append("generated panel A does not identify a unique transform")
    if not errors and not facts["c_transform_discriminative"]:
        errors.append("generated panel C does not discriminate all transforms")
    if errors:
        raise RuntimeError("internal construction error: " + "; ".join(errors))

    expected = {
        "command": command,
        "a_active_count": a_active_count,
        "c_active_count": c_active_count,
    }
    observed = observe_overrides(grid)
    if observed != expected:
        raise RuntimeError(
            f"internal construction mismatch: expected {expected}, observed {observed}"
        )
    return [row[:] for row in grid]


def _valid_analysis(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return analysis


def _fixed_transform(code: int) -> Callable[[list[list[int]]], list[list[int]]]:
    def rival(grid):
        analysis = _valid_analysis(grid)
        return _apply_grid(analysis["facts"]["c"], code)

    return rival


def _copy_panel(name: str):
    def rival(grid):
        analysis = _valid_analysis(grid)
        return copy.deepcopy(analysis["facts"][name])

    return rival


def _recolor_answer_to_ab(grid):
    analysis = _valid_analysis(grid)
    color = analysis["facts"]["a_color"]
    return [
        [color if value != 0 else 0 for value in row]
        for row in analysis["facts"]["answer"]
    ]


SEMANTIC_RIVALS = {
    **{
        f"always_{_CODE_NAMES[code]}": _fixed_transform(code)
        for code in CODES
    },
    "recolor_output_to_ab": _recolor_answer_to_ab,
    "copy_panel_a": _copy_panel("a"),
    "copy_panel_b": _copy_panel("b"),
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _command_witness(code: int):
    def witness(grid):
        analysis = _analyze(grid)
        return (
            not analysis["errors"]
            and analysis["facts"]["command"] == code
            and analysis["facts"]["c_transform_discriminative"]
        )

    return witness


SEMANTIC_WITNESSES = {
    f"{_CODE_NAMES[code]}_branch": _command_witness(code) for code in CODES
}
WITNESS_RIVALS = {
    f"{_CODE_NAMES[code]}_branch": [
        name
        for name in SEMANTIC_RIVALS
        if name != f"always_{_CODE_NAMES[code]}"
    ]
    for code in CODES
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        reasons.append(f"need at least {EXAMPLES_NEEDED} demonstrations")
    commands: set[int] = set()
    valid_pairs: list[dict[str, Any]] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        analysis = _analyze(pair["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} malformed: {analysis['errors'][0]}")
            continue
        facts = analysis["facts"]
        if facts["command"] is None:
            reasons.append(f"demo {index} does not identify one transform")
            continue
        if not facts["c_transform_discriminative"]:
            reasons.append(f"demo {index} query panel does not distinguish all transforms")
        commands.add(facts["command"])
        if pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"demo {index} output disagrees with the transform analogy rule")
        valid_pairs.append(pair)
    if len(demos) >= EXAMPLES_NEEDED and len(commands) < EXAMPLES_NEEDED:
        reasons.append(
            f"demonstrations expose only {len(commands)} distinct transforms: {sorted(commands)}"
        )
    for name, rival in LESSON_COMPETITORS.items():
        if valid_pairs and not any(
            rival(pair["input"]) != pair["output"] for pair in valid_pairs
        ):
            reasons.append(f"demonstrations do not refute rival {name}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        analysis = _analyze(query["input"])
        if analysis["errors"]:
            reasons.append(f"query malformed: {analysis['errors'][0]}")
        elif analysis["facts"]["command"] is None:
            reasons.append("query does not identify one transform")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output disagrees with the transform analogy rule")
    return reasons


def mutation_fixtures():
    base = generate(
        73,
        2,
        difficulty="medium",
        command=2,
        a_active_count=5,
        c_active_count=5,
    )
    analysis = _valid_analysis(base)
    facts = analysis["facts"]
    bands = _content_bands(base)

    broken_separator = copy.deepcopy(base)
    first_gap = bands[0][1]
    broken_separator[0][first_gap] = facts["a_color"]

    mixed_b_color = copy.deepcopy(base)
    b_start, b_stop = bands[1]
    for row in range(5):
        for col in range(b_start, b_stop):
            if mixed_b_color[row][col] != 0:
                mixed_b_color[row][col] = facts["c_color"]
                break
        else:
            continue
        break

    missing_c = copy.deepcopy(base)
    c_start, c_stop = bands[2]
    for row in range(5):
        for col in range(c_start, c_stop):
            missing_c[row][col] = 0

    same_role_color = copy.deepcopy(base)
    for row in range(5):
        for col in range(c_start, c_stop):
            if same_role_color[row][col] != 0:
                same_role_color[row][col] = facts["a_color"]

    mixed_c_color = copy.deepcopy(base)
    for row in range(5):
        for col in range(c_start, c_stop):
            if mixed_c_color[row][col] != 0:
                mixed_c_color[row][col] = facts["a_color"]
                break
        else:
            continue
        break

    blank = full_grid(5, 17, 0)
    return [
        ("broken_separator", broken_separator),
        ("mixed_b_role_color", mixed_b_color),
        ("missing_panel_c", missing_c),
        ("c_reuses_ab_color", same_role_color),
        ("c_uses_mixed_colors", mixed_c_color),
        ("blank_rule_hiding_canvas", blank),
    ]
