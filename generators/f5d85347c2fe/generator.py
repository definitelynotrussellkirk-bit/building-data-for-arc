"""Generator for ARC task f5d85347c2fe — fill each gray frame from its dot.

Each input contains two or three separated color-5 rectangular outline frames.
Every frame encloses exactly one non-{0,5} dot.  The output preserves the grid
and the gray borders, but fills every cell of each strict frame interior with
that frame's dot color.

The curriculum deliberately includes three canonical morphology profiles and a
three-frame / larger-rectangle rebuttal profile.  Repeated dot colors and
relative dot positions are scheduled independently so a lesson cannot teach
"two frames only", "all dot colors must differ", "use the first dot everywhere",
or a fixed frame-size shortcut.
"""
from __future__ import annotations

from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "f5d85347c2fe"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "8389730df0cc"
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.70

SUMMARY = (
    "Find every separated color-5 rectangular outline.  Each strict interior "
    "contains exactly one colored dot.  Fill that entire interior with its own "
    "dot color while preserving the color-5 border and all exterior background."
)

INVARIANTS = [
    "background is 0 and frame borders are color 5",
    "each color-5 component is a complete rectangular outline at least 4x4",
    "each strict frame interior contains exactly one non-{0,5} dot",
    "frames have a one-cell exterior moat and do not nest, overlap, or touch",
    "all non-background input cells belong to a frame border or its single dot",
]

PROFILES = ("canonical_11", "canonical_12", "canonical_13", "broad_three")
COLOR_RELATIONS = ("distinct", "repeated")
DOT_LAYOUTS = ("same_relative", "different_relative")
SCHEDULE_PROFILES = PROFILES

# Only exact, returned-grid-observable controls are declared.  Position jitter,
# palette labels, and difficulty are nuisance variables rather than metadata
# claims.  Keeping the contract small makes every cross-product lawful.
AXES = {
    "profile": {
        "type": "str",
        "default": "four-draw canonical_11|canonical_12|canonical_13|broad_three schedule",
        "valid": "|".join(PROFILES),
    },
    "color_relation": {
        "type": "str",
        "default": "scheduled distinct|repeated",
        "valid": "|".join(COLOR_RELATIONS),
    },
    "dot_layout": {
        "type": "str",
        "default": "scheduled same_relative|different_relative",
        "valid": "|".join(DOT_LAYOUTS),
    },
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

# (height, width, frame boxes), where a box is inclusive r1,c1,r2,c2.
# The first three are the exact linked canonical dimension/size profiles.
_PROFILE_SPECS = {
    "canonical_11": (
        11,
        11,
        ((1, 1, 4, 4), (6, 4, 9, 8)),       # 4x4 + 4x5
    ),
    "canonical_12": (
        12,
        12,
        ((1, 1, 5, 5), (7, 7, 10, 10)),     # 5x5 + 4x4
    ),
    "canonical_13": (
        12,
        13,
        ((1, 1, 4, 4), (6, 7, 10, 11)),     # 4x4 + 5x5
    ),
    "broad_three": (
        15,
        18,
        ((1, 1, 4, 6), (1, 10, 5, 14), (8, 4, 13, 7)),  # 4x6, 5x5, 6x4
    ),
}

_CANONICAL_PROFILE_SIGNATURES = {
    (11, 11, ((4, 4), (4, 5))): "canonical_11",
    (12, 12, ((4, 4), (5, 5))): "canonical_12",
    (12, 13, ((4, 4), (5, 5))): "canonical_13",
}
_ALL_PROFILE_SIGNATURES = {
    **_CANONICAL_PROFILE_SIGNATURES,
    (15, 18, ((4, 6), (5, 5), (6, 4))): "broad_three",
}
_ANCHORS = ("top_left", "top_right", "bottom_right", "bottom_left")


def _components_of_color(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] == color
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            components.append(cells)
    return components


def _expected_border(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return (
        {(r1, c) for c in range(c1, c2 + 1)}
        | {(r2, c) for c in range(c1, c2 + 1)}
        | {(r, c1) for r in range(r1, r2 + 1)}
        | {(r, c2) for r in range(r1, r2 + 1)}
    )


def _boxes_overlap_with_moat(a, b) -> bool:
    ar1, ac1, ar2, ac2 = a
    br1, bc1, br2, bc2 = b
    return not (
        ar2 + 1 < br1
        or br2 + 1 < ar1
        or ac2 + 1 < bc1
        or bc2 + 1 < ac1
    )


def _analyze(grid: Any) -> tuple[list[str], dict[str, Any] | None]:
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list):
        return ["grid must be a nonempty list of rows"], None
    width = len(grid[0])
    if width == 0 or any(not isinstance(row, list) or len(row) != width for row in grid):
        return ["grid must be rectangular and nonempty"], None
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("grid contains a non-integer or color outside 0..9")

    h, w = len(grid), width
    components = _components_of_color(grid, 5)
    if not components:
        errors.append("no color-5 frame found")
        return errors, None

    frames: list[dict[str, Any]] = []
    covered: set[tuple[int, int]] = set()
    for index, cells in enumerate(components):
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        box = (min(rows), min(cols), max(rows), max(cols))
        r1, c1, r2, c2 = box
        fh, fw = r2 - r1 + 1, c2 - c1 + 1
        border = _expected_border(box)
        if fh < 4 or fw < 4:
            errors.append(f"frame {index} is too small: {fh}x{fw}")
        if set(cells) != border:
            errors.append(f"color-5 component {index} is not a complete rectangle outline")
        interior = [(r, c) for r in range(r1 + 1, r2) for c in range(c1 + 1, c2)]
        dots = [(r, c, grid[r][c]) for r, c in interior if grid[r][c] not in (0, 5)]
        interior_fives = [(r, c) for r, c in interior if grid[r][c] == 5]
        if interior_fives:
            errors.append(f"frame {index} interior contains color 5")
        if len(dots) != 1:
            errors.append(f"frame {index} has {len(dots)} inner dots, expected exactly 1")
            dot = None
        else:
            dot = dots[0]
            covered.add((dot[0], dot[1]))
        covered |= border
        frames.append({
            "box": box,
            "height": fh,
            "width": fw,
            "interior": interior,
            "dot": dot,
        })

    frames.sort(key=lambda frame: (frame["box"][0], frame["box"][1]))
    for left in range(len(frames)):
        for right in range(left + 1, len(frames)):
            if _boxes_overlap_with_moat(frames[left]["box"], frames[right]["box"]):
                errors.append(f"frames {left} and {right} overlap or violate the one-cell moat")

    stray = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0 and (r, c) not in covered
    ]
    if stray:
        errors.append(f"stray non-background cells outside frame grammar: {stray[:5]}")

    return errors, {"height": h, "width": w, "frames": frames}


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, ambiguous, nested, touching, or rule-hiding scenes."""
    del difficulty, meta
    errors, _analysis = _analyze(grid)
    return errors


def _profile_signature(analysis: dict[str, Any]) -> tuple[int, int, tuple[tuple[int, int], ...]]:
    sizes = tuple(sorted((frame["height"], frame["width"]) for frame in analysis["frames"]))
    return analysis["height"], analysis["width"], sizes


def strict_canonical_like(grid) -> list[str]:
    """Accept exactly the three linked canonical dimension/frame-size profiles."""
    errors, analysis = _analyze(grid)
    if errors or analysis is None:
        return errors
    signature = _profile_signature(analysis)
    if signature not in _CANONICAL_PROFILE_SIGNATURES:
        errors.append(
            "grid/frame-size profile is outside the three linked canonical train/test profiles"
        )
    return errors


def _dot_anchor(frame: dict[str, Any]) -> str:
    dot = frame["dot"]
    if dot is None:
        raise ValueError("frame has no unique dot")
    r1, c1, r2, c2 = frame["box"]
    row_side = "top" if dot[0] - (r1 + 1) <= (r2 - 1) - dot[0] else "bottom"
    col_side = "left" if dot[1] - (c1 + 1) <= (c2 - 1) - dot[1] else "right"
    return f"{row_side}_{col_side}"


def observe_overrides(grid) -> dict[str, str]:
    """Recover every declared exact axis from the returned input grid."""
    errors, analysis = _analyze(grid)
    if errors or analysis is None:
        raise ValueError("cannot observe overrides from invalid grid: " + "; ".join(errors))
    signature = _profile_signature(analysis)
    profile = _ALL_PROFILE_SIGNATURES.get(signature)
    if profile is None:
        raise ValueError(f"unknown generated profile signature: {signature!r}")
    colors = [frame["dot"][2] for frame in analysis["frames"]]
    if len(set(colors)) == 1:
        color_relation = "repeated"
    elif len(set(colors)) == len(colors):
        color_relation = "distinct"
    else:
        raise ValueError(f"mixed partial color repetition is outside the exact axis: {colors}")
    anchors = [_dot_anchor(frame) for frame in analysis["frames"]]
    dot_layout = "same_relative" if len(set(anchors)) == 1 else "different_relative"
    return {
        "profile": profile,
        "color_relation": color_relation,
        "dot_layout": dot_layout,
    }


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used only for tests and named rival discrimination."""
    errors, analysis = _analyze(grid)
    if errors or analysis is None:
        raise ValueError("outside rule domain: " + "; ".join(errors))
    out = [list(row) for row in grid]
    for frame in analysis["frames"]:
        color = frame["dot"][2]
        for r, c in frame["interior"]:
            out[r][c] = color
    return out


def _transform_box(box, h: int, w: int, flip_v: bool, flip_h: bool):
    r1, c1, r2, c2 = box
    if flip_v:
        r1, r2 = h - 1 - r2, h - 1 - r1
    if flip_h:
        c1, c2 = w - 1 - c2, w - 1 - c1
    return r1, c1, r2, c2


def _anchor_cell(box, anchor: str) -> tuple[int, int]:
    r1, c1, r2, c2 = box
    rows = {"top": r1 + 1, "bottom": r2 - 1}
    cols = {"left": c1 + 1, "right": c2 - 1}
    row_side, col_side = anchor.split("_")
    return rows[row_side], cols[col_side]


def schedule_profile(seed, sample_index, difficulty=None) -> str:
    """Expose the four-consecutive-draw curriculum schedule to the semantic gate."""
    del seed, difficulty
    return PROFILES[sample_index % len(PROFILES)]


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {unknown}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_profile = schedule_profile(seed, sample_index, difficulty)
    profile_choices = PROFILES if overrides.get("profile") is not None else (scheduled_profile,)
    profile = ctx.draw_choice("profile", profile_choices)

    scheduled_relation = COLOR_RELATIONS[(sample_index // 2) % 2]
    relation_choices = COLOR_RELATIONS if overrides.get("color_relation") is not None else (scheduled_relation,)
    color_relation = ctx.draw_choice("color_relation", relation_choices)

    scheduled_layout = DOT_LAYOUTS[sample_index % 2]
    layout_choices = DOT_LAYOUTS if overrides.get("dot_layout") is not None else (scheduled_layout,)
    dot_layout = ctx.draw_choice("dot_layout", layout_choices)

    h, w, base_boxes = _PROFILE_SPECS[profile]
    layout_rng = ctx.draw_rng(f"layout_{difficulty or 'medium'}")
    flip_v = bool(layout_rng.randrange(2))
    flip_h = bool(layout_rng.randrange(2))
    boxes = [_transform_box(box, h, w, flip_v, flip_h) for box in base_boxes]

    palette_rng = ctx.draw_rng(f"palette_{difficulty or 'medium'}")
    palette = list(range(1, 10))
    palette.remove(5)
    palette_rng.shuffle(palette)
    if color_relation == "repeated":
        colors = [palette[0]] * len(boxes)
    else:
        colors = palette[:len(boxes)]

    anchor_rng = ctx.draw_rng(f"anchors_{difficulty or 'medium'}")
    start = anchor_rng.randrange(len(_ANCHORS))
    if dot_layout == "same_relative":
        anchors = [_ANCHORS[start]] * len(boxes)
    else:
        anchors = [_ANCHORS[(start + index) % len(_ANCHORS)] for index in range(len(boxes))]

    grid = full_grid(h, w, 0)
    for box, color, anchor in zip(boxes, colors, anchors):
        for r, c in _expected_border(box):
            grid[r][c] = 5
        dot_r, dot_c = _anchor_cell(box, anchor)
        grid[dot_r][dot_c] = color

    errors = self_check(grid)
    if errors:
        raise RuntimeError("generator constructed invalid scene: " + "; ".join(errors))
    observed = observe_overrides(grid)
    expected = {
        "profile": profile,
        "color_relation": color_relation,
        "dot_layout": dot_layout,
    }
    if observed != expected:
        raise RuntimeError(f"observable axis mismatch: expected {expected}, observed {observed}")
    return grid


def _analysis_if_valid(grid):
    errors, analysis = _analyze(grid)
    return None if errors else analysis


def _witness_profile(profile_name: str):
    def witness(grid):
        analysis = _analysis_if_valid(grid)
        return (
            analysis is not None
            and _ALL_PROFILE_SIGNATURES.get(_profile_signature(analysis)) == profile_name
        )
    return witness


def _witness_repeated_colors(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    colors = [frame["dot"][2] for frame in analysis["frames"]]
    return len(colors) >= 2 and len(set(colors)) == 1


def _witness_distinct_colors(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return False
    colors = [frame["dot"][2] for frame in analysis["frames"]]
    return len(colors) >= 2 and len(set(colors)) == len(colors)


def _witness_rectangular_frame(grid):
    analysis = _analysis_if_valid(grid)
    return analysis is not None and any(
        frame["height"] != frame["width"] for frame in analysis["frames"]
    )


def _witness_nonidentity(grid):
    try:
        return rule_mirror(grid) != grid
    except ValueError:
        return False


SEMANTIC_WITNESSES = {
    "canonical_11_profile": _witness_profile("canonical_11"),
    "canonical_12_profile": _witness_profile("canonical_12"),
    "canonical_13_profile": _witness_profile("canonical_13"),
    "three_frames_refute_fixed_two": _witness_profile("broad_three"),
    "repeated_dot_color_is_lawful": _witness_repeated_colors,
    "distinct_dot_colors_need_local_transfer": _witness_distinct_colors,
    "rectangular_frames_are_lawful": _witness_rectangular_frame,
    "interior_fill_changes_more_than_marker": _witness_nonidentity,
}


def _copy(grid):
    return [list(row) for row in grid]


def _fill_selected(grid, predicate, color_fn=None):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return _copy(grid)
    out = _copy(grid)
    for index, frame in enumerate(analysis["frames"]):
        if not predicate(index, frame, analysis):
            continue
        color = frame["dot"][2] if color_fn is None else color_fn(index, frame, analysis)
        for r, c in frame["interior"]:
            out[r][c] = color
    return out


def _rival_no_op(grid):
    return _copy(grid)


def _rival_only_first_frame(grid):
    return _fill_selected(grid, lambda index, frame, analysis: index == 0)


def _rival_only_first_two_frames(grid):
    return _fill_selected(grid, lambda index, frame, analysis: index < 2)


def _rival_first_dot_color_everywhere(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return _copy(grid)
    first_color = analysis["frames"][0]["dot"][2]
    return _fill_selected(
        grid,
        lambda index, frame, analysis: True,
        lambda index, frame, analysis: first_color,
    )


def _rival_reject_repeated_colors(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return _copy(grid)
    colors = [frame["dot"][2] for frame in analysis["frames"]]
    return _copy(grid) if len(set(colors)) != len(colors) else rule_mirror(grid)


def _rival_only_canonical_frame_sizes(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None:
        return _copy(grid)
    allowed = {(4, 4), (4, 5), (5, 5)}
    return _fill_selected(
        grid,
        lambda index, frame, analysis: (frame["height"], frame["width"]) in allowed,
    )


def _rival_only_square_frames(grid):
    return _fill_selected(
        grid,
        lambda index, frame, analysis: frame["height"] == frame["width"],
    )


def _rival_only_11x11_profile(grid):
    analysis = _analysis_if_valid(grid)
    if analysis is None or (analysis["height"], analysis["width"]) != (11, 11):
        return _copy(grid)
    return rule_mirror(grid)


SEMANTIC_RIVALS = {
    "no_op_marker_only": _rival_no_op,
    "only_first_frame": _rival_only_first_frame,
    "only_first_two_frames": _rival_only_first_two_frames,
    "first_dot_color_everywhere": _rival_first_dot_color_everywhere,
    "reject_repeated_colors": _rival_reject_repeated_colors,
    "only_canonical_frame_sizes": _rival_only_canonical_frame_sizes,
    "only_square_frames": _rival_only_square_frames,
    "only_11x11_profile": _rival_only_11x11_profile,
}

WITNESS_RIVALS = {
    "canonical_11_profile": "only_square_frames",
    "canonical_12_profile": "only_11x11_profile",
    "canonical_13_profile": "only_11x11_profile",
    "three_frames_refute_fixed_two": [
        "only_first_two_frames",
        "only_canonical_frame_sizes",
    ],
    "repeated_dot_color_is_lawful": "reject_repeated_colors",
    "distinct_dot_colors_need_local_transfer": "first_dot_color_everywhere",
    "rectangular_frames_are_lawful": "only_square_frames",
    "interior_fill_changes_more_than_marker": ["no_op_marker_only", "only_first_frame"],
}

# These rivals fit all official pairs, so generated counterexamples are required.
CANONICAL_SHORTCUTS = {
    "only_first_two_frames": _rival_only_first_two_frames,
    "reject_repeated_colors": _rival_reject_repeated_colors,
    "only_canonical_frame_sizes": _rival_only_canonical_frame_sizes,
}

LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject a lesson whenever a named plausible rival survives its demos."""
    reasons: list[str] = []
    for index, demo in enumerate(demos):
        try:
            expected = rule_mirror(demo["input"])
        except ValueError as exc:
            reasons.append(f"demo {index} outside rule domain: {exc}")
            continue
        if expected != demo["output"]:
            reasons.append(f"demo {index} output disagrees with frame-fill rule")
    try:
        query_answer = rule_mirror(query["input"])
    except ValueError as exc:
        reasons.append(f"query outside rule domain: {exc}")
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(demo["input"]) == demo["output"] for demo in demos)
        if survives and competitor(query["input"]) != query_answer:
            reasons.append(
                f"competing rule {name!r} fits every demo but answers query differently"
            )
    return reasons
