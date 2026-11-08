"""Constructive input generator for ARC task ``a784ff872856``.

The unchanged Racket authority extracts each nonzero 4-connected object,
crops it to its bounding box, sorts by ``(-bbox_width, -bbox_height, color)``,
and vertically packs the normalized crops with one zero row between them.

Every ordinary generated input contains a deliberate width-vs-cell-count
inversion plus a secondary-key lesson: equal-width objects with different
heights, equal-dimension objects with different colors, or both.  Together the
four-step schedule teaches every key in the pinned ordering.
"""
from __future__ import annotations

from typing import Any, Callable, Iterable, NamedTuple

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "a784ff872856"
TASK_ID = GENERATOR_ID
RULE_HASH = "7991026f57da"
VERSION = "2.1.0"

SUMMARY = (
    "Extract each nonzero 4-connected object, crop it to its bounding box, "
    "sort by bounding-box width descending, then height descending, then "
    "color ascending, and vertically pack the left-aligned crops with one "
    "zero row between neighbors."
)

EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 4
_SCHEDULE_ANCHORS = (
    (7, 10, 3),
    (7, 11, 3),
    (8, 12, 3),
    "difficulty_broad",
)
SCHEDULE_PROFILES = (
    (7, 10, 3),
    (7, 11, 3),
    (8, 12, 3),
    (9, 12, 3),
    (10, 13, 4),
    (12, 15, 4),
)

INVARIANTS = [
    "background is 0 and every object has a distinct nonzero color",
    "3-4 mutually separated 4-connected objects teach a secondary sort key",
    "every ordinary draw contains a width-vs-cell-count inversion",
    "every four-step lesson window teaches height and color tie breakers",
    "canonical-sized anchors recur in every difficulty band",
]

SECONDARY_KEY_SCHEDULE = (
    "height_tie",
    "color_tie",
    "height_tie",
    "color_tie",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "4-step schedule: 7, 7, 8, then difficulty-broad",
        "valid": "7..14",
    },
    "grid_w": {
        "type": "int",
        "default": "4-step schedule: 10, 11, 12, then difficulty-broad",
        "valid": "9..16",
    },
    "n": {
        "type": "int",
        "default": "4-step schedule: 3, 3, 3, then difficulty-broad",
        "valid": "3..4",
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


# The width-4 sparse crop has five cells while the width-2 dense crop has six,
# so cell-count-first always disagrees with width-first.  Reusing the wide crop
# creates a color tie; pairing the two width-2 crops creates a height tie.
_WIDE_SPARSE = ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1))  # 2x4, size 5
_NARROW_DENSE = ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1))  # 3x2, size 6
_NARROW_SHORT = ((0, 0), (0, 1), (1, 0))  # 2x2, size 3


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None):
    """Return the declared deterministic four-step lesson profile."""
    del seed
    role = int(sample_index) % LESSON_SCHEDULE_PERIOD
    profile = _SCHEDULE_ANCHORS[role]
    if profile != "difficulty_broad":
        return profile
    broad = {
        None: (10, 13, 4),
        "easy": (9, 12, 3),
        "medium": (10, 13, 4),
        "hard": (12, 15, 4),
    }
    if difficulty not in broad:
        raise ValueError(f"unknown difficulty {difficulty!r}")
    return broad[difficulty]


def _validate_call(seed: Any, sample_index: Any, difficulty: Any, overrides: dict[str, Any]) -> None:
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
    """Honor the full override domain while keeping exact schedule anchors."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return ctx.draw_int_strict(name, scheduled, scheduled)


def _shape_size(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    cells = tuple(shape)
    return max(r for r, _ in cells) + 1, max(c for _, c in cells) + 1


def _flip_shape(
    shape: tuple[tuple[int, int], ...], *, vertical: bool, horizontal: bool
) -> tuple[tuple[int, int], ...]:
    h, w = _shape_size(shape)
    transformed = []
    for r, c in shape:
        transformed.append((h - 1 - r if vertical else r, w - 1 - c if horizontal else c))
    return tuple(sorted(transformed))


def _bbox_separated(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
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
    """Exhaustive randomized backtracking; every advertised boundary is feasible."""
    candidate_lists: list[list[tuple[int, int]]] = []
    sizes: list[tuple[int, int]] = []
    for shape in shapes:
        sh, sw = _shape_size(shape)
        sizes.append((sh, sw))
        candidates = [(r, c) for r in range(h - sh + 1) for c in range(w - sw + 1)]
        rng.shuffle(candidates)
        candidate_lists.append(candidates)

    chosen: list[tuple[int, int]] = []
    boxes: list[tuple[int, int, int, int]] = []

    def search(index: int) -> bool:
        if index == len(shapes):
            return True
        sh, sw = sizes[index]
        for r0, c0 in candidate_lists[index]:
            box = (r0, c0, r0 + sh - 1, c0 + sw - 1)
            if not all(_bbox_separated(box, old) for old in boxes):
                continue
            chosen.append((r0, c0))
            boxes.append(box)
            if search(index + 1):
                return True
            boxes.pop()
            chosen.pop()
        return False

    if not search(0):
        raise ValueError(f"could not place {len(shapes)} separated objects in {h}x{w}")
    return tuple(chosen)


def secondary_key_mode(sample_index: int, n: int) -> str:
    """Return the deterministic secondary-key lesson for this draw."""
    if n == 4:
        return "combined"
    return SECONDARY_KEY_SCHEDULE[int(sample_index) % LESSON_SCHEDULE_PERIOD]


def _lesson_shapes(sample_index: int, n: int):
    mode = secondary_key_mode(sample_index, n)
    if mode == "height_tie":
        return (_WIDE_SPARSE, _NARROW_DENSE, _NARROW_SHORT)
    if mode == "color_tie":
        return (_WIDE_SPARSE, _WIDE_SPARSE, _NARROW_DENSE)
    if mode == "combined":
        return (_WIDE_SPARSE, _WIDE_SPARSE, _NARROW_DENSE, _NARROW_SHORT)
    raise AssertionError(f"unknown secondary-key mode {mode!r}")


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
    scheduled_h, scheduled_w, scheduled_n = schedule_profile(seed, sample_index, difficulty)
    h = _draw_axis(ctx, "grid_h", 7, 14, scheduled_h)
    w = _draw_axis(ctx, "grid_w", 9, 16, scheduled_w)
    n = _draw_axis(ctx, "n", 3, 4, scheduled_n)

    shape_rng = ctx.draw_rng("shape_reflections")
    selected = _lesson_shapes(sample_index, n)
    shapes = tuple(
        _flip_shape(
            shape,
            vertical=bool(shape_rng.randrange(2)),
            horizontal=bool(shape_rng.randrange(2)),
        )
        for shape in selected
    )
    positions = _place_shapes(h, w, shapes, ctx.draw_rng("object_positions"))
    colors = ctx.draw_rng("object_colors").sample(list(range(1, 10)), n)

    grid = full_grid(h, w, 0)
    for color, shape, (r0, c0) in zip(colors, shapes, positions):
        for r, c in shape:
            grid[r0 + r][c0 + c] = color
    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError(f"constructive generator produced an invalid grid: {errors}")
    required_witnesses = ["width_over_cell_count"]
    mode = secondary_key_mode(sample_index, n)
    if mode in ("height_tie", "combined"):
        required_witnesses.append("height_descending_on_width_tie")
    if mode in ("color_tie", "combined"):
        required_witnesses.append("color_ascending_on_dimension_tie")
    missing = [
        name for name in required_witnesses if not SEMANTIC_WITNESSES[name](grid)
    ]
    if missing:
        raise RuntimeError(f"constructive generator lost semantic witnesses: {missing}")
    return grid


def _grid_error(grid: Any) -> str | None:
    if not isinstance(grid, (list, tuple)) or not grid:
        return "grid must be a nonempty list/tuple of rows"
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return "every row must be a list/tuple"
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return "grid must be nonempty and rectangular"
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        return "grid cells must be integer colors 0..9 (not bool)"
    return None


def _object_infos(grid) -> list[ObjectInfo]:
    """Measure same-color 4-connected nonzero components without mutating input."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    infos: list[ObjectInfo] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            queue = [(r, c)]
            seen.add((r, c))
            for rr, cc in queue:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            cells = tuple(sorted(queue))
            rows = [rr for rr, _ in cells]
            cols = [cc for _, cc in cells]
            r0, r1 = min(rows), max(rows)
            c0, c1 = min(cols), max(cols)
            shape = tuple(sorted((rr - r0, cc - c0) for rr, cc in cells))
            infos.append(
                ObjectInfo(
                    color=color,
                    cells=cells,
                    shape=shape,
                    r0=r0,
                    c0=c0,
                    r1=r1,
                    c1=c1,
                    height=r1 - r0 + 1,
                    width=c1 - c0 + 1,
                    size=len(cells),
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
    """Independent Python mirror, regression-checked against the Racket authority."""
    return _pack(grid, lambda obj: (-obj.width, -obj.height, obj.color))


def _cell_count_first(grid) -> list[list[int]]:
    """RIVAL: sort by occupied cell count before bbox width."""
    return _pack(
        grid,
        lambda obj: (-obj.size, -obj.width, -obj.height, obj.color),
    )


def _height_ascending_on_width_ties(grid) -> list[list[int]]:
    """RIVAL: use the correct width key but put shorter tied objects first."""
    return _pack(grid, lambda obj: (-obj.width, obj.height, obj.color))


def _color_descending_on_dimension_ties(grid) -> list[list[int]]:
    """RIVAL: use the correct dimensions but reverse the final color key."""
    return _pack(grid, lambda obj: (-obj.width, -obj.height, -obj.color))


def _has_width_cell_count_inversion(grid) -> bool:
    try:
        infos = _object_infos(grid)
    except Exception:
        return False
    return any(
        wider.width > narrower.width and wider.size < narrower.size
        for wider in infos
        for narrower in infos
    )


def _has_height_tie(grid) -> bool:
    """True when the height key decides between equal-width objects."""
    try:
        infos = _object_infos(grid)
    except Exception:
        return False
    return any(
        left.width == right.width and left.height != right.height
        for index, left in enumerate(infos)
        for right in infos[index + 1 :]
    )


def _has_color_tie(grid) -> bool:
    """True when the color key decides between equal-dimension objects."""
    try:
        infos = _object_infos(grid)
    except Exception:
        return False
    return any(
        left.width == right.width
        and left.height == right.height
        and left.color != right.color
        for index, left in enumerate(infos)
        for right in infos[index + 1 :]
    )


def observe_overrides(grid) -> dict[str, int]:
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n": len(_object_infos(grid)),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    first_error = _grid_error(grid)
    if first_error:
        return [first_error]
    h, w = len(grid), len(grid[0])
    errors: list[str] = []
    if not 7 <= h <= 14:
        errors.append(f"grid height {h} outside 7..14")
    if not 9 <= w <= 16:
        errors.append(f"grid width {w} outside 9..16")
    infos = _object_infos(grid)
    if not 3 <= len(infos) <= 4:
        errors.append(f"expected 3-4 nonzero objects, got {len(infos)}")
    colors = [info.color for info in infos]
    if len(colors) != len(set(colors)):
        errors.append("objects must use distinct colors")
    for index, left in enumerate(infos):
        a = (left.r0, left.c0, left.r1, left.c1)
        for right in infos[index + 1 :]:
            b = (right.r0, right.c0, right.r1, right.c1)
            if not _bbox_separated(a, b):
                errors.append("object bounding boxes need at least one background row or column")
                return errors
    return errors


def strict_canonical_like(grid):
    """Lawful inputs in the declared generator manifold, including singletons."""
    return self_check(grid)


SEMANTIC_WITNESSES = {
    "width_over_cell_count": _has_width_cell_count_inversion,
    "height_descending_on_width_tie": _has_height_tie,
    "color_ascending_on_dimension_tie": _has_color_tie,
}
SEMANTIC_RIVALS = {
    "cell_count_first": _cell_count_first,
    "height_ascending_on_width_ties": _height_ascending_on_width_ties,
    "color_descending_on_dimension_ties": _color_descending_on_dimension_ties,
}
WITNESS_RIVALS = {
    "width_over_cell_count": ["cell_count_first"],
    "height_descending_on_width_tie": ["height_ascending_on_width_ties"],
    "color_ascending_on_dimension_tie": ["color_descending_on_dimension_ties"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
