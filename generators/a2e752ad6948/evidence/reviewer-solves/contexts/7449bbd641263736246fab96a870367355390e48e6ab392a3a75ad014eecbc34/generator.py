"""Generator for arc_additional_puzzles_21_set20_bundle:M136 — Checker Frames.

Rule: each rectangular frame contains one differently colored marker. Fill the
frame interior with a checkerboard anchored at the interior's top-left cell:
marker color on even parity cells, frame color on odd parity cells.

Normal lessons contain two separated frames with independent local color pairs.
At least one marker is deliberately off the output checker phase, which rules
out the tempting but wrong "start the checkerboard at the marker" shortcut.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_rect_outline, full_grid

GENERATOR_ID = "a2e752ad6948"
VERSION = "2.0.0"  # guarantee two frames; make axes exact; structural self-check
TASK_ID = "a2e752ad6948"
RULE_HASH = "39fb0a2b12e8"  # whitespace-normalized canonical program_solution
SUMMARY = (
    "Two separated 4-6 cell rectangular frames, each with one differently "
    "colored interior marker. Fill every interior with a top-left-anchored "
    "checkerboard using that frame's local marker and border colors."
)

INVARIANTS = [
    "exactly 2 complete, one-cell-thick rectangular frames of size 4..6 per side",
    "each frame contains exactly 1 interior marker whose color differs from every frame color",
    "the four frame/marker role colors are distinct and the frames have at least one background cell between them",
    "at least one marker is on odd local parity, so marker-anchored filling is observably wrong",
]

TEXTURES = ("default", "warm", "cool", "varied")
HELPFUL_TEXTURES = TEXTURES
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAYOUTS = ("horizontal", "vertical", "diagonal_down", "diagonal_up")
MARKER_PHASES = ("mixed", "odd")

# Each texture uses four distinct non-zero colors. The sets are intentionally
# identifiable from the returned grid so `observe_overrides` can audit exact
# texture overrides; role assignment is shuffled independently per instance.
_TEXTURE_PALETTES = {
    "default": (1, 2, 3, 4),
    "warm": (2, 4, 7, 9),
    "cool": (1, 3, 6, 8),
    "varied": (5, 6, 7, 9),
}
_PALETTE_TO_TEXTURE = {
    frozenset(colors): name for name, colors in _TEXTURE_PALETTES.items()
}

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-skewed 11..17",
        "valid": "11..17",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-skewed 12..20",
        "valid": "12..20",
    },
    "layout": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(LAYOUTS),
    },
    "marker_phase": {
        "type": "str",
        "default": "rng mixed|odd",
        "valid": "|".join(MARKER_PHASES),
    },
    "texture": {
        "type": "str",
        "default": "rng",
        "valid": "|".join(TEXTURES),
    },
}


def _randint(rng, lo: int, hi: int) -> int:
    if hi < lo:
        raise ValueError(f"empty placement interval [{lo}, {hi}]")
    return rng.randint(lo, hi)


def _frame_in_region(rng, region, *, fixed_h=None, fixed_w=None):
    """Choose a 4..6 frame entirely inside an inclusive region."""
    r_lo, r_hi, c_lo, c_hi = region
    cap_h, cap_w = r_hi - r_lo + 1, c_hi - c_lo + 1
    if cap_h < 4 or cap_w < 4:
        raise ValueError(f"region {region} cannot hold a 4x4 frame")
    fh = fixed_h if fixed_h is not None else _randint(rng, 4, min(6, cap_h))
    fw = fixed_w if fixed_w is not None else _randint(rng, 4, min(6, cap_w))
    if not (4 <= fh <= min(6, cap_h) and 4 <= fw <= min(6, cap_w)):
        raise ValueError(f"frame {(fh, fw)} does not fit region {region}")
    r0 = _randint(rng, r_lo, r_hi - fh + 1)
    c0 = _randint(rng, c_lo, c_hi - fw + 1)
    return r0, c0, fh, fw


def _choose_frames(h: int, w: int, layout: str, rng):
    """Return two guaranteed-separated frame boxes for the requested layout."""
    if layout == "horizontal":
        gap_c = w // 2
        left = (1, h - 2, 1, gap_c - 1)
        right = (1, h - 2, gap_c + 1, w - 2)
        common_h = _randint(rng, 4, min(6, h - 2))
        r0 = _randint(rng, 1, h - common_h - 1)
        first = _frame_in_region(rng, left, fixed_h=common_h)
        second = _frame_in_region(rng, right, fixed_h=common_h)
        return (
            (r0, first[1], common_h, first[3]),
            (r0, second[1], common_h, second[3]),
        )

    if layout == "vertical":
        gap_r = h // 2
        top = (1, gap_r - 1, 1, w - 2)
        bottom = (gap_r + 1, h - 2, 1, w - 2)
        common_w = _randint(rng, 4, min(6, w - 2))
        c0 = _randint(rng, 1, w - common_w - 1)
        first = _frame_in_region(rng, top, fixed_w=common_w)
        second = _frame_in_region(rng, bottom, fixed_w=common_w)
        return (
            (first[0], c0, first[2], common_w),
            (second[0], c0, second[2], common_w),
        )

    gap_r, gap_c = h // 2, w // 2
    top_left = (1, gap_r - 1, 1, gap_c - 1)
    top_right = (1, gap_r - 1, gap_c + 1, w - 2)
    bottom_left = (gap_r + 1, h - 2, 1, gap_c - 1)
    bottom_right = (gap_r + 1, h - 2, gap_c + 1, w - 2)
    if layout == "diagonal_down":
        regions = (top_left, bottom_right)
    elif layout == "diagonal_up":
        regions = (bottom_left, top_right)
    else:
        raise ValueError(f"unknown layout {layout!r}")
    return tuple(_frame_in_region(rng, region) for region in regions)


def _marker_position(box, parity: int, rng):
    r0, c0, fh, fw = box
    candidates = [
        (r, c)
        for r in range(r0 + 1, r0 + fh - 1)
        for c in range(c0 + 1, c0 + fw - 1)
        if ((r - (r0 + 1)) + (c - (c0 + 1))) % 2 == parity
    ]
    if not candidates:
        raise ValueError(f"frame {box} has no interior parity-{parity} cell")
    return rng.choice(candidates)


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 11, 17)
    w = ctx.draw_int_diff("grid_w", 12, 20)
    layout = ctx.draw_choice("layout", LAYOUTS)
    marker_phase = ctx.draw_choice("marker_phase", MARKER_PHASES)
    texture = ctx.draw_choice("texture", TEXTURES)

    layout_rng = ctx.draw_rng("layout_geometry")
    marker_rng = ctx.draw_rng("marker_positions")
    palette_rng = ctx.draw_rng("palette_roles")
    boxes = _choose_frames(h, w, layout, layout_rng)

    phases = [1, 1] if marker_phase == "odd" else [0, 1]
    if marker_phase == "mixed" and marker_rng.randrange(2):
        phases.reverse()

    colors = list(_TEXTURE_PALETTES[texture])
    palette_rng.shuffle(colors)
    g = full_grid(h, w, 0)
    for box, phase, (border, marker) in zip(
        boxes,
        phases,
        ((colors[0], colors[1]), (colors[2], colors[3])),
    ):
        r0, c0, fh, fw = box
        draw_rect_outline(g, r0, c0, fh, fw, border)
        mr, mc = _marker_position(box, phase, marker_rng)
        g[mr][mc] = marker
    return g


def _same_color_components(grid):
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                cr, cc = stack.pop()
                cells.append((cr, cc))
                for nr, nc in (
                    (cr - 1, cc),
                    (cr + 1, cc),
                    (cr, cc - 1),
                    (cr, cc + 1),
                ):
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append((color, cells))
    return components


def _analyze(grid):
    """Recover frame records and non-zero cells not explained by the grammar."""
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        raise ValueError("grid is not a non-empty list of rows")
    w = len(grid[0])
    if w == 0 or any(not isinstance(row, list) or len(row) != w for row in grid):
        raise ValueError("grid is ragged or empty-width")
    h = len(grid)
    if any(
        not isinstance(value, int)
        or isinstance(value, bool)
        or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        raise ValueError("grid contains a non-ARC color")

    frames = []
    for color, component in _same_color_components(grid):
        cells = set(component)
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        r1, r2, c1, c2 = min(rows), max(rows), min(cols), max(cols)
        fh, fw = r2 - r1 + 1, c2 - c1 + 1
        if fh < 4 or fw < 4:
            continue
        perimeter = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
            if r in (r1, r2) or c in (c1, c2)
        }
        if cells != perimeter:
            continue
        markers = [
            (r, c, grid[r][c])
            for r in range(r1 + 1, r2)
            for c in range(c1 + 1, c2)
            if grid[r][c] not in (0, color)
        ]
        frames.append(
            {
                "color": color,
                "r1": r1,
                "r2": r2,
                "c1": c1,
                "c2": c2,
                "h": fh,
                "w": fw,
                "markers": markers,
                "perimeter": perimeter,
            }
        )
    frames.sort(key=lambda frame: (frame["r1"], frame["c1"]))

    explained = set()
    for frame in frames:
        explained.update(frame["perimeter"])
        explained.update((r, c) for r, c, _ in frame["markers"])
    extras = [
        (r, c, grid[r][c])
        for r in range(h)
        for c in range(w)
        if grid[r][c] != 0 and (r, c) not in explained
    ]
    return frames, extras


def _layout_of(frames) -> str:
    if len(frames) != 2:
        return "invalid"
    centers = [
        (frame["r1"] + frame["r2"], frame["c1"] + frame["c2"])
        for frame in frames
    ]
    if centers[0][0] == centers[1][0]:
        return "horizontal"
    if centers[0][1] == centers[1][1]:
        return "vertical"
    left, right = sorted(centers, key=lambda center: center[1])
    return "diagonal_down" if left[0] < right[0] else "diagonal_up"


def _marker_phase_of(frames) -> str:
    phases = []
    for frame in frames:
        if len(frame["markers"]) != 1:
            return "invalid"
        r, c, _ = frame["markers"][0]
        phases.append(
            ((r - (frame["r1"] + 1)) + (c - (frame["c1"] + 1))) % 2
        )
    if phases == [1, 1]:
        return "odd"
    if sorted(phases) == [0, 1]:
        return "mixed"
    return "even" if phases == [0, 0] else "invalid"


def observe_overrides(grid):
    frames, extras = _analyze(grid)
    if len(frames) != 2 or extras or any(len(frame["markers"]) != 1 for frame in frames):
        raise ValueError("grid does not satisfy the two-frame teaching grammar")
    role_colors = [frame["color"] for frame in frames]
    role_colors.extend(frame["markers"][0][2] for frame in frames)
    texture = _PALETTE_TO_TEXTURE.get(frozenset(role_colors), "unknown")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "layout": _layout_of(frames),
        "marker_phase": _marker_phase_of(frames),
        "texture": texture,
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed lessons; canonical all-even examples remain lawful."""
    try:
        frames, extras = _analyze(grid)
    except ValueError as exc:
        return [str(exc)]

    h, w = len(grid), len(grid[0])
    errors = []
    if len(frames) != 2:
        errors.append(f"expected exactly 2 complete rectangular frames, found {len(frames)}")
        return errors

    role_colors = []
    for index, frame in enumerate(frames, 1):
        if not (4 <= frame["h"] <= 6 and 4 <= frame["w"] <= 6):
            errors.append(
                f"frame {index} has size {frame['h']}x{frame['w']}; expected each side in 4..6"
            )
        if not (
            frame["r1"] >= 1
            and frame["c1"] >= 1
            and frame["r2"] <= h - 2
            and frame["c2"] <= w - 2
        ):
            errors.append(f"frame {index} lacks a one-cell outer background margin")
        if len(frame["markers"]) != 1:
            errors.append(
                f"frame {index} has {len(frame['markers'])} interior markers; expected exactly 1"
            )
        role_colors.append(frame["color"])
        if len(frame["markers"]) == 1:
            role_colors.append(frame["markers"][0][2])

    first, second = frames
    separated = (
        first["r2"] + 2 <= second["r1"]
        or second["r2"] + 2 <= first["r1"]
        or first["c2"] + 2 <= second["c1"]
        or second["c2"] + 2 <= first["c1"]
    )
    if not separated:
        errors.append("frames touch or overlap; expected at least one background row/column between them")
    if extras:
        errors.append(f"found {len(extras)} unexplained non-zero cell(s) outside frame roles")
    if len(role_colors) == 4 and len(set(role_colors)) != 4:
        errors.append(f"frame and marker role colors are not all distinct: {role_colors}")
    return errors
