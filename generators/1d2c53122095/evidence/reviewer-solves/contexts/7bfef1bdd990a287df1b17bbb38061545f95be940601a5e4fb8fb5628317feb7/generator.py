"""Generate count-selected bands inside nested rectangular frames.

The literal ARC rule is:

* count the red (2) cells in the top row to obtain one-based depth ``k``;
* rank the yellow (4) rectangular frames from outside to inside;
* fill background cells inside frame ``k`` but outside the next inner frame
  with cyan (8); when ``k`` selects the innermost frame, fill its center.

The selected Racket program remains the sole output authority.  This module
only emits inputs and provides an independent Python mirror for adversarial
checks.  Six unique linked profiles per difficulty form a deterministic
curriculum.  Every four-consecutive-demo window contains outer, intermediate,
and innermost selection, while the following query has a profile not present
in those demonstrations.  Thus fixed-depth, shape-only, and exact-profile-copy
shortcuts cannot survive a production lesson.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "1d2c53122095"
TASK_ID = GENERATOR_ID
VERSION = "3.1.0"
RULE_HASH = "4e070bae635e"

SUMMARY = (
    "A zero-background grid contains two to five strictly nested yellow (4) "
    "rectangular frames and k red (2) markers in the top row. Count the red "
    "markers, select the k-th frame from outside to inside, and fill cyan (8) "
    "background inside that frame down to the next inner frame. If k selects "
    "the innermost frame, fill its central interior. Linked profiles vary "
    "canvas size, frame count, frame gap, aspect ratio, placement, and depth."
)

INVARIANTS = [
    "all input cells are 0, 2, or 4; red markers occur only in row 0",
    "two to five complete color-4 rectangular frames are strictly nested",
    "k = top-row red-marker count and 1 <= k <= frame count",
    "for k below the innermost depth, fill only the band before frame k+1",
    "for k equal to frame count, fill the selected frame's central interior",
]

# A profile is an exact observable linked grammar point:
# (band, name, grid_h, grid_w, n_frames, gap, k, inner_h, inner_w).
# Every six-profile band is ordered O, M, I, O, I, M.  Therefore every cyclic
# four-demo window contains outer, intermediate, and innermost selection, and
# its offset-four query is one of the two profiles not shown in those demos.
# A few exact profiles are deliberately shared across adjacent difficulty bands;
# difficulty changes the curriculum mix, not the legality of a scene.
_PROFILE_ROWS = (
    ("easy", "easy_outer_13_nf2", 13, 13, 2, 2, 1, 5, 5),
    ("easy", "easy_middle_17_nf3", 17, 17, 3, 2, 2, 5, 5),
    ("easy", "easy_inner_13_nf2", 13, 13, 2, 2, 2, 5, 5),
    ("easy", "easy_outer_17_nf3", 17, 17, 3, 2, 1, 5, 5),
    ("easy", "easy_inner_17_nf3", 17, 17, 3, 2, 3, 5, 5),
    ("easy", "easy_middle_15x17_nf3", 15, 17, 3, 2, 2, 3, 5),
    ("medium", "medium_outer_21_nf4", 21, 21, 4, 2, 1, 5, 5),
    ("medium", "medium_middle2_21_nf4", 21, 21, 4, 2, 2, 5, 5),
    ("medium", "medium_inner_19x23_nf4", 19, 23, 4, 2, 4, 3, 7),
    # Preserve the canonical-named exact override while using it to break the
    # 21x21-shape/depth correlation in the ordinary medium curriculum.
    ("medium", "canonical_inner_21_nf4", 21, 21, 4, 2, 4, 5, 5),
    ("medium", "medium_middle3_19x23_nf4", 19, 23, 4, 2, 3, 3, 7),
    ("hard", "hard_outer_23x25_nf5", 23, 25, 5, 2, 1, 3, 5),
    ("hard", "hard_middle_23x25_nf5", 23, 25, 5, 2, 3, 3, 5),
    ("hard", "hard_inner_23x25_nf5", 23, 25, 5, 2, 5, 3, 5),
    ("hard", "hard_gap3_middle_21_nf3", 21, 21, 3, 3, 2, 3, 5),
    # Canonical-only override anchor keeps the remaining published input inside
    # the strict hook without forcing the ordinary curriculum to one shape.
    ("canonical", "canonical_middle3_21_nf4", 21, 21, 4, 2, 3, 5, 5),
)
_PROFILE_BY_NAME = {
    name: (band, height, width, n_frames, gap, k, inner_h, inner_w)
    for band, name, height, width, n_frames, gap, k, inner_h, inner_w in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    "easy": (
        "easy_outer_13_nf2",
        "easy_middle_17_nf3",
        "easy_inner_13_nf2",
        "easy_outer_17_nf3",
        "easy_inner_17_nf3",
        "easy_middle_15x17_nf3",
    ),
    "medium": (
        "medium_outer_21_nf4",
        "medium_middle2_21_nf4",
        "medium_inner_19x23_nf4",
        "easy_outer_17_nf3",
        "canonical_inner_21_nf4",
        "medium_middle3_19x23_nf4",
    ),
    "hard": (
        "hard_outer_23x25_nf5",
        "hard_middle_23x25_nf5",
        "hard_inner_23x25_nf5",
        "medium_outer_21_nf4",
        "canonical_inner_21_nf4",
        "hard_gap3_middle_21_nf3",
    ),
}
SCENE_PROFILES = tuple(name for _band_name, name, *_rest in _PROFILE_ROWS)
SCHEDULE_PROFILES = tuple(
    name for band in ("easy", "medium", "hard") for name in _PROFILES_BY_BAND[band]
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic six-profile curriculum for the difficulty band",
        "valid": (
            "easy_outer_13_nf2|easy_middle_17_nf3|easy_inner_13_nf2|"
            "easy_outer_17_nf3|easy_inner_17_nf3|easy_middle_15x17_nf3|"
            "medium_outer_21_nf4|medium_middle2_21_nf4|"
            "medium_inner_19x23_nf4|canonical_inner_21_nf4|"
            "medium_middle3_19x23_nf4|"
            "hard_outer_23x25_nf5|hard_middle_23x25_nf5|"
            "hard_inner_23x25_nf5|hard_gap3_middle_21_nf3|"
            "canonical_middle3_21_nf4"
        ),
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 4

Grid = list[list[int]]
Box = tuple[int, int, int, int]


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the exact profile at one deterministic curriculum position."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")


def _frame_outline(grid: Grid, box: Box, color: int = 4) -> None:
    top, left, bottom, right = box
    for col in range(left, right + 1):
        grid[top][col] = color
        grid[bottom][col] = color
    for row in range(top, bottom + 1):
        grid[row][left] = color
        grid[row][right] = color


def _outer_size(n_frames: int, gap: int, inner_h: int, inner_w: int) -> tuple[int, int]:
    growth = 2 * gap * (n_frames - 1)
    return inner_h + growth, inner_w + growth


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Return one deterministic input; the canonical Racket rule owns output."""
    _validate_call(difficulty, overrides)
    band = _band(difficulty)
    scheduled = overrides.get("scene_profile") or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile = ctx.draw_choice("scene_profile", (scheduled,))
    (
        _profile_band,
        height,
        width,
        n_frames,
        gap,
        k,
        inner_h,
        inner_w,
    ) = _PROFILE_BY_NAME[profile]

    outer_h, outer_w = _outer_size(n_frames, gap, inner_h, inner_w)
    layout_rng = ctx.draw_rng("layout")
    marker_rng = ctx.draw_rng("markers")
    top = layout_rng.randint(2, height - outer_h - 1)
    left = layout_rng.randint(0, width - outer_w - 1)

    grid = full_grid(height, width, 0)
    for depth in range(n_frames):
        inset = depth * gap
        box = (
            top + inset,
            left + inset,
            top + outer_h - 1 - inset,
            left + outer_w - 1 - inset,
        )
        _frame_outline(grid, box)

    # Marker positions are deliberately independent of frame placement.  The
    # rule depends on their count, not their location or proximity to a frame.
    for col in marker_rng.sample(range(width), k):
        grid[0][col] = 2

    observed = observe_overrides(grid)
    if observed.get("scene_profile") != profile:
        raise AssertionError(
            f"constructed profile {profile!r} observed as {observed.get('scene_profile')!r}"
        )
    return grid


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 1 <= len(grid) <= 30 or not 1 <= width <= 30:
        return [f"ARC grid dimensions must be in 1..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _components(grid: Grid, color: int) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    remaining = {
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (row + drow, col + dcol)
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    component.add(neighbor)
                    queue.append(neighbor)
        components.append(component)
    return components


def _bbox(cells: set[tuple[int, int]]) -> Box:
    rows = [row for row, _col in cells]
    cols = [col for _row, col in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _outline_cells(box: Box) -> set[tuple[int, int]]:
    top, left, bottom, right = box
    return {
        *((top, col) for col in range(left, right + 1)),
        *((bottom, col) for col in range(left, right + 1)),
        *((row, left) for row in range(top, bottom + 1)),
        *((row, right) for row in range(top, bottom + 1)),
    }


def _analysis(grid: Any, *, teaching: bool = False) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors, "frames": [], "scene_profile": None}

    normalized = [list(row) for row in grid]
    height, width = len(normalized), len(normalized[0])
    palette = {value for row in normalized for value in row}
    if not palette <= {0, 2, 4}:
        errors.append(f"input palette must be a subset of {{0,2,4}}, found {sorted(palette)}")

    markers = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if normalized[row][col] == 2
    ]
    if not markers:
        errors.append("expected at least one red marker in the top row")
    if any(row != 0 for row, _col in markers):
        errors.append("red marker cells may occur only in row 0")

    frames: list[Box] = []
    for component in _components(normalized, 4):
        box = _bbox(component)
        if component != _outline_cells(box):
            errors.append(f"color-4 component is not one complete rectangular outline: bbox={box}")
            continue
        top, left, bottom, right = box
        if bottom - top < 2 or right - left < 2:
            errors.append(f"frame must enclose at least one cell: bbox={box}")
            continue
        frames.append(box)

    frames.sort(
        key=lambda box: (box[2] - box[0] + 1) * (box[3] - box[1] + 1),
        reverse=True,
    )
    if not 2 <= len(frames) <= 5:
        errors.append(f"expected two to five nested frames, found {len(frames)}")

    insets: list[tuple[int, int, int, int]] = []
    for outer, inner in zip(frames, frames[1:]):
        top_gap = inner[0] - outer[0]
        left_gap = inner[1] - outer[1]
        bottom_gap = outer[2] - inner[2]
        right_gap = outer[3] - inner[3]
        inset = (top_gap, left_gap, bottom_gap, right_gap)
        insets.append(inset)
        if min(inset) < 2:
            errors.append(
                "frames must be strictly nested with at least one background "
                f"cell between outlines, found inset={inset}"
            )

    k = len(markers)
    if frames and not 1 <= k <= len(frames):
        errors.append(f"red-marker count k={k} must be in 1..{len(frames)}")

    gap: int | None = None
    if insets and all(len(set(inset)) == 1 for inset in insets):
        candidate_gaps = {inset[0] for inset in insets}
        if len(candidate_gaps) == 1:
            gap = next(iter(candidate_gaps))

    scene_profile: str | None = None
    if not errors and gap is not None:
        outer = frames[0]
        inner = frames[-1]
        signature = (
            height,
            width,
            len(frames),
            gap,
            k,
            outer[2] - outer[0] + 1,
            outer[3] - outer[1] + 1,
            inner[2] - inner[0] + 1,
            inner[3] - inner[1] + 1,
        )
        for name, (
            _profile_band,
            p_height,
            p_width,
            p_frames,
            p_gap,
            p_k,
            p_inner_h,
            p_inner_w,
        ) in _PROFILE_BY_NAME.items():
            p_outer_h, p_outer_w = _outer_size(p_frames, p_gap, p_inner_h, p_inner_w)
            if signature == (
                p_height,
                p_width,
                p_frames,
                p_gap,
                p_k,
                p_outer_h,
                p_outer_w,
                p_inner_h,
                p_inner_w,
            ):
                scene_profile = name
                break

    if teaching and not errors and scene_profile is None:
        errors.append("teaching scene must realize one declared linked scene_profile")

    return {
        "errors": errors,
        "height": height,
        "width": width,
        "markers": markers,
        "k": k,
        "frames": frames,
        "insets": insets,
        "gap": gap,
        "scene_profile": scene_profile,
    }


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the intended nested-frame input grammar and exact overrides."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def teaching_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the narrower generated curriculum and linked profile."""
    del difficulty
    analysis = _analysis(grid, teaching=True)
    errors = list(analysis["errors"])
    if errors:
        return errors
    observed = {"scene_profile": analysis["scene_profile"]}
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(f"override {name}={requested!r} realized as {observed.get(name)!r}")
    return errors


def observe_overrides(grid) -> dict[str, str | None]:
    """Recover the complete exact declared profile from the returned grid."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def canonical_profile_index(grid) -> int | None:
    """Index the five published depth/shape profiles when one is present."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    signature = (
        analysis["height"],
        analysis["width"],
        len(analysis["frames"]),
        analysis["k"],
    )
    signatures = (
        (13, 13, 2, 1),
        (17, 17, 3, 2),
        (21, 21, 4, 3),
        (21, 21, 4, 4),
        (21, 21, 4, 2),
    )
    try:
        return signatures.index(signature)
    except ValueError:
        return None


def _fill_for_depth(grid: Grid, depth: int, *, preserve_inner: bool = True) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid nested-frame input: " + "; ".join(analysis["errors"]))
    frames: list[Box] = analysis["frames"]
    selected_depth = max(1, min(int(depth), len(frames)))
    target = frames[selected_depth - 1]
    inner = frames[selected_depth] if selected_depth < len(frames) else None
    output = [list(row) for row in grid]
    for row in range(target[0] + 1, target[2]):
        for col in range(target[1] + 1, target[3]):
            if output[row][col] != 0:
                continue
            if preserve_inner and inner is not None:
                if inner[0] < row < inner[2] and inner[1] < col < inner[3]:
                    continue
            output[row][col] = 8
    return output


def rule_mirror(grid: Grid) -> Grid:
    """Independent Python mirror for tests; Racket remains output authority."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid nested-frame input: " + "; ".join(analysis["errors"]))
    return _fill_for_depth(grid, analysis["k"])


def _rival_identity(grid: Grid) -> Grid:
    return [list(row) for row in grid]


def _rival_always_outer(grid: Grid) -> Grid:
    return _fill_for_depth(grid, 1)


def _rival_always_innermost(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    return _fill_for_depth(grid, len(analysis["frames"]))


def _rival_reverse_depth(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    return _fill_for_depth(grid, len(analysis["frames"]) - analysis["k"] + 1)


def _rival_fill_full_target(grid: Grid) -> Grid:
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    return _fill_for_depth(grid, analysis["k"], preserve_inner=False)


def _rival_shape_only_depth(grid: Grid) -> Grid:
    """Plausible canonical-correlation shortcut: infer depth from canvas size."""
    analysis = _analysis(grid)
    if analysis["errors"]:
        raise ValueError("invalid input")
    guessed = {13: 1, 17: 2, 21: 3}.get(analysis["height"], 1)
    return _fill_for_depth(grid, guessed)


def strict_canonical_like(grid) -> list[str]:
    """The complete generated profile set is the strict task-linked manifold."""
    return teaching_check(grid)


def _valid_analysis(grid: Grid) -> dict[str, Any] | None:
    analysis = _analysis(grid, teaching=True)
    return None if analysis["errors"] else analysis


def _outer_selection(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["k"] == 1


def _intermediate_selection(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and 1 < analysis["k"] < len(analysis["frames"])


def _innermost_selection(grid: Grid) -> bool:
    analysis = _valid_analysis(grid)
    return analysis is not None and analysis["k"] == len(analysis["frames"])


SEMANTIC_WITNESSES: dict[str, Callable[[Grid], bool]] = {
    "outer_selection": _outer_selection,
    "intermediate_selection": _intermediate_selection,
    "innermost_selection": _innermost_selection,
}

SEMANTIC_RIVALS = {
    "identity": _rival_identity,
    "always_outer": _rival_always_outer,
    "always_innermost": _rival_always_innermost,
    "reverse_depth": _rival_reverse_depth,
    "fill_full_target": _rival_fill_full_target,
    "shape_only_depth": _rival_shape_only_depth,
}
WITNESS_RIVALS = {
    "outer_selection": ["identity", "always_innermost", "reverse_depth", "fill_full_target"],
    "intermediate_selection": [
        "identity",
        "always_outer",
        "always_innermost",
        "reverse_depth",
        "fill_full_target",
        "shape_only_depth",
    ],
    "innermost_selection": ["identity", "always_outer", "reverse_depth", "shape_only_depth"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Reject named semantic rivals and the contextual profile-copy shortcut."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"at least {EXAMPLES_NEEDED} demonstrations are required"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query must contain an input grid"]

    reasons: list[str] = []
    query_errors = teaching_check(query["input"])
    query_profile: str | None = None
    if query_errors:
        reasons.append("query input is outside the teaching grammar")
    else:
        query_profile = observe_overrides(query["input"]).get("scene_profile")

    valid_demos: list[dict[str, Any]] = []
    demo_profiles: list[str] = []
    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} must contain input and output grids")
            continue
        errors = teaching_check(demo["input"])
        if errors:
            reasons.append(f"demo {index} input is outside the teaching grammar")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output is not the selected count-indexed band")
            continue
        valid_demos.append(demo)
        profile = observe_overrides(demo["input"]).get("scene_profile")
        if profile is not None:
            demo_profiles.append(profile)

    if query_profile is not None and query_profile in demo_profiles:
        reasons.append(
            "query scene_profile repeats a demonstration, permitting a profile-copy shortcut"
        )

    for name, rival in LESSON_COMPETITORS.items():
        if valid_demos and all(rival(demo["input"]) == demo["output"] for demo in valid_demos):
            reasons.append(f"demonstrations do not refute rival {name!r}")
    return reasons
