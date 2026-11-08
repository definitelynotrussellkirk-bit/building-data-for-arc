"""Generator for 7c2b3290ba62 — identify the candidate pair completing a target.

The input is a horizontal sequence of equally sized panels separated by full
color-9 columns::

    SOURCE | TARGET | CANDIDATE_0 | CANDIDATE_1 | ...

Panel occupancy ignores color identity: every value other than 0 and 9 is an
occupied cell.  Exactly one unordered candidate pair has occupancy whose union
with SOURCE equals TARGET.  The authoritative Racket rule returns a 1 x N strip
with cyan (8) at those two candidate indices.

This generator constructs the unique pair rather than hoping random panels have
one.  Every normal draw also makes three common wrong rules visibly fail:
ignoring SOURCE, intersecting candidates instead of unioning them, and selecting
a single completing candidate.  One out of every four default draws preserves
the canonical 4 x 29 / seven-color profile in every difficulty band.
"""
from __future__ import annotations

from collections.abc import Callable, Sequence
from itertools import combinations
from typing import Any

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "7c2b3290ba62"
TASK_ID = GENERATOR_ID
RULE_HASH = "8518d3e47ce6"
VERSION = "3.1.0"

SUMMARY = (
    "Panels SOURCE | TARGET | CANDIDATES are separated by color-9 columns. "
    "Using occupied positions only, find the unique candidate pair whose union "
    "with SOURCE exactly equals TARGET; mark those two candidate indices cyan "
    "in a 1xN output strip. Generated lessons vary geometry, candidate count, "
    "pair position and panel colors while retaining a canonical-profile lane."
)

INVARIANTS = [
    "SOURCE, TARGET and 3..7 candidate panels have equal geometry and single-column color-9 separators",
    "SOURCE is a non-empty proper subset of TARGET and contributes cells absent from every candidate",
    "exactly one pair of non-empty, disjoint candidates completes TARGET with SOURCE",
    "every non-matching candidate has at least one occupied cell outside TARGET",
    "cyan 8 is reserved for output markers and never appears in generated inputs",
    "SOURCE/TARGET share one panel color; candidate panel colors are distinct and task-irrelevant (the seven-candidate lane necessarily reuses the source color once)",
]

EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.20
SCHEDULE_PROFILES = (0, 1, 2, 3)
EXPECTED_OUTPUT_CODOMAIN = sum(n * (n - 1) // 2 for n in range(3, 8))

AXES = {
    "panel_h": {
        "type": "int",
        "default": "canonical slot 4; otherwise difficulty-aware 3..6",
        "valid": "3..6",
    },
    "panel_w": {
        "type": "int",
        "default": "canonical slot 4; otherwise compatible difficulty-aware 2..4",
        "valid": "2..4",
    },
    "n_cands": {
        "type": "int",
        "default": "canonical slot 4; otherwise difficulty-aware 3..7",
        "valid": "3..7",
    },
}

# ARC grids are at most 30 columns.  Total width is
# (n_cands + 2) * panel_w + (n_cands + 1) separators.
INCOMPATIBLE_OVERRIDE_COMBINATIONS = [
    {"panel_w": 4, "n_cands": 5},
    {"panel_w": 4, "n_cands": 6},
    {"panel_w": 4, "n_cands": 7},
    {"panel_w": 3, "n_cands": 6},
    {"panel_w": 3, "n_cands": 7},
]

_VALID_DIFFICULTIES = (None, "easy", "medium", "hard")
_AXIS_BOUNDS = {
    "panel_h": (3, 6),
    "panel_w": (2, 4),
    "n_cands": (3, 7),
}
_OCCUPANCY_COLORS = tuple(range(1, 8))


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> int:
    """Stable four-step curriculum schedule, independent of seed and band."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _total_width(panel_w: int, n_cands: int) -> int:
    return (n_cands + 2) * panel_w + (n_cands + 1)


def _compatible(panel_w: int, n_cands: int) -> bool:
    return _total_width(panel_w, n_cands) <= 30


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    if difficulty not in _VALID_DIFFICULTIES:
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override axis/axes: {', '.join(unknown)}")
    for name, value in overrides.items():
        if value is None:
            continue
        if type(value) is not int:
            raise TypeError(f"{name} must be an integer, not {type(value).__name__}")
        lo, hi = _AXIS_BOUNDS[name]
        if not lo <= value <= hi:
            raise ValueError(f"{name} override {value} outside [{lo}, {hi}]")
    panel_w = overrides.get("panel_w")
    n_cands = overrides.get("n_cands")
    if panel_w is not None and n_cands is not None and not _compatible(panel_w, n_cands):
        raise ValueError(
            "incompatible overrides panel_w and n_cands: "
            f"width {_total_width(panel_w, n_cands)} exceeds ARC limit 30"
        )


def _draw_axis(ctx, overrides: dict[str, Any], name: str, lo: int, hi: int) -> int:
    valid_lo, valid_hi = _AXIS_BOUNDS[name]
    if overrides.get(name) is not None:
        return ctx.draw_int_strict(name, valid_lo, valid_hi)
    return ctx.draw_int_strict(name, lo, hi)


def _scheduled_candidate_count(seed: int, profile: int, difficulty: Any) -> int:
    """Low-discrepancy default lane over the task's finite output alphabet.

    The unbanded lane is deliberately arranged so the standard 24-episode,
    six-example lint horizon observes every legal pair label for N=3..7.
    Difficulty bands retain their intended candidate-count progression.
    """
    if profile == 0:
        return 4
    if difficulty == "easy":
        return {1: 4, 2: 3, 3: 4}[profile]
    if difficulty == "medium":
        return {1: 5, 2: 6, 3: 4 if seed % 2 == 0 else 5}[profile]
    if difficulty == "hard":
        return {1: 7, 2: 6, 3: 7}[profile]
    if profile == 1:
        return 7
    if profile == 2:
        return 6
    # Three sparse N=3 episodes are enough to cover its three labels; the
    # remaining profile-3 episodes exercise all ten N=5 labels.
    return 3 if seed % 8 == 0 else 5


def _default_ranges(seed: int, profile: int, difficulty: Any) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int]]:
    if profile == 0:
        return (4, 4), (4, 4), (4, 4)
    if difficulty == "easy":
        h_range, w_range = (3, 4), (2, 4)
    elif difficulty == "hard":
        h_range, w_range = (5, 6), (2, 3)
    elif difficulty == "medium":
        h_range, w_range = (4, 5), (2, 4)
    else:
        h_range, w_range = (3, 6), (2, 4)
    n_cands = _scheduled_candidate_count(seed, profile, difficulty)
    return h_range, w_range, (n_cands, n_cands)


def _draw_geometry(ctx, overrides: dict[str, Any], profile: int, difficulty: Any) -> tuple[int, int, int]:
    h_range, w_range, n_range = _default_ranges(ctx.seed, profile, difficulty)
    panel_h = _draw_axis(ctx, overrides, "panel_h", *h_range)

    # Draw an explicitly supplied axis over its full declared domain.  When
    # only one linked axis is supplied, adapt the other default rather than
    # rejecting a valid single-axis request because of a difficulty preference.
    if overrides.get("n_cands") is not None:
        n_cands = _draw_axis(ctx, overrides, "n_cands", *_AXIS_BOUNDS["n_cands"])
    else:
        n_lo, n_hi = n_range
        if overrides.get("panel_w") is not None:
            max_n = max(n for n in range(3, 8) if _compatible(int(overrides["panel_w"]), n))
            n_lo, n_hi = max(3, n_lo), min(max_n, n_hi)
            if n_lo > n_hi:
                n_lo, n_hi = 3, max_n
        n_cands = _draw_axis(ctx, overrides, "n_cands", n_lo, n_hi)

    if overrides.get("panel_w") is not None:
        panel_w = _draw_axis(ctx, overrides, "panel_w", *_AXIS_BOUNDS["panel_w"])
    else:
        max_w = max(width for width in range(2, 5) if _compatible(width, n_cands))
        w_lo, w_hi = max(2, w_range[0]), min(max_w, w_range[1])
        if w_lo > w_hi:
            w_lo, w_hi = 2, max_w
        panel_w = _draw_axis(ctx, overrides, "panel_w", w_lo, w_hi)

    if not _compatible(panel_w, n_cands):
        raise ValueError(
            "incompatible overrides panel_w and n_cands: "
            f"width {_total_width(panel_w, n_cands)} exceeds ARC limit 30"
        )
    return panel_h, panel_w, n_cands


def _panel_palette(ctx, n_cands: int, canonical_profile: bool) -> tuple[int, list[int]]:
    if canonical_profile:
        # Exact public palette: SOURCE/TARGET=2; candidate colors 3,4,6,7.
        return 2, [3, 4, 6, 7]
    palette = list(_OCCUPANCY_COLORS)
    ctx.draw_rng("panel_palette").shuffle(palette)
    if n_cands == len(palette):
        # ARC has only seven non-background, non-separator, non-output-marker
        # colors.  Keep candidate colors distinct; one candidate therefore
        # shares SOURCE/TARGET's color in this widest lane.
        return palette[0], palette[:]
    return palette[0], palette[1 : n_cands + 1]


def _paint_panel(grid: list[list[int]], panel_index: int, panel_w: int, cells: set[tuple[int, int]], color: int) -> None:
    start = panel_index * (panel_w + 1)
    for row, col in cells:
        grid[row][start + col] = color


def _build(ctx, panel_h: int, panel_w: int, n_cands: int, *, canonical_profile: bool) -> list[list[int]]:
    n_panels = n_cands + 2
    grid = full_grid(panel_h, _total_width(panel_w, n_cands), 0)
    for panel_index in range(1, n_panels):
        separator = panel_index * (panel_w + 1) - 1
        for row in range(panel_h):
            grid[row][separator] = 9

    cells = [(row, col) for row in range(panel_h) for col in range(panel_w)]
    occupancy_rng = ctx.draw_rng("occupancy")
    if canonical_profile:
        target_count = occupancy_rng.choice((3, 4))
        source_count = target_count - 2
    else:
        max_target = len(cells) - 1
        if ctx.difficulty == "easy":
            lo, hi = 3, min(max_target, max(4, len(cells) // 2))
        elif ctx.difficulty == "hard":
            lo, hi = max(3, len(cells) // 2), max_target
        else:
            lo, hi = 3, max_target
        target_count = occupancy_rng.randint(lo, hi)
        source_count = occupancy_rng.randint(1, target_count - 2)

    target = set(occupancy_rng.sample(cells, target_count))
    source = set(occupancy_rng.sample(sorted(target), source_count))
    missing = list(target - source)
    occupancy_rng.shuffle(missing)
    if canonical_profile:
        cut = 1
    else:
        cut = occupancy_rng.randint(1, len(missing) - 1)
    part_a = set(missing[:cut])
    part_b = set(missing[cut:])
    outside = [cell for cell in cells if cell not in target]

    pair_rng = ctx.draw_rng("candidate_content")
    answer_pairs = list(combinations(range(n_cands), 2))
    answer_a, answer_b = answer_pairs[(ctx.seed + ctx.sample_index) % len(answer_pairs)]
    candidate_cells: list[set[tuple[int, int]]] = []
    for candidate_index in range(n_cands):
        if candidate_index == answer_a:
            chosen = set(part_a)
        elif candidate_index == answer_b:
            chosen = set(part_b)
        elif canonical_profile:
            chosen = {pair_rng.choice(outside)}
        else:
            # Distractors never use SOURCE cells and always carry at least one
            # cell outside TARGET, so no pair containing one can be an exact
            # completion and no source-free pair can accidentally equal TARGET.
            available = [cell for cell in cells if cell not in source]
            count = pair_rng.randint(1, min(len(available), max(2, len(cells) // 2)))
            chosen = set(pair_rng.sample(available, count))
            if not (chosen - target):
                chosen.add(pair_rng.choice(outside))
        candidate_cells.append(chosen)

    source_color, candidate_colors = _panel_palette(ctx, n_cands, canonical_profile)
    _paint_panel(grid, 0, panel_w, source, source_color)
    _paint_panel(grid, 1, panel_w, target, source_color)
    for index, chosen in enumerate(candidate_cells):
        _paint_panel(grid, 2 + index, panel_w, chosen, candidate_colors[index])
    return grid


def generate(seed: int, sample_index: int, *, difficulty: Any = None, **overrides: Any) -> list[list[int]]:
    _validate_call(difficulty, overrides)
    profile = schedule_profile(seed, sample_index, difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    panel_h, panel_w, n_cands = _draw_geometry(ctx, overrides, profile, difficulty)
    canonical_profile = profile == 0 and (panel_h, panel_w, n_cands) == (4, 4, 4)
    return _build(ctx, panel_h, panel_w, n_cands, canonical_profile=canonical_profile)


def _validate_grid_shape(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    for row in grid:
        for value in row:
            if type(value) is not int or not 0 <= value <= 9:
                raise ValueError("grid cells must be integer ARC colors 0..9")
    return len(grid), width


def _split_panels(grid: list[list[int]]) -> list[list[list[int]]]:
    height, width = _validate_grid_shape(grid)
    separator_cols = [
        col for col in range(width) if all(grid[row][col] == 9 for row in range(height))
    ]
    if len(separator_cols) < 4:
        raise ValueError(f"expected at least four full color-9 separators, got {len(separator_cols)}")
    panel_w = separator_cols[0]
    if panel_w < 1:
        raise ValueError("first panel is empty")
    expected = list(range(panel_w, width, panel_w + 1))
    if separator_cols != expected:
        raise ValueError(f"separator columns are not single and evenly spaced: {separator_cols}")
    if expected[-1] >= width - 1:
        raise ValueError("last candidate panel is empty")

    panels: list[list[list[int]]] = []
    start = 0
    for separator in separator_cols + [width]:
        panel = [row[start:separator] for row in grid]
        if not panel or any(len(row) != panel_w for row in panel):
            raise ValueError("panels must have equal positive width")
        panels.append(panel)
        start = separator + 1
    return panels


def _occupancy(panel: Sequence[Sequence[int]]) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(panel)
        for col, value in enumerate(values)
        if value not in (0, 9)
    }


def _panel_nonzero_colors(panel: Sequence[Sequence[int]]) -> set[int]:
    return {value for row in panel for value in row if value not in (0, 9)}


def _analysis(grid: list[list[int]]) -> dict[str, Any]:
    panels = _split_panels(grid)
    if len(panels) < 5:
        raise ValueError("expected SOURCE, TARGET and at least three candidates")
    source = _occupancy(panels[0])
    target = _occupancy(panels[1])
    candidates = [_occupancy(panel) for panel in panels[2:]]
    good_pairs = [
        (left, right)
        for left in range(len(candidates))
        for right in range(left + 1, len(candidates))
        if source | candidates[left] | candidates[right] == target
    ]
    return {
        "panels": panels,
        "panel_h": len(grid),
        "panel_w": len(panels[0][0]),
        "n_cands": len(candidates),
        "source": source,
        "target": target,
        "candidates": candidates,
        "good_pairs": good_pairs,
    }


def _pair_output(n_cands: int, pair: tuple[int, int] | None) -> list[list[int]]:
    output = [[0] * n_cands]
    if pair is not None:
        output[0][pair[0]] = 8
        output[0][pair[1]] = 8
    return output


def rule_mirror(grid: list[list[int]]) -> list[list[int]]:
    """Independent Python mirror of the authoritative first-matching-pair rule."""
    info = _analysis(grid)
    pair = info["good_pairs"][0] if info["good_pairs"] else None
    return _pair_output(info["n_cands"], pair)


oracle_output = rule_mirror


def observe_overrides(grid: list[list[int]]) -> dict[str, int]:
    info = _analysis(grid)
    return {
        "panel_h": info["panel_h"],
        "panel_w": info["panel_w"],
        "n_cands": info["n_cands"],
    }


def self_check(grid: Any, *, difficulty: Any = None, meta: Any = None) -> list[str]:
    del difficulty, meta
    try:
        info = _analysis(grid)
    except (TypeError, ValueError) as exc:
        return [str(exc)]

    errors: list[str] = []
    panel_h, panel_w, n_cands = info["panel_h"], info["panel_w"], info["n_cands"]
    if not 3 <= panel_h <= 6:
        errors.append(f"panel height {panel_h} outside generated domain 3..6")
    if not 2 <= panel_w <= 4:
        errors.append(f"panel width {panel_w} outside generated domain 2..4")
    if not 3 <= n_cands <= 7:
        errors.append(f"candidate count {n_cands} outside generated domain 3..7")
    if not _compatible(panel_w, n_cands):
        errors.append("panel width and candidate count exceed ARC width 30")

    panels = info["panels"]
    if any(9 in row for panel in panels for row in panel):
        errors.append("color 9 is reserved for full separator columns")
    if any(8 in row for panel in panels for row in panel):
        errors.append("color 8 is reserved for output markers")

    source, target = info["source"], info["target"]
    candidates = info["candidates"]
    capacity = panel_h * panel_w
    if not source:
        errors.append("SOURCE occupancy must be non-empty")
    if not source < target:
        errors.append("SOURCE occupancy must be a proper subset of TARGET")
    if len(target) > capacity - 1:
        errors.append("TARGET must leave at least one outside cell for distractors")
    if len(target - source) < 2:
        errors.append("TARGET minus SOURCE must contain at least two cells")
    if any(not candidate for candidate in candidates):
        errors.append("every candidate panel must be non-empty")
    if any(source & candidate for candidate in candidates):
        errors.append("candidate occupancies must not repeat SOURCE cells")

    source_colors = _panel_nonzero_colors(panels[0])
    target_colors = _panel_nonzero_colors(panels[1])
    candidate_colors = [_panel_nonzero_colors(panel) for panel in panels[2:]]
    if len(source_colors) != 1 or target_colors != source_colors:
        errors.append("SOURCE and TARGET must be monochrome in the same occupancy color")
    if any(len(colors) != 1 for colors in candidate_colors):
        errors.append("each candidate panel must be monochrome")
    flat_candidate_colors = [next(iter(colors)) for colors in candidate_colors if len(colors) == 1]
    if len(flat_candidate_colors) == len(candidate_colors):
        if len(set(flat_candidate_colors)) != len(flat_candidate_colors):
            errors.append("candidate panel colors must be distinct")
        if source_colors:
            source_color = next(iter(source_colors))
            source_matches = flat_candidate_colors.count(source_color)
            expected_matches = 1 if n_cands == 7 else 0
            if source_matches != expected_matches:
                errors.append(
                    "candidate/source color overlap must be absent except for "
                    "exactly one candidate in the seven-candidate lane"
                )

    good_pairs = info["good_pairs"]
    if len(good_pairs) != 1:
        errors.append(f"expected exactly one completing candidate pair, got {good_pairs}")
    else:
        left, right = good_pairs[0]
        if candidates[left] & candidates[right]:
            errors.append("the completing candidates must be disjoint complements")
        for index, candidate in enumerate(candidates):
            if index not in (left, right) and not (candidate - target):
                errors.append(f"distractor candidate {index} needs a cell outside TARGET")
    return errors


def strict_canonical_like(grid: list[list[int]]) -> list[str]:
    """Recognize the exact public geometry/palette family, not an exact replay."""
    errors = self_check(grid)
    if errors:
        return [f"generator-domain: {reason}" for reason in errors]
    info = _analysis(grid)
    reasons: list[str] = []
    if (info["panel_h"], len(grid[0]), info["panel_w"], info["n_cands"]) != (4, 29, 4, 4):
        reasons.append("expected canonical geometry: four rows, width 29, six 4-column panels")
    colors = {value for row in grid for value in row}
    if len(colors) != 7:
        reasons.append(f"expected seven input colors including 0 and 9, got {len(colors)}")
    if len(info["source"]) not in (1, 2):
        reasons.append("canonical SOURCE occupancy has one or two cells")
    if len(info["target"]) not in (3, 4):
        reasons.append("canonical TARGET occupancy has three or four cells")
    if any(len(candidate) != 1 for candidate in info["candidates"]):
        reasons.append("canonical candidates are singleton occupancies")
    return reasons


def _rival_ignore_source(grid: list[list[int]]) -> list[list[int]]:
    info = _analysis(grid)
    candidates, target = info["candidates"], info["target"]
    pair = next(
        (
            (left, right)
            for left in range(len(candidates))
            for right in range(left + 1, len(candidates))
            if candidates[left] | candidates[right] == target
        ),
        None,
    )
    return _pair_output(info["n_cands"], pair)


def _rival_intersection(grid: list[list[int]]) -> list[list[int]]:
    info = _analysis(grid)
    source, target, candidates = info["source"], info["target"], info["candidates"]
    pair = next(
        (
            (left, right)
            for left in range(len(candidates))
            for right in range(left + 1, len(candidates))
            if source | (candidates[left] & candidates[right]) == target
        ),
        None,
    )
    return _pair_output(info["n_cands"], pair)


def _rival_single_candidate(grid: list[list[int]]) -> list[list[int]]:
    info = _analysis(grid)
    output = [[0] * info["n_cands"]]
    for index, candidate in enumerate(info["candidates"]):
        if info["source"] | candidate == info["target"]:
            output[0][index] = 8
            break
    return output


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "ignore_source": _rival_ignore_source,
    "intersect_candidates": _rival_intersection,
    "single_candidate": _rival_single_candidate,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _witness_source_required(grid: list[list[int]]) -> bool:
    info = _analysis(grid)
    return bool(info["source"]) and all(info["source"].isdisjoint(candidate) for candidate in info["candidates"])


def _witness_disjoint_complements(grid: list[list[int]]) -> bool:
    info = _analysis(grid)
    if len(info["good_pairs"]) != 1:
        return False
    left, right = info["good_pairs"][0]
    a, b = info["candidates"][left], info["candidates"][right]
    return bool(a and b) and a.isdisjoint(b) and info["source"] | a | b == info["target"]


def _witness_pair_required(grid: list[list[int]]) -> bool:
    info = _analysis(grid)
    return all(info["source"] | candidate != info["target"] for candidate in info["candidates"])


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "source_required": _witness_source_required,
    "disjoint_complements": _witness_disjoint_complements,
    "pair_required": _witness_pair_required,
}
WITNESS_RIVALS = {
    "source_required": ["ignore_source"],
    "disjoint_complements": ["intersect_candidates"],
    "pair_required": ["single_candidate"],
}


def lesson_identifiable(demos: list[dict[str, Any]], query: dict[str, Any]) -> list[str]:
    """Reject a lesson when a declared wrong rule fits demos but changes query."""
    reasons: list[str] = []
    if not isinstance(demos, list) or not isinstance(query, dict):
        return ["lesson must contain a demo list and one query pair"]
    for name, rival in LESSON_COMPETITORS.items():
        try:
            query_differs = rival(query["input"]) != query["output"]
            fits_demos = all(rival(pair["input"]) == pair["output"] for pair in demos)
        except (KeyError, TypeError, ValueError) as exc:
            reasons.append(f"{name}: invalid lesson pair ({exc})")
            continue
        if query_differs and fits_demos:
            reasons.append(f"{name} fits every demonstration but changes the query answer")
    return reasons
