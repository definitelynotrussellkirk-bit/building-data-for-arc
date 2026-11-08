"""Constructive generator for ARC task ``87388eaff4ce``.

The unchanged Racket authority extracts each nonzero 4-connected object, crops
it to its bounding box, sorts by bounding-box height descending with color
ascending as the tie-break, and vertically packs the left-aligned crops with one
zero row between neighbors.

Every ordinary generated input contains four deliberate teaching witnesses:

* two objects have the same height, with row-major order opposite color order;
* the taller object has fewer cells than a shorter object;
* the taller object is narrower than a shorter object; and
* at least two distinct heights are present.

Those properties make height-only stable order, cell-count-first, width-first,
and ascending-height competitors disagree with the selected rule on every
ordinary draw instead of leaving output-relevant branches unobserved.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, NamedTuple

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "87388eaff4ce"
TASK_ID = GENERATOR_ID
RULE_HASH = "c701ff882260"
VERSION = "3.0.0"

SUMMARY = (
    "Extract each nonzero 4-connected object, crop it to its bounding box, "
    "sort by bounding-box height descending with color ascending as the "
    "tie-break, then vertically pack the left-aligned crops with one zero row "
    "between neighboring crops."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = (
    (9, 12, "height4_plus_height2_tie"),
    (10, 13, "height4_plus_height3_tie"),
)

INVARIANTS = [
    "background is 0 and the grid has a canonical 9x12 or 10x13 profile",
    "exactly three separated 4-connected objects use distinct nonzero colors",
    "ordinary draws contain a repeated-height pair that exposes color ascending",
    "ordinary draws invert height against both occupied area and bbox width",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "alternating canonical profile 9 or 10",
        "valid": "9..10",
    },
    "grid_w": {
        "type": "int",
        "default": "alternating canonical profile 12 or 13",
        "valid": "12..13",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []


class ObjectInfo(NamedTuple):
    color: int
    cells: tuple[tuple[int, int], ...]
    shape: tuple[tuple[int, int], ...]
    r0: int
    c0: int
    r1: int
    c1: int
    height: int
    width: int
    size: int


# These shapes cover every canonical object family.  Ordinary generation uses
# the first three for 9-row inputs and line4/cross5/t4 for 10-row inputs.
_BASE_SHAPES: dict[str, tuple[tuple[int, int], ...]] = {
    "line4": ((0, 0), (1, 0), (2, 0), (3, 0)),
    "u5": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2)),
    "square4": ((0, 0), (0, 1), (1, 0), (1, 1)),
    "t4": ((0, 0), (1, 0), (1, 1), (2, 0)),
    "cross5": ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    "line3": ((0, 0), (1, 0), (2, 0)),
    "rect6": ((0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)),
    "l4": ((0, 0), (1, 0), (2, 0), (2, 1)),
}

# Family multisets accepted by strict_canonical_like/self_check.  Four are the
# labeled canonical populations; the final one is the 10-row teaching profile.
_GENERATED_FAMILY_MULTISETS = {
    tuple(sorted(("line4", "u5", "square4"))),
    tuple(sorted(("line4", "cross5", "t4"))),
}
_ALLOWED_FAMILY_MULTISETS = _GENERATED_FAMILY_MULTISETS | {
    tuple(sorted(("t4", "cross5", "line3"))),
    tuple(sorted(("line4", "l4", "rect6"))),
    tuple(sorted(("line4", "t4", "square4"))),
}
# Canonical-only support signatures, ordered by ascending object color.  They
# prevent the strict checker from treating a destructive mutation into a
# different canonical shape multiset as an ordinary generated sample.
_CANONICAL_COLOR_RANK_FAMILIES = {
    ("u5", "line4", "square4"),
    ("t4", "cross5", "line3"),
    ("l4", "rect6", "line4"),
    ("line4", "t4", "square4"),
}


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None):
    """Return the deterministic default profile used by the production sampler."""
    del seed
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    # Medium is offset only to ensure difficulty is an observable schedule input;
    # every band still alternates through both exact canonical profiles.
    offset = 1 if difficulty == "medium" else 0
    return SCHEDULE_PROFILES[(sample_index + offset) % len(SCHEDULE_PROFILES)]


def _validate_call(
    seed: Any,
    sample_index: Any,
    difficulty: Any,
    overrides: dict[str, Any],
) -> None:
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axes: {unknown}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")


def _draw_axis(ctx, name: str, lo: int, hi: int, scheduled: int) -> int:
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _shape_size(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _normalize_shape(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    cells = tuple(shape)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _flip_shape(
    shape: tuple[tuple[int, int], ...], *, vertical: bool, horizontal: bool
) -> tuple[tuple[int, int], ...]:
    h, w = _shape_size(shape)
    transformed = [
        (h - 1 - r if vertical else r, w - 1 - c if horizontal else c)
        for r, c in shape
    ]
    return _normalize_shape(transformed)


def _shape_variants(
    shape: tuple[tuple[int, int], ...]
) -> set[tuple[tuple[int, int], ...]]:
    return {
        _flip_shape(shape, vertical=vertical, horizontal=horizontal)
        for vertical in (False, True)
        for horizontal in (False, True)
    }


_FAMILY_BY_SHAPE: dict[tuple[tuple[int, int], ...], str] = {}
for _family, _shape in _BASE_SHAPES.items():
    for _variant in _shape_variants(_shape):
        previous = _FAMILY_BY_SHAPE.setdefault(_variant, _family)
        if previous != _family:
            raise RuntimeError(
                f"shape-family collision between {previous!r} and {_family!r}"
            )


def _family_for_shape(shape: Iterable[tuple[int, int]]) -> str | None:
    return _FAMILY_BY_SHAPE.get(_normalize_shape(shape))


def _bbox_separated(
    a: tuple[int, int, int, int], b: tuple[int, int, int, int]
) -> bool:
    ar0, ac0, ar1, ac1 = a
    br0, bc0, br1, bc1 = b
    return (
        ar1 + 1 < br0
        or br1 + 1 < ar0
        or ac1 + 1 < bc0
        or bc1 + 1 < ac0
    )


def _place_shapes(
    h: int,
    w: int,
    shapes: tuple[tuple[tuple[int, int], ...], ...],
    rng,
) -> tuple[tuple[int, int], ...]:
    """Randomized exhaustive backtracking; no capped silent placement failure."""
    candidates_by_shape: list[list[tuple[int, int]]] = []
    sizes: list[tuple[int, int]] = []
    for shape in shapes:
        sh, sw = _shape_size(shape)
        sizes.append((sh, sw))
        candidates = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
        rng.shuffle(candidates)
        candidates_by_shape.append(candidates)

    positions: list[tuple[int, int]] = []
    boxes: list[tuple[int, int, int, int]] = []

    def search(index: int) -> bool:
        if index == len(shapes):
            return True
        sh, sw = sizes[index]
        for r0, c0 in candidates_by_shape[index]:
            box = (r0, c0, r0 + sh - 1, c0 + sw - 1)
            if not all(_bbox_separated(box, existing) for existing in boxes):
                continue
            positions.append((r0, c0))
            boxes.append(box)
            if search(index + 1):
                return True
            boxes.pop()
            positions.pop()
        return False

    if not search(0):
        raise ValueError(f"could not place {len(shapes)} separated objects in {h}x{w}")
    return tuple(positions)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(seed, sample_index, difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled_h, scheduled_w, _ = schedule_profile(seed, sample_index, difficulty)
    h = _draw_axis(ctx, "grid_h", 9, 10, scheduled_h)
    w = _draw_axis(ctx, "grid_w", 12, 13, scheduled_w)

    if h == 9:
        selected_names = ("line4", "u5", "square4")
    else:
        selected_names = ("line4", "cross5", "t4")

    reflection_rng = ctx.draw_rng("shape_reflections")
    shapes = tuple(
        _flip_shape(
            _BASE_SHAPES[name],
            vertical=bool(reflection_rng.randrange(2)),
            horizontal=bool(reflection_rng.randrange(2)),
        )
        for name in selected_names
    )
    positions = _place_shapes(h, w, shapes, ctx.draw_rng("object_positions"))

    low, middle, high = sorted(ctx.draw_rng("object_colors").sample(range(1, 10), 3))
    colors = [middle, 0, 0]
    # Shapes 1 and 2 have equal height.  Give the earlier bbox the larger color
    # so stable row-major tie handling conflicts with color-ascending handling.
    if positions[1] < positions[2]:
        colors[1], colors[2] = high, low
    else:
        colors[1], colors[2] = low, high

    grid = full_grid(h, w, 0)
    for color, shape, (r0, c0) in zip(colors, shapes, positions):
        for r, c in shape:
            grid[r0 + r][c0 + c] = color

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive generator produced an invalid grid: {errors}")
    missing = [name for name, predicate in SEMANTIC_WITNESSES.items() if not predicate(grid)]
    if missing:
        raise RuntimeError(f"constructive generator lost teaching witnesses: {missing}")
    if len(rule_mirror(grid)) <= len(grid):
        raise RuntimeError("constructive generator lost the canonical reshape relation")
    return grid


def _grid_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty list/tuple of rows"
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return "every row must be a list/tuple"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be nonempty and rectangular"
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return "grid cells must be integer colors 0..9 (not bool)"
    return None


def _object_infos(grid) -> list[ObjectInfo]:
    """Measure same-color nonzero 4-connected components without mutation."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    infos: list[ObjectInfo] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            cells = [(r, c)]
            seen.add((r, c))
            for rr, cc in cells:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        cells.append((nr, nc))
            ordered_cells = tuple(sorted(cells))
            rows = [rr for rr, _ in ordered_cells]
            cols = [cc for _, cc in ordered_cells]
            r0, r1 = min(rows), max(rows)
            c0, c1 = min(cols), max(cols)
            shape = tuple(sorted((rr - r0, cc - c0) for rr, cc in ordered_cells))
            infos.append(
                ObjectInfo(
                    color=color,
                    cells=ordered_cells,
                    shape=shape,
                    r0=r0,
                    c0=c0,
                    r1=r1,
                    c1=c1,
                    height=r1 - r0 + 1,
                    width=c1 - c0 + 1,
                    size=len(ordered_cells),
                )
            )
    return infos


def _pack(grid, key: Callable[[ObjectInfo], tuple]) -> list[list[int]]:
    infos = sorted(_object_infos(grid), key=key)
    if not infos:
        return []
    out_h = sum(info.height for info in infos) + len(infos) - 1
    out_w = max(info.width for info in infos)
    out = full_grid(out_h, out_w, 0)
    top = 0
    for info in infos:
        for r, c in info.shape:
            out[top + r][c] = info.color
        top += info.height + 1
    return out


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror checked against the Racket label authority."""
    return _pack(grid, lambda obj: (-obj.height, obj.color))


def _height_only_row_major(grid) -> list[list[int]]:
    """RIVAL: sort by height but preserve row-major order on ties."""
    return _pack(grid, lambda obj: (-obj.height, obj.r0, obj.c0))


def _cell_count_first(grid) -> list[list[int]]:
    """RIVAL: sort by occupied area before height."""
    return _pack(grid, lambda obj: (-obj.size, -obj.height, obj.color))


def _width_first(grid) -> list[list[int]]:
    """RIVAL: sort by bbox width before height."""
    return _pack(grid, lambda obj: (-obj.width, -obj.height, obj.color))


def _height_ascending(grid) -> list[list[int]]:
    """RIVAL: use the correct key in the wrong direction."""
    return _pack(grid, lambda obj: (obj.height, obj.color))


def _has_color_tiebreak_witness(grid) -> bool:
    try:
        infos = _object_infos(grid)
    except Exception:
        return False
    return any(
        left.height == right.height
        and (left.r0, left.c0) < (right.r0, right.c0)
        and left.color > right.color
        for left in infos
        for right in infos
        if left is not right
    )


def _has_height_cell_count_inversion(grid) -> bool:
    try:
        infos = _object_infos(grid)
    except Exception:
        return False
    return any(
        taller.height > shorter.height and taller.size < shorter.size
        for taller in infos
        for shorter in infos
    )


def _has_height_width_inversion(grid) -> bool:
    try:
        infos = _object_infos(grid)
    except Exception:
        return False
    return any(
        taller.height > shorter.height and taller.width < shorter.width
        for taller in infos
        for shorter in infos
    )


def _has_descending_height_witness(grid) -> bool:
    try:
        return len({info.height for info in _object_infos(grid)}) >= 2
    except Exception:
        return False


def observe_overrides(grid) -> dict[str, int]:
    return {"grid_h": len(grid), "grid_w": len(grid[0])}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    first_error = _grid_error(grid)
    if first_error:
        return [first_error]

    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not 9 <= h <= 10:
        errors.append(f"grid height {h} outside 9..10")
    if not 12 <= w <= 13:
        errors.append(f"grid width {w} outside 12..13")

    infos = _object_infos(grid)
    if len(infos) != 3:
        errors.append(f"expected exactly 3 nonzero objects, got {len(infos)}")
        return errors

    colors = [info.color for info in infos]
    if len(colors) != len(set(colors)):
        errors.append("objects must use distinct colors")

    for index, left in enumerate(infos):
        left_box = (left.r0, left.c0, left.r1, left.c1)
        for right in infos[index + 1 :]:
            right_box = (right.r0, right.c0, right.r1, right.c1)
            if not _bbox_separated(left_box, right_box):
                errors.append(
                    "object bounding boxes need at least one background row or column"
                )
                return errors

    families: list[str] = []
    for info in infos:
        family = _family_for_shape(info.shape)
        if family is None:
            errors.append(
                f"object color {info.color} has an unsupported normalized shape"
            )
        else:
            families.append(family)
    if len(families) == len(infos):
        signature = tuple(sorted(families))
        if signature not in _ALLOWED_FAMILY_MULTISETS:
            errors.append(f"unsupported three-object shape-family signature {signature}")
        else:
            family_by_shape = {
                info.shape: _family_for_shape(info.shape) for info in infos
            }
            ranked_families = tuple(
                family_by_shape[info.shape] for info in sorted(infos, key=lambda item: item.color)
            )
            generated_like = (
                signature in _GENERATED_FAMILY_MULTISETS
                and _has_color_tiebreak_witness(grid)
                and _has_height_cell_count_inversion(grid)
                and _has_height_width_inversion(grid)
                and _has_descending_height_witness(grid)
            )
            canonical_like = ranked_families in _CANONICAL_COLOR_RANK_FAMILIES
            if not generated_like and not canonical_like:
                errors.append(
                    "shape families do not form an ordinary teaching profile or a "
                    "labeled canonical support profile"
                )
    return errors


def strict_canonical_like(grid):
    """Accept the selected generator manifold and all labeled canonical inputs."""
    return self_check(grid)


SEMANTIC_WITNESSES = {
    "color_tiebreak": _has_color_tiebreak_witness,
    "height_over_cell_count": _has_height_cell_count_inversion,
    "height_over_width": _has_height_width_inversion,
    "descending_height": _has_descending_height_witness,
}
SEMANTIC_RIVALS = {
    "height_only_row_major": _height_only_row_major,
    "cell_count_first": _cell_count_first,
    "width_first": _width_first,
    "height_ascending": _height_ascending,
}
WITNESS_RIVALS = {
    "color_tiebreak": ["height_only_row_major"],
    "height_over_cell_count": ["cell_count_first"],
    "height_over_width": ["width_first"],
    "descending_height": ["height_ascending"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Report any declared competitor that survives demos but changes query."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = rival(query["input"]) != query["output"]
        except Exception as exc:  # retain malformed-lesson diagnostics
            reasons.append(f"competitor {name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"competitor {name} fits every demonstration but changes the query"
            )
    return reasons
