"""Generator for ARC task 444801d8 / rule family d6607fc42bcc.

Each color-1 component is a rectangular frame with one missing, non-corner
cell on either its top or bottom edge.  One colored dot lies inside the frame
in the same column as that notch.  The output fills the strict interior and
the notch with the dot color, then paints one full-frame-width row immediately
outside the notched edge.

The four distinct public inputs are all 10x10.  Their complete linked profile
includes the relative frame positions and sizes, notch side and column, and
dot offset.  Absolute translation, dot-color renaming, horizontal reflection,
and whole-scene vertical reflection are lawful nuisance variation.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "d6607fc42bcc"
VERSION = "3.0.0"
TASK_ID = "d6607fc42bcc"
RULE_HASH = "30de93f65182"

SUMMARY = (
    "A 0-background 10..18 x 10..18 grid contains one or two vertically "
    "separated color-1 rectangular frames. Each frame has exactly one "
    "non-corner notch on its top or bottom edge and exactly one interior "
    "dot in color 2..9, aligned to the notch column. The output fills the "
    "frame interior and notch with the dot color and paints one full-width "
    "row immediately outside the notched edge. The color-1 wall remains."
)

INVARIANTS = [
    "background is 0 and every color-1 component is one exact notched frame",
    "one or two frames, each 3..6 rows by 5..7 columns",
    "each frame has one non-corner top or bottom notch with projection room",
    "each frame has exactly one interior color-2..9 dot aligned to its notch",
    "two-frame scenes are vertically separated and use distinct dot colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "primary")
SEMANTIC_TEXTURES = ("top_open", "bottom_open")
HELPFUL_TEXTURES = PALETTE_KINDS + SEMANTIC_TEXTURES
DEGENERATE_TEXTURES = ()
TEXTURES = ("none",) + HELPFUL_TEXTURES

_PALETTES = {
    "default": (2, 3, 4, 5, 6, 7, 8, 9),
    "warm": (2, 3, 4, 5, 7, 9),
    "cool": (2, 6, 8, 9),
    "primary": (2, 3, 4),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 10..18",
        "valid": "10..18",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 10..18",
        "valid": "10..18",
    },
    "frame_count": {
        "type": "int",
        "default": "difficulty-aware rng 1..2",
        "valid": "1..2",
    },
    "palette_kind": {
        "type": "str",
        "default": "rng helpful",
        "valid": "|".join(PALETTE_KINDS),
    },
    "texture": {
        "type": "str",
        "default": "none",
        "valid": "|".join(TEXTURES),
    },
}

_VALID_H = (10, 18)
_VALID_W = (10, 18)
_PROFILE_PRIOR = 0.25
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# (grid_h, grid_w, frames), where each frame is
# (relative_top, relative_left, height, width, opening, notch_rel_col,
#  dot_rel_row, dot_rel_col).  Dot colors are nuisance labels.
_PROFILE_SPECS = (
    (10, 10, (
        (0, 0, 4, 5, "top", 2, 1, 2),
        (5, 3, 3, 5, "top", 2, 1, 2),
    )),
    (10, 10, (
        (0, 0, 5, 5, "top", 2, 2, 2),
    )),
    (10, 10, (
        (0, 0, 4, 5, "top", 2, 1, 2),
        (6, 3, 3, 5, "top", 2, 1, 2),
    )),
    (10, 10, (
        (0, 0, 4, 5, "top", 2, 1, 2),
        (5, 4, 4, 5, "top", 2, 1, 2),
    )),
)


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for label in ("grid_h", "grid_w", "frame_count"):
        value = overrides.get(label)
        if value is not None and type(value) is not int:
            raise ValueError(f"{label} must be an integer")
    for label in ("palette_kind", "texture"):
        value = overrides.get(label)
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{label} must be a string")
    texture = overrides.get("texture")
    palette = overrides.get("palette_kind")
    if texture in PALETTE_KINDS and palette is not None and palette != texture:
        raise ValueError(
            f"texture={texture!r} conflicts with palette_kind={palette!r}"
        )


def _coerce_grid(grid):
    return [
        [
            int(value)
            if isinstance(value, str) and value.isdigit()
            else value
            for value in row
        ]
        for row in grid
    ]


def _components_of_color(grid, color):
    h, w = len(grid), len(grid[0])
    seen = set()
    components = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for dr, dc in _CARDINAL:
                    nr, nc = cr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(tuple(sorted(cells)))
    return components


def _u_frame_records(grid):
    """Return exact one-notch color-1 frames and their interior dots."""
    frames = []
    for cells in _components_of_color(grid, 1):
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        r1 = max(r for r, _ in cells)
        c1 = max(c for _, c in cells)
        if r1 - r0 + 1 < 3 or c1 - c0 + 1 < 3:
            continue
        perimeter = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        candidates = []
        for opening, edge_r in (("top", r0), ("bottom", r1)):
            gaps = [
                c
                for c in range(c0 + 1, c1)
                if (edge_r, c) not in cells
            ]
            if (
                len(gaps) == 1
                and set(cells) == perimeter - {(edge_r, gaps[0])}
            ):
                candidates.append((opening, gaps[0]))
        if len(candidates) != 1:
            continue
        opening, gap_c = candidates[0]
        dots = [
            (r, c, grid[r][c])
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] not in (0, 1)
        ]
        frames.append({
            "bbox": (r0, c0, r1, c1),
            "opening": opening,
            "gap_c": gap_c,
            "dots": dots,
        })
    return sorted(frames, key=lambda frame: frame["bbox"][:2])


def _flip(grid, *, vertical=False, horizontal=False):
    out = [row[:] for row in grid]
    if vertical:
        out.reverse()
    if horizontal:
        out = [list(reversed(row)) for row in out]
    return out


def _raw_profile_signature(grid):
    frames = _u_frame_records(grid)
    if (
        not 1 <= len(frames) <= 2
        or len(_components_of_color(grid, 1)) != len(frames)
        or any(len(frame["dots"]) != 1 for frame in frames)
    ):
        return None
    anchor_r = min(frame["bbox"][0] for frame in frames)
    anchor_c = min(frame["bbox"][1] for frame in frames)
    profile = []
    for frame in frames:
        r0, c0, r1, c1 = frame["bbox"]
        dot_r, dot_c, _ = frame["dots"][0]
        profile.append((
            r0 - anchor_r,
            c0 - anchor_c,
            r1 - r0 + 1,
            c1 - c0 + 1,
            frame["opening"],
            frame["gap_c"] - c0,
            dot_r - r0,
            dot_c - c0,
        ))
    return len(grid), len(grid[0]), tuple(profile)


def canonical_profile_signature(grid):
    """Complete public profile, quotienting only lawful scene symmetries."""
    if (
        not isinstance(grid, (list, tuple))
        or not grid
        or not all(isinstance(row, (list, tuple)) for row in grid)
        or not grid[0]
        or any(len(row) != len(grid[0]) for row in grid)
    ):
        return None
    g = _coerce_grid(grid)
    if any(type(value) is not int for row in g for value in row):
        return None
    if self_check(g):
        return None
    variants = []
    for vertical in (False, True):
        for horizontal in (False, True):
            signature = _raw_profile_signature(
                _flip(g, vertical=vertical, horizontal=horizontal)
            )
            if signature is not None:
                variants.append(signature)
    return min(variants) if variants else None


def _draw_notched_frame(
    grid,
    r0,
    c0,
    height,
    width,
    *,
    opening,
    notch_rel_col,
    dot_rel_row,
    dot_rel_col,
    dot_color,
):
    r1, c1 = r0 + height - 1, c0 + width - 1
    for c in range(c0, c1 + 1):
        grid[r0][c] = 1
        grid[r1][c] = 1
    for r in range(r0 + 1, r1):
        grid[r][c0] = 1
        grid[r][c1] = 1
    edge_r = r0 if opening == "top" else r1
    grid[edge_r][c0 + notch_rel_col] = 0
    grid[r0 + dot_rel_row][c0 + dot_rel_col] = dot_color


def _template_from_profile(profile):
    h, w, specs = profile
    grid = full_grid(h, w, 0)
    colors = (2, 3)
    for index, spec in enumerate(specs):
        r0, c0, fh, fw, opening, gap, dot_r, dot_c = spec
        _draw_notched_frame(
            grid,
            r0 + 1,
            c0,
            fh,
            fw,
            opening=opening,
            notch_rel_col=gap,
            dot_rel_row=dot_r,
            dot_rel_col=dot_c,
            dot_color=colors[index],
        )
    return grid


def is_canonical_profile(grid):
    signature = canonical_profile_signature(grid)
    return (
        signature is not None
        and signature in _CANONICAL_PROFILE_SIGNATURES
    )


def observe_overrides(grid):
    """Observe exact semantic axes from the returned grid, never metadata."""
    try:
        g = _coerce_grid(grid)
        return {"frame_count": len(_u_frame_records(g))}
    except (TypeError, ValueError, IndexError):
        return {}


def rule_mirror(grid):
    """Python spelling of the canonical Racket rule on valid inputs."""
    g = _coerce_grid(grid)
    out = [row[:] for row in g]
    for frame in _u_frame_records(g):
        if len(frame["dots"]) != 1:
            continue
        r0, c0, r1, c1 = frame["bbox"]
        color = frame["dots"][0][2]
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if out[r][c] == 0:
                    out[r][c] = color
        edge_r = r0 if frame["opening"] == "top" else r1
        for c in range(c0 + 1, c1):
            if g[edge_r][c] == 0:
                out[edge_r][c] = color
        bar_r = r0 - 1 if frame["opening"] == "top" else r1 + 1
        for c in range(c0, c1 + 1):
            out[bar_r][c] = color
    return out


def self_check(grid, *, difficulty=None, meta=None):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid is empty or not a row sequence"]
    if not all(isinstance(row, (list, tuple)) for row in grid):
        return ["grid contains a non-row value"]
    widths = {len(row) for row in grid}
    if len(widths) != 1 or not widths or next(iter(widths)) == 0:
        return ["grid is ragged or has empty rows"]
    g = _coerce_grid(grid)
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in g
        for value in row
    ):
        return ["grid contains a non-integer or color outside 0..9"]

    h, w = len(g), len(g[0])
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append(f"grid height {h} outside {_VALID_H[0]}..{_VALID_H[1]}")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append(f"grid width {w} outside {_VALID_W[0]}..{_VALID_W[1]}")

    color1_components = _components_of_color(g, 1)
    frames = _u_frame_records(g)
    if len(color1_components) != len(frames):
        errors.append("a color-1 component is not an exact one-notch frame")
    if not 1 <= len(frames) <= 2:
        errors.append(f"frame count {len(frames)} outside 1..2")

    covered = set()
    dot_colors = []
    for index, frame in enumerate(frames):
        r0, c0, r1, c1 = frame["bbox"]
        fh, fw = r1 - r0 + 1, c1 - c0 + 1
        if not 3 <= fh <= 6 or not 5 <= fw <= 7:
            errors.append(
                f"frame {index} size {fh}x{fw} outside 3..6 x 5..7"
            )
        if frame["opening"] == "top" and r0 == 0:
            errors.append(f"frame {index} has no row above its top notch")
        if frame["opening"] == "bottom" and r1 == h - 1:
            errors.append(f"frame {index} has no row below its bottom notch")
        if len(frame["dots"]) != 1:
            errors.append(
                f"frame {index} has {len(frame['dots'])} dots, expected 1"
            )
        else:
            dot_r, dot_c, dot_color = frame["dots"][0]
            dot_colors.append(dot_color)
            if not 2 <= dot_color <= 9:
                errors.append(
                    f"frame {index} dot color {dot_color} outside 2..9"
                )
            if dot_c != frame["gap_c"]:
                errors.append(
                    f"frame {index} dot column is not aligned to its notch"
                )
            if not (r0 < dot_r < r1 and c0 < dot_c < c1):
                errors.append(f"frame {index} dot is not strictly interior")
        covered.update(
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
        )

    outside = [
        (r, c)
        for r, row in enumerate(g)
        for c, value in enumerate(row)
        if value != 0 and (r, c) not in covered
    ]
    if outside:
        errors.append(f"{len(outside)} nonzero cells lie outside every frame")

    if len(frames) == 2:
        upper, lower = sorted(frames, key=lambda frame: frame["bbox"][0])
        if lower["bbox"][0] - upper["bbox"][2] - 1 < 1:
            errors.append("two frames lack a blank separating row")
        if len(dot_colors) == 2 and len(set(dot_colors)) != 2:
            errors.append("two-frame scene uses the same dot color twice")
        for index, frame in enumerate(frames):
            r0, c0, r1, c1 = frame["bbox"]
            bar_r = r0 - 1 if frame["opening"] == "top" else r1 + 1
            for other_index, other in enumerate(frames):
                if index == other_index:
                    continue
                or0, oc0, or1, oc1 = other["bbox"]
                if (
                    or0 <= bar_r <= or1
                    and max(c0, oc0) <= min(c1, oc1)
                ):
                    errors.append(
                        f"frame {index} projection row intersects frame "
                        f"{other_index}"
                    )
    return errors


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    canonical_profile_signature(_template_from_profile(profile))
    for profile in _PROFILE_SPECS
)


def _draw_profile(profile, rng, palette, opening_mode):
    h, w, specs = profile
    union_h = max(r0 + fh for r0, _, fh, _, _, _, _, _ in specs)
    union_w = max(c0 + fw for _, c0, _, fw, _, _, _, _ in specs)
    anchor_r = rng.randint(1, h - union_h)
    anchor_c = rng.randint(0, w - union_w)
    colors = rng.sample(list(palette), len(specs))
    grid = full_grid(h, w, 0)
    for index, spec in enumerate(specs):
        rr, cc, fh, fw, _, gap, dot_r, dot_c = spec
        _draw_notched_frame(
            grid,
            anchor_r + rr,
            anchor_c + cc,
            fh,
            fw,
            opening="top",
            notch_rel_col=gap,
            dot_rel_row=dot_r,
            dot_rel_col=dot_c,
            dot_color=colors[index],
        )
    vertical = (
        opening_mode == "bottom"
        if opening_mode is not None
        else bool(rng.randrange(2))
    )
    horizontal = bool(rng.randrange(2))
    return _flip(grid, vertical=vertical, horizontal=horizontal)


def _general_frame_specs(h, w, frame_count, rng, band):
    height_ranges = {
        "easy": (3, 4),
        "medium": (3, 5),
        "hard": (4, 6),
    }
    width_ranges = {
        "easy": (5, 5),
        "medium": (5, 6),
        "hard": (6, 7),
    }
    h_lo, h_hi = height_ranges[band]
    w_lo, w_hi = width_ranges[band]
    h_hi = min(h_hi, h - 1)
    w_hi = min(w_hi, w)

    if frame_count == 1:
        fh = rng.randint(h_lo, h_hi)
        fw = rng.randint(w_lo, w_hi)
        r0 = rng.randint(1, h - fh)
        c0 = rng.randint(0, w - fw)
        return [(r0, c0, fh, fw)]

    feasible = [
        (fh1, fh2, gap)
        for fh1 in range(h_lo, h_hi + 1)
        for fh2 in range(h_lo, h_hi + 1)
        for gap in range(1, 4)
        if 1 + fh1 + gap + fh2 <= h
    ]
    if not feasible:
        raise ValueError(
            f"cannot place two {band} frames constructively on {h}x{w}"
        )
    fh1, fh2, gap = rng.choice(feasible)
    top_margin = rng.randint(1, h - fh1 - gap - fh2)
    fw1 = rng.randint(w_lo, w_hi)
    fw2 = rng.randint(w_lo, w_hi)
    return [
        (top_margin, rng.randint(0, w - fw1), fh1, fw1),
        (
            top_margin + fh1 + gap,
            rng.randint(0, w - fw2),
            fh2,
            fw2,
        ),
    ]


def _draw_general(h, w, frame_count, rng, palette, band, opening_mode):
    specs = _general_frame_specs(h, w, frame_count, rng, band)
    colors = rng.sample(list(palette), frame_count)
    grid = full_grid(h, w, 0)
    for index, (r0, c0, fh, fw) in enumerate(specs):
        notch = rng.randint(1, fw - 2)
        dot_r = rng.randint(1, fh - 2)
        _draw_notched_frame(
            grid,
            r0,
            c0,
            fh,
            fw,
            opening="top",
            notch_rel_col=notch,
            dot_rel_row=dot_r,
            dot_rel_col=notch,
            dot_color=colors[index],
        )
    vertical = (
        opening_mode == "bottom"
        if opening_mode is not None
        else bool(rng.randrange(2))
    )
    horizontal = bool(rng.randrange(2))
    return _flip(grid, vertical=vertical, horizontal=horizontal)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    if overrides.get("texture") is not None:
        texture = ctx.draw_choice("texture", TEXTURES)
    else:
        texture = ctx.draw_choice("texture", ("none",))

    forced_palette = texture if texture in PALETTE_KINDS else None
    if forced_palette is not None:
        palette_kind = ctx.draw_choice("palette_kind", (forced_palette,))
    else:
        palette_kind = ctx.draw_choice("palette_kind", PALETTE_KINDS)
    palette = _PALETTES[palette_kind]
    opening_mode = {
        "top_open": "top",
        "bottom_open": "bottom",
    }.get(texture)

    exact_overrides = {
        label
        for label in ("grid_h", "grid_w", "frame_count")
        if overrides.get(label) is not None
    }
    band = difficulty or "medium"
    profile = None
    if not exact_overrides:
        prior_rng = ctx.draw_rng(f"canonical_prior|{band}")
        if prior_rng.random() < _PROFILE_PRIOR:
            profile_index = ctx.draw_choice(
                f"canonical_form|{band}",
                tuple(range(len(_PROFILE_SPECS))),
            )
            profile = _PROFILE_SPECS[profile_index]

    if overrides.get("grid_h") is not None:
        h = ctx.draw_int("grid_h", *_VALID_H)
    elif profile is not None:
        h = ctx.draw_int("grid_h", profile[0], profile[0])
    else:
        h = ctx.draw_int(
            "grid_h",
            *{
                "easy": (10, 12),
                "medium": (12, 15),
                "hard": (15, 18),
            }[band],
        )

    if overrides.get("grid_w") is not None:
        w = ctx.draw_int("grid_w", *_VALID_W)
    elif profile is not None:
        w = ctx.draw_int("grid_w", profile[1], profile[1])
    else:
        w = ctx.draw_int(
            "grid_w",
            *{
                "easy": (10, 12),
                "medium": (12, 15),
                "hard": (15, 18),
            }[band],
        )

    if overrides.get("frame_count") is not None:
        frame_count = ctx.draw_int("frame_count", 1, 2)
    elif profile is not None:
        frame_count = ctx.draw_int(
            "frame_count", len(profile[2]), len(profile[2])
        )
    else:
        frame_count = ctx.draw_choice(
            "frame_count",
            {
                "easy": (1, 1, 2),
                "medium": (1, 2),
                "hard": (2,),
            }[band],
        )

    rng = ctx.draw_rng("layout")
    if profile is not None:
        grid = _draw_profile(profile, rng, palette, opening_mode)
    else:
        grid = _draw_general(
            h,
            w,
            frame_count,
            rng,
            palette,
            band,
            opening_mode,
        )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
