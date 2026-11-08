"""Fixed-color stencil transfer with canonical shapes and role counterexamples.

Stamp the green (3) tight binary crop into the matching solid cyan (8) canvas.
Positions vary. Every ordinary four-slot window contains four role quadrants,
four mask families and two of each canonical footprint. Three demonstrations
refute the declared eight rivals after any one pair is held out. Explicit
controls specify lawful individual inputs, not a guaranteed teaching lesson.
"""
from __future__ import annotations
import hashlib
from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "5639e60f0fac"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c4cb7e8eec6d"
SUMMARY = (
    "Preserve a connected green (3) template and stamp its untransformed 3x3 "
    "or 3x4 binary crop into an isolated matching solid cyan (8) canvas. "
    "Template holes become zero in the canvas. Roles follow fixed colors; "
    "object positions vary in all four quadrants on a zero background."
)
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LESSON_SCHEDULE_PERIOD = 12
INVARIANTS = [
    "integer colors 0, 3 and 8 only; zero background",
    "one connected green template, tight bbox 3x3 or 3x4, with stencil holes",
    "one solid cyan canvas matching the template bbox",
    "bounding boxes isolated by at least one empty row or column",
    "green template preserved; canvas receives its untransformed binary crop",
    "ordinary four-pair windows cover four position quadrants and mask families",
]
PALETTE_KINDS = ("default", "L_template", "T_template", "Z_template")
HELPFUL_TEXTURES = PALETTE_KINDS
INVALID_TEXTURES = ("no_template", "no_canvas", "mismatched_dims")
TEMPLATE_KINDS = ("fixed_3x3", "fixed_3x4")
POSITION_PROFILES = ("upper_left", "upper_right", "lower_left", "lower_right")
SCHEDULE_PROFILES = POSITION_PROFILES
GRID_PROFILES = ((10, 14), (11, 15), (12, 16))
AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile cycle", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "canonical-profile cycle", "valid": "10..18"},
    "palette_kind": {"type": "str", "default": "mask-family cycle; colors stay 3 and 8",
                     "valid": "|".join(PALETTE_KINDS)},
    "template_kind": {"type": "str", "default": "alternating canonical footprints",
                      "valid": "|".join(TEMPLATE_KINDS)},
    "position_bias": {"type": "str", "default": "four-quadrant cycle",
                      "valid": "|".join(POSITION_PROFILES)},
    "palette_size": {"type": "int", "default": "2", "valid": "2", "probe": "diagnostic"},
    "n_distinct_colors": {"type": "int", "default": "2", "valid": "2", "probe": "diagnostic"},
    "canvas_size": {"type": "str", "default": "match", "valid": "match", "probe": "diagnostic"},
    "texture": {"type": "str", "default": "alias for palette_kind",
                "valid": "|".join(HELPFUL_TEXTURES)},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"palette_kind": a, "texture": b}
    for a in PALETTE_KINDS for b in PALETTE_KINDS if a != b
]


def _phase(seed, label, period):
    # A seed-only phase preserves sliding windows. Layout RNG still uses the
    # full seed/index/version context, with no global random state.
    raw = repr((seed, label)).encode("utf-8")
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big") % period


def schedule_profile(seed, sample_index, difficulty=None):
    return POSITION_PROFILES[(sample_index + _phase(seed, "position", 4)) % 4]


def _scheduled_choice(ctx, label, choices, scheduled, overrides):
    return ctx.draw_choice(label, choices if overrides.get(label) is not None else (scheduled,))


def _flips(mask):
    frozen = tuple(tuple(row) for row in mask)
    return tuple(dict.fromkeys((frozen, tuple(row[::-1] for row in frozen),
                               frozen[::-1], tuple(row[::-1] for row in frozen[::-1]))))


def _mask_variants(width, family):
    if family == "default":
        bases = ([[1, 1, 0], [0, 1, 0], [1, 1, 1]],) if width == 3 else (
            [[1, 0, 1, 0], [1, 1, 1, 1], [0, 0, 1, 0]],
            [[0, 1, 1, 0], [0, 0, 1, 0], [1, 1, 1, 1]],
        )
    elif family == "L_template":
        bases = ([[1] + [0] * (width - 1), [1] + [0] * (width - 1), [1] * width],)
    elif family == "T_template":
        stem = [int(c == width // 2) for c in range(width)]
        bases = ([[1] * width, stem, stem],)
    else:
        bases = ([[1, 1, 0], [0, 1, 0], [0, 1, 1]],) if width == 3 else (
            [[1, 1, 1, 0], [0, 0, 1, 0], [0, 0, 1, 1]],
        )
    return tuple(dict.fromkeys(variant for base in bases for variant in _flips(base)))


def _two_intervals(rng, length, size):
    first = rng.randint(0, length - 2 * size - 1)
    second = rng.randint(first + size + 1, length - size)
    return first, second


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    for label, choices in (("palette_kind", PALETTE_KINDS), ("texture", HELPFUL_TEXTURES)):
        if overrides.get(label) is not None and overrides[label] not in choices:
            raise ValueError(f"{label} must be one of {choices}; invalid fixtures are diagnostic-only")
    if (overrides.get("palette_kind") is not None and overrides.get("texture") is not None
            and overrides["palette_kind"] != overrides["texture"]):
        raise ValueError("incompatible palette_kind and texture: both name the same mask family")
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION,
                  task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    gh, gw = GRID_PROFILES[(sample_index + _phase(seed, "dimensions", 3)) % 3]
    hb = (8, 14) if overrides.get("grid_h") is not None else (gh, gh)
    wb = (10, 18) if overrides.get("grid_w") is not None else (gw, gw)
    h = ctx.draw_int_strict("grid_h", *hb)
    w = ctx.draw_int_strict("grid_w", *wb)
    shape = _scheduled_choice(ctx, "template_kind", TEMPLATE_KINDS,
                             TEMPLATE_KINDS[(sample_index + _phase(seed, "shape", 2)) % 2], overrides)
    position = _scheduled_choice(ctx, "position_bias", POSITION_PROFILES,
                                 schedule_profile(seed, sample_index, difficulty), overrides)
    family = (overrides.get("palette_kind") or overrides.get("texture") or
              PALETTE_KINDS[(sample_index + _phase(seed, "family", 4)) % 4])
    family = _scheduled_choice(ctx, "palette_kind", PALETTE_KINDS, family, overrides)
    ctx.draw_choice("texture", (family,))
    ctx.draw_int_strict("palette_size", 2, 2)
    ctx.draw_int_strict("n_distinct_colors", 2, 2)
    ctx.draw_choice("canvas_size", ("match",))
    width = 3 if shape == "fixed_3x3" else 4
    rng = ctx.draw_rng("layout")
    variants = _mask_variants(width, family)
    # Easy uses the base orientation, medium adds a horizontal reflection,
    # hard includes all reflected variants and both nonsquare canonical masks.
    # This is an orientation-support control, not measured human difficulty.
    limit = 1 if difficulty == "easy" else len(variants) if difficulty == "hard" else 2
    mask = rng.choice(variants[:limit])
    upper, lower = _two_intervals(rng, h, 3)
    left, right = _two_intervals(rng, w, width)
    tr, cr = (upper, lower) if position.startswith("upper") else (lower, upper)
    tc, cc = (left, right) if position.endswith("left") else (right, left)
    grid = full_grid(h, w, 0)
    for r in range(3):
        for c in range(width):
            grid[tr + r][tc + c] = 3 if mask[r][c] else 0
            grid[cr + r][cc + c] = 8
    errors = self_check(grid)
    if errors:
        raise RuntimeError("internal stencil invariant: " + "; ".join(errors))
    return grid


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen, comps = set(), []
    for sr in range(h):
        for sc in range(w):
            if grid[sr][sc] != color or (sr, sc) in seen:
                continue
            stack, cells = [(sr, sc)], []
            seen.add((sr, sc))
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(cells)
    return comps


def _bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def _parts(grid):
    template = _bbox(_components(grid, 3)[0])
    canvas = _bbox(_components(grid, 8)[0])
    tr, tc, br, bc = template
    mask = tuple(tuple(int(grid[r][c] == 3) for c in range(tc, bc + 1))
                 for r in range(tr, br + 1))
    return template, canvas, mask


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return ["grid must be a nonempty list of rows"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return ["empty or ragged rows"]
    if len(grid) > 30 or width > 30:
        return ["grid exceeds ARC dimensions"]
    if any(type(value) is not int or value not in (0, 3, 8) for row in grid for value in row):
        return ["cells must be integer colors 0, 3 or 8 (not bool)"]
    templates, canvases = _components(grid, 3), _components(grid, 8)
    errors = []
    if len(templates) != 1:
        errors.append(f"expected one connected green template, got {len(templates)}")
    if len(canvases) != 1:
        errors.append(f"expected one connected cyan canvas, got {len(canvases)}")
    if errors:
        return errors
    t, c = _bbox(templates[0]), _bbox(canvases[0])
    th, tw, ch, cw = t[2] - t[0] + 1, t[3] - t[1] + 1, c[2] - c[0] + 1, c[3] - c[1] + 1
    if (th, tw) not in ((3, 3), (3, 4)):
        errors.append(f"template bbox must be 3x3 or 3x4, got {th}x{tw}")
    if (ch, cw) != (th, tw) or len(canvases[0]) != ch * cw:
        errors.append("cyan canvas must be solid and match the template dimensions")
    if len(templates[0]) == th * tw:
        errors.append("template must have stencil holes")
    if not (t[2] + 1 < c[0] or c[2] + 1 < t[0] or t[3] + 1 < c[1] or c[3] + 1 < t[1]):
        errors.append("object bounding boxes need an empty separating row or column")
    return errors


def strict_canonical_like(grid):
    """The bounded task manifold, not all inputs the Racket program can accept."""
    return self_check(grid)


def observe_overrides(grid):
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe invalid stencil: " + "; ".join(errors))
    template, canvas, mask = _parts(grid)
    width = len(mask[0])
    family = next((name for name in PALETTE_KINDS if mask in _mask_variants(width, name)), "other")
    position = ("upper" if template[0] < canvas[0] else "lower") + "_" + (
        "left" if template[1] < canvas[1] else "right")
    return {"grid_h": len(grid), "grid_w": len(grid[0]),
            "template_kind": f"fixed_3x{width}", "position_bias": position,
            "palette_kind": family, "texture": family, "palette_size": 2,
            "n_distinct_colors": 2, "canvas_size": "match"}


def _stamp(grid, mask, canvas, color=8):
    out = [row[:] for row in grid]
    for r, row in enumerate(mask):
        for c, value in enumerate(row):
            out[canvas[0] + r][canvas[1] + c] = color if value else 0
    return out


def rule_mirror(grid):
    """Python observation aid; actual authority checks execute public Racket."""
    _, canvas, mask = _parts(grid)
    return _stamp(grid, mask, canvas)


def _rival_identity(grid):
    return [row[:] for row in grid]


def _rival_erase_template(grid):
    return [[0 if v == 3 else v for v in row] for row in rule_mirror(grid)]


def _rival_flip_lr(grid):
    _, canvas, mask = _parts(grid)
    return _stamp(grid, [row[::-1] for row in mask], canvas)


def _rival_flip_ud(grid):
    _, canvas, mask = _parts(grid)
    return _stamp(grid, mask[::-1], canvas)


def _rival_rotate_180(grid):
    _, canvas, mask = _parts(grid)
    return _stamp(grid, [row[::-1] for row in mask[::-1]], canvas)


def _rival_position(grid, axis):
    template, canvas, _ = _parts(grid)
    first, second = sorted((template, canvas), key=lambda box: (box[axis], box[1 - axis]))
    source_color = 3 if first == template else 8
    destination_color = 8 if second == canvas else 3
    mask = [[int(grid[r][c] == source_color) for c in range(first[1], first[3] + 1)]
            for r in range(first[0], first[2] + 1)]
    return _stamp(grid, mask, second, destination_color)


def _rival_left_to_right(grid):
    return _rival_position(grid, 1)


def _rival_top_to_bottom(grid):
    return _rival_position(grid, 0)


def _rival_clip_width_3(grid):
    _, canvas, mask = _parts(grid)
    return _stamp(grid, [[v if c < 3 else 0 for c, v in enumerate(row)] for row in mask], canvas)


SEMANTIC_RIVALS = {
    "identity": _rival_identity, "erase_template": _rival_erase_template,
    "flip_lr": _rival_flip_lr, "flip_ud": _rival_flip_ud,
    "rotate_180": _rival_rotate_180, "left_to_right": _rival_left_to_right,
    "top_to_bottom": _rival_top_to_bottom, "clip_width_3": _rival_clip_width_3,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {name: SEMANTIC_RIVALS[name] for name in ("left_to_right", "top_to_bottom")}


def _asymmetric_mask(grid):
    mask = _parts(grid)[2]
    return all(other != mask for other in (tuple(row[::-1] for row in mask),
                                          mask[::-1], tuple(row[::-1] for row in mask[::-1])))


SEMANTIC_WITNESSES = {
    "template_right": lambda grid: _parts(grid)[0][1] > _parts(grid)[1][1],
    "template_below": lambda grid: _parts(grid)[0][0] > _parts(grid)[1][0],
    "four_columns": lambda grid: len(_parts(grid)[2][0]) == 4,
    "asymmetric_mask": _asymmetric_mask,
    "stencil_holes": lambda grid: any(not cell for row in _parts(grid)[2] for cell in row),
    "preserved_template": lambda grid: any(3 in row for row in grid),
}
WITNESS_RIVALS = {
    "template_right": ["left_to_right"], "template_below": ["top_to_bottom"],
    "four_columns": ["clip_width_3"],
    "asymmetric_mask": ["flip_lr", "flip_ud", "rotate_180"],
    "stencil_holes": ["identity"], "preserved_template": ["erase_template"],
}


def lesson_identifiable(demos, query=None) -> list[str]:
    """Check supplied pairs against the finite declared competitor set."""
    if not isinstance(demos, list) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            return [f"demonstration {index} is not an input/output pair"]
        errors = self_check(pair["input"])
        if errors:
            return [f"demonstration {index}: {errors[0]}"]
        if rule_mirror(pair["input"]) != pair["output"]:
            return [f"demonstration {index} has the wrong stencil output"]
    reasons = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if query is None or rival(query["input"]) != query["output"]:
                reasons.append(f"rival {name} survives every demonstration")
    return reasons
