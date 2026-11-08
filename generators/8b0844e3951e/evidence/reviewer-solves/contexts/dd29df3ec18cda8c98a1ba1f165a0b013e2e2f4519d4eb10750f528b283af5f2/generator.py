"""Generator for ARC task 5582e5ca (fill with the nonzero mode color).

The canonical 3x3 demonstrations use a low-plurality nonzero mode (count 3),
several near runners-up, and sometimes a zero distractor.  This generator keeps
that frequency-comparison lesson while widening only to 3..5 cells per side.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "8b0844e3951e"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "b2abbd0be28f"

SUMMARY = (
    "A 3x3 to 5x5 multicolor grid has one strict most-common NONZERO color. "
    "Its lead may be clear or only one cell over the runner-up. Zero is absent, "
    "sparse, or more common than every nonzero color, so the solver must ignore "
    "zero when taking the mode. Fill an output of identical dimensions entirely "
    "with that unique nonzero mode color."
)
INVARIANTS = [
    "the grid is rectangular with height and width in 3..5",
    "there is a unique most-common nonzero color",
    "at least two other nonzero colors appear and the input is not uniform",
    "zero is absent, less frequent than the nonzero mode, or strictly more frequent",
]

MODE_STRENGTHS = ("clear", "near_tie")
BACKGROUND_PROFILES = ("absent", "sparse", "dominant")
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

AXES = {
    "grid_h": {"type": "int", "default": "difficulty-skewed 3..5", "valid": "3..5"},
    "grid_w": {"type": "int", "default": "difficulty-skewed 3..5", "valid": "3..5"},
    "mode_color": {"type": "color", "default": "rng", "valid": "1..9"},
    "mode_strength": {
        "type": "str",
        "default": "clear-biased easy / near_tie-biased hard",
        "valid": "|".join(MODE_STRENGTHS),
    },
    "background_profile": {
        "type": "str",
        "default": "absent|sparse|dominant",
        "valid": "|".join(BACKGROUND_PROFILES),
    },
}


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unsupported difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    h = ctx.draw_int_diff("grid_h", 3, 5)
    w = ctx.draw_int_diff("grid_w", 3, 5)
    mode_color = ctx.draw_color("mode_color", exclude={0})

    strength_options = {
        "easy": ("clear", "clear", "clear", "near_tie"),
        "medium": ("clear", "near_tie"),
        "hard": ("near_tie", "near_tie", "near_tie", "clear"),
        None: ("clear", "near_tie"),
    }[difficulty]
    mode_strength = ctx.draw_choice("mode_strength", strength_options)
    background_profile = ctx.draw_choice(
        "background_profile", ("absent", "sparse", "dominant")
    )

    rng = ctx.draw_rng("count_profile")
    zero_count, mode_count, distractor_counts = _choose_frequency_profile(
        h * w, background_profile, mode_strength, difficulty, rng
    )
    distractor_colors = ctx.draw_distinct_colors(
        "distractor_colors",
        n=len(distractor_counts),
        exclude={0, mode_color},
    )

    morphology_rng = ctx.draw_rng("morphology")
    if background_profile == "dominant":
        # Zero is the visual background, but the requested answer lives inside
        # the one connected nonzero object.  This rebuts "fill with background".
        foreground = _connected_cells(h, w, h * w - zero_count, morphology_rng)
        grid = full_grid(h, w, 0)
        values = [mode_color] * mode_count
        for color, count in zip(distractor_colors, distractor_counts):
            values.extend([color] * count)
    else:
        # The nonzero mode is the visual background.  Its complement is one
        # connected, mixed-color object, matching canonical fragmentation.
        foreground = _connected_cells(h, w, h * w - mode_count, morphology_rng)
        grid = full_grid(h, w, mode_color)
        values = [0] * zero_count
        for color, count in zip(distractor_colors, distractor_counts):
            values.extend([color] * count)

    morphology_rng.shuffle(values)
    for (r, c), value in zip(foreground, values):
        grid[r][c] = value

    errors = self_check(grid, difficulty=difficulty)
    if errors:
        raise RuntimeError("internal invalid draw: " + "; ".join(errors))
    return grid


def _choose_frequency_profile(area, background_profile, mode_strength, difficulty, rng):
    candidates = []
    for zero_count in range(area - 2):
        if background_profile == "absent" and zero_count != 0:
            continue
        if background_profile == "sparse" and zero_count == 0:
            continue
        if background_profile == "dominant" and zero_count == 0:
            continue
        nonzero_total = area - zero_count
        for k in range(2, min(4, nonzero_total - 1) + 1):
            for mode_count in range(2, nonzero_total - k + 1):
                if background_profile == "sparse" and not zero_count < mode_count:
                    continue
                if background_profile == "dominant" and not zero_count > mode_count:
                    continue
                counts = _allocate_distractors(nonzero_total - mode_count, k, mode_count, mode_strength)
                if counts is None:
                    continue
                palette = 1 + k + int(zero_count > 0)
                if mode_count / area >= (2 / 3):
                    continue
                ratio = mode_count / nonzero_total
                target_ratio = {
                    ("near_tie", "easy"): 0.40,
                    ("near_tie", "medium"): 0.34,
                    ("near_tie", "hard"): 0.28,
                    ("near_tie", None): 0.33,
                    ("clear", "easy"): 0.56,
                    ("clear", "medium"): 0.46,
                    ("clear", "hard"): 0.40,
                    ("clear", None): 0.46,
                }[(mode_strength, difficulty)]
                zero_target = {"absent": 0.0, "sparse": 0.10, "dominant": 0.42}[background_profile]
                score = (
                    abs(palette - 5),
                    abs(ratio - target_ratio),
                    abs(zero_count / area - zero_target),
                )
                candidates.append((score, zero_count, mode_count, counts))
    if not candidates:
        raise ValueError(
            f"no lawful profile for area={area}, background_profile={background_profile}, "
            f"mode_strength={mode_strength}"
        )
    candidates.sort(key=lambda item: item[0])
    best_score = candidates[0][0]
    near_best = [item for item in candidates if item[0] <= (best_score[0], best_score[1] + 0.08, best_score[2] + 0.08)]
    _, zero_count, mode_count, counts = rng.choice(near_best[: max(1, min(8, len(near_best)))])
    rng.shuffle(counts)
    return zero_count, mode_count, counts


def _allocate_distractors(total, k, mode_count, mode_strength):
    cap = mode_count - (1 if mode_strength == "near_tie" else 2)
    if cap < 1 or total < k or total > k * cap:
        return None
    counts = [1] * k
    remaining = total - k
    if mode_strength == "near_tie":
        need = cap - 1
        if remaining < need:
            return None
        counts[0] += need
        remaining -= need
    i = 0
    while remaining:
        room = cap - counts[i % k]
        if room:
            add = min(room, remaining)
            counts[i % k] += add
            remaining -= add
        i += 1
        if i > 100:
            return None
    if mode_strength == "near_tie" and max(counts) != mode_count - 1:
        return None
    if mode_strength == "clear" and max(counts) > mode_count - 2:
        return None
    return counts


def _connected_cells(h, w, n, rng):
    if not 1 <= n <= h * w:
        raise ValueError(f"connected-cell request {n} outside 1..{h*w}")
    start = (rng.randrange(h), rng.randrange(w))
    cells = {start}
    frontier = set(_neighbors(start[0], start[1], h, w))
    while len(cells) < n:
        choices = sorted(frontier)
        chosen = rng.choice(choices)
        frontier.remove(chosen)
        cells.add(chosen)
        for nxt in _neighbors(chosen[0], chosen[1], h, w):
            if nxt not in cells:
                frontier.add(nxt)
    result = sorted(cells)
    rng.shuffle(result)
    return result


def _neighbors(r, c, h, w):
    return [
        (nr, nc)
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if 0 <= nr < h and 0 <= nc < w
    ]


def observe_overrides(grid):
    facts, errors = _analyze(grid)
    if errors:
        return {}
    return {
        "grid_h": facts["h"],
        "grid_w": facts["w"],
        "mode_color": facts["mode_color"],
        "mode_strength": facts["mode_strength"],
        "background_profile": facts["background_profile"],
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    _, errors = _analyze(grid)
    return errors


def _analyze(grid):
    errors = []
    if not isinstance(grid, list) or not grid or not all(isinstance(row, list) for row in grid):
        return {}, ["grid must be a nonempty list of rows"]
    h = len(grid)
    w = len(grid[0]) if grid[0] else 0
    if w == 0 or any(len(row) != w for row in grid):
        return {}, ["grid must be nonempty and rectangular"]
    if not (3 <= h <= 5 and 3 <= w <= 5):
        errors.append(f"dimensions must be in 3..5, got {h}x{w}")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        errors.append("cells must be integer ARC colors 0..9")
        return {}, errors

    counts = Counter(value for row in grid for value in row)
    nonzero = {color: count for color, count in counts.items() if color != 0}
    if len(nonzero) < 3:
        errors.append("need a mode plus at least two nonzero distractor colors")
        return {}, errors
    ranked = sorted(nonzero.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        errors.append("nonzero mode must be unique")
        return {}, errors
    mode_color, mode_count = ranked[0]
    runner_count = ranked[1][1]
    if mode_count - runner_count == 1:
        mode_strength = "near_tie"
    elif mode_count - runner_count >= 2:
        mode_strength = "clear"
    else:
        errors.append("invalid nonzero mode margin")
        return {}, errors

    zero_count = counts.get(0, 0)
    if zero_count == 0:
        background_profile = "absent"
    elif zero_count < mode_count:
        background_profile = "sparse"
    elif zero_count > mode_count:
        background_profile = "dominant"
    else:
        errors.append("zero count may not tie the nonzero mode count")
        return {}, errors

    palette_size = len(counts)
    if not 4 <= palette_size <= 6:
        errors.append(f"palette must contain 4..6 colors, got {palette_size}")
    if mode_count >= h * w:
        errors.append("input is already uniform")
    if mode_count / (h * w) >= (2 / 3):
        errors.append("mode is too overwhelming to teach frequency comparison")

    return {
        "h": h,
        "w": w,
        "mode_color": mode_color,
        "mode_count": mode_count,
        "runner_count": runner_count,
        "mode_strength": mode_strength,
        "zero_count": zero_count,
        "background_profile": background_profile,
        "palette_size": palette_size,
    }, errors


def _component_count(grid, background):
    h, w = len(grid), len(grid[0])
    seen = set()
    total = 0
    for r in range(h):
        for c in range(w):
            if grid[r][c] == background or (r, c) in seen:
                continue
            total += 1
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                cr, cc = queue.popleft()
                for nr, nc in _neighbors(cr, cc, h, w):
                    if grid[nr][nc] != background and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
    return total
