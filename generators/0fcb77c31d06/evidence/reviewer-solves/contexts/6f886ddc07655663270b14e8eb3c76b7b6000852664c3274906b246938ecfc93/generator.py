"""Generator for 16b:m110: select by legend frequency, crop, and scale 2x.

The first row is a color-count legend.  Its unique most frequent nonzero color
is the key.  In the body, select the largest 4-connected object of that color,
crop its bounding box from the input, and upscale the crop by a factor of two.

Generated teaching inputs deliberately defeat the strongest shortcuts left by
the canonical examples: the key is not the leftmost legend color, there are two
key-color body objects, the earlier one is smaller, and a non-key object is
larger than the selected key object.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "0fcb77c31d06"
TASK_ID = GENERATOR_ID
RULE_HASH = "c515fc7de0cf"
VERSION = "3.0.0"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Row 0 is a sparse legend with three or four nonzero colors and one unique "
    "frequency winner. Rows 2+ contain two separated objects in that key color "
    "plus differently colored distractors. Select the largest key-color object, "
    "crop its bounding box from the input, and upscale the crop 2x. Generated "
    "examples make the smaller key object occur earlier and make a non-key "
    "object larger, so both legend counting and largest-within-key are required."
)

INVARIANTS = [
    "background is 0 and row 1 is a blank separator",
    "row 0 has three or four colors with a unique strict frequency winner",
    "the leftmost legend color is not the winner",
    "the body has exactly two separated key-color components with a unique largest",
    "the top-left key component is the smaller one",
    "a non-key component is larger than the selected key component",
    "the selected key crop contains both key cells and background before 2x scaling",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted choice from 9|10|11|12",
        "valid": "9|10|11|12",
        "doc": "Exact observable input height; every value is supported in every band.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted choice from 10|11|12|13|14",
        "valid": "10|11|12|13|14",
        "doc": "Exact observable input width; every value is supported in every band.",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_HEIGHTS = (9, 10, 11, 12)
_WIDTHS = (10, 11, 12, 13, 14)
_COLORS = tuple(range(1, 10))

# Compact nonrectangular polyominoes.  Every selected-object template contains
# at least one zero in its bounding box, so the crop operation is visible.
_BASE_SHAPES: dict[int, tuple[tuple[int, int], ...]] = {
    3: ((0, 0), (1, 0), (1, 1)),
    4: ((0, 0), (0, 1), (0, 2), (1, 1)),
    5: ((0, 0), (0, 1), (1, 0), (1, 1), (2, 0)),
    6: ((0, 0), (0, 1), (1, 0), (1, 1), (1, 2), (2, 2)),
    7: ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 1), (2, 2)),
}


def _normalize(shape):
    rows = [r for r, _ in shape]
    cols = [c for _, c in shape]
    min_r, min_c = min(rows), min(cols)
    return tuple(sorted((r - min_r, c - min_c) for r, c in shape))


def _oriented_shape(size: int, rng):
    """Return a deterministic random rotation/reflection of a base shape."""
    shape = list(_BASE_SHAPES[size])
    if rng.randrange(2):
        shape = [(r, -c) for r, c in shape]
    for _ in range(rng.randrange(4)):
        shape = [(c, -r) for r, c in shape]
    return _normalize(shape)


def _shape_bbox(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _component_sort_key(cells):
    r0, c0, _r1, _c1 = _bbox(cells)
    return -len(cells), r0, c0


def _components(grid, *, body_only: bool = True):
    """Return same-color 4-connected components as ``(color, cells)``."""
    h, w = len(grid), len(grid[0])
    start_row = 1 if body_only else 0
    seen: set[tuple[int, int]] = set()
    result: list[tuple[int, list[tuple[int, int]]]] = []
    for sr in range(start_row, h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells: list[tuple[int, int]] = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in _CARDINAL:
                    nr, nc = r + dr, c + dc
                    if not (start_row <= nr < h and 0 <= nc < w):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    stack.append((nr, nc))
            result.append((color, sorted(cells)))
    return result


def _legend_info(grid):
    entries = [(c, value) for c, value in enumerate(grid[0]) if value != 0]
    if not entries:
        return {}, None, None
    counts = Counter(value for _c, value in entries)
    key = min(counts, key=lambda color: (-counts[color], color))
    return dict(sorted(counts.items())), key, entries[0][1]


def _analysis(grid):
    """Structural analysis shared by checks, the oracle, and rival rules."""
    legend_counts, key, leftmost = _legend_info(grid)
    body_components = _components(grid)
    key_components = [cells for color, cells in body_components if color == key]
    selected = min(key_components, key=_component_sort_key) if key_components else None
    top_left = min(key_components, key=lambda cells: (_bbox(cells)[0], _bbox(cells)[1], -len(cells))) if key_components else None
    return {
        "legend_counts": legend_counts,
        "key": key,
        "leftmost_legend_color": leftmost,
        "body_components": body_components,
        "key_components": key_components,
        "selected_key_component": selected,
        "top_left_key_component": top_left,
    }


def _crop_and_upscale(grid, cells):
    if not cells:
        raise ValueError("cannot crop an empty component")
    r0, c0, r1, c1 = _bbox(cells)
    crop = [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
    output: list[list[int]] = []
    for row in crop:
        doubled = [value for value in row for _ in range(2)]
        output.append(doubled[:])
        output.append(doubled[:])
    return output


def _selected_crop_has_background(grid) -> bool:
    info = _analysis(grid)
    cells = info["selected_key_component"]
    if not cells:
        return False
    r0, c0, r1, c1 = _bbox(cells)
    return any(grid[r][c] == 0 for r in range(r0, r1 + 1) for c in range(c0, c1 + 1))


def oracle_output(grid):
    """Python mirror for tests and diagnostics; Racket remains authoritative."""
    info = _analysis(grid)
    if info["key"] is None:
        raise ValueError("legend has no nonzero color")
    if info["selected_key_component"] is None:
        raise ValueError("body has no component in the legend key color")
    return _crop_and_upscale(grid, info["selected_key_component"])


def _components_of_color(grid, color):
    """Compatibility helper retained for existing review tooling."""
    return [cells for component_color, cells in _components(grid) if component_color == color]


def _rival_leftmost_legend_then_top_left_key(grid):
    _counts, _key, leftmost = _legend_info(grid)
    candidates = [cells for color, cells in _components(grid) if color == leftmost]
    if not candidates:
        raise ValueError("leftmost legend color has no body component")
    chosen = min(candidates, key=lambda cells: (_bbox(cells)[0], _bbox(cells)[1], -len(cells)))
    return _crop_and_upscale(grid, chosen)


def _rival_frequency_then_top_left_key(grid):
    info = _analysis(grid)
    if not info["key_components"]:
        raise ValueError("key color has no body component")
    return _crop_and_upscale(grid, info["top_left_key_component"])


def _rival_frequency_then_all_key_bbox(grid):
    info = _analysis(grid)
    all_cells = [cell for component in info["key_components"] for cell in component]
    if not all_cells:
        raise ValueError("key color has no body component")
    return _crop_and_upscale(grid, all_cells)


def _rival_largest_body_object(grid):
    components = _components(grid)
    if not components:
        raise ValueError("body has no object")
    _color, cells = min(components, key=lambda item: _component_sort_key(item[1]))
    return _crop_and_upscale(grid, cells)


SEMANTIC_RIVALS = {
    "leftmost_legend_then_top_left_key": _rival_leftmost_legend_then_top_left_key,
    "frequency_then_top_left_key": _rival_frequency_then_top_left_key,
    "frequency_then_all_key_bbox": _rival_frequency_then_all_key_bbox,
    "largest_body_object_ignoring_legend": _rival_largest_body_object,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# Every labeled canonical pair puts the key in the leftmost legend cell and has
# only one key-color body component, so these shortcuts fit all public labels.
CANONICAL_SHORTCUTS = {
    "leftmost_legend_then_top_left_key": _rival_leftmost_legend_then_top_left_key,
    "frequency_then_top_left_key": _rival_frequency_then_top_left_key,
    "frequency_then_all_key_bbox": _rival_frequency_then_all_key_bbox,
}


def _witness_not_leftmost(grid):
    return oracle_output(grid) != _rival_leftmost_legend_then_top_left_key(grid)


def _witness_largest_key_component(grid):
    return oracle_output(grid) != _rival_frequency_then_top_left_key(grid)


def _witness_component_not_all_key_bbox(grid):
    return oracle_output(grid) != _rival_frequency_then_all_key_bbox(grid)


def _witness_legend_filters_larger_distractor(grid):
    return oracle_output(grid) != _rival_largest_body_object(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "frequency_not_leftmost_position": _witness_not_leftmost,
    "largest_key_not_top_left_key": _witness_largest_key_component,
    "largest_component_not_all_key_pixels": _witness_component_not_all_key_bbox,
    "legend_filters_larger_distractor": _witness_legend_filters_larger_distractor,
}
WITNESS_RIVALS = {
    "frequency_not_leftmost_position": ["leftmost_legend_then_top_left_key"],
    "largest_key_not_top_left_key": ["frequency_then_top_left_key"],
    "largest_component_not_all_key_pixels": ["frequency_then_all_key_bbox"],
    "legend_filters_larger_distractor": ["largest_body_object_ignoring_legend"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any named rival that survives demos but changes the query."""
    official_query = oracle_output(query["input"])
    errors = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos):
            if rival(query["input"]) != official_query:
                errors.append(f"demos do not rule out rival operation {name}")
    return errors


def _dimension_options(values, difficulty, *, axis):
    """Keep the full override domain while biasing ordinary draws by band."""
    if axis == "grid_h":
        favored = {
            "easy": (9, 9, 9, 10, 10),
            "medium": (9, 10, 10, 11, 11),
            "hard": (9, 10, 10, 11, 11, 12, 12),
            None: (9, 10, 10, 11),
        }[difficulty]
    else:
        favored = {
            "easy": (10, 10, 11, 11, 12),
            "medium": (10, 11, 11, 12, 12, 13),
            "hard": (10, 11, 12, 12, 13, 14, 14),
            None: (10, 11, 12, 12, 13),
        }[difficulty]
    return tuple(values) + favored * 8


def _can_place(grid, shape, r0, c0):
    h, w = len(grid), len(grid[0])
    sh, sw = _shape_bbox(shape)
    if r0 < 2 or c0 < 0 or r0 + sh > h or c0 + sw > w:
        return False
    # Keep component bounding boxes at least one cell apart.  This makes the
    # object decomposition unambiguous and prevents another object entering the
    # selected crop's holes.
    for r in range(max(1, r0 - 1), min(h, r0 + sh + 1)):
        for c in range(max(0, c0 - 1), min(w, c0 + sw + 1)):
            if grid[r][c] != 0:
                return False
    return True


def _candidate_positions(grid, shape, *, before=None, after=None, reverse=False):
    h, w = len(grid), len(grid[0])
    sh, sw = _shape_bbox(shape)
    positions = []
    for r0 in range(2, h - sh + 1):
        for c0 in range(0, w - sw + 1):
            pos = (r0, c0)
            if before is not None and not (pos < before):
                continue
            if after is not None and not (pos > after):
                continue
            if _can_place(grid, shape, r0, c0):
                positions.append(pos)
    positions.sort(reverse=reverse)
    return positions


def _paint(grid, shape, pos, color):
    r0, c0 = pos
    for dr, dc in shape:
        grid[r0 + dr][c0 + dc] = color


def _erase(grid, shape, pos):
    r0, c0 = pos
    for dr, dc in shape:
        grid[r0 + dr][c0 + dc] = 0


def _place_roles(grid, roles, rng):
    """Backtracking placement for the four teaching objects."""
    placed: dict[str, tuple[int, int]] = {}
    nodes = 0

    def search(index):
        nonlocal nodes
        if index == len(roles):
            return True
        nodes += 1
        if nodes > 25_000:
            return False
        name, shape, color = roles[index]
        before = placed.get("selected_key") if name == "small_key" else None
        # Put the selected key later in reading order, leaving room for the
        # deliberately misleading smaller key component before it.
        after = (2, 0) if name == "selected_key" else None
        reverse = name in {"selected_key", "large_distractor"}
        positions = _candidate_positions(
            grid,
            shape,
            before=before,
            after=after,
            reverse=reverse,
        )
        # Randomize within broad position preference without losing deterministic
        # backtracking completeness.
        if len(positions) > 1:
            block = max(1, len(positions) // 3)
            head, tail = positions[:block], positions[block:]
            rng.shuffle(head)
            rng.shuffle(tail)
            positions = head + tail
        for pos in positions:
            _paint(grid, shape, pos, color)
            placed[name] = pos
            if search(index + 1):
                return True
            placed.pop(name, None)
            _erase(grid, shape, pos)
        return False

    if search(0):
        return placed
    return None


def _legend_palette(rng, sample_index):
    n_colors = 3 if sample_index % 2 == 0 else 4
    palette = sorted(rng.sample(_COLORS, n_colors))
    key_index = 1 if n_colors == 3 else 1 + ((sample_index // 2) % 2)
    key = palette[key_index]
    others = [color for color in palette if color != key]
    return palette, key, others


def _put_legend(grid, rng, key, others):
    w = len(grid[0])
    leftmost = others[0]
    if len(others) == 2:
        values = [key, key, key, others[0], others[1]]
        # One extra non-key count creates the canonical 3/2/1 profile.
        values.append(others[0])
    else:
        values = [key, key, key, key, *others]
    values.remove(leftmost)
    rng.shuffle(values)
    columns = rng.sample(range(1, w), len(values))
    grid[0][0] = leftmost
    for col, color in zip(columns, values):
        grid[0][col] = color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative integer")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axis: {sorted(unknown)!r}")
    for name, value in overrides.items():
        if value is not None and type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_choice("grid_h", _dimension_options(_HEIGHTS, difficulty, axis="grid_h"))
    w = ctx.draw_choice("grid_w", _dimension_options(_WIDTHS, difficulty, axis="grid_w"))
    palette_rng = ctx.draw_rng("palette")
    legend_rng = ctx.draw_rng("legend")
    shape_rng = ctx.draw_rng("shapes")
    layout_rng = ctx.draw_rng("layout")

    _palette, key, others = _legend_palette(palette_rng, sample_index)
    big_size = {"easy": 4, "medium": 5, "hard": 6}.get(
        difficulty,
        4 + (sample_index % 3),
    )
    small_size = 3
    large_distractor_size = big_size + 1
    other_distractor_size = 3 + (sample_index % 2)

    for _attempt in range(80):
        grid = full_grid(h, w, 0)
        _put_legend(grid, legend_rng, key, others)
        selected_shape = _oriented_shape(big_size, shape_rng)
        large_distractor_shape = _oriented_shape(large_distractor_size, shape_rng)
        small_shape = _oriented_shape(small_size, shape_rng)
        other_shape = _oriented_shape(other_distractor_size, shape_rng)

        roles = [
            ("selected_key", selected_shape, key),
            ("large_distractor", large_distractor_shape, others[0]),
            ("small_key", small_shape, key),
            ("other_distractor", other_shape, others[1]),
        ]
        if _place_roles(grid, roles, layout_rng) is None:
            continue
        if teaching_check(grid):
            continue
        return grid
    raise ValueError(
        f"could not place teaching objects on {h}x{w} grid after bounded search"
    )


def observe_overrides(grid) -> dict[str, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("cannot observe axes from an empty grid")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("cannot observe axes from a ragged grid")
    return {"grid_h": len(grid), "grid_w": width}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the task-linked authority grammar, including canonical inputs."""
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["grid cells must be integer ARC colors 0..9"]

    errors: list[str] = []
    if len(grid) < 3:
        errors.append("grid must have a legend row, separator row, and body")
        return errors
    if any(grid[1]):
        errors.append("row 1 should be a blank separator")

    info = _analysis(grid)
    counts = info["legend_counts"]
    if not counts:
        errors.append("row 0 legend must contain nonzero colors")
        return errors
    if len(counts) < 2:
        errors.append(f"legend needs at least two colors, got {counts}")
    key = info["key"]
    max_count = max(counts.values())
    if sum(count == max_count for count in counts.values()) != 1:
        errors.append(f"legend needs a unique most-frequent color, got {counts}")

    body_colors = {color for color, _cells in info["body_components"]}
    unknown_body = body_colors - set(counts)
    if unknown_body:
        errors.append(f"body colors must occur in legend, got extra {sorted(unknown_body)}")
    if not info["key_components"]:
        errors.append(f"body has no component in key color {key}")
        return errors
    ordered = sorted(info["key_components"], key=_component_sort_key)
    if len(ordered) > 1 and len(ordered[0]) == len(ordered[1]):
        errors.append("largest key-color component must be unique")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Validate the shared canonical/generated task manifold.

    This predicate must accept the imported canonical examples as well as
    generated examples.  Anti-shortcut properties belong in ``teaching_check``:
    the public examples legitimately have the key at the left edge and only one
    key-color object.
    """
    errors = list(self_check(grid))
    if errors:
        return errors
    info = _analysis(grid)
    if len(info["legend_counts"]) not in (3, 4):
        errors.append(
            f"canonical-like legend should use three or four colors, got {len(info['legend_counts'])}"
        )
    if not _selected_crop_has_background(grid):
        errors.append("selected key crop must contain background as well as key cells")
    if len({color for color, _cells in info["body_components"] if color != info["key"]}) < 2:
        errors.append("body needs at least two non-key distractor colors")
    return errors


def teaching_check(grid) -> list[str]:
    """Require the stronger anti-shortcut contract for generated lessons only."""
    errors = list(strict_canonical_like(grid))
    if errors:
        return errors
    info = _analysis(grid)
    if info["leftmost_legend_color"] == info["key"]:
        errors.append("leftmost legend color must not be the frequency winner")
    if len(info["key_components"]) != 2:
        errors.append(
            f"teaching input needs exactly two key-color components, got {len(info['key_components'])}"
        )
    else:
        sizes = sorted((len(cells) for cells in info["key_components"]), reverse=True)
        if sizes[0] <= sizes[1]:
            errors.append("two key-color components need a unique largest")
        if info["top_left_key_component"] == info["selected_key_component"]:
            errors.append("top-left key component must be the smaller distractor")
    selected = info["selected_key_component"]
    if selected:
        largest_non_key = max(
            (len(cells) for color, cells in info["body_components"] if color != info["key"]),
            default=0,
        )
        if largest_non_key <= len(selected):
            errors.append("a non-key distractor must be larger than the selected key component")
    for witness_name, witness in SEMANTIC_WITNESSES.items():
        try:
            if not witness(grid):
                errors.append(f"missing semantic witness {witness_name}")
        except Exception as exc:  # make malformed inputs fail loudly but readably
            errors.append(f"semantic witness {witness_name} errored: {exc}")
    return errors

