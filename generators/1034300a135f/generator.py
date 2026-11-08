"""Semantic generator for ARC task 1034300a135f.

Every non-background input cell is a marker.  Markers are stably sorted by
their minimum distance to a canvas edge; their colors then become output rings
from outside to inside.  The canonical ``mode`` ignores zero, so backgrounds
must be nonzero while zero remains a lawful marker color.
"""
from __future__ import annotations

from collections import Counter, defaultdict

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "1034300a135f"
TASK_ID = "1034300a135f"
VERSION = "3.1.0"
RULE_HASH = "4e51401fbef6"
SUMMARY = "Stable-sort marker cells by minimum edge distance and paint their colors as concentric output rings from outside inward."
INVARIANTS = [
    "the Racket mode ignores zero, so the unique modal nonzero color is the background",
    "every cell unequal to that background is an independent marker, including color zero",
    "markers are scanned row-major and stably sorted by minimum distance to any edge",
    "the d-th output ring uses the d-th sorted marker color while d is below marker count",
    "positions deeper than the marker count retain the background",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
GENERAL_PROFILES = (
    "full_odd_square",
    "full_even_square",
    "full_wide_rectangle",
    "full_tall_rectangle",
    "partial_center_background",
    "sparse_distance_jumps",
    "zero_outer_ring",
    "zero_inner_ring",
    "tied_distance_row_major",
    "repeated_color_layers",
    "teaching_combined",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
EXAMPLES_NEEDED = 3
SCHEDULE_PROFILES = SCENE_PROFILES
_TEACHING_PROFILE = "teaching_combined"
_SCHEDULE_VARIETY_PROFILES = tuple(
    profile for profile in SCENE_PROFILES if profile != _TEACHING_PROFILE
)
LESSON_SCHEDULE_PERIOD = 2 * len(_SCHEDULE_VARIETY_PROFILES)
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "rotation-safe teaching counterexamples alternating with exact-public and generalized ring-order lessons",
        "valid": "public_1|public_2|public_3|public_4|full_odd_square|full_even_square|full_wide_rectangle|full_tall_rectangle|partial_center_background|sparse_distance_jumps|zero_outer_ring|zero_inner_ring|tied_distance_row_major|repeated_color_layers|teaching_combined",
    }
}

_PUBLIC_ROWS = (
    "777777777/777477777/777777377/777777777/777787777/777717777/777777777/777777777/777777707",
    "5777777/7777777/7777777/7872977/7777777/7777777/7777777",
    "77777777777/77777707777/77777717777/77777777777/77777777777/77777577777/77777977777/77777677777/77777777777/77777777777/78777777777",
    "7777777777770/7777777777777/7777777777777/7777777717777/7777777787777/7777757777777/7777772777777/7777777777777/7777777777777/7777777777777/7777737777777/7477777777777/7777777777777",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _validate_request(seed, sample_index, difficulty):
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    if type(sample_index) is not int:
        raise TypeError("sample_index must be an integer (not bool)")
    if sample_index < 0:
        raise ValueError("sample_index must be nonnegative")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed, sample_index, difficulty=None):
    """Return the declared rotation-safe profile for one sample index.

    Every four-pair lesson contains two ``teaching_combined`` instances.  Thus
    every three-demo rotation retains at least one example that simultaneously
    falsifies all declared marker-order shortcuts.  Odd slots cycle through
    every other profile so the schedule still covers the full grammar.
    """
    _validate_request(seed, sample_index, difficulty)
    if sample_index % 2 == 0:
        return _TEACHING_PROFILE
    return _SCHEDULE_VARIETY_PROFILES[
        (sample_index // 2) % len(_SCHEDULE_VARIETY_PROFILES)
    ]


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 5 <= len(grid) <= 30 or not 5 <= width <= 30:
        return ["grid dimensions must be within 5..30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _edge_distance(row, col, height, width):
    return min(row, col, height - 1 - row, width - 1 - col)


def _extract_facts(grid):
    height, width = len(grid), len(grid[0])
    nonzero_counts = Counter(value for row in grid for value in row if value != 0)
    if not nonzero_counts:
        raise ValueError("Racket mode requires at least one nonzero color")
    maximum = max(nonzero_counts.values())
    modes = [color for color, count in nonzero_counts.items() if count == maximum]
    if len(modes) != 1:
        raise ValueError("nonzero background mode must be unique")
    background = modes[0]
    markers = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color != background:
                markers.append({
                    "row": row,
                    "col": col,
                    "color": color,
                    "distance": _edge_distance(row, col, height, width),
                })
    ordered = sorted(markers, key=lambda marker: marker["distance"])
    sequence = [marker["color"] for marker in ordered]
    count = len(sequence)
    output = [
        [
            sequence[distance] if distance < count else background
            for col in range(width)
            for distance in [_edge_distance(row, col, height, width)]
        ]
        for row in range(height)
    ]
    return {
        "height": height,
        "width": width,
        "capacity": (min(height, width) + 1) // 2,
        "background": background,
        "markers": markers,
        "ordered_markers": ordered,
        "sequence": sequence,
        "distances": [marker["distance"] for marker in ordered],
        "output": output,
        "changed": sum(before != after for old, new in zip(grid, output) for before, after in zip(old, new)),
    }


def _is_teaching_signature(facts):
    """Recognize the deliberately multi-witness lesson profile."""
    height, width = facts["height"], facts["width"]
    capacity = facts["capacity"]
    colors = facts["sequence"]
    distances = facts["distances"]
    count = len(colors)
    expected_distances = [0, 2, 2] + list(range(3, count))
    return (
        height == width
        and height % 2 == 1
        and 3 <= count <= 8
        and count < capacity
        and distances == expected_distances
        and colors[0] == colors[1]
        and colors[0] != 0
        and colors[2] == 0
        and colors.count(0) == 1
        and len(set(colors)) == count - 1
        and colors != sorted(colors)
    )


def _general_signature(facts):
    height, width = facts["height"], facts["width"]
    capacity = facts["capacity"]
    colors = facts["sequence"]
    distances = facts["distances"]
    count = len(colors)
    if not 3 <= count <= 8 or count > capacity:
        return None
    if _is_teaching_signature(facts):
        return _TEACHING_PROFILE
    if len(set(colors)) < count:
        if (
            0 not in colors
            and len(set(colors)) == count - 1
            and distances == list(range(count))
            and height == width
            and height % 2 == 1
            and count == capacity
        ):
            return "repeated_color_layers"
        return None
    if len(set(distances)) < count:
        if 0 not in colors and height == width and height % 2 == 1:
            return "tied_distance_row_major"
        return None
    if 0 in colors:
        if colors.count(0) != 1 or distances != list(range(count)) or height != width or height % 2 != 1 or count != capacity:
            return None
        if colors[0] == 0:
            return "zero_outer_ring"
        if colors[-1] == 0:
            return "zero_inner_ring"
        return None
    if height == width and distances == list(range(count)) and count == capacity:
        return "full_odd_square" if height % 2 else "full_even_square"
    if width > height and distances == list(range(count)) and count == capacity:
        return "full_wide_rectangle"
    if height > width and distances == list(range(count)) and count == capacity:
        return "full_tall_rectangle"
    if height == width and height % 2 == 1 and distances == list(range(count)) and count <= capacity - 2:
        return "partial_center_background"
    if height == width and height % 2 == 1 and len(set(distances)) == count and distances != list(range(count)) and max(distances) < capacity:
        return "sparse_distance_jumps"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None}
    try:
        facts = _extract_facts(grid)
    except (TypeError, ValueError) as exc:
        return {"errors": [str(exc)], "scene_profile": None}
    if facts["background"] == 0:
        errors.append("background cannot be zero because canonical mode excludes zero")
    if not 3 <= len(facts["markers"]) <= 8:
        errors.append("expected 3..8 marker cells")
    if len(facts["markers"]) > facts["capacity"]:
        errors.append("marker count exceeds the number of observable output rings")
    if facts["changed"] <= 0:
        errors.append("canonical rule must visibly change the input")
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid))) or _general_signature(facts)
    if profile is None:
        errors.append("scene does not match a declared semantic profile")
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": facts["output"]}


def rule_mirror(grid):
    errors = _valid_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    return _extract_facts(grid)["output"]


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def strict_canonical_like(grid):
    """Semantic-gate hook: the declared grammar is the strict manifold."""
    return self_check(grid)


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _paint_ranked(facts, sequence, *, extend_last=False):
    background = facts["background"]
    height, width = facts["height"], facts["width"]
    return [
        [
            (
                sequence[distance]
                if distance < len(sequence)
                else sequence[-1]
                if extend_last and sequence
                else background
            )
            for col in range(width)
            for distance in [_edge_distance(row, col, height, width)]
        ]
        for row in range(height)
    ]


def _rival_reverse_equal_distance_ties(grid):
    facts = _extract_facts(grid)
    width = facts["width"]
    ordered = sorted(
        facts["markers"],
        key=lambda marker: (
            marker["distance"],
            -(marker["row"] * width + marker["col"]),
        ),
    )
    return _paint_ranked(facts, [marker["color"] for marker in ordered])


def _rival_use_raw_edge_distance_as_ring_index(grid):
    facts = _extract_facts(grid)
    by_distance = {}
    for marker in facts["ordered_markers"]:
        by_distance.setdefault(marker["distance"], marker["color"])
    background = facts["background"]
    height, width = facts["height"], facts["width"]
    return [
        [
            by_distance.get(_edge_distance(row, col, height, width), background)
            for col in range(width)
        ]
        for row in range(height)
    ]


def _rival_extend_last_color_to_center(grid):
    facts = _extract_facts(grid)
    return _paint_ranked(facts, facts["sequence"], extend_last=True)


def _rival_ignore_zero_markers(grid):
    facts = _extract_facts(grid)
    sequence = [color for color in facts["sequence"] if color != 0]
    return _paint_ranked(facts, sequence)


def _rival_deduplicate_marker_colors(grid):
    facts = _extract_facts(grid)
    sequence = list(dict.fromkeys(facts["sequence"]))
    return _paint_ranked(facts, sequence)


def _rival_sort_marker_colors_numerically(grid):
    facts = _extract_facts(grid)
    return _paint_ranked(facts, sorted(facts["sequence"]))


SEMANTIC_RIVALS = {
    "reverse_equal_distance_ties": _rival_reverse_equal_distance_ties,
    "use_raw_edge_distance_as_ring_index": (
        _rival_use_raw_edge_distance_as_ring_index
    ),
    "extend_last_color_to_center": _rival_extend_last_color_to_center,
    "ignore_zero_markers": _rival_ignore_zero_markers,
    "deduplicate_marker_colors": _rival_deduplicate_marker_colors,
    "sort_marker_colors_numerically": _rival_sort_marker_colors_numerically,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = {
    name: SEMANTIC_RIVALS[name]
    for name in (
        "reverse_equal_distance_ties",
        "use_raw_edge_distance_as_ring_index",
        "extend_last_color_to_center",
        "deduplicate_marker_colors",
    )
}


def _lawful_facts(grid):
    analysis = _analysis(grid)
    return None if analysis["errors"] else analysis["facts"]


def _witness_equal_distance_tie(grid):
    facts = _lawful_facts(grid)
    return bool(facts and len(set(facts["distances"])) < len(facts["distances"]))


def _witness_distance_gap(grid):
    facts = _lawful_facts(grid)
    if not facts:
        return False
    unique = sorted(set(facts["distances"]))
    return unique != list(range(len(unique)))


def _witness_partial_background(grid):
    facts = _lawful_facts(grid)
    return bool(facts and len(facts["sequence"]) < facts["capacity"])


def _witness_zero_marker(grid):
    facts = _lawful_facts(grid)
    return bool(facts and 0 in facts["sequence"])


def _witness_repeated_marker_color(grid):
    facts = _lawful_facts(grid)
    return bool(facts and len(set(facts["sequence"])) < len(facts["sequence"]))


def _witness_nonmonotone_color_order(grid):
    facts = _lawful_facts(grid)
    return bool(facts and facts["sequence"] != sorted(facts["sequence"]))


SEMANTIC_WITNESSES = {
    "equal_distance_tie": _witness_equal_distance_tie,
    "distance_gap": _witness_distance_gap,
    "partial_background": _witness_partial_background,
    "zero_marker": _witness_zero_marker,
    "repeated_marker_color": _witness_repeated_marker_color,
    "nonmonotone_color_order": _witness_nonmonotone_color_order,
}
BRANCH_WITNESSES = tuple(SEMANTIC_WITNESSES)
WITNESS_RIVALS = {
    "equal_distance_tie": ["reverse_equal_distance_ties"],
    "distance_gap": ["use_raw_edge_distance_as_ring_index"],
    "partial_background": ["extend_last_color_to_center"],
    "zero_marker": ["ignore_zero_markers"],
    "repeated_marker_color": ["deduplicate_marker_colors"],
    "nonmonotone_color_order": ["sort_marker_colors_numerically"],
}


def lesson_identifiable(demos, query):
    """Name any executable rival that fits the demos but changes the query."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and output grids"]

    reasons = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} must contain input and output grids")
            continue
        errors = self_check(pair["input"])
        if errors:
            reasons.append(f"pair {index} is outside the declared grammar: {errors[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"pair {index} output disagrees with the selected rule")
    if reasons:
        return reasons

    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            if competitor(query["input"]) != query["output"]:
                reasons.append(f"rival '{name}' fits every demo but changes the query")
    return reasons


def _size_limits(difficulty):
    if difficulty == "easy":
        return 7, 9, 13
    if difficulty == "medium":
        return 10, 13, 21
    if difficulty == "hard":
        return 14, 15, 30
    return 7, 15, 24


def _pick_parity_size(rng, low, high, parity, minimum=7):
    choices = [size for size in range(max(low, minimum), high + 1) if size % 2 == parity]
    if not choices:
        raise ValueError("no legal size in requested parity band")
    return rng.choice(choices)


def _ring_cells(height, width, distance):
    return [
        (row, col)
        for row in range(height)
        for col in range(width)
        if _edge_distance(row, col, height, width) == distance
    ]


def _place_markers(grid, specs, rng):
    height, width = len(grid), len(grid[0])
    grouped = defaultdict(list)
    for distance, color in specs:
        grouped[distance].append(color)
    for distance, colors in grouped.items():
        candidates = _ring_cells(height, width, distance)
        chosen = sorted(rng.sample(candidates, len(colors)))
        for (row, col), color in zip(chosen, colors):
            grid[row][col] = color


def _general_scene(ctx, profile, rng):
    low, high, long_high = _size_limits(ctx.difficulty)
    for _ in range(100):
        if profile in {"full_even_square"}:
            height = width = _pick_parity_size(rng, low, high + 1, 0, minimum=8)
        else:
            short = _pick_parity_size(rng, low, high, 1, minimum=7)
            if profile == "full_wide_rectangle":
                height = short
                width = rng.randint(short + 2, max(short + 2, long_high))
            elif profile == "full_tall_rectangle":
                width = short
                height = rng.randint(short + 2, max(short + 2, long_high))
            else:
                height = width = short
        capacity = (min(height, width) + 1) // 2
        background = rng.randint(1, 9)
        nonzero = [color for color in range(1, 10) if color != background]

        if profile == _TEACHING_PROFILE:
            if capacity < 4:
                continue
            count = min(8, capacity - 1)
            distances = [0, 2, 2] + list(range(3, count))
        elif profile == "partial_center_background":
            if capacity < 5:
                continue
            count = rng.randint(3, capacity - 2)
            distances = list(range(count))
        elif profile == "sparse_distance_jumps":
            if capacity < 5:
                continue
            count = rng.randint(3, min(6, capacity - 1))
            middle = rng.sample(list(range(1, capacity - 1)), count - 2)
            distances = sorted([0, capacity - 1] + middle)
        elif profile == "tied_distance_row_major":
            count = rng.randint(4, min(8, capacity))
            tie_distance = rng.randint(0, count - 2)
            distances = sorted(list(range(count - 1)) + [tie_distance])
        else:
            count = capacity
            distances = list(range(count))
        if count > 8:
            continue

        if profile == _TEACHING_PROFILE:
            anchor = rng.choice(nonzero)
            middle = rng.sample(
                [color for color in nonzero if color != anchor],
                count - 3,
            )
            colors = [anchor, anchor, 0, *middle]
        elif profile in {"zero_outer_ring", "zero_inner_ring"}:
            colors = rng.sample(nonzero, count - 1)
            colors.insert(0 if profile == "zero_outer_ring" else len(colors), 0)
        elif profile == "repeated_color_layers":
            colors = rng.sample(nonzero, count - 1)
            repeat_at = rng.randint(0, count - 2)
            colors.insert(repeat_at + 1, colors[repeat_at])
        else:
            colors = rng.sample(nonzero, count)

        grid = [[background for _ in range(width)] for _ in range(height)]
        _place_markers(grid, list(zip(distances, colors)), rng)
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct {profile}")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_request(seed, sample_index, difficulty)
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    scheduled = schedule_profile(seed, sample_index, difficulty)
    if overrides.get("scene_profile") is None:
        profile = ctx.draw_choice("scene_profile", [scheduled])
    else:
        profile = ctx.draw_choice("scene_profile", SCENE_PROFILES)
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(ctx, profile, ctx.draw_rng("geometry"))
