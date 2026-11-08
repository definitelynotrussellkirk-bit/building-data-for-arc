"""Teach content-relative floor halving, including dimensions and blank borders.

Every default four-pair window contains one canonical 6x6 box, one other
even box, and two odd rectangular boxes. Holding out any one pair leaves
examples that distinguish fixed-size, ceil, capped-size and square crops.
Only the complete content box must touch its outer edges: the answer may
have an empty top row or left column, as the canonical task already does.
"""
from __future__ import annotations

from collections import Counter

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "d2b3402dde86"
TASK_ID = "d2b3402dde86"
VERSION = "2.1.0"
RULE_HASH = "115e212b540d"
SUMMARY = "Crop to non-zero content, then return its upper-left floor-half in each dimension."
EXAMPLES_NEEDED = 3

SCENE_POSITIONS = {
    f"bbox_r{row}_c{col}": (row, col)
    for row in (1, 2, 3) for col in (1, 2, 3)
}
SCENE_PROFILES = tuple(SCENE_POSITIONS)
POSITION_SCENE = {position: profile for profile, position in SCENE_POSITIONS.items()}
EXTENT_SHAPES = {
    "canonical": ((6, 6),),
    "even": tuple((h, w) for h in (4, 6, 8) for w in (4, 6, 8) if (h, w) != (6, 6)),
    # Each odd example witnesses floor rounding, independent dimensions and
    # an answer dimension greater than three. Both orientations are sampled.
    "odd": ((5, 9), (7, 9), (9, 5), (9, 7)),
}
EXTENT_PROFILES = tuple(EXTENT_SHAPES)
SCHEDULE_PROFILES = EXTENT_PROFILES
_SCHEDULE = ("canonical", "odd", "even", "odd")
_BAND_SPECS = {"easy": (20, 3), "medium": (22, 4), "hard": (24, 5)}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "keyed draw over all nine padded content-box positions",
        "valid": "bbox_r1_c1|bbox_r1_c2|bbox_r1_c3|bbox_r2_c1|bbox_r2_c2|bbox_r2_c3|bbox_r3_c1|bbox_r3_c2|bbox_r3_c3",
    },
    "extent_profile": {
        "type": "str",
        "default": "seed-offset cycle: canonical, odd, even, odd",
        "valid": "canonical|even|odd",
    },
}
INVARIANTS = [
    "rectangular ARC grid with fixed zero background and three through five foreground colors",
    "observable content-box position is one through three rows and columns from the canvas origin",
    "canonical 6x6 content is mixed with other even boxes and odd rectangular boxes",
    "the complete content bounding box has real support on all four sides and zero external padding",
    "the upper-left floor-half has at least two foreground colors and differs from alternative windows",
    "blank answer borders are retained; the answer is not cropped a second time",
]
# Exactly one quarter of default samples use the retained canonical profile.
MIN_STRICT_FRAC = 0.20


def schedule_profile(seed, sample_index, difficulty=None):
    """Default extent class; explicit extent overrides intentionally bypass it."""
    del difficulty
    return _SCHEDULE[(sample_index + seed) % len(_SCHEDULE)]


def _grid_errors(grid) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
           for row in grid for value in row):
        return ["grid cells must be ARC color integers from zero through nine"]
    return []


def _content_bbox(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not cells:
        raise ValueError("grid contains no non-zero content")
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def _crop_to_content(grid):
    top, left, bottom, right = _content_bbox(grid)
    return [list(row[left:right + 1]) for row in grid[top:bottom + 1]]


def rule_mirror(grid):
    """Input-pure authoring mirror; labels still come from the Racket runtime."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    content = _crop_to_content(grid)
    return [row[:len(content[0]) // 2] for row in content[:len(content) // 2]]


def _quadrants(content):
    h, w = len(content) // 2, len(content[0]) // 2
    return {
        "upper_left": [row[:w] for row in content[:h]],
        "upper_right": [row[-w:] for row in content[:h]],
        "lower_left": [row[:w] for row in content[-h:]],
        "lower_right": [row[-w:] for row in content[-h:]],
    }


def _center_window(content):
    h, w = len(content) // 2, len(content[0]) // 2
    top, left = (len(content) - h) // 2, (len(content[0]) - w) // 2
    return [row[left:left + w] for row in content[top:top + h]]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _texture_errors(content):
    errors = []
    if not all((any(content[0]), any(content[-1]),
                any(row[0] for row in content), any(row[-1] for row in content))):
        errors.append("content must touch all four global bounding-box edges")
    quadrants = _quadrants(content)
    answer = quadrants["upper_left"]
    if len({value for row in answer for value in row if value}) < 2:
        errors.append("the answer must expose at least two foreground colors")
    if len({_frozen(value) for value in quadrants.values()}) != 4:
        errors.append("the four floor-sized corner windows must be visually distinct")
    if answer == _center_window(content):
        errors.append("the answer must differ from the centered floor-sized window")
    return errors


def _paint_cells(rng, height, width, support, palette):
    grid = full_grid(height, width, 0)
    cells = list(support)
    colors = list(palette[:len(cells)])
    while len(colors) < len(cells):
        colors.append(rng.choice(palette))
    rng.shuffle(colors)
    rng.shuffle(cells)
    for (r, c), color in zip(cells, colors):
        grid[r][c] = color
    return grid


def _assemble_content(rng, shape, palette, nonzero_count, edge_feature):
    height, width = shape
    out_h, out_w = height // 2, width // 2
    forbidden = ({(0, c) for c in range(out_w)} if edge_feature == "blank_top" else
                 {(r, 0) for r in range(out_h)} if edge_feature == "blank_left" else set())
    for _attempt in range(256):
        if shape == (6, 6):
            counts = {20: (5, 5, 5, 5), 22: (5, 5, 6, 6), 24: (6, 6, 6, 6)}[nonzero_count]
            content = full_grid(6, 6, 0)
            for quadrant, count in enumerate(counts):
                top, left = (quadrant // 2) * 3, (quadrant % 2) * 3
                eligible = [(r, c) for r in range(3) for c in range(3)
                            if (top + r, left + c) not in forbidden]
                piece = _paint_cells(rng, 3, 3, rng.sample(eligible, count), palette)
                for r in range(3):
                    content[top + r][left:left + 3] = piece[r]
        else:
            eligible = [(r, c) for r in range(height) for c in range(width)
                        if (r, c) not in forbidden]
            count = round(height * width * nonzero_count / 36)
            content = _paint_cells(rng, height, width, rng.sample(eligible, count), palette)
        if not _texture_errors(content):
            return content
    raise RuntimeError("failed to construct a supported asymmetric content texture")


def _difficulty_spec(ctx):
    difficulty = ctx.difficulty
    if isinstance(difficulty, str) and difficulty in _BAND_SPECS:
        return _BAND_SPECS[difficulty]
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        value = max(0.0, min(1.0, float(difficulty)))
        return _BAND_SPECS[("easy", "medium", "hard")[min(2, int(value * 3))]]
    return _BAND_SPECS[ctx.draw_choice("difficulty_profile", ("easy", "medium", "hard"))]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unsupported override axes: {sorted(unknown)}")
    # Resolve the default before using the same exact typed draw as overrides.
    # None retains the shared context's established no-override convention.
    effective = dict(overrides)
    if effective.get("extent_profile") is None:
        effective["extent_profile"] = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=effective)
    scene = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    extent = ctx.draw_choice("extent_profile", EXTENT_PROFILES)
    shape = ctx.draw_choice("content_shape", EXTENT_SHAPES[extent])
    nonzero_count, palette_size = _difficulty_spec(ctx)
    palette = ctx.draw_distinct_colors("palette", n=palette_size, exclude={0})
    # Two border witnesses in every four-pair window survive any single holdout.
    # The seed phase is independent of the extent phase, so odd/even geometry
    # does not determine border style across the population.
    edge_feature = (ctx.draw_choice("answer_border", ("blank_top", "blank_left"))
                    if (sample_index + seed // 4) % 2 else "free")
    content = _assemble_content(ctx.draw_rng("content"), shape, palette, nonzero_count, edge_feature)
    height, width = shape
    grid = full_grid(max(10, height + 4), max(10, width + 4), 0)
    top, left = SCENE_POSITIONS[scene]
    for r in range(height):
        grid[top + r][left:left + width] = content[r]
    return grid


def _analysis(grid):
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors, "profile": None, "extent": None, "content": None}
    try:
        top, left, bottom, right = _content_bbox(grid)
    except ValueError as exc:
        return {"errors": [str(exc)], "profile": None, "extent": None, "content": None}
    shape = (bottom - top + 1, right - left + 1)
    extent = next((name for name, shapes in EXTENT_SHAPES.items() if shape in shapes), None)
    scene = POSITION_SCENE.get((top, left))
    if extent is None:
        errors.append(f"unsupported content-box dimensions: {shape}")
    if scene is None:
        errors.append("content-box position must have row and column in one through three")
    if (len(grid), len(grid[0])) != (max(10, shape[0] + 4), max(10, shape[1] + 4)):
        errors.append("canvas dimensions must retain the declared independent content padding")
    if bottom >= len(grid) - 1 or right >= len(grid[0]) - 1:
        errors.append("content must retain external zero padding on every side")
    content = [list(row[left:right + 1]) for row in grid[top:bottom + 1]]
    colors = {value for row in content for value in row if value}
    if not 3 <= len(colors) <= 5:
        errors.append("content must use three through five foreground colors")
    if shape[0] >= 2 and shape[1] >= 2:
        errors.extend(_texture_errors(content))
    else:
        errors.append("content must have nonempty half-sized windows")
    return {"errors": errors, "profile": scene, "extent": extent, "content": content}


def observe_overrides(grid):
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["profile"], "extent_profile": analysis["extent"]}


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    return list(_analysis(grid)["errors"])


def strict_canonical_like(grid):
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if analysis["extent"] != "canonical":
        return errors + ["strict canonical profile requires a 6x6 content box on a 10x10 canvas"]
    content = analysis["content"]
    if not 20 <= sum(value != 0 for row in content for value in row) <= 24:
        errors.append("canonical content must contain 20 through 24 non-zero cells")
    for name, quadrant in _quadrants(content).items():
        values = [value for row in quadrant for value in row if value]
        if len(values) not in (5, 6) or len(set(values)) < 3:
            errors.append(f"canonical {name} must expose five or six cells and at least three colors")
    return errors


def _rival_modal_fill(grid):
    content = _crop_to_content(grid)
    counts = Counter(value for row in content for value in row if value)
    color = min((-count, value) for value, count in counts.items())[1]
    return full_grid(len(content) // 2, len(content[0]) // 2, color)


def _rival_ceil_half(grid):
    content = _crop_to_content(grid)
    return [row[:(len(content[0]) + 1) // 2] for row in content[:(len(content) + 1) // 2]]


def _rival_square_height(grid):
    content = _crop_to_content(grid)
    side = len(content) // 2
    return [row[:side] for row in content[:side]]


def _rival_square_width(grid):
    content = _crop_to_content(grid)
    side = len(content[0]) // 2
    return [row[:side] for row in content[:side]]


CANONICAL_SHORTCUTS = {
    "fixed_three_after_crop": lambda grid: [row[:3] for row in _crop_to_content(grid)[:3]],
    "ceil_half_crop": _rival_ceil_half,
    "capped_three_half_crop": lambda grid: [row[:3] for row in rule_mirror(grid)[:3]],
    "square_from_height": _rival_square_height,
    "square_from_width": _rival_square_width,
}
SEMANTIC_RIVALS = {
    "identity": lambda grid: [list(row) for row in grid],
    "full_content_crop": _crop_to_content,
    "upper_right_quadrant": lambda grid: _quadrants(_crop_to_content(grid))["upper_right"],
    "lower_left_quadrant": lambda grid: _quadrants(_crop_to_content(grid))["lower_left"],
    "lower_right_quadrant": lambda grid: _quadrants(_crop_to_content(grid))["lower_right"],
    "fixed_canvas_upper_left": lambda grid: [list(row[:len(rule_mirror(grid)[0])])
                                             for row in grid[:len(rule_mirror(grid))]],
    "centered_crop_window": lambda grid: _center_window(_crop_to_content(grid)),
    "modal_color_fill": _rival_modal_fill,
    "trim_answer_background": lambda grid: _crop_to_content(rule_mirror(grid)),
    **CANONICAL_SHORTCUTS,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _rival_differs(grid, name):
    try:
        return rule_mirror(grid) != SEMANTIC_RIVALS[name](grid)
    except (TypeError, ValueError, IndexError):
        return False


SEMANTIC_WITNESSES = {
    name: (lambda grid, rival=name: _rival_differs(grid, rival))
    for name in SEMANTIC_RIVALS
}
WITNESS_RIVALS = {name: [name] for name in SEMANTIC_RIVALS}


def lesson_identifiable(demos, query):
    """Return concrete query ambiguities, separating equivalent survivors."""
    if not isinstance(demos, list) or not demos:
        return ["lesson requires at least one demonstration"]
    reasons = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output grids")
            continue
        try:
            if _grid_errors(pair["output"]) or rule_mirror(pair["input"]) != pair["output"]:
                reasons.append(f"pair {index} output disagrees with the authoritative rule")
        except (TypeError, ValueError, IndexError) as exc:
            reasons.append(f"pair {index} is not rule-applicable: {exc}")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        try:
            if all(rival(pair["input"]) == pair["output"] for pair in demos):
                if rival(query["input"]) != query["output"]:
                    reasons.append(f"named rival {name!r} fits every demo but changes the query answer")
        except (TypeError, ValueError, IndexError) as exc:
            reasons.append(f"named rival {name!r} raised {type(exc).__name__}: {exc}")
    return reasons
