"""Generator for ARC task 963f59bc / content hash 084de7b050a1.

The input contains blue cells (1) and singleton colored dots.  Dots are read in
row-major order.  For each dot, the rule first looks for a blue cell in the
same COLUMN; if one exists, the FIRST such blue in row-major order is paired
with the dot and the entire original blue set is reflected vertically across
the midpoint between that blue and the dot.  If no blue shares the column, the
same operation is tried horizontally using the first blue in the dot's ROW.
Dots with neither alignment do nothing.  Reflections are painted in the dot's
color, clipped cell-by-cell at the canvas edge, and later dots overwrite earlier
reflections where their painted copies overlap.

Five sequential schedule profiles deliberately expose the source-level details
that are not all identifiable from the public examples alone: connected and
disconnected blue sets, column priority on a both-aligned dot, first-match vs
nearest-anchor behavior, inert decoys, clipping, and scan-order overlap.
"""
from __future__ import annotations

from collections import deque
from typing import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "084de7b050a1"
TASK_ID = "084de7b050a1"
VERSION = "3.0.0"
RULE_HASH = "e059ff61aa1e"
EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "Colored dots reflect the entire original blue set. A dot uses the first "
    "blue in its column if one exists; otherwise it uses the first blue in its "
    "row. The blue-dot pair defines the reflection midpoint. Unaligned dots "
    "are inert, out-of-bounds reflected cells are clipped, and dots act in "
    "row-major order so later colored reflections overwrite earlier ones."
)

INVARIANTS = [
    "background is 0, every source blue cell is 1, and each colored dot is a singleton",
    "at least one dot shares a row or column with blue and changes the output",
    "all original blue cells participate, including blue cells in disconnected components",
    "a both-aligned dot uses its column because the column branch has priority",
    "the first row-major aligned blue is the reflection anchor; unaligned dots do nothing",
    "reflections clip at the boundary and later dots win overlap conflicts",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty/schedule anchored to canonical 11..14 sizes with generalized 15..16 cases",
        "valid": "11..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty/schedule anchored to canonical 11..16 widths",
        "valid": "11..16",
    },
    "n_dots": {
        "type": "int",
        "default": "schedule uses 1 or 2 decisive dots",
        "valid": "1..4",
    },
    "blue_size": {
        "type": "int",
        "default": "schedule uses canonical-like 6, 7, or 9 cells; hard also exercises 10",
        "valid": "6..10",
    },
}

# We reject unknown overrides ourselves and every declared axis is compatible
# across its full finite boundary matrix.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()

SCHEDULE_PROFILES = (
    "core_connected",
    "global_disconnected",
    "priority_first_match",
    "inert_decoy",
    "clip_overlap",
)

_DOT_COLORS = (2, 3, 4, 5, 6, 7, 8, 9)
_DIRS4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
_VALID_DIFFICULTIES = frozenset((None, "easy", "medium", "hard"))

# Prefixes 6..10 are connected.  The repeated rows/columns create multiple
# legal anchors without making the blue-dot midpoint coincide with the dot.
_CONNECTED_BANK = (
    (2, 2), (3, 2), (4, 2), (3, 3), (3, 4), (3, 5),
    (2, 5), (4, 5), (5, 3), (1, 2),
)

# Prefixes 6..10 remain disconnected and still contain repeated rows/columns.
_DISCONNECTED_BANK = (
    (2, 2), (4, 2), (3, 3), (3, 5), (2, 5), (5, 4),
    (1, 4), (4, 6), (6, 3), (1, 7),
)

_DEFAULT_DIMS = {
    "easy": {
        "core_connected": (12, 11),
        "global_disconnected": (12, 12),
        "priority_first_match": (11, 11),
        "inert_decoy": (12, 11),
        "clip_overlap": (12, 12),
    },
    "medium": {
        "core_connected": (14, 13),
        "global_disconnected": (12, 12),
        "priority_first_match": (14, 13),
        "inert_decoy": (14, 16),
        "clip_overlap": (13, 14),
    },
    "hard": {
        "core_connected": (14, 16),
        "global_disconnected": (14, 13),
        "priority_first_match": (15, 15),
        "inert_decoy": (14, 16),
        "clip_overlap": (16, 16),
    },
    None: {
        "core_connected": (12, 11),
        "global_disconnected": (14, 13),
        "priority_first_match": (11, 11),
        "inert_decoy": (14, 16),
        "clip_overlap": (12, 12),
    },
}

_DEFAULT_BLUE_SIZE = {
    "core_connected": 7,
    "global_disconnected": 9,
    "priority_first_match": 6,
    "inert_decoy": 7,
    "clip_overlap": 9,
}

_DEFAULT_DOT_COUNT = {
    "core_connected": 2,
    "global_disconnected": 1,
    "priority_first_match": 2,
    "inert_decoy": 2,
    "clip_overlap": 2,
}

_PROFILE_COLORS = {
    "core_connected": (3, 6, 4, 8),
    "global_disconnected": (6, 3, 8, 2),
    "priority_first_match": (3, 8, 6, 2),
    "inert_decoy": (2, 8, 3, 6),
    "clip_overlap": (2, 7, 5, 9),
}


def schedule_profile(seed, sample_index, difficulty=None):
    """Five-period schedule; every consecutive five-demo window covers all profiles."""
    del seed, difficulty
    return SCHEDULE_PROFILES[sample_index % len(SCHEDULE_PROFILES)]


def _validate_generate_controls(seed, sample_index, difficulty, overrides):
    """Reject scalar coercions before they can alter deterministic draw keys."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool, float, or string)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(
            "difficulty must be one of None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis: {unknown[0]}")


def _draw_exact_axis(ctx, overrides, label, default, lo, hi):
    """Honor the full declared override domain without scalar coercion."""
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default, default)


def _blue_components_from_cells(blues):
    remaining = set(blues)
    comps = []
    while remaining:
        start = min(remaining)
        q = deque([start])
        remaining.remove(start)
        comp = []
        while q:
            r, c = q.popleft()
            comp.append((r, c))
            for dr, dc in _DIRS4:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    q.append(nxt)
        comps.append(sorted(comp))
    return comps


def _blue_components(grid):
    blues = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    return _blue_components_from_cells(blues)


def _dot_effect(blues, r, c, h, w, *, row_priority=False, nearest=False):
    """Return the source-rule branch and reflected coordinates for one dot."""
    col_matches = [b for b in blues if b[1] == c]
    row_matches = [b for b in blues if b[0] == r]

    use_row = bool(row_matches) and (row_priority or not col_matches)
    if col_matches and not use_row:
        matches = col_matches
        anchor = min(matches, key=lambda b: (abs(b[0] - r), b)) if nearest else matches[0]
        pivot_sum = anchor[0] + r
        raw = [(pivot_sum - br, bc) for br, bc in blues]
        branch = "column"
    elif row_matches:
        matches = row_matches
        anchor = min(matches, key=lambda b: (abs(b[1] - c), b)) if nearest else matches[0]
        pivot_sum = anchor[1] + c
        raw = [(br, pivot_sum - bc) for br, bc in blues]
        branch = "row"
    else:
        return {
            "branch": "none",
            "both": False,
            "anchor": None,
            "matches": (),
            "raw_targets": (),
            "targets": frozenset(),
            "clipped": False,
        }

    targets = frozenset(
        (rr, cc) for rr, cc in raw if 0 <= rr < h and 0 <= cc < w
    )
    return {
        "branch": branch,
        "both": bool(col_matches and row_matches),
        "anchor": anchor,
        "matches": tuple(matches),
        "raw_targets": tuple(raw),
        "targets": targets,
        "clipped": len(targets) < len(blues),
    }


def _mirror_variant(
    grid,
    *,
    row_priority=False,
    nearest=False,
    component_only=False,
    dot_center=False,
    drop_clipped=False,
    earlier_wins=False,
    force_decoys=False,
    suppress_branches=(),
):
    """Python mirror used only for generation checks and named rival solvers."""
    if not grid or not grid[0]:
        return [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    blues = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 1
    ]
    dots = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 1)
    ]
    out = [row[:] for row in grid]
    painted_by_reflection = set()
    comps = _blue_components_from_cells(blues)
    comp_by_cell = {cell: comp for comp in comps for cell in comp}

    for dr, dc in dots:
        color = grid[dr][dc]
        effect = _dot_effect(
            blues, dr, dc, h, w,
            row_priority=row_priority,
            nearest=nearest,
        )

        if effect["branch"] == "none" and force_decoys and blues:
            anchor = min(
                blues,
                key=lambda b: (abs(b[0] - dr) + abs(b[1] - dc), b),
            )
            # A plausible "every marker acts" shortcut: reflect on whichever
            # axis is closer to the nearest blue, using the dot itself as the
            # opposite endpoint of that midpoint.
            if abs(anchor[0] - dr) >= abs(anchor[1] - dc):
                raw = [(anchor[0] + dr - br, bc) for br, bc in blues]
            else:
                raw = [(br, anchor[1] + dc - bc) for br, bc in blues]
            effect = {
                "branch": "forced",
                "anchor": anchor,
                "raw_targets": tuple(raw),
                "targets": frozenset(
                    (rr, cc)
                    for rr, cc in raw
                    if 0 <= rr < h and 0 <= cc < w
                ),
                "clipped": any(
                    not (0 <= rr < h and 0 <= cc < w) for rr, cc in raw
                ),
            }

        if effect["branch"] == "none":
            continue
        if effect["branch"] in suppress_branches:
            continue

        source_blues = blues
        if component_only and effect.get("anchor") is not None:
            source_blues = comp_by_cell[effect["anchor"]]

        if dot_center:
            if effect["branch"] == "column":
                raw = [(2 * dr - br, bc) for br, bc in source_blues]
            elif effect["branch"] == "row":
                raw = [(br, 2 * dc - bc) for br, bc in source_blues]
            else:
                raw = list(effect["raw_targets"])
        elif component_only:
            anchor = effect["anchor"]
            if effect["branch"] == "column":
                pivot_sum = anchor[0] + dr
                raw = [(pivot_sum - br, bc) for br, bc in source_blues]
            elif effect["branch"] == "row":
                pivot_sum = anchor[1] + dc
                raw = [(br, pivot_sum - bc) for br, bc in source_blues]
            else:
                raw = list(effect["raw_targets"])
        else:
            raw = list(effect["raw_targets"])

        if drop_clipped and any(
            not (0 <= rr < h and 0 <= cc < w) for rr, cc in raw
        ):
            continue

        for rr, cc in raw:
            if not (0 <= rr < h and 0 <= cc < w):
                continue
            if earlier_wins and (rr, cc) in painted_by_reflection:
                continue
            out[rr][cc] = color
            painted_by_reflection.add((rr, cc))
    return out


def _mirror(grid):
    return _mirror_variant(grid)


def _candidate_effects(blues, h, w):
    occupied = set(blues)
    candidates = []
    for r in range(h):
        for c in range(w):
            if (r, c) in occupied:
                continue
            effect = _dot_effect(blues, r, c, h, w)
            if effect["branch"] == "none":
                continue
            nearest_effect = _dot_effect(blues, r, c, h, w, nearest=True)
            row_effect = _dot_effect(blues, r, c, h, w, row_priority=True)
            candidates.append({
                "pos": (r, c),
                **effect,
                "nearest_diff": nearest_effect["targets"] != effect["targets"],
                "row_priority_diff": row_effect["targets"] != effect["targets"],
            })
    return candidates


def _choose(rng, items):
    if not items:
        raise ValueError("no candidate satisfies scheduled semantic profile")
    return items[rng.randrange(len(items))]


def _component_only_differs(blues, candidate, h, w):
    comps = _blue_components_from_cells(blues)
    if len(comps) < 2 or candidate["anchor"] is None:
        return False
    comp = next(comp for comp in comps if candidate["anchor"] in comp)
    if candidate["branch"] == "column":
        pivot_sum = candidate["anchor"][0] + candidate["pos"][0]
        comp_targets = {
            (pivot_sum - br, bc)
            for br, bc in comp
            if 0 <= pivot_sum - br < h and 0 <= bc < w
        }
    else:
        pivot_sum = candidate["anchor"][1] + candidate["pos"][1]
        comp_targets = {
            (br, pivot_sum - bc)
            for br, bc in comp
            if 0 <= br < h and 0 <= pivot_sum - bc < w
        }
    return comp_targets != set(candidate["targets"])


def _unaligned_cells(blues, h, w):
    blue_rows = {r for r, _ in blues}
    blue_cols = {c for _, c in blues}
    occupied = set(blues)
    return [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in occupied and r not in blue_rows and c not in blue_cols
    ]


def _select_profile_dots(profile, blues, h, w, n_dots, rng):
    candidates = _candidate_effects(blues, h, w)
    selected = []

    def add(candidate):
        if candidate["pos"] not in {item["pos"] for item in selected}:
            selected.append(candidate)

    if profile == "core_connected":
        columns = [
            c for c in candidates
            if c["branch"] == "column" and not c["both"] and not c["clipped"]
        ]
        rows = [
            c for c in candidates
            if c["branch"] == "row" and not c["both"] and not c["clipped"]
        ]
        add(_choose(rng, columns))
        if n_dots >= 2:
            add(_choose(rng, rows))

    elif profile == "global_disconnected":
        global_candidates = [
            c for c in candidates
            if not c["both"] and not c["clipped"]
            and _component_only_differs(blues, c, h, w)
        ]
        add(_choose(rng, global_candidates))

    elif profile == "priority_first_match":
        both = [c for c in candidates if c["both"] and c["row_priority_diff"]]
        first_match = [
            c for c in candidates
            if len(c["matches"]) >= 2 and c["nearest_diff"] and not c["both"]
        ]
        add(_choose(rng, both))
        if n_dots >= 2:
            add(_choose(rng, first_match))

    elif profile == "inert_decoy":
        active = [
            c for c in candidates
            if not c["both"] and not c["clipped"]
        ]
        add(_choose(rng, active))
        if n_dots >= 2:
            decoys = _unaligned_cells(blues, h, w)
            occupied = {item["pos"] for item in selected}
            decoys = [pos for pos in decoys if pos not in occupied]
            pos = _choose(rng, decoys)
            selected.append({"pos": pos, "branch": "none", "targets": frozenset()})

    elif profile == "clip_overlap":
        if n_dots == 1:
            clipped = [c for c in candidates if c["clipped"] and c["targets"]]
            add(_choose(rng, clipped))
        else:
            pairs = []
            for index, first in enumerate(candidates):
                for second in candidates[index + 1:]:
                    if not (first["clipped"] or second["clipped"]):
                        continue
                    overlap = set(first["targets"]) & set(second["targets"])
                    if overlap:
                        pairs.append((first, second))
            first, second = _choose(rng, pairs)
            add(first)
            add(second)
    else:  # pragma: no cover - schedule is closed and tested
        raise ValueError(f"unknown schedule profile: {profile!r}")

    # Explicit n_dots overrides may request more dots than the pedagogical
    # minimum. Fill them with active, mostly visible dots so the scene remains
    # useful and every requested dot is observable in the returned grid.
    occupied = {item["pos"] for item in selected}
    fillers = [
        c for c in candidates
        if c["pos"] not in occupied and not c["both"] and not c["clipped"]
    ]
    while len(selected) < n_dots and fillers:
        choice = _choose(rng, fillers)
        add(choice)
        occupied.add(choice["pos"])
        fillers = [c for c in fillers if c["pos"] not in occupied]

    if len(selected) < n_dots:
        decoys = [
            pos for pos in _unaligned_cells(blues, h, w)
            if pos not in {item["pos"] for item in selected}
        ]
        while len(selected) < n_dots and decoys:
            pos = _choose(rng, decoys)
            decoys.remove(pos)
            selected.append({"pos": pos, "branch": "none", "targets": frozenset()})

    if len(selected) != n_dots:
        raise ValueError(f"could not place exactly {n_dots} colored dots")
    return selected


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_generate_controls(seed, sample_index, difficulty, overrides)

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    band_key = difficulty if difficulty in ("easy", "medium", "hard") else None
    default_h, default_w = _DEFAULT_DIMS[band_key][profile]
    h = _draw_exact_axis(ctx, overrides, "grid_h", default_h, 11, 16)
    w = _draw_exact_axis(ctx, overrides, "grid_w", default_w, 11, 16)

    default_blue = _DEFAULT_BLUE_SIZE[profile]
    if difficulty == "hard" and profile == "clip_overlap":
        default_blue = 10
    blue_size = _draw_exact_axis(ctx, overrides, "blue_size", default_blue, 6, 10)
    n_dots = _draw_exact_axis(
        ctx, overrides, "n_dots", _DEFAULT_DOT_COUNT[profile], 1, 4
    )

    bank = _DISCONNECTED_BANK if profile == "global_disconnected" else _CONNECTED_BANK
    relative = list(bank[:blue_size])
    shape_h = max(r for r, _ in relative) + 1
    shape_w = max(c for _, c in relative) + 1
    placement_rng = ctx.draw_rng("placement")

    # Keep at least one outer row/column available for decoys and clipping, but
    # vary the translation whenever the requested canvas has spare room.
    max_r_shift = max(0, h - shape_h - 2)
    max_c_shift = max(0, w - shape_w - 2)

    last_error = None
    for attempt in range(24):
        r_shift = placement_rng.randint(0, max_r_shift) if max_r_shift else 0
        c_shift = placement_rng.randint(0, max_c_shift) if max_c_shift else 0
        blues = sorted((r + r_shift, c + c_shift) for r, c in relative)
        try:
            dots = _select_profile_dots(
                profile, blues, h, w, n_dots, placement_rng
            )
        except ValueError as exc:
            last_error = exc
            continue

        grid = full_grid(h, w, 0)
        for r, c in blues:
            grid[r][c] = 1
        colors = _PROFILE_COLORS[profile]
        for index, item in enumerate(dots):
            r, c = item["pos"]
            grid[r][c] = colors[index % len(colors)]

        if self_check(grid):
            last_error = ValueError(self_check(grid)[0])
            continue
        if _mirror(grid) == grid:
            last_error = ValueError("scheduled board became an identity")
            continue
        # Ordinary curriculum draws carry a profile guarantee, not merely a
        # profile-shaped layout.  This matters because clipping/overwrite or a
        # poorly placed decoy can otherwise make the intended rival
        # observationally equivalent on a particular draw.  Explicit override
        # probes intentionally relax the pedagogical minimum so every declared
        # axis value remains realizable.
        if not overrides:
            required = {
                "core_connected": (_witness_vertical, _witness_horizontal),
                "global_disconnected": (_witness_global_components,),
                "priority_first_match": (_witness_both_priority, _witness_first_match),
                "inert_decoy": (_witness_decoy,),
                "clip_overlap": (_witness_clip, _witness_overlap),
            }[profile]
            if not all(predicate(grid) for predicate in required):
                last_error = ValueError(f"{profile} profile lost a decisive semantic witness")
                continue
        return grid

    raise ValueError(f"could not realize {profile} profile: {last_error}")


def _grid_roles(grid):
    if not grid or not grid[0]:
        return [], []
    blues = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    ]
    dots = [
        (r, c, grid[r][c])
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 1)
    ]
    return blues, dots


def self_check(grid, *, difficulty=None, meta=None):
    del difficulty, meta
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty rectangle"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["grid rows must be sequences"]
    width = len(grid[0]) if grid else 0
    if width == 0 or any(len(row) != width for row in grid):
        return ["grid must be a non-empty rectangle"]
    if any(
        not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9
        for row in grid for value in row
    ):
        errors.append("ARC colors must be integer values 0..9")
        return errors

    blues, dots = _grid_roles(grid)
    if not (2 <= len(blues) <= 30):
        errors.append(f"expected 2-30 blue cells, found {len(blues)}")
    if not (1 <= len(dots) <= 10):
        errors.append(f"expected 1-10 colored dots, found {len(dots)}")
    colors = [color for _, _, color in dots]
    if len(colors) != len(set(colors)):
        errors.append("each colored dot must use a distinct singleton color")

    if blues and dots:
        blue_rows = {r for r, _ in blues}
        blue_cols = {c for _, c in blues}
        active = [
            (r, c) for r, c, _ in dots
            if r in blue_rows or c in blue_cols
        ]
        if not active:
            errors.append("at least one dot must share a row or column with blue")
        elif _mirror(grid) == [list(row) for row in grid]:
            errors.append("the active reflection must visibly change the grid")
    return errors


def strict_canonical_like(grid):
    """Task-linked grammar, intentionally broader than exact public layouts."""
    reasons = self_check(grid)
    if reasons:
        return [f"self_check: {reason}" for reason in reasons]
    blues, dots = _grid_roles(grid)
    if not (6 <= len(blues) <= 10):
        reasons.append("canonical blue-set envelope is 6..10 cells")
    if not (1 <= len(dots) <= 4):
        reasons.append("teaching distribution uses 1..4 singleton colored dots")
    if not (11 <= len(grid) <= 16 and 11 <= len(grid[0]) <= 16):
        reasons.append("canonical/generalized teaching canvas is 11..16 by 11..16")
    return reasons


def observe_overrides(grid):
    blues, dots = _grid_roles(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]) if grid else 0,
        "n_dots": len(dots),
        "blue_size": len(blues),
    }


def _features(grid):
    h, w = len(grid), len(grid[0])
    blues, dots3 = _grid_roles(grid)
    dots = [(r, c) for r, c, _ in dots3]
    effects = [(_dot_effect(blues, r, c, h, w), (r, c)) for r, c in dots]
    true_output = _mirror(grid)
    return {
        "blues": blues,
        "dots": dots,
        "effects": effects,
        "components": _blue_components_from_cells(blues),
        "true_output": true_output,
    }


def _witness_vertical(grid):
    f = _features(grid)
    return (
        any(effect["branch"] == "column" for effect, _ in f["effects"])
        and _mirror_variant(grid, suppress_branches={"column"}) != f["true_output"]
    )


def _witness_horizontal(grid):
    f = _features(grid)
    return (
        any(effect["branch"] == "row" for effect, _ in f["effects"])
        and _mirror_variant(grid, suppress_branches={"row"}) != f["true_output"]
    )


def _witness_connected(grid):
    return len(_features(grid)["components"]) == 1


def _witness_disconnected(grid):
    return len(_features(grid)["components"]) >= 2


def _witness_global_components(grid):
    f = _features(grid)
    return len(f["components"]) >= 2 and _mirror_variant(grid, component_only=True) != f["true_output"]


def _witness_both_priority(grid):
    f = _features(grid)
    return (
        any(effect["both"] for effect, _ in f["effects"])
        and _mirror_variant(grid, row_priority=True) != f["true_output"]
    )


def _witness_first_match(grid):
    f = _features(grid)
    has_multiple = any(
        effect["branch"] != "none" and len(effect["matches"]) >= 2
        for effect, _ in f["effects"]
    )
    return has_multiple and _mirror_variant(grid, nearest=True) != f["true_output"]


def _witness_decoy(grid):
    f = _features(grid)
    return (
        any(effect["branch"] == "none" for effect, _ in f["effects"])
        and _mirror_variant(grid, force_decoys=True) != f["true_output"]
    )


def _witness_clip(grid):
    f = _features(grid)
    return (
        any(effect["clipped"] for effect, _ in f["effects"] if effect["branch"] != "none")
        and _mirror_variant(grid, drop_clipped=True) != f["true_output"]
    )


def _witness_overlap(grid):
    return _mirror_variant(grid, earlier_wins=True) != _mirror(grid)


def _witness_midpoint_not_dot(grid):
    return _mirror_variant(grid, dot_center=True) != _mirror(grid)


SEMANTIC_WITNESSES = {
    "vertical_branch": _witness_vertical,
    "horizontal_branch": _witness_horizontal,
    "connected_blue_set": _witness_connected,
    "disconnected_blue_set": _witness_disconnected,
    "global_multi_component_reflection": _witness_global_components,
    "column_priority_when_both_aligned": _witness_both_priority,
    "first_matching_anchor_not_nearest": _witness_first_match,
    "unaligned_dot_is_inert": _witness_decoy,
    "cellwise_boundary_clipping": _witness_clip,
    "later_dot_wins_overlap": _witness_overlap,
    "blue_dot_midpoint_not_dot_center": _witness_midpoint_not_dot,
}

SEMANTIC_RIVALS: dict[str, Callable] = {
    "ignore_column_branch": lambda grid: _mirror_variant(grid, suppress_branches={"column"}),
    "ignore_row_branch": lambda grid: _mirror_variant(grid, suppress_branches={"row"}),
    "connected_blue_is_inert": lambda grid: (
        [row[:] for row in grid] if len(_blue_components(grid)) == 1 else _mirror(grid)
    ),
    "disconnected_blue_is_inert": lambda grid: (
        [row[:] for row in grid] if len(_blue_components(grid)) >= 2 else _mirror(grid)
    ),
    "reflect_across_dot_itself": lambda grid: _mirror_variant(grid, dot_center=True),
    "reflect_only_anchor_component": lambda grid: _mirror_variant(grid, component_only=True),
    "row_priority_when_both_aligned": lambda grid: _mirror_variant(grid, row_priority=True),
    "nearest_aligned_blue_is_anchor": lambda grid: _mirror_variant(grid, nearest=True),
    "every_colored_dot_must_act": lambda grid: _mirror_variant(grid, force_decoys=True),
    "drop_whole_reflection_if_clipped": lambda grid: _mirror_variant(grid, drop_clipped=True),
    "earlier_dot_wins_overlap": lambda grid: _mirror_variant(grid, earlier_wins=True),
}

WITNESS_RIVALS = {
    "vertical_branch": ["ignore_column_branch"],
    "horizontal_branch": ["ignore_row_branch"],
    "connected_blue_set": ["connected_blue_is_inert"],
    "disconnected_blue_set": ["disconnected_blue_is_inert"],
    "global_multi_component_reflection": ["reflect_only_anchor_component"],
    "column_priority_when_both_aligned": ["row_priority_when_both_aligned"],
    "first_matching_anchor_not_nearest": ["nearest_aligned_blue_is_anchor"],
    "unaligned_dot_is_inert": ["every_colored_dot_must_act"],
    "cellwise_boundary_clipping": ["drop_whole_reflection_if_clipped"],
    "later_dot_wins_overlap": ["earlier_dot_wins_overlap"],
    "blue_dot_midpoint_not_dot_center": ["reflect_across_dot_itself"],
}

# These source-level shortcuts fit all public canonical pairs; the scheduled
# generated profiles therefore owe explicit counterexamples to each one.
CANONICAL_SHORTCUTS = {
    "row_priority_when_both_aligned": SEMANTIC_RIVALS["row_priority_when_both_aligned"],
    "nearest_aligned_blue_is_anchor": SEMANTIC_RIVALS["nearest_aligned_blue_is_anchor"],
    "every_colored_dot_must_act": SEMANTIC_RIVALS["every_colored_dot_must_act"],
    "drop_whole_reflection_if_clipped": SEMANTIC_RIVALS["drop_whole_reflection_if_clipped"],
    "earlier_dot_wins_overlap": SEMANTIC_RIVALS["earlier_dot_wins_overlap"],
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query):
    """Every five-demo window must kill every named rival that changes the query."""
    reasons = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} lacks input/output")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} malformed: {errors[0]}")
        elif _mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with reflection rule")
    if reasons:
        return reasons

    required = {
        "global_multi_component_reflection",
        "column_priority_when_both_aligned",
        "first_matching_anchor_not_nearest",
        "unaligned_dot_is_inert",
        "cellwise_boundary_clipping",
        "later_dot_wins_overlap",
    }
    missing = [
        name for name in sorted(required)
        if not any(SEMANTIC_WITNESSES[name](pair["input"]) for pair in demos)
    ]
    if missing:
        reasons.append("demonstrations miss decisive witnesses: " + ", ".join(missing))

    for name, competitor in LESSON_COMPETITORS.items():
        consistent = all(
            competitor(pair["input"]) == pair["output"]
            for pair in demos
        )
        if consistent and competitor(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not refute rival rule: {name}")
    return reasons
