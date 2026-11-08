"""Generator for d4ea5a7deae6 (bank edd0efb19ea0 task M85).

Each color-1 rectangular frame contains one token and one seed.  Token 2
selects a plus kernel, token 3 an X kernel, and token 4 a full 3x3 kernel.
The output keeps the frame walls and paints the selected kernel in the seed
color, centered on the seed and clipped to the strict frame interior.

The public scenes have two horizontally separated frames.  Their linked
answer-bearing profile includes the grid dimensions, relative frame
positions and sizes, token values, and seed offsets within each frame.
Absolute translation, seed color names, token positions, and whole-scene
horizontal/vertical reflection are lawful nuisance variation.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid


GENERATOR_ID = "d4ea5a7deae6"
VERSION = "3.0.0"
TASK_ID = "d4ea5a7deae6"
RULE_HASH = "efb277668cb4"

SUMMARY = (
    "A 0-background 10..16 x 13..20 grid contains one or two separated "
    "color-1 rectangular frames. Each frame has exactly one token in "
    "{2,3,4} and one seed in {5,6,7,8,9}. Token 2 paints a plus, token 3 "
    "an X, and token 4 a full 3x3 footprint in the seed color, clipped to "
    "the strict frame interior. Default scenes use two frames with distinct "
    "tokens and seed colors and mix centered and clipped footprints."
)

INVARIANTS = [
    "background is 0 and every color-1 component is one full rectangle perimeter",
    "one or two frames, each 5..7 rows by 4..6 columns",
    "two-frame scenes are horizontally separated by at least two blank columns",
    "each frame interior has exactly one token in {2,3,4} and one seed in {5..9}",
    "two-frame scenes use distinct token values and distinct seed colors",
]

PALETTE_KINDS = ("default", "warm", "cool", "varied")
SEMANTIC_TEXTURES = ("clipped", "centered")
HELPFUL_TEXTURES = PALETTE_KINDS + SEMANTIC_TEXTURES
DEGENERATE_TEXTURES = ()
TEXTURES = ("none",) + HELPFUL_TEXTURES

_PALETTES = {
    "default": (5, 6),
    "warm": (5, 7, 9),
    "cool": (6, 8),
    "varied": (5, 6, 7, 8, 9),
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-aware rng 10..16",
        "valid": "10..16",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-aware rng 13..20",
        "valid": "13..20",
    },
    "n_frames": {
        "type": "int",
        "default": "2",
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

_VALID_H = (10, 16)
_VALID_W = (13, 20)
_PROFILE_PRIOR = 0.30
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))

# (grid_h, grid_w, frames), where each frame is
# (relative_top, relative_left, height, width, token, seed_rel_r, seed_rel_c).
# Token position is intentionally absent: the rule reads its value but not its
# position.  Seed colors are also nuisance labels.
_PROFILE_SPECS = (
    (11, 13, (
        (0, 0, 5, 5, 2, 2, 2),
        (0, 7, 5, 4, 4, 2, 1),
    )),
    (10, 14, (
        (0, 0, 6, 5, 3, 2, 2),
        (1, 7, 6, 4, 2, 3, 1),
    )),
    (12, 15, (
        (0, 0, 6, 5, 4, 3, 2),
        (0, 8, 6, 5, 3, 2, 2),
    )),
    (11, 14, (
        (0, 0, 6, 5, 2, 2, 2),
        (0, 7, 7, 5, 4, 3, 2),
    )),
    (12, 15, (
        (0, 0, 6, 5, 2, 3, 2),
        (1, 7, 7, 5, 3, 3, 2),
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
    for label in ("grid_h", "grid_w", "n_frames"):
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
    out = []
    for row in grid:
        out.append([
            int(value) if isinstance(value, str) and value.isdigit() else value
            for value in row
        ])
    return out


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


def _frame_records(grid):
    """Return exact color-1 rectangle frames and their interior markers."""
    frames = []
    for cells in _components_of_color(grid, 1):
        r0 = min(r for r, _ in cells)
        c0 = min(c for _, c in cells)
        r1 = max(r for r, _ in cells)
        c1 = max(c for _, c in cells)
        perimeter = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        if set(cells) != perimeter:
            continue
        nonzero = [
            (r, c, grid[r][c])
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] != 0
        ]
        tokens = [cell for cell in nonzero if cell[2] in (2, 3, 4)]
        seeds = [cell for cell in nonzero if cell[2] not in (2, 3, 4)]
        frames.append({
            "bbox": (r0, c0, r1, c1),
            "tokens": tokens,
            "seeds": seeds,
        })
    return sorted(frames, key=lambda frame: frame["bbox"][:2])


def _kernel(token):
    if token == 2:
        return ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
    if token == 3:
        return ((0, 0), (-1, -1), (-1, 1), (1, -1), (1, 1))
    return tuple(
        (dr, dc)
        for dr in range(-1, 2)
        for dc in range(-1, 2)
    )


def _flip(grid, *, vertical=False, horizontal=False):
    out = [row[:] for row in grid]
    if vertical:
        out.reverse()
    if horizontal:
        out = [list(reversed(row)) for row in out]
    return out


def _raw_profile_signature(grid):
    frames = _frame_records(grid)
    if (
        len(frames) != 2
        or any(len(frame["tokens"]) != 1 for frame in frames)
        or any(len(frame["seeds"]) != 1 for frame in frames)
    ):
        return None
    anchor_r = min(frame["bbox"][0] for frame in frames)
    anchor_c = min(frame["bbox"][1] for frame in frames)
    profile = []
    for frame in frames:
        r0, c0, r1, c1 = frame["bbox"]
        token = frame["tokens"][0][2]
        seed_r, seed_c, _ = frame["seeds"][0]
        profile.append((
            r0 - anchor_r,
            c0 - anchor_c,
            r1 - r0 + 1,
            c1 - c0 + 1,
            token,
            seed_r - r0,
            seed_c - c0,
        ))
    return len(grid), len(grid[0]), tuple(profile)


def canonical_profile_signature(grid):
    """Complete answer-bearing profile, quotienting only lawful nuisances."""
    if not grid or not grid[0] or any(len(row) != len(grid[0]) for row in grid):
        return None
    g = _coerce_grid(grid)
    if any(type(value) is not int for row in g for value in row):
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


def _template_from_profile(profile):
    h, w, specs = profile
    grid = full_grid(h, w, 0)
    colors = (5, 6)
    for index, (r0, c0, fh, fw, token, sr, sc) in enumerate(specs):
        draw_frame(grid, r0, c0, r0 + fh - 1, c0 + fw - 1, 1)
        seed = (r0 + sr, c0 + sc)
        token_candidates = [
            (r, c)
            for r in range(r0 + 1, r0 + fh - 1)
            for c in range(c0 + 1, c0 + fw - 1)
            if (r, c) != seed
        ]
        tr, tc = token_candidates[0]
        grid[tr][tc] = token
        grid[seed[0]][seed[1]] = colors[index]
    return grid


_CANONICAL_PROFILE_SIGNATURES = frozenset(
    canonical_profile_signature(_template_from_profile(profile))
    for profile in _PROFILE_SPECS
)


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
        return {"n_frames": len(_frame_records(g))}
    except (TypeError, ValueError, IndexError):
        return {}


def rule_mirror(grid):
    """Python spelling of the stored Racket rule."""
    g = _coerce_grid(grid)
    out = [
        [1 if value == 1 else 0 for value in row]
        for row in g
    ]
    for frame in _frame_records(g):
        if not frame["tokens"] or not frame["seeds"]:
            continue
        r0, c0, r1, c1 = frame["bbox"]
        token = frame["tokens"][-1][2]
        sr, sc, color = frame["seeds"][-1]
        for dr, dc in _kernel(token):
            r, c = sr + dr, sc + dc
            if r0 < r < r1 and c0 < c < c1:
                out[r][c] = color
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
    if any(type(value) is not int or not 0 <= value <= 9
           for row in g for value in row):
        errors.append("grid contains a non-integer or color outside 0..9")
        return errors
    h, w = len(g), len(g[0])
    if not (_VALID_H[0] <= h <= _VALID_H[1]):
        errors.append(f"grid height {h} outside {_VALID_H[0]}..{_VALID_H[1]}")
    if not (_VALID_W[0] <= w <= _VALID_W[1]):
        errors.append(f"grid width {w} outside {_VALID_W[0]}..{_VALID_W[1]}")

    color1_components = _components_of_color(g, 1)
    frames = _frame_records(g)
    if len(color1_components) != len(frames):
        errors.append("a color-1 component is not a complete rectangle frame")
    if not 1 <= len(frames) <= 2:
        errors.append(f"frame count {len(frames)} outside 1..2")

    covered = set()
    tokens = []
    seed_colors = []
    for index, frame in enumerate(frames):
        r0, c0, r1, c1 = frame["bbox"]
        fh, fw = r1 - r0 + 1, c1 - c0 + 1
        if not 5 <= fh <= 7 or not 4 <= fw <= 6:
            errors.append(
                f"frame {index} size {fh}x{fw} outside 5..7 x 4..6"
            )
        if len(frame["tokens"]) != 1:
            errors.append(
                f"frame {index} has {len(frame['tokens'])} tokens, expected 1"
            )
        if len(frame["seeds"]) != 1:
            errors.append(
                f"frame {index} has {len(frame['seeds'])} seeds, expected 1"
            )
        if len(frame["tokens"]) == 1:
            tokens.append(frame["tokens"][0][2])
        if len(frame["seeds"]) == 1:
            seed_color = frame["seeds"][0][2]
            seed_colors.append(seed_color)
            if seed_color not in range(5, 10):
                errors.append(
                    f"frame {index} seed color {seed_color} outside 5..9"
                )
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
        left, right = sorted(frames, key=lambda frame: frame["bbox"][1])
        _, _, _, left_c1 = left["bbox"]
        _, right_c0, _, _ = right["bbox"]
        if right_c0 - left_c1 - 1 < 2:
            errors.append("two frames lack the required two-column gap")
        if len(tokens) == 2 and len(set(tokens)) != 2:
            errors.append("two-frame scene uses the same token twice")
        if len(seed_colors) == 2 and len(set(seed_colors)) != 2:
            errors.append("two-frame scene uses the same seed color twice")
    return errors


def _draw_profile(profile, rng, palette):
    h, w, specs = profile
    union_h = max(r0 + fh for r0, _, fh, _, _, _, _ in specs)
    union_w = max(c0 + fw for _, c0, _, fw, _, _, _ in specs)
    anchor_r = rng.randint(0, h - union_h)
    anchor_c = rng.randint(0, w - union_w)
    colors = rng.sample(list(palette), len(specs))
    grid = full_grid(h, w, 0)
    for index, (rr, cc, fh, fw, token, sr, sc) in enumerate(specs):
        r0, c0 = anchor_r + rr, anchor_c + cc
        draw_frame(grid, r0, c0, r0 + fh - 1, c0 + fw - 1, 1)
        seed = (r0 + sr, c0 + sc)
        candidates = [
            (r, c)
            for r in range(r0 + 1, r0 + fh - 1)
            for c in range(c0 + 1, c0 + fw - 1)
            if (r, c) != seed
        ]
        tr, tc = rng.choice(candidates)
        grid[tr][tc] = token
        grid[seed[0]][seed[1]] = colors[index]
    flip = rng.choice(("none", "horizontal", "vertical", "both"))
    return _flip(
        grid,
        vertical=flip in ("vertical", "both"),
        horizontal=flip in ("horizontal", "both"),
    )


def _general_frame_specs(h, w, n_frames, rng, *, centered):
    min_width = 5 if centered else 5
    if n_frames == 1:
        fh = rng.randint(5, min(7, h - 1))
        fw = rng.randint(min_width, min(6, w - 1))
        r0 = rng.randint(0, h - fh)
        c0 = rng.randint(0, w - fw)
        return [(r0, c0, fh, fw)]

    for _ in range(100):
        fh1 = rng.randint(5, min(7, h))
        fh2 = rng.randint(5, min(7, h))
        fw1 = rng.randint(min_width, min(6, w))
        fw2 = rng.randint(min_width, min(6, w))
        max_gap = min(4, w - fw1 - fw2)
        if max_gap < 2:
            continue
        gap = rng.randint(2, max_gap)
        total_w = fw1 + gap + fw2
        if total_w > w:
            continue
        c0 = rng.randint(0, w - total_w)
        r0 = rng.randint(0, h - fh1)
        r1 = rng.randint(0, h - fh2)
        return [
            (r0, c0, fh1, fw1),
            (r1, c0 + fw1 + gap, fh2, fw2),
        ]
    raise ValueError(f"cannot place two separated frames on {h}x{w}")


def _seed_candidates(fh, fw, token, *, clipped):
    candidates = []
    for r in range(1, fh - 1):
        for c in range(1, fw - 1):
            footprint = [(r + dr, c + dc) for dr, dc in _kernel(token)]
            is_clipped = any(
                not (1 <= rr < fh - 1 and 1 <= cc < fw - 1)
                for rr, cc in footprint
            )
            if is_clipped == clipped:
                candidates.append((r, c))
    return candidates


def _draw_general(h, w, n_frames, rng, palette, texture):
    centered = texture == "centered"
    specs = _general_frame_specs(
        h, w, n_frames, rng, centered=centered
    )
    tokens = rng.sample((2, 3, 4), n_frames)
    colors = rng.sample(list(palette), n_frames)
    if texture == "clipped":
        clipped_modes = [True] * n_frames
    elif texture == "centered":
        clipped_modes = [False] * n_frames
    elif n_frames == 2 and rng.random() < 0.40:
        clipped_index = rng.randrange(2)
        clipped_modes = [index == clipped_index for index in range(2)]
    else:
        clipped_modes = [False] * n_frames

    grid = full_grid(h, w, 0)
    for index, (r0, c0, fh, fw) in enumerate(specs):
        draw_frame(grid, r0, c0, r0 + fh - 1, c0 + fw - 1, 1)
        seed_options = _seed_candidates(
            fh, fw, tokens[index], clipped=clipped_modes[index]
        )
        if not seed_options:
            raise ValueError(
                f"no {'clipped' if clipped_modes[index] else 'centered'} "
                f"seed position for frame {fh}x{fw}"
            )
        sr, sc = rng.choice(seed_options)
        seed = (r0 + sr, c0 + sc)
        token_options = [
            (r, c)
            for r in range(r0 + 1, r0 + fh - 1)
            for c in range(c0 + 1, c0 + fw - 1)
            if (r, c) != seed
        ]
        tr, tc = rng.choice(token_options)
        grid[tr][tc] = tokens[index]
        grid[seed[0]][seed[1]] = colors[index]
    return grid


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

    numeric_overrides = {
        label
        for label in ("grid_h", "grid_w", "n_frames")
        if overrides.get(label) is not None
    }
    semantic_texture = texture in SEMANTIC_TEXTURES
    profile = None
    band = difficulty or "medium"
    if not numeric_overrides and not semantic_texture:
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
        h_ranges = {
            "easy": (10, 12),
            "medium": (10, 14),
            "hard": (12, 16),
        }
        h = ctx.draw_int("grid_h", *h_ranges[band])

    if overrides.get("grid_w") is not None:
        w = ctx.draw_int("grid_w", *_VALID_W)
    elif profile is not None:
        w = ctx.draw_int("grid_w", profile[1], profile[1])
    else:
        w_ranges = {
            "easy": (13, 15),
            "medium": (13, 18),
            "hard": (15, 20),
        }
        w = ctx.draw_int("grid_w", *w_ranges[band])

    if overrides.get("n_frames") is not None:
        n_frames = ctx.draw_int("n_frames", 1, 2)
    elif profile is not None:
        n_frames = ctx.draw_int("n_frames", 2, 2)
    else:
        n_frames = ctx.draw_choice("n_frames", (2,))

    rng = ctx.draw_rng("layout")
    if profile is not None:
        grid = _draw_profile(profile, rng, palette)
    else:
        grid = _draw_general(
            h, w, n_frames, rng, palette, texture
        )
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid grid: " + "; ".join(errors))
    return grid
