"""Semantic generator for ARC task d9f24cd1 / cd818a9d92d1.

The output first repeats the entire bottom guide row upward.  Gray 5 cells are
then restored at their input positions.  A gray cell whose column is marked by
a bottom-row red 2 deflects that red column one cell right: cells above the
gray are cleared in the original column, and red is painted in the right-hand
column from the top through the row immediately below the blocker.  Gray cells
outside marker columns are inert distractors and must remain gray.

Every ordinary generated scene contains both an on-column blocker and an
off-column distractor.  Marker columns are separated so every deflection is
visible rather than hidden by an adjacent marker column.
"""
from __future__ import annotations

from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "cd818a9d92d1"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "c71beb1e22d0"
EXAMPLES_NEEDED = 4

SUMMARY = (
    "Repeat the bottom guide row into every output row. Preserve every gray "
    "5 at its input position. When a gray 5 lies above a bottom-row red 2, "
    "clear that red column above the blocker and continue it one cell right "
    "from the top through the row below the blocker. Gray cells outside red "
    "marker columns are preserved distractors and do not bend a column."
)

INVARIANTS = [
    "background is 0 and the input palette is exactly a subset of {0,2,5}",
    "the bottom row contains separated red 2 markers and no gray cells",
    "at least one gray blocker is in a marker column and at least one is off-column",
    "blocker rows and columns are distinct and leave room below each blocker",
    "no off-column blocker occupies a bend destination or sits immediately left of a marker",
    "every canonical train/test input from both source rows is accepted",
]

# Each tuple is (marker_count, on-column blocker count, off-column blocker
# count).  The three canonical cue/answer relations are represented exactly;
# the compact and expanded profiles exercise the same grammar at boundaries.
BRANCH_PROFILES = {
    "compact_one_bend_one_distractor": (2, 1, 1),
    "canonical_one_bend_one_distractor": (3, 1, 1),
    "canonical_one_bend_two_distractors": (3, 1, 2),
    "canonical_two_bends_one_distractor": (3, 2, 1),
    "expanded_two_bends_two_distractors": (4, 2, 2),
    "expanded_three_bends_one_distractor": (4, 3, 1),
}
_PROFILE_BY_COUNTS = {value: key for key, value in BRANCH_PROFILES.items()}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng; explicit overrides use the full domain",
        "valid": "5..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng; explicit overrides use the full domain",
        "valid": "6..18",
    },
    "branch_profile": {
        "type": "str",
        "default": "sample-index schedule over every profile feasible for the dimensions",
        "valid": "compact_one_bend_one_distractor|canonical_one_bend_one_distractor|canonical_one_bend_two_distractors|canonical_two_bends_one_distractor|expanded_two_bends_two_distractors|expanded_three_bends_one_distractor",
    },
}

_VALID_H = (5, 16)
_VALID_W = (6, 18)
_BAND_RANGES = {
    "easy": ((5, 8), (6, 10)),
    "medium": ((7, 12), (8, 14)),
    "hard": ((10, 16), (12, 18)),
}


def _band(difficulty) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _draw_dimension(ctx, name: str, default: tuple[int, int], valid: tuple[int, int]) -> int:
    """Band-shaped defaults, but exact overrides are validated globally."""
    if ctx.overrides.get(name) is not None:
        return ctx.draw_int(name, valid[0], valid[1])
    return ctx.draw_int(name, default[0], default[1])


def _joint_placements(width: int, counts: tuple[int, int, int]):
    """All marker/on-blocker supports that leave enough inert columns."""
    n_markers, n_on, n_off = counts
    inner = tuple(range(1, width - 1))
    placements = []
    for marker_cols in combinations(inner, n_markers):
        if any(b - a < 2 for a, b in zip(marker_cols, marker_cols[1:])):
            continue
        marker_set = set(marker_cols)
        for on_cols in combinations(marker_cols, n_on):
            bend_destinations = {c + 1 for c in on_cols}
            off_candidates = tuple(
                c
                for c in inner
                if c not in marker_set
                and c not in bend_destinations
                and c + 1 not in marker_set
            )
            if len(off_candidates) >= n_off:
                placements.append((marker_cols, on_cols, off_candidates))
    return placements


def _profile_feasible(profile: str, height: int, width: int) -> bool:
    counts = BRANCH_PROFILES[profile]
    total_blockers = counts[1] + counts[2]
    return total_blockers <= height - 3 and bool(_joint_placements(width, counts))


def _analyze(grid):
    errors: list[str] = []
    result = {
        "errors": errors,
        "branch_profile": None,
        "marker_cols": (),
        "on_blockers": (),
        "off_blockers": (),
    }
    if not isinstance(grid, (list, tuple)) or not grid:
        errors.append("grid must be non-empty")
        return result
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        errors.append("rows must be non-empty")
        return result
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != w for row in grid):
        errors.append("grid must be rectangular")
        return result
    if any(
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return result
    if not (_VALID_H[0] <= h <= _VALID_H[1] and _VALID_W[0] <= w <= _VALID_W[1]):
        errors.append(
            f"dimensions {h}x{w} outside {_VALID_H[0]}..{_VALID_H[1]} x "
            f"{_VALID_W[0]}..{_VALID_W[1]}"
        )

    palette = {value for row in grid for value in row}
    if not palette <= {0, 2, 5}:
        errors.append(f"input palette must be a subset of {{0,2,5}}, got {sorted(palette)}")
    if any(value not in (0, 2) for value in grid[-1]):
        errors.append("bottom guide row may contain only background 0 and marker 2")

    marker_cols = tuple(c for c, value in enumerate(grid[-1]) if value == 2)
    if len(marker_cols) < 2:
        errors.append(f"expected at least two bottom-row markers, found {len(marker_cols)}")
    if any(c >= w - 1 for c in marker_cols):
        errors.append("a marker in the last column cannot bend right")
    if any(b - a < 2 for a, b in zip(marker_cols, marker_cols[1:])):
        errors.append("marker columns must be separated by at least one blank column")

    blockers = tuple(
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    )
    if any(r == h - 1 for r, _ in blockers):
        errors.append("gray blockers may not appear on the bottom guide row")
    if any(r < 1 or r > h - 3 for r, _ in blockers):
        errors.append("each blocker must lie in rows 1..h-3")
    if len({r for r, _ in blockers}) != len(blockers):
        errors.append("blocker rows must be distinct")
    if len({c for _, c in blockers}) != len(blockers):
        errors.append("blocker columns must be distinct")

    marker_set = set(marker_cols)
    on_blockers = tuple((r, c) for r, c in blockers if c in marker_set)
    off_blockers = tuple((r, c) for r, c in blockers if c not in marker_set)
    if not on_blockers:
        errors.append("expected at least one on-column blocker")
    if not off_blockers:
        errors.append("expected at least one off-column gray distractor")
    bend_destinations = {c + 1 for _, c in on_blockers}
    bad_off = [(r, c) for r, c in off_blockers if c in bend_destinations]
    if bad_off:
        errors.append(f"off-column blockers occupy bend destinations: {bad_off}")

    counts = (len(marker_cols), len(on_blockers), len(off_blockers))
    profile = _PROFILE_BY_COUNTS.get(counts)
    if profile is None:
        errors.append(f"unsupported marker/on/off count tuple {counts}")

    result.update(
        {
            "branch_profile": profile,
            "marker_cols": marker_cols,
            "on_blockers": on_blockers,
            "off_blockers": off_blockers,
            "counts": counts,
        }
    )
    return result


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or branch-hiding scenes while accepting all canonicals."""
    return list(_analyze(grid)["errors"])


def observe_overrides(grid) -> dict[str, object]:
    """Recover every declared axis exactly from the returned grid itself."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "branch_profile": analysis["branch_profile"],
    }


def rule_mirror(grid):
    """Independent Python mirror used only for tests; Racket remains authority."""
    h, w = len(grid), len(grid[0])
    bottom = list(grid[-1])
    out = [bottom[:] for _ in range(h)]
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 5:
                continue
            out[r][c] = 5
            if bottom[c] != 2:
                continue
            for rr in range(0, min(h, r + 2)):
                if rr < r:
                    out[rr][c] = 0
                if rr == r:
                    out[rr][c] = 5
                if c + 1 < w:
                    out[rr][c + 1] = 2
    return out


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")

    band = _band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )

    requested_profile = overrides.get("branch_profile")
    if requested_profile is not None and requested_profile not in BRANCH_PROFILES:
        raise ValueError(
            f"unknown branch_profile {requested_profile!r}; valid: {tuple(BRANCH_PROFILES)}"
        )

    h_default, w_default = _BAND_RANGES[band]
    if requested_profile is not None:
        n_markers, n_on, n_off = BRANCH_PROFILES[requested_profile]
        min_h = n_on + n_off + 3
        # Find the true minimum width for a visible, shortcut-rebutting joint
        # placement rather than relying on marker spacing alone.
        min_w = next(
            width
            for width in range(_VALID_W[0], _VALID_W[1] + 1)
            if _joint_placements(width, (n_markers, n_on, n_off))
        )
        if overrides.get("grid_h") is None:
            h_default = (max(h_default[0], min_h), max(h_default[1], min_h))
        if overrides.get("grid_w") is None:
            w_default = (max(w_default[0], min_w), max(w_default[1], min_w))

    h = _draw_dimension(ctx, "grid_h", h_default, _VALID_H)
    w = _draw_dimension(ctx, "grid_w", w_default, _VALID_W)

    feasible = tuple(
        profile
        for profile in BRANCH_PROFILES
        if _profile_feasible(profile, h, w)
    )
    if requested_profile is not None:
        if requested_profile not in feasible:
            raise ValueError(
                f"branch_profile {requested_profile!r} is incompatible with grid {h}x{w}"
            )
        profile = ctx.draw_choice("branch_profile", (requested_profile,))
    else:
        if not feasible:
            raise ValueError(f"no branch profile is feasible for grid {h}x{w}")
        # Deterministic coverage schedule: every feasible semantic profile gets
        # positive support instead of relying on an unlucky random draw.
        scheduled = feasible[sample_index % len(feasible)]
        profile = ctx.draw_choice("branch_profile", (scheduled,))

    counts = BRANCH_PROFILES[profile]
    placement_rng = ctx.draw_rng("placement")
    placements = _joint_placements(w, counts)
    marker_cols, on_cols, off_candidates = placement_rng.choice(placements)
    off_cols = tuple(sorted(placement_rng.sample(list(off_candidates), counts[2])))

    blocker_rows = placement_rng.sample(list(range(1, h - 2)), counts[1] + counts[2])
    placement_rng.shuffle(blocker_rows)
    on_rows = blocker_rows[: counts[1]]
    off_rows = blocker_rows[counts[1] :]

    grid = full_grid(h, w, 0)
    for c in marker_cols:
        grid[h - 1][c] = 2
    for r, c in zip(on_rows, on_cols):
        grid[r][c] = 5
    for r, c in zip(off_rows, off_cols):
        grid[r][c] = 5

    errors = self_check(grid, difficulty=band)
    if errors:
        raise AssertionError("internal generator error: " + "; ".join(errors))
    return grid
