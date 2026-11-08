"""Curriculum generator for ARC task ae0a295c2271 / b230c067.

The authoritative transformation is object-frequency recoloring.  Treat every
4-connected non-background component as an object and compare exact
translation-normalized cell sets (rotations/reflections are *not* equivalent).
Objects whose exact shape occurs once become red (2); objects whose exact shape
occurs twice become blue (1); background remains 0.

Version 4 keeps the deterministic three-profile curriculum while removing a
positional shortcut: the row-major first object now alternates between a
repeated and singleton shape class.  Every three consecutive ordinary examples
include both first-object roles plus:

* a canonical-scale large-shape episode,
* a canonical-scale six-object episode with two different repeated classes and
  two unique classes of the same size and D4 orbit, and
* a non-canonical-palette episode.

Together those witnesses refute size-frequency, rotation/flip-equivalence,
"only the modal shape repeats", fixed-position, one-output-color, and
color-8-only shortcuts while retaining exact canonical dimensions/palette in
all difficulty bands.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Callable, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ae0a295c2271"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "6c9ec74ee7cf"

SUMMARY = (
    "Find each 4-connected nonzero object and compare its exact normalized "
    "shape with every other object. Recolor a singleton shape class red (2) "
    "and a repeated shape class blue (1); leave background 0. Rotation and "
    "reflection do not count as the same shape."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.50

INVARIANTS = [
    "background is 0 and all object cells share one input color outside {0,1,2}",
    "ordinary scenes contain at least one singleton and one repeated exact-shape class",
    "ordinary repeated classes contain exactly two translated copies",
    "objects are 4-connected, disjoint, and generated with a one-cell moat",
    "exact translation-normalized shape, not size or D4 orbit, determines recoloring",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "10x10 canonical anchors plus difficulty-skewed varied scenes",
        "valid": "10..20",
    },
    "grid_w": {
        "type": "int",
        "default": "10x10 canonical anchors plus difficulty-skewed varied scenes",
        "valid": "10..20",
    },
    "n_twin_pairs": {
        "type": "int",
        "default": "scheduled 1 or 2 distinct repeated shape classes",
        "valid": "1..2",
    },
    "n_uniques": {
        "type": "int",
        "default": "scheduled 1 or 2 singleton shape classes",
        "valid": "1..2",
    },
    "input_color": {
        "type": "color",
        "default": "canonical 8 anchors plus varied colors",
        "valid": "3..9",
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

SCHEDULE_PROFILES = (
    "canonical_large_one_pair",
    "canonical_two_pairs_d4",
    "varied_palette",
)

# Four exact orientations per family.  Within each family every shape has the
# same area and belongs to one D4 orbit.  This lets generated episodes separate
# exact-shape frequency from both size-frequency and rotation/flip frequency.
_SHAPE_FAMILIES: dict[str, dict[str, tuple[tuple[int, int], ...]]] = {
    "corner3": {
        "corner_nw": ((0, 0), (0, 1), (1, 0)),
        "corner_ne": ((0, 0), (0, 1), (1, 1)),
        "corner_sw": ((0, 0), (1, 0), (1, 1)),
        "corner_se": ((0, 1), (1, 0), (1, 1)),
    },
    "tee4": {
        "tee_up": ((0, 0), (0, 1), (0, 2), (1, 1)),
        "tee_down": ((0, 1), (1, 0), (1, 1), (1, 2)),
        "tee_left": ((0, 0), (1, 0), (1, 1), (2, 0)),
        "tee_right": ((0, 1), (1, 0), (1, 1), (2, 1)),
    },
    "ell4": {
        "ell_nw": ((0, 0), (1, 0), (1, 1), (1, 2)),
        "ell_ne": ((0, 2), (1, 0), (1, 1), (1, 2)),
        "ell_sw": ((0, 0), (0, 1), (0, 2), (1, 0)),
        "ell_se": ((0, 0), (0, 1), (0, 2), (1, 2)),
    },
    "notch8": {
        "notch_nw": tuple(
            (r, c) for r in range(3) for c in range(3) if (r, c) != (0, 0)
        ),
        "notch_ne": tuple(
            (r, c) for r in range(3) for c in range(3) if (r, c) != (0, 2)
        ),
        "notch_sw": tuple(
            (r, c) for r in range(3) for c in range(3) if (r, c) != (2, 0)
        ),
        "notch_se": tuple(
            (r, c) for r in range(3) for c in range(3) if (r, c) != (2, 2)
        ),
    },
}

_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    name: cells
    for family in _SHAPE_FAMILIES.values()
    for name, cells in family.items()
}
_SHAPE_NAME_BY_CELLS = {cells: name for name, cells in _SHAPES.items()}


def _validate_call(
    seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]
) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a literal Python integer")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be a literal Python integer")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError("unknown override(s): " + ", ".join(unknown))
    for name, lo, hi in (
        ("grid_h", 10, 20),
        ("grid_w", 10, 20),
        ("n_twin_pairs", 1, 2),
        ("n_uniques", 1, 2),
        ("input_color", 3, 9),
    ):
        if name not in overrides or overrides[name] is None:
            continue
        value = overrides[name]
        if isinstance(value, bool) or not isinstance(value, int) or not lo <= value <= hi:
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Three consecutive examples cover every decisive curriculum profile."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _draw_scheduled_int(ctx, name: str, lo: int, hi: int, default: int, overrides: dict[str, Any]) -> int:
    if overrides.get(name) is not None:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_int(name, default, default)


def _draw_scheduled_color(ctx, default: int, overrides: dict[str, Any]) -> int:
    if overrides.get("input_color") is not None:
        return ctx.draw_color("input_color", exclude={0, 1, 2})
    return ctx.draw_choice("input_color", (default,))


def _profile_defaults(ctx, profile: str, difficulty: Any) -> dict[str, int]:
    if profile == "canonical_large_one_pair":
        return {
            "grid_h": 10,
            "grid_w": 10,
            "n_twin_pairs": 1,
            "n_uniques": 1,
            "input_color": 8,
        }
    if profile == "canonical_two_pairs_d4":
        return {
            "grid_h": 10,
            "grid_w": 10,
            "n_twin_pairs": 2,
            "n_uniques": 2,
            "input_color": 8,
        }

    # The varied profile is deliberately non-8 so a palette-conditioned rule
    # cannot survive a complete three-demo window.  Difficulty changes scale,
    # not semantics.
    if difficulty == "easy":
        h_lo, h_hi, w_lo, w_hi = 10, 13, 10, 13
    elif difficulty == "hard":
        h_lo, h_hi, w_lo, w_hi = 17, 20, 17, 20
    else:
        h_lo, h_hi, w_lo, w_hi = 12, 18, 12, 18
    color = ctx.draw_rng("varied_color").choice((3, 4, 5, 6, 7, 9))
    return {
        "grid_h": ctx.draw_rng("varied_h").randint(h_lo, h_hi),
        "grid_w": ctx.draw_rng("varied_w").randint(w_lo, w_hi),
        "n_twin_pairs": 1 + ctx.draw_rng("varied_pairs").randrange(2),
        "n_uniques": 1 + ctx.draw_rng("varied_uniques").randrange(2),
        "input_color": color,
    }


def _shape_plan(profile: str, n_pairs: int, n_uniques: int, rng) -> list[tuple[str, bool]]:
    """Return ``(shape_name, is_repeated)`` classes, not object copies."""
    class_count = n_pairs + n_uniques
    if profile == "canonical_large_one_pair" and class_count <= 2:
        names = list(_SHAPE_FAMILIES["notch8"])
    elif profile == "canonical_two_pairs_d4":
        names = list(_SHAPE_FAMILIES["corner3"])
    else:
        family_name = rng.choice(("corner3", "tee4", "ell4"))
        names = list(_SHAPE_FAMILIES[family_name])
    rng.shuffle(names)
    names = names[:class_count]
    repeated = names[:n_pairs]
    uniques = names[n_pairs:]
    return [(name, True) for name in repeated] + [(name, False) for name in uniques]


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int]:
    points = tuple(cells)
    return max(r for r, _ in points) + 1, max(c for _, c in points) + 1


def _candidate_origins(h: int, w: int, cells: tuple[tuple[int, int], ...], rng) -> list[tuple[int, int]]:
    sh, sw = _bbox(cells)
    origins = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
    rng.shuffle(origins)
    return origins


def _can_place(grid: list[list[int]], cells: tuple[tuple[int, int], ...], r0: int, c0: int) -> bool:
    h, w = len(grid), len(grid[0])
    for dr, dc in cells:
        r, c = r0 + dr, c0 + dc
        for rr in range(max(0, r - 1), min(h, r + 2)):
            for cc in range(max(0, c - 1), min(w, c + 2)):
                if grid[rr][cc] != 0:
                    return False
    return True


def _paint(grid: list[list[int]], cells: tuple[tuple[int, int], ...], r0: int, c0: int, color: int) -> None:
    for dr, dc in cells:
        grid[r0 + dr][c0 + dc] = color


def _erase(grid: list[list[int]], cells: tuple[tuple[int, int], ...], r0: int, c0: int) -> None:
    for dr, dc in cells:
        grid[r0 + dr][c0 + dc] = 0


def _place_object_multiset(
    h: int,
    w: int,
    shape_names: list[str],
    color: int,
    rng,
    lead_shape: str,
) -> list[list[int]]:
    """Backtracking placement with a one-cell moat and a selected first role."""
    grid = full_grid(h, w, 0)
    first_cells = _SHAPES[lead_shape]
    first_h, first_w = _bbox(first_cells)
    # Pin one scheduled class to the top-left so the row-major first object's
    # semantic role is explicit and testable.  The caller alternates that role
    # between repeated and singleton classes; all remaining placement varies.
    first_candidates = [(0, 0)]

    remaining = list(shape_names)
    remaining.remove(lead_shape)
    # Larger shapes first drastically reduces backtracking; ties are shuffled.
    rng.shuffle(remaining)
    remaining.sort(key=lambda name: len(_SHAPES[name]), reverse=True)

    def place_rest(index: int) -> bool:
        if index == len(remaining):
            return True
        cells = _SHAPES[remaining[index]]
        for r0, c0 in _candidate_origins(h, w, cells, rng):
            if not _can_place(grid, cells, r0, c0):
                continue
            _paint(grid, cells, r0, c0, color)
            if place_rest(index + 1):
                return True
            _erase(grid, cells, r0, c0)
        return False

    for r0, c0 in first_candidates:
        if not _can_place(grid, first_cells, r0, c0):
            continue
        _paint(grid, first_cells, r0, c0, color)
        if place_rest(0):
            return grid
        _erase(grid, first_cells, r0, c0)
    raise RuntimeError(
        f"unable to place {len(shape_names)} objects with margins on {h}x{w}"
    )


def generate(seed: int, sample_index: int, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    defaults = _profile_defaults(ctx, profile, difficulty)
    h = _draw_scheduled_int(ctx, "grid_h", 10, 20, defaults["grid_h"], overrides)
    w = _draw_scheduled_int(ctx, "grid_w", 10, 20, defaults["grid_w"], overrides)
    n_pairs = _draw_scheduled_int(
        ctx, "n_twin_pairs", 1, 2, defaults["n_twin_pairs"], overrides
    )
    n_uniques = _draw_scheduled_int(
        ctx, "n_uniques", 1, 2, defaults["n_uniques"], overrides
    )
    color = _draw_scheduled_color(ctx, defaults["input_color"], overrides)

    layout_rng = ctx.draw_rng("shape_and_layout")
    classes = _shape_plan(profile, n_pairs, n_uniques, layout_rng)
    repeated_names = [name for name, repeated in classes if repeated]
    unique_names = [name for name, repeated in classes if not repeated]
    object_shapes = [name for name in repeated_names for _ in range(2)] + unique_names
    # Every three-example window contains both row-major first roles.  This
    # refutes positional exceptions such as "force the first object red" while
    # preserving the same object-frequency rule and profile schedule.
    lead_shape = repeated_names[0] if sample_index % 2 == 0 else unique_names[0]
    grid = _place_object_multiset(h, w, object_shapes, color, layout_rng, lead_shape)
    errors = self_check(grid)
    if errors:
        raise RuntimeError("generated invalid scene: " + "; ".join(errors))
    return grid


def _component_cells(grid: Any) -> tuple[list[list[tuple[int, int]]], list[str]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return [], ["empty grid"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return [], ["empty row"]
    w = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        return [], ["ragged grid"]
    h = len(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return [], [f"invalid color at ({r},{c}): {value!r}"]

    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 0 or (r, c) in seen:
                continue
            color = grid[r][c]
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(sorted(cells))
    components.sort(key=lambda cells: min(cells))
    return components, []


def _normalize_cells(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _analysis(grid: Any) -> dict[str, Any]:
    components, errors = _component_cells(grid)
    if errors:
        return {"errors": errors, "components": [], "shapes": [], "frequencies": {}}
    shapes = [_normalize_cells(cells) for cells in components]
    frequencies = Counter(shapes)
    colors = {
        grid[r][c]
        for cells in components
        for r, c in cells
    }
    return {
        "errors": [],
        "components": components,
        "shapes": shapes,
        "frequencies": frequencies,
        "colors": colors,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Structural grammar shared by canonical inputs and generated scenes."""
    del difficulty, meta
    analysis = _analysis(grid)
    if analysis["errors"]:
        return list(analysis["errors"])
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not (5 <= h <= 30 and 5 <= w <= 30):
        errors.append(f"grid dimensions outside supported grammar: {h}x{w}")
    components = analysis["components"]
    if not (3 <= len(components) <= 6):
        errors.append(f"expected 3..6 non-background objects, found {len(components)}")
    if len(analysis["colors"]) != 1:
        errors.append(f"objects must share one input color, found {sorted(analysis['colors'])}")
    elif next(iter(analysis["colors"]), 0) in (0, 1, 2):
        errors.append("input object color must exclude output colors 1 and 2")
    for index, cells in enumerate(components):
        if not (3 <= len(cells) <= 10):
            errors.append(f"object {index} area {len(cells)} outside canonical 3..10")
    counts = sorted(analysis["frequencies"].values())
    if any(count not in (1, 2) for count in counts):
        errors.append(f"shape-class multiplicities must be 1 or 2, found {counts}")
    n_unique = sum(count == 1 for count in counts)
    n_repeated = sum(count == 2 for count in counts)
    if not (1 <= n_unique <= 2):
        errors.append(f"expected 1..2 singleton shape classes, found {n_unique}")
    if not (1 <= n_repeated <= 2):
        errors.append(f"expected 1..2 repeated shape classes, found {n_repeated}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Canonical-scale/palette branch used by the strict semantic census."""
    errors = self_check(grid)
    if errors:
        return errors
    if len(grid) != 10 or len(grid[0]) != 10:
        return ["canonical dimensions are 10x10"]
    palette = {value for row in grid for value in row}
    if palette != {0, 8}:
        return [f"canonical input palette is {{0,8}}, found {sorted(palette)}"]
    signature = tuple(sorted(_analysis(grid)["frequencies"].values()))
    if signature not in ((1, 2), (1, 1, 2, 2)):
        return [f"canonical shape-frequency signature not matched: {signature}"]
    return []


def rule_mirror(grid) -> list[list[int]]:
    """Pinned Python audit mirror; labels still come from the Racket oracle."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid grid: " + "; ".join(analysis["errors"]))
    output = [list(row) for row in grid]
    for cells, shape in zip(analysis["components"], analysis["shapes"]):
        color = 2 if analysis["frequencies"][shape] == 1 else 1
        for r, c in cells:
            output[r][c] = color
    return output


def observe_overrides(grid) -> dict[str, int]:
    """Recover every declared exact axis from the returned grid."""
    analysis = _analysis(grid)
    observed = {
        "grid_h": len(grid) if isinstance(grid, (list, tuple)) else 0,
        "grid_w": len(grid[0]) if isinstance(grid, (list, tuple)) and grid else 0,
    }
    if analysis["errors"]:
        return observed
    counts = analysis["frequencies"].values()
    observed.update(
        {
            "n_twin_pairs": sum(count == 2 for count in counts),
            "n_uniques": sum(count == 1 for count in counts),
            "input_color": next(iter(analysis["colors"])),
        }
    )
    return observed


def semantic_observables(grid) -> dict[str, Any]:
    analysis = _analysis(grid)
    counts = sorted(analysis.get("frequencies", {}).values())
    first_count = (
        analysis["frequencies"][analysis["shapes"][0]]
        if analysis.get("shapes")
        else 0
    )
    return {
        **observe_overrides(grid),
        "shape_frequency_signature": counts,
        "both_output_branches": 1 in counts and 2 in counts,
        "first_object_frequency": first_count,
        "strict_canonical_like": not strict_canonical_like(grid),
    }


def _recolor_by_group_key(grid, key_fn: Callable[[tuple[tuple[int, int], ...]], Any]) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    keys = [key_fn(shape) for shape in analysis["shapes"]]
    frequencies = Counter(keys)
    output = [list(row) for row in grid]
    for cells, key in zip(analysis["components"], keys):
        color = 2 if frequencies[key] == 1 else 1
        for r, c in cells:
            output[r][c] = color
    return output


def _transform_shape(shape: tuple[tuple[int, int], ...], transform: str) -> tuple[tuple[int, int], ...]:
    points = list(shape)
    max_r = max(r for r, _ in points)
    max_c = max(c for _, c in points)
    if transform == "identity":
        raw = points
    elif transform == "rot90":
        raw = [(c, max_r - r) for r, c in points]
    elif transform == "rot180":
        raw = [(max_r - r, max_c - c) for r, c in points]
    elif transform == "rot270":
        raw = [(max_c - c, r) for r, c in points]
    elif transform == "flip_lr":
        raw = [(r, max_c - c) for r, c in points]
    elif transform == "flip_ud":
        raw = [(max_r - r, c) for r, c in points]
    elif transform == "transpose":
        raw = [(c, r) for r, c in points]
    else:
        raw = [(max_c - c, max_r - r) for r, c in points]
    return _normalize_cells(raw)


def _d4_key(shape: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    return min(
        _transform_shape(shape, name)
        for name in (
            "identity", "rot90", "rot180", "rot270",
            "flip_lr", "flip_ud", "transpose", "anti_transpose",
        )
    )


def _rival_all_blue(grid):
    output = [list(row) for row in grid]
    for r, row in enumerate(output):
        for c, value in enumerate(row):
            if value != 0:
                output[r][c] = 1
    return output


def _rival_all_red(grid):
    output = [list(row) for row in grid]
    for r, row in enumerate(output):
        for c, value in enumerate(row):
            if value != 0:
                output[r][c] = 2
    return output


def _rival_size_frequency(grid):
    return _recolor_by_group_key(grid, len)


def _rival_d4_frequency(grid):
    return _recolor_by_group_key(grid, _d4_key)


def _rival_only_first_repeated_class(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    repeated = [shape for shape in analysis["shapes"] if analysis["frequencies"][shape] == 2]
    chosen = repeated[0] if repeated else None
    output = [list(row) for row in grid]
    for cells, shape in zip(analysis["components"], analysis["shapes"]):
        color = 1 if chosen is not None and shape == chosen else 2
        for r, c in cells:
            output[r][c] = color
    return output


def _rival_color8_only(grid):
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["colors"] != {8}:
        return [list(row) for row in grid]
    return rule_mirror(grid)


def _rival_first_red_rest_blue(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return [list(row) for row in grid]
    output = [list(row) for row in grid]
    for index, cells in enumerate(analysis["components"]):
        for r, c in cells:
            output[r][c] = 2 if index == 0 else 1
    return output


def _rival_force_first_red(grid):
    """Apply the intended rule except for a positional first-object exception."""
    output = rule_mirror(grid)
    analysis = _analysis(grid)
    if analysis["errors"] or not analysis["components"]:
        return output
    for r, c in analysis["components"][0]:
        output[r][c] = 2
    return output


def _rival_force_first_blue(grid):
    """Apply the intended rule except for the opposite positional exception."""
    output = rule_mirror(grid)
    analysis = _analysis(grid)
    if analysis["errors"] or not analysis["components"]:
        return output
    for r, c in analysis["components"][0]:
        output[r][c] = 1
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "all_objects_repeated_blue": _rival_all_blue,
    "all_objects_unique_red": _rival_all_red,
    "frequency_by_area_not_shape": _rival_size_frequency,
    "frequency_by_rotation_or_reflection_orbit": _rival_d4_frequency,
    "only_first_repeated_class_is_blue": _rival_only_first_repeated_class,
    "apply_rule_only_when_input_color_is_8": _rival_color8_only,
    "first_object_red_everything_else_blue": _rival_first_red_rest_blue,
    "force_first_object_red_then_apply_frequency_rule": _rival_force_first_red,
    "force_first_object_blue_then_apply_frequency_rule": _rival_force_first_blue,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Only this palette-conditioned shortcut agrees with every retained canonical
# pair.  The other named rivals are intentionally partial lesson competitors
# and must not be advertised as canonical-equivalent shortcuts.
CANONICAL_SHORTCUTS = {
    "apply_rule_only_when_input_color_is_8": _rival_color8_only,
}


def _both_branches(grid) -> bool:
    counts = _analysis(grid).get("frequencies", {}).values()
    return any(count == 1 for count in counts) and any(count == 2 for count in counts)


def _same_size_different_frequency(grid) -> bool:
    analysis = _analysis(grid)
    entries = [(len(shape), count) for shape, count in analysis.get("frequencies", {}).items()]
    return any(size_a == size_b and count_a != count_b for i, (size_a, count_a) in enumerate(entries) for size_b, count_b in entries[i + 1:])


def _d4_related_different_frequency(grid) -> bool:
    analysis = _analysis(grid)
    entries = [(shape, count) for shape, count in analysis.get("frequencies", {}).items()]
    return any(_d4_key(shape_a) == _d4_key(shape_b) and count_a != count_b for i, (shape_a, count_a) in enumerate(entries) for shape_b, count_b in entries[i + 1:])


def _two_repeated_classes(grid) -> bool:
    return sum(count == 2 for count in _analysis(grid).get("frequencies", {}).values()) >= 2


def _multiple_unique_classes(grid) -> bool:
    return sum(count == 1 for count in _analysis(grid).get("frequencies", {}).values()) >= 2


def _noncanonical_input_color(grid) -> bool:
    return _analysis(grid).get("colors") not in (set(), {8})


def _first_object_is_unique(grid) -> bool:
    analysis = _analysis(grid)
    return bool(analysis.get("shapes")) and analysis["frequencies"][analysis["shapes"][0]] == 1


def _first_object_is_repeated(grid) -> bool:
    analysis = _analysis(grid)
    return bool(analysis.get("shapes")) and analysis["frequencies"][analysis["shapes"][0]] == 2


SEMANTIC_WITNESSES = {
    "singleton_and_repeated_branches": _both_branches,
    "same_area_classes_have_different_frequencies": _same_size_different_frequency,
    "d4_related_classes_have_different_frequencies": _d4_related_different_frequency,
    "two_distinct_repeated_shape_classes": _two_repeated_classes,
    "multiple_singleton_shape_classes": _multiple_unique_classes,
    "noncanonical_input_color": _noncanonical_input_color,
    "row_major_first_object_is_unique": _first_object_is_unique,
    "row_major_first_object_is_repeated": _first_object_is_repeated,
}

WITNESS_RIVALS = {
    "singleton_and_repeated_branches": [
        "all_objects_repeated_blue",
        "all_objects_unique_red",
    ],
    "same_area_classes_have_different_frequencies": ["frequency_by_area_not_shape"],
    "d4_related_classes_have_different_frequencies": [
        "frequency_by_rotation_or_reflection_orbit"
    ],
    "two_distinct_repeated_shape_classes": ["only_first_repeated_class_is_blue"],
    "multiple_singleton_shape_classes": ["first_object_red_everything_else_blue"],
    "noncanonical_input_color": ["apply_rule_only_when_input_color_is_8"],
    "row_major_first_object_is_unique": [
        "force_first_object_blue_then_apply_frequency_rule"
    ],
    "row_major_first_object_is_repeated": [
        "force_first_object_red_then_apply_frequency_rule"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require a complete three-profile demonstration window."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is missing input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"demo {index} is unlawful: {errors[0]}")
        elif rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} output disagrees with pinned audit mirror")
    query_errors = self_check(query["input"])
    if query_errors:
        reasons.append(f"query is unlawful: {query_errors[0]}")
    elif rule_mirror(query["input"]) != query["output"]:
        reasons.append("query output disagrees with pinned audit mirror")

    required = {
        "same-area discriminator": _same_size_different_frequency,
        "D4 discriminator": _d4_related_different_frequency,
        "two repeated classes": _two_repeated_classes,
        "non-8 palette": _noncanonical_input_color,
        "first-object singleton witness": _first_object_is_unique,
        "first-object repeated witness": _first_object_is_repeated,
    }
    for label, predicate in required.items():
        if not any(predicate(pair["input"]) for pair in demos if isinstance(pair, dict) and "input" in pair):
            reasons.append(f"demonstrations lack {label}")

    for name, rival in SEMANTIC_RIVALS.items():
        rejected = any(
            isinstance(pair, dict)
            and "input" in pair
            and "output" in pair
            and rival(pair["input"]) != pair["output"]
            for pair in demos
        )
        if not rejected and rival(query["input"]) != query["output"]:
            reasons.append(f"named rival remains viable on demonstrations: {name}")
    return reasons
