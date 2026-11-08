"""Size-sort and bottom-pack FOUR-connected monochromatic objects.

The unchanged canonical Racket `mode` excludes zero.  Therefore the field is
nonzero and uniquely most frequent; zero is a perfectly lawful OBJECT color.
Only components whose bounding box spans the whole canvas are discarded.

Version 3.1 repairs silent placement loss and false override promises.  Ordinary
samples alternate a varied shape family with an area-vs-cell-count trap, using
shared colors, non-7 backgrounds, and alternating frame presence in the latter.
Any two consecutive default samples refute four executable rivals (verified,
not assumed), including the retained frame-preservation audit counterexample.
Explicit overrides opt out of that lesson guarantee, never out of validation.
Seed and sample coordinates are exact public API values, never coerced scalars.
"""
from __future__ import annotations

from collections import Counter
from numbers import Integral

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ee64b9b0fe20"
TASK_ID = "ee64b9b0fe20"
VERSION = "3.1.0"
RULE_HASH = "e0863705f64c"  # normalized canonical program; raw SHA begins f9da66074774
SUMMARY = (
    "Drop monochromatic 4-connected objects to the bottom, packing their bounding "
    "boxes left-to-right by distinct cell count; discard whole-canvas-bbox frames. "
    "Varied 10..18 canvases, 2..6 shapes, zero-inclusive/repeated object colors, "
    "rectangles and irregular blobs up to 12 cells, optional frames, real overrides, "
    "and measured area-sort/color-group/background/frame-preservation shortcuts."
)
INVARIANTS = [
    "the nonzero field is the unique most frequent color, including against zero",
    "2..6 non-frame monochromatic four-connected objects have distinct cell counts",
    "object colors may repeat and may be zero; different colors may touch",
    "every requested object is placed, and packed bounding-box widths fit the canvas",
    "an optional frame has whole-canvas bbox and a color absent from the objects",
]
HELPFUL_TEXTURES = ("mixed", "rectangles", "area_trap")
DEGENERATE_TEXTURES = ("no_shapes", "single_shape", "full_grid")
AXES = {
    "grid_h": {"type": "int", "default": "60% shared 10x10 canvas, else 10..18", "valid": "10..18"},
    "grid_w": {"type": "int", "default": "60% shared 10x10 canvas, else 10..18", "valid": "10..18"},
    "shape_count": {"type": "int", "default": "difficulty-dependent 2..5", "valid": "2..6"},
    "bg_color": {"type": "color", "default": "nonzero; trap lessons exclude 7", "valid": "1..9"},
    "frame": {"type": "bool", "default": "alternates by sample_index", "valid": "true|false"},
    "palette_size": {"type": "int", "default": "shape_count or shape_count-1", "valid": "1..6"},
    "texture": {"type": "str", "default": "mixed / area_trap lesson cycle",
                "valid": "|".join(HELPFUL_TEXTURES), "probe": "diagnostic"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [("shape_count", "palette_size")]
MIN_STRICT_FRAC = 1.0
VALID_DIFFICULTIES = (None, "easy", "medium", "hard")


def _validate_overrides(overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(sorted(unknown))}")
    clean = {key: value for key, value in overrides.items() if value is not None}
    for key in ("grid_h", "grid_w", "shape_count", "palette_size", "bg_color"):
        if key in clean and (isinstance(clean[key], bool) or not isinstance(clean[key], Integral)):
            raise TypeError(f"{key} must be an integer, not {clean[key]!r}")
    if "frame" in clean and not isinstance(clean["frame"], bool):
        raise TypeError("frame must be a boolean")
    return clean


def _validate_difficulty(difficulty):
    if difficulty not in VALID_DIFFICULTIES:
        allowed = ", ".join(repr(value) for value in VALID_DIFFICULTIES)
        raise ValueError(f"difficulty must be one of {allowed}, not {difficulty!r}")
    return difficulty


def _validate_call(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise TypeError(f"seed must be an integer, not {type(seed).__name__}")
    if type(sample_index) is not int:
        raise TypeError(
            f"sample_index must be an integer, not {type(sample_index).__name__}"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    return _validate_difficulty(difficulty)


def _integer(ctx, name, lo, hi, defaults):
    # Default bias and legality are deliberately separate: an explicit endpoint
    # is valid in every difficulty band, rather than clamped to a draw band.
    if name in ctx.overrides:
        return ctx.draw_int(name, lo, hi)
    return ctx.draw_choice(name, defaults)


def _choice(ctx, name, legal, defaults):
    return ctx.draw_choice(name, legal if name in ctx.overrides else defaults)


def _bbox(cells):
    return (min(r for r, c in cells), min(c for r, c in cells),
            max(r for r, c in cells), max(c for r, c in cells))


def _blob(rng, size, max_h, max_w, rectangular=False):
    choices = [(height, size // height) for height in range(1, max_h + 1)
               if size % height == 0 and size // height <= max_w]
    if rectangular:
        if not choices:
            return None
        height, width = rng.choice(choices)
        return [(r, c) for r in range(height) for c in range(width)]
    if choices and rng.randrange(3) == 0:
        height, width = rng.choice(choices)
        return [(r, c) for r in range(height) for c in range(width)]
    if max_h * max_w < size:
        return None
    cells = {(rng.randrange(max_h), rng.randrange(max_w))}
    while len(cells) < size:
        frontier = {(r + dr, c + dc) for r, c in cells
                    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
                    if 0 <= r + dr < max_h and 0 <= c + dc < max_w
                    and (r + dr, c + dc) not in cells}
        cells.add(rng.choice(sorted(frontier)))
    r0, c0, _, _ = _bbox(cells)
    return sorted((r - r0, c - c0) for r, c in cells)


def _shape_set(rng, count, height, width, mass_budget, texture):
    shapes = []
    sizes = []
    if texture == "area_trap":
        # Five cells, bbox area nine; six cells, bbox area six.  No area tie.
        shapes = [[(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)],
                  [(r, c) for r in range(2) for c in range(3)]]
        sizes = [5, 6]
    left = count - len(shapes)
    remaining_mass = mass_budget - sum(sizes)
    cap = min(12, max(6, 2 * remaining_mass // max(1, left) - 1))
    choices = [size for size in range(1, cap + 1) if size not in sizes]
    if len(choices) < left:
        return None
    rest = rng.sample(choices, left)
    if sum(rest) > remaining_mass:
        return None
    remaining_width = width - sum(_bbox(s)[3] + 1 for s in shapes)
    for index, size in enumerate(rest):
        # Reserve at least one column for every still-unbuilt component.
        max_w = min(5, remaining_width - (len(rest) - index - 1))
        if max_w < 1:
            return None
        shape = _blob(rng, size, height, max_w, texture == "rectangles")
        if shape is None:
            return None
        remaining_width -= _bbox(shape)[3] + 1
        shapes.append(shape)
    return shapes


def _place(rng, h, w, bg, frame_color, shapes, colors):
    grid = full_grid(h, w, bg)
    edge = int(frame_color is not None)
    if edge:
        for c in range(w):
            grid[0][c] = grid[-1][c] = frame_color
        for r in range(h):
            grid[r][0] = grid[r][-1] = frame_color
    # Large-first placement is merely a packing heuristic, NOT output ordering.
    for shape, color in sorted(zip(shapes, colors), key=lambda item: -len(item[0])):
        _, _, bottom, right = _bbox(shape)
        origins = [(r, c) for r in range(edge, h - edge - bottom)
                   for c in range(edge, w - edge - right)]
        rng.shuffle(origins)
        for r0, c0 in origins:
            cells = [(r0 + r, c0 + c) for r, c in shape]
            if any(grid[r][c] != bg for r, c in cells):
                continue
            # Monochromatic components may touch OTHER colors, including the
            # frame, but never merge with an existing same-color component.
            if any(0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == color
                   for r, c in cells for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))):
                continue
            for r, c in cells:
                grid[r][c] = color
            break
        else:
            return None  # Retry the WHOLE scene; never return a short scene.
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    difficulty = _validate_call(seed, sample_index, difficulty)
    overrides = _validate_overrides(overrides)
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    # The two-example cycle is shared by a seed family; overrides opt out.
    phase = int(sample_index) % 2
    # Joint canonical scale, drawn independently of texture/color curriculum.
    # Independent h/w bias only gave 5/60 exact canvases in the first battery.
    canonical_scale = ctx.draw_rng("canvas-policy").random() < 0.60
    sizes = (10,) if canonical_scale else tuple(range(10, 19))
    h = _integer(ctx, "grid_h", 10, 18, sizes)
    w = _integer(ctx, "grid_w", 10, 18, sizes)
    counts = (2, 3) if difficulty == "easy" else ((4, 5) if difficulty == "hard" else (3, 4))
    # A pinned palette implies enough objects unless count is pinned as well.
    if "palette_size" in overrides and "shape_count" not in overrides:
        counts = tuple(max(n, overrides["palette_size"]) for n in counts)
    count = _integer(ctx, "shape_count", 2, 6, counts)
    bg = _choice(ctx, "bg_color", tuple(range(1, 10)),
                 tuple(c for c in range(1, 10) if not phase or c != 7))
    # Frame presence is an executed rule branch: every two consecutive default
    # examples cover both absent and present.  This prevents an episode from
    # teaching only frameless demos and then querying a frame-preserving rival.
    frame = _choice(ctx, "frame", (False, True), (bool(phase),))
    texture = _choice(ctx, "texture", HELPFUL_TEXTURES + DEGENERATE_TEXTURES,
                      ("mixed",) if phase == 0 else ("area_trap",))
    palette_size = _integer(ctx, "palette_size", 1, 6, (count if not phase else max(1, count - 1),))
    if palette_size > count:
        raise ValueError("palette_size cannot exceed shape_count")
    if texture in DEGENERATE_TEXTURES:
        return _draw_from_degenerate(texture, h, w, bg)
    rng = ctx.draw_rng("construction")
    edge = int(frame)
    frame_mass = 2 * h + 2 * w - 4 if frame else 0
    # This sufficient bound makes the field dominate even with one object color.
    mass_budget = min(72, h * w - 2 * frame_mass - 1, (h * w - frame_mass - 1) // 2)
    require_curriculum = phase == 1 and not overrides
    for _ in range(512):
        shapes = _shape_set(rng, count, h - 2 * edge, w, mass_budget, texture)
        if shapes is None or any(_bbox(s)[3] + 1 > w - 2 * edge for s in shapes):
            continue
        palette = rng.sample([c for c in range(10) if c != bg], palette_size)
        colors = [palette[index % palette_size] for index in range(count)]
        rng.shuffle(colors)
        frame_color = rng.choice([c for c in range(10) if c != bg and c not in palette]) if frame else None
        grid = _place(rng, h, w, bg, frame_color, shapes, colors)
        if grid is None or self_check(grid):
            continue
        answer = rule_mirror(grid)
        # An explicit area_trap must really refute area-sort even with shared
        # colors; compare full outputs, not just differing sort-key sequences.
        if texture == "area_trap" and rival_bbox_area(grid) == answer:
            continue
        if require_curriculum and any(rival(grid) == answer for rival in SEMANTIC_RIVALS.values()):
            continue
        return grid
    raise RuntimeError(f"could not construct an exact scene after 512 attempts: {overrides!r}")


def _components_non_bg(grid, bg):
    h, w = len(grid), len(grid[0])
    seen, out = set(), []
    for sr in range(h):
        for sc in range(w):
            if (sr, sc) in seen or grid[sr][sc] == bg:
                continue
            color, queue, cells = grid[sr][sc], [(sr, sc)], []
            seen.add((sr, sc))
            while queue:
                r, c = queue.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen and grid[nr][nc] == color:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            out.append((color, cells))
    return out


def _analyze(grid, background=None):
    h, w = len(grid), len(grid[0])
    counts = Counter(v for row in grid for v in row if v != 0)
    bg = background if background is not None else (max(counts, key=counts.get) if counts else 0)
    components = _components_non_bg(grid, bg)
    shapes = [(color, cells) for color, cells in components if _bbox(cells) != (0, 0, h - 1, w - 1)]
    return h, w, bg, components, shapes


def self_check(grid, *, difficulty=None, meta=None):
    """A total validator: malformed input returns reasons, never IndexError."""
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["expected a nonempty rectangular grid"]
    if any(not isinstance(row, (list, tuple)) or not row for row in grid):
        return ["expected nonempty grid rows"]
    if len({len(row) for row in grid}) != 1:
        return ["ragged grid"]
    if any(isinstance(v, bool) or not isinstance(v, Integral) or not 0 <= v <= 9 for row in grid for v in row):
        return ["colors must be integers in 0..9, not booleans"]
    h, w = len(grid), len(grid[0])
    if not (10 <= h <= 18 and 10 <= w <= 18):
        return ["canvas dimensions must be 10..18"]
    counts = Counter(v for row in grid for v in row)
    nonzero = {v: n for v, n in counts.items() if v != 0}
    if not nonzero:
        return ["a nonzero background is required by Racket mode"]
    bg = max(nonzero, key=nonzero.get)
    if any(n >= counts[bg] for v, n in counts.items() if v != bg):
        return ["background must be the unique most frequent color"]
    _, _, _, components, shapes = _analyze(grid)
    errors = []
    if not 2 <= len(shapes) <= 6:
        errors.append(f"expected 2..6 non-frame shapes, got {len(shapes)}")
    sizes = [len(cells) for color, cells in shapes]
    if len(sizes) != len(set(sizes)):
        errors.append(f"non-frame sizes must be distinct: {sorted(sizes)}")
    widths = [_bbox(cells)[3] - _bbox(cells)[1] + 1 for color, cells in shapes]
    if sum(widths) > w:
        errors.append(f"packed widths exceed canvas: {sum(widths)} > {w}")
    if len(components) - len(shapes) > 1:
        errors.append("at most one whole-canvas-bbox frame is supported")
    return errors


def _pack(grid, shapes, bg, key):
    h, w = len(grid), len(grid[0])
    output, offset = full_grid(h, w, bg), 0
    for color, cells in sorted(shapes, key=key):
        r0, c0, r1, c1 = _bbox(cells)
        for r, c in cells:
            nr, nc = h - (r1 - r0 + 1) + r - r0, offset + c - c0
            # Rival rules can invent over-wide grouped objects; give a total
            # clipped rival rather than raising. Valid rule_mirror never clips.
            if 0 <= nr < h and 0 <= nc < w:
                output[nr][nc] = color
        offset += c1 - c0 + 1
    return output


def rule_mirror(grid):
    """Diagnostic Python mirror, NOT an authority for dataset labels."""
    _, _, bg, _, shapes = _analyze(grid)
    return _pack(grid, shapes, bg, key=lambda item: len(item[1]))


def rival_bbox_area(grid):
    _, _, bg, _, shapes = _analyze(grid)
    return _pack(grid, shapes, bg, key=lambda item: (
        (_bbox(item[1])[2] - _bbox(item[1])[0] + 1) * (_bbox(item[1])[3] - _bbox(item[1])[1] + 1)))


def rival_group_by_color(grid):
    _, _, bg, _, shapes = _analyze(grid)
    groups = {}
    for color, cells in shapes:
        groups.setdefault(color, []).extend(cells)
    return _pack(grid, list(groups.items()), bg, key=lambda item: len(item[1]))


def rival_fixed_background_7(grid):
    _, _, bg, _, shapes = _analyze(grid, background=7)
    return _pack(grid, shapes, bg, key=lambda item: len(item[1]))


def rival_preserve_frame(grid):
    """Pack by the intended rule, but incorrectly restore any enclosing frame."""
    output = rule_mirror(grid)
    h, w, _, components, _ = _analyze(grid)
    for color, cells in components:
        if _bbox(cells) == (0, 0, h - 1, w - 1):
            for r, c in cells:
                output[r][c] = color
    return output


def observe_overrides(grid):
    h, w, bg, components, shapes = _analyze(grid)
    return {"grid_h": h, "grid_w": w, "bg_color": bg, "shape_count": len(shapes),
            "palette_size": len({color for color, cells in shapes}), "frame": len(components) > len(shapes)}


def semantic_observables(grid):
    _, _, bg, components, shapes = _analyze(grid)
    cells = {(r, c): color for color, shape in shapes for r, c in shape}
    return {**observe_overrides(grid), "shape_sizes": sorted(len(shape) for color, shape in shapes),
            "zero_object": any(color == 0 for color, shape in shapes),
            "nonrectangular": any(len(s) < (_bbox(s)[2] - _bbox(s)[0] + 1) * (_bbox(s)[3] - _bbox(s)[1] + 1)
                                  for color, s in shapes),
            "different_colors_touch": any((r + dr, c + dc) in cells and cells[r + dr, c + dc] != color
                                           for (r, c), color in cells.items() for dr, dc in ((1, 0), (0, 1))),
            "shortcut_disagreements": {name: rival(grid) != rule_mirror(grid) for name, rival in SEMANTIC_RIVALS.items()}}


def strict_canonical_like(grid):
    return self_check(grid)


def _refutes(grid, rival):
    return not self_check(grid) and rival(grid) != rule_mirror(grid)


SEMANTIC_RIVALS = {
    "bbox_area": rival_bbox_area,
    "group_by_color": rival_group_by_color,
    "fixed_background_7": rival_fixed_background_7,
    "preserve_frame": rival_preserve_frame,
}
# Only fixed-background-7 survives EVERY canonical variant.  Area sorting and
# color grouping fit the three original demonstrations but the original held-out
# query refutes them; frame preservation is refuted by the framed canonical demo.
CANONICAL_SHORTCUTS = {"fixed_background_7": rival_fixed_background_7}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
SEMANTIC_WITNESSES = {
    "cell_count_not_bbox_area": lambda g: _refutes(g, rival_bbox_area),
    "components_not_color_classes": lambda g: _refutes(g, rival_group_by_color),
    "background_not_fixed_7": lambda g: _refutes(g, rival_fixed_background_7),
    "frames_removed_not_preserved": lambda g: _refutes(g, rival_preserve_frame),
}
WITNESS_RIVALS = {"cell_count_not_bbox_area": ["bbox_area"],
                  "components_not_color_classes": ["group_by_color"],
                  "background_not_fixed_7": ["fixed_background_7"],
                  "frames_removed_not_preserved": ["preserve_frame"]}


def lesson_identifiable(demos, query):
    reasons = []
    for i, demo in enumerate(demos):
        if self_check(demo["input"]) or demo.get("output") != rule_mirror(demo["input"]):
            reasons.append(f"demo {i} is not a lawful labeled example")
    if self_check(query["input"]):
        reasons.append("query is outside the declared domain")
    if reasons:
        return reasons
    expected = rule_mirror(query["input"])
    if query.get("output") is not None and query["output"] != expected:
        reasons.append("query output disagrees with the task mirror")
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in demos) and rival(query["input"]) != expected:
            reasons.append(f"rival {name} fits demos but changes the query")
    return reasons


def _draw_from_degenerate(name, h, w, bg):
    grid = full_grid(h, w, bg)
    if name == "single_shape":
        grid[3][3] = grid[4][3] = (bg + 1) % 10
    elif name == "full_grid":
        grid = full_grid(h, w, (bg + 1) % 10)
    return grid
