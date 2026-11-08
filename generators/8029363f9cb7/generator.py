"""Semantic generator for task ``8029363f9cb7``.

A red source launches a beam to the right, even when it is nearer the right
frame.  Slash mirrors (3) and backslash mirrors (4) reflect the beam, every
traversed zero becomes cyan in the output,
and the first wall (5), whether interior or on the frame, stops the beam.
Off-path mirrors and walls are deliberate distractors: only objects encountered
by the traced beam affect the answer.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "8029363f9cb7"
TASK_ID = GENERATOR_ID
VERSION = "5.0.0"
RULE_HASH = "a08bfbc3cb49"

SUMMARY = (
    "Launch a beam rightward from the single red(2) source, including when "
    "the source is nearer the right frame. Paint only empty "
    "cells traversed by that beam cyan(8), reflect on slash(3) and "
    "backslash(4) mirrors, and stop at the first gray(5) wall. Mirrors and "
    "walls outside the traced route are distractors and remain unchanged."
)

INVARIANTS = [
    "a full gray(5) outer frame surrounds a zero background",
    "one interior red(2) source launches the beam to the right from either side",
    "at least one slash(3) or backslash(4) mirror lies on the traced route",
    "the route terminates at either an interior wall or the outer frame",
    "off-path mirrors and walls may be present and must not affect the answer",
]


@dataclass(frozen=True)
class _Profile:
    band: str
    height: int
    width: int
    hit_colors: tuple[int, ...]
    stop_kind: str
    distractor_color: int | None
    source_side: str


# Every four consecutive samples in a band contain:
#   * a slash and a backslash witness,
#   * an interior-wall stop and an outer-frame stop,
#   * an off-path mirror distractor,
#   * a route with multiple reflections,
#   * a source near each vertical side while still launching right.
# Five rows reproduce the complete linked canonical signatures; the remaining
# rows vary only rule-lawful route geometry while preserving canonical shape and
# palette profiles.
_PROFILE_ROWS: tuple[tuple[str, _Profile], ...] = (
    (
        "easy_inner_slash_clean",
        _Profile("easy", 8, 11, (3,), "interior", None, "left"),
    ),
    (
        "easy_outer_backslash_clean",
        _Profile("easy", 9, 12, (4, 4), "border", None, "right"),
    ),
    (
        "easy_outer_mixed_distractor",
        _Profile("easy", 8, 12, (4, 3), "border", 4, "right"),
    ),
    (
        "easy_inner_mixed_distractor",
        _Profile("easy", 9, 13, (3, 4), "interior", 3, "left"),
    ),
    (
        "medium_inner_mixed_clean",
        _Profile("medium", 8, 12, (4, 3), "interior", None, "left"),
    ),
    (
        "medium_outer_three_turn_distractor",
        _Profile("medium", 9, 13, (4, 3, 4), "border", 3, "right"),
    ),
    (
        "medium_inner_three_turn_distractor",
        _Profile("medium", 10, 14, (4, 3, 4), "interior", 4, "right"),
    ),
    (
        "medium_outer_double_slash_clean",
        _Profile("medium", 8, 11, (3, 3), "border", None, "left"),
    ),
    (
        "hard_outer_mixed_distractor",
        _Profile("hard", 10, 14, (4, 3), "border", 4, "left"),
    ),
    (
        "hard_inner_three_turn_clean",
        _Profile("hard", 9, 13, (3, 4, 3), "interior", None, "right"),
    ),
    (
        "hard_outer_double_backslash_distractor",
        _Profile("hard", 8, 12, (4, 4), "border", 3, "right"),
    ),
    (
        "hard_inner_double_slash_clean",
        _Profile("hard", 9, 12, (3, 3), "interior", None, "left"),
    ),
)

SCENE_PROFILES = tuple(name for name, _profile in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = dict(_PROFILE_ROWS)
_PROFILES_BY_BAND = {
    band: tuple(name for name, profile in _PROFILE_ROWS if profile.band == band)
    for band in ("easy", "medium", "hard")
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four-slot, difficulty-specific semantic curriculum",
        "valid": (
            "easy_inner_slash_clean|easy_outer_backslash_clean|"
            "easy_outer_mixed_distractor|easy_inner_mixed_distractor|"
            "medium_inner_mixed_clean|medium_outer_three_turn_distractor|"
            "medium_inner_three_turn_distractor|medium_outer_double_slash_clean|"
            "hard_outer_mixed_distractor|hard_inner_three_turn_clean|"
            "hard_outer_double_backslash_distractor|"
            "hard_inner_double_slash_clean"
        ),
    }
}

HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()
EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 0.20

# Strict empirical-manifold signatures extracted jointly from all five
# canonical inputs.  Segment lengths and source row are lawful nuisance
# variables; shape, palette size, hit-mirror sequence, stop class, and number
# of off-path mirrors are retained together.
_CANONICAL_LINKED_SIGNATURES = {
    (8, 12, 5, (4, 3), "interior", 0),
    (9, 13, 5, (4, 3, 4), "border", 1),
    (10, 14, 5, (4, 3), "border", 1),
    (8, 11, 4, (3,), "interior", 0),
    (9, 12, 4, (4, 4), "border", 0),
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the four-slot curriculum profile for this sample index."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _rectangular_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(
        not isinstance(row, (list, tuple)) or len(row) != width
        for row in grid
    ):
        return ["grid must be rectangular"]
    if not 3 <= len(grid) <= 30 or not 3 <= width <= 30:
        return [f"grid dimensions must be in 3..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or not 0 <= value <= 9
            ):
                return ["cells must be literal ARC integers 0..9"]
    return []


def _reflect(color: int, dr: int, dc: int) -> tuple[int, int]:
    if color == 3:
        return -dc, -dr
    if color == 4:
        return dc, dr
    raise ValueError(f"not a mirror color: {color}")


def _source_side(width: int, source_col: int) -> str:
    """Classify which vertical frame is nearer to the source."""
    left_distance = source_col
    right_distance = width - 1 - source_col
    if left_distance < right_distance:
        return "left"
    if right_distance < left_distance:
        return "right"
    return "center"


def _simulate(
    grid: Sequence[Sequence[int]],
    *,
    mirror_mode: str = "official",
    launch_mode: str = "right",
    ignore_interior_walls: bool = False,
    stop_after_mirrors: int | None = None,
) -> list[list[int]]:
    """Trace one source-launched beam without mutating the input."""
    output = [list(row) for row in grid]
    height, width = len(output), len(output[0])
    sources = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if output[row][col] == 2
    ]
    if len(sources) != 1:
        raise ValueError(f"expected exactly one source, found {len(sources)}")
    source_row, source_col = sources[0]
    if launch_mode == "right":
        dc = 1
    elif launch_mode == "away_from_nearest_vertical_frame":
        left_distance = source_col
        right_distance = width - 1 - source_col
        dc = 1 if left_distance <= right_distance else -1
    else:
        raise ValueError(f"unknown launch mode: {launch_mode!r}")
    row, col = source_row, source_col + dc
    dr = 0
    seen: set[tuple[int, int, int, int]] = set()
    mirror_hits = 0
    for _fuel in range(max(500, height * width * 8)):
        state = (row, col, dr, dc)
        if state in seen or not (0 <= row < height and 0 <= col < width):
            break
        seen.add(state)
        value = grid[row][col]
        if value == 5:
            border = row in (0, height - 1) or col in (0, width - 1)
            if not (ignore_interior_walls and not border):
                break
            row += dr
            col += dc
            continue
        if value == 0:
            output[row][col] = 8
        if value in (3, 4):
            mirror_hits += 1
            if stop_after_mirrors is not None and mirror_hits >= stop_after_mirrors:
                break
            effective = value
            if mirror_mode == "all_slash":
                effective = 3
            elif mirror_mode == "all_backslash":
                effective = 4
            dr, dc = _reflect(effective, dr, dc)
        row += dr
        col += dc
    return output


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Independent Python mirror; synchronized Racket remains output authority."""
    errors = _rectangular_errors(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _simulate(grid)


def _analysis(grid: Any) -> dict[str, Any]:
    errors = _rectangular_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    extras = sorted(
        {value for row in grid for value in row if value not in (0, 2, 3, 4, 5)}
    )
    if extras:
        errors.append(f"unexpected input colors: {extras}")
    if any(grid[0][col] != 5 or grid[-1][col] != 5 for col in range(width)):
        errors.append("top and bottom borders must be solid gray(5)")
    if any(grid[row][0] != 5 or grid[row][-1] != 5 for row in range(height)):
        errors.append("left and right borders must be solid gray(5)")

    sources = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 2
    ]
    if len(sources) != 1:
        errors.append(f"expected exactly one red(2) source, found {len(sources)}")
        return {
            "errors": errors,
            "height": height,
            "width": width,
            "sources": sources,
        }
    source = sources[0]
    if source[0] in (0, height - 1) or source[1] in (0, width - 1):
        errors.append("the source must be inside the frame")

    row, col = source[0], source[1] + 1
    dr, dc = 0, 1
    seen: set[tuple[int, int, int, int]] = set()
    traversed: list[tuple[int, int, int]] = []
    painted: list[tuple[int, int]] = []
    hit_mirrors: list[tuple[int, int, int]] = []
    stop_kind = "none"
    stop_cell: tuple[int, int] | None = None
    trace_error: str | None = None
    for _fuel in range(max(500, height * width * 8)):
        state = (row, col, dr, dc)
        if state in seen:
            stop_kind = "loop"
            trace_error = "beam entered a repeated position/direction state"
            break
        if not (0 <= row < height and 0 <= col < width):
            stop_kind = "out_of_bounds"
            trace_error = "beam left the grid without meeting a wall"
            break
        seen.add(state)
        value = grid[row][col]
        if value == 5:
            stop_cell = (row, col)
            stop_kind = (
                "border"
                if row in (0, height - 1) or col in (0, width - 1)
                else "interior"
            )
            break
        traversed.append((row, col, value))
        if value == 0:
            painted.append((row, col))
        elif value in (3, 4):
            hit_mirrors.append((row, col, value))
            dr, dc = _reflect(value, dr, dc)
        elif value != 2:
            trace_error = f"beam encountered unsupported color {value}"
            stop_kind = "invalid"
            break
        row += dr
        col += dc
    else:
        stop_kind = "fuel"
        trace_error = "beam trace exceeded its safety limit"

    if trace_error:
        errors.append(trace_error)
    all_mirrors = [
        (row, col, grid[row][col])
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] in (3, 4)
    ]
    hit_positions = {(row, col) for row, col, _value in hit_mirrors}
    off_path_mirrors = [
        mirror for mirror in all_mirrors if mirror[:2] not in hit_positions
    ]
    interior_walls = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
        if grid[row][col] == 5
    ]
    palette = {value for row_values in grid for value in row_values}
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "source": source,
        "source_side": _source_side(width, source[1]),
        "traversed": traversed,
        "painted": painted,
        "hit_mirrors": hit_mirrors,
        "hit_colors": tuple(value for _row, _col, value in hit_mirrors),
        "all_mirrors": all_mirrors,
        "off_path_mirrors": off_path_mirrors,
        "interior_walls": interior_walls,
        "stop_kind": stop_kind,
        "stop_cell": stop_cell,
        "palette": palette,
        "palette_size": len(palette),
    }


def _profile_signature(grid: Any) -> tuple[Any, ...] | None:
    analysis = _analysis(grid)
    if analysis["errors"]:
        return None
    return (
        analysis["height"],
        analysis["width"],
        analysis["source_side"],
        analysis["hit_colors"],
        analysis["stop_kind"],
        tuple(sorted(value for _row, _col, value in analysis["off_path_mirrors"])),
    )


def _declared_signature(profile: _Profile) -> tuple[Any, ...]:
    extras = () if profile.distractor_color is None else (profile.distractor_color,)
    return (
        profile.height,
        profile.width,
        profile.source_side,
        profile.hit_colors,
        profile.stop_kind,
        extras,
    )


_PROFILE_BY_SIGNATURE = {
    _declared_signature(profile): name for name, profile in _PROFILE_ROWS
}


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact composite semantic profile from a returned grid."""
    name = _PROFILE_BY_SIGNATURE.get(_profile_signature(grid))
    return {"scene_profile": name} if name is not None else {}


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Accept authority-valid beam scenes, including off-path distractors."""
    del difficulty
    analysis = _analysis(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if not analysis["hit_mirrors"]:
        errors.append("the traced beam must encounter at least one mirror")
    if not analysis["painted"]:
        errors.append("the rule must paint at least one empty traversed cell")
    if analysis["stop_kind"] not in ("interior", "border"):
        errors.append("the beam must terminate at a gray wall")
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observe_overrides(grid).get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as "
                f"{observe_overrides(grid).get(name)!r}"
            )
    return errors


def _construct_profile(profile: _Profile, rng) -> list[list[int]] | None:
    height, width = profile.height, profile.width
    grid = full_grid(height, width, 0)
    for col in range(width):
        grid[0][col] = 5
        grid[-1][col] = 5
    for row in range(height):
        grid[row][0] = 5
        grid[row][-1] = 5

    source_row = rng.randint(1, height - 2)
    if profile.source_side == "left":
        source_col = 1
    elif profile.source_side == "right":
        # Keep room for an empty launch cell, a mirror, and at least one
        # post-reflection horizontal cell while making the right frame nearer.
        source_col = width - 5
    else:
        raise ValueError(f"unknown source side: {profile.source_side!r}")
    grid[source_row][source_col] = 2
    hard = {(source_row, source_col)}
    path: list[tuple[int, int]] = []
    path_set: set[tuple[int, int]] = set()
    row, col, dr, dc = source_row, source_col + 1, 0, 1

    for mirror_color in profile.hit_colors:
        lengths = list(range(1, 5))
        rng.shuffle(lengths)
        placed = False
        for length in lengths:
            zeros: list[tuple[int, int]] = []
            trial_row, trial_col = row, col
            for _step in range(length):
                if not (
                    1 <= trial_row <= height - 2
                    and 1 <= trial_col <= width - 2
                ) or (trial_row, trial_col) in hard:
                    break
                zeros.append((trial_row, trial_col))
                trial_row += dr
                trial_col += dc
            else:
                mirror_pos = (trial_row, trial_col)
                if (
                    1 <= trial_row <= height - 2
                    and 1 <= trial_col <= width - 2
                    and mirror_pos not in hard
                    and mirror_pos not in path_set
                ):
                    next_dr, next_dc = _reflect(mirror_color, dr, dc)
                    next_pos = (trial_row + next_dr, trial_col + next_dc)
                    if (
                        1 <= next_pos[0] <= height - 2
                        and 1 <= next_pos[1] <= width - 2
                        and next_pos not in hard
                    ):
                        for position in zeros:
                            path.append(position)
                            path_set.add(position)
                        grid[trial_row][trial_col] = mirror_color
                        hard.add(mirror_pos)
                        row, col = next_pos
                        dr, dc = next_dr, next_dc
                        placed = True
                        break
        if not placed:
            return None

    if profile.stop_kind == "interior":
        lengths = list(range(1, 5))
        rng.shuffle(lengths)
        placed = False
        for length in lengths:
            zeros = []
            trial_row, trial_col = row, col
            for _step in range(length):
                if not (
                    1 <= trial_row <= height - 2
                    and 1 <= trial_col <= width - 2
                ) or (trial_row, trial_col) in hard:
                    break
                zeros.append((trial_row, trial_col))
                trial_row += dr
                trial_col += dc
            else:
                wall_pos = (trial_row, trial_col)
                post_wall = (trial_row + dr, trial_col + dc)
                if (
                    1 <= trial_row <= height - 2
                    and 1 <= trial_col <= width - 2
                    and wall_pos not in hard
                    and wall_pos not in path_set
                    # Keep at least one untouched interior zero behind the
                    # terminal wall.  This makes the first-wall rule visibly
                    # different from the tempting "ignore interior walls"
                    # shortcut in every scheduled lesson.
                    and 1 <= post_wall[0] <= height - 2
                    and 1 <= post_wall[1] <= width - 2
                    and post_wall not in hard
                    and post_wall not in path_set
                ):
                    for position in zeros:
                        path.append(position)
                        path_set.add(position)
                    grid[trial_row][trial_col] = 5
                    hard.add(wall_pos)
                    hard.add(post_wall)
                    placed = True
                    break
        if not placed:
            return None
    else:
        zeros = []
        trial_row, trial_col = row, col
        placed = False
        for _step in range(height * width):
            if trial_row in (0, height - 1) or trial_col in (0, width - 1):
                placed = True
                break
            if (trial_row, trial_col) in hard:
                break
            zeros.append((trial_row, trial_col))
            trial_row += dr
            trial_col += dc
        if not placed or not zeros:
            return None
        for position in zeros:
            path.append(position)
            path_set.add(position)

    # Every canonical input has exactly one interior wall.  For border-stop
    # profiles it is a true distractor; for interior-stop profiles it is the
    # terminal wall already placed above.
    available = [
        (candidate_row, candidate_col)
        for candidate_row in range(1, height - 1)
        for candidate_col in range(1, width - 1)
        if (candidate_row, candidate_col) not in hard
        and (candidate_row, candidate_col) not in path_set
    ]
    if profile.stop_kind == "border":
        if not available:
            return None
        wall_pos = rng.choice(available)
        grid[wall_pos[0]][wall_pos[1]] = 5
        hard.add(wall_pos)
        available.remove(wall_pos)

    if profile.distractor_color is not None:
        official_output = _simulate(grid)
        candidates = []
        for candidate_row, candidate_col in available:
            has_unused_zero_neighbor = any(
                1 <= candidate_row + delta_row <= height - 2
                and 1 <= candidate_col + delta_col <= width - 2
                and grid[candidate_row + delta_row][candidate_col + delta_col] == 0
                and official_output[candidate_row + delta_row][candidate_col + delta_col] == 0
                for delta_row, delta_col in ((0, 1), (1, 0), (0, -1), (-1, 0))
            )
            if has_unused_zero_neighbor:
                candidates.append((candidate_row, candidate_col))
        if not candidates:
            return None
        mirror_pos = rng.choice(candidates)
        grid[mirror_pos[0]][mirror_pos[1]] = profile.distractor_color

    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    scheduled = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile_name = ctx.draw_choice("scene_profile", [scheduled])
    profile = _PROFILE_BY_NAME[profile_name]
    rng = ctx.draw_rng("layout")
    expected_signature = _declared_signature(profile)
    for _attempt in range(500):
        grid = _construct_profile(profile, rng)
        if grid is None:
            continue
        if self_check(grid):
            continue
        if _profile_signature(grid) != expected_signature:
            continue
        return grid
    raise ValueError(f"could not realize beam profile {profile_name!r}")


def strict_canonical_like(grid) -> list[str]:
    """Check the linked empirical manifold, not independent marginals."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analysis(grid)
    if analysis["source"][1] != 1:
        errors.append("canonical sources occupy interior column 1")
    if len(analysis["interior_walls"]) != 1:
        errors.append("canonical inputs contain exactly one interior gray wall")
    linked = (
        analysis["height"],
        analysis["width"],
        analysis["palette_size"],
        analysis["hit_colors"],
        analysis["stop_kind"],
        len(analysis["off_path_mirrors"]),
    )
    if linked not in _CANONICAL_LINKED_SIGNATURES:
        errors.append(f"linked beam signature is outside the canonical set: {linked!r}")
    return errors


def _rival_all_mirrors_backslash(grid):
    return _simulate(grid, mirror_mode="all_backslash")


def _rival_all_mirrors_slash(grid):
    return _simulate(grid, mirror_mode="all_slash")


def _rival_ignore_interior_walls(grid):
    return _simulate(grid, ignore_interior_walls=True)


def _rival_stop_after_last_mirror(grid):
    analysis = _analysis(grid)
    count = max(1, len(analysis.get("hit_mirrors", ())))
    return _simulate(grid, stop_after_mirrors=count)


def _rival_stop_after_first_mirror(grid):
    return _simulate(grid, stop_after_mirrors=1)


def _rival_launch_away_from_nearest_vertical_frame(grid):
    """Canonical-fitting shortcut: infer launch direction from source placement."""
    return _simulate(grid, launch_mode="away_from_nearest_vertical_frame")


def _rival_launch_from_unhit_mirrors(grid):
    output = rule_mirror(grid)
    analysis = _analysis(grid)
    height, width = len(grid), len(grid[0])
    for mirror_row, mirror_col, _value in analysis.get("off_path_mirrors", ()):
        for delta_row, delta_col in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            row = mirror_row + delta_row
            col = mirror_col + delta_col
            if not (
                0 <= row < height
                and 0 <= col < width
                and grid[row][col] == 0
                and output[row][col] == 0
            ):
                continue
            while 0 <= row < height and 0 <= col < width and grid[row][col] != 5:
                if grid[row][col] == 0:
                    output[row][col] = 8
                row += delta_row
                col += delta_col
            break
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "launch_away_from_nearest_vertical_frame": (
        _rival_launch_away_from_nearest_vertical_frame
    ),
    "treat_every_mirror_as_backslash": _rival_all_mirrors_backslash,
    "treat_every_mirror_as_slash": _rival_all_mirrors_slash,
    "ignore_interior_walls": _rival_ignore_interior_walls,
    "stop_at_last_mirror": _rival_stop_after_last_mirror,
    "stop_at_first_mirror": _rival_stop_after_first_mirror,
    "launch_from_every_unhit_mirror": _rival_launch_from_unhit_mirrors,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)

# All public canonical sources are one cell from the left frame.  This rival
# therefore reproduces every canonical answer while incorrectly launching left
# from a source nearer the right frame.  Generated lessons must rebut it.
CANONICAL_SHORTCUTS = {
    "launch_away_from_nearest_vertical_frame": (
        _rival_launch_away_from_nearest_vertical_frame
    ),
}


def _analysis_witness(predicate: Callable[[dict[str, Any]], bool]):
    def witness(grid) -> bool:
        analysis = _analysis(grid)
        return not analysis["errors"] and bool(predicate(analysis))

    return witness


SEMANTIC_WITNESSES = {
    "slash_reflection_on_path": _analysis_witness(
        lambda analysis: 3 in analysis["hit_colors"]
    ),
    "backslash_reflection_on_path": _analysis_witness(
        lambda analysis: 4 in analysis["hit_colors"]
    ),
    "interior_wall_stops_beam": _analysis_witness(
        lambda analysis: analysis["stop_kind"] == "interior"
    ),
    "outer_frame_stops_beam": _analysis_witness(
        lambda analysis: analysis["stop_kind"] == "border"
    ),
    "off_path_mirror_is_ignored": _analysis_witness(
        lambda analysis: bool(analysis["off_path_mirrors"])
    ),
    "multiple_reflections_are_followed": _analysis_witness(
        lambda analysis: len(analysis["hit_mirrors"]) >= 2
    ),
    "right_side_source_still_launches_right": _analysis_witness(
        lambda analysis: analysis["source_side"] == "right"
    ),
}
WITNESS_RIVALS = {
    "slash_reflection_on_path": ["treat_every_mirror_as_backslash"],
    "backslash_reflection_on_path": ["treat_every_mirror_as_slash"],
    "interior_wall_stops_beam": ["ignore_interior_walls"],
    "outer_frame_stops_beam": ["stop_at_last_mirror"],
    "off_path_mirror_is_ignored": ["launch_from_every_unhit_mirror"],
    "multiple_reflections_are_followed": ["stop_at_first_mirror"],
    "right_side_source_still_launches_right": [
        "launch_away_from_nearest_vertical_frame"
    ],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Require every four-demo window to falsify the named shortcut rules."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]

    reasons: list[str] = []
    hit_colors: set[int] = set()
    stop_kinds: set[str] = set()
    source_sides: set[str] = set()
    has_off_path = False
    has_multi_turn = False
    shapes: set[tuple[int, int]] = set()
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the beam-tracing rule")
            continue
        analysis = _analysis(pair["input"])
        if analysis["errors"]:
            reasons.append(f"demo {index} is structurally invalid: {analysis['errors']}")
            continue
        hit_colors.update(analysis["hit_colors"])
        stop_kinds.add(analysis["stop_kind"])
        source_sides.add(analysis["source_side"])
        has_off_path = has_off_path or bool(analysis["off_path_mirrors"])
        has_multi_turn = has_multi_turn or len(analysis["hit_mirrors"]) >= 2
        shapes.add((analysis["height"], analysis["width"]))

    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the beam-tracing rule")
    if hit_colors != {3, 4}:
        reasons.append("demonstrations must expose both slash and backslash reflection")
    if stop_kinds != {"interior", "border"}:
        reasons.append("demonstrations must expose both interior-wall and frame stops")
    if source_sides != {"left", "right"}:
        reasons.append("demonstrations must expose sources near both vertical frames")
    if not has_off_path:
        reasons.append("demonstrations need an off-path mirror distractor")
    if not has_multi_turn:
        reasons.append("demonstrations need a route with multiple reflections")
    if len(shapes) < 2:
        reasons.append("demonstrations need at least two grid shapes")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demonstrations do not falsify rival: {name}")
    return reasons
