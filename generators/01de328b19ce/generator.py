"""Generator for task 01de328b19ce: transform-and-stamp commands.

Remove every command cell colored 1..5, crop the remaining multicolor template,
and stamp one transformed copy with its top-left at each command cell.  Command
colors mean 1=identity, 2=rotate clockwise, 3=rotate 180 degrees,
4=rotate counter-clockwise, and 5=flip left/right.  Zero template cells are
transparent, off-grid cells clip, and the output contains only the stamps.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "01de328b19ce"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
RULE_HASH = "f6817aded7d7"

SUMMARY = (
    "A cropped template in colors 6-9 is erased from the scene and copied at "
    "isolated command cells colored 1-5.  The command chooses identity, 90° "
    "clockwise, 180°, 90° counter-clockwise, or left-right reflection; the "
    "transformed template is placed top-left at the command, with transparent "
    "zeros and boundary clipping."
)
EXAMPLES_NEEDED = 4

INVARIANTS = [
    "background is 0 and all cells are ARC colors 0..9",
    "one cropped template field uses colors 6..9 (internal gaps/components are preserved)",
    "0..5 isolated command cells use distinct colors 1..5",
    "ordinary templates distinguish identity, three rotations, and flip-lr",
    "stamps use top-left alignment, preserve template colors, clip, and erase the source",
]

TEXTURES = ("plain", "multicolor", "edge_clip", "no_anchors", "rot_symmetric_base")
HELPFUL_TEXTURES = ("plain", "multicolor", "edge_clip")
DEGENERATE_TEXTURES = ("no_anchors", "rot_symmetric_base")
LAWFUL_DEGENERATE_TEXTURES = DEGENERATE_TEXTURES
_TEMPLATE_COLORS = (6, 7, 8, 9)

AXES = {
    "grid_h": {"type": "int", "default": "canonical-profile schedule", "valid": "8..14"},
    "grid_w": {"type": "int", "default": "canonical-profile schedule", "valid": "10..16"},
    "n_anchors": {"type": "int", "default": "3", "valid": "1..5"},
    "texture": {"type": "str", "default": "four-sample teaching schedule", "valid": "|".join(TEXTURES)},
}

# A no-anchor scene has no observable value for n_anchors.  Rejecting that
# pair is intentional and machine-readable rather than silently ignoring it.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = (
    {"texture": "no_anchors", "n_anchors": None},
)

SCHEDULE_PROFILES = ("multicolor_a", "edge_clip", "multicolor_b", "plain")
_PROFILE_DIMS = ((10, 12), (11, 13), (12, 12), (10, 13))
_PROFILE_TEXTURE = ("multicolor", "edge_clip", "multicolor", "plain")
_PROFILE_CODES = (
    (1, 2, 5, 3, 4),
    (3, 4, 5, 1, 2),
    (1, 3, 5, 2, 4),
    (2, 4, 5, 1, 3),
)


def _difficulty_offset(difficulty):
    if difficulty == "medium":
        return 1
    if difficulty == "hard":
        return 2
    if isinstance(difficulty, (int, float)) and not isinstance(difficulty, bool):
        return min(3, max(0, int(float(difficulty) * 4)))
    return 0


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    return SCHEDULE_PROFILES[(sample_index + _difficulty_offset(difficulty)) % len(SCHEDULE_PROFILES)]


def _rot_cw(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _rot_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _rot_ccw(grid):
    return [list(row) for row in zip(*grid)][::-1]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _transform(grid, code):
    return {
        1: lambda x: [list(row) for row in x],
        2: _rot_cw,
        3: _rot_180,
        4: _rot_ccw,
        5: _flip_lr,
    }[code](grid)


def _matrix_key(grid):
    return tuple(tuple(row) for row in grid)


def _all_variants_distinct(template):
    return len({_matrix_key(_transform(template, code)) for code in range(1, 6)}) == 5


def _crop_nonzero(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    if not cells:
        return []
    r1, r2 = min(r for r, _ in cells), max(r for r, _ in cells)
    c1, c2 = min(c for _, c in cells), max(c for _, c in cells)
    return [row[c1:c2 + 1] for row in grid[r1:r2 + 1]]


def _template_from_scene(grid):
    erased = [[0 if 1 <= value <= 5 else value for value in row] for row in grid]
    return _crop_nonzero(erased)


def _anchors(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if 1 <= value <= 5
    ]


def _paint_transparent(out, sub, top, left):
    h, w = len(out), len(out[0])
    for dr, row in enumerate(sub):
        for dc, value in enumerate(row):
            rr, cc = top + dr, left + dc
            if value and 0 <= rr < h and 0 <= cc < w:
                out[rr][cc] = value
    return out


def rule_mirror(grid):
    """Faithful Python mirror used only for tests and semantic rivals."""
    template = _template_from_scene(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c, code in _anchors(grid):
        _paint_transparent(out, _transform(template, code), r, c)
    return out


def _connected(cells):
    if not cells:
        return False
    remaining = set(cells)
    stack = [remaining.pop()]
    seen = set(stack)
    while stack:
        r, c = stack.pop()
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            p = (r + dr, c + dc)
            if p in remaining:
                remaining.remove(p)
                seen.add(p)
                stack.append(p)
    return not remaining


def _grow_template(rng, multicolor):
    """Connected 4-7-cell chiral polyomino; all five task transforms differ."""
    for _ in range(300):
        target = rng.randint(4, 7)
        cells = {(0, 0)}
        while len(cells) < target:
            r, c = rng.choice(tuple(cells))
            dr, dc = rng.choice(((1, 0), (-1, 0), (0, 1), (0, -1)))
            candidate = (r + dr, c + dc)
            next_cells = cells | {candidate}
            rows = [x for x, _ in next_cells]
            cols = [y for _, y in next_cells]
            if max(rows) - min(rows) < 4 and max(cols) - min(cols) < 4:
                cells = next_cells
        r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
        norm = sorted((r - r0, c - c0) for r, c in cells)
        sh = max(r for r, _ in norm) + 1
        sw = max(c for _, c in norm) + 1
        if sh < 2 or sw < 2:
            continue
        template = full_grid(sh, sw, 0)
        colors = rng.sample(_TEMPLATE_COLORS, 2) if multicolor else [rng.choice(_TEMPLATE_COLORS)]
        for index, (r, c) in enumerate(norm):
            template[r][c] = colors[index % len(colors)]
        if multicolor and len({value for row in template for value in row if value}) < 2:
            continue
        if _all_variants_distinct(template):
            return template
    # F-pentomino has no symmetry under the five transformations used here.
    color_a, color_b = (6, 7) if multicolor else (6, 6)
    return [[0, color_a, color_b], [color_a, color_b, 0], [0, color_a, 0]]


def _template_cells(template, top, left):
    return {
        (top + r, left + c)
        for r, row in enumerate(template)
        for c, value in enumerate(row)
        if value
    }


def _halo_clear(point, occupied):
    r, c = point
    return all((r + dr, c + dc) not in occupied for dr in (-1, 0, 1) for dc in (-1, 0, 1))


def _stamp_footprint(template, code, top, left, h, w):
    transformed = _transform(template, code)
    visible = set()
    clipped = 0
    for dr, row in enumerate(transformed):
        for dc, value in enumerate(row):
            if not value:
                continue
            rr, cc = top + dr, left + dc
            if 0 <= rr < h and 0 <= cc < w:
                visible.add((rr, cc))
            else:
                clipped += 1
    return visible, clipped


def _place_anchors(grid, template, codes, *, edge_clip, rng):
    h, w = len(grid), len(grid[0])
    occupied = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    chosen = []
    output_used = set()

    for index, code in enumerate(codes):
        wants_clip = edge_clip and index == 0
        candidates = []
        for r in range(h):
            for c in range(w):
                if grid[r][c] != 0 or not _halo_clear((r, c), occupied):
                    continue
                visible, clipped = _stamp_footprint(template, code, r, c, h, w)
                if not visible:
                    continue
                if wants_clip:
                    if clipped == 0:
                        continue
                elif clipped:
                    continue
                overlap = len(visible & output_used)
                distance = min((abs(r - rr) + abs(c - cc) for rr, cc in occupied), default=h + w)
                candidates.append((overlap, -distance, rng.random(), r, c, visible))
        if not candidates:
            return False
        candidates.sort()
        _, _, _, r, c, visible = candidates[0]
        grid[r][c] = code
        occupied.add((r, c))
        chosen.append((r, c))
        output_used.update(visible)
    return True


def _scheduled_context(seed, sample_index, difficulty, overrides):
    profile = (sample_index + _difficulty_offset(difficulty)) % 4
    default_h, default_w = _PROFILE_DIMS[profile]
    effective = dict(overrides)
    effective.setdefault("grid_h", default_h)
    effective.setdefault("grid_w", default_w)
    effective.setdefault("texture", _PROFILE_TEXTURE[profile])
    if effective.get("texture") != "no_anchors":
        effective.setdefault("n_anchors", 3)
    return profile, gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard") and not isinstance(difficulty, (int, float)):
        raise ValueError(f"unsupported difficulty {difficulty!r}")
    if overrides.get("texture") == "no_anchors" and overrides.get("n_anchors") is not None:
        exc = ValueError("texture='no_anchors' is incompatible with n_anchors")
        exc.incompatible_axes = ("texture", "n_anchors")
        raise exc

    profile, ctx = _scheduled_context(seed, sample_index, difficulty, overrides)
    h = ctx.draw_int("grid_h", 8, 14)
    w = ctx.draw_int("grid_w", 10, 16)
    texture = ctx.draw_choice("texture", TEXTURES)
    n_anchors = 0 if texture == "no_anchors" else ctx.draw_int("n_anchors", 1, 5)
    rng = ctx.draw_rng("layout")

    for attempt in range(160):
        grid = full_grid(h, w, 0)
        if texture == "rot_symmetric_base":
            color = rng.choice(_TEMPLATE_COLORS)
            template = [[color, color], [color, color]]
        else:
            template = _grow_template(rng, multicolor=texture == "multicolor")

        sh, sw = len(template), len(template[0])
        # Source template remains near the upper-left, leaving room for commands.
        r_hi = max(1, min(2, h - sh - 2))
        c_hi = max(1, min(3, w - sw - 2))
        top = rng.randint(1, r_hi)
        left = rng.randint(1, c_hi)
        for r, row in enumerate(template):
            for c, value in enumerate(row):
                if value:
                    grid[top + r][left + c] = value

        if texture == "no_anchors":
            if not self_check(grid):
                return grid
            continue

        ordering = list(_PROFILE_CODES[profile])
        # Preserve the teaching schedule for the default three commands while
        # still honoring every exact 1..5 boundary override.
        codes = ordering[:n_anchors]
        if _place_anchors(grid, template, codes, edge_clip=texture == "edge_clip", rng=rng):
            if not self_check(grid):
                return grid
    raise ValueError(f"could not realize a valid {texture!r} scene after 160 attempts")


def _template_component_errors(template):
    cells = [(r, c) for r, row in enumerate(template) for c, value in enumerate(row) if value]
    errors = []
    if not cells:
        return ["no template cell in colors 6..9"]
    if not any(template[0]):
        errors.append("template crop has an empty top edge")
    if not any(template[-1]):
        errors.append("template crop has an empty bottom edge")
    if not any(row[0] for row in template):
        errors.append("template crop has an empty left edge")
    if not any(row[-1] for row in template):
        errors.append("template crop has an empty right edge")
    return errors


def _texture_of(grid):
    anchors = _anchors(grid)
    if not anchors:
        return "no_anchors"
    template = _template_from_scene(grid)
    variants = {_matrix_key(_transform(template, code)) for code in range(1, 6)}
    if len(variants) < 5:
        return "rot_symmetric_base"
    h, w = len(grid), len(grid[0])
    if any(_stamp_footprint(template, code, r, c, h, w)[1] for r, c, code in anchors):
        return "edge_clip"
    colors = {value for row in template for value in row if value}
    return "multicolor" if len(colors) >= 2 else "plain"


def observe_overrides(grid):
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_anchors": len(_anchors(grid)),
        "texture": _texture_of(grid),
    }


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a non-empty 2D list"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid rows must be non-empty rectangular lists"]

    errors = []
    h, w = len(grid), width
    if not (8 <= h <= 14 and 10 <= w <= 16):
        errors.append(f"dimensions must be 8..14 by 10..16, got {h}x{w}")
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) is not an ARC color: {value!r}")
    if errors:
        return errors

    anchors = _anchors(grid)
    if len(anchors) > 5:
        errors.append(f"at most five commands are allowed, got {len(anchors)}")
    codes = [code for _, _, code in anchors]
    if len(codes) != len(set(codes)):
        errors.append("command colors 1..5 must be distinct")
    for r, c, code in anchors:
        neighbors = [
            grid[rr][cc]
            for rr in range(max(0, r - 1), min(h, r + 2))
            for cc in range(max(0, c - 1), min(w, c + 2))
            if (rr, cc) != (r, c)
        ]
        if any(neighbors):
            errors.append(f"command color {code} at ({r},{c}) is not isolated by a zero halo")

    template = _template_from_scene(grid)
    errors.extend(_template_component_errors(template))
    if template:
        bad = sorted({value for row in template for value in row if value not in (0, 6, 7, 8, 9)})
        if bad:
            errors.append(f"template contains non-template colors {bad}")
        texture = _texture_of(grid)
        if texture == "rot_symmetric_base":
            if not (len(template) == 2 and len(template[0]) == 2 and len({v for row in template for v in row}) == 1):
                errors.append("only a solid 2x2 template is a lawful rotational degeneracy")
        elif not _all_variants_distinct(template):
            errors.append("ordinary template must distinguish all five command transforms")
    return errors


def strict_canonical_like(grid):
    return self_check(grid)


MIN_STRICT_FRAC = 0.95


def _rival_keep_template(grid):
    out = rule_mirror(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if 6 <= value <= 9:
                out[r][c] = value
    return out


def _rival_centered(grid):
    template = _template_from_scene(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c, code in _anchors(grid):
        sub = _transform(template, code)
        _paint_transparent(out, sub, r - len(sub) // 2, c - len(sub[0]) // 2)
    return out


def _rival_monochrome(grid):
    template = [[6 if value else 0 for value in row] for row in _template_from_scene(grid)]
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c, code in _anchors(grid):
        _paint_transparent(out, _transform(template, code), r, c)
    return out


def _rival_identity_codes(grid):
    template = _template_from_scene(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c, _ in _anchors(grid):
        _paint_transparent(out, template, r, c)
    return out


def _rival_code5_rot180(grid):
    template = _template_from_scene(grid)
    out = full_grid(len(grid), len(grid[0]), 0)
    for r, c, code in _anchors(grid):
        sub = _rot_180(template) if code == 5 else _transform(template, code)
        _paint_transparent(out, sub, r, c)
    return out


def _rival_drop_clipped(grid):
    template = _template_from_scene(grid)
    h, w = len(grid), len(grid[0])
    out = full_grid(h, w, 0)
    for r, c, code in _anchors(grid):
        sub = _transform(template, code)
        footprint, clipped = _stamp_footprint(template, code, r, c, h, w)
        if footprint and not clipped:
            _paint_transparent(out, sub, r, c)
    return out


def _rival_keep_commands(grid):
    out = rule_mirror(grid)
    for r, c, code in _anchors(grid):
        out[r][c] = code
    return out


SEMANTIC_RIVALS: dict[str, Callable] = {
    "preserve source template": _rival_keep_template,
    "center stamps on commands": _rival_centered,
    "recolor stamps to 6": _rival_monochrome,
    "ignore command transforms": _rival_identity_codes,
    "treat code 5 as rotate-180": _rival_code5_rot180,
    "drop boundary-crossing stamps": _rival_drop_clipped,
    "preserve command cells": _rival_keep_commands,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = {"drop boundary-crossing stamps": _rival_drop_clipped}


def _differs(grid, rival_name):
    return SEMANTIC_RIVALS[rival_name](deepcopy(grid)) != rule_mirror(grid)


def _has_code(grid, codes):
    return any(code in codes for _, _, code in _anchors(grid))


SEMANTIC_WITNESSES = {
    "source_template_erased": lambda grid: _differs(grid, "preserve source template"),
    "top_left_alignment": lambda grid: _differs(grid, "center stamps on commands"),
    "template_colors_preserved": lambda grid: _texture_of(grid) == "multicolor" and _differs(grid, "recolor stamps to 6"),
    "rotation_commands_visible": lambda grid: _has_code(grid, {2, 3, 4}) and _differs(grid, "ignore command transforms"),
    "flip_command_visible": lambda grid: _has_code(grid, {5}) and _differs(grid, "treat code 5 as rotate-180"),
    "partial_boundary_stamp": lambda grid: _texture_of(grid) == "edge_clip" and _differs(grid, "drop boundary-crossing stamps"),
    "commands_are_instructions": lambda grid: _differs(grid, "preserve command cells"),
}

WITNESS_RIVALS = {
    "source_template_erased": ["preserve source template"],
    "top_left_alignment": ["center stamps on commands"],
    "template_colors_preserved": ["recolor stamps to 6"],
    "rotation_commands_visible": ["ignore command transforms"],
    "flip_command_visible": ["treat code 5 as rotate-180"],
    "partial_boundary_stamp": ["drop boundary-crossing stamps"],
    "commands_are_instructions": ["preserve command cells"],
}


def lesson_identifiable(demos, query):
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons = []
    for index, pair in enumerate([*demos, query]):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
        elif pair["output"] != rule_mirror(pair["input"]):
            reasons.append(f"pair {index} output disagrees with transform-and-stamp rule")
    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(pair["input"]) == pair["output"] for pair in demos):
            if rival(query["input"]) != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
    return reasons
