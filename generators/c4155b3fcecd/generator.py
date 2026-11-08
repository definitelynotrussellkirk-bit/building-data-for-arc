"""Generator for ARC task ``c4155b3fcecd``.

Rule: copy every nonzero singleton marker to the horizontally opposite cell,
reflecting across the vertical center line while retaining the source marker.

The canonical examples put every source on the left, so a left-to-right-only
shortcut fits them all.  The finite curriculum below deliberately cycles
through both-sided, canonical-profile left-only, both-sided, and right-only
scenes.  Any two demonstrations left after rotating a three-pair lesson expose
sources on both sides and therefore identify the bidirectional rule against
that shortcut.
"""
from __future__ import annotations

from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "c4155b3fcecd"
TASK_ID = GENERATOR_ID
VERSION = "2.0.0"
RULE_HASH = "e45306d2be09"

SUMMARY = (
    "Copy every sparse nonzero singleton marker to its vertical-axis mirror "
    "position, keeping the original marker."
)

INVARIANTS = [
    "the background is zero and every nonzero input cell is an orthogonally isolated singleton marker",
    "ordinary inputs contain at least two marker colors, rows, and mirror distances",
    "no marker lies on an odd-width center column or occupies another marker's mirror target",
    "sources may occur on the left, the right, or both sides of the vertical axis",
]

# name, band, height, width, marker count, color count, left count, right count
#
# Slot 1 in each band exactly matches one canonical (height, width, nonzero
# palette-size) profile.  Slot order is semantically important: both, left,
# both, right makes every cyclic three-pair window identifiable after any one
# pair is held out as query.
_PROFILE_ROWS = (
    ("e5x7_n4_c2_both", "easy", 5, 7, 4, 2, 2, 2),
    ("e6x9_n3_c3_left", "easy", 6, 9, 3, 3, 3, 0),
    ("e6x8_n5_c3_both", "easy", 6, 8, 5, 3, 3, 2),
    ("e7x9_n4_c3_right", "easy", 7, 9, 4, 3, 0, 4),
    ("m6x10_n5_c3_both", "medium", 6, 10, 5, 3, 2, 3),
    ("m7x10_n2_c2_left", "medium", 7, 10, 2, 2, 2, 0),
    ("m7x9_n5_c3_both", "medium", 7, 9, 5, 3, 3, 2),
    ("m8x10_n4_c3_right", "medium", 8, 10, 4, 3, 0, 4),
    ("h8x12_n6_c4_both", "hard", 8, 12, 6, 4, 3, 3),
    ("h8x11_n3_c3_left", "hard", 8, 11, 3, 3, 3, 0),
    ("h9x13_n7_c4_both", "hard", 9, 13, 7, 4, 4, 3),
    ("h9x12_n5_c4_right", "hard", 9, 12, 5, 4, 0, 5),
)
SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {row[0]: row[1:] for row in _PROFILE_ROWS}
_PROFILE_BY_SIGNATURE = {
    (row[2], row[3], row[4], row[5], row[6], row[7]): row[0]
    for row in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    band: tuple(row[0] for row in _PROFILE_ROWS if row[1] == band)
    for band in ("easy", "medium", "hard")
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot both/left/both/right curriculum for the selected difficulty band",
        "valid": (
            "e5x7_n4_c2_both|e6x9_n3_c3_left|e6x8_n5_c3_both|e7x9_n4_c3_right|"
            "m6x10_n5_c3_both|m7x10_n2_c2_left|m7x9_n5_c3_both|m8x10_n4_c3_right|"
            "h8x12_n6_c4_both|h8x11_n3_c3_left|h9x13_n7_c4_both|h9x12_n5_c4_right"
        ),
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 2


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-slot profile for a difficulty band."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 3 <= len(grid) <= 14 or not 3 <= width <= 14:
        return [f"grid dimensions must be in 3..14, found {len(grid)}x{width}"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _side(width: int, col: int) -> str:
    if col < width // 2:
        return "left"
    if col >= (width + 1) // 2:
        return "right"
    return "axis"


def _mirror_distance(width: int, col: int) -> int:
    """Integer distance proxy from the vertical axis, invariant under mirror."""
    return abs((width - 1) - 2 * col)


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    markers = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    if len(markers) < 2:
        errors.append(f"expected at least two singleton markers, found {len(markers)}")

    axis_markers = [(r, c) for r, c, _ in markers if _side(width, c) == "axis"]
    if axis_markers:
        errors.append("markers must avoid the odd-width vertical center column")

    positions = {(r, c) for r, c, _ in markers}
    for r, c, _ in markers:
        if any(
            neighbor in positions
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        ):
            errors.append("every nonzero marker must be an orthogonal singleton")
            break

    mirror_collisions = [
        (r, c)
        for r, c, _ in markers
        if (r, width - 1 - c) in positions
    ]
    if mirror_collisions:
        errors.append("a marker's mirror target must be background in the input")

    colors = {value for _, _, value in markers}
    rows = {r for r, _, _ in markers}
    distances = {_mirror_distance(width, c) for _, c, _ in markers}
    if len(colors) < 2:
        errors.append("ordinary scenes need at least two marker colors")
    if len(rows) < 2:
        errors.append("ordinary scenes need markers on at least two rows")
    if len(distances) < 2:
        errors.append("ordinary scenes need at least two mirror distances")

    left_count = sum(_side(width, c) == "left" for _, c, _ in markers)
    right_count = sum(_side(width, c) == "right" for _, c, _ in markers)
    signature = (
        height,
        width,
        len(markers),
        len(colors),
        left_count,
        right_count,
    )
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "markers": markers,
        "colors": colors,
        "rows": rows,
        "distances": distances,
        "left_count": left_count,
        "right_count": right_count,
        "scene_profile": _PROFILE_BY_SIGNATURE.get(signature),
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept canonical inputs and reject malformed or shortcut-hiding scenes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The ordinary sparse-singleton manifold used by canonical and generated inputs."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the sole exact axis from returned pixels."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def _placement_is_compatible(
    candidate: tuple[int, int], chosen: Sequence[tuple[int, int]], width: int
) -> bool:
    r, c = candidate
    for rr, cc in chosen:
        if max(abs(r - rr), abs(c - cc)) <= 1:
            return False
        if r == rr and c == width - 1 - cc:
            return False
    return True


def _choose_positions(
    height: int,
    width: int,
    left_needed: int,
    right_needed: int,
    rng,
) -> list[tuple[int, int]]:
    """Choose sparse source positions with exact side counts and visible diversity."""
    pools = {
        "left": [(r, c) for r in range(height) for c in range(width) if _side(width, c) == "left"],
        "right": [(r, c) for r in range(height) for c in range(width) if _side(width, c) == "right"],
    }
    target_sides = ["left"] * left_needed + ["right"] * right_needed

    for _attempt in range(256):
        rng.shuffle(target_sides)
        shuffled = {name: list(cells) for name, cells in pools.items()}
        rng.shuffle(shuffled["left"])
        rng.shuffle(shuffled["right"])
        chosen: list[tuple[int, int]] = []
        for side in target_sides:
            candidate = next(
                (
                    cell
                    for cell in shuffled[side]
                    if cell not in chosen
                    and _placement_is_compatible(cell, chosen, width)
                ),
                None,
            )
            if candidate is None:
                break
            chosen.append(candidate)
        if len(chosen) != len(target_sides):
            continue
        if len({r for r, _ in chosen}) < 2:
            continue
        if len({_mirror_distance(width, c) for _, c in chosen}) < 2:
            continue
        return chosen
    raise RuntimeError(
        f"could not place {left_needed}+{right_needed} singleton markers in {height}x{width}"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", [scheduled])
    _profile_band, height, width, n_markers, n_colors, left_count, right_count = _PROFILE_BY_NAME[profile]
    rng = ctx.draw_rng("layout")
    positions = _choose_positions(height, width, left_count, right_count, rng)
    colors = list(ctx.draw_distinct_colors("colors", n=n_colors, exclude={0}))
    assignments = colors + [colors[index % n_colors] for index in range(n_markers - n_colors)]
    rng.shuffle(assignments)

    grid = full_grid(height, width, 0)
    for (row, col), color in zip(positions, assignments):
        grid[row][col] = color
    return grid


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python oracle for tests; synchronized Racket remains authority."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("invalid grid: " + "; ".join(errors))
    output = [list(row) for row in grid]
    width = len(output[0])
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0:
                output[row][width - 1 - col] = value
    return output


def _rival_left_only(grid):
    """Canonical-compatible wrong shortcut: copy only left-side sources."""
    output = [list(row) for row in grid]
    width = len(output[0])
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0 and _side(width, col) == "left":
                output[row][width - 1 - col] = value
    return output


def _rival_right_only(grid):
    output = [list(row) for row in grid]
    width = len(output[0])
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0 and _side(width, col) == "right":
                output[row][width - 1 - col] = value
    return output


def _rival_first_color_only(grid):
    output = [list(row) for row in grid]
    width = len(output[0])
    first = next((value for values in grid for value in values if value != 0), None)
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0 and value == first:
                output[row][width - 1 - col] = value
    return output


def _rival_nearest_distance_only(grid):
    output = [list(row) for row in grid]
    width = len(output[0])
    distances = [
        _mirror_distance(width, col)
        for values in grid
        for col, value in enumerate(values)
        if value != 0
    ]
    nearest = min(distances) if distances else None
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value != 0 and _mirror_distance(width, col) == nearest:
                output[row][width - 1 - col] = value
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "mirror_left_side_only": _rival_left_only,
    "mirror_right_side_only": _rival_right_only,
    "mirror_first_color_only": _rival_first_color_only,
    "mirror_nearest_distance_only": _rival_nearest_distance_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {"mirror_left_side_only": _rival_left_only}


def _has_left_source(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["left_count"] > 0


def _has_right_source(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and analysis["right_count"] > 0


def _has_multiple_colors(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["colors"]) > 1


def _has_multiple_distances(grid) -> bool:
    analysis = _analysis(grid)
    return not analysis["errors"] and len(analysis["distances"]) > 1


SEMANTIC_WITNESSES = {
    "left_source": _has_left_source,
    "right_source": _has_right_source,
    "multiple_colors": _has_multiple_colors,
    "multiple_mirror_distances": _has_multiple_distances,
}
WITNESS_RIVALS = {
    "left_source": ["mirror_right_side_only"],
    "right_source": ["mirror_left_side_only"],
    "multiple_colors": ["mirror_first_color_only"],
    "multiple_mirror_distances": ["mirror_nearest_distance_only"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Reject lessons where a named plausible rival survives every demo."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    sides: set[str] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the vertical-mirror rule")
        analysis = _analysis(pair["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} is outside the ordinary singleton manifold")
        else:
            if analysis["left_count"]:
                sides.add("left")
            if analysis["right_count"]:
                sides.add("right")
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the vertical-mirror rule")
    if sides != {"left", "right"}:
        reasons.append("demonstrations must include source markers on both sides of the axis")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
