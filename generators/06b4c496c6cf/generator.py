"""Generator for arc_puzzle_bank_21_set15:S15_M2.

The color-2 object is a reusable template.  Normalize its cells against the
TOP-LEFT OF ITS BOUNDING BOX, then stamp those offsets at every marker cell of
colors 3..9.  Each stamp inherits its marker's color.  The output is rebuilt
on a blank canvas, colors are applied in numeric order (higher colors win
cross-color overlaps), and out-of-bounds cells clip silently.

The nine-pair schedule uses eight demonstrations plus one query.  It keeps
one plain canonical-style pair and repeats each of the four shortcut-breaking
profiles twice, so every cyclic start and every held-out query position still
leaves a witness for every canonical-compatible shortcut.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "06b4c496c6cf"
TASK_ID = GENERATOR_ID
VERSION = "3.2.0"
RULE_HASH = "7bb33c62cc2e"

SUMMARY = (
    "Use the connected color-2 object as a bbox-top-left-anchored template. "
    "On a blank same-size canvas, stamp it at every color-3..9 marker in the "
    "marker color; higher marker colors win overlaps and edge cells clip. "
    "Nine-pair, eight-demonstration lessons keep one canonical-style plain pair "
    "and duplicate each shortcut-breaking profile, making every held-out query "
    "rotation identifiable against the declared competitors; every scene also "
    "includes a marker color 6..9 to teach the full marker palette."
)

EXAMPLES_NEEDED = 8
MIN_STRICT_FRAC = 0.05

INVARIANTS = [
    "the input is a 10..18 by 12..22 grid with modal background 0",
    "exactly one 4-connected color-2 template has 3..6 cells in a 2..3 by 2..3 bbox",
    "there are 1..6 marker cells, each colored 3..9, and every marker has at least one in-bounds stamped cell",
    "ordinary lessons expose at most one special relation: hollow bbox corner, one overlap pair, one repeated marker color, or one clipped marker",
    "the authoritative output starts blank, removes the template, stamps every marker, applies colors 3..9 in order, and clips out-of-bounds offsets",
]

TEXTURES = ("plain", "hollow_corner", "overlap_pair", "pair_markers", "clip")
HELPFUL_TEXTURES = TEXTURES[1:]
DEGENERATE_TEXTURES: tuple[str, ...] = ()
_TEXTURE_SCHEDULE = (
    "plain",
    "hollow_corner",
    "overlap_pair",
    "pair_markers",
    "clip",
    "hollow_corner",
    "overlap_pair",
    "pair_markers",
    "clip",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical slot 10; otherwise difficulty-aware 10..18",
        "valid": "10..18",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical slot 16; otherwise difficulty-aware 12..22",
        "valid": "12..22",
    },
    "marker_count": {
        "type": "int",
        "default": "canonical slot 3; otherwise difficulty-aware 1..6",
        "valid": "1..6",
    },
    "texture": {
        "type": "str",
        "default": "sample_index mod 9 rotation-safe schedule",
        "valid": "plain|hollow_corner|overlap_pair|pair_markers|clip",
        "doc": (
            "plain has no special relation; hollow_corner omits the template "
            "bbox top-left cell; overlap_pair has exactly one pair of "
            "cross-color stamp footprints overlap; pair_markers repeats one "
            "marker color exactly twice; clip has exactly one partial stamp"
        ),
    },
}

# These two combinations cannot realize their named relation with one marker.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"texture": "overlap_pair", "marker_count": 1},
    {"texture": "pair_markers", "marker_count": 1},
]

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

# Exact normalized template masks in the three canonical inputs.
_CANONICAL_TEMPLATES = (
    ((0, 0), (0, 2), (1, 0), (1, 1), (1, 2)),
    ((0, 0), (0, 1), (1, 0), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (1, 0), (1, 1), (2, 1)),
)

# Broader lawful morphology, still compact enough to support six independent
# stamps at every valid boundary size.
_TOP_LEFT_TEMPLATES = _CANONICAL_TEMPLATES + (
    ((0, 0), (0, 1), (0, 2), (1, 1)),
    ((0, 0), (1, 0), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 0), (0, 1), (1, 1), (1, 2)),
)

_HOLLOW_TEMPLATES = (
    ((0, 1), (1, 0), (1, 1), (2, 0)),
    ((0, 1), (0, 2), (1, 0), (1, 1)),
    ((0, 2), (1, 1), (1, 2), (2, 0), (2, 1)),
)


def _normalize(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _shape_dims(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == color
    }
    out = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        queue = deque([start])
        cells = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in _DIRS4:
                nxt = (r + dr, c + dc)
                if nxt in unseen:
                    unseen.remove(nxt)
                    queue.append(nxt)
        out.append(tuple(sorted(cells)))
    return out


def _footprint(anchor, offsets, h, w):
    ar, ac = anchor
    all_cells = {(ar + dr, ac + dc) for dr, dc in offsets}
    in_bounds = {
        (r, c) for r, c in all_cells if 0 <= r < h and 0 <= c < w
    }
    return in_bounds, len(in_bounds) != len(all_cells)


def _scene_facts(grid) -> dict[str, Any]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid:
        return {"errors": ["grid must be a non-empty list"]}
    if not all(isinstance(row, (list, str)) and row for row in grid):
        return {"errors": ["grid rows must be non-empty lists or digit strings"]}
    coerced = [
        [int(v) if isinstance(v, str) and v.isdigit() else v for v in row]
        for row in grid
    ]
    w = len(coerced[0])
    if any(len(row) != w for row in coerced):
        return {"errors": ["grid must be rectangular"]}
    h = len(coerced)
    if not (10 <= h <= 18):
        errors.append(f"grid height must be in 10..18, got {h}")
    if not (12 <= w <= 22):
        errors.append(f"grid width must be in 12..22, got {w}")
    if any(type(v) is not int or not 0 <= v <= 9 for row in coerced for v in row):
        errors.append("every cell must be an integer color in 0..9")
        return {"errors": errors, "grid": coerced}

    counts = Counter(v for row in coerced for v in row)
    if set(counts) - set(range(10)):
        errors.append("palette contains an invalid color")
    if counts[0] * 2 <= h * w:
        errors.append("background 0 must occupy more than half the grid")

    comps2 = _components(coerced, 2)
    if len(comps2) != 1:
        errors.append(f"expected exactly one color-2 template component, got {len(comps2)}")
        return {
            "errors": errors,
            "grid": coerced,
            "grid_h": h,
            "grid_w": w,
            "template_components": tuple(comps2),
        }
    template = comps2[0]
    offsets = _normalize(template)
    sh, sw = _shape_dims(offsets)
    if not 3 <= len(template) <= 6:
        errors.append(f"template must have 3..6 cells, got {len(template)}")
    if not (2 <= sh <= 3 and 2 <= sw <= 3):
        errors.append(f"template bbox must be 2..3 by 2..3, got {sh}x{sw}")

    markers = tuple(
        sorted(
            (r, c, coerced[r][c])
            for r in range(h)
            for c in range(w)
            if 3 <= coerced[r][c] <= 9
        )
    )
    invalid_nonzero = sorted(
        {v for row in coerced for v in row if v not in (0, 2) and not 3 <= v <= 9}
    )
    if invalid_nonzero:
        errors.append(f"non-marker foreground colors present: {invalid_nonzero}")
    if not 1 <= len(markers) <= 6:
        errors.append(f"expected 1..6 marker cells, got {len(markers)}")

    template_set = set(template)
    footprints = []
    clipped_indices = []
    for index, (r, c, _color) in enumerate(markers):
        in_bounds, clipped = _footprint((r, c), offsets, h, w)
        footprints.append(in_bounds)
        if not in_bounds:
            errors.append(f"marker {(r, c)} has no in-bounds stamped cell")
        if in_bounds & template_set:
            errors.append(f"marker {(r, c)} would stamp across the source template")
        if clipped:
            clipped_indices.append(index)

    overlap_pairs = []
    for left in range(len(footprints)):
        for right in range(left + 1, len(footprints)):
            if footprints[left] & footprints[right]:
                overlap_pairs.append((left, right))

    color_counts = Counter(color for _r, _c, color in markers)
    repeated_colors = {color: n for color, n in color_counts.items() if n > 1}
    if repeated_colors and (
        len(repeated_colors) != 1 or next(iter(repeated_colors.values())) != 2
    ):
        errors.append(
            "at most one marker color may repeat, and it must occur exactly twice"
        )
    if len(clipped_indices) > 1:
        errors.append("at most one marker may have a clipped stamp")
    if len(overlap_pairs) > 1:
        errors.append("at most one pair of stamp footprints may overlap")

    hollow = (0, 0) not in offsets
    special_count = sum(
        (hollow, bool(clipped_indices), bool(overlap_pairs), bool(repeated_colors))
    )
    if special_count > 1:
        errors.append(
            "scene combines multiple special relations; keep hollow, overlap, "
            "repeated-color, and clipping witnesses separate"
        )

    if hollow:
        texture = "hollow_corner"
    elif clipped_indices:
        texture = "clip"
    elif overlap_pairs:
        texture = "overlap_pair"
    elif repeated_colors:
        texture = "pair_markers"
    else:
        texture = "plain"

    return {
        "errors": errors,
        "grid": coerced,
        "grid_h": h,
        "grid_w": w,
        "template": template,
        "template_offsets": offsets,
        "template_h": sh,
        "template_w": sw,
        "markers": markers,
        "marker_count": len(markers),
        "footprints": tuple(frozenset(cells) for cells in footprints),
        "clipped_indices": tuple(clipped_indices),
        "overlap_pairs": tuple(overlap_pairs),
        "repeated_colors": repeated_colors,
        "texture": texture,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    return list(_scene_facts(grid)["errors"])


def observe_overrides(grid):
    facts = _scene_facts(grid)
    if facts["errors"]:
        raise ValueError("cannot observe axes from invalid grid: " + "; ".join(facts["errors"]))
    return {
        "grid_h": facts["grid_h"],
        "grid_w": facts["grid_w"],
        "marker_count": facts["marker_count"],
        "texture": facts["texture"],
    }


def _apply_stamps(
    grid,
    *,
    color_order=range(3, 10),
    one_per_color=False,
    skip_clipped=False,
    force_marker_cell=False,
    keep_template=False,
    template_offsets=None,
):
    facts = _scene_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid stamp scene: " + "; ".join(facts["errors"]))
    h, w = facts["grid_h"], facts["grid_w"]
    out = full_grid(h, w, 0)
    markers = facts["markers"]
    offsets = (
        facts["template_offsets"]
        if template_offsets is None
        else tuple(template_offsets)
    )
    for color in color_order:
        selected = [(r, c, v) for r, c, v in markers if v == color]
        if one_per_color:
            selected = selected[:1]
        for r, c, _value in selected:
            in_bounds, clipped = _footprint((r, c), offsets, h, w)
            if skip_clipped and clipped:
                continue
            for rr, cc in sorted(in_bounds):
                out[rr][cc] = color
    if force_marker_cell:
        for r, c, color in markers:
            out[r][c] = color
    if keep_template:
        for r, c in facts["template"]:
            out[r][c] = 2
    return out


def rule_mirror(grid):
    """Independent Python mirror for tests; canonical Racket remains authority."""
    return _apply_stamps(grid)


def _rival_force_marker_cell(grid):
    return _apply_stamps(grid, force_marker_cell=True)


def _rival_lower_color_wins(grid):
    return _apply_stamps(grid, color_order=range(9, 2, -1))


def _rival_one_marker_per_color(grid):
    return _apply_stamps(grid, one_per_color=True)


def _rival_skip_clipped_stamp(grid):
    return _apply_stamps(grid, skip_clipped=True)


def _rival_keep_template(grid):
    return _apply_stamps(grid, keep_template=True)


def _rival_canonical_colors_only(grid):
    return _apply_stamps(grid, color_order=range(3, 6))


def _rival_first_occupied_cell_anchor(grid):
    facts = _scene_facts(grid)
    if facts["errors"]:
        raise ValueError("invalid stamp scene: " + "; ".join(facts["errors"]))
    first_row, first_col = min(facts["template_offsets"])
    shifted = tuple(
        sorted(
            (row - first_row, col - first_col)
            for row, col in facts["template_offsets"]
        )
    )
    return _apply_stamps(grid, template_offsets=shifted)


def strict_canonical_like(grid) -> list[str]:
    facts = _scene_facts(grid)
    reasons = list(facts["errors"])
    if reasons:
        return reasons
    if (facts["grid_h"], facts["grid_w"]) != (10, 16):
        reasons.append("canonical canvas is exactly 10x16")
    if facts["marker_count"] != 3:
        reasons.append("canonical inputs contain exactly three marker cells")
    if len({color for _r, _c, color in facts["markers"]}) != 3:
        reasons.append("canonical markers use three distinct colors")
    if facts["template_offsets"] not in _CANONICAL_TEMPLATES:
        reasons.append("template is not one of the three canonical normalized masks")
    if facts["texture"] != "plain":
        reasons.append("canonical inputs have no clipping, overlap, repeated marker, or hollow corner")
    return reasons


def _is_texture(name):
    def predicate(grid):
        facts = _scene_facts(grid)
        return not facts["errors"] and facts["texture"] == name

    return predicate


def _template_removed(grid):
    facts = _scene_facts(grid)
    if facts["errors"]:
        return False
    out = rule_mirror(grid)
    return all(out[r][c] != 2 for r, c in facts["template"])


def _has_extended_marker_palette(grid):
    facts = _scene_facts(grid)
    return not facts["errors"] and any(
        color >= 6 for _row, _col, color in facts["markers"]
    )


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "hollow_corner_anchor_gap": _is_texture("hollow_corner"),
    "overlapping_stamps": _is_texture("overlap_pair"),
    "repeated_marker_color": _is_texture("pair_markers"),
    "clipped_stamp": _is_texture("clip"),
    "template_removed": _template_removed,
    "extended_marker_palette": _has_extended_marker_palette,
}

SEMANTIC_RIVALS = {
    "force_marker_cell": _rival_force_marker_cell,
    "lower_color_wins_overlap": _rival_lower_color_wins,
    "one_marker_per_color": _rival_one_marker_per_color,
    "skip_clipped_stamp": _rival_skip_clipped_stamp,
    "keep_template": _rival_keep_template,
    "canonical_colors_only": _rival_canonical_colors_only,
    "first_occupied_cell_anchor": _rival_first_occupied_cell_anchor,
}

WITNESS_RIVALS = {
    "hollow_corner_anchor_gap": [
        "force_marker_cell",
        "first_occupied_cell_anchor",
    ],
    "overlapping_stamps": ["lower_color_wins_overlap"],
    "repeated_marker_color": ["one_marker_per_color"],
    "clipped_stamp": ["skip_clipped_stamp"],
    "template_removed": ["keep_template"],
    "extended_marker_palette": ["canonical_colors_only"],
}

# All six are compatible with every canonical pair; generated witnesses are
# therefore required to distinguish them from the true rule.
CANONICAL_SHORTCUTS = {
    "force_marker_cell": _rival_force_marker_cell,
    "lower_color_wins_overlap": _rival_lower_color_wins,
    "one_marker_per_color": _rival_one_marker_per_color,
    "skip_clipped_stamp": _rival_skip_clipped_stamp,
    "canonical_colors_only": _rival_canonical_colors_only,
    "first_occupied_cell_anchor": _rival_first_occupied_cell_anchor,
}
LESSON_COMPETITORS = dict(CANONICAL_SHORTCUTS)

SCHEDULE_PROFILES = frozenset(TEXTURES)


def schedule_profile(seed, sample_index, difficulty=None):
    del seed, difficulty
    return _TEXTURE_SCHEDULE[int(sample_index) % len(_TEXTURE_SCHEDULE)]


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    refuted = {name: False for name in LESSON_COMPETITORS}
    textures = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} is not an input/output pair")
            continue
        facts = _scene_facts(pair["input"])
        if facts["errors"]:
            reasons.append(f"demo {index} malformed: {facts['errors'][0]}")
            continue
        official = rule_mirror(pair["input"])
        if official != pair["output"]:
            reasons.append(f"demo {index} output disagrees with the stamping rule")
        textures.add(facts["texture"])
        for name, competitor in LESSON_COMPETITORS.items():
            if competitor(pair["input"]) != pair["output"]:
                refuted[name] = True
    for name, was_refuted in refuted.items():
        if not was_refuted:
            reasons.append(f"demos do not refute competitor {name!r}")
    # Plain is useful grounding but has no canonical-compatible rival of its own.
    # Each special profile is duplicated in the nine-pair cycle, so any single
    # held-out query still leaves all four shortcut-breaking witnesses in demos.
    missing = set(HELPFUL_TEXTURES) - textures
    if missing:
        reasons.append(f"demos miss scheduled texture witness(es): {sorted(missing)}")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query is not an input/output pair")
    else:
        qfacts = _scene_facts(query["input"])
        if qfacts["errors"]:
            reasons.append(f"query malformed: {qfacts['errors'][0]}")
        elif "output" in query and rule_mirror(query["input"]) != query["output"]:
            reasons.append("query output disagrees with the stamping rule")
    return reasons


def _validate_call(difficulty, overrides):
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")


def _draw_int_axis(ctx, explicit, label, default_lo, default_hi, valid_lo, valid_hi):
    if label in explicit:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, default_lo, default_hi)


def _anchor_far_from_template(anchor, template_cells):
    r, c = anchor
    return all(abs(r - rr) > 1 or abs(c - cc) > 1 for rr, cc in template_cells)


def _full_anchor_candidates(h, w, offsets, template_cells):
    sh, sw = _shape_dims(offsets)
    candidates = []
    for r in range(h - sh + 1):
        for c in range(w - sw + 1):
            footprint, clipped = _footprint((r, c), offsets, h, w)
            if clipped or footprint & template_cells:
                continue
            if not _anchor_far_from_template((r, c), template_cells):
                continue
            candidates.append(((r, c), footprint))
    return candidates


def _clip_anchor_candidates(h, w, offsets, template_cells):
    candidates = []
    for r in range(h):
        for c in range(w):
            footprint, clipped = _footprint((r, c), offsets, h, w)
            if not clipped or not footprint or footprint & template_cells:
                continue
            if not _anchor_far_from_template((r, c), template_cells):
                continue
            candidates.append(((r, c), footprint))
    return candidates


def _anchors_far(left, right):
    return abs(left[0] - right[0]) > 1 or abs(left[1] - right[1]) > 1


def _choose_layout(h, w, shape, marker_count, texture, colors, rng):
    sh, sw = _shape_dims(shape)
    for _attempt in range(300):
        tr = rng.randint(0, h - sh)
        tc = rng.randint(0, w - sw)
        template_cells = {(tr + r, tc + c) for r, c in shape}
        full = _full_anchor_candidates(h, w, shape, template_cells)
        rng.shuffle(full)
        chosen: list[tuple[tuple[int, int], set[tuple[int, int]]]] = []

        if texture == "clip":
            clipped = _clip_anchor_candidates(h, w, shape, template_cells)
            rng.shuffle(clipped)
            if not clipped:
                continue
            chosen.append(clipped[0])
        elif texture == "overlap_pair":
            pair = None
            for i, (a_anchor, a_foot) in enumerate(full):
                for b_anchor, b_foot in full[i + 1 :]:
                    if not _anchors_far(a_anchor, b_anchor):
                        continue
                    if a_foot & b_foot:
                        pair = ((a_anchor, a_foot), (b_anchor, b_foot))
                        break
                if pair:
                    break
            if pair is None:
                continue
            chosen.extend(pair)
        else:
            if not full:
                continue
            chosen.append(full[0])

        while len(chosen) < marker_count:
            placed = False
            for candidate in full:
                anchor, footprint = candidate
                if any(anchor == old_anchor for old_anchor, _ in chosen):
                    continue
                if any(not _anchors_far(anchor, old_anchor) for old_anchor, _ in chosen):
                    continue
                if any(footprint & old_foot for _old_anchor, old_foot in chosen):
                    continue
                chosen.append(candidate)
                placed = True
                break
            if not placed:
                break
        if len(chosen) != marker_count:
            continue

        grid = full_grid(h, w, 0)
        for r, c in template_cells:
            grid[r][c] = 2
        for ((r, c), _footprint), color in zip(chosen, colors):
            grid[r][c] = color
        return grid
    raise ValueError(
        f"could not realize texture={texture!r} with {marker_count} markers on {h}x{w}"
    )




def _ensure_extended_marker_color(colors):
    colors = list(colors)
    if colors and not any(color >= 6 for color in colors):
        replacement = next(color for color in range(6, 10) if color not in colors)
        colors[-1] = replacement
    return colors

def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    band = "medium" if difficulty is None else difficulty
    explicit = set(overrides)
    scheduled = dict(overrides)
    scheduled.setdefault("texture", schedule_profile(seed, sample_index, difficulty))
    # A single-axis marker_count override must remain realizable regardless of
    # the scheduled texture.  Only an explicitly requested incompatible pair
    # is rejected (and declared above for the override contract).
    if (
        scheduled.get("marker_count") == 1
        and "texture" not in overrides
        and scheduled["texture"] in ("overlap_pair", "pair_markers")
    ):
        scheduled["texture"] = "plain"
    profile_index = int(sample_index) % len(_TEXTURE_SCHEDULE)
    canonical_scale_slot = (
        profile_index in (0, 1)
        and scheduled["texture"] in ("plain", "hollow_corner")
        and not ({"grid_h", "grid_w", "marker_count"} & explicit)
    )
    strict_canonical_slot = canonical_scale_slot and scheduled["texture"] == "plain"
    if canonical_scale_slot:
        scheduled.setdefault("grid_h", 10)
        scheduled.setdefault("grid_w", 16)
        scheduled.setdefault("marker_count", 3)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=scheduled,
    )
    texture = ctx.draw_choice("texture", TEXTURES)

    if band == "easy":
        h_bounds, w_bounds, marker_bounds = (10, 12), (12, 16), (1, 3)
    elif band == "hard":
        h_bounds, w_bounds, marker_bounds = (14, 18), (18, 22), (3, 6)
    else:
        h_bounds, w_bounds, marker_bounds = (10, 15), (13, 18), (2, 5)
    if (
        texture in ("overlap_pair", "pair_markers")
        and "marker_count" not in explicit
        and not canonical_scale_slot
    ):
        marker_bounds = (max(2, marker_bounds[0]), max(2, marker_bounds[1]))
    h = _draw_int_axis(ctx, explicit | ({"grid_h"} if canonical_scale_slot else set()),
                       "grid_h", *h_bounds, 10, 18)
    w = _draw_int_axis(ctx, explicit | ({"grid_w"} if canonical_scale_slot else set()),
                       "grid_w", *w_bounds, 12, 22)
    marker_count = _draw_int_axis(
        ctx,
        explicit | ({"marker_count"} if canonical_scale_slot else set()),
        "marker_count",
        *marker_bounds,
        1,
        6,
    )
    if texture in ("overlap_pair", "pair_markers") and marker_count < 2:
        raise ValueError(f"texture={texture!r} requires marker_count >= 2")

    rng = ctx.draw_rng("layout")
    if texture == "hollow_corner":
        shape = rng.choice(_HOLLOW_TEMPLATES)
    elif strict_canonical_slot:
        shape = rng.choice(_CANONICAL_TEMPLATES)
    elif texture == "overlap_pair":
        # The 3x3 L has a guaranteed non-adjacent, one-cell overlap under a
        # two-column shift, making the color-order witness robust.
        shape = ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2))
    else:
        shape = rng.choice(_TOP_LEFT_TEMPLATES)

    if texture == "pair_markers":
        unique = _ensure_extended_marker_color(ctx.draw_distinct_colors(
            "marker_colors", n=marker_count - 1, exclude=(0, 1, 2)
        ))
        colors = [unique[0], unique[0], *unique[1:]]
    else:
        colors = _ensure_extended_marker_color(ctx.draw_distinct_colors(
            "marker_colors", n=marker_count, exclude=(0, 1, 2)
        ))
    if texture == "overlap_pair":
        colors[:2] = sorted(colors[:2])

    grid = _choose_layout(h, w, shape, marker_count, texture, colors, rng)
    findings = self_check(grid, difficulty=difficulty)
    if findings:
        raise AssertionError("constructed invalid scene: " + "; ".join(findings))
    observed = observe_overrides(grid)
    expected = {
        "grid_h": h,
        "grid_w": w,
        "marker_count": marker_count,
        "texture": texture,
    }
    if observed != expected:
        raise AssertionError(f"constructed axes {expected!r}, observed {observed!r}")
    return grid
