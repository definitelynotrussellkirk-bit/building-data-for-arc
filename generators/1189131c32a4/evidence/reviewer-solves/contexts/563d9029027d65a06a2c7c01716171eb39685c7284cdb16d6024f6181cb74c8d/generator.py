"""Semantic generator for ARC task 1189131c32a4.

The input is only an encoding of color frequencies.  ``unique`` first puts
the distinct colors in numeric order; colors other than the fixed orange
background (7) are then stably sorted by increasing count and reversed.
Consequently ties use descending numeric color order.  The ranked colors
become concentric square rings, most frequent outside and least frequent at
the center.
"""
from __future__ import annotations

from collections import Counter, deque

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "1189131c32a4"
TASK_ID = "1189131c32a4"
VERSION = "3.0.0"
RULE_HASH = "cb24e3652642"
SUMMARY = "Rank every non-7 color by descending frequency, using descending numeric color order for ties, then paint concentric square rings."
INVARIANTS = [
    "7 is the fixed background and is excluded even when another color is modal",
    "zero is a lawful foreground color",
    "unique sorts colors into ascending numeric order before frequency sorting",
    "reversing the stable ascending frequency sort makes ties use descending numeric color order",
    "n colors produce a (2n-1)-square with most frequent outside and least frequent at center",
    "input component geometry has no effect on the output",
]

PUBLIC_PROFILES = tuple(f"public_{index}" for index in range(1, 5))
GENERAL_PROFILES = (
    "two_connected",
    "three_connected",
    "four_connected",
    "five_connected",
    "six_connected",
    "zero_ranked",
    "tie_two_way",
    "tie_three_way",
    "scattered_components",
    "mixed_components",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four exact-public and ten generalized frequency-ranking lessons",
        "valid": "public_1|public_2|public_3|public_4|two_connected|three_connected|four_connected|five_connected|six_connected|zero_ranked|tie_two_way|tie_three_way|scattered_components|mixed_components",
    }
}

_PUBLIC_ROWS = (
    "777777/777447/777447/677777/667777/777777",
    "777777877/777777877/755778887/755777777/777777777/777111777/777171777/777111777/777777777",
    "7777777/7888733/7878777/7888777/7777797/0077777/0077777",
    "77977222/77977272/57777777/55787777/57777077/77177007/71117700/11111770",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): profile for profile, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be non-empty"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 4 <= len(grid) <= 30 or not 4 <= width <= 30:
        return ["grid dimensions must be within 4..30"]
    if any(isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9 for row in grid for value in row):
        return ["cells must be literal ARC integers 0..9"]
    return []


def _component_count(grid, color):
    height, width = len(grid), len(grid[0])
    unseen = {(row, col) for row in range(height) for col in range(width) if grid[row][col] == color}
    components = 0
    while unseen:
        components += 1
        queue = deque([unseen.pop()])
        while queue:
            row, col = queue.popleft()
            for nr, nc in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if (nr, nc) in unseen:
                    unseen.remove((nr, nc))
                    queue.append((nr, nc))
    return components


def _extract_facts(grid):
    counts = Counter(color for row in grid for color in row if color != 7)
    colors = sorted(counts)
    if not colors:
        raise ValueError("need at least one non-7 color")
    ranked = list(reversed(sorted(colors, key=counts.__getitem__)))
    count = len(ranked)
    size = 2 * count - 1
    center = count - 1
    output = [
        [ranked[count - 1 - max(abs(row - center), abs(col - center))] for col in range(size)]
        for row in range(size)
    ]
    return {
        "colors": colors,
        "counts": dict(counts),
        "ranked": ranked,
        "components": {color: _component_count(grid, color) for color in colors},
        "output": output,
        "changed": (
            len(grid) != size
            or len(grid[0]) != size
            or any(grid[row][col] != output[row][col] for row in range(size) for col in range(size))
        ),
    }


def _tie_groups(facts):
    groups = Counter(facts["counts"].values())
    return sorted(size for size in groups.values() if size > 1)


def _general_signature(facts):
    colors = facts["colors"]
    count = len(colors)
    components = list(facts["components"].values())
    ties = _tie_groups(facts)
    contains_zero = 0 in colors
    if contains_zero:
        if count == 4 and not ties and all(value == 1 for value in components):
            return "zero_ranked"
        return None
    if count == 4 and ties == [2] and all(value == 1 for value in components):
        return "tie_two_way"
    if count == 4 and ties == [3] and all(value == 1 for value in components):
        return "tie_three_way"
    if ties:
        return None
    if count == 4 and all(value >= 2 for value in components):
        return "scattered_components"
    if count == 4 and any(value == 1 for value in components) and any(value >= 2 for value in components):
        return "mixed_components"
    if all(value == 1 for value in components) and 2 <= count <= 6:
        return f"{('two', 'three', 'four', 'five', 'six')[count - 2]}_connected"
    return None


def _analysis(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "scene_profile": None}
    try:
        facts = _extract_facts(grid)
    except ValueError as exc:
        return {"errors": [str(exc)], "scene_profile": None}
    if not 2 <= len(facts["colors"]) <= 6:
        errors.append("expected 2..6 distinct non-7 colors")
    if 7 not in {value for row in grid for value in row}:
        errors.append("fixed background color 7 must be present")
    if Counter(value for row in grid for value in row).most_common(1)[0][0] != 7:
        errors.append("fixed background color 7 must be the modal input color")
    if not facts["changed"]:
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


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _size_range(difficulty):
    if difficulty == "easy":
        return 7, 10
    if difficulty == "medium":
        return 8, 12
    if difficulty == "hard":
        return 10, 14
    return 7, 12


def _connected_cells(row, width, count, rng):
    """Place one compact component on its own row."""
    start = rng.randint(0, width - count)
    return {(row, col) for col in range(start, start + count)}


def _paint_connected(grid, colors, counts, rng):
    row0 = rng.randint(0, len(grid) - (2 * len(colors) - 1))
    for index, (color, count) in enumerate(zip(colors, counts)):
        for row, col in _connected_cells(row0 + 2 * index, len(grid[0]), count, rng):
            grid[row][col] = color


def _isolated_candidates(height, width, minimum_row=0):
    return [(row, col) for row in range(minimum_row, height, 2) for col in range(0, width, 2)]


def _paint_scattered(grid, colors, counts, rng, minimum_row=0):
    candidates = _isolated_candidates(len(grid), len(grid[0]), minimum_row)
    rng.shuffle(candidates)
    if sum(counts) > len(candidates):
        raise AssertionError("not enough isolated cells")
    offset = 0
    for color, count in zip(colors, counts):
        for row, col in candidates[offset:offset + count]:
            grid[row][col] = color
        offset += count


def _general_scene(ctx, profile, rng):
    low, high = _size_range(ctx.difficulty)
    if profile.endswith("_connected"):
        n = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6}[profile.split("_")[0]]
        minimum_height, minimum_width = 2 * n - 1, n + 4
    elif profile in {"zero_ranked", "tie_two_way", "tie_three_way"}:
        minimum_height, minimum_width = 7, 9
    elif profile == "mixed_components":
        minimum_height, minimum_width = 9, 8
    else:
        minimum_height, minimum_width = 7, 8
    height = rng.randint(max(low, minimum_height), max(high, minimum_height))
    width = rng.randint(max(low, minimum_width), max(high, minimum_width))
    palette = rng.sample([1, 2, 3, 4, 5, 6, 8, 9], 6)
    grid = [[7 for _ in range(width)] for _ in range(height)]

    if profile.endswith("_connected"):
        n = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6}[profile.split("_")[0]]
        colors = palette[:n]
        offset = rng.randrange(3)
        counts = list(range(1 + offset, n + 1 + offset))
        rng.shuffle(counts)
        _paint_connected(grid, colors, counts, rng)
    elif profile == "zero_ranked":
        colors = palette[:3] + [0]
        rng.shuffle(colors)
        counts = [2, 3, 5, 7]
        rng.shuffle(counts)
        _paint_connected(grid, colors, counts, rng)
    elif profile == "tie_two_way":
        colors = palette[:4]
        counts = [2, 2, 4, 6]
        rng.shuffle(counts)
        _paint_connected(grid, colors, counts, rng)
    elif profile == "tie_three_way":
        colors = palette[:4]
        counts = [3, 3, 3, 6]
        rng.shuffle(counts)
        _paint_connected(grid, colors, counts, rng)
    elif profile == "scattered_components":
        colors = palette[:4]
        counts = [2, 3, 4, 5]
        rng.shuffle(counts)
        _paint_scattered(grid, colors, counts, rng)
    elif profile == "mixed_components":
        colors = palette[:4]
        counts = [2, 3, 4, 5]
        rng.shuffle(counts)
        # Two private connected bands above; isolated cells begin below a blank separator.
        split = 2
        top_height = 2 * split - 1
        top = [[7 for _ in range(width)] for _ in range(top_height)]
        _paint_connected(top, colors[:split], counts[:split], rng)
        for row in range(top_height):
            grid[row] = top[row]
        _paint_scattered(grid, colors[split:], counts[split:], rng, minimum_row=top_height + 1)
    else:
        raise ValueError(f"unknown scene_profile: {profile!r}")

    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != profile:
        raise AssertionError((profile, analysis))
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = sorted(set(overrides) - {"scene_profile"})
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    ctx = gen_ctx(seed=seed, sample_index=sample_index, version=VERSION, task_id=TASK_ID, difficulty=difficulty, overrides=overrides)
    profile = ctx.draw_choice("scene_profile", PUBLIC_PROFILES + GENERAL_PROFILES * 4)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        return [row[:] for row in _PUBLIC_INPUTS[profile]]
    return _general_scene(ctx, profile, ctx.draw_rng("geometry"))
