"""Generator for ARC task 68bc2e87 (canonical task 809c8b84e40a).

The input is a cyan-8 canvas carrying four or five differently colored hollow
rectangular frames.  Frames are painted in a global bottom-to-top order; at a
border crossing the later frame hides the earlier one.  The Racket oracle
recovers every visible frame bbox, reads those crossing winners as precedence
edges, and emits the unique bottom-to-top color order as an ``n x 1`` strip.

The curriculum deliberately alternates two overlap-graph regimes.  Dense
profiles make every pair cross, while sparse profiles reproduce canonical-like
chains where some frame pairs never meet and their relation is only recoverable
transitively.  Sparse scenes deliberately let some tempting shortcuts fit one
example; the adjacent dense control kills them, while the sparse example kills
the dense-only visible-cell-count shortcut.
"""
from __future__ import annotations

from itertools import permutations
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import draw_frame, full_grid


GENERATOR_ID = "809c8b84e40a"
TASK_ID = GENERATOR_ID
VERSION = "4.0.0"
# Re-pinned to the comment-preserving selected source returned with this repair.
RULE_HASH = "a9ac01cfb199"
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "On cyan (8), four or five distinct-colored rectangular frame outlines are "
    "painted in a global z-order. At every border crossing the later/top frame "
    "is visible. Infer the unique precedence order, including transitive order "
    "between frames that do not directly cross, and output the frame colors as "
    "a one-column strip from bottom to top."
)

INVARIANTS = [
    "background is color 8 and every non-background color denotes one frame",
    "each visible color lies only on the perimeter of its recovered bbox",
    "crossing cells show one of the frame colors whose perimeters meet there",
    "crossing winners induce one acyclic, unique bottom-to-top order",
    "ordinary lessons contain four or five distinct frame colors and no color 0",
]

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

# Canonical sparse geometry from the public training row.  The four-frame case
# is a pure path; the five-frame case has a Hamiltonian path plus a few chords.
_CHAIN4_BOXES = (
    (1, 2, 6, 7),
    (3, 5, 9, 16),
    (7, 9, 13, 13),
    (11, 11, 15, 14),
)
_CHAIN4_PATH = (0, 1, 2, 3)

_CHAIN5_BOXES = (
    (7, 9, 15, 16),
    (1, 1, 16, 5),
    (5, 7, 16, 10),
    (5, 12, 9, 14),
    (3, 3, 14, 18),
)
_CHAIN5_PATH = (1, 4, 2, 0, 3)


def _mirror_h(
    boxes: tuple[tuple[int, int, int, int], ...], width: int
) -> tuple[tuple[int, int, int, int], ...]:
    return tuple((r1, width - 1 - c2, r2, width - 1 - c1) for r1, c1, r2, c2 in boxes)


def _mirror_v(
    boxes: tuple[tuple[int, int, int, int], ...], height: int
) -> tuple[tuple[int, int, int, int], ...]:
    return tuple((height - 1 - r2, c1, height - 1 - r1, c2) for r1, c1, r2, c2 in boxes)


# Alternating dense/sparse order is intentional: every two-consecutive-demo
# window includes both direct pairwise evidence and a transitive-order case.
_PROFILES: dict[str, dict[str, Any]] = {
    "dense_canonical_4_dr": {
        "kind": "dense",
        "h": 18,
        "w": 19,
        "n": 4,
        "box_h": 10,
        "box_w": 11,
        "step": 2,
        "dr": 1,
        "dc": 1,
    },
    "chain_canonical_4": {
        "kind": "chain",
        "h": 18,
        "w": 19,
        "boxes": _CHAIN4_BOXES,
        "path": _CHAIN4_PATH,
    },
    "dense_canonical_5_dl": {
        "kind": "dense",
        "h": 18,
        "w": 19,
        "n": 5,
        "box_h": 12,
        "box_w": 13,
        "step": 1,
        "dr": 1,
        "dc": -1,
    },
    "chain_canonical_5": {
        "kind": "chain",
        "h": 18,
        "w": 19,
        "boxes": _CHAIN5_BOXES,
        "path": _CHAIN5_PATH,
    },
    "dense_wide_4_dr": {
        "kind": "dense",
        "h": 16,
        "w": 22,
        "n": 4,
        "box_h": 8,
        "box_w": 14,
        "step": 2,
        "dr": 1,
        "dc": 1,
    },
    "chain_canonical_4_mirror": {
        "kind": "chain",
        "h": 18,
        "w": 19,
        "boxes": _mirror_h(_CHAIN4_BOXES, 19),
        "path": _CHAIN4_PATH,
    },
    "dense_tall_5_ul": {
        "kind": "dense",
        "h": 22,
        "w": 16,
        "n": 5,
        "box_h": 16,
        "box_w": 10,
        "step": 1,
        "dr": -1,
        "dc": -1,
    },
    "chain_canonical_5_mirror": {
        "kind": "chain",
        "h": 18,
        "w": 19,
        "boxes": _mirror_v(_CHAIN5_BOXES, 18),
        "path": _CHAIN5_PATH,
    },
}
SCHEDULE_PROFILES = tuple(_PROFILES)
_BAND_OFFSETS = {None: 0, "easy": 0, "medium": 2, "hard": 4}

AXES = {
    "scene_profile": {
        "type": "enum",
        "default": "seeded alternating dense/sparse canonical-anchored schedule",
        "valid": [
            "dense_canonical_4_dr",
            "chain_canonical_4",
            "dense_canonical_5_dl",
            "chain_canonical_5",
            "dense_wide_4_dr",
            "chain_canonical_4_mirror",
            "dense_tall_5_ul",
            "chain_canonical_5_mirror",
        ],
        "doc": "Exact recoverable frame-geometry profile.",
    }
}
# The one declared axis is independent; every profile is legal in every band.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, Any], ...] = ()


def _band_offset(difficulty: Any) -> int:
    if difficulty not in _BAND_OFFSETS:
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    return _BAND_OFFSETS[difficulty]


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Deterministic curriculum slot with alternating overlap topology."""
    return SCHEDULE_PROFILES[
        (int(sample_index) + int(seed) // 3 + _band_offset(difficulty))
        % len(SCHEDULE_PROFILES)
    ]


def _dense_boxes(profile: dict[str, Any]) -> tuple[tuple[int, int, int, int], ...]:
    h, w, n = profile["h"], profile["w"], profile["n"]
    box_h, box_w, step = profile["box_h"], profile["box_w"], profile["step"]
    dr, dc = profile["dr"], profile["dc"]
    max_shift = step * (n - 1)
    top0 = 1 if dr > 0 else h - box_h - 1
    left0 = 1 if dc > 0 else w - box_w - 1
    boxes = []
    for index in range(n):
        top = top0 + dr * step * index
        left = left0 + dc * step * index
        boxes.append((top, left, top + box_h - 1, left + box_w - 1))
    if max_shift <= 0:
        raise AssertionError("dense profile must shift between frames")
    return tuple(boxes)


def _profile_boxes(name: str) -> tuple[tuple[int, int, int, int], ...]:
    profile = _PROFILES[name]
    if profile["kind"] == "dense":
        return _dense_boxes(profile)
    return tuple(profile["boxes"])


def _outline_hits(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return {
        (r, c)
        for r in range(r1, r2 + 1)
        for c in range(c1, c2 + 1)
        if r in (r1, r2) or c in (c1, c2)
    }


def _coerce_grid(grid: Any) -> list[list[int]]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return []
    out: list[list[int]] = []
    for row in grid:
        if isinstance(row, str):
            try:
                values = [int(value) for value in row]
            except ValueError:
                return []
        elif isinstance(row, (list, tuple)):
            values = []
            for value in row:
                if isinstance(value, bool) or not isinstance(value, int):
                    return []
                values.append(value)
        else:
            return []
        out.append(values)
    return out


def _frame_bbox(grid: list[list[int]], color: int) -> tuple[int, int, int, int] | None:
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color]
    if not cells:
        return None
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _bottom_to_top_order(
    colors: list[int], edges: set[tuple[int, int]]
) -> tuple[list[int], bool, bool]:
    """Return (order, unique, acyclic) for edges encoded as (top, bottom)."""
    remaining = set(colors)
    order: list[int] = []
    unique = True
    while remaining:
        candidates = [
            color
            for color in remaining
            if not any(top == color and bottom in remaining for top, bottom in edges)
        ]
        if not candidates:
            return order, False, False
        if len(candidates) != 1:
            unique = False
        chosen = min(candidates)
        order.append(chosen)
        remaining.remove(chosen)
    return order, unique, True


def _analysis(grid: Any) -> dict[str, Any]:
    g = _coerce_grid(grid)
    errors: list[str] = []
    if not g or not g[0] or any(len(row) != len(g[0]) for row in g):
        return {"grid": g, "errors": ["grid must be nonempty and rectangular"]}

    h, w = len(g), len(g[0])
    for r, row in enumerate(g):
        for c, value in enumerate(row):
            if not 0 <= value <= 9:
                errors.append(f"cell ({r},{c}) has non-ARC color {value!r}")
    palette = sorted({value for row in g for value in row})
    if 8 not in palette:
        errors.append("cyan background color 8 is absent")
    if 0 in palette:
        errors.append("color 0 is not part of the frame/background grammar")
    colors = [value for value in palette if value != 8]
    if not 4 <= len(colors) <= 5:
        errors.append(f"expected four or five non-background frame colors, got {colors}")

    boxes: dict[int, tuple[int, int, int, int]] = {}
    outlines: dict[int, set[tuple[int, int]]] = {}
    visible_counts: dict[int, int] = {}
    for color in colors:
        box = _frame_bbox(g, color)
        if box is None:
            continue
        r1, c1, r2, c2 = box
        if r2 <= r1 or c2 <= c1:
            errors.append(f"frame color {color} has degenerate bbox {box}")
        boxes[color] = box
        outlines[color] = _outline_hits(box)
        visible_counts[color] = sum(value == color for row in g for value in row)

    if len(set(boxes.values())) != len(boxes):
        errors.append("two colors recover the same frame bbox")

    edges: set[tuple[int, int]] = set()
    crossing_pairs: set[frozenset[int]] = set()
    for r, row in enumerate(g):
        for c, visible in enumerate(row):
            owners = [color for color, outline in outlines.items() if (r, c) in outline]
            if not owners:
                if visible != 8:
                    errors.append(
                        f"cell ({r},{c})={visible} lies outside every recovered frame perimeter"
                    )
                continue
            if visible not in owners:
                errors.append(
                    f"cell ({r},{c})={visible} is not one of perimeter owners {sorted(owners)}"
                )
                continue
            if len(owners) >= 2:
                for other in owners:
                    if other != visible:
                        edges.add((visible, other))
                        crossing_pairs.add(frozenset((visible, other)))

    order, unique, acyclic = _bottom_to_top_order(colors, edges)
    if not acyclic:
        errors.append("crossing winners contain a z-order cycle")
    elif not unique:
        errors.append("crossing winners do not determine one unique bottom-to-top order")
    if len(order) != len(colors):
        errors.append(f"z-order contains {len(order)} of {len(colors)} frame colors")

    box_set = frozenset(boxes.values())
    scene_profile = None
    for name, profile in _PROFILES.items():
        if h == profile["h"] and w == profile["w"] and box_set == frozenset(_profile_boxes(name)):
            scene_profile = name
            break

    return {
        "grid": g,
        "errors": errors,
        "h": h,
        "w": w,
        "colors": colors,
        "boxes": boxes,
        "outlines": outlines,
        "visible_counts": visible_counts,
        "edges": edges,
        "crossing_pairs": crossing_pairs,
        "order": order,
        "scene_profile": scene_profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the authority-aligned frame grammar and exact declared axes."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and requested is not None and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def observe_overrides(grid) -> dict[str, Any]:
    """Recover every exact declared semantic axis from an ordinary generated grid."""
    return {"scene_profile": _analysis(grid).get("scene_profile")}


def strict_canonical_like(grid) -> list[str]:
    """Task-linked strict predicate: valid frames plus a unique global z-order."""
    return self_check(grid)


def _correct_output(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("input is outside the frame-z-order teaching grammar")
    return [[color] for color in analysis["order"]]


def _numeric_ascending(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input")
    return [[color] for color in sorted(analysis["colors"])]


def _spatial_top_left(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input")
    colors = sorted(
        analysis["colors"],
        key=lambda color: (*analysis["boxes"][color], color),
    )
    return [[color] for color in colors]


def _visible_count_ascending(grid: Any) -> list[list[int]]:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("malformed input")
    colors = sorted(
        analysis["colors"],
        key=lambda color: (analysis["visible_counts"][color], color),
    )
    return [[color] for color in colors]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "numeric_ascending": _numeric_ascending,
    "spatial_top_left": _spatial_top_left,
    "visible_count_ascending": _visible_count_ascending,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _pairwise_crossing(analysis: dict[str, Any]) -> bool:
    colors = analysis["colors"]
    need = len(colors) * (len(colors) - 1) // 2
    return len(analysis["crossing_pairs"]) == need


def _witness(predicate: Callable[[dict[str, Any]], bool]) -> Callable[[Any], bool]:
    def wrapped(grid: Any) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(predicate(analysis))

    return wrapped


SEMANTIC_WITNESSES = {
    "dense_direct_comparisons": _witness(_pairwise_crossing),
    "transitive_nonpairwise_order": _witness(lambda a: not _pairwise_crossing(a)),
    "numeric_order_rebuttal": _witness(
        lambda a: _numeric_ascending(a["grid"]) != [[c] for c in a["order"]]
    ),
    "spatial_order_rebuttal": _witness(
        lambda a: _spatial_top_left(a["grid"]) != [[c] for c in a["order"]]
    ),
    "visible_count_rebuttal": _witness(
        lambda a: _visible_count_ascending(a["grid"]) != [[c] for c in a["order"]]
    ),
}
WITNESS_RIVALS = {
    "dense_direct_comparisons": ["spatial_top_left"],
    "transitive_nonpairwise_order": ["visible_count_ascending"],
    "numeric_order_rebuttal": ["numeric_ascending"],
    "spatial_order_rebuttal": ["spatial_top_left"],
    "visible_count_rebuttal": ["visible_count_ascending"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every two-demo lesson to teach crossing order, not a shortcut."""
    reasons: list[str] = []
    if len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]

    valid_demos = []
    dense_seen = False
    transitive_seen = False
    for index, pair in enumerate(demos):
        try:
            expected = _correct_output(pair.get("input"))
        except ValueError:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if pair.get("output") != expected:
            reasons.append(f"demo {index} output is not the inferred bottom-to-top order")
        analysis = _analysis(pair.get("input"))
        dense_seen = dense_seen or _pairwise_crossing(analysis)
        transitive_seen = transitive_seen or not _pairwise_crossing(analysis)
        valid_demos.append(pair)

    if not dense_seen:
        reasons.append("demonstrations omit a dense direct-comparison frame graph")
    if not transitive_seen:
        reasons.append("demonstrations omit a transitive non-pairwise frame graph")

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(pair.get("input")) == pair.get("output") for pair in valid_demos):
            reasons.append(f"demonstrations do not falsify rival rule {name}")

    try:
        expected_query = _correct_output(query.get("input"))
    except ValueError:
        reasons.append("query input is outside the teaching grammar")
        return reasons
    if query.get("output") != expected_query:
        reasons.append("query output is not the inferred bottom-to-top order")
    return reasons


def _draw_axis_choice(ctx, overrides: dict[str, Any], name: str, scheduled: Any, options):
    if overrides.get(name) is not None:
        return ctx.draw_choice(name, options)
    return ctx.draw_choice(name, (scheduled,))


def _render_scene(
    h: int,
    w: int,
    boxes: tuple[tuple[int, int, int, int], ...],
    colors: list[int],
    order: tuple[int, ...],
) -> list[list[int]]:
    grid = full_grid(h, w, 8)
    for index in order:
        draw_frame(grid, *boxes[index], colors[index])
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _band_offset(difficulty)
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    scheduled = schedule_profile(seed, sample_index, difficulty)
    profile_name = _draw_axis_choice(
        ctx, overrides, "scene_profile", scheduled, SCHEDULE_PROFILES
    )
    profile = _PROFILES[profile_name]
    h, w = profile["h"], profile["w"]
    boxes = _profile_boxes(profile_name)
    n_frames = len(boxes)

    colors = list(ctx.draw_distinct_colors("frame_colors", n=n_frames, exclude={0, 8}))
    rng = ctx.draw_rng("layout")

    if profile["kind"] == "dense":
        # Dense scenes are shortcut-killing controls.  Vary both color placement
        # and z-order until none of the named non-semantic sort rules fit.
        rng.shuffle(colors)
        orders = list(permutations(range(n_frames)))
        rng.shuffle(orders)
    else:
        # Sparse scenes are deliberate anchors: map ascending color labels along
        # the canonical Hamiltonian path and paint that path bottom-to-top.  A
        # numeric-sort shortcut therefore fits this *single* demo, but the
        # adjacent dense control in every two-demo window kills it.  This makes
        # the curriculum teach why crossing evidence matters instead of merely
        # banning locally ambiguous examples.
        path = tuple(profile["path"])
        ordered_colors = sorted(colors)
        colors = [0] * n_frames
        for rank, box_index in enumerate(path):
            colors[box_index] = ordered_colors[rank]
        orders = [path]

    chosen = None
    for order in orders:
        grid = _render_scene(h, w, boxes, colors, tuple(order))
        analysis = _analysis(grid)
        if analysis["errors"]:
            continue
        expected = [[color] for color in analysis["order"]]
        if profile["kind"] == "dense" and any(
            SEMANTIC_RIVALS[name](grid) == expected
            for name in ("numeric_ascending", "spatial_top_left")
        ):
            continue
        chosen = grid
        break
    if chosen is None:
        raise AssertionError(
            f"could not realize shortcut-rebutting z-order for profile {profile_name}"
        )

    errors = self_check(
        chosen,
        difficulty=difficulty,
        meta={"overrides": ctx.recorded_draws()},
    )
    if errors:
        raise AssertionError("generated invalid frame-z-order lesson: " + "; ".join(errors))
    return chosen
