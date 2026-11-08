"""Generator for ARC task e7a25a18 / content hash 5da2f80a4a4f.

A hollow colour-2 rectangle contains a smaller rectangular coloured key.  The
output is the frame's bounding box with the key enlarged independently in rows
and columns until it fills the frame interior.  The key may be displaced inside
the frame; its position is not copied to the output.

Four exact anchor profiles retain the canonical and earlier control geometries.
Two variable families independently draw frame/key geometry, key position, and
palette count. The eight-slot schedule puts a variable control in every three-
demonstration window. Such controls refute not only fixed 2x/quadrant rules but
also the v4 shortcut of looking up the enlargement from the frame dimensions.
"""
from __future__ import annotations

from copy import deepcopy
from itertools import product
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid


GENERATOR_ID = "5da2f80a4a4f"
TASK_ID = GENERATOR_ID
VERSION = "5.0.0"
RULE_HASH = "5501c0734c5a"

SUMMARY = (
    "A 0-background grid contains one hollow colour-2 rectangular frame and "
    "one fully coloured rectangular key strictly inside it. Extract the key's "
    "bounding box, then resize it by integer row/column replication to fill "
    "the frame interior. Return only the frame bounding box: colour-2 border "
    "plus the enlarged key. Key position inside the input frame is irrelevant."
)

INVARIANTS = [
    "exactly one complete colour-2 rectangular outline; no other colour-2 cells",
    "all non-{0,2} cells form one full rectangular key strictly inside the frame",
    "key height and width divide the corresponding frame-interior dimensions",
    "row and column enlargement factors are at least 2, so the task is non-identity",
    "the key uses at least two colours and no non-zero cells occur outside the frame",
]

EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()

# A profile is an exact observable geometry tuple:
# (frame_h, frame_w, key_h, key_w, key_offset_r, key_offset_c).
_PROFILES: tuple[dict[str, Any], ...] = (
    {
        "name": "canonical_small_offset",
        "geometry": (6, 6, 2, 2, 0, 1),
        "palette_size": 4,
    },
    {
        "name": "canonical_large_blocks",
        "geometry": (10, 10, 4, 4, 1, 1),
        "palette_size": 4,
    },
    {
        "name": "row_scale_three",
        "geometry": (8, 10, 2, 4, 2, 1),
        "palette_size": 3,
    },
    {
        "name": "column_scale_three",
        "geometry": (10, 8, 4, 2, 1, 3),
        "palette_size": 3,
    },
)
# This rival fits every canonical pair and the entire v4 generator support.
# Keep its constants independent of the expanded profile table.
_FRAME_SCALE_LOOKUP = {
    (6, 6): (2, 2), (10, 10): (2, 2),
    (8, 10): (3, 2), (10, 8): (2, 3),
}
_VARIABLE_NAMES = ("variable_wide_frame", "variable_tall_frame")
# Enumerate the small feasible set once. All frames fit every declared canvas
# override. At least six key cells allow non-quadrant controls with 2-4 colours.
# Excluding the lookup's scale creates a genuine counterexample by construction,
# not a seed search or a weakened semantic check.
_WIDE_GEOMETRIES = tuple(sorted(
    (kh * rs + 2, kw * cs + 2, kh, kw)
    for kh, kw, rs, cs in product(range(2, 6), repeat=4)
    if kh * kw > 4 and kh * rs + 2 < kw * cs + 2 <= 12
    and rs != cs
    and (rs, cs) != _FRAME_SCALE_LOOKUP.get((kh * rs + 2, kw * cs + 2), (2, 2))
))
_VARIABLE_GEOMETRIES = {
    "variable_wide_frame": _WIDE_GEOMETRIES,
    "variable_tall_frame": tuple((fw, fh, kw, kh) for fh, fw, kh, kw in _WIDE_GEOMETRIES),
}
_VARIABLE_GEOMETRY_TO_PROFILE = {
    geometry: name for name, geometries in _VARIABLE_GEOMETRIES.items()
    for geometry in geometries
}
_PROFILE_BY_NAME = {profile["name"]: profile for profile in _PROFILES}
_PROFILE_BY_NAME.update({name: {"name": name} for name in _VARIABLE_NAMES})
_GEOMETRY_TO_PROFILE = {
    tuple(profile["geometry"]): profile["name"] for profile in _PROFILES
}
# Literal names keep AXES statically inspectable by the inherited linter.
SCENE_PROFILES = (
    "canonical_small_offset", "canonical_large_blocks", "row_scale_three",
    "column_scale_three", "variable_wide_frame", "variable_tall_frame",
)
SCHEDULE_PROFILES = (
    "canonical_small_offset", "canonical_large_blocks", "variable_wide_frame",
    "row_scale_three", "variable_tall_frame", "column_scale_three",
    "variable_wide_frame", "variable_tall_frame",
)

AXES = {
    "grid_h": {
        "type": "int",
        "default": "scheduled canonical-weighted 12..18",
        "valid": "12..18",
    },
    "grid_w": {
        "type": "int",
        "default": "scheduled canonical-weighted 12..18",
        "valid": "12..18",
    },
    "scene_profile": {
        "type": "str",
        "default": "eight-slot anchor/control schedule",
        "valid": "|".join(SCENE_PROFILES),
    },
    "palette_size": {
        "type": "int",
        "default": "anchor 4|4|3|3; variable families independently sample 2..4",
        "valid": "2..4",
    },
}


def _validate_seed_and_sample_index(seed: Any, sample_index: Any) -> None:
    """Reject coercible public scalars before they reach keyed RNG helpers."""
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool, float, or string)")
    if type(sample_index) is not int:
        raise TypeError(
            "sample_index must be an integer (not bool, float, or string)"
        )
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the deterministic curriculum residue used by the semantic gate."""
    _validate_seed_and_sample_index(seed, sample_index)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _profile_for(sample_index: int) -> dict[str, Any]:
    return _PROFILE_BY_NAME[SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]]


def _draw_default_int(ctx, overrides, label: str, default: int, lo: int, hi: int) -> int:
    if label in overrides and overrides[label] is not None:
        return ctx.draw_int_strict(label, lo, hi)
    return ctx.draw_int_strict(label, default, default)


def _draw_default_choice(ctx, overrides, label: str, default: str, options: tuple[str, ...]) -> str:
    if label in overrides and overrides[label] is not None:
        return str(ctx.draw_choice(label, options))
    return str(ctx.draw_choice(label, (default,)))


def _validate_override_names(overrides: dict[str, Any]) -> None:
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")


def _scheduled_grid_size(profile_name: str, difficulty: str | None) -> tuple[int, int]:
    # The two canonical profiles remain 14x14 in every band so each band keeps
    # exact canonical (height, width, palette-count) support. The harder profiles
    # expand the surrounding canvas without changing the task operation.
    # Variable controls share the canonical canvas: margins cannot identify them.
    if profile_name in ("canonical_small_offset", "canonical_large_blocks", *_VARIABLE_NAMES):
        return 14, 14
    if difficulty == "easy":
        return (12, 14) if profile_name == "row_scale_three" else (14, 12)
    if difficulty == "hard":
        return (16, 18) if profile_name == "row_scale_three" else (18, 16)
    return (14, 16) if profile_name == "row_scale_three" else (16, 14)


def _is_quadrant_pattern(key: list[list[int]]) -> bool:
    """Check quadrant constancy on a 2x lattice, including odd key dimensions."""
    colours = list(dict.fromkeys(value for row in key for value in row))
    colours += [colours[-1]] * max(0, 4 - len(colours))
    kh, kw = len(key), len(key[0])
    return all(
        key[r // 2][c // 2] == colours[(0 if r < kh else 2) + (0 if c < kw else 1)]
        for r in range(2 * kh) for c in range(2 * kw)
    )


def _break_quadrant_pattern(key: list[list[int]]) -> list[list[int]]:
    """A bounded, colour-count-preserving repair for discriminative controls."""
    if not _is_quadrant_pattern(key):
        return key
    cells = [(r, c) for r in range(len(key)) for c in range(len(key[0]))]
    for i, (r, c) in enumerate(cells):
        for rr, cc in cells[i + 1:]:
            if key[r][c] == key[rr][cc]:
                continue
            key[r][c], key[rr][cc] = key[rr][cc], key[r][c]
            if not _is_quadrant_pattern(key):
                return key
            key[r][c], key[rr][cc] = key[rr][cc], key[r][c]
    raise ValueError("key has no non-quadrant permutation")


def _pattern_for(profile_name: str, kh: int, kw: int, palette: list[int], rng) -> list[list[int]]:
    """Build a full key using every colour without a fixed palette prefix."""
    n = len(palette)
    if profile_name == "canonical_large_blocks" and kh == kw == 4:
        # Canonical train/test use a 2x2 logical key whose cells are already 2x2
        # blocks. Preserve that branch while allowing 2-4 colours under override.
        logical = [palette[i % n] for i in range(4)]
        rng.shuffle(logical)
        return [
            [logical[(r // 2) * 2 + (c // 2)] for c in range(4)]
            for r in range(4)
        ]

    # Guarantee coverage BEFORE shuffling. Overwriting a shuffled prefix both
    # fixes first-occurrence positions and distorts colour frequencies.
    cells = list(palette) + [rng.choice(palette) for _ in range(kh * kw - n)]
    rng.shuffle(cells)
    matrix = [cells[r * kw:(r + 1) * kw] for r in range(kh)]
    return _break_quadrant_pattern(matrix) if profile_name in _VARIABLE_NAMES else matrix


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_seed_and_sample_index(seed, sample_index)
    _validate_override_names(overrides)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = _profile_for(sample_index)
    profile_name = _draw_default_choice(
        ctx,
        overrides,
        "scene_profile",
        scheduled["name"],
        SCENE_PROFILES,
    )
    profile = _PROFILE_BY_NAME[profile_name]
    if profile_name in _VARIABLE_NAMES:
        fh, fw, kh, kw = ctx.draw_rng("relative_geometry").choice(
            _VARIABLE_GEOMETRIES[profile_name]
        )
        key_rng = ctx.draw_rng("key_position")
        key_off_r = key_rng.randint(0, fh - 2 - kh)
        key_off_c = key_rng.randint(0, fw - 2 - kw)
    else:
        fh, fw, kh, kw, key_off_r, key_off_c = profile["geometry"]

    default_h, default_w = _scheduled_grid_size(profile_name, difficulty)
    h = _draw_default_int(ctx, overrides, "grid_h", default_h, 12, 18)
    w = _draw_default_int(ctx, overrides, "grid_w", default_w, 12, 18)
    if h < fh or w < fw:
        raise ValueError(
            f"scene_profile={profile_name!r} frame {fh}x{fw} does not fit grid {h}x{w}"
        )

    if profile_name in _VARIABLE_NAMES:
        palette_size = ctx.draw_int_strict("palette_size", 2, 4)
    else:
        palette_size = _draw_default_int(
            ctx, overrides, "palette_size", int(profile["palette_size"]), 2, 4,
        )
    if palette_size > kh * kw:
        raise ValueError(
            f"palette_size={palette_size} exceeds key area {kh * kw}"
        )

    palette = list(ctx.draw_distinct_colors("key_palette", n=palette_size, exclude={0, 2}))
    pattern_rng = ctx.draw_rng("key_pattern")
    key = _pattern_for(profile_name, kh, kw, palette, pattern_rng)

    placement_rng = ctx.draw_rng("frame_position")
    r0 = placement_rng.randint(0, h - fh)
    c0 = placement_rng.randint(0, w - fw)

    grid = full_grid(h, w, 0)
    draw_rect_outline(grid, r0, c0, fh, fw, 2)
    key_r0 = r0 + 1 + key_off_r
    key_c0 = c0 + 1 + key_off_c
    for r in range(kh):
        for c in range(kw):
            grid[key_r0 + r][key_c0 + c] = key[r][c]

    findings = self_check(grid, difficulty=difficulty, meta={"overrides": ctx.recorded_draws()})
    if findings:
        raise AssertionError("generated invalid scene: " + "; ".join(findings))
    return grid


def _rectangular_grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if len(grid) > 30 or width > 30:
        return [f"grid exceeds ARC limit: {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _rectangular_grid_errors(grid)
    if errors:
        return {"errors": errors}
    h, w = len(grid), len(grid[0])
    twos = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if not twos:
        return {"errors": ["no colour-2 frame cells"]}
    r0 = min(r for r, _ in twos)
    r1 = max(r for r, _ in twos)
    c0 = min(c for _, c in twos)
    c1 = max(c for _, c in twos)
    fh, fw = r1 - r0 + 1, c1 - c0 + 1
    if fh < 4 or fw < 4:
        errors.append(f"frame too small: {fh}x{fw}")

    expected_outline = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    actual_twos = set(twos)
    missing = expected_outline - actual_twos
    extra = actual_twos - expected_outline
    if missing:
        errors.append(f"frame outline has {len(missing)} missing cell(s)")
    if extra:
        errors.append(f"found {len(extra)} colour-2 cell(s) off the frame outline")

    outside_nonzero = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 2)
        and not (r0 < r < r1 and c0 < c < c1)
    ]
    if outside_nonzero:
        errors.append(f"non-frame coloured cells outside frame: {outside_nonzero[:3]}")

    key_cells = [
        (r, c)
        for r in range(r0 + 1, r1)
        for c in range(c0 + 1, c1)
        if grid[r][c] not in (0, 2)
    ]
    if not key_cells:
        errors.append("no coloured key inside frame")
        return {
            "errors": errors,
            "height": h,
            "width": w,
            "frame": (r0, c0, r1, c1),
        }

    kr0 = min(r for r, _ in key_cells)
    kr1 = max(r for r, _ in key_cells)
    kc0 = min(c for _, c in key_cells)
    kc1 = max(c for _, c in key_cells)
    kh, kw = kr1 - kr0 + 1, kc1 - kc0 + 1
    key_matrix = [[grid[r][c] for c in range(kc0, kc1 + 1)] for r in range(kr0, kr1 + 1)]
    holes = [
        (r, c)
        for r in range(kr0, kr1 + 1)
        for c in range(kc0, kc1 + 1)
        if grid[r][c] in (0, 2)
    ]
    if holes:
        errors.append(f"key bounding box contains {len(holes)} blank/frame cell(s)")

    interior_h, interior_w = fh - 2, fw - 2
    if interior_h % kh:
        errors.append(f"key height {kh} does not divide interior height {interior_h}")
        rscale = None
    else:
        rscale = interior_h // kh
    if interior_w % kw:
        errors.append(f"key width {kw} does not divide interior width {interior_w}")
        cscale = None
    else:
        cscale = interior_w // kw
    if rscale is not None and rscale < 2:
        errors.append(f"row enlargement factor must be >=2, found {rscale}")
    if cscale is not None and cscale < 2:
        errors.append(f"column enlargement factor must be >=2, found {cscale}")

    colours = sorted({value for row in key_matrix for value in row if value not in (0, 2)})
    if len(colours) < 2:
        errors.append(f"key must use at least two colours, found {len(colours)}")

    geometry = (
        fh,
        fw,
        kh,
        kw,
        kr0 - (r0 + 1),
        kc0 - (c0 + 1),
    )
    return {
        "errors": errors,
        "height": h,
        "width": w,
        "frame": (r0, c0, r1, c1),
        "frame_h": fh,
        "frame_w": fw,
        "interior_h": interior_h,
        "interior_w": interior_w,
        "key_bbox": (kr0, kc0, kr1, kc1),
        "key_h": kh,
        "key_w": kw,
        "key_matrix": key_matrix,
        "key_offset_r": geometry[4],
        "key_offset_c": geometry[5],
        "palette_size": len(colours),
        "rscale": rscale,
        "cscale": cscale,
        "geometry": geometry,
        "scene_profile": _GEOMETRY_TO_PROFILE.get(
            geometry, _VARIABLE_GEOMETRY_TO_PROFILE.get(geometry[:4])
        ),
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def observe_overrides(grid) -> dict[str, Any]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    observed = {
        "grid_h": analysis["height"],
        "grid_w": analysis["width"],
        "palette_size": analysis["palette_size"],
    }
    if analysis.get("scene_profile") is not None:
        observed["scene_profile"] = analysis["scene_profile"]
    return observed


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The structural grammar accepted for canonical and generated inputs."""
    return self_check(grid)


def rule_mirror(grid) -> list[list[int]]:
    """Independent Python mirror for tests; canonical Racket remains authority."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("invalid input: " + "; ".join(analysis["errors"]))
    key = analysis["key_matrix"]
    rscale = analysis["rscale"]
    cscale = analysis["cscale"]
    oh, ow = analysis["frame_h"], analysis["frame_w"]
    return [
        [
            2
            if r in (0, oh - 1) or c in (0, ow - 1)
            else key[(r - 1) // rscale][(c - 1) // cscale]
            for c in range(ow)
        ]
        for r in range(oh)
    ]


def _rival_crop_frame(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return deepcopy(grid)
    r0, c0, r1, c1 = analysis["frame"]
    return [list(row[c0:c1 + 1]) for row in grid[r0:r1 + 1]]


def _rival_fixed_2x(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return deepcopy(grid)
    key = analysis["key_matrix"]
    oh, ow = 2 * analysis["key_h"] + 2, 2 * analysis["key_w"] + 2
    return [
        [
            2
            if r in (0, oh - 1) or c in (0, ow - 1)
            else key[(r - 1) // 2][(c - 1) // 2]
            for c in range(ow)
        ]
        for r in range(oh)
    ]


def _rival_frame_scale_lookup(grid) -> list[list[int]]:
    """Use v4's frame-to-scale table instead of deriving scale from the key."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return deepcopy(grid)
    rs, cs = _FRAME_SCALE_LOOKUP.get((analysis["frame_h"], analysis["frame_w"]), (2, 2))
    interior = [
        [value for value in row for _ in range(cs)]
        for row in analysis["key_matrix"] for _ in range(rs)
    ]
    border = [2] * (len(interior[0]) + 2)
    return [border[:]] + [[2, *row, 2] for row in interior] + [border[:]]


def _rival_four_quadrants(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return deepcopy(grid)
    colours: list[int] = []
    for row in analysis["key_matrix"]:
        for value in row:
            if value not in colours:
                colours.append(value)
    while len(colours) < 4:
        colours.append(colours[-1])
    oh, ow = analysis["frame_h"], analysis["frame_w"]
    ih, iw = oh - 2, ow - 2
    return [
        [
            2
            if r in (0, oh - 1) or c in (0, ow - 1)
            else colours[(0 if r - 1 < ih / 2 else 2) + (0 if c - 1 < iw / 2 else 1)]
            for c in range(ow)
        ]
        for r in range(oh)
    ]


def _rival_square_output(grid) -> list[list[int]]:
    official = rule_mirror(grid)
    if len(official) == len(official[0]):
        return official
    side = min(len(official), len(official[0]))
    return [row[:side] for row in official[:side]]


def _rival_top_left_2x2(grid) -> list[list[int]]:
    analysis = _analyze(grid)
    if analysis["errors"]:
        return deepcopy(grid)
    r0, c0, _, _ = analysis["frame"]
    guessed = [[grid[r0 + 1 + r][c0 + 1 + c] for c in range(2)] for r in range(2)]
    oh, ow = analysis["frame_h"], analysis["frame_w"]
    ih, iw = oh - 2, ow - 2
    return [
        [
            2
            if r in (0, oh - 1) or c in (0, ow - 1)
            else guessed[min(1, (r - 1) * 2 // ih)][min(1, (c - 1) * 2 // iw)]
            for c in range(ow)
        ]
        for r in range(oh)
    ]


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "crop_frame_without_enlarging": _rival_crop_frame,
    "fixed_2x_enlargement": _rival_fixed_2x,
    "four_colour_quadrants": _rival_four_quadrants,
    "always_square_output": _rival_square_output,
    "read_top_left_2x2": _rival_top_left_2x2,
    "frame_size_scale_lookup": _rival_frame_scale_lookup,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS

# These all reproduce every canonical pair: canonical frames are square, the
# scale is 2 in both directions, and the visible keys encode four quadrants.
# Generated rectangular/non-2x/non-quadrant profiles are therefore essential.
CANONICAL_SHORTCUTS = {
    "fixed_2x_enlargement": _rival_fixed_2x,
    "four_colour_quadrants": _rival_four_quadrants,
    "always_square_output": _rival_square_output,
    "frame_size_scale_lookup": _rival_frame_scale_lookup,
}


def _lawful(grid) -> dict[str, Any] | None:
    analysis = _analyze(grid)
    return analysis if not analysis["errors"] else None


def _witness_offset_key(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and (analysis["key_offset_r"], analysis["key_offset_c"]) != (0, 0))


def _witness_variable_scale(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and (analysis["rscale"] != 2 or analysis["cscale"] != 2))


def _witness_rectangular_frame(grid) -> bool:
    analysis = _lawful(grid)
    return bool(analysis and analysis["frame_h"] != analysis["frame_w"])


def _witness_nonquadrant_key(grid) -> bool:
    analysis = _lawful(grid)
    if not analysis:
        return False
    # This witness is deliberately discriminator-defined: shape/palette
    # marginals alone do not prove that the four-quadrant rival disagrees.
    return _rival_four_quadrants(grid) != rule_mirror(grid)


def _witness_frame_lookup_failure(grid) -> bool:
    return bool(_lawful(grid) and _rival_frame_scale_lookup(grid) != rule_mirror(grid))


SEMANTIC_WITNESSES = {
    "offset_key_position_is_irrelevant": _witness_offset_key,
    "scale_is_derived_from_frame": _witness_variable_scale,
    "rectangular_frame_scales_axes_independently": _witness_rectangular_frame,
    "key_is_not_always_four_distinct_quadrants": _witness_nonquadrant_key,
    "frame_dimensions_do_not_determine_scale": _witness_frame_lookup_failure,
}
WITNESS_RIVALS = {
    "offset_key_position_is_irrelevant": ["read_top_left_2x2"],
    "scale_is_derived_from_frame": ["fixed_2x_enlargement"],
    "rectangular_frame_scales_axes_independently": ["always_square_output"],
    "key_is_not_always_four_distinct_quadrants": ["four_colour_quadrants"],
    "frame_dimensions_do_not_determine_scale": ["frame_size_scale_lookup"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every three-demo window to eliminate the plausible shortcuts."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    if self_check(query["input"]):
        reasons.append("query input is outside the task grammar")

    valid_demos: list[dict[str, Any]] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        findings = self_check(demo["input"])
        if findings:
            reasons.append(f"demo {index} input is outside the task grammar: {findings[:1]}")
            continue
        expected = rule_mirror(demo["input"])
        if demo["output"] != expected:
            reasons.append(f"demo {index} output does not match resize-key-to-frame")
            continue
        valid_demos.append(demo)

    if len(valid_demos) != len(demos):
        return reasons

    survivors = []
    for name, rival in LESSON_COMPETITORS.items():
        if all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            survivors.append(name)
    if survivors:
        reasons.append(f"demonstrations leave rival rule(s) alive: {survivors}")

    if not any(_witness_variable_scale(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations never show a scale factor other than 2")
    if not any(_witness_rectangular_frame(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations never show independent row/column scaling")
    if not any(_witness_nonquadrant_key(demo["input"]) for demo in valid_demos):
        reasons.append("demonstrations never refute the four-quadrant shortcut")
    return reasons
