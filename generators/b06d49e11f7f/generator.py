"""Generator for b06d49e11f7f — decode a legend, then repaint framed rooms.

Rows 0-1 are a sparse source→target color legend.  Each color-5 rectangular
frame below the legend contains one source-colored seed.  The authoritative
rule fills the *entire* frame interior, including the seed cell, with that
seed's target color from the legend; the color-5 outline and everything
outside framed interiors stay unchanged.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from puzzle_generators.base import gen_ctx, stable_rng
from puzzle_generators.helpers.grid import draw_frame, full_grid

GENERATOR_ID = "b06d49e11f7f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "9538488b69e8"

SUMMARY = (
    "Rows 0-1 form a sparse source→target color legend.  Below it are 1-4 "
    "separate hollow color-5 rectangular rooms.  Every room contains exactly "
    "one source-colored seed.  Read the legend by column, use the seed to "
    "select its target color, and repaint the room's whole interior—including "
    "the seed cell—with that target while preserving the color-5 outline and "
    "all cells outside room interiors.  Default draws repeatedly revisit the "
    "canonical 10x12/11x13/12x14 scale while also exploring larger layouts."
)

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

INVARIANTS = [
    "rows 0-1 contain paired nonzero source→target legend entries and no half-pairs",
    "1-4 separate hollow rectangular color-5 frames occur below the legend",
    "each frame interior contains exactly one nonzero, non-5 seed cell",
    "every seed color is a legend source and its mapped target differs from it",
    "there are no stray nonzero body cells outside frame outlines/interior seeds",
    "at least one room has interior area >1, so full-interior fill is observable",
    "within one lesson seed, a repeated source color changes target across sample indexes",
]

# All declared boundaries are exact in every difficulty band.  Difficulty only
# changes the default schedule; an explicit override is always validated against
# this full declared domain.
AXES = {
    "n_rooms": {
        "type": "int",
        "default": "canonical anchor=2; otherwise difficulty-banded",
        "valid": "1..4",
        "doc": "Exact number of color-5 rooms.",
    },
    "grid_h": {
        "type": "int",
        "default": "canonical anchor or difficulty-banded",
        "valid": "9..17",
        "doc": "Exact grid height including the two legend rows.",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical anchor or difficulty-banded",
        "valid": "11..22",
        "doc": "Exact grid width.",
    },
}

# Every Cartesian boundary combination is constructible by the four-slot room
# layout, including (9, 11, 4); no silent incompatibility policy is needed.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

_AVAILABLE = (1, 2, 3, 4, 6, 7, 8, 9)
_CANONICAL_PROFILE = {
    "easy": (10, 12, 2),    # palette size 6 = 0/5 + 2 source + 2 target
    "medium": (11, 13, 3), # palette size 8 = 0/5 + 3 source + 3 target
    "hard": (12, 14, 3),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unsupported difficulty: {difficulty!r}")


def _draw_scheduled_int(ctx, overrides, label, lo, hi, scheduled) -> int:
    """Use full-domain validation for overrides, a narrower schedule otherwise."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, lo, hi)
    return ctx.draw_choice(label, tuple(scheduled))


def _place_frame(g, r0, c0, fh, fw) -> None:
    draw_frame(g, r0, c0, r0 + fh - 1, c0 + fw - 1, 5)


def _room_slots(h: int, w: int) -> list[tuple[int, int, int, int]]:
    """Four disjoint slots, each at least 3x5 even at the 9x11 boundary."""
    body_h = h - 2
    top_h = (body_h - 1) // 2
    bottom_h = body_h - 1 - top_h
    left_w = (w - 1) // 2
    right_w = w - 1 - left_w
    return [
        (2, 0, top_h, left_w),
        (2, left_w + 1, top_h, right_w),
        (2 + top_h + 1, 0, bottom_h, left_w),
        (2 + top_h + 1, left_w + 1, bottom_h, right_w),
    ]


def _anchor_source(seed: int) -> int:
    rng = stable_rng(seed, f"{TASK_ID}|anchor_source", VERSION)
    return _AVAILABLE[rng.randrange(len(_AVAILABLE))]


def _anchor_target(seed: int, sample_index: int, source: int) -> int:
    """Same lesson seed reuses one source but changes its target every sample."""
    options = tuple(color for color in _AVAILABLE if color != source)
    rng = stable_rng(seed, f"{TASK_ID}|anchor_target_offset", VERSION)
    offset = rng.randrange(len(options))
    return options[(sample_index + offset) % len(options)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    band = _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    rng = ctx.draw_rng("layout")

    # Two of every three default sample indexes are exact canonical profiles.
    # This keeps every band visibly anchored while one third of draws still
    # explores the broader difficulty scale.
    canonical_anchor = sample_index % 3 != 2
    canonical_h, canonical_w, canonical_pairs = _CANONICAL_PROFILE[band]
    room_choices = {
        "easy": range(1, 3),
        "medium": range(2, 4),
        "hard": range(2, 5),
    }[band]
    h_choices = {
        "easy": range(9, 12),
        "medium": range(10, 15),
        "hard": range(13, 18),
    }[band]
    w_choices = {
        "easy": range(11, 15),
        "medium": range(13, 19),
        "hard": range(16, 23),
    }[band]

    n_rooms = _draw_scheduled_int(
        ctx, overrides, "n_rooms", 1, 4,
        (2,) if canonical_anchor else room_choices,
    )
    h = _draw_scheduled_int(
        ctx, overrides, "grid_h", 9, 17,
        (canonical_h,) if canonical_anchor else h_choices,
    )
    w = _draw_scheduled_int(
        ctx, overrides, "grid_w", 11, 22,
        (canonical_w,) if canonical_anchor else w_choices,
    )

    # The canonical profile controls palette cardinality on default anchors.
    # Off-anchor, every fourth sample omits the extra legend distractor so the
    # curriculum includes both "all pairs used" and "unused pair" examples.
    if canonical_anchor and not any(
        overrides.get(name) is not None for name in ("n_rooms", "grid_h", "grid_w")
    ):
        legend_k = max(n_rooms, canonical_pairs)
    else:
        add_distractor = sample_index % 4 != 0 and n_rooms < 4
        legend_k = n_rooms + int(add_distractor)
        legend_k = max(legend_k, canonical_pairs if canonical_anchor else n_rooms)
    legend_k = min(4, legend_k)

    anchor_source = _anchor_source(seed)
    anchor_target = _anchor_target(seed, sample_index, anchor_source)

    # Source and target sets are disjoint and targets are unique.  Besides
    # eliminating accidental identity mappings, this makes multi-room mapping
    # differences directly visible in the output.
    source_pool = [
        color for color in _AVAILABLE
        if color not in (anchor_source, anchor_target)
    ]
    sources = [anchor_source] + rng.sample(source_pool, legend_k - 1)
    target_pool = [color for color in _AVAILABLE if color not in sources]
    remaining_targets = [color for color in target_pool if color != anchor_target]
    targets = [anchor_target] + rng.sample(remaining_targets, legend_k - 1)
    pairs = list(zip(sources, targets))
    mapping = dict(pairs)

    # Every scene exposes the lesson-stable anchor source inside a room.
    other_sources = [source for source in sources if source != anchor_source]
    frame_sources = [anchor_source] + rng.sample(other_sources, n_rooms - 1)

    g = full_grid(h, w, 0)
    legend_cols = rng.sample(range(w), legend_k)

    # If an unused legend pair exists, place one such distractor at the
    # leftmost legend column.  This creates a clean counterexample to the rival
    # "fill rooms with legend targets from left to right" without changing the
    # oracle rule.
    unused_sources = [source for source in sources if source not in frame_sources]
    if unused_sources:
        left_index = min(range(legend_k), key=lambda index: legend_cols[index])
        unused_index = next(
            index for index, (source, _target) in enumerate(pairs)
            if source == unused_sources[0]
        )
        pairs[left_index], pairs[unused_index] = pairs[unused_index], pairs[left_index]

    for col, (source, target) in zip(legend_cols, pairs):
        g[0][col] = source
        g[1][col] = target

    slots = rng.sample(_room_slots(h, w), n_rooms)
    for index, (source, (slot_r, slot_c, slot_h, slot_w)) in enumerate(
        zip(frame_sources, slots)
    ):
        # The anchor room always has >1 interior cell, including at the minimum
        # 9x11 boundary (slot is 3x5 there), so "recolor only the seed" is never
        # observationally equivalent to the true full-interior fill.
        min_fw = 4 if index == 0 else 3
        fh = rng.randint(3, min(6, slot_h))
        fw = rng.randint(min_fw, min(7, slot_w))
        r0 = slot_r + rng.randint(0, slot_h - fh)
        c0 = slot_c + rng.randint(0, slot_w - fw)
        _place_frame(g, r0, c0, fh, fw)
        sr = rng.randint(r0 + 1, r0 + fh - 2)
        sc = rng.randint(c0 + 1, c0 + fw - 2)
        g[sr][sc] = source

    # Keep the local name alive as a deliberate audit cue: frame seeds are
    # selected from keys of this mapping, and the Racket oracle owns outputs.
    assert all(source in mapping for source in frame_sources)
    return g


def _components(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    out = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            q = [(r, c)]
            seen.add((r, c))
            cells = []
            for rr, cc in q:
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        q.append((nr, nc))
            out.append(cells)
    return out


def _frame_bbox(cells):
    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    r1, c1, r2, c2 = min(rs), min(cs), max(rs), max(cs)
    if r2 - r1 + 1 < 3 or c2 - c1 + 1 < 3:
        return None
    want = {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }
    return (r1, c1, r2, c2) if set(cells) == want else None


def _analyse(grid):
    errors: list[str] = []
    info: dict[str, Any] = {}
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return info, ["grid must be a non-empty list of rows"]
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        return info, ["grid must be rectangular"]
    h = len(grid)
    if h < 3:
        return info, ["grid must have two legend rows plus a body"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("grid colors must be integers 0..9")

    pairs: list[tuple[int, int, int]] = []
    for c in range(w):
        source, target = grid[0][c], grid[1][c]
        if (source == 0) != (target == 0):
            errors.append(f"legend column {c} is a half-pair")
        elif source != 0:
            pairs.append((c, source, target))
    if not pairs:
        errors.append("legend must contain at least one source-target pair")
    if any(source == 5 or target == 5 for _, source, target in pairs):
        errors.append("legend colors must not use frame color 5")
    sources = [source for _, source, _ in pairs]
    if len(set(sources)) != len(sources):
        errors.append("legend source colors must be unique")
    mapping = {source: target for _, source, target in pairs}

    frame_records = []
    all_frame_cells: set[tuple[int, int]] = set()
    components = _components(grid, 5)
    for index, cells in enumerate(components):
        bbox = _frame_bbox(cells)
        if bbox is None:
            errors.append(f"color-5 component {index} is not a hollow rectangle")
            continue
        r1, c1, r2, c2 = bbox
        if r1 < 2:
            errors.append("frame overlaps legend rows")
        interior = [
            (r, c)
            for r in range(r1 + 1, r2)
            for c in range(c1 + 1, c2)
        ]
        seed_cells = [
            (r, c, grid[r][c])
            for r, c in interior
            if grid[r][c] not in (0, 5)
        ]
        if len(seed_cells) != 1:
            errors.append(
                f"frame {index} interior must contain exactly one seed cell; found {len(seed_cells)}"
            )
            seed = None
        else:
            seed = seed_cells[0]
            if seed[2] not in mapping:
                errors.append(f"frame {index} seed color {seed[2]} is not a legend source")
        all_frame_cells.update(cells)
        frame_records.append({
            "bbox": bbox,
            "interior": interior,
            "seed": seed,
        })

    if not (1 <= len(frame_records) <= 4):
        errors.append(f"expected 1-4 rectangular frames, found {len(frame_records)}")

    allowed_body = set(all_frame_cells)
    for frame in frame_records:
        if frame["seed"] is not None:
            allowed_body.add((frame["seed"][0], frame["seed"][1]))
    stray = [
        (r, c, grid[r][c])
        for r in range(2, h)
        for c in range(w)
        if grid[r][c] != 0 and (r, c) not in allowed_body
    ]
    if stray:
        errors.append(f"body contains stray nonzero cell outside rooms at {stray[0][:2]}")

    used_mappings = []
    for frame in frame_records:
        if frame["seed"] is None:
            continue
        seed_color = frame["seed"][2]
        if seed_color in mapping:
            used_mappings.append((seed_color, mapping[seed_color]))
    if used_mappings and not any(source != target for source, target in used_mappings):
        errors.append("at least one used seed mapping must change color")

    info.update({
        "grid_h": h,
        "grid_w": w,
        "palette_size": len({value for row in grid for value in row}),
        "pairs": pairs,
        "mapping": mapping,
        "sources": set(sources),
        "frames": frame_records,
        "n_rooms": len(frame_records),
        "legend_k": len(pairs),
        "used_mappings": used_mappings,
        "first_legend_target": pairs[0][2] if pairs else None,
        "unused_sources": set(sources) - {source for source, _ in used_mappings},
    })
    return info, sorted(set(errors))


def observe_overrides(grid) -> dict[str, int]:
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return {name: int(info[name]) for name in AXES}


def self_check(grid, *, difficulty=None, meta=None):
    return _analyse(grid)[1]


def strict_canonical_like(grid) -> list[str]:
    return self_check(grid)


def rule_mirror(grid):
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = deepcopy(grid)
    for frame in info["frames"]:
        seed_color = frame["seed"][2]
        target = info["mapping"].get(seed_color, seed_color)
        for r, c in frame["interior"]:
            out[r][c] = target
    return out


def _rival_seed_echo(grid):
    """Wrong rule: spread the seed's own color, ignoring legend targets."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = deepcopy(grid)
    for frame in info["frames"]:
        seed_color = frame["seed"][2]
        for r, c in frame["interior"]:
            out[r][c] = seed_color
    return out


def _rival_first_legend_target(grid):
    """Wrong rule: use the leftmost legend target for every room."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = deepcopy(grid)
    target = info["first_legend_target"]
    for frame in info["frames"]:
        for r, c in frame["interior"]:
            out[r][c] = target
    return out


def _rival_seed_cell_only(grid):
    """Wrong rule: recolor only the seed cell instead of the full interior."""
    info, errors = _analyse(grid)
    if errors:
        raise ValueError("; ".join(errors))
    out = deepcopy(grid)
    for frame in info["frames"]:
        r, c, source = frame["seed"]
        out[r][c] = info["mapping"][source]
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "seed_echo": _rival_seed_echo,
    "first_legend_target": _rival_first_legend_target,
    "seed_cell_only": _rival_seed_cell_only,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def _witness_mapped_seed_changes(grid) -> bool:
    info, errors = _analyse(grid)
    return not errors and any(source != target for source, target in info["used_mappings"])


def _witness_full_interior(grid) -> bool:
    info, errors = _analyse(grid)
    return not errors and any(len(frame["interior"]) > 1 for frame in info["frames"])


def _witness_multiple_targets(grid) -> bool:
    info, errors = _analyse(grid)
    return not errors and len({target for _source, target in info["used_mappings"]}) >= 2


def _witness_unused_legend(grid) -> bool:
    info, errors = _analyse(grid)
    return not errors and bool(info["unused_sources"])


def _witness_canonical_profile(grid) -> bool:
    info, errors = _analyse(grid)
    if errors:
        return False
    return (info["grid_h"], info["grid_w"], info["palette_size"]) in {
        (10, 12, 6), (11, 13, 8), (12, 14, 8)
    }


SEMANTIC_WITNESSES: dict[str, Callable[[Any], bool]] = {
    "mapped_seed_changes_color": _witness_mapped_seed_changes,
    "full_interior_fill_observable": _witness_full_interior,
    "multiple_room_targets": _witness_multiple_targets,
    "unused_legend_distractor": _witness_unused_legend,
    "canonical_profile_anchor": _witness_canonical_profile,
}
WITNESS_RIVALS = {
    "mapped_seed_changes_color": ["seed_echo"],
    "full_interior_fill_observable": ["seed_cell_only"],
    "multiple_room_targets": ["first_legend_target"],
    "unused_legend_distractor": ["first_legend_target"],
}
BRANCH_WITNESSES = {"canonical_profile_anchor"}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    source_targets: dict[int, set[int]] = {}
    competitor_survives = {name: True for name in LESSON_COMPETITORS}
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        info, errors = _analyse(pair["input"])
        if errors:
            reasons.append(f"demo {index} malformed: {errors[0]}")
            continue
        expected = rule_mirror(pair["input"])
        if pair["output"] != expected:
            reasons.append(f"demo {index} output does not match legend-driven interior fill")
        for source, target in info["used_mappings"]:
            source_targets.setdefault(source, set()).add(target)
        for name, rival in LESSON_COMPETITORS.items():
            if rival(pair["input"]) != pair["output"]:
                competitor_survives[name] = False

    # A lesson-stable anchor source is deliberately remapped between demos.
    # This is a family-level rebuttal to memorizing a fixed global color map,
    # rather than a single hard-coded competitor.
    if not any(len(targets) >= 2 for targets in source_targets.values()):
        reasons.append("demonstrations do not show one seed color mapping to different targets")

    for name, survives in competitor_survives.items():
        if survives:
            reasons.append(f"rival {name!r} matches every demonstration")

    if not isinstance(query, dict) or "input" not in query:
        reasons.append("query must contain an input grid")
    else:
        qerrors = self_check(query["input"])
        if qerrors:
            reasons.append(f"query malformed: {qerrors[0]}")
        elif "output" in query and query["output"] != rule_mirror(query["input"]):
            reasons.append("query output does not match the authoritative transform")
    return reasons
