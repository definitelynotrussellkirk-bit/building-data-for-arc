"""Generator for ARC task ``f59691ac00f3``.

The input is a color-7 board whose only non-background cells are 2/5 seeds in
row 0.  The Racket rule grows a downward diagonal cellular automaton: for each
cell below row 0, read the upper-left and upper-right parents; if either parent
is background, leave the cell background; if both parents are equal, write the
opposite 2/5 color; otherwise copy the right parent.

For the legal palette {2, 5}, the color table is also exactly "opposite of the
left parent, gated by both parents being present".  The generator deliberately
covers all four parent-pair witnesses and records that answer-equivalent
shortcut instead of pretending the canonical wording uniquely identifies one
Boolean formulation.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f59691ac00f3"
VERSION = "3.0.0"  # distribution break: exact observable axes, canonical all-one-color seeds, no invalid textures
TASK_ID = "f59691ac00f3"
RULE_HASH = "343570d857e4"  # sha256[:12] of whitespace-normalized canonical program_solution

SUMMARY = (
    "Color-7 background grid. Row 0 contains a lawful 2/5 seed pattern and "
    "all lower rows start as 7. For each row r>0 and column c, read the two "
    "diagonal parents lp=(r-1,c-1) and rp=(r-1,c+1), using 7 outside the "
    "grid. If either parent is 7, keep 7. If lp==rp, write the opposite "
    "2/5 color; otherwise write rp. Generated lessons always contain at "
    "least one active parent pair, so the output is never identical to the "
    "input."
)

INVARIANTS = [
    "rectangular grid, 3..8 rows and 5..16 columns",
    "input palette is exactly a subset of {2, 5, 7}, with 7 as background",
    "only row 0 may contain seed colors 2 or 5; every lower input row is all 7",
    "row 0 contains at least two seeds and at least one pair exactly two columns apart",
    "both one-color canonical branches and mixed-color branches are lawful",
]

SEED_PROFILES = ("same_2", "same_5", "alternating", "mixed")
SUPPORT_MODES = ("single_parity", "dual_parity")
PLACEMENTS = ("left", "center", "right", "free")

_H_LO, _H_HI = 3, 8
_W_LO, _W_HI = 5, 16
_CHAIN_LO, _CHAIN_HI = 2, 7
_PROFILE_MIN_LENGTH = {
    "same_2": 2,
    "same_5": 2,
    "alternating": 3,
    "mixed": 5,
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "band rng 3..4 easy, 4..6 medium, 5..8 hard",
        "valid": "3..8",
    },
    "grid_w": {
        "type": "int",
        "default": "band rng 5..9 easy, 7..13 medium, 10..16 hard; grows when an explicit motif needs room",
        "valid": "5..16",
    },
    "chain_length": {
        "type": "int",
        "default": "rng among lengths feasible for the selected seed profile and width",
        "valid": "2..7",
    },
    "seed_profile": {
        "type": "str",
        "default": "rng across all four linked parent-pair profiles",
        "valid": "|".join(SEED_PROFILES),
    },
    "support_mode": {
        "type": "str",
        "default": "rng single parity (spaced seeds) or dual parity (dense run)",
        "valid": "|".join(SUPPORT_MODES),
    },
    "placement": {
        "type": "str",
        "default": "rng among structurally distinguishable left/center/right/free placements",
        "valid": "|".join(PLACEMENTS),
    },
}


def _strict_int(value, name):
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer, got {value!r}")
    return value


def _banded_int(ctx, overrides, label, lo, hi, valid_lo, valid_hi):
    """Difficulty shapes defaults only; exact overrides use the full contract."""
    if overrides.get(label) is not None:
        return ctx.draw_int(label, valid_lo, valid_hi)
    return ctx.draw_int(label, lo, hi)


def _span(chain_length, support_mode):
    # One parity uses columns s,s+2,...; dual parity adds s+1,s+3,...
    return 2 * chain_length - (1 if support_mode == "single_parity" else 0)


def _placement_min_slack(placement):
    return {"left": 0, "right": 1, "center": 2, "free": 3}[placement]


def _placement_starts(width, span, placement):
    slack = width - span
    if slack < 0:
        return []
    anchors = {0, slack, slack // 2}
    if placement == "left":
        return [0]
    if placement == "right":
        return [slack] if slack >= 1 else []
    if placement == "center":
        center = slack // 2
        return [center] if slack >= 2 and center not in {0, slack} else []
    return [start for start in range(slack + 1) if start not in anchors]


def _profile_sequence(profile, length, rng):
    if profile == "same_2":
        return [2] * length
    if profile == "same_5":
        return [5] * length
    if profile == "alternating":
        first = rng.choice((2, 5))
        second = 7 - first
        return [first if i % 2 == 0 else second for i in range(length)]

    # Every variant below already contains 22, 25, 55, and 52 transitions.
    base = [2, 2, 5, 5, 2]
    variants = (
        base,
        [7 - value for value in base],
        list(reversed(base)),
        [7 - value for value in reversed(base)],
    )
    seq = list(rng.choice(variants))
    while len(seq) < length:
        seq.append(rng.choice((2, 5)))
    return seq


def _pair_profile(sequences):
    pairs = {
        (seq[i], seq[i + 1])
        for seq in sequences
        for i in range(len(seq) - 1)
    }
    if pairs == {(2, 2)}:
        return "same_2"
    if pairs == {(5, 5)}:
        return "same_5"
    if pairs == {(2, 5), (5, 2)}:
        return "alternating"
    if pairs == {(2, 2), (2, 5), (5, 2), (5, 5)}:
        return "mixed"
    return None


def _generated_signature(grid):
    """Recover every exact semantic axis from a grid produced by generate().

    Canonical inputs are intentionally broader than the generated motif family,
    so this returns an empty mapping for lawful but non-canonicalized seed rows.
    """
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return {}
    if any(value != 7 for row in grid[1:] for value in row):
        return {}
    top = grid[0]
    active = [c for c, value in enumerate(top) if value in (2, 5)]
    if len(active) < 2 or any(value not in (2, 5, 7) for value in top):
        return {}
    start, end = active[0], active[-1]
    dense = active == list(range(start, end + 1))
    spaced = active == list(range(start, end + 1, 2))
    if dense:
        support_mode = "dual_parity"
        sequences = [
            [top[c] for c in range(start, end + 1, 2)],
            [top[c] for c in range(start + 1, end + 1, 2)],
        ]
        if len(sequences[0]) != len(sequences[1]):
            return {}
    elif spaced:
        support_mode = "single_parity"
        sequences = [[top[c] for c in active]]
    else:
        return {}

    length = len(sequences[0])
    profile = _pair_profile(sequences)
    if profile is None or not (_CHAIN_LO <= length <= _CHAIN_HI):
        return {}
    span = end - start + 1
    slack = len(top) - span
    if start == 0:
        placement = "left"
    elif slack >= 1 and start == slack:
        placement = "right"
    elif slack >= 2 and start == slack // 2 and start not in {0, slack}:
        placement = "center"
    elif start in _placement_starts(len(top), span, "free"):
        placement = "free"
    else:
        return {}
    return {
        "chain_length": length,
        "seed_profile": profile,
        "support_mode": support_mode,
        "placement": placement,
    }


def observe_overrides(grid):
    """Exact values recoverable from the returned grid, not request metadata."""
    return _generated_signature(grid)


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the full lawful task envelope, including every canonical input."""
    if not grid or not grid[0]:
        return ["grid must be non-empty"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return ["grid must be rectangular"]

    errors = []
    height = len(grid)
    if not (_H_LO <= height <= _H_HI and _W_LO <= width <= _W_HI):
        errors.append(
            f"dimensions {height}x{width} outside declared "
            f"{_H_LO}..{_H_HI} x {_W_LO}..{_W_HI}"
        )
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("all cells must be integer ARC colors 0..9")
    if any(value != 7 for row in grid[1:] for value in row):
        errors.append("every input row below row 0 must be background color 7")
    if any(value not in (2, 5, 7) for value in grid[0]):
        errors.append("row 0 may contain only seed colors 2/5 and background 7")

    active = [c for c, value in enumerate(grid[0]) if value in (2, 5)]
    if len(active) < 2:
        errors.append("row 0 must contain at least two 2/5 seeds")
    active_set = set(active)
    if not any(c + 2 in active_set for c in active):
        errors.append(
            "row 0 has no seed pair two columns apart, so the canonical rule "
            "would leave the input unchanged"
        )
    return errors


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {unknown}; valid axes: {sorted(AXES)}")

    # Validate exact raw values before feasibility filtering so errors are loud
    # and do not silently coerce booleans/floats into integer axes.
    explicit_width = overrides.get("grid_w")
    if explicit_width is not None:
        explicit_width = _strict_int(explicit_width, "grid_w")
        if not (_W_LO <= explicit_width <= _W_HI):
            raise ValueError(f"grid_w {explicit_width} outside {_W_LO}..{_W_HI}")
    explicit_length = overrides.get("chain_length")
    if explicit_length is not None:
        explicit_length = _strict_int(explicit_length, "chain_length")
        if not (_CHAIN_LO <= explicit_length <= _CHAIN_HI):
            raise ValueError(
                f"chain_length {explicit_length} outside {_CHAIN_LO}..{_CHAIN_HI}"
            )
    explicit_placement = overrides.get("placement")
    if explicit_placement is not None and explicit_placement not in PLACEMENTS:
        raise ValueError(f"placement {explicit_placement!r} not in {PLACEMENTS}")
    explicit_profile = overrides.get("seed_profile")
    if explicit_profile is not None and explicit_profile not in SEED_PROFILES:
        raise ValueError(f"seed_profile {explicit_profile!r} not in {SEED_PROFILES}")
    explicit_support = overrides.get("support_mode")
    if explicit_support is not None and explicit_support not in SUPPORT_MODES:
        raise ValueError(f"support_mode {explicit_support!r} not in {SUPPORT_MODES}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    if band == "easy":
        h_lo, h_hi, w_lo, w_hi = 3, 4, 5, 9
    elif band == "hard":
        h_lo, h_hi, w_lo, w_hi = 5, 8, 10, 16
    else:
        h_lo, h_hi, w_lo, w_hi = 4, 6, 7, 13

    height = _banded_int(
        ctx, overrides, "grid_h", h_lo, h_hi, _H_LO, _H_HI
    )

    # Enumerate the small exact feasibility space first. This makes every
    # single-axis override valid and every incompatible combination reject
    # explicitly, rather than drawing an impossible companion and clamping it.
    triples = []
    for profile in SEED_PROFILES:
        if explicit_profile is not None and profile != explicit_profile:
            continue
        for support_mode in SUPPORT_MODES:
            if explicit_support is not None and support_mode != explicit_support:
                continue
            for length in range(_PROFILE_MIN_LENGTH[profile], _CHAIN_HI + 1):
                if explicit_length is not None and length != explicit_length:
                    continue
                span = _span(length, support_mode)
                min_slack = (
                    _placement_min_slack(explicit_placement)
                    if explicit_placement is not None
                    else 0
                )
                minimum_width = max(_W_LO, span + min_slack)
                width_limit = explicit_width if explicit_width is not None else _W_HI
                if minimum_width <= width_limit:
                    triples.append((profile, support_mode, length))
    if not triples:
        raise ValueError(
            "incompatible seed_profile/support_mode/chain_length/grid_w/placement overrides"
        )

    profile_options = [p for p in SEED_PROFILES if any(t[0] == p for t in triples)]
    profile = ctx.draw_choice("seed_profile", profile_options)
    triples = [t for t in triples if t[0] == profile]

    support_options = [m for m in SUPPORT_MODES if any(t[1] == m for t in triples)]
    support_mode = ctx.draw_choice("support_mode", support_options)
    triples = [t for t in triples if t[1] == support_mode]

    lengths = sorted({t[2] for t in triples})
    if lengths != list(range(lengths[0], lengths[-1] + 1)):
        raise RuntimeError(f"internal non-contiguous feasible lengths: {lengths}")
    chain_length = ctx.draw_int("chain_length", lengths[0], lengths[-1])
    span = _span(chain_length, support_mode)

    min_slack = (
        _placement_min_slack(explicit_placement)
        if explicit_placement is not None
        else 0
    )
    minimum_width = max(_W_LO, span + min_slack)
    if explicit_width is not None:
        width = ctx.draw_int("grid_w", _W_LO, _W_HI)
        if width < minimum_width:
            raise ValueError(
                f"grid_w {width} is too small for {support_mode} "
                f"chain_length={chain_length} and placement={explicit_placement!r}; "
                f"need at least {minimum_width}"
            )
    else:
        draw_lo = max(w_lo, minimum_width)
        draw_hi = max(draw_lo, w_hi)
        if draw_hi > _W_HI:
            raise ValueError(
                f"selected motif needs width {draw_lo}, beyond declared max {_W_HI}"
            )
        width = ctx.draw_int("grid_w", draw_lo, draw_hi)

    placement_options = [
        placement
        for placement in PLACEMENTS
        if _placement_starts(width, span, placement)
    ]
    placement = ctx.draw_choice("placement", placement_options)
    starts = _placement_starts(width, span, placement)
    if not starts:
        raise RuntimeError("selected a placement with no legal start")
    if placement == "free":
        start = ctx.draw_rng("free_start").choice(starts)
    else:
        start = starts[0]

    g = full_grid(height, width, 7)
    first = _profile_sequence(
        profile, chain_length, ctx.draw_rng("first_chain_colors")
    )
    for i, value in enumerate(first):
        g[0][start + 2 * i] = value
    if support_mode == "dual_parity":
        second = _profile_sequence(
            profile, chain_length, ctx.draw_rng("second_chain_colors")
        )
        for i, value in enumerate(second):
            g[0][start + 1 + 2 * i] = value

    observed = _generated_signature(g)
    expected = {
        "chain_length": chain_length,
        "seed_profile": profile,
        "support_mode": support_mode,
        "placement": placement,
    }
    if observed != expected:
        raise RuntimeError(
            f"internal axis realization mismatch: expected {expected}, observed {observed}"
        )
    errors = self_check(g, difficulty=difficulty, meta={"overrides": overrides})
    if errors:
        raise RuntimeError(f"internal generator invariant failure: {errors}")
    return g
