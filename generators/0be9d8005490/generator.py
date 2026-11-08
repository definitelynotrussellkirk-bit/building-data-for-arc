"""Generator for 0be9d8005490: complete a wildcard template.

The yellow cells define wildcard positions inside one dense 3x3 template.
Every other 3x3 occurrence must agree with the template's blue/cyan body and
must be blank at the wildcard positions.  The output copies yellow into those
blank wildcard cells while preserving the template, scene noise, and all
nonzero cells.

Four profiles preserve the complete linked public template morphology and
target count.  A fifth profile samples the surrounding lawful 3x3 template
space.  All profiles retain the demonstrated 22x22 canvas, 0/1/4/8 role
palette, dense distractor field, and one or two exact targets.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations, product

from puzzle_generators.base import gen_ctx


GENERATOR_ID = "0be9d8005490"
TASK_ID = "0be9d8005490"
VERSION = "4.0.0"
RULE_HASH = "ad2d4daab289"

SUMMARY = (
    "Build a dense 22x22 black field containing one 3x3 blue/cyan template "
    "whose yellow cells are blank wildcards. Place one or two exact unmarked "
    "copies plus substantial blue/cyan distractor noise. Copy yellow into "
    "the wildcard slots of every exact copy; preserve all source content."
)

EXAMPLES_NEEDED = 4
EXPECTED_OUTPUT_CODOMAIN = 1_000_000
OUTPUT_CODOMAIN_BY_DIFFICULTY = {
    "easy": 200_000,
    "medium": 500_000,
    "hard": 1_000_000,
    None: 500_000,
}

INVARIANTS = [
    "the calibrated input is a 22x22 grid using exactly colors 0, 1, 4, and 8",
    "all yellow cells lie in one 3x3 bbox and define four to six wildcards",
    "every non-wildcard template cell is blue or cyan and both colors occur",
    "one or two disjoint copies match the body and are blank at all wildcards",
    "44..90 blue/cyan noise cells remain outside the template and clean copies",
    "the output preserves every nonzero cell and fills exactly each target wildcard",
]

SCENE_PROFILES = (
    "wild4_body5_targets2",
    "wild5_body4_targets1",
    "wild6_body3_targets2",
    "wild5_body4_targets2",
    "generalized",
)

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "difficulty-weighted complete linked form",
        "valid": "|".join(SCENE_PROFILES),
        "doc": (
            "Recovered from the D4-normalized 3x3 wildcard/body pattern and "
            "the exact number of clean unmarked target copies."
        ),
    },
}

HELPFUL_TEXTURES = ()
DEGENERATE_TEXTURES = ()


_PUBLIC_PATTERNS = {
    "wild4_body5_targets2": {
        "template": (
            (-1, 8, -1),
            (8, 1, 1),
            (-1, 1, -1),
        ),
        "targets": 2,
    },
    "wild5_body4_targets1": {
        "template": (
            (1, -1, 1),
            (-1, 8, -1),
            (-1, -1, 1),
        ),
        "targets": 1,
    },
    "wild6_body3_targets2": {
        "template": (
            (-1, 8, -1),
            (8, -1, 1),
            (-1, -1, -1),
        ),
        "targets": 2,
    },
    "wild5_body4_targets2": {
        "template": (
            (-1, 8, -1),
            (-1, 8, 8),
            (-1, 1, -1),
        ),
        "targets": 2,
    },
}


def _rotate_pattern(pattern):
    height = len(pattern)
    width = len(pattern[0])
    return tuple(
        tuple(pattern[height - 1 - row][col] for row in range(height))
        for col in range(width)
    )


def _flip_pattern(pattern):
    return tuple(tuple(reversed(row)) for row in pattern)


def _pattern_orbit(pattern):
    variants = []
    current = tuple(tuple(row) for row in pattern)
    for _ in range(4):
        variants.extend((current, _flip_pattern(current)))
        current = _rotate_pattern(current)
    return tuple(dict.fromkeys(variants))


def _normal_pattern(pattern):
    return min(_pattern_orbit(pattern))


_EXACT_SIGNATURES = {
    (
        _normal_pattern(spec["template"]),
        spec["targets"],
    ): profile
    for profile, spec in _PUBLIC_PATTERNS.items()
}
_EXACT_PATTERN_FORMS = {
    _normal_pattern(spec["template"])
    for spec in _PUBLIC_PATTERNS.values()
}


def _matches_template_at(grid, template, top, left):
    height = len(grid)
    width = len(grid[0])
    if (
        top < 0
        or left < 0
        or top + len(template) > height
        or left + len(template[0]) > width
    ):
        return False
    return all(
        grid[top + row][left + col] == (0 if value == -1 else value)
        for row, values in enumerate(template)
        for col, value in enumerate(values)
    )


def _isolated_unique(pattern):
    grid = [[0 for _ in range(7)] for _ in range(7)]
    for row, values in enumerate(pattern):
        for col, value in enumerate(values):
            if value != -1:
                grid[2 + row][2 + col] = value
    matches = [
        (top, left)
        for top in range(5)
        for left in range(5)
        if _matches_template_at(grid, pattern, top, left)
    ]
    return matches == [(2, 2)]


def _build_general_templates():
    templates = []
    positions = tuple((row, col) for row in range(3) for col in range(3))
    for wildcard_count in (4, 5, 6):
        for wildcard_cells in combinations(positions, wildcard_count):
            wildcard_set = set(wildcard_cells)
            wildcard_rows = {row for row, _ in wildcard_set}
            wildcard_cols = {col for _, col in wildcard_set}
            if wildcard_rows != {0, 1, 2} or wildcard_cols != {0, 1, 2}:
                continue
            body_cells = tuple(cell for cell in positions if cell not in wildcard_set)
            for body_values in product((1, 8), repeat=len(body_cells)):
                if set(body_values) != {1, 8}:
                    continue
                mapping = dict(zip(body_cells, body_values))
                pattern = tuple(
                    tuple(
                        -1 if (row, col) in wildcard_set
                        else mapping[(row, col)]
                        for col in range(3)
                    )
                    for row in range(3)
                )
                if _normal_pattern(pattern) in _EXACT_PATTERN_FORMS:
                    continue
                if _isolated_unique(pattern):
                    templates.append(pattern)
    return tuple(templates)


_GENERAL_TEMPLATES = _build_general_templates()
if not _GENERAL_TEMPLATES:
    raise RuntimeError("generalized template inventory is empty")
if not all(
    _isolated_unique(spec["template"])
    for spec in _PUBLIC_PATTERNS.values()
):
    raise RuntimeError("a public template has an ambiguous isolated match")


def _coerce_arc_grid(grid):
    errors = []
    if not isinstance(grid, (list, tuple)) or not grid:
        return [], ["grid must be a nonempty row sequence"]
    if any(not isinstance(row, (list, tuple)) for row in grid):
        return [], ["every grid row must be a sequence"]
    width = len(grid[0])
    if width == 0 or any(len(row) != width for row in grid):
        return [], ["grid must be nonempty and rectangular"]
    if len(grid) > 30 or width > 30:
        errors.append("grid dimensions must not exceed 30")
    output = []
    for row in grid:
        output_row = []
        for value in row:
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or not 0 <= value <= 9
            ):
                errors.append("grid values must be integer ARC colors 0..9")
                return [], errors
            output_row.append(value)
        output.append(output_row)
    return output, errors


def _template_from_grid(grid):
    yellow = [
        (row, col)
        for row in range(len(grid))
        for col in range(len(grid[0]))
        if grid[row][col] == 4
    ]
    if not yellow:
        return None
    top = min(row for row, _ in yellow)
    bottom = max(row for row, _ in yellow)
    left = min(col for _, col in yellow)
    right = max(col for _, col in yellow)
    template = tuple(
        tuple(
            -1 if grid[top + row][left + col] == 4
            else grid[top + row][left + col]
            for col in range(right - left + 1)
        )
        for row in range(bottom - top + 1)
    )
    return (top, left), template, tuple(yellow)


def _find_matches(grid, template, origin):
    height = len(grid)
    width = len(grid[0])
    template_height = len(template)
    template_width = len(template[0])
    return tuple(
        (top, left)
        for top in range(height - template_height + 1)
        for left in range(width - template_width + 1)
        if (top, left) != origin
        and _matches_template_at(grid, template, top, left)
    )


def _boxes_disjoint(boxes):
    return all(
        abs(top_a - top_b) >= 3 or abs(left_a - left_b) >= 3
        for index, (top_a, left_a) in enumerate(boxes)
        for top_b, left_b in boxes[index + 1 :]
    )


def _analyze_scene(grid):
    original, errors = _coerce_arc_grid(grid)
    if errors or len(original) != 22 or len(original[0]) != 22:
        return None
    values = {value for row in original for value in row}
    if values != {0, 1, 4, 8}:
        return None
    template_info = _template_from_grid(original)
    if template_info is None:
        return None
    origin, template, yellow = template_info
    if len(template) != 3 or len(template[0]) != 3:
        return None
    wildcard_count = sum(
        value == -1
        for row in template
        for value in row
    )
    body_values = [
        value
        for row in template
        for value in row
        if value != -1
    ]
    if (
        len(yellow) != wildcard_count
        or not 4 <= wildcard_count <= 6
        or set(body_values) != {1, 8}
        or any(value not in (1, 8) for value in body_values)
    ):
        return None
    matches = _find_matches(original, template, origin)
    if len(matches) not in (1, 2):
        return None
    if not _boxes_disjoint((origin, *matches)):
        return None
    counts = Counter(value for row in original for value in row)
    noise_nonzero = (
        counts[1]
        + counts[8]
        - len(body_values) * (1 + len(matches))
    )
    if not 44 <= noise_nonzero <= 90:
        return None
    signature = (_normal_pattern(template), len(matches))
    profile = _EXACT_SIGNATURES.get(signature, "generalized")
    return {
        "scene_profile": profile,
        "origin": origin,
        "template": template,
        "matches": matches,
        "wildcard_count": wildcard_count,
        "body_count": len(body_values),
        "noise_nonzero": noise_nonzero,
        "color_counts": counts,
    }


def observe_overrides(grid):
    """Recover every declared semantic override from the returned grid."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return {}
    return {"scene_profile": analysis["scene_profile"]}


def canonical_profile_index(grid):
    """Return a linked public-profile index, or ``None``."""
    analysis = _analyze_scene(grid)
    if analysis is None:
        return None
    profile = analysis["scene_profile"]
    if profile == "generalized":
        return None
    return SCENE_PROFILES.index(profile)


def self_check(grid, *, difficulty=None, meta=None):
    """Strict returned-grid recognizer for the calibrated task grammar."""
    _original, errors = _coerce_arc_grid(grid)
    if errors:
        return errors
    if difficulty not in (None, "easy", "medium", "hard"):
        return ["difficulty must be easy, medium, hard, or None"]
    analysis = _analyze_scene(grid)
    if analysis is None:
        return [
            "expected a 22x22 0/1/4/8 scene with one dense 3x3 "
            "four-to-six-wildcard template, one or two exact blank-wildcard "
            "copies, and 44..90 blue/cyan distractor cells"
        ]
    if isinstance(meta, dict):
        requested = meta.get("overrides")
        if not isinstance(requested, dict):
            requested = meta
        requested_profile = requested.get("scene_profile")
        if (
            requested_profile is not None
            and requested_profile != analysis["scene_profile"]
        ):
            errors.append(
                f"scene_profile requested {requested_profile!r}, "
                f"observed {analysis['scene_profile']!r}"
            )
    return errors


def _profile_options(difficulty):
    generalized_weight = {
        "easy": 4,
        "medium": 5,
        "hard": 6,
        None: 5,
    }[difficulty]
    return tuple(_PUBLIC_PATTERNS) + ("generalized",) * generalized_weight


def _noise_range(difficulty):
    if difficulty == "easy":
        return 47, 58
    if difficulty == "hard":
        return 75, 90
    return 59, 74


def _transform_pattern(pattern, transform_index):
    return _pattern_orbit(pattern)[transform_index % len(_pattern_orbit(pattern))]


def _positions_compatible(first, second):
    return (
        abs(first[0] - second[0]) >= 5
        or abs(first[1] - second[1]) >= 5
    )


def _choose_positions(rng, count):
    candidates = [
        (top, left)
        for top in range(20)
        for left in range(20)
    ]
    rng.shuffle(candidates)
    selected = []
    visits = 0

    def search(start):
        nonlocal visits
        if len(selected) == count:
            return True
        for index in range(start, len(candidates)):
            visits += 1
            if visits > 20000:
                return False
            candidate = candidates[index]
            if not all(
                _positions_compatible(candidate, prior)
                for prior in selected
            ):
                continue
            selected.append(candidate)
            if search(index + 1):
                return True
            selected.pop()
        return False

    if not search(0):
        raise RuntimeError("could not construct separated 3x3 placements")
    return tuple(selected)


def _box_cells(top, left):
    return {
        (top + row, left + col)
        for row in range(3)
        for col in range(3)
    }


def _stamp_template(grid, top, left, template, marked):
    for row, values in enumerate(template):
        for col, value in enumerate(values):
            if value == -1:
                grid[top + row][left + col] = 4 if marked else 0
            else:
                grid[top + row][left + col] = value


def _safe_decoy_options(template, mode, rng):
    if mode == "near_miss":
        options = [
            (row, col, 8 if value == 1 else 1)
            for row, values in enumerate(template)
            for col, value in enumerate(values)
            if value in (1, 8)
        ]
    else:
        options = [
            (row, col, color)
            for row, values in enumerate(template)
            for col, value in enumerate(values)
            if value == -1
            for color in (1, 8)
        ]
    rng.shuffle(options)
    return options


def _place_decoy(
    grid,
    top,
    left,
    template,
    origin,
    target_positions,
    mode,
    rng,
):
    expected = set(target_positions)
    for changed_row, changed_col, changed_value in _safe_decoy_options(
        template,
        mode,
        rng,
    ):
        prior = [grid[top + row][left + col] for row in range(3) for col in range(3)]
        _stamp_template(grid, top, left, template, marked=False)
        grid[top + changed_row][left + changed_col] = changed_value
        if set(_find_matches(grid, template, origin)) == expected:
            return
        for index, value in enumerate(prior):
            grid[top + index // 3][left + index % 3] = value
    raise RuntimeError(f"could not place a safe {mode} decoy")


def _would_create_extra_match(
    grid,
    template,
    origin,
    expected_targets,
    row,
    col,
    color,
):
    previous = grid[row][col]
    grid[row][col] = color
    creates = False
    for delta_row, values in enumerate(template):
        for delta_col, value in enumerate(values):
            if value != color:
                continue
            top = row - delta_row
            left = col - delta_col
            if (top, left) == origin or (top, left) in expected_targets:
                continue
            if _matches_template_at(grid, template, top, left):
                creates = True
                break
        if creates:
            break
    grid[row][col] = previous
    return creates


def _add_dense_noise(
    grid,
    template,
    origin,
    target_positions,
    protected,
    budget,
    rng,
):
    body_count = sum(
        value != -1
        for row in template
        for value in row
    )
    counts = Counter(value for row in grid for value in row)
    current_noise = (
        counts[1]
        + counts[8]
        - body_count * (1 + len(target_positions))
    )
    needed = budget - current_noise
    if needed < 0:
        raise RuntimeError("decoy exceeds the requested noise budget")
    candidates = [
        (row, col)
        for row in range(22)
        for col in range(22)
        if grid[row][col] == 0 and (row, col) not in protected
    ]
    rng.shuffle(candidates)
    expected_targets = set(target_positions)
    for row, col in candidates:
        colors = [1, 8]
        rng.shuffle(colors)
        for color in colors:
            if _would_create_extra_match(
                grid,
                template,
                origin,
                expected_targets,
                row,
                col,
                color,
            ):
                continue
            grid[row][col] = color
            needed -= 1
            break
        if needed == 0:
            break
    if needed:
        raise RuntimeError(
            f"could not place {needed} dense-noise cells without a false match"
        )


def _construct_scene(profile, difficulty, context):
    rng = context.draw_rng("layout")
    if profile == "generalized":
        template = rng.choice(_GENERAL_TEMPLATES)
        target_count = (
            1
            if difficulty == "easy" and rng.randrange(3) == 0
            else 2
        )
        adversary_mode = rng.choice(("near_miss", "occupied_wildcard"))
    else:
        spec = _PUBLIC_PATTERNS[profile]
        template = spec["template"]
        target_count = spec["targets"]
        adversary_mode = None
    template = _transform_pattern(template, rng.randrange(8))
    placement_count = 1 + target_count + (adversary_mode is not None)
    placements = _choose_positions(rng, placement_count)
    origin = placements[0]
    targets = placements[1 : 1 + target_count]
    decoy = placements[-1] if adversary_mode is not None else None

    grid = [[0 for _ in range(22)] for _ in range(22)]
    _stamp_template(grid, *origin, template, marked=True)
    for top, left in targets:
        _stamp_template(grid, top, left, template, marked=False)
    if set(_find_matches(grid, template, origin)) != set(targets):
        raise RuntimeError("signal placements created an unintended match")

    protected = set()
    for top, left in (origin, *targets):
        protected.update(_box_cells(top, left))
    if decoy is not None:
        _place_decoy(
            grid,
            *decoy,
            template,
            origin,
            targets,
            adversary_mode,
            rng,
        )
        protected.update(_box_cells(*decoy))

    low_noise, high_noise = _noise_range(difficulty)
    noise_budget = context.draw_int("noise_nonzero", low_noise, high_noise)
    _add_dense_noise(
        grid,
        template,
        origin,
        targets,
        protected,
        noise_budget,
        rng,
    )
    if set(_find_matches(grid, template, origin)) != set(targets):
        raise RuntimeError("dense noise created an unintended match")
    return grid


def _validate_call(difficulty, overrides):
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            "difficulty must be None, 'easy', 'medium', or 'hard'"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError("unknown override(s): " + ", ".join(unknown))
    profile = overrides.get("scene_profile")
    if profile is not None and profile not in SCENE_PROFILES:
        raise ValueError("unknown scene_profile")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_call(difficulty, overrides)
    context = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = context.draw_choice(
        "scene_profile",
        _profile_options(difficulty),
    )
    grid = _construct_scene(profile, difficulty, context)
    errors = self_check(
        grid,
        difficulty=difficulty,
        meta={"overrides": overrides},
    )
    if errors:
        raise RuntimeError(
            "constructed an invalid calibrated scene: " + "; ".join(errors)
        )
    if rule_mirror(grid) == grid:
        raise RuntimeError("constructed an identity rule example")
    return grid


def rule_mirror(grid):
    """Input-pure Python mirror of the complete canonical Racket rule."""
    original, errors = _coerce_arc_grid(grid)
    if errors:
        raise ValueError("; ".join(errors))
    template_info = _template_from_grid(original)
    if template_info is None:
        raise ValueError("canonical rule requires at least one color-4 cell")
    origin, template, _yellow = template_info
    output = [row[:] for row in original]
    for top, left in _find_matches(original, template, origin):
        for row, values in enumerate(template):
            for col, value in enumerate(values):
                if value == -1:
                    output[top + row][left + col] = 4
    return output


_mirror = rule_mirror
