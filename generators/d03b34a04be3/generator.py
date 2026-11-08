"""Generator for ARC task d03b34a04be3 — selector-color bounding-box crop.

The top-left cell is a color key, not part of the selected body.  Find every
other cell of that color, take their joint tight bounding box, and return the
original subgrid inside that box.  Other colors inside the box are preserved.

The curriculum deliberately interleaves canonical-profile anchors with generated
counterexamples to the canonically underdetermined masking shortcut and to
other plausible mistakes, including selecting the modal nonzero color instead
of reading the top-left key.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d03b34a04be3"
TASK_ID = "d03b34a04be3"
VERSION = "2.0.0"
RULE_HASH = "e7aaedd41057"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Read the selector color at (0,0), exclude that key cell, and crop the "
    "original grid to the joint bbox of every remaining selector-colored cell."
)
INVARIANTS = [
    "literal 0 is the background and (0,0) is a nonzero selector key",
    "at least three selector-colored body cells lie strictly below and right of the key",
    "the selected cells have a two-dimensional proper bbox containing at least one zero",
    "at least one non-selector distractor lies outside the selected bbox",
    "the output preserves every original value inside the selected bbox",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 6))
GENERAL_PROFILES = (
    "wide_adversary",
    "tall_adversary",
    "compact_adversary",
    "square_adversary",
    "sparse_adversary",
    "edge_adversary",
    "dense_adversary",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
SCHEDULE_PROFILES = (
    "public_1",
    "wide_adversary",
    "public_2",
    "tall_adversary",
    "public_3",
    "compact_adversary",
    "public_4",
    "square_adversary",
    "public_5",
    "sparse_adversary",
    "edge_adversary",
    "dense_adversary",
)
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic 12-slot canonical/adversarial schedule",
        "valid": "public_1|public_2|public_3|public_4|public_5|wide_adversary|tall_adversary|compact_adversary|square_adversary|sparse_adversary|edge_adversary|dense_adversary",
    }
}


def _decode(rows: str) -> list[list[int]]:
    return [[int(value) for value in row] for row in rows.split("/")]


# Exact public inputs are retained as canonical-profile anchors.  Their outputs
# remain Racket-authoritative; the generator returns inputs only.
_PUBLIC_ROWS = {
    "public_1": (
        "300000000000/000000005550/000330000500/000030000000/"
        "000000000000/000000000000/000000300000/000000330000/"
        "000000000000/000000000000"
    ),
    "public_2": (
        "60000000000/00000000040/00000660040/00000066040/00000000000/"
        "02200000000/02000000000/00000000000/00000000000"
    ),
    "public_3": (
        "4000000000/0000000707/0000000070/0004400000/0004400000/"
        "0000000000/0000004000/0000004400/0000000000/0000000000"
    ),
    "public_4": (
        "500000000000/000000000000/005550000000/000500000000/"
        "000000000000/000050008800/000055008800/000000000000/"
        "000000000000"
    ),
    "public_5": (
        "200000000000/000000000770/000022000700/000002200000/"
        "000000000000/000000000000/000000020000/000000022000/"
        "000000000000/000000000000"
    ),
}
_PUBLIC_INPUTS = {name: _decode(rows) for name, rows in _PUBLIC_ROWS.items()}


def _color_role_signature(grid: list[list[int]] | tuple[tuple[int, ...], ...]):
    """Canonicalize nonzero colors by first reading-order occurrence."""
    mapping = {0: 0}
    next_role = 1
    rows = []
    for row in grid:
        out = []
        for value in row:
            if value not in mapping:
                mapping[value] = next_role
                next_role += 1
            out.append(mapping[value])
        rows.append(tuple(out))
    return tuple(rows)


_PUBLIC_SIGNATURES = {
    _color_role_signature(grid): name for name, grid in _PUBLIC_INPUTS.items()
}
if len(_PUBLIC_SIGNATURES) != len(_PUBLIC_INPUTS):
    raise AssertionError("public selector-crop profiles must have unique color-role geometry")


# Each generated profile has a unique (bbox height, bbox width, target count)
# signature.  Patterns include multiple disconnected selector-color components
# so the lesson demonstrates that all matching cells, not one object, define
# the crop.  Reflections vary surface form without changing the signature.
_PROFILE_PATTERNS: dict[str, tuple[int, int, tuple[tuple[int, int], ...]]] = {
    "wide_adversary": (
        3,
        7,
        ((0, 0), (0, 1), (0, 6), (1, 3), (2, 0), (2, 5), (2, 6)),
    ),
    "tall_adversary": (
        7,
        3,
        ((0, 0), (1, 0), (6, 0), (3, 1), (0, 2), (5, 2), (6, 2)),
    ),
    "compact_adversary": (
        3,
        4,
        ((0, 0), (0, 1), (1, 3), (2, 2), (2, 3)),
    ),
    "square_adversary": (
        5,
        5,
        ((0, 0), (0, 1), (1, 1), (0, 4), (3, 3), (4, 0), (4, 3), (4, 4)),
    ),
    "sparse_adversary": (
        6,
        6,
        ((0, 0), (0, 5), (2, 2), (2, 3), (5, 0), (5, 5)),
    ),
    "edge_adversary": (
        4,
        5,
        ((0, 0), (0, 1), (1, 4), (2, 2), (3, 0), (3, 3), (3, 4)),
    ),
    "dense_adversary": (
        4,
        4,
        ((0, 0), (0, 1), (1, 0), (0, 3), (1, 3), (2, 1), (3, 0), (3, 2), (3, 3)),
    ),
}
_GENERAL_SIGNATURES = {
    (height, width, len(pattern)): name
    for name, (height, width, pattern) in _PROFILE_PATTERNS.items()
}
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def schedule_profile(seed: int, sample_index: int, difficulty: str | None = None) -> str:
    """Expose the deterministic sliding curriculum to the semantic gate."""
    del difficulty
    return SCHEDULE_PROFILES[(seed + sample_index) % len(SCHEDULE_PROFILES)]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a nonempty sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["rows must be nonempty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return ["grid dimensions must not exceed 30"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be integer ARC colors 0..9"]
    return []


def _bbox(cells: list[tuple[int, int]] | set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [row for row, _ in cells]
    cols = [col for _, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        stack = [start]
        component: set[tuple[int, int]] = set()
        remaining.remove(start)
        while stack:
            row, col = stack.pop()
            component.add((row, col))
            for dr, dc in _CARDINAL:
                neighbor = (row + dr, col + dc)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
        result.append(component)
    return result


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    result: dict[str, Any] = {"errors": errors, "scene_profile": None}
    if errors:
        return result

    height, width = len(grid), len(grid[0])
    selector = grid[0][0]
    if selector == 0:
        errors.append("selector at (0,0) must be nonzero")
        return result

    target = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == selector and (row, col) != (0, 0)
    }
    if len(target) < 3:
        errors.append(f"need at least three selector cells outside the key, found {len(target)}")
        return result

    row0, col0, row1, col1 = _bbox(target)
    bbox_height, bbox_width = row1 - row0 + 1, col1 - col0 + 1
    if row0 == 0 or col0 == 0:
        errors.append("selected body bbox must lie strictly below and right of the key")
    if bbox_height < 2 or bbox_width < 2:
        errors.append("selected body bbox must vary in both dimensions")

    inside = {
        (row, col)
        for row in range(row0, row1 + 1)
        for col in range(col0, col1 + 1)
    }
    zero_inside = {cell for cell in inside if grid[cell[0]][cell[1]] == 0}
    interior_other = {
        cell
        for cell in inside
        if grid[cell[0]][cell[1]] not in (0, selector)
    }
    exterior_other = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in inside
        and (row, col) != (0, 0)
        and grid[row][col] not in (0, selector)
    }
    if not zero_inside:
        errors.append("selected bbox must contain at least one background cell")
    if not exterior_other:
        errors.append("need at least one non-selector distractor outside the selected bbox")
    palette = {value for row in grid for value in row}
    if len(palette) < 3:
        errors.append("lesson needs background, selector, and distractor values")

    output = [list(row[col0 : col1 + 1]) for row in grid[row0 : row1 + 1]]
    if len(output) == height and len(output[0]) == width:
        errors.append("selected bbox must be a proper crop")

    public = _PUBLIC_SIGNATURES.get(_color_role_signature(grid))
    general = _GENERAL_SIGNATURES.get((bbox_height, bbox_width, len(target)))
    profile = public or general or "lawful_other"
    counts = Counter(
        value
        for row in grid
        for value in row
        if value != 0
    )
    modal_nonzero = min(
        (color for color, count in counts.items() if count == max(counts.values())),
        default=selector,
    )

    result.update(
        {
            "errors": errors,
            "height": height,
            "width": width,
            "selector": selector,
            "target": target,
            "target_count": len(target),
            "target_components": _components(target),
            "bbox": (row0, col0, row1, col1),
            "bbox_height": bbox_height,
            "bbox_width": bbox_width,
            "inside": inside,
            "zero_inside": zero_inside,
            "interior_other": interior_other,
            "exterior_other": exterior_other,
            "palette": palette,
            "counts": counts,
            "modal_nonzero": modal_nonzero,
            "output": output,
            "scene_profile": profile,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept the task grammar and reject malformed or rule-hiding scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    requested = None
    if isinstance(meta, dict):
        nested = meta.get("overrides")
        source = nested if isinstance(nested, dict) else meta
        requested = source.get("scene_profile")
    if not errors and requested is not None and analysis["scene_profile"] != requested:
        errors.append(
            f"scene_profile requested {requested!r}, observed {analysis['scene_profile']!r}"
        )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Blocking task-linked semantic predicate used by the strict census."""
    return self_check(grid)


def canonical_profile_signature(grid):
    """Name exact public anchors without conflating them with generated scenes."""
    return _PUBLIC_SIGNATURES.get(_color_role_signature(grid))


def observe_overrides(grid) -> dict[str, str]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {"scene_profile": analysis["scene_profile"]}


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only for semantic witnesses and rival checks."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return [row[:] for row in analysis["output"]]


def _crop_to_cells(grid: list[list[int]], cells: set[tuple[int, int]]) -> list[list[int]]:
    if not cells:
        return [[0]]
    row0, col0, row1, col1 = _bbox(cells)
    return [list(row[col0 : col1 + 1]) for row in grid[row0 : row1 + 1]]


def _mask_selector_only(grid: list[list[int]]) -> list[list[int]]:
    analysis = _analysis(grid)
    row0, col0, row1, col1 = analysis["bbox"]
    selector = analysis["selector"]
    return [
        [selector if grid[row][col] == selector else 0 for col in range(col0, col1 + 1)]
        for row in range(row0, row1 + 1)
    ]


def _modal_nonzero_crop(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(
        value
        for row_index, row in enumerate(grid)
        for col_index, value in enumerate(row)
        if value != 0 and (row_index, col_index) != (0, 0)
    )
    if not counts:
        return [[0]]
    maximum = max(counts.values())
    color = min(value for value, count in counts.items() if count == maximum)
    cells = {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == color
    }
    return _crop_to_cells(grid, cells)


def _first_selector_component_crop(grid: list[list[int]]) -> list[list[int]]:
    selector = grid[0][0]
    cells = {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == selector and (row, col) != (0, 0)
    }
    components = _components(cells)
    return _crop_to_cells(grid, min(components, key=lambda component: min(component)))


def _all_nonzero_body_crop(grid: list[list[int]]) -> list[list[int]]:
    cells = {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] != 0 and (row, col) != (0, 0)
    }
    return _crop_to_cells(grid, cells)


def _include_selector_key_crop(grid: list[list[int]]) -> list[list[int]]:
    selector = grid[0][0]
    cells = {
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == selector
    }
    return _crop_to_cells(grid, cells)


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "mask_selector_only": _mask_selector_only,
    "modal_nonzero_crop": _modal_nonzero_crop,
    "first_selector_component": _first_selector_component_crop,
    "all_nonzero_body_bbox": _all_nonzero_body_crop,
    "include_selector_key": _include_selector_key_crop,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _lawful_facts(grid) -> dict[str, Any] | None:
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis


def _preserves_interior_distractor(grid) -> bool:
    facts = _lawful_facts(grid)
    return bool(facts and facts["interior_other"])


def _selector_not_modal(grid) -> bool:
    facts = _lawful_facts(grid)
    return bool(facts and facts["modal_nonzero"] != facts["selector"])


def _all_selector_components_needed(grid) -> bool:
    facts = _lawful_facts(grid)
    if not facts or len(facts["target_components"]) < 2:
        return False
    return _first_selector_component_crop(grid) != facts["output"]


def _outside_distractors_must_be_ignored(grid) -> bool:
    facts = _lawful_facts(grid)
    return bool(facts and facts["exterior_other"] and _all_nonzero_body_crop(grid) != facts["output"])


def _selector_key_must_be_excluded(grid) -> bool:
    facts = _lawful_facts(grid)
    return bool(facts and _include_selector_key_crop(grid) != facts["output"])


SEMANTIC_WITNESSES = {
    "preserve_interior_distractor": _preserves_interior_distractor,
    "selector_not_modal": _selector_not_modal,
    "joint_bbox_across_components": _all_selector_components_needed,
    "ignore_outside_distractors": _outside_distractors_must_be_ignored,
    "exclude_selector_key": _selector_key_must_be_excluded,
}
WITNESS_RIVALS = {
    "preserve_interior_distractor": ["mask_selector_only"],
    "selector_not_modal": ["modal_nonzero_crop"],
    "joint_bbox_across_components": ["first_selector_component"],
    "ignore_outside_distractors": ["all_nonzero_body_bbox"],
    "exclude_selector_key": ["include_selector_key"],
}


def _same_grid(left: Any, right: Any) -> bool:
    return left == right


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson when a named rival fits demos but changes the query."""
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits = all(
                _same_grid(competitor(demo["input"]), demo["output"])
                for demo in demos
            )
            query_differs = not _same_grid(
                competitor(query["input"]), query["output"]
            )
        except Exception as exc:  # a broken competitor cannot certify ambiguity
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits and query_differs:
            reasons.append(f"competitor {name} fits every demo but changes the query")
    return reasons


def _reflected_pattern(
    pattern: tuple[tuple[int, int], ...],
    height: int,
    width: int,
    flip_rows: bool,
    flip_cols: bool,
) -> tuple[tuple[int, int], ...]:
    return tuple(
        (
            height - 1 - row if flip_rows else row,
            width - 1 - col if flip_cols else col,
        )
        for row, col in pattern
    )


def _dimensions(profile: str, difficulty: str | None, rng) -> tuple[int, int]:
    bbox_height, bbox_width, _ = _PROFILE_PATTERNS[profile]
    extra = {None: 6, "easy": 5, "medium": 6, "hard": 8}[difficulty]
    height = max(bbox_height + 4, 9) + rng.randint(0, max(1, extra - 4))
    width = max(bbox_width + 4, 11) + rng.randint(0, max(1, extra - 4))
    return min(height, 18), min(width, 20)



def _public_scene(ctx, profile: str) -> list[list[int]]:
    """Recolor a canonical anchor while preserving its exact geometry/profile."""
    grid = _PUBLIC_INPUTS[profile]
    old_colors = []
    for row in grid:
        for value in row:
            if value != 0 and value not in old_colors:
                old_colors.append(value)
    rng = ctx.draw_rng("public_palette")
    new_colors = rng.sample(tuple(range(1, 10)), len(old_colors))
    mapping = dict(zip(old_colors, new_colors))
    recolored = [
        [0 if value == 0 else mapping[value] for value in row]
        for row in grid
    ]
    analysis = _analysis(recolored)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"public profile drift: {profile} -> {analysis}")
    return recolored

def _general_scene(ctx, profile: str) -> list[list[int]]:
    rng = ctx.draw_rng("geometry")
    bbox_height, bbox_width, base_pattern = _PROFILE_PATTERNS[profile]
    height, width = _dimensions(profile, ctx.difficulty, rng)
    if height < bbox_height + 3 or width < bbox_width + 2:
        raise AssertionError("internal dimensions cannot fit the selected profile")

    colors = rng.sample(tuple(range(1, 10)), 2)
    selector, decoy = colors
    grid = full_grid(height, width, 0)
    grid[0][0] = selector

    # Reserve three top rows for a dominant non-selector decoy.  The selected
    # bbox therefore starts below the key and cannot accidentally include it.
    row0 = height - bbox_height if profile == "edge_adversary" else rng.randint(3, height - bbox_height)
    col0 = (
        width - bbox_width
        if profile == "edge_adversary" and rng.random() < 0.5
        else rng.randint(1, width - bbox_width)
    )
    pattern = _reflected_pattern(
        base_pattern,
        bbox_height,
        bbox_width,
        flip_rows=bool(rng.randint(0, 1)),
        flip_cols=bool(rng.randint(0, 1)),
    )
    for row, col in pattern:
        grid[row0 + row][col0 + col] = selector

    zero_inside = [
        (row0 + row, col0 + col)
        for row in range(bbox_height)
        for col in range(bbox_width)
        if grid[row0 + row][col0 + col] == 0
    ]
    if not zero_inside:
        raise AssertionError("adversarial profile unexpectedly fills its bbox")
    center = (row0 + bbox_height // 2, col0 + bbox_width // 2)
    interior = min(
        zero_inside,
        key=lambda cell: (abs(cell[0] - center[0]) + abs(cell[1] - center[1]), cell),
    )
    grid[interior[0]][interior[1]] = decoy

    exterior_slots = [
        (row, col)
        for row in range(min(3, row0))
        for col in range(width)
        if (row, col) != (0, 0)
    ]
    rng.shuffle(exterior_slots)
    exterior_count = len(pattern) + 3
    if len(exterior_slots) < exterior_count:
        raise AssertionError("not enough exterior slots for modal-color counterexample")
    for row, col in exterior_slots[:exterior_count]:
        grid[row][col] = decoy

    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError(f"internal profile drift: {profile} -> {analysis}")
    for witness in SEMANTIC_WITNESSES.values():
        if not witness(grid):
            raise AssertionError(f"profile {profile} failed a mandatory semantic witness")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"scene_profile must be one of {SCENE_PROFILES}, got {requested!r}")
    scheduled = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    # Record the scheduled profile through the public keyed-draw API so the
    # default-path provenance can be compared with the returned grid.
    profile = ctx.draw_choice(
        "scene_profile",
        SCENE_PROFILES if requested is not None else (scheduled,),
    )
    if profile in PUBLIC_PROFILES:
        return _public_scene(ctx, profile)
    return _general_scene(ctx, profile)
