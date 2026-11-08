"""Generator for ARC task 14c5c68b0201 (base task a57f2f04).

Each non-background color is a sparse stamp inside its own rectangular hole.
The output repeats that stamp's exact bounding-box pattern across the whole
hole, preserving the stamp's phase; the modal background is unchanged.

The finite layout profiles keep ordinary training anchored to all four unique
canonical canvases while adding lawful scale/background variants. Every axis is
recoverable from the returned input by :func:`observe_overrides`.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "14c5c68b0201"
TASK_ID = GENERATOR_ID
RULE_HASH = "b125453b4d98"
VERSION = "3.1.0"  # exact overrides, structural grammar, canonical anchors, semantic rivals
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 0.25

SUMMARY = (
    "One to three disjoint rectangular holes lie in a modal background. Each "
    "hole contains one sparse colored stamp and no other active color. For "
    "each stamp color independently, take the stamp's bounding-box pattern "
    "and repeat it by row/column modulo across the entire containing hole, "
    "using the stamp's original top-left as the phase origin."
)

INVARIANTS = [
    "every non-background component is a filled rectangle of zero/stamp cells",
    "each rectangular hole contains exactly one active color",
    "each stamp is sparse and strictly smaller than its hole",
    "holes are separated by at least one background cell",
    "the modal background and all cells outside holes remain unchanged",
]

# BBoxes are inclusive (top, left, bottom, right). The first four profiles are
# the four unique canonical geometries; the rest broaden scale without changing
# the rule. Repeating canonical names in the draw options below gives a 75%
# canonical-layout prior while every exact override remains accepted.
LAYOUTS: dict[str, tuple[int, int, tuple[tuple[int, int, int, int], ...]]] = {
    "official_a": (23, 19, ((2, 2, 7, 9), (13, 7, 18, 15))),
    "official_b": (19, 13, ((3, 2, 14, 7),)),
    "official_c": (24, 21, ((3, 6, 11, 15), (14, 3, 19, 17))),
    "official_d": (26, 22, ((2, 3, 10, 8), (4, 13, 11, 18), (16, 3, 21, 10))),
    "compact": (18, 18, ((3, 3, 12, 12),)),
    "wide": (20, 26, ((2, 2, 9, 11), (10, 15, 17, 23))),
    "tall": (26, 20, ((2, 2, 11, 9), (15, 10, 23, 17))),
    "triple": (26, 26, ((2, 2, 10, 10), (2, 16, 11, 23), (16, 7, 23, 18))),
}
OFFICIAL_LAYOUTS = frozenset({"official_a", "official_b", "official_c", "official_d"})

# Every motif is 4-connected, sparse, touches all four sides of its own bbox,
# and fits every declared hole. Motif i is used in the first hole, i+1 in the
# second, etc.; that sequence makes motif_index exactly observable.
MOTIFS: tuple[tuple[tuple[int, ...], ...], ...] = (
    ((1, 1),
     (1, 0)),
    ((0, 1, 0),
     (1, 1, 0),
     (0, 1, 1)),
    ((1, 0, 1, 1),
     (1, 1, 0, 1),
     (0, 1, 1, 0)),
    ((0, 1, 0, 1, 0),
     (1, 1, 0, 1, 1),
     (0, 1, 1, 1, 0)),
)

ANCHOR_PROFILES = ("corners", "edges", "interior")
PALETTE_BANDS = ("low", "high")
BACKGROUND_COLORS = (8, 9)

AXES = {
    "layout_profile": {
        "type": "str",
        "default": "difficulty-aware weighted draw; every profile remains legal",
        "valid": "official_a|official_b|official_c|official_d|compact|wide|tall|triple",
    },
    "motif_index": {"type": "int", "default": "difficulty-aware weighted draw 0..3", "valid": "0..3"},
    "anchor_profile": {
        "type": "str",
        "default": "difficulty-aware corners|edges|interior",
        "valid": "corners|edges|interior",
    },
    "palette_band": {
        "type": "str",
        "default": "difficulty-aware low|high",
        "valid": "low|high",
    },
    "background_color": {
        "type": "color",
        "default": "difficulty-aware 8|9",
        "valid": "8|9",
    },
}

# All declared cross-products are constructively supported.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []
_ALLOWED_OVERRIDES = frozenset(AXES)


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - _ALLOWED_OVERRIDES)
    if unknown:
        raise ValueError(f"unknown override key(s): {unknown}")


def _bbox(cells: list[tuple[int, int]] | set[tuple[int, int]]) -> tuple[int, int, int, int]:
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _shape(motif: tuple[tuple[int, ...], ...]) -> tuple[int, int]:
    return len(motif), len(motif[0])


def _anchor_position(
    hole: tuple[int, int, int, int],
    motif: tuple[tuple[int, ...], ...],
    profile: str,
    hole_index: int,
) -> tuple[int, int]:
    r1, c1, r2, c2 = hole
    mh, mw = _shape(motif)
    max_r = r2 - mh + 1
    max_c = c2 - mw + 1
    if profile == "corners":
        # Start at bottom-right rather than top-left so every ordinary scene
        # contains a phase witness against hole-origin tiling.
        corner = ("br", "tl", "tr", "bl")[hole_index % 4]
        return {
            "tl": (r1, c1),
            "tr": (r1, max_c),
            "br": (max_r, max_c),
            "bl": (max_r, c1),
        }[corner]
    if profile == "edges":
        edge = ("top", "bottom", "right", "left")[hole_index % 4]
        mid_r = r1 + (r2 - r1 + 1 - mh) // 2
        mid_c = c1 + (c2 - c1 + 1 - mw) // 2
        return {
            "top": (r1, mid_c),
            "bottom": (max_r, mid_c),
            "right": (mid_r, max_c),
            "left": (mid_r, c1),
        }[edge]
    if profile == "interior":
        # Centered and therefore away from every edge for all declared holes.
        return (
            r1 + (r2 - r1 + 1 - mh) // 2,
            c1 + (c2 - c1 + 1 - mw) // 2,
        )
    raise ValueError(f"unknown anchor profile {profile!r}")


def _colors_for(palette_band: str, count: int) -> tuple[int, ...]:
    palette = (1, 2, 3) if palette_band == "low" else (4, 6, 7)
    return palette[:count]


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

    # Difficulty changes the curriculum distribution, not legality: every
    # declared override value remains present in every option tuple. Easy is
    # canonical-heavy with small motifs; hard emphasizes expanded layouts,
    # larger motifs, interior phase offsets, high colors, and background 9.
    band = difficulty if difficulty in ("easy", "medium", "hard") else "medium"
    layout_options = {
        "easy": (
            "official_a", "official_a", "official_a", "official_a",
            "official_b", "official_b", "official_b", "official_b",
            "official_c", "official_c", "official_c", "official_c",
            "official_d", "official_d", "official_d", "official_d",
            "compact", "wide", "tall", "triple",
        ),
        "medium": (
            "official_a", "official_a", "official_b", "official_b",
            "official_c", "official_c", "official_d", "official_d",
            "compact", "compact", "wide", "wide", "tall", "tall",
            "triple", "triple",
        ),
        "hard": (
            "official_a", "official_b", "official_c", "official_d",
            "compact", "compact", "compact", "wide", "wide", "wide",
            "tall", "tall", "tall", "triple", "triple", "triple",
        ),
    }[band]
    motif_options = {
        "easy": (0, 0, 0, 0, 1, 1, 2, 3),
        "medium": (0, 1, 1, 2, 2, 3, 3),
        "hard": (0, 1, 2, 2, 3, 3, 3, 3),
    }[band]
    anchor_options = {
        "easy": ("corners", "corners", "edges", "interior"),
        "medium": ("corners", "edges", "edges", "interior"),
        "hard": ("corners", "edges", "interior", "interior"),
    }[band]
    palette_options = {
        "easy": ("low", "low", "low", "high"),
        "medium": ("low", "low", "high", "high"),
        "hard": ("low", "high", "high", "high"),
    }[band]
    background_options = {
        "easy": (8, 8, 8, 9),
        "medium": (8, 8, 9, 9),
        "hard": (8, 9, 9, 9),
    }[band]

    layout_profile = ctx.draw_choice("layout_profile", layout_options)
    motif_index = ctx.draw_choice("motif_index", motif_options)
    anchor_profile = ctx.draw_choice("anchor_profile", anchor_options)
    palette_band = ctx.draw_choice("palette_band", palette_options)
    background_color = ctx.draw_choice("background_color", background_options)

    height, width, holes = LAYOUTS[layout_profile]
    grid = full_grid(height, width, background_color)
    colors = _colors_for(palette_band, len(holes))

    for index, (hole, color) in enumerate(zip(holes, colors)):
        r1, c1, r2, c2 = hole
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                grid[row][col] = 0
        motif = MOTIFS[(motif_index + index) % len(MOTIFS)]
        top, left = _anchor_position(hole, motif, anchor_profile, index)
        for dr, motif_row in enumerate(motif):
            for dc, filled in enumerate(motif_row):
                if filled:
                    grid[top + dr][left + dc] = color

    return grid


def _components_not_bg(grid: list[list[int]], bg: int) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (r, c)
        for r in range(height)
        for c in range(width)
        if grid[r][c] != bg
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        queue = deque([start])
        remaining.remove(start)
        comp = {start}
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (row + dr, col + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    comp.add(nxt)
                    queue.append(nxt)
        components.append(comp)
    return sorted(components, key=lambda comp: _bbox(comp))


def _normalized_stamp(
    grid: list[list[int]], color: int
) -> tuple[tuple[tuple[int, ...], ...], tuple[int, int, int, int]]:
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    box = _bbox(cells)
    r1, c1, r2, c2 = box
    motif = tuple(
        tuple(1 if grid[r][c] == color else 0 for c in range(c1, c2 + 1))
        for r in range(r1, r2 + 1)
    )
    return motif, box


def _parse_scene(grid: Any) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return None, ["grid must be a non-empty list of rows"]
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return None, ["grid must be rectangular and non-empty"]
    height = len(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 9:
                return None, [f"cell ({r},{c}) is not an ARC color"]

    counts = Counter(value for row in grid for value in row)
    bg, bg_count = counts.most_common(1)[0]
    if bg == 0:
        errors.append("zero cannot be the modal background")
    if sum(1 for count in counts.values() if count == bg_count) > 1:
        errors.append("background mode must be unique")

    components = _components_not_bg(grid, bg)
    if not components:
        errors.append("at least one rectangular hole is required")
        return None, errors
    if len(components) > 3:
        errors.append(f"expected at most three holes, found {len(components)}")

    holes: list[dict[str, Any]] = []
    seen_colors: set[int] = set()
    for comp_index, comp in enumerate(components):
        r1, c1, r2, c2 = _bbox(comp)
        rectangle = {
            (r, c)
            for r in range(r1, r2 + 1)
            for c in range(c1, c2 + 1)
        }
        if comp != rectangle:
            errors.append(f"hole {comp_index} is not a filled rectangle of zero/stamp cells")
            continue
        if r1 == 0 or c1 == 0 or r2 == height - 1 or c2 == width - 1:
            errors.append(f"hole {comp_index} must have a background border")
        border = {
            (r, c)
            for r in range(max(0, r1 - 1), min(height, r2 + 2))
            for c in range(max(0, c1 - 1), min(width, c2 + 2))
            if not (r1 <= r <= r2 and c1 <= c <= c2)
        }
        if any(grid[r][c] != bg for r, c in border):
            errors.append(f"hole {comp_index} touches another non-background region")

        active = sorted({grid[r][c] for r, c in comp if grid[r][c] not in (0, bg)})
        if len(active) != 1:
            errors.append(f"hole {comp_index} must contain exactly one active color")
            continue
        color = active[0]
        if color in seen_colors:
            errors.append(f"active color {color} appears in more than one hole")
        seen_colors.add(color)
        color_cells = {(r, c) for r, c in comp if grid[r][c] == color}
        stamp_box = _bbox(color_cells)
        sr1, sc1, sr2, sc2 = stamp_box
        stamp_area = (sr2 - sr1 + 1) * (sc2 - sc1 + 1)
        if len(color_cells) == stamp_area:
            errors.append(f"hole {comp_index} stamp must be sparse, not a solid rectangle")
        if (sr1, sc1, sr2, sc2) == (r1, c1, r2, c2):
            errors.append(f"hole {comp_index} stamp must be strictly smaller than its hole")
        if not (r1 <= sr1 <= sr2 <= r2 and c1 <= sc1 <= sc2 <= c2):
            errors.append(f"hole {comp_index} stamp bbox leaves its hole")

        holes.append({
            "bbox": (r1, c1, r2, c2),
            "color": color,
            "stamp_bbox": stamp_box,
            "color_cells": color_cells,
        })

    if errors:
        return None, errors
    return {
        "height": height,
        "width": width,
        "background": bg,
        "holes": holes,
    }, []


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    _, errors = _parse_scene(grid)
    return errors


def _layout_name(scene: dict[str, Any]) -> str | None:
    signature = (
        scene["height"],
        scene["width"],
        tuple(hole["bbox"] for hole in scene["holes"]),
    )
    for name, (height, width, holes) in LAYOUTS.items():
        if signature == (height, width, holes):
            return name
    return None


def _motif_index(grid: list[list[int]], scene: dict[str, Any]) -> int | None:
    motifs = [_normalized_stamp(grid, hole["color"])[0] for hole in scene["holes"]]
    for start in range(len(MOTIFS)):
        if all(motif == MOTIFS[(start + i) % len(MOTIFS)] for i, motif in enumerate(motifs)):
            return start
    return None


def _anchor_profile(grid: list[list[int]], scene: dict[str, Any], motif_index: int) -> str | None:
    for profile in ANCHOR_PROFILES:
        expected = []
        actual = []
        for i, hole in enumerate(scene["holes"]):
            motif = MOTIFS[(motif_index + i) % len(MOTIFS)]
            expected.append(_anchor_position(hole["bbox"], motif, profile, i))
            stamp_box = _normalized_stamp(grid, hole["color"])[1]
            actual.append((stamp_box[0], stamp_box[1]))
        if actual == expected:
            return profile
    return None


def observe_overrides(grid) -> dict[str, Any]:
    scene, errors = _parse_scene(grid)
    if errors or scene is None:
        return {}
    layout = _layout_name(scene)
    motif_index = _motif_index(grid, scene)
    anchor = None if motif_index is None else _anchor_profile(grid, scene, motif_index)
    colors = [hole["color"] for hole in scene["holes"]]
    if colors and all(color in (1, 2, 3) for color in colors):
        palette = "low"
    elif colors and all(color in (4, 6, 7) for color in colors):
        palette = "high"
    else:
        palette = None
    return {
        "layout_profile": layout,
        "motif_index": motif_index,
        "anchor_profile": anchor,
        "palette_band": palette,
        "background_color": scene["background"],
    }


def strict_canonical_like(grid) -> list[str]:
    scene, errors = _parse_scene(grid)
    if errors or scene is None:
        return errors or ["scene did not parse"]
    reasons: list[str] = []
    if scene["background"] != 8:
        reasons.append("canonical background is 8")
    if _layout_name(scene) not in OFFICIAL_LAYOUTS:
        reasons.append("hole geometry is not one of the four canonical layouts")
    return reasons


def _solve_true_py(grid: list[list[int]]) -> list[list[int]]:
    scene, errors = _parse_scene(grid)
    if errors or scene is None:
        return [row[:] for row in grid]
    out = [row[:] for row in grid]
    for hole in scene["holes"]:
        r1, c1, r2, c2 = hole["bbox"]
        color = hole["color"]
        stamp, stamp_box = _normalized_stamp(grid, color)
        sr1, sc1, _, _ = stamp_box
        sh, sw = len(stamp), len(stamp[0])
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                if stamp[(row - sr1) % sh][(col - sc1) % sw]:
                    out[row][col] = color
    return out


def _rival_identity(grid: list[list[int]]) -> list[list[int]]:
    return [row[:] for row in grid]


def _rival_solid_fill(grid: list[list[int]]) -> list[list[int]]:
    scene, errors = _parse_scene(grid)
    if errors or scene is None:
        return [row[:] for row in grid]
    out = [row[:] for row in grid]
    for hole in scene["holes"]:
        r1, c1, r2, c2 = hole["bbox"]
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                out[row][col] = hole["color"]
    return out


def _rival_hole_origin_phase(grid: list[list[int]]) -> list[list[int]]:
    scene, errors = _parse_scene(grid)
    if errors or scene is None:
        return [row[:] for row in grid]
    out = [row[:] for row in grid]
    for hole in scene["holes"]:
        r1, c1, r2, c2 = hole["bbox"]
        color = hole["color"]
        stamp, _ = _normalized_stamp(grid, color)
        sh, sw = len(stamp), len(stamp[0])
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                if stamp[(row - r1) % sh][(col - c1) % sw]:
                    out[row][col] = color
    return out


def _rival_fixed_2x2(grid: list[list[int]]) -> list[list[int]]:
    scene, errors = _parse_scene(grid)
    if errors or scene is None:
        return [row[:] for row in grid]
    out = [row[:] for row in grid]
    for hole in scene["holes"]:
        r1, c1, r2, c2 = hole["bbox"]
        color = hole["color"]
        stamp, stamp_box = _normalized_stamp(grid, color)
        sr1, sc1, _, _ = stamp_box
        tiny = tuple(tuple(row[:2]) for row in stamp[:2])
        for row in range(r1, r2 + 1):
            for col in range(c1, c2 + 1):
                if tiny[(row - sr1) % len(tiny)][(col - sc1) % len(tiny[0])]:
                    out[row][col] = color
    return out




def _rival_first_hole_only(grid: list[list[int]]) -> list[list[int]]:
    scene, errors = _parse_scene(grid)
    if errors or scene is None:
        return [row[:] for row in grid]
    if not scene["holes"]:
        return [row[:] for row in grid]
    out = [row[:] for row in grid]
    hole = scene["holes"][0]
    r1, c1, r2, c2 = hole["bbox"]
    color = hole["color"]
    stamp, stamp_box = _normalized_stamp(grid, color)
    sr1, sc1, _, _ = stamp_box
    sh, sw = len(stamp), len(stamp[0])
    for row in range(r1, r2 + 1):
        for col in range(c1, c2 + 1):
            if stamp[(row - sr1) % sh][(col - sc1) % sw]:
                out[row][col] = color
    return out


def _rival_fixed_background_8(grid: list[list[int]]) -> list[list[int]]:
    scene, errors = _parse_scene(grid)
    if errors or scene is None or scene["background"] != 8:
        return [row[:] for row in grid]
    return _solve_true_py(grid)


def _scene_or_none(grid: Any) -> dict[str, Any] | None:
    scene, errors = _parse_scene(grid)
    return None if errors else scene


def _witness_expansion(grid: Any) -> bool:
    scene = _scene_or_none(grid)
    if scene is None:
        return False
    return any(
        hole["bbox"] != hole["stamp_bbox"]
        for hole in scene["holes"]
    )


def _witness_sparse(grid: Any) -> bool:
    scene = _scene_or_none(grid)
    if scene is None:
        return False
    return all(
        len(hole["color_cells"])
        < (hole["stamp_bbox"][2] - hole["stamp_bbox"][0] + 1)
          * (hole["stamp_bbox"][3] - hole["stamp_bbox"][1] + 1)
        for hole in scene["holes"]
    )


def _witness_phase_offset(grid: Any) -> bool:
    scene = _scene_or_none(grid)
    if scene is None:
        return False
    # A geometric offset is only decisive when it changes the answer; offsets
    # equal to a whole motif period are answer-equivalent and prove nothing.
    return _solve_true_py(grid) != _rival_hole_origin_phase(grid)


def _witness_non_2x2(grid: Any) -> bool:
    scene = _scene_or_none(grid)
    if scene is None:
        return False
    return any(
        (hole["stamp_bbox"][2] - hole["stamp_bbox"][0] + 1,
         hole["stamp_bbox"][3] - hole["stamp_bbox"][1] + 1) != (2, 2)
        for hole in scene["holes"]
    )


def _witness_single(grid: Any) -> bool:
    scene = _scene_or_none(grid)
    return scene is not None and len(scene["holes"]) == 1


def _witness_multiple(grid: Any) -> bool:
    scene = _scene_or_none(grid)
    return scene is not None and len(scene["holes"]) >= 2


def _witness_alt_background(grid: Any) -> bool:
    scene = _scene_or_none(grid)
    return scene is not None and scene["background"] != 8


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "identity": _rival_identity,
    "solid_fill": _rival_solid_fill,
    "hole_origin_phase": _rival_hole_origin_phase,
    "fixed_2x2_motif": _rival_fixed_2x2,
    "first_hole_only": _rival_first_hole_only,
    "fixed_background_8": _rival_fixed_background_8,
}

SEMANTIC_WITNESSES = {
    "expansion_required": _witness_expansion,
    "sparse_motif": _witness_sparse,
    "phase_offset": _witness_phase_offset,
    "non_2x2_motif": _witness_non_2x2,
    "single_hole": _witness_single,
    "multiple_holes": _witness_multiple,
    "alternate_background": _witness_alt_background,
}

WITNESS_RIVALS = {
    "expansion_required": ["identity"],
    "sparse_motif": ["solid_fill"],
    "phase_offset": ["hole_origin_phase"],
    "non_2x2_motif": ["fixed_2x2_motif"],
    "single_hole": ["identity"],
    "multiple_holes": ["first_hole_only"],
    "alternate_background": ["fixed_background_8"],
}

# Every ordinary draw refutes these two competitors individually, so lesson
# identifiability does not depend on a fragile sample-index schedule.
LESSON_COMPETITORS = {
    "identity": _rival_identity,
    "solid_fill": _rival_solid_fill,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    for name, competitor in LESSON_COMPETITORS.items():
        fits_demos = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if fits_demos and competitor(query["input"]) != query["output"]:
            reasons.append(f"competitor {name!r} fits every demo but changes the query answer")
    return reasons
