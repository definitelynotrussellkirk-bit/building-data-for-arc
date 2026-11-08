"""Semantic generator for ARC task 5295bc5ff1cb.

The lower-right cell identifies a cover color.  The non-cover prefix of the
first row and the non-cover prefix of the first column delimit a visible
top-left periodic pattern.  Discover its smallest column and row periods,
shift the pattern one column left, and tile it across the whole output grid,
replacing the right and bottom cover regions.
"""
from __future__ import annotations

from functools import lru_cache

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "5295bc5ff1cb"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "e3633abbbdea"
SUMMARY = "Infer the smallest 2-D period of a top-left pattern, shift it one column left, and tile it over the cover region."

INVARIANTS = [
    "the lower-right cell supplies a cover color absent from the visible pattern rectangle",
    "the first cover in column zero determines the visible pattern height",
    "the first cover in row zero determines the visible pattern width",
    "the smallest period of the first-row prefix determines the column period",
    "the smallest repetition of the visible period-width rows determines the row period",
    "the output samples the periodic source at row modulo row-period and column-plus-one modulo column-period",
]

PUBLIC_PROFILES = ("public_train_1", "public_train_2", "public_train_3", "public_test_1")
PERIOD_PROFILES = (
    "period_2x2", "period_2x3", "period_3x2", "period_3x3",
    "period_2x4", "period_4x2", "period_3x4", "period_4x3",
)
COVER_PROFILES = ("thin_bottom_cover", "thin_right_cover", "minimal_cover", "large_cover")
GENERAL_PROFILES = PERIOD_PROFILES + COVER_PROFILES
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "uniform rng over four linked public and twelve generalized periodic lessons",
        "valid": "|".join(SCENE_PROFILES),
    }
}


_PUBLIC_INPUTS = {
    "public_train_1": (
        "63636361", "36363631", "63636361", "36363631",
        "63636361", "36363631", "63636361", "11111111",
    ),
    "public_train_2": (
        "67676763333", "76767673333", "67676763333", "76767673333",
        "67676763333", "76767673333", "67676763333", "33333333333",
        "33333333333", "33333333333", "33333333333",
    ),
    "public_train_3": (
        "545456", "454546", "545456", "454546", "545456", "666666",
    ),
    "public_test_1": (
        "857857857857333333", "578578578578333333", "857857857857333333",
        "578578578578333333", "857857857857333333", "578578578578333333",
        "857857857857333333", "578578578578333333", "857857857857333333",
        "578578578578333333", "857857857857333333", "578578578578333333",
        "333333333333333333", "333333333333333333", "333333333333333333",
        "333333333333333333", "333333333333333333", "333333333333333333",
    ),
}
_PUBLIC_SIGNATURES = {
    tuple(tuple(int(value) for value in row) for row in mask): profile
    for profile, mask in _PUBLIC_INPUTS.items()
}
_PERIOD_TO_PROFILE = {
    (2, 2): "period_2x2",
    (2, 3): "period_2x3",
    (3, 2): "period_3x2",
    (3, 3): "period_3x3",
    (2, 4): "period_2x4",
    (4, 2): "period_4x2",
    (3, 4): "period_3x4",
    (4, 3): "period_4x3",
}


def _band(difficulty):
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return difficulty
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def _validate_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid must have non-empty rows"], 0, 0
    height, width = len(grid), len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"], height, width
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], height, width
    return [], height, width


def _smallest_col_period(prefix):
    for period in range(1, len(prefix) + 1):
        if all(value == prefix[index % period] for index, value in enumerate(prefix)):
            return period
    raise AssertionError("finite sequence always has a period")


def _smallest_row_period(grid, top_h, col_period):
    for period in range(1, top_h + 1):
        if all(
            grid[row][col] == grid[row % period][col]
            for row in range(top_h)
            for col in range(col_period)
        ):
            return period
    raise AssertionError("finite matrix always has a row period")


def _classify_general(info):
    height, width = info["height"], info["width"]
    bottom_cover = height - info["top_h"]
    right_cover = width - info["prefix_width"]
    if bottom_cover >= max(2, height // 2) and right_cover >= max(2, width // 2):
        return "large_cover"
    if bottom_cover == 1 and right_cover == 1:
        return "minimal_cover"
    if bottom_cover == 1:
        return "thin_bottom_cover"
    if right_cover == 1:
        return "thin_right_cover"
    return _PERIOD_TO_PROFILE.get((info["row_period"], info["col_period"]))


def _analysis(grid):
    errors, height, width = _validate_grid(grid)
    result = {"errors": errors, "height": height, "width": width, "scene_profile": None}
    if errors:
        return result
    cover = grid[-1][-1]
    top_h = 0
    while top_h < height and grid[top_h][0] != cover:
        top_h += 1
    prefix_width = 0
    while prefix_width < width and grid[0][prefix_width] != cover:
        prefix_width += 1
    if not 1 <= top_h < height:
        errors.append("first column must contain a non-empty pattern followed by cover")
    if not 2 <= prefix_width < width:
        errors.append("first row must contain a shifting pattern of width at least two followed by cover")
    if top_h * prefix_width < 6:
        errors.append("visible pattern rectangle is too small to teach periodic continuation")
    if errors:
        return result
    if any(grid[row][col] == cover for row in range(top_h) for col in range(prefix_width)):
        errors.append("cover color may not occur inside the visible pattern rectangle")
    if any(
        grid[row][col] != cover
        for row in range(height)
        for col in range(width)
        if row >= top_h or col >= prefix_width
    ):
        errors.append("cells outside the visible top-left pattern rectangle must be cover")
    if errors:
        return result
    prefix = list(grid[0][:prefix_width])
    col_period = _smallest_col_period(prefix)
    row_period = _smallest_row_period(grid, top_h, col_period)
    output = [
        [grid[row % row_period][(col + 1) % col_period] for col in range(width)]
        for row in range(height)
    ]
    info = {
        "cover": cover,
        "top_h": top_h,
        "prefix_width": prefix_width,
        "bottom_cover_rows": height - top_h,
        "right_cover_cols": width - prefix_width,
        "row_period": row_period,
        "col_period": col_period,
        "tile_palette": tuple(sorted({grid[row][col] for row in range(row_period) for col in range(col_period)})),
        "output": output,
    }
    signature = tuple(tuple(row) for row in grid)
    profile = _PUBLIC_SIGNATURES.get(signature) or _classify_general(result | info)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared periodic lesson")
    if output == [list(row) for row in grid]:
        errors.append("lesson must produce a visible shifted-and-filled output")
    result.update(info)
    result.update({"scene_profile": profile, "errors": errors})
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
    info = _analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    return [row[:] for row in info["output"]]


def _dimensions(rng, band):
    lo, hi = {"easy": (6, 8), "medium": (9, 13), "hard": (14, 18)}[band]
    return rng.randint(lo, hi), rng.randint(lo, hi)


@lru_cache(maxsize=None)
def _fragmented_masks(row_period, col_period):
    """Return maximally fragmented binary tiles with the requested periods."""
    if row_period == 1:
        mask = tuple(tuple(col == col_period - 1 for col in range(col_period)) for _ in range(1))
        return (mask,)
    candidates = []
    best = -1
    for bits in range(1, 1 << (row_period * col_period)):
        mask = tuple(
            tuple(bool(bits & (1 << (row * col_period + col))) for col in range(col_period))
            for row in range(row_period)
        )
        if _smallest_col_period(mask[0]) != col_period:
            continue
        if _smallest_row_period(mask, row_period, col_period) != row_period:
            continue
        if any(
            mask[row][col] and (
                mask[(row + 1) % row_period][col]
                or mask[row][(col + 1) % col_period]
            )
            for row in range(row_period)
            for col in range(col_period)
        ):
            continue
        score = sum(sum(row) for row in mask)
        if score * 2 >= row_period * col_period:
            continue
        if score > best:
            best, candidates = score, [mask]
        elif score == best:
            candidates.append(mask)
    if not candidates:
        raise RuntimeError("no fragmented tile realizes requested period")
    return tuple(candidates)


def _fundamental_tile(rng, row_period, col_period, cover):
    colors = [color for color in range(1, 10) if color != cover]
    rng.shuffle(colors)
    background, accent = colors[:2]
    mask = rng.choice(_fragmented_masks(row_period, col_period))
    return [
        [accent if mask[row][col] else background for col in range(col_period)]
        for row in range(row_period)
    ]


def _general_grid(rng, profile, band):
    height, width = _dimensions(rng, band)
    if profile in PERIOD_PROFILES:
        row_period, col_period = next(period for period, name in _PERIOD_TO_PROFILE.items() if name == profile)
        bottom_cover = 2
        right_cover = 2
    else:
        row_period, col_period = rng.choice(((2, 2), (2, 3), (3, 2), (3, 3)))
        if profile == "minimal_cover":
            bottom_cover = right_cover = 1
        elif profile == "thin_bottom_cover":
            bottom_cover = 1
            right_cover = rng.randint(2, min(4, width - col_period))
        elif profile == "thin_right_cover":
            right_cover = 1
            bottom_cover = rng.randint(2, min(4, height - row_period))
        elif profile == "large_cover":
            bottom_cover = height - max(row_period, 3)
            right_cover = width - max(col_period, 3)
        else:
            raise ValueError(f"unknown scene_profile: {profile!r}")
    top_h = height - bottom_cover
    prefix_width = width - right_cover
    if top_h < row_period or prefix_width < col_period:
        raise RuntimeError("profile geometry cannot contain its fundamental tile")
    cover = rng.randint(1, 9)
    tile = _fundamental_tile(rng, row_period, col_period, cover)
    grid = [[cover for _ in range(width)] for _ in range(height)]
    for row in range(top_h):
        for col in range(prefix_width):
            grid[row][col] = tile[row % row_period][col % col_period]
    return grid


def _public_grid(profile):
    return [[int(value) for value in row] for row in _PUBLIC_INPUTS[profile]]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    context = gen_ctx(
        seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID,
        difficulty=difficulty, overrides=overrides,
    )
    profile = context.draw_choice("scene_profile", list(SCENE_PROFILES))
    rng = context.draw_rng("layout")
    grid = _public_grid(profile) if profile in PUBLIC_PROFILES else _general_grid(rng, profile, _band(difficulty))
    observed = observe_overrides(grid)
    if observed != {"scene_profile": profile}:
        raise RuntimeError(f"profile construction mismatch: {profile!r} -> {observed!r}")
    return grid


def self_check(grid, *, difficulty=None, meta=None):
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
            errors.append(f"requested scene_profile {requested}, observed {info['scene_profile']}")
    return errors
