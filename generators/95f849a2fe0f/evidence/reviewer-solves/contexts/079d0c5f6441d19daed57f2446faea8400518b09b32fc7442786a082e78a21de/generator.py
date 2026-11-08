"""Semantic input sampler for ARC task 95f849a2fe0f.

The authoritative rule sorts the two colored objects by color, normalizes each
object to its own top-left corner, takes the symmetric difference of the two
cell sets, and paints that XOR cyan (8) in the *shared normalized frame*.
Unlike an ordinary final crop, the authority preserves a blank leading row or
column when the XOR cancels every cell on that edge.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "95f849a2fe0f"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "0aa57664563a"
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "Two separated connected tetrominoes, red 2 and green 3, are normalized "
    "independently. The output is their symmetric difference in cyan 8, "
    "rendered from shared normalized origin (0,0), including any leading "
    "blank row or column created by cancellation."
)
INVARIANTS = [
    "input dimensions and palette match one of the three canonical profiles",
    "red 2 and green 3 each form exactly one separated 4-connected tetromino",
    "the normalized tetrominoes differ, so their symmetric difference is non-empty",
    "output coordinates stay in the shared normalized frame rather than being re-cropped",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_test_1")
GENERAL_PROFILES = ("anchored", "leading_row", "leading_col", "leading_both")
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
RECROP_WITNESS_PROFILES = ("leading_row", "leading_col", "leading_both")

# Alternating witness/non-witness profiles makes every four consecutive pairs
# contain two re-crop counterexamples. Therefore every 3-demo query rotation
# retains at least one demonstration that refutes the shortcut.
DEFAULT_SCHEDULE = (
    "leading_row", "anchored", "leading_col", "anchored", "leading_both", "anchored",
)
SCHEDULE_PROFILES = GENERAL_PROFILES

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS = []
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "cyclic lesson schedule alternating anchored XORs with leading-blank witnesses",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_CANONICAL_DIMS = ((7, 12), (7, 13), (8, 14))
_BAND_DIMS = {"easy": (7, 12), "medium": (7, 13), "hard": (8, 14)}

_PUBLIC_INPUTS = {
    "public_train_1": (
        "000000000000",
        "020000033300",
        "020000003000",
        "022000000000",
        "000000000000",
        "000000000000",
        "000000000000",
    ),
    "public_train_2": (
        "0000000000000",
        "0220000030000",
        "0022000030000",
        "0000000033000",
        "0000000000000",
        "0000000000000",
        "0000000000000",
    ),
    "public_test_1": (
        "00000000000000",
        "02200000000000",
        "02200000333000",
        "00000000030000",
        "00000000000000",
        "00000000000000",
        "00000000000000",
        "00000000000000",
    ),
}
_PUBLIC_SIGNATURES = {
    tuple(tuple(int(cell) for cell in row) for row in rows): profile
    for profile, rows in _PUBLIC_INPUTS.items()
}

# Five free tetrominoes. D4 closure below yields all 19 fixed tetrominoes.
_FREE_TETROMINOES = (
    {(0, 0), (1, 0), (2, 0), (3, 0)},                         # I
    {(0, 0), (0, 1), (1, 0), (1, 1)},                         # O
    {(0, 0), (0, 1), (0, 2), (1, 1)},                         # T
    {(0, 0), (1, 0), (2, 0), (2, 1)},                         # L/J
    {(0, 1), (0, 2), (1, 0), (1, 1)},                         # S/Z
)


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _normalize(cells):
    cells = frozenset(cells)
    if not cells:
        return frozenset()
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return frozenset((r - r0, c - c0) for r, c in cells)


def _shape_key(shape):
    return tuple(sorted(shape))


def _d4_variants(shape):
    variants = set()
    for transform in range(8):
        moved = []
        for r, c in shape:
            if transform == 0:
                point = (r, c)
            elif transform == 1:
                point = (c, -r)
            elif transform == 2:
                point = (-r, -c)
            elif transform == 3:
                point = (-c, r)
            elif transform == 4:
                point = (r, -c)
            elif transform == 5:
                point = (-r, c)
            elif transform == 6:
                point = (c, r)
            else:
                point = (-c, -r)
            moved.append(point)
        variants.add(_normalize(moved))
    return variants


_FIXED_TETROMINOES = tuple(sorted(
    {variant for free in _FREE_TETROMINOES for variant in _d4_variants(free)},
    key=_shape_key,
))
if len(_FIXED_TETROMINOES) != 19:  # import-time invariant, not sampled behavior
    raise RuntimeError("tetromino catalogue must contain exactly 19 fixed shapes")


def _xor_profile(first, second):
    xor = frozenset(first ^ second)
    if not xor:
        raise ValueError("normalized shapes must differ")
    leading_row = min(r for r, _ in xor) > 0
    leading_col = min(c for _, c in xor) > 0
    if leading_row and leading_col:
        return "leading_both"
    if leading_row:
        return "leading_row"
    if leading_col:
        return "leading_col"
    return "anchored"


def _build_pair_pools():
    pools = {profile: [] for profile in GENERAL_PROFILES}
    for first in _FIXED_TETROMINOES:
        for second in _FIXED_TETROMINOES:
            if first == second:
                continue
            profile = _xor_profile(first, second)
            pools[profile].append((first, second))
    result = {}
    for profile, pairs in pools.items():
        if not pairs:
            raise RuntimeError(f"empty tetromino pair pool for {profile}")
        result[profile] = tuple(sorted(
            pairs, key=lambda pair: (_shape_key(pair[0]), _shape_key(pair[1]))
        ))
    return result


_PAIR_POOLS = _build_pair_pools()


def _connected4(cells):
    cells = set(cells)
    if not cells:
        return False
    seen = {next(iter(cells))}
    stack = list(seen)
    while stack:
        r, c = stack.pop()
        for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if neighbor in cells and neighbor not in seen:
                seen.add(neighbor)
                stack.append(neighbor)
    return seen == cells


def _shape_grid(cells):
    cells = frozenset(cells)
    if not cells:
        return [[0]]
    height = max(r for r, _ in cells) + 1
    width = max(c for _, c in cells) + 1
    return [[8 if (r, c) in cells else 0 for c in range(width)] for r in range(height)]


def _recrop_cells(cells):
    cells = frozenset(cells)
    if not cells:
        return [[0]]
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [[8 if (r, c) in cells else 0 for c in range(c0, c1 + 1)]
            for r in range(r0, r1 + 1)]


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"], 0, 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or value not in (0, 2, 3):
                return ["input cells must be integer colors 0, 2, or 3"], height, width
    return [], height, width


def _analysis(grid):
    errors, height, width = _validate_grid(grid)
    result = {
        "errors": errors,
        "height": height,
        "width": width,
        "scene_profile": None,
    }
    if errors:
        return result

    if (height, width) not in _CANONICAL_DIMS:
        errors.append(
            f"dimensions {(height, width)} must match a canonical profile {_CANONICAL_DIMS}"
        )

    colors = {value for row in grid for value in row}
    if colors != {0, 2, 3}:
        errors.append(f"input palette must be exactly {{0, 2, 3}}, got {sorted(colors)}")

    first_cells = frozenset(
        (r, c) for r in range(height) for c in range(width) if grid[r][c] == 2
    )
    second_cells = frozenset(
        (r, c) for r in range(height) for c in range(width) if grid[r][c] == 3
    )
    for color, cells in ((2, first_cells), (3, second_cells)):
        if len(cells) != 4:
            errors.append(f"color {color} must contain exactly four cells, got {len(cells)}")
        elif not _connected4(cells):
            errors.append(f"color {color} must form one 4-connected tetromino")

    if first_cells and second_cells:
        if any(
            (r + dr, c + dc) in second_cells
            for r, c in first_cells
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        ):
            errors.append("the two colored objects must be separated by background")
        first_shape = _normalize(first_cells)
        second_shape = _normalize(second_cells)
        xor = frozenset(first_shape ^ second_shape)
        if not xor:
            errors.append("normalized tetrominoes must differ")
    else:
        first_shape = frozenset()
        second_shape = frozenset()
        xor = frozenset()

    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature)
    if profile is None and xor:
        profile = _xor_profile(first_shape, second_shape)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared normalized-XOR scene profile")

    result.update({
        "first_cells": first_cells,
        "second_cells": second_cells,
        "first_shape": first_shape,
        "second_shape": second_shape,
        "xor": xor,
        "output": _shape_grid(xor),
        "scene_profile": profile,
        "errors": errors,
    })
    return result


def canonical_profile_signature(grid):
    info = _analysis(grid)
    profile = info.get("scene_profile")
    return profile if not info["errors"] and profile in PUBLIC_PROFILES else None


def observe_overrides(grid):
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return {"scene_profile": info["scene_profile"]}


def rule_mirror(grid):
    """Independent Python mirror of the pinned Racket authority."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def recrop_xor_rival(grid):
    """Plausible wrong rule: discard blank top/left frame after XOR."""
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return _recrop_cells(info["xor"])


def strict_canonical_like(grid):
    """Accept exactly the selected task's canonical-sized lawful manifold."""
    return self_check(grid)


def _public_grid(profile):
    return [[int(cell) for cell in row] for row in _PUBLIC_INPUTS[profile]]


def _shape_dims(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _put_shape(grid, shape, color, origin):
    r0, c0 = origin
    for r, c in shape:
        grid[r0 + r][c0 + c] = color


def _general_grid(rng, profile, band):
    height, width = _BAND_DIMS[band]
    first, second = rng.choice(_PAIR_POOLS[profile])
    first_h, first_w = _shape_dims(first)
    second_h, second_w = _shape_dims(second)

    # Horizontal order is irrelevant to the rule and independently varied.
    if rng.choice((False, True)):
        left = (first, 2, first_h, first_w)
        right = (second, 3, second_h, second_w)
    else:
        left = (second, 3, second_h, second_w)
        right = (first, 2, first_h, first_w)

    gap = rng.choice((2, 3))
    total_width = left[3] + gap + right[3]
    if total_width > width:
        gap = 2
        total_width = left[3] + gap + right[3]
    spare = width - total_width
    left_col = rng.randint(0, spare)
    right_col = left_col + left[3] + gap

    # Keeping both origins below row 1 prevents accidental replay of a public
    # input while still varying vertical placement within canonical canvases.
    left_row = rng.randint(2, height - left[2])
    right_row = rng.randint(2, height - right[2])

    grid = [[0 for _ in range(width)] for _ in range(height)]
    _put_shape(grid, left[0], left[1], (left_row, left_col))
    _put_shape(grid, right[0], right[1], (right_row, right_col))
    return grid


def schedule_profile(seed, sample_index, difficulty=None):
    del seed
    _band(difficulty)  # validate the same public domain as generate()
    if isinstance(sample_index, bool) or not isinstance(sample_index, int):
        raise ValueError("sample_index must be an integer")
    return DEFAULT_SCHEDULE[sample_index % len(DEFAULT_SCHEDULE)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    band = _band(difficulty)

    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if requested is None:
        scheduled = schedule_profile(seed, sample_index, difficulty)
        profile = context.draw_choice("scene_profile", (scheduled,))
    else:
        profile = context.draw_choice("scene_profile", SCENE_PROFILES)

    if profile in PUBLIC_PROFILES:
        grid = _public_grid(profile)
    else:
        grid = _general_grid(context.draw_rng(f"layout:{band}:{profile}"), profile, band)

    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile!r} -> {observed!r}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
    if difficulty not in (None, "easy", "medium", "hard"):
        return [f"unknown difficulty: {difficulty!r}"]
    info = _analysis(grid)
    errors = list(info["errors"])
    overrides = (meta or {}).get("overrides", {}) if isinstance(meta, dict) else {}
    if overrides:
        unknown = set(overrides) - {"scene_profile"}
        if unknown:
            errors.append(f"unknown override(s): {sorted(unknown)}")
        requested = overrides.get("scene_profile")
        if requested not in SCENE_PROFILES:
            errors.append(f"unknown scene_profile: {requested!r}")
        elif not errors and info["scene_profile"] != requested:
            errors.append(
                f"requested scene_profile {requested!r}, observed {info['scene_profile']!r}"
            )
    return errors


def _has_leading_blank_frame(grid):
    info = _analysis(grid)
    return not info["errors"] and info["scene_profile"] in RECROP_WITNESS_PROFILES


def lesson_identifiable(demos, query):
    """Report a generated lesson ambiguous under any declared competitor."""
    reasons = []
    for name, competitor in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                competitor(pair["input"]) == pair["output"] for pair in demos
            )
            changes_query = competitor(query["input"]) != query["output"]
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"{name}: malformed lesson pair ({exc})")
            continue
        if fits_demos and changes_query:
            reasons.append(
                f"{name} fits every demonstration but predicts a different query output"
            )
    return reasons


SEMANTIC_WITNESSES = {"leading_blank_frame": _has_leading_blank_frame}
SEMANTIC_RIVALS = {"recrop_xor": recrop_xor_rival}
WITNESS_RIVALS = {"leading_blank_frame": ["recrop_xor"]}
CANONICAL_SHORTCUTS = {"recrop_xor": recrop_xor_rival}
LESSON_COMPETITORS = {"recrop_xor": recrop_xor_rival}
