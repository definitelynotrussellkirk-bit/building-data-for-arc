"""Semantic generator for ARC task 78645c33b002 (source eb5a1d5d).

Read the ordered colors of nested, filled, axis-aligned rectangles from the
outside inward.  Normalize that hierarchy to a compact odd square containing
one one-cell-thick concentric ring per input layer and the innermost color at
the center.
"""
from __future__ import annotations

from puzzle_generators.base import gen_ctx

GENERATOR_ID = "78645c33b002"
TASK_ID = "78645c33b002"
VERSION = "3.1.0"
# Preserve the established per-profile draw streams while changing only the
# default lesson schedule. Explicit profile replays therefore remain stable.
DRAW_VERSION = "3.0.0"
RULE_HASH = "d565393b63e9"
EXAMPLES_NEEDED = 3
LESSON_SCHEDULE_PERIOD = 80
SUMMARY = "Compress nested filled rectangles to one-cell concentric rings in their outside-to-inside color order."
INVARIANTS = [
    "the input is a rectangular ARC-color grid containing two through six nested filled rectangles",
    "each rectangle is strictly inset on all four sides of its parent and each exposed ring is uniform",
    "adjacent layers have different colors, though a non-adjacent color may repeat",
    "the innermost rectangle is uniform and at least 3x3",
    "the output side is 2K-1 for K input layers",
    "the output has one one-cell-thick concentric ring per ordered input color and the innermost color at its center",
]

PUBLIC_PROFILES = ("public_1", "public_2", "public_3", "public_4")
GENERAL_PROFILES = (
    "two_layers",
    "six_layers",
    "repeated_colors",
    "square_centered",
    "rectangular_centered",
    "thin_offcenter",
    "thick_offcenter",
    "tall_offcenter",
    "wide_offcenter",
    "square_offcenter",
)
SCENE_PROFILES = PUBLIC_PROFILES + GENERAL_PROFILES
HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()
AXES = {
    "scene_profile": {
        "type": "str",
        "default": "four linked official hierarchies and ten layer-count/thickness/asymmetry contrasts",
        "valid": "|".join(SCENE_PROFILES),
    }
}

_PUBLIC_ROWS = (
    "5555555555555555555555555/5555555555555555555555555/5555555555555555555555555/5555666666666666666555555/5555666666666666666555555/5555666666666666666555555/5555666666666666666555555/5555666666666666666555555/5555666666666666666555555/5555666666666666666555555/5555666666666666666555555/5555666666666666666555555/5555666666666666666555555/5555666666666666666555555/5555666666666666666555555/5555666666666666666555555/5555555555555555555555555/5555555555555555555555555/5555555555555555555555555/5555555555555555555555555/5555555555555555555555555/5555555555555555555555555",
    "888888888888888888888888888/888888888888888888888888888/888333333333333333333888888/888333333333333333333888888/888333333333333333333888888/888333333333333333333888888/888333333333333333333888888/888333333333333333333888888/888333333333333333333888888/888333222222333333333888888/888333222222333333333888888/888333222222333333333888888/888333222222333333333888888/888333222222333333333888888/888333222222333333333888888/888333333333333333333888888/888333333333333333333888888/888333333333333333333888888/888888888888888888888888888/888888888888888888888888888/888888888888888888888888888/888888888888888888888888888/888888888888888888888888888",
    "3333333333333333333333/3333333333333333333333/3333333333333333333333/3338888888888888833333/3338888888888888833333/3338822222222288833333/3338822211111288833333/3338822211111288833333/3338822211111288833333/3338822222222288833333/3338822222222288833333/3338822222222288833333/3338822222222288833333/3338822222222288833333/3338888888888888833333/3338888888888888833333/3338888888888888833333/3333333333333333333333/3333333333333333333333/3333333333333333333333/3333333333333333333333",
    "222222222222222222222222222/222222222222222222222222222/222222222222222222222222222/222222222222222222222222222/222222222222222222222222222/222111111111111111111112222/222111111111111111111112222/222111333333333333331112222/222111333333333333331112222/222111333333333333331112222/222111333888888888331112222/222111333888222288331112222/222111333888222288331112222/222111333888222288331112222/222111333888222288331112222/222111333888888888331112222/222111333888888888331112222/222111333333333333331112222/222111333333333333331112222/222111333333333333331112222/222111333333333333331112222/222111111111111111111112222/222111111111111111111112222/222111111111111111111112222/222222222222222222222222222/222222222222222222222222222",
)


def _decode(text):
    return [[int(value) for value in row] for row in text.split("/")]


_PUBLIC_INPUTS = {name: _decode(text) for name, text in zip(PUBLIC_PROFILES, _PUBLIC_ROWS)}
_PUBLIC_SIGNATURES = {tuple(map(tuple, grid)): name for name, grid in _PUBLIC_INPUTS.items()}


def _valid_grid(grid):
    if not isinstance(grid, (list, tuple)) or not 12 <= len(grid) <= 30:
        return ["input must contain twelve through thirty rows"]
    if not isinstance(grid[0], (list, tuple)) or not 12 <= len(grid[0]) <= 30:
        return ["input must contain twelve through thirty columns"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["input must be rectangular"]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        return ["input cells must be literal ARC color integers from zero through nine"]
    return []


def _extract_layers(grid):
    errors = _valid_grid(grid)
    if errors:
        return {"errors": errors, "layers": (), "bboxes": (), "insets": ()}
    height, width = len(grid), len(grid[0])
    bbox = (0, 0, height - 1, width - 1)
    layers = []
    bboxes = []
    insets = []
    for _ in range(7):
        row0, col0, row1, col1 = bbox
        color = grid[row0][col0]
        layers.append(color)
        bboxes.append(bbox)
        different = [
            (row, col)
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
            if grid[row][col] != color
        ]
        if not different:
            break
        inner = (
            min(row for row, _ in different),
            min(col for _, col in different),
            max(row for row, _ in different),
            max(col for _, col in different),
        )
        inner_row0, inner_col0, inner_row1, inner_col1 = inner
        inset = (inner_row0 - row0, inner_col0 - col0, row1 - inner_row1, col1 - inner_col1)
        if min(inset) < 1:
            errors.append("each inner rectangle must be strictly inset on all four sides")
            break
        if any(
            grid[row][col] != color
            for row in range(row0, row1 + 1)
            for col in range(col0, col1 + 1)
            if not (inner_row0 <= row <= inner_row1 and inner_col0 <= col <= inner_col1)
        ):
            errors.append("every exposed rectangular ring must be uniform")
            break
        insets.append(inset)
        bbox = inner
    else:
        errors.append("at most six nested rectangles are supported")
    if len(layers) < 2:
        errors.append("at least two nested rectangles are required")
    if len(layers) > 6:
        errors.append("at most six nested rectangles are supported")
    if any(first == second for first, second in zip(layers, layers[1:])):
        errors.append("adjacent layers must have different colors")
    if bboxes:
        row0, col0, row1, col1 = bboxes[-1]
        if row1 - row0 + 1 < 3 or col1 - col0 + 1 < 3:
            errors.append("the innermost rectangle must be at least 3x3")
    return {"errors": errors, "layers": tuple(layers), "bboxes": tuple(bboxes), "insets": tuple(insets)}


def rule_mirror(grid):
    """Exact Python mirror of recursive layer extraction and ring normalization."""
    extracted = _extract_layers(grid)
    if extracted["errors"]:
        raise ValueError("; ".join(extracted["errors"]))
    layers = extracted["layers"]
    size = 2 * len(layers) - 1
    middle = size // 2
    return [
        [layers[len(layers) - 1 - max(abs(row - middle), abs(col - middle))] for col in range(size)]
        for row in range(size)
    ]


def _main_diagonal_run_compression(grid):
    """Canonical-fitting shortcut: infer rings from run changes on the NW-SE diagonal."""
    if _valid_grid(grid):
        return [list(row) for row in grid]
    runs = []
    for index in range(min(len(grid), len(grid[0]))):
        value = grid[index][index]
        if not runs or runs[-1] != value:
            runs.append(value)
    colors = runs[: (len(runs) + 1) // 2]
    size = 2 * len(colors) - 1
    middle = size // 2
    return [
        [colors[len(colors) - 1 - max(abs(row - middle), abs(col - middle))] for col in range(size)]
        for row in range(size)
    ]


def _refutes_main_diagonal_run_compression(grid):
    return not self_check(grid) and _main_diagonal_run_compression(grid) != rule_mirror(grid)


def strict_canonical_like(grid):
    """The strict semantic domain is the generator's validated rectangle grammar."""
    return self_check(grid)


SEMANTIC_WITNESSES = {
    "refutes_main_diagonal_run_compression": _refutes_main_diagonal_run_compression,
}
SEMANTIC_RIVALS = {
    "main_diagonal_run_compression": _main_diagonal_run_compression,
}
WITNESS_RIVALS = {
    "refutes_main_diagonal_run_compression": ["main_diagonal_run_compression"],
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query=None):
    """Reject lessons where the named diagonal shortcut survives every demonstration."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons = []
    pairs = list(demos) + ([] if query is None else [query])
    for index, pair in enumerate(pairs):
        label = "query" if query is not None and index == len(demos) else f"demo {index}"
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"{label} must contain input and output")
            continue
        findings = strict_canonical_like(pair["input"])
        if findings:
            reasons.append(f"{label} is outside the strict grammar: {findings[0]}")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"{label} output disagrees with the selected rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(competitor(pair["input"]) == pair["output"] for pair in demos)
        if not survives:
            continue
        if query is None or competitor(query["input"]) != query["output"]:
            reasons.append(f"named rival survives all demonstrations: {name}")
    return reasons


def _color_pattern(colors):
    labels = {}
    return tuple(labels.setdefault(color, len(labels)) for color in colors)


def _structural_key(grid):
    extracted = _extract_layers(grid)
    if extracted["errors"]:
        return None
    return len(grid), len(grid[0]), extracted["bboxes"], _color_pattern(extracted["layers"])


def _rotated(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _transforms(grid):
    result = []
    current = [row[:] for row in grid]
    for _ in range(4):
        result.append([row[:] for row in current])
        result.append([row[::-1] for row in current])
        current = _rotated(current)
    return result


_PUBLIC_FAMILIES = {
    _structural_key(transformed): profile
    for profile, grid in _PUBLIC_INPUTS.items()
    for transformed in _transforms(grid)
}


def _general_profile(facts):
    count = facts["layer_count"]
    if count == 2:
        return "two_layers"
    if count == 6:
        return "six_layers"
    if len(set(facts["layers"])) < count:
        return "repeated_colors"
    centered = all(top == bottom and left == right for top, left, bottom, right in facts["insets"])
    if centered:
        return "square_centered" if facts["height"] == facts["width"] else "rectangular_centered"
    minimums = [min(inset) for inset in facts["insets"]]
    if all(value == 1 for value in minimums):
        return "thin_offcenter"
    if all(value >= 3 for value in minimums):
        return "thick_offcenter"
    if facts["height"] > facts["width"]:
        return "tall_offcenter"
    if facts["width"] > facts["height"]:
        return "wide_offcenter"
    return "square_offcenter"


def _analysis(grid):
    extracted = _extract_layers(grid)
    errors = list(extracted["errors"])
    if errors:
        return {"errors": errors, "scene_profile": None, "facts": None, "output": None}
    layers, bboxes, insets = extracted["layers"], extracted["bboxes"], extracted["insets"]
    facts = {
        "height": len(grid),
        "width": len(grid[0]),
        "layer_count": len(layers),
        "layers": layers,
        "color_pattern": _color_pattern(layers),
        "bboxes": bboxes,
        "insets": insets,
        "innermost_shape": (bboxes[-1][2] - bboxes[-1][0] + 1, bboxes[-1][3] - bboxes[-1][1] + 1),
        "output_size": 2 * len(layers) - 1,
    }
    profile = _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))
    if profile is None:
        profile = _PUBLIC_FAMILIES.get(_structural_key(grid))
    if profile is None:
        profile = _general_profile(facts)
    if profile not in SCENE_PROFILES:
        errors.append("grid does not match a declared nested-rectangle profile")
    output = None if errors else rule_mirror(grid)
    if output is not None:
        size = facts["output_size"]
        if len(output) != size or any(len(row) != size for row in output):
            errors.append("output must be the 2K-1 square for K layers")
        if output[size // 2][size // 2] != layers[-1]:
            errors.append("output center must use the innermost color")
    return {"errors": errors, "scene_profile": profile, "facts": facts, "output": output}


def self_check(grid, *, difficulty=None, meta=None):
    return _analysis(grid)["errors"]


def canonical_profile_signature(grid):
    return _PUBLIC_SIGNATURES.get(tuple(map(tuple, grid)))


def canonical_family_signature(grid):
    return _PUBLIC_FAMILIES.get(_structural_key(grid))


def observe_overrides(grid):
    analysis = _analysis(grid)
    return {"scene_profile": analysis["scene_profile"]} if not analysis["errors"] else {}


def _limits(difficulty):
    if difficulty == "easy":
        return 14, 21
    if difficulty == "medium":
        return 19, 26
    if difficulty == "hard":
        return 24, 30
    return 18, 29


def _paint_nested(height, width, insets, colors):
    grid = [[colors[0]] * width for _ in range(height)]
    bbox = (0, 0, height - 1, width - 1)
    for color, (top, left, bottom, right) in zip(colors[1:], insets):
        row0, col0, row1, col1 = bbox
        bbox = row0 + top, col0 + left, row1 - bottom, col1 - right
        inner_row0, inner_col0, inner_row1, inner_col1 = bbox
        if inner_row1 - inner_row0 + 1 < 3 or inner_col1 - inner_col0 + 1 < 3:
            raise AssertionError("nested rectangles exhausted the canvas")
        for row in range(inner_row0, inner_row1 + 1):
            for col in range(inner_col0, inner_col1 + 1):
                grid[row][col] = color
    return grid


def _palette(count, rng, *, repeated=False):
    if repeated:
        first, second, third = rng.sample(range(10), 3)
        return [first, second, third, first]
    return rng.sample(range(10), count)


def _mixed_insets(count, rng):
    insets = []
    for index in range(count - 1):
        if index == 0:
            values = [1, rng.randint(2, 3), rng.randint(2, 3), rng.randint(2, 3)]
        elif index == 1:
            values = [2, 2, rng.randint(2, 3), rng.randint(2, 3)]
        else:
            values = [rng.randint(1, 3) for _ in range(4)]
        rng.shuffle(values)
        insets.append(tuple(values))
    return insets


def _general_scene_once(profile, difficulty, rng):
    lo, hi = _limits(difficulty)
    if profile == "two_layers":
        count = 2
    elif profile == "six_layers":
        count = 6
        lo = max(lo, 23)
        hi = max(hi, lo)
    elif profile == "repeated_colors":
        count = 4
    elif profile == "thick_offcenter":
        count = 3
        lo = max(lo, 21)
    else:
        count = rng.randint(3, 5)

    if profile in ("square_centered", "square_offcenter"):
        side = rng.randint(lo, hi)
        height = width = side
    elif profile == "tall_offcenter":
        width = rng.randint(lo, max(lo, hi - 3))
        height = rng.randint(width + 2, min(30, width + 7))
    elif profile == "wide_offcenter":
        height = rng.randint(lo, max(lo, hi - 3))
        width = rng.randint(height + 2, min(30, height + 7))
    else:
        height, width = rng.randint(lo, hi), rng.randint(lo, hi)
        if profile == "rectangular_centered" and height == width:
            width = min(30, width + 1)

    if profile in ("square_centered", "rectangular_centered"):
        insets = []
        remaining_h, remaining_w = height, width
        for _ in range(count - 1):
            maximum = min(3, (remaining_h - 3) // 2, (remaining_w - 3) // 2)
            if maximum < 1:
                raise AssertionError("canvas too small for centered hierarchy")
            amount = rng.randint(1, maximum)
            insets.append((amount, amount, amount, amount))
            remaining_h -= 2 * amount
            remaining_w -= 2 * amount
    elif profile == "thin_offcenter" or profile == "six_layers":
        insets = []
        for _ in range(count - 1):
            values = [1, rng.randint(1, 2), rng.randint(1, 2), rng.randint(1, 2)]
            if len(set(values)) == 1:
                values[-1] = 2
            rng.shuffle(values)
            insets.append(tuple(values))
    elif profile == "thick_offcenter":
        insets = []
        for index in range(count - 1):
            values = [rng.randint(3, 4) for _ in range(4)]
            if len(set(values)) == 1:
                values[index % 4] = 3 if values[index % 4] == 4 else 4
            insets.append(tuple(values))
    else:
        insets = _mixed_insets(count, rng)

    colors = _palette(count, rng, repeated=profile == "repeated_colors")
    return _paint_nested(height, width, insets, colors)


def _general_scene(profile, difficulty, rng):
    for _ in range(100):
        try:
            grid = _general_scene_once(profile, difficulty, rng)
        except (AssertionError, ValueError):
            continue
        analysis = _analysis(grid)
        if not analysis["errors"] and analysis["scene_profile"] == profile:
            return grid
    raise AssertionError(f"could not construct valid scene profile {profile!r}")


def _public_nuisance(profile, rng):
    source = _PUBLIC_INPUTS[profile]
    transformed = rng.choice(_transforms(source))
    colors = sorted({value for row in transformed for value in row})
    replacement = rng.sample(range(10), len(colors))
    mapping = dict(zip(colors, replacement))
    return [[mapping[value] for value in row] for row in transformed]


def _scheduled_profile(sample_index):
    """Periodic default prior with two shortcut witnesses in every four pairs."""
    residue = sample_index % 8
    block = sample_index // 8
    if residue % 2 == 0:
        return "thin_offcenter"
    if residue in (1, 3, 5):
        offset = {1: 0, 3: 1, 5: 2}[residue]
        return PUBLIC_PROFILES[(block + offset) % len(PUBLIC_PROFILES)]
    return GENERAL_PROFILES[block % len(GENERAL_PROFILES)]


def _shortcut_witness_scene(difficulty, rng):
    """Build a lawful thin off-center hierarchy whose deepest layer misses r=c."""
    height, width, left_inset = {
        "easy": (16, 23, 4),
        "medium": (19, 26, 4),
        "hard": (24, 30, 5),
        None: (20, 27, 4),
    }[difficulty]
    insets = [(1, left_inset, 1, 1)] * 4
    grid = _paint_nested(height, width, insets, _palette(5, rng))
    analysis = _analysis(grid)
    if analysis["errors"] or analysis["scene_profile"] != "thin_offcenter":
        raise AssertionError("shortcut witness left the declared thin_offcenter profile")
    if not _refutes_main_diagonal_run_compression(grid):
        raise AssertionError("shortcut witness no longer refutes the diagonal rival")
    return grid


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int:
        raise ValueError("seed must be a literal integer (not bool)")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError("sample_index must be a nonnegative literal integer (not bool)")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")
    unknown = set(overrides) - {"scene_profile"}
    if unknown:
        raise ValueError(f"unknown override(s): {sorted(unknown)!r}")
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=DRAW_VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    explicit_profile = overrides.get("scene_profile") is not None
    profile_options = SCENE_PROFILES if explicit_profile else (_scheduled_profile(sample_index),)
    profile = ctx.draw_choice("scene_profile", profile_options)
    if profile not in SCENE_PROFILES:
        raise ValueError(f"unknown scene_profile: {profile!r}")
    if profile in PUBLIC_PROFILES:
        if overrides.get("scene_profile") is not None:
            return [row[:] for row in _PUBLIC_INPUTS[profile]]
        grid = _public_nuisance(profile, ctx.draw_rng("public_transform"))
    elif not explicit_profile and sample_index % 2 == 0:
        grid = _shortcut_witness_scene(difficulty, ctx.draw_rng("shortcut_witness"))
    else:
        grid = _general_scene(profile, difficulty, ctx.draw_rng("scene"))
    errors = self_check(grid)
    if errors:
        raise AssertionError("generated invalid nested-rectangle lesson: " + "; ".join(errors))
    return grid
