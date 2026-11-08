"""Generator for H31 — rank non-background colors by global cell frequency.

The authoritative rule counts every nonzero color across the whole grid,
combining disconnected components, then emits one row containing every color
ordered by descending total count. Equal counts are ordered by ascending color
value.

Three consecutive examples cover the decisive semantics:

* ``distinct`` — distinct totals, with the least-frequent color split into
  several objects so object-count and first-seen shortcuts fail;
* ``tie`` — at least two colors have equal totals, with row-major first
  occurrence deliberately opposing the ascending-color tie break;
* ``component_trap`` — the most frequent color is split into components whose
  largest member is smaller than the runner-up's component, refuting a
  largest-component interpretation.
"""
from __future__ import annotations

from collections import Counter, deque
from typing import Any, Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "08728376666d"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "6910296fd9a0"  # sha256[:12] of normalized canonical program_solution
EXAMPLES_NEEDED = 3
MIN_STRICT_FRAC = 1.0

SUMMARY = (
    "A sparse 0-background grid contains 2..5 nonzero colors. Count all cells "
    "of each color globally, combining disconnected components, and output one "
    "row of every color sorted by descending total count with ascending color "
    "as the tie break. A three-profile schedule exposes distinct totals, an "
    "explicit tie, and a largest-component trap."
)

INVARIANTS = [
    "background 0 is present and remains the unique excluded color",
    "2..5 nonzero colors each occupy at least three cells",
    "the output contains every nonzero color exactly once",
    "ranking uses total cell count across all same-color components",
    "equal total counts are ordered by ascending numeric color",
]

PROFILES = ("distinct", "tie", "component_trap")

AXES = {
    "grid_h": {
        "type": "int",
        "default": "canonical-shape schedule; overrides 7..16",
        "valid": "7..16",
    },
    "grid_w": {
        "type": "int",
        "default": "canonical-shape schedule; overrides 8..18",
        "valid": "8..18",
    },
    "n_colors": {
        "type": "int",
        "default": "canonical palette-size schedule; overrides 2..5",
        "valid": "2..5",
    },
    "profile": {
        "type": "str",
        "default": "sample_index schedule over distinct|tie|component_trap",
        "valid": "distinct|tie|component_trap",
        "doc": (
            "distinct splits the least-frequent color into several objects; "
            "tie makes count ties observable; component_trap makes total count "
            "disagree with largest-component size"
        ),
    },
}

# Every Cartesian product of the four declared axes is supported.  The override
# checker may falsify this explicit claim.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: tuple[dict[str, object], ...] = ()
LAWFUL_DEGENERATE_TEXTURES: tuple[str, ...] = ()

SCHEDULE_PROFILES = (0, 1, 2)
CANONICAL_SHAPES = (
    (10, 12, 3),
    (11, 13, 3),
    (10, 11, 2),
    (9, 14, 2),
    (10, 12, 2),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> int:
    """Three consecutive sample indexes cover every semantic profile."""
    del seed, difficulty
    return int(sample_index) % len(SCHEDULE_PROFILES)


def _scheduled_profile(seed: int, sample_index: int) -> str:
    return PROFILES[schedule_profile(seed, sample_index)]


def _scheduled_shape(
    seed: int, sample_index: int, difficulty=None
) -> tuple[int, int, int]:
    """Cycle through canonical profiles with a visible difficulty-band offset."""
    band_offset = {"easy": 0, "medium": 1, "hard": 2}.get(difficulty, 0)
    index = (int(seed) + int(sample_index) + band_offset) % len(CANONICAL_SHAPES)
    return CANONICAL_SHAPES[index]


def _profile_counts(profile: str, n_colors: int) -> list[int]:
    """Observable count multisets sized to match the canonical 4..12-cell range."""
    if profile == "distinct":
        table = {
            2: [10, 6],
            3: [12, 8, 5],
            4: [12, 9, 6, 4],
            5: [13, 10, 8, 6, 4],
        }
    elif profile == "tie":
        table = {
            2: [8, 8],
            3: [10, 7, 7],
            4: [11, 8, 8, 5],
            5: [12, 9, 9, 6, 4],
        }
    elif profile == "component_trap":
        table = {
            2: [10, 7],
            3: [12, 8, 5],
            4: [12, 9, 6, 4],
            5: [13, 10, 8, 6, 4],
        }
    else:
        raise ValueError(f"unknown profile {profile!r}")
    return list(table[n_colors])


def _choose_rank_palette(rng, n_colors: int, profile: str) -> list[int]:
    """Return colors aligned with the count table's descending-rank positions."""
    for _ in range(200):
        colors = rng.sample(range(1, 10), n_colors)
        if profile == "tie":
            if n_colors == 2:
                # Equal counts make the true row ascending, which refutes the
                # descending-color shortcut.
                colors = sorted(colors)
            else:
                # Positions 1 and 2 are tied. Store them in the true ascending
                # order; placement later forces first-seen order to oppose it.
                colors[1:3] = sorted(colors[1:3])
            truth = _ranked_colors(Counter(dict(zip(colors, _profile_counts(profile, n_colors)))))
            if truth != sorted(colors, reverse=True):
                return colors
            continue

        # Distinct-count profiles align this list exactly with the true rank.
        # For two colors choose descending numeric order so color-ascending is
        # certainly wrong; for larger palettes reject both monotone orders.
        if n_colors == 2:
            colors = sorted(colors, reverse=True)
            return colors
        if colors != sorted(colors) and colors != sorted(colors, reverse=True):
            return colors
    raise ValueError("could not choose a shortcut-refuting palette")


def _split_sizes(total: int, parts: int) -> list[int]:
    """Positive, near-balanced component sizes summing to total."""
    if not (1 <= parts <= total):
        raise ValueError(f"cannot split {total} cells into {parts} positive parts")
    base, extra = divmod(total, parts)
    return [base + (1 if index < extra else 0) for index in range(parts)]


def _component_plan(profile: str, counts: list[int]) -> list[list[int]]:
    plans = [[count] for count in counts]
    if profile == "distinct":
        # The least-frequent color has the MOST objects, so ranking objects
        # rather than cells puts it first and is visibly wrong.
        plans[-1] = _split_sizes(counts[-1], min(3, counts[-1]))
    elif profile == "component_trap":
        # Split the true winner so each component is smaller than the runner-up
        # component. The count tables guarantee this inequality.
        plans[0] = _split_sizes(counts[0], 2)
    return plans


def _neighbors4(cell: tuple[int, int]) -> tuple[tuple[int, int], ...]:
    r, c = cell
    return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))


def _grow_component(
    rng,
    h: int,
    w: int,
    occupied: set[tuple[int, int]],
    size: int,
    *,
    forbidden_adjacent: set[tuple[int, int]],
) -> set[tuple[int, int]] | None:
    """Grow one connected component without overlapping existing content.

    Different colors may touch, as in canonical examples.  Only earlier
    components of the SAME color are supplied through ``forbidden_adjacent``;
    keeping one blank orthogonal gap between them makes component counts exact.
    """
    legal_starts = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if (r, c) not in occupied
        and not any(nb in forbidden_adjacent for nb in _neighbors4((r, c)))
    ]
    rng.shuffle(legal_starts)
    for start in legal_starts[:80]:
        cells = {start}
        frontier = [start]
        while frontier and len(cells) < size:
            source = frontier[rng.randrange(len(frontier))]
            candidates = list(_neighbors4(source))
            rng.shuffle(candidates)
            grew = False
            for nr, nc in candidates:
                candidate = (nr, nc)
                if not (0 <= nr < h and 0 <= nc < w):
                    continue
                if candidate in occupied or candidate in cells:
                    continue
                if any(nb in forbidden_adjacent for nb in _neighbors4(candidate)):
                    continue
                cells.add(candidate)
                frontier.append(candidate)
                grew = True
                if len(cells) == size:
                    break
            if not grew:
                frontier.remove(source)
        if len(cells) == size:
            return cells
    return None


def _paint_scene(
    h: int,
    w: int,
    colors: list[int],
    component_plan: list[list[int]],
    rng,
) -> list[list[int]] | None:
    grid = full_grid(h, w, 0)
    occupied: set[tuple[int, int]] = set()

    # Randomize the color placement order independently of frequency rank so
    # row-major first occurrence cannot become a hidden synonym for the answer.
    placement_order = list(range(len(colors)))
    rng.shuffle(placement_order)
    for color_index in placement_order:
        color = colors[color_index]
        same_color: set[tuple[int, int]] = set()
        for size in component_plan[color_index]:
            component = _grow_component(
                rng,
                h,
                w,
                occupied,
                size,
                forbidden_adjacent=same_color,
            )
            if component is None:
                return None
            for r, c in component:
                grid[r][c] = color
            occupied |= component
            same_color |= component
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override axis/axes: {', '.join(unknown)}")

    effective = dict(overrides)
    default_h, default_w, default_n_colors = _scheduled_shape(
        seed, sample_index, difficulty
    )
    effective.setdefault("grid_h", default_h)
    effective.setdefault("grid_w", default_w)
    effective.setdefault("n_colors", default_n_colors)
    effective.setdefault("profile", _scheduled_profile(seed, sample_index))
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=effective,
    )

    h = ctx.draw_int_diff("grid_h", 7, 16)
    w = ctx.draw_int_diff("grid_w", 8, 18)
    n_colors = ctx.draw_int_diff("n_colors", 2, 5)
    profile = ctx.draw_choice("profile", PROFILES)

    counts = _profile_counts(profile, n_colors)
    colors = _choose_rank_palette(ctx.draw_rng("palette"), n_colors, profile)
    plan = _component_plan(profile, counts)
    layout_rng = ctx.draw_rng("layout")

    for _attempt in range(240):
        grid = _paint_scene(h, w, colors, plan, layout_rng)
        if grid is None:
            continue
        obs = semantic_observables(grid)
        if obs.get("errors") or obs.get("profile") != profile:
            continue

        truth = obs["rule_output"]
        # Every ordinary profile must visibly defeat the fixed-value and
        # first-seen shortcuts; specialized profiles have stronger obligations.
        if profile == "distinct":
            if truth == _colors_ascending(grid):
                continue
            if truth == _first_seen(grid):
                continue
            if truth == _component_count(grid):
                continue
        elif profile == "tie":
            if truth == _tie_first_seen(grid):
                continue
            if truth == _tie_descending_color(grid):
                continue
            if truth == _colors_descending(grid):
                continue
        else:
            if truth == _largest_component(grid):
                continue

        errors = self_check(grid, difficulty=difficulty)
        if errors:
            raise AssertionError("generator produced invalid lesson: " + "; ".join(errors))
        return grid
    raise ValueError(
        f"could not realize profile={profile!r}, n_colors={n_colors}, grid={h}x{w}"
    )


def _normalize_grid(grid: Any) -> tuple[list[list[int]] | None, list[str]]:
    if not isinstance(grid, list) or not grid:
        return None, ["grid must be a nonempty list of rows"]
    if not all(isinstance(row, list) and row for row in grid):
        return None, ["every row must be a nonempty list"]
    width = len(grid[0])
    if any(len(row) != width for row in grid):
        return None, ["grid is ragged"]
    normalized: list[list[int]] = []
    for row in grid:
        normalized_row: list[int] = []
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not (0 <= value <= 9):
                return None, [f"cell value {value!r} is not an ARC color 0..9"]
            normalized_row.append(value)
        normalized.append(normalized_row)
    return normalized, []


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    h = len(grid)
    w = len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    found: list[list[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        q = deque([start])
        cells = [start]
        while q:
            cell = q.popleft()
            for nr, nc in _neighbors4(cell):
                candidate = (nr, nc)
                if candidate in remaining:
                    remaining.remove(candidate)
                    q.append(candidate)
                    cells.append(candidate)
        found.append(cells)
    return found


def _ranked_colors(counts: Counter[int]) -> list[int]:
    return sorted(counts, key=lambda color: (-counts[color], color))


def _infer_profile(
    counts: Counter[int],
    ranked: list[int],
    largest_components: dict[int, int],
    component_counts: dict[int, int],
) -> str | None:
    values = list(counts.values())
    if len(set(values)) < len(values):
        return "tie"
    if len(ranked) >= 2:
        top, runner_up = ranked[:2]
        if (
            component_counts[top] >= 2
            and largest_components[top] < largest_components[runner_up]
        ):
            return "component_trap"
    return "distinct"


def semantic_observables(grid: Any) -> dict[str, Any]:
    normalized, errors = _normalize_grid(grid)
    if errors:
        return {"errors": errors}
    assert normalized is not None
    h = len(normalized)
    w = len(normalized[0])
    counts = Counter(value for row in normalized for value in row if value != 0)
    if not counts:
        return {"errors": ["grid has no nonzero colors"], "grid_h": h, "grid_w": w}

    colors = sorted(counts)
    ranked = _ranked_colors(counts)
    first_seen: list[int] = []
    for row in normalized:
        for value in row:
            if value != 0 and value not in first_seen:
                first_seen.append(value)

    parts = {color: _components(normalized, color) for color in colors}
    component_counts = {color: len(items) for color, items in parts.items()}
    component_sizes = {
        color: sorted((len(item) for item in items), reverse=True)
        for color, items in parts.items()
    }
    largest_components = {
        color: sizes[0] if sizes else 0 for color, sizes in component_sizes.items()
    }
    profile = _infer_profile(counts, ranked, largest_components, component_counts)
    background_count = sum(value == 0 for row in normalized for value in row)
    return {
        "errors": [],
        "grid": normalized,
        "grid_h": h,
        "grid_w": w,
        "n_colors": len(colors),
        "colors": colors,
        "counts": dict(counts),
        "ranked_colors": ranked,
        "first_seen_colors": first_seen,
        "component_counts": component_counts,
        "component_sizes": component_sizes,
        "largest_components": largest_components,
        "profile": profile,
        "background_count": background_count,
        "rule_output": [ranked],
    }


def self_check(grid, *, difficulty=None, meta=None):
    """Validate the sparse frequency-ranking teaching grammar."""
    del difficulty, meta
    obs = semantic_observables(grid)
    errors = list(obs.get("errors", []))
    if errors:
        return errors

    h = obs["grid_h"]
    w = obs["grid_w"]
    if not (7 <= h <= 16 and 8 <= w <= 18):
        errors.append(f"grid dimensions {h}x{w} outside 7..16 by 8..18")
    if not (2 <= obs["n_colors"] <= 5):
        errors.append(f"need 2..5 nonzero colors, got {obs['n_colors']}")

    count_values = list(obs["counts"].values())
    too_small = sorted(color for color, count in obs["counts"].items() if count < 3)
    too_large = sorted(color for color, count in obs["counts"].items() if count > 16)
    if too_small:
        errors.append(f"nonzero colors have fewer than three cells: {too_small}")
    if too_large:
        errors.append(f"nonzero colors exceed the 16-cell grammar ceiling: {too_large}")
    if obs["background_count"] < max(8, (h * w) // 5):
        errors.append("background 0 does not occupy the required sparse margin")
    if max(obs["largest_components"].values(), default=0) < 3:
        errors.append("no color has a canonical-scale connected component")
    if len(obs["rule_output"]) != 1 or len(obs["rule_output"][0]) != obs["n_colors"]:
        errors.append("frequency ranking does not yield one color per nonzero input color")
    if sum(count_values) + obs["background_count"] != h * w:
        errors.append("color counts do not cover the rectangular grid")
    if obs["profile"] not in PROFILES:
        errors.append("grid does not realize a declared observable profile")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Accepted scenes match the canonical sparse global-count manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, Any]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("cannot observe malformed grid: " + "; ".join(obs["errors"]))
    return {
        "grid_h": obs["grid_h"],
        "grid_w": obs["grid_w"],
        "n_colors": obs["n_colors"],
        "profile": obs["profile"],
    }


def rule_mirror(grid: Any) -> list[list[int]]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    return [list(obs["ranked_colors"])]


def _colors_ascending(grid: Any) -> list[list[int]]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    return [sorted(obs["colors"])]


def _colors_descending(grid: Any) -> list[list[int]]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    return [sorted(obs["colors"], reverse=True)]


def _first_seen(grid: Any) -> list[list[int]]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    return [list(obs["first_seen_colors"])]


def _largest_component(grid: Any) -> list[list[int]]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    ordered = sorted(
        obs["colors"],
        key=lambda color: (-obs["largest_components"][color], color),
    )
    return [ordered]


def _component_count(grid: Any) -> list[list[int]]:
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    ordered = sorted(
        obs["colors"],
        key=lambda color: (-obs["component_counts"][color], color),
    )
    return [ordered]


def _most_frequent_only(grid: Any) -> list[list[int]]:
    return [[rule_mirror(grid)[0][0]]]


def _tie_first_seen(grid: Any) -> list[list[int]]:
    """Wrong rule: descending counts, preserving row-major order on ties."""
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    first_index = {color: index for index, color in enumerate(obs["first_seen_colors"])}
    ordered = sorted(
        obs["colors"],
        key=lambda color: (-obs["counts"][color], first_index[color]),
    )
    return [ordered]


def _tie_descending_color(grid: Any) -> list[list[int]]:
    """Wrong rule: descending counts and descending numeric color on ties."""
    obs = semantic_observables(grid)
    if obs.get("errors"):
        raise ValueError("; ".join(obs["errors"]))
    ordered = sorted(obs["colors"], key=lambda color: (-obs["counts"][color], -color))
    return [ordered]


SEMANTIC_RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "colors_ascending": _colors_ascending,
    "colors_descending": _colors_descending,
    "first_seen": _first_seen,
    "largest_component": _largest_component,
    "component_count": _component_count,
    "most_frequent_only": _most_frequent_only,
    "tie_first_seen": _tie_first_seen,
    "tie_descending_color": _tie_descending_color,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _rival_differs(grid: Any, name: str) -> bool:
    return SEMANTIC_RIVALS[name](grid) != rule_mirror(grid)


SEMANTIC_WITNESSES = {
    "frequency_refutes_color_ascending": lambda grid: _rival_differs(
        grid, "colors_ascending"
    ),
    "tie_refutes_color_descending": lambda grid: (
        semantic_observables(grid).get("profile") == "tie"
        and _rival_differs(grid, "colors_descending")
    ),
    "placement_refutes_first_seen": lambda grid: _rival_differs(grid, "first_seen"),
    "global_total_refutes_largest_component": lambda grid: (
        semantic_observables(grid).get("profile") == "component_trap"
        and _rival_differs(grid, "largest_component")
    ),
    "cell_count_refutes_object_count": lambda grid: (
        semantic_observables(grid).get("profile") == "distinct"
        and _rival_differs(grid, "component_count")
    ),
    "all_colors_refute_top_only": lambda grid: _rival_differs(
        grid, "most_frequent_only"
    ),
    "ascending_tie_refutes_first_seen": lambda grid: (
        semantic_observables(grid).get("profile") == "tie"
        and _rival_differs(grid, "tie_first_seen")
    ),
    "ascending_tie_refutes_descending_tie": lambda grid: (
        semantic_observables(grid).get("profile") == "tie"
        and _rival_differs(grid, "tie_descending_color")
    ),
}

WITNESS_RIVALS = {
    "frequency_refutes_color_ascending": ["colors_ascending"],
    "tie_refutes_color_descending": ["colors_descending"],
    "placement_refutes_first_seen": ["first_seen"],
    "global_total_refutes_largest_component": ["largest_component"],
    "cell_count_refutes_object_count": ["component_count"],
    "all_colors_refute_top_only": ["most_frequent_only"],
    "ascending_tie_refutes_first_seen": ["tie_first_seen"],
    "ascending_tie_refutes_descending_tie": ["tie_descending_color"],
}

# Canonical examples contain no equal-frequency colors, so both wrong tie rules
# fit every canonical pair. Scheduled tie scenes are necessary counterexamples.
CANONICAL_SHORTCUTS = {
    "tie_first_seen": _tie_first_seen,
    "tie_descending_color": _tie_descending_color,
}


def lesson_identifiable(demos, query) -> list[str]:
    reasons: list[str] = []
    if not isinstance(demos, list) or not demos:
        return ["lesson has no demonstrations"]
    if not isinstance(query, dict) or "input" not in query:
        return ["query is missing an input grid"]

    for index, demo in enumerate(demos):
        if not isinstance(demo, dict) or "input" not in demo or "output" not in demo:
            reasons.append(f"demo {index} is missing input/output")
            continue
        check = self_check(demo["input"])
        if check:
            reasons.append(f"demo {index} is outside the teaching grammar: {check}")
            continue
        if demo["output"] != rule_mirror(demo["input"]):
            reasons.append(f"demo {index} output disagrees with global frequency ranking")

    query_check = self_check(query["input"])
    if query_check:
        reasons.append(f"query is outside the teaching grammar: {query_check}")
    if reasons:
        return reasons

    query_truth = rule_mirror(query["input"])
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(demo["input"]) == demo["output"] for demo in demos):
            if competitor(query["input"]) != query_truth:
                reasons.append(
                    f"demos remain compatible with competitor {name!r}, "
                    "which changes the query answer"
                )
            else:
                reasons.append(f"competitor {name!r} survives every demo and query")
    return reasons
