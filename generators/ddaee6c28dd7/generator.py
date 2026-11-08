"""Semantic generator for ARC task ``ddaee6c28dd7``.

The input contains several separated, monochrome objects on background 0.
Exactly one object has the greatest bounding-box width.  The canonical Racket
rule crops that object to its bounding box, preserves its mask, and recolors
all of its cells to 8.

Version 2 replaces the old inert palette/texture aliases and fallible random
placement with a joint feasible-spec draw, exact observable axes, constructive
backtracking placement, and a mutation-sensitive structural ``self_check``.
"""
from __future__ import annotations

import hashlib
from itertools import product
from numbers import Real
from typing import Any, Iterable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid
from puzzle_generators.helpers.selfcheck import components, components_have_clearance


GENERATOR_ID = "ddaee6c28dd7"
TASK_ID = GENERATOR_ID
VERSION = "2.4.0"
RULE_HASH = "4a26a7475b9d"  # sha256[:12] of whitespace-normalized canonical rule
SUMMARY = (
    "Select the unique component with the widest bounding box, crop its exact "
    "mask to that box, and recolor the selected cells to 8."
)
INVARIANTS = [
    "background is 0 and input color 8 is absent",
    "there are 2..5 separated monochrome 4-connected components",
    "exactly one component has the maximum bounding-box width",
    "at least one distractor is exactly one column narrower than the target",
    "target color, shape, size, and position vary independently of selection",
]

WINNER_PROFILES = ("bar", "path", "frame", "solid")
_ALLOWED_COLORS = (1, 2, 3, 4, 5, 6, 7, 9)
_DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))

AXES = {
    "height": {
        "type": "int",
        "default": "difficulty-linked feasible joint draw",
        "valid": "8..16",
        "doc": "Exact returned canvas height.",
    },
    "width": {
        "type": "int",
        "default": "difficulty-linked feasible joint draw",
        "valid": "11..20",
        "doc": "Exact returned canvas width.",
    },
    "distractor_count": {
        "type": "int",
        "default": "2 easy / 2..4 medium-hard",
        "valid": "1..4",
        "doc": "Exact number of non-target components.",
    },
    "winner_w": {
        "type": "int",
        "default": "4..5 easy / 5..7 medium / 6..8 hard",
        "valid": "4..8",
        "doc": "Exact bounding-box width of the unique selected component.",
    },
    "winner_h": {
        "type": "int",
        "default": "profile-linked 1..4",
        "valid": "1..4",
        "doc": "Exact bounding-box height of the unique selected component.",
    },
    "winner_color": {
        "type": "color",
        "default": "keyed seed draw rotated by sample_index for lesson spread",
        "valid": "1..9 (!=8)",
        "doc": "Exact input color of the selected component.",
    },
    "winner_profile": {
        "type": "str",
        "default": "seed-keyed lesson rotation over four morphology classes",
        "valid": "bar|path|frame|solid",
        "doc": "Recoverable target morphology class.",
    },
}

_GLOBAL_DOMAINS = {
    "height": tuple(range(8, 17)),
    "width": tuple(range(11, 21)),
    "distractor_count": tuple(range(1, 5)),
    "winner_w": tuple(range(4, 9)),
    "winner_h": tuple(range(1, 5)),
    "winner_color": _ALLOWED_COLORS,
    "winner_profile": WINNER_PROFILES,
}

_BAND_DOMAINS = {
    "easy": {
        "height": tuple(range(8, 12)),
        "width": tuple(range(11, 16)),
        "distractor_count": (2, 3),
        "winner_w": (4, 5),
        "winner_h": (1, 2, 3),
    },
    "medium": {
        "height": tuple(range(10, 15)),
        "width": tuple(range(14, 19)),
        "distractor_count": (2, 3, 4),
        "winner_w": (5, 6, 7),
        "winner_h": (1, 2, 3, 4),
    },
    "hard": {
        "height": tuple(range(13, 17)),
        "width": tuple(range(17, 21)),
        "distractor_count": (3, 4),
        "winner_w": (6, 7, 8),
        "winner_h": (2, 3, 4),
    },
}
_LESSON_PROFILE_PATTERNS = {
    # Demo 0 is always a sparse path so the sample_index==0 area challenger
    # can be strictly larger.  Seed-keyed patterns vary query morphology while
    # keeping sparse paths dominant enough to avoid a tiny fixed-mask grammar.
    "easy": (
        ("path", "path", "bar", "path"),
        ("path", "frame", "path", "path"),
        ("path", "path", "solid", "frame"),
        ("path", "bar", "path", "solid"),
    ),
    "medium": (
        ("path", "frame", "path", "path"),
        ("path", "path", "solid", "frame"),
        ("path", "bar", "path", "solid"),
        ("path", "path", "frame", "bar"),
    ),
    "hard": (
        ("path", "frame", "path", "path"),
        ("path", "path", "solid", "frame"),
        ("path", "solid", "path", "path"),
        ("path", "path", "frame", "solid"),
    ),
}


def _difficulty_band(difficulty: Any) -> str:
    if difficulty is None:
        return "medium"
    if isinstance(difficulty, str):
        if difficulty not in _BAND_DOMAINS:
            raise ValueError("difficulty must be easy, medium, hard, or numeric 0..1")
        return difficulty
    if isinstance(difficulty, bool) or not isinstance(difficulty, Real):
        raise ValueError("difficulty must be easy, medium, hard, or numeric 0..1")
    value = float(difficulty)
    if not 0.0 <= value <= 1.0:
        raise ValueError("numeric difficulty must lie in 0..1")
    return "easy" if value < 1 / 3 else "hard" if value > 2 / 3 else "medium"


def _coerce_override(name: str, value: Any) -> Any:
    domain = _GLOBAL_DOMAINS[name]
    if name == "winner_profile":
        if not isinstance(value, str) or value not in domain:
            raise ValueError(f"{name} must be one of {domain!r}")
        return value
    if isinstance(value, bool):
        raise ValueError(f"{name} must be an integer, not bool")
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped or stripped.lstrip("-").isdigit() is False:
            raise ValueError(f"{name} must be an exact integer")
        value = int(stripped)
    if not isinstance(value, int):
        raise ValueError(f"{name} must be an exact integer")
    if value not in domain:
        raise ValueError(f"{name}={value!r} outside declared domain {domain!r}")
    return value


def _profile_compatible(profile: str, winner_h: int) -> bool:
    if profile == "bar":
        return winner_h == 1
    if profile == "frame":
        return winner_h >= 3
    return winner_h >= 2


def _bbox_size(shape: Iterable[tuple[int, int]]) -> tuple[int, int]:
    shape = tuple(shape)
    return (
        max(row for row, _ in shape) + 1,
        max(col for _, col in shape) + 1,
    )


def _normalize(shape: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    shape = tuple(shape)
    r0 = min(row for row, _ in shape)
    c0 = min(col for _, col in shape)
    return tuple(sorted((row - r0, col - c0) for row, col in shape))


def _make_path(height: int, width: int, rng) -> tuple[tuple[int, int], ...]:
    """Connected sparse shape with exact bbox, not a bar/frame/solid."""
    steps = [(1, 0)] * (height - 1) + [(0, 1)] * (width - 1)
    rng.shuffle(steps)
    row = col = 0
    cells = {(row, col)}
    for dr, dc in steps:
        row += dr
        col += dc
        cells.add((row, col))
    # Add a few keyed branches without ever filling the rectangle.
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if (row, col) not in cells
        and any((row + dr, col + dc) in cells for dr, dc in _DIR4)
    ]
    rng.shuffle(candidates)
    cap = min(len(candidates), max(0, (height * width - len(cells)) // 3))
    for cell in candidates[: rng.randint(0, cap) if cap else 0]:
        cells.add(cell)
    border = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }
    if cells == border or len(cells) == height * width:
        # A monotone endpoint path is always a lawful sparse fallback.
        row = col = 0
        cells = {(0, 0)}
        for dr, dc in steps:
            row += dr
            col += dc
            cells.add((row, col))
    return tuple(sorted(cells))


def _winner_shape(profile: str, height: int, width: int, rng):
    if profile == "bar":
        return tuple((0, col) for col in range(width))
    if profile == "solid":
        return tuple(product(range(height), range(width)))
    if profile == "frame":
        return tuple(
            (row, col)
            for row in range(height)
            for col in range(width)
            if row in (0, height - 1) or col in (0, width - 1)
        )
    return _make_path(height, width, rng)


def _distractor_shape(height: int, width: int, mode: str, rng):
    if height == 1:
        return tuple((0, col) for col in range(width))
    if mode == "solid":
        return tuple(product(range(height), range(width)))
    if mode == "frame" and height >= 3 and width >= 3:
        return tuple(
            (row, col)
            for row in range(height)
            for col in range(width)
            if row in (0, height - 1) or col in (0, width - 1)
        )
    return _make_path(height, width, rng)


def _candidate_domains(band: str, requested: dict[str, Any], *, preferred: bool):
    source = _BAND_DOMAINS[band] if preferred else _GLOBAL_DOMAINS
    domains = {}
    for name in ("height", "width", "distractor_count", "winner_w", "winner_h"):
        domains[name] = (requested[name],) if name in requested else source[name]
    return domains


def _semantic_specs(
    band: str,
    scheduled: str,
    requested: dict[str, Any],
    rng,
):
    requested_profile = requested.get("winner_profile")

    def build(preferred: bool, force_scheduled: bool):
        domains = _candidate_domains(band, requested, preferred=preferred)
        if requested_profile is not None:
            profiles = (requested_profile,)
        elif force_scheduled:
            profiles = (scheduled,)
        else:
            profiles = WINNER_PROFILES
        specs = []
        for height, width, count, winner_w, winner_h, profile in product(
            domains["height"],
            domains["width"],
            domains["distractor_count"],
            domains["winner_w"],
            domains["winner_h"],
            profiles,
        ):
            if winner_w > width or winner_h > height:
                continue
            if not _profile_compatible(profile, winner_h):
                continue
            # Necessary packing lower bound with one-cell separation.  It is
            # intentionally loose; constructive placement is the final test.
            nonzero_capacity = height * width
            minimum_cells = winner_w + count
            if nonzero_capacity < minimum_cells:
                continue
            specs.append((height, width, count, winner_w, winner_h, profile))
        rng.shuffle(specs)
        return specs

    # Preserve the profile schedule on ordinary draws when feasible. Exact
    # overrides may legitimately require a different morphology.
    for preferred, force_scheduled in ((True, True), (True, False), (False, False)):
        specs = build(preferred, force_scheduled)
        if specs:
            yield from specs


def _blocked_cells(cells: set[tuple[int, int]], height: int, width: int):
    blocked = set()
    for row, col in cells:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                rr, cc = row + dr, col + dc
                if 0 <= rr < height and 0 <= cc < width:
                    blocked.add((rr, cc))
    return blocked


def _pack_shapes(height: int, width: int, shapes, rng):
    """Place all shapes with an eight-neighbour zero moat via backtracking."""
    indexed = list(enumerate(shapes))
    indexed.sort(key=lambda item: (_bbox_size(item[1])[0] * _bbox_size(item[1])[1]), reverse=True)
    placements = {}
    nodes = 0

    def rec(index: int, blocked: set[tuple[int, int]]) -> bool:
        nonlocal nodes
        if index == len(indexed):
            return True
        if nodes > 25000:
            return False
        object_index, shape = indexed[index]
        shape_h, shape_w = _bbox_size(shape)
        candidates = [
            (top, left)
            for top in range(height - shape_h + 1)
            for left in range(width - shape_w + 1)
        ]
        rng.shuffle(candidates)
        for top, left in candidates:
            nodes += 1
            cells = {(top + row, left + col) for row, col in shape}
            if cells & blocked:
                continue
            placements[object_index] = (top, left)
            if rec(index + 1, blocked | _blocked_cells(cells, height, width)):
                return True
            placements.pop(object_index, None)
        return False

    if not rec(0, set()):
        return None
    return [placements[index] for index in range(len(shapes))]


def _build_scene(spec, winner_color: int, ctx, sample_index: int):
    height, width, count, winner_w, winner_h, profile = spec
    shape_rng = ctx.draw_rng(
        f"shapes:{height}:{width}:{count}:{winner_w}:{winner_h}:{profile}"
    )
    winner = _winner_shape(profile, winner_h, winner_w, shape_rng)
    winner_area = len(winner)

    # The first distractor is always the near-width challenger.  A disjoint
    # sample-index schedule supplies area and height counterexamples to common
    # shortcuts whenever geometry permits.
    challenge = sample_index % 3
    distractors = []
    for index in range(count):
        dw = winner_w - 1 if index == 0 else shape_rng.randint(1, winner_w - 1)
        max_dh = min(4, height)
        if index == 0 and challenge == 0:
            dh = max_dh
            mode = "solid"
        elif index == 0 and challenge == 1 and winner_h < max_dh:
            dh = max_dh
            mode = "path"
        else:
            dh = shape_rng.randint(1, max_dh)
            mode = shape_rng.choice(("path", "solid", "frame"))
        shape = _distractor_shape(dh, dw, mode, shape_rng)
        distractors.append(shape)

    # If an area-challenge draw is possible, make it real.  Otherwise the
    # lesson still remains valid and the census records the fallback branch.
    if challenge == 0 and len(distractors[0]) <= winner_area:
        dh = min(4, height)
        candidate = _distractor_shape(dh, winner_w - 1, "solid", shape_rng)
        if len(candidate) > winner_area:
            distractors[0] = candidate

    shapes = [winner, *distractors]
    placement_rng = ctx.draw_rng(
        f"placement:{height}:{width}:{count}:{winner_w}:{winner_h}:{profile}"
    )
    placements = _pack_shapes(height, width, shapes, placement_rng)
    if placements is None:
        return None

    available = [color for color in _ALLOWED_COLORS if color != winner_color]
    color_rng = ctx.draw_rng("distractor_colors")
    color_rng.shuffle(available)
    colors = [winner_color, *available[:count]]
    grid = full_grid(height, width, 0)
    for shape, color, (top, left) in zip(shapes, colors, placements):
        for row, col in shape:
            grid[top + row][left + col] = color
    return grid


def _validate_grid(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty row sequence"], 0, 0
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"], len(grid), 0
    height, width = len(grid), len(grid[0])
    for row in grid:
        if not isinstance(row, (list, tuple)) or len(row) != width:
            return ["grid must be rectangular"], height, width
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be integer ARC colors 0..9"], height, width
    return errors, height, width


def _profile_of(comp) -> str:
    r1, c1, r2, c2 = comp["bbox"]
    height, width = r2 - r1 + 1, c2 - c1 + 1
    normalized = set(comp["norm"])
    if height == 1 and len(normalized) == width:
        return "bar"
    if len(normalized) == height * width:
        return "solid"
    border = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if row in (0, height - 1) or col in (0, width - 1)
    }
    if height >= 3 and normalized == border:
        return "frame"
    return "path"


def _analyze(grid):
    errors, height, width = _validate_grid(grid)
    result = {
        "errors": errors,
        "height": height,
        "width": width,
        "components": [],
        "winner": None,
        "distractors": [],
        "winner_w": None,
        "winner_h": None,
        "winner_color": None,
        "winner_profile": None,
        "area_relation": None,
    }
    if errors:
        return result
    if any(8 in row for row in grid):
        errors.append("input color 8 is forbidden; 8 is reserved for the answer")

    comps = components([list(row) for row in grid], same_color=True, connectivity=4)
    result["components"] = comps
    if not 2 <= len(comps) <= 5:
        errors.append(f"expected 2..5 components, found {len(comps)}")
        return result
    if not components_have_clearance(grid, comps, diagonal=True):
        errors.append("components must be separated by an eight-neighbour zero moat")

    colors = [comp["color"] for comp in comps]
    if len(set(colors)) != len(colors):
        errors.append("every component must have a distinct input color")

    widths = []
    for comp in comps:
        r1, c1, r2, c2 = comp["bbox"]
        widths.append(c2 - c1 + 1)
    max_width = max(widths)
    winners = [comp for comp, comp_width in zip(comps, widths) if comp_width == max_width]
    if len(winners) != 1:
        errors.append(f"widest component must be unique, found {len(winners)}")
        return result
    winner = winners[0]
    distractors = [comp for comp in comps if comp is not winner]
    r1, c1, r2, c2 = winner["bbox"]
    winner_h, winner_w = r2 - r1 + 1, c2 - c1 + 1
    result.update(
        {
            "winner": winner,
            "distractors": distractors,
            "winner_w": winner_w,
            "winner_h": winner_h,
            "winner_color": winner["color"],
            "winner_profile": _profile_of(winner),
        }
    )
    if winner_w < 4:
        errors.append(f"winner width must be at least 4, found {winner_w}")
    distractor_widths = []
    for comp in distractors:
        dr1, dc1, dr2, dc2 = comp["bbox"]
        distractor_widths.append(dc2 - dc1 + 1)
    if any(comp_width >= winner_w for comp_width in distractor_widths):
        errors.append("every distractor must be strictly narrower than the winner")
    if winner_w - 1 not in distractor_widths:
        errors.append("a near-width distractor exactly one column narrower is required")

    winner_area = len(winner["cells"])
    distractor_areas = [len(comp["cells"]) for comp in distractors]
    if max(distractor_areas) > winner_area:
        result["area_relation"] = "distractor_larger"
    elif max(distractor_areas) == winner_area:
        result["area_relation"] = "area_tie"
    else:
        result["area_relation"] = "winner_largest"
    return result


def observe_overrides(grid):
    """Recover every declared exact axis from the returned input grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    return {
        "height": analysis["height"],
        "width": analysis["width"],
        "distractor_count": len(analysis["distractors"]),
        "winner_w": analysis["winner_w"],
        "winner_h": analysis["winner_h"],
        "winner_color": analysis["winner_color"],
        "winner_profile": analysis["winner_profile"],
    }


def semantic_signature(grid):
    """Task-linked observables used by the review census and focused tests."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    winner = analysis["winner"]
    distractors = analysis["distractors"]
    r1, c1, r2, c2 = winner["bbox"]
    distractor_heights = [comp["bbox"][2] - comp["bbox"][0] + 1 for comp in distractors]
    distractor_widths = [comp["bbox"][3] - comp["bbox"][1] + 1 for comp in distractors]
    return {
        **observe_overrides(grid),
        "winner_area": len(winner["cells"]),
        "winner_top_left": (r1, c1),
        "winner_touches_border": r1 == 0 or c1 == 0 or r2 == analysis["height"] - 1 or c2 == analysis["width"] - 1,
        "winner_mask": tuple(winner["norm"]),
        "area_relation": analysis["area_relation"],
        "has_taller_distractor": max(distractor_heights) > analysis["winner_h"],
        "distractor_widths": tuple(sorted(distractor_widths)),
        "palette": tuple(sorted(comp["color"] for comp in analysis["components"])),
    }


def rule_mirror(grid):
    """Test-only mirror; the canonical Racket program remains authoritative."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        raise ValueError("; ".join(analysis["errors"]))
    winner = analysis["winner"]
    r1, c1, r2, c2 = winner["bbox"]
    cells = set(winner["cells"])
    return [
        [8 if (row, col) in cells else 0 for col in range(c1, c2 + 1)]
        for row in range(r1, r2 + 1)
    ]


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed or shortcut-revealing lesson inputs."""
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = {name: meta[name] for name in AXES if name in meta}
        observed = observe_overrides(grid)
        for name, value in requested.items():
            if name in AXES and observed.get(name) != value:
                errors.append(
                    f"{name} metadata requested {value!r}, observed {observed.get(name)!r}"
                )
    return errors


def mutation_fixtures():
    """Declared structural impostors that every valid checker must reject."""
    no_components = full_grid(8, 11, 0)

    single_component = full_grid(8, 11, 0)
    for col in range(4):
        single_component[2][2 + col] = 3

    tied_widest = full_grid(8, 11, 0)
    for col in range(4):
        tied_widest[1][1 + col] = 2
        tied_widest[6][6 + col] = 4

    missing_near_challenger = full_grid(8, 11, 0)
    for col in range(5):
        missing_near_challenger[1][1 + col] = 2
    for row, col in ((5, 1), (5, 2), (6, 1)):
        missing_near_challenger[row][col] = 4

    touching_components = full_grid(8, 11, 0)
    for col in range(5):
        touching_components[2][1 + col] = 2
    for col in range(4):
        touching_components[3][2 + col] = 4

    answer_color_leak = full_grid(8, 11, 0)
    for col in range(5):
        answer_color_leak[1][1 + col] = 8
    for col in range(4):
        answer_color_leak[6][5 + col] = 3

    return [
        ("no_components", no_components),
        ("single_component", single_component),
        ("tied_widest", tied_widest),
        ("missing_near_challenger", missing_near_challenger),
        ("touching_components", touching_components),
        ("answer_color_leak", answer_color_leak),
    ]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)}")
    requested = {
        name: _coerce_override(name, value)
        for name, value in overrides.items()
        if value is not None
    }
    band = _difficulty_band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=requested,
    )
    spec_rng = ctx.draw_rng("scene_spec_order")
    winner_color = requested.get("winner_color")
    if winner_color is None:
        # A keyed per-seed anchor plus the sequential sample offset guarantees
        # distinct target colors across the first three lesson demonstrations.
        # The selected object is still identified only by width, and exact
        # winner_color overrides bypass this schedule unchanged.
        lesson_key = f"{TASK_ID}|{VERSION}|{seed!r}|{band}|winner_color_anchor"
        anchor = int.from_bytes(
            hashlib.sha256(lesson_key.encode("utf-8")).digest()[:8], "big"
        ) % len(_ALLOWED_COLORS)
        winner_color = _ALLOWED_COLORS[(anchor + sample_index) % len(_ALLOWED_COLORS)]

    profile_patterns = _LESSON_PROFILE_PATTERNS[band]
    profile_key = f"{TASK_ID}|{VERSION}|{seed!r}|{band}|winner_profile_pattern"
    profile_pattern_index = int.from_bytes(
        hashlib.sha256(profile_key.encode("utf-8")).digest()[:8], "big"
    ) % len(profile_patterns)
    profile_pattern = profile_patterns[profile_pattern_index]
    scheduled_profile = profile_pattern[sample_index % len(profile_pattern)]

    tried = set()
    for spec in _semantic_specs(band, scheduled_profile, requested, spec_rng):
        if spec in tried:
            continue
        tried.add(spec)
        grid = _build_scene(spec, winner_color, ctx, sample_index)
        if grid is None:
            continue
        analysis = _analyze(grid)
        if analysis["errors"]:
            continue
        height, width, count, winner_w, winner_h, profile = spec
        # Pin every exact semantic value through the public GenCtx draw API so
        # ordinary draws and explicit overrides have auditable provenance.
        ctx.draw_int("height", height, height)
        ctx.draw_int("width", width, width)
        ctx.draw_int("distractor_count", count, count)
        ctx.draw_int("winner_w", winner_w, winner_w)
        ctx.draw_int("winner_h", winner_h, winner_h)
        ctx.draw_choice("winner_color", (winner_color,))
        ctx.draw_choice("winner_profile", (profile,))
        return [list(row) for row in grid]

    detail = ", ".join(f"{name}={value!r}" for name, value in sorted(requested.items()))
    raise ValueError(
        "incompatible overrides: no separated scene can realize the requested "
        f"widest-object grammar on an 8..16 by 11..20 canvas ({detail or 'defaults'})"
    )
