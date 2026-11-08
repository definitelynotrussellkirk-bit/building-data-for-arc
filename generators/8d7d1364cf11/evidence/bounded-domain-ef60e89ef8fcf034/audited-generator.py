"""Canonical-like input sampler for 8d7d1364cf11.

The unchanged Racket authority finds every 8-connected multicolor component on
background 4. Components larger than one cell are source templates; singleton
components are dots. A dot whose color occurs in a source template stamps that
whole template onto an all-4 output with the matching source cell aligned to the
dot. Dots whose colors are absent from every template disappear.

This sampler deliberately gives every productive dot color one globally unique
source-cell anchor. That preserves the selected rule while removing an opaque
"first matching cell" shortcut that the old fixed templates exposed.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8d7d1364cf11"
TASK_ID = GENERATOR_ID
RULE_HASH = "0a9706fafc20"
VERSION = "3.0.0"
SUMMARY = (
    "On background 4, two or three separated multicolor source templates each "
    "contain a globally unique accent cell. Isolated dots matching an accent "
    "stamp that template with the accent aligned to the dot; isolated colors "
    "absent from all templates are decoys and vanish. The output contains only "
    "the stamped copies, not the source templates or original dots."
)

INVARIANTS = [
    "background is 4 and remains the majority color",
    "two or three 8-connected source templates are separated by an 8-neighbor moat",
    "each source has one globally unique accent color and at least one matching dot",
    "productive dot colors match exactly one source cell globally",
    "at least one isolated absent-color decoy dot is present",
    "all productive stamps fit in bounds and are pairwise disjoint from sources and each other",
]

AXES = {
    "grid_h": {"type": "int", "default": "canonical 18 or broad 16..24", "valid": "16..24"},
    "grid_w": {"type": "int", "default": "canonical 18 or broad 16..24", "valid": "16..24"},
    "n_shapes": {"type": "int", "default": "2..3", "valid": "2..3"},
    "copies_per_shape": {"type": "int", "default": "1..2", "valid": "1..2"},
    "n_decoy_dots": {"type": "int", "default": "1..3", "valid": "1..3"},
    "shape_variant": {"type": "int", "default": "0..5", "valid": "0..5"},
    "shared_body": {"type": "bool", "default": "true in core, otherwise keyed", "valid": "true|false"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("canonical_core", "broad")
_VALID_DIFFICULTIES = {None, "easy", "medium", "hard"}

# Six pairwise nontrivial connected masks. Dihedral transforms are applied per
# source, so these are grammar families rather than fixed screen orientations.
_SHAPE_PATTERNS = (
    ((0, 1), (1, 0), (1, 1), (1, 2), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (0, 2), (1, 0), (1, 2), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (3, 2)),
    ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2), (2, 3)),
    ((0, 1), (0, 2), (1, 0), (1, 1), (1, 2), (2, 1), (2, 3), (3, 1)),
)
# Each shape_variant selects a distinct unordered family set, so the exact
# override can be recovered from pixels even though source positions are random.
_VARIANT_SETS = {
    2: ((0, 1), (2, 3), (4, 5), (0, 2), (1, 4), (3, 5)),
    3: ((0, 1, 2), (3, 4, 5), (0, 2, 4), (1, 3, 5), (0, 3, 5), (1, 2, 4)),
}


def _validate_request_scalars(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed, sample_index, difficulty=None):
    _validate_request_scalars(seed, sample_index, difficulty)
    return "canonical_core" if sample_index % 4 == 0 else "broad"


def _normalize(cells):
    cells = tuple(cells)
    if not cells:
        raise ValueError("cannot normalize an empty shape")
    min_r = min(r for r, _c in cells)
    min_c = min(c for _r, c in cells)
    return tuple(sorted((r - min_r, c - min_c) for r, c in cells))


def _dihedral(cells, code):
    transformed = []
    for r, c in cells:
        x, y = r, -c if code >= 4 else c
        for _ in range(code % 4):
            x, y = y, -x
        transformed.append((x, y))
    return _normalize(transformed)


def _well_formed(grid):
    if not isinstance(grid, list) or not grid:
        return False
    if not all(isinstance(row, list) for row in grid):
        return False
    width = len(grid[0])
    if not (1 <= len(grid) <= 30 and 1 <= width <= 30):
        return False
    return all(
        len(row) == width and all(type(value) is int and 0 <= value <= 9 for value in row)
        for row in grid
    )


def _components(grid):
    """Row-major 8-connected non-background components."""
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
    for start_r in range(height):
        for start_c in range(width):
            if grid[start_r][start_c] == 4 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col, grid[row][col]))
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        if dr == dc == 0:
                            continue
                        nr, nc = row + dr, col + dc
                        if (
                            0 <= nr < height
                            and 0 <= nc < width
                            and grid[nr][nc] != 4
                            and (nr, nc) not in seen
                        ):
                            seen.add((nr, nc))
                            stack.append((nr, nc))
            components.append(tuple(sorted(cells)))
    return components


def _scene(grid):
    components = _components(grid)
    shapes = [component for component in components if len(component) > 1]
    dots = [component[0] for component in components if len(component) == 1]
    matches = {}
    for shape_index, shape in enumerate(shapes):
        for row, col, color in shape:
            matches.setdefault(color, []).append((shape_index, row, col))
    active = []
    decoys = []
    ambiguous = []
    per_shape = Counter()
    for row, col, color in dots:
        found = matches.get(color, [])
        if len(found) == 1:
            shape_index, anchor_r, anchor_c = found[0]
            active.append((row, col, color, shape_index, anchor_r, anchor_c))
            per_shape[shape_index] += 1
        elif not found:
            decoys.append((row, col, color))
        else:
            ambiguous.append((row, col, color, tuple(found)))
    return {
        "components": components,
        "shapes": shapes,
        "dots": dots,
        "matches": matches,
        "active": active,
        "decoys": decoys,
        "ambiguous": ambiguous,
        "per_shape": per_shape,
    }


def _stamp_cells(shape, anchor, dot):
    anchor_r, anchor_c = anchor
    dot_r, dot_c = dot
    return tuple((dot_r + row - anchor_r, dot_c + col - anchor_c, color) for row, col, color in shape)


def _validate_scene(grid):
    if not _well_formed(grid):
        return ["grid must be a nonempty rectangular integer grid with dimensions at most 30"]
    height, width = len(grid), len(grid[0])
    errors = []
    if sum(value == 4 for row in grid for value in row) <= height * width // 2:
        errors.append("background color 4 is not the majority")
    scene = _scene(grid)
    shapes = scene["shapes"]
    active = scene["active"]
    decoys = scene["decoys"]
    if not 2 <= len(shapes) <= 3:
        errors.append(f"expected 2 or 3 source templates, found {len(shapes)}")
    if any(not 4 <= len(shape) <= 12 for shape in shapes):
        errors.append("every source template must contain 4..12 cells")
    if scene["ambiguous"]:
        colors = sorted({item[2] for item in scene["ambiguous"]})
        errors.append(f"productive dot color has multiple source-cell anchors: {colors}")
    if len(active) < len(shapes):
        errors.append(f"only {len(active)} productive dots for {len(shapes)} source templates")
    missing = [index for index in range(len(shapes)) if scene["per_shape"].get(index, 0) == 0]
    if missing:
        errors.append(f"source template(s) without a matching productive dot: {missing}")
    if not decoys:
        errors.append("no absent-color decoy dot")

    shape_colors = Counter(color for shape in shapes for _r, _c, color in shape)
    for color in {item[2] for item in active}:
        if shape_colors[color] != 1:
            errors.append(f"productive color {color} occurs {shape_colors[color]} times in source templates")
    for index, shape in enumerate(shapes):
        accent_colors = {color for _r, _c, color, mapped, _ar, _ac in active if mapped == index}
        if len(accent_colors) != 1:
            errors.append(f"source template {index} has {len(accent_colors)} productive accent colors")
            continue
        body = [color for _r, _c, color in shape if color not in accent_colors]
        if len(body) < 3 or len(set(body)) != 1:
            errors.append(f"source template {index} does not have one repeated body color")

    off_origin = False
    for dot_r, dot_c, _color, shape_index, anchor_r, anchor_c in active:
        shape = shapes[shape_index]
        min_r = min(row for row, _col, _value in shape)
        min_c = min(col for _row, col, _value in shape)
        off_origin |= (anchor_r, anchor_c) != (min_r, min_c)
        for row, col, _value in _stamp_cells(shape, (anchor_r, anchor_c), (dot_r, dot_c)):
            if not (0 <= row < height and 0 <= col < width):
                errors.append(f"productive stamp at {(dot_r, dot_c)} is clipped")
                break
    if active and not off_origin:
        errors.append("all productive accents are at template top-left; alignment is not taught")
    return errors


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return _validate_scene(grid)


def strict_canonical_like(grid):
    return _validate_scene(grid)


def _can_place_component(grid, cells):
    height, width = len(grid), len(grid[0])
    points = {(row, col) for row, col, _value in cells}
    for row, col in points:
        if not (0 <= row < height and 0 <= col < width) or grid[row][col] != 4:
            return False
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == dc == 0:
                    continue
                neighbor = (row + dr, col + dc)
                if neighbor in points:
                    continue
                nr, nc = neighbor
                if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] != 4:
                    return False
    return True


def _paint(grid, cells, value=None):
    for row, col, color in cells:
        grid[row][col] = color if value is None else value


def _source_candidates(height, width, template, rng):
    max_r = max(row for row, _col, _color in template)
    max_c = max(col for _row, col, _color in template)
    candidates = [(row, col) for row in range(1, height - max_r - 1) for col in range(1, width - max_c - 1)]
    rng.shuffle(candidates)
    return candidates


def _place_sources(grid, templates, rng):
    candidates = [_source_candidates(len(grid), len(grid[0]), template, rng) for template in templates]
    placed = [None] * len(templates)

    def search(index):
        if index == len(templates):
            return True
        template = templates[index]
        for top, left in candidates[index]:
            cells = tuple((top + row, left + col, color) for row, col, color in template)
            if not _can_place_component(grid, cells):
                continue
            _paint(grid, cells)
            placed[index] = cells
            if search(index + 1):
                return True
            _paint(grid, cells, 4)
            placed[index] = None
        return False

    if not search(0):
        raise RuntimeError("constructive source placement failed")
    return tuple(placed)


def _single_isolated(grid, row, col):
    height, width = len(grid), len(grid[0])
    if not (0 <= row < height and 0 <= col < width) or grid[row][col] != 4:
        return False
    return all(
        not (0 <= row + dr < height and 0 <= col + dc < width) or grid[row + dr][col + dc] == 4
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if not (dr == dc == 0)
    )


def _dot_candidates(height, width, template, accent):
    accent_r, accent_c = accent
    max_r = max(row for row, _col, _color in template)
    max_c = max(col for _row, col, _color in template)
    return [
        (row, col)
        for row in range(accent_r, height - (max_r - accent_r))
        for col in range(accent_c, width - (max_c - accent_c))
    ]


def _place_active_dots(grid, templates, accents, colors, copies_per_shape, source_cells, rng):
    requests = [shape_index for shape_index in range(len(templates)) for _ in range(copies_per_shape)]
    rng.shuffle(requests)
    source_points = {(row, col) for shape in source_cells for row, col, _value in shape}
    reserved_output = set(source_points)
    placed = []
    candidates = {}
    for shape_index in range(len(templates)):
        choices = _dot_candidates(len(grid), len(grid[0]), templates[shape_index], accents[shape_index])
        rng.shuffle(choices)
        candidates[shape_index] = choices

    def search(index):
        if index == len(requests):
            return True
        shape_index = requests[index]
        template = templates[shape_index]
        accent = accents[shape_index]
        for row, col in candidates[shape_index]:
            if not _single_isolated(grid, row, col):
                continue
            footprint = {
                (nr, nc)
                for nr, nc, _value in _stamp_cells(template, accent, (row, col))
            }
            if footprint & reserved_output:
                continue
            grid[row][col] = colors[shape_index]
            reserved_output.update(footprint)
            placed.append((row, col, colors[shape_index], shape_index, footprint))
            if search(index + 1):
                return True
            placed.pop()
            reserved_output.difference_update(footprint)
            grid[row][col] = 4
        return False

    if not search(0):
        raise RuntimeError("constructive productive-dot placement failed")
    return tuple(placed), reserved_output


def _place_decoys(grid, count, color, reserved_output, rng):
    candidates = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if (row, col) not in reserved_output
    ]
    rng.shuffle(candidates)
    placed = []
    for row, col in candidates:
        if _single_isolated(grid, row, col):
            grid[row][col] = color
            placed.append((row, col, color))
            if len(placed) == count:
                return tuple(placed)
    raise RuntimeError("constructive decoy placement failed")


def _strict_bool(ctx, name, default_options):
    used = name in ctx.overrides and ctx.overrides[name] is not None
    value = ctx.overrides.get(name)
    if used and type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return ctx.draw_choice(name, default_options)


def _axis_int(ctx, name, lo, hi, core_value=None):
    used = name in ctx.overrides and ctx.overrides[name] is not None
    if core_value is not None and not used:
        return ctx.draw_int_strict(name, core_value, core_value)
    return ctx.draw_int_strict(name, lo, hi)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request_scalars(seed, sample_index, difficulty)
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    integer_axes = {"grid_h", "grid_w", "n_shapes", "copies_per_shape", "n_decoy_dots", "shape_variant"}
    for name in integer_axes & overrides.keys():
        value = overrides[name]
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    if "shared_body" in overrides and overrides["shared_body"] is not None and type(overrides["shared_body"]) is not bool:
        raise ValueError("shared_body must be a boolean")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    core = schedule_profile(seed, sample_index, difficulty) == "canonical_core"
    # Difficulty does not alter the rule or exact-axis contract.  It enters the
    # nuisance draws (palette/orientation/layout) so the public band knob is
    # honest while every band still spans the full semantic grammar.
    band_token = str(difficulty) if difficulty is not None else "unbanded"
    grid_h = _axis_int(ctx, "grid_h", 16, 24, 18 if core else None)
    grid_w = _axis_int(ctx, "grid_w", 16, 24, 18 if core else None)
    n_shapes = _axis_int(ctx, "n_shapes", 2, 3, 2 + ((sample_index // 4) % 2) if core else None)
    copies_per_shape = _axis_int(ctx, "copies_per_shape", 1, 2, 1 + ((sample_index // 8) % 2) if core else None)
    n_decoy_dots = _axis_int(ctx, "n_decoy_dots", 1, 3, 2 if core else None)
    shape_variant = _axis_int(ctx, "shape_variant", 0, 5, (sample_index // 4) % 6 if core else None)
    shared_body = _strict_bool(ctx, "shared_body", (True,) if core and "shared_body" not in overrides else (False, True))

    palette_rng = ctx.draw_rng(f"palette_{band_token}")
    if core:
        if shared_body:
            body_colors = [1] * n_shapes
            accent_colors = [3, 6, 8][:n_shapes]
        else:
            body_colors = [1, 2, 7][:n_shapes]
            accent_colors = [3, 6, 8][:n_shapes]
        decoy_color = 5
    else:
        # Canonical examples always use 5 as an absent-color decoy.  Broad
        # profiles deliberately invert that accidental correlation: 5 is a
        # productive accent and the true decoy is another color.
        palette = [1, 2, 3, 6, 7, 8, 9]
        palette_rng.shuffle(palette)
        if shared_body:
            body_colors = [palette[0]] * n_shapes
            accent_colors = [5] + palette[1:n_shapes]
            decoy_color = palette[n_shapes]
        else:
            body_colors = palette[:n_shapes]
            accent_colors = [5] + palette[n_shapes : 2 * n_shapes - 1]
            decoy_color = palette[2 * n_shapes - 1]

    templates = []
    accents = []
    for shape_index, variant in enumerate(_VARIANT_SETS[n_shapes][shape_variant]):
        orientation = ctx.draw_rng(f"shape_orientation_{band_token}_{shape_index}").randrange(8)
        cells = _dihedral(_SHAPE_PATTERNS[variant], orientation)
        accent = max(cells, key=lambda point: (point[0] + point[1], point[0], point[1]))
        accents.append(accent)
        templates.append(
            tuple(
                (row, col, accent_colors[shape_index] if (row, col) == accent else body_colors[shape_index])
                for row, col in cells
            )
        )

    grid = full_grid(grid_h, grid_w, 4)
    source_cells = _place_sources(grid, tuple(templates), ctx.draw_rng(f"source_placements_{band_token}"))
    _active, reserved_output = _place_active_dots(
        grid,
        tuple(templates),
        tuple(accents),
        tuple(accent_colors),
        copies_per_shape,
        source_cells,
        ctx.draw_rng(f"productive_dot_placements_{band_token}"),
    )
    _place_decoys(grid, n_decoy_dots, decoy_color, reserved_output, ctx.draw_rng(f"decoy_placements_{band_token}"))
    return grid



def _shape_signature(shape):
    occupied = _normalize((row, col) for row, col, _value in shape)
    return min(_dihedral(occupied, code) for code in range(8))


_PATTERN_SIGNATURE_TO_INDEX = {
    min(_dihedral(pattern, code) for code in range(8)): index
    for index, pattern in enumerate(_SHAPE_PATTERNS)
}


def observe_overrides(grid):
    """Recover every exact control from pixels for the override-honesty linter."""
    if not _well_formed(grid):
        raise ValueError("cannot observe overrides on a malformed grid")
    scene = _scene(grid)
    shapes = scene["shapes"]
    n_shapes = len(shapes)
    if n_shapes not in _VARIANT_SETS:
        raise ValueError(f"unsupported observed source count: {n_shapes}")
    counts = [scene["per_shape"].get(index, 0) for index in range(n_shapes)]
    if not counts or len(set(counts)) != 1:
        raise ValueError(f"productive copies are not uniform across sources: {counts}")
    variant_indices = []
    body_colors = []
    for shape_index, shape in enumerate(shapes):
        signature = _shape_signature(shape)
        if signature not in _PATTERN_SIGNATURE_TO_INDEX:
            raise ValueError(f"unrecognized source shape signature: {signature}")
        variant_indices.append(_PATTERN_SIGNATURE_TO_INDEX[signature])
        accents = {
            color
            for _row, _col, color, mapped, _anchor_r, _anchor_c in scene["active"]
            if mapped == shape_index
        }
        bodies = {value for _row, _col, value in shape if value not in accents}
        if len(bodies) != 1:
            raise ValueError(f"source {shape_index} has non-unique observed body colors: {sorted(bodies)}")
        body_colors.append(next(iter(bodies)))
    key = tuple(sorted(variant_indices))
    try:
        shape_variant = next(
            index
            for index, family in enumerate(_VARIANT_SETS[n_shapes])
            if tuple(sorted(family)) == key
        )
    except StopIteration as exc:
        raise ValueError(f"unrecognized shape-variant family: {key}") from exc
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_shapes": n_shapes,
        "copies_per_shape": counts[0],
        "n_decoy_dots": len(scene["decoys"]),
        "shape_variant": shape_variant,
        "shared_body": len(set(body_colors)) == 1,
    }

def _solve_unique(grid):
    height, width = len(grid), len(grid[0])
    scene = _scene(grid)
    output = full_grid(height, width, 4)
    for dot_r, dot_c, _color, shape_index, anchor_r, anchor_c in scene["active"]:
        for row, col, value in _stamp_cells(
            scene["shapes"][shape_index], (anchor_r, anchor_c), (dot_r, dot_c)
        ):
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = value
    return output


def _rival_preserve_sources(grid):
    intended = _solve_unique(grid)
    output = deepcopy(grid)
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if intended[row][col] != 4:
                output[row][col] = intended[row][col]
    return output


def _rival_top_left_alignment(grid):
    height, width = len(grid), len(grid[0])
    scene = _scene(grid)
    output = full_grid(height, width, 4)
    for dot_r, dot_c, _color, shape_index, _anchor_r, _anchor_c in scene["active"]:
        shape = scene["shapes"][shape_index]
        min_r = min(row for row, _col, _value in shape)
        min_c = min(col for _row, col, _value in shape)
        for row, col, value in shape:
            nr, nc = dot_r + row - min_r, dot_c + col - min_c
            if 0 <= nr < height and 0 <= nc < width:
                output[nr][nc] = value
    return output


def _rival_first_template_only(grid):
    height, width = len(grid), len(grid[0])
    scene = _scene(grid)
    output = full_grid(height, width, 4)
    if not scene["shapes"]:
        return output
    first = scene["shapes"][0]
    active_colors = {item[2] for item in scene["active"] if item[3] == 0}
    anchor_candidates = [(row, col) for row, col, value in first if value in active_colors]
    anchor = anchor_candidates[0] if anchor_candidates else (first[-1][0], first[-1][1])
    for dot_r, dot_c, _color, _shape_index, _anchor_r, _anchor_c in scene["active"]:
        for row, col, value in _stamp_cells(first, anchor, (dot_r, dot_c)):
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = value
    return output


def _rival_stamp_decoys(grid):
    output = _solve_unique(grid)
    scene = _scene(grid)
    if not scene["shapes"]:
        return output
    shape = scene["shapes"][0]
    anchor = max(((row, col) for row, col, _value in shape), key=lambda point: (point[0] + point[1], point))
    for dot_r, dot_c, _color in scene["decoys"]:
        for row, col, value in _stamp_cells(shape, anchor, (dot_r, dot_c)):
            if 0 <= row < len(grid) and 0 <= col < len(grid[0]):
                output[row][col] = value
    return output


def _rival_ignore_productive_color5(grid):
    """Canonical-fitting color shortcut: treat every color-5 dot as noise."""
    height, width = len(grid), len(grid[0])
    scene = _scene(grid)
    output = full_grid(height, width, 4)
    for dot_r, dot_c, color, shape_index, anchor_r, anchor_c in scene["active"]:
        if color == 5:
            continue
        for row, col, value in _stamp_cells(
            scene["shapes"][shape_index], (anchor_r, anchor_c), (dot_r, dot_c)
        ):
            if 0 <= row < height and 0 <= col < width:
                output[row][col] = value
    return output


SEMANTIC_RIVALS = {
    "preserve_sources": _rival_preserve_sources,
    "top_left_alignment": _rival_top_left_alignment,
    "first_template_only": _rival_first_template_only,
    "stamp_decoys": _rival_stamp_decoys,
    "ignore_productive_color5": _rival_ignore_productive_color5,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _differs(name, grid):
    try:
        return SEMANTIC_RIVALS[name](grid) != _solve_unique(grid)
    except Exception:
        return False


SEMANTIC_WITNESSES = {
    "sources_are_cleared": lambda grid: _differs("preserve_sources", grid),
    "accent_alignment": lambda grid: _differs("top_left_alignment", grid),
    "template_selection": lambda grid: _differs("first_template_only", grid),
    "absent_color_decoy": lambda grid: _differs("stamp_decoys", grid),
    "productive_color5": lambda grid: _differs("ignore_productive_color5", grid),
}
WITNESS_RIVALS = {
    "sources_are_cleared": "preserve_sources",
    "accent_alignment": "top_left_alignment",
    "template_selection": "first_template_only",
    "absent_color_decoy": "stamp_decoys",
    "productive_color5": "ignore_productive_color5",
}


def lesson_identifiable(demos, query):
    reasons = []
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must be a labeled pair"]
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits = all(rival(pair["input"]) == pair["output"] for pair in demos)
            if fits and rival(query["input"]) != query["output"]:
                reasons.append(f"{name} fits every demonstration but changes the query")
        except Exception as exc:
            reasons.append(f"{name} failed to score: {type(exc).__name__}: {exc}")
    return reasons
