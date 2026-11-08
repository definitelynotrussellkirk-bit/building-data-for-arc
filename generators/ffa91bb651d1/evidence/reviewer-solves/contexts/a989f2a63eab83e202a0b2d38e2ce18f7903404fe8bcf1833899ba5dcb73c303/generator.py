"""Sampler for ARC task ffa91bb651d1: fill exact matching row endpoints.

For each row independently, the selected rule fires only when the row contains
exactly two nonzero cells and those cells have the same color.  It fills the
inclusive horizontal span between them.  Rows with two different colors, three
same-color cells, or a repeated pair plus another nonzero cell stay unchanged.

The two-profile lesson schedule alternates a canonical scene with one compact
adversarial scene.  The adversarial scene simultaneously refutes three rules
that reproduce every public canonical pair: filling each color that occurs
exactly twice, also applying the rule vertically, and requiring exactly three
target rows before doing any work.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from itertools import combinations

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "ffa91bb651d1"
TASK_ID = GENERATOR_ID
RULE_HASH = "021dbc79a954"
VERSION = "3.0.0"
SUMMARY = (
    "In each row, exactly two nonzero cells of the same color fill their "
    "inclusive horizontal span; every other row is unchanged."
)

INVARIANTS = [
    "background is 0 and all cells are integer ARC colors 0..9",
    "the grid is 6..16 by 8..16 with 6 or 7 total colors including 0",
    "there are exactly 2 or 3 target rows with a zero gap between endpoints",
    "there is exactly one mismatched two-cell row and one three-of-a-kind row",
    "comprehensive scenes add one repeated-pair-plus-singleton row",
    "comprehensive scenes contain a gapped vertical exact pair as a negative witness",
]

SCENE_PATTERNS = ("canonical", "comprehensive")
SCHEDULE_PROFILES = SCENE_PATTERNS

AXES = {
    "grid_h": {
        "type": "int",
        "default": "6..16; strongly anchored to a canonical profile",
        "valid": "6..16",
    },
    "grid_w": {
        "type": "int",
        "default": "8..16; strongly anchored to a canonical profile",
        "valid": "8..16",
    },
    "n_targets": {
        "type": "int",
        "default": "3 canonical / 2 comprehensive",
        "valid": "2..3",
    },
    "scene_pattern": {
        "type": "str",
        "default": "alternating canonical|comprehensive lesson schedule",
        "valid": "|".join(SCENE_PATTERNS),
    },
    "palette_count": {
        "type": "int",
        "default": "6 or 7 total colors including background; canonical anchored",
        "valid": "6..7",
    },
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict] = []
MIN_STRICT_FRAC = 1.0
EXAMPLES_NEEDED = 3

# (height, width, total palette size including background).  These are the five
# exact public profiles.  They are scale anchors, never copied puzzle layouts.
_CANONICAL_PROFILES = (
    (8, 10, 6),
    (7, 11, 7),
    (9, 9, 7),
    (6, 12, 6),
    (8, 8, 7),
)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic branch used by an ordinary production draw."""
    del seed, difficulty
    return SCHEDULE_PROFILES[int(sample_index) % len(SCHEDULE_PROFILES)]


def _profile_options(difficulty) -> tuple[tuple[int, int, int], ...]:
    # Difficulty changes emphasis only.  Every exact public axis value remains
    # legal and constructive in every band.
    if difficulty == "easy":
        weights = (9, 7, 3, 9, 7)
    elif difficulty == "hard":
        weights = (4, 7, 9, 4, 7)
    else:
        weights = (6, 6, 6, 6, 6)
    return tuple(
        profile
        for profile, weight in zip(_CANONICAL_PROFILES, weights)
        for _ in range(weight)
    )


def _weighted_axis(ctx, name: str, values, anchor):
    """Keep the complete exact domain while strongly weighting one profile."""
    options = tuple(values) + (anchor,) * 80
    return ctx.draw_choice(name, options)


def _validate_overrides(overrides: dict) -> None:
    unknown = set(overrides) - set(AXES)
    if unknown:
        raise ValueError(f"unknown override axes: {sorted(unknown)}")
    for name in ("grid_h", "grid_w", "n_targets", "palette_count"):
        value = overrides.get(name)
        if value is not None and type(value) is not int:
            raise ValueError(f"{name} must be an integer, not {type(value).__name__}")
    value = overrides.get("scene_pattern")
    if value is not None and type(value) is not str:
        raise ValueError(
            f"scene_pattern must be a string, not {type(value).__name__}"
        )


def _choose_pair(width: int, rng, forbidden=()) -> tuple[int, int]:
    blocked = set(forbidden)
    choices = [
        (left, right)
        for left, right in combinations(range(width), 2)
        if right - left >= 2 and left not in blocked and right not in blocked
    ]
    if not choices:
        raise ValueError("no gapped endpoint pair fits the requested columns")
    return rng.choice(choices)


def _choose_mismatch(
    width: int, rng, forbidden_left=(), forbidden_right=()
) -> tuple[int, int]:
    blocked_left = set(forbidden_left)
    blocked_right = set(forbidden_right)
    choices = [
        (left, right)
        for left in range(width)
        for right in range(width)
        if abs(right - left) >= 2
        and left not in blocked_left
        and right not in blocked_right
    ]
    if not choices:
        raise ValueError("no mismatched endpoint layout fits the requested columns")
    return rng.choice(choices)


def _choose_triple(width: int, rng, forbidden=(), required=None) -> tuple[int, int, int]:
    blocked = set(forbidden)
    choices = []
    for cols in combinations(range(width), 3):
        if any(col in blocked for col in cols):
            continue
        if required is not None and required not in cols:
            continue
        # At least one zero lies between the outer cells.  The canonical rule
        # ignores a three-cell row regardless, but this makes the negative
        # condition visually legible in generated lessons.
        if cols[-1] - cols[0] < 3:
            continue
        choices.append(cols)
    if not choices:
        raise ValueError("no triple layout fits the requested columns")
    return rng.choice(choices)


def _choose_pair_plus_singleton(width: int, rng, forbidden=()) -> tuple[int, int, int]:
    blocked = set(forbidden)
    choices = []
    for left, right in combinations(range(width), 2):
        if right - left < 2 or left in blocked or right in blocked:
            continue
        for singleton in range(width):
            if singleton in blocked or singleton in (left, right):
                continue
            if singleton < left or singleton > right:
                choices.append((left, right, singleton))
    if not choices:
        raise ValueError("no pair-plus-singleton layout fits the requested columns")
    return rng.choice(choices)


def _draw_canonical_scene(grid, n_targets: int, colors: tuple[int, ...], rng) -> None:
    height, width = len(grid), len(grid[0])
    role_count = n_targets + 3  # targets, two mismatch colors, triple color
    role_colors = [colors[index % len(colors)] for index in range(role_count)]
    target_colors = role_colors[:n_targets]
    mismatch_colors = role_colors[n_targets : n_targets + 2]
    triple_color = role_colors[n_targets + 2]
    missing_colors = [color for color in colors if color not in role_colors]

    active_count = n_targets + 2 + len(missing_colors)
    rows = rng.sample(range(height), active_count)
    target_rows = rows[:n_targets]
    mismatch_row = rows[n_targets]
    triple_row = rows[n_targets + 1]
    singleton_rows = rows[n_targets + 2 :]

    # Avoid every same-color vertical alignment.  Therefore the row-or-column
    # shortcut fits these canonical-profile scenes just as it fits all public
    # canonical examples.
    used_columns: dict[int, set[int]] = defaultdict(set)
    for row_index, color in zip(target_rows, target_colors):
        left, right = _choose_pair(width, rng, used_columns[color])
        grid[row_index][left] = color
        grid[row_index][right] = color
        used_columns[color].update((left, right))

    left, right = _choose_mismatch(
        width,
        rng,
        used_columns[mismatch_colors[0]],
        used_columns[mismatch_colors[1]],
    )
    grid[mismatch_row][left] = mismatch_colors[0]
    grid[mismatch_row][right] = mismatch_colors[1]
    used_columns[mismatch_colors[0]].add(left)
    used_columns[mismatch_colors[1]].add(right)

    triple_cols = _choose_triple(width, rng, used_columns[triple_color])
    for col in triple_cols:
        grid[triple_row][col] = triple_color
    used_columns[triple_color].update(triple_cols)

    for row_index, color in zip(singleton_rows, missing_colors):
        choices = [col for col in range(width) if col not in used_columns[color]]
        col = rng.choice(choices)
        grid[row_index][col] = color
        used_columns[color].add(col)


def _draw_comprehensive_scene(
    grid, n_targets: int, colors: tuple[int, ...], rng
) -> None:
    height, width = len(grid), len(grid[0])

    # There are n_targets + 4 independently colored roles.  For the smallest
    # case this is six roles, enough to realize either advertised palette.
    roles = [colors[index % len(colors)] for index in range(n_targets + 4)]
    target_colors = roles[:n_targets]
    vertical_color = roles[n_targets]
    mismatch_other = roles[n_targets + 1]
    pair_color = roles[n_targets + 2]
    singleton_color = roles[n_targets + 3]

    row_pairs = [pair for pair in combinations(range(height), 2) if pair[1] - pair[0] >= 2]
    mismatch_row, triple_row = rng.choice(row_pairs)
    remaining = [row for row in range(height) if row not in (mismatch_row, triple_row)]
    chosen = rng.sample(remaining, n_targets + 1)
    target_rows = chosen[:n_targets]
    pair_row = chosen[-1]

    witness_col = rng.randrange(width)
    other_cols = [col for col in range(width) if abs(col - witness_col) >= 2]
    mismatch_col = rng.choice(other_cols)
    grid[mismatch_row][witness_col] = vertical_color
    grid[mismatch_row][mismatch_col] = mismatch_other

    triple_cols = _choose_triple(width, rng, required=witness_col)
    for col in triple_cols:
        grid[triple_row][col] = vertical_color

    for row_index, color in zip(target_rows, target_colors):
        left, right = _choose_pair(width, rng, {witness_col})
        grid[row_index][left] = color
        grid[row_index][right] = color

    left, right, singleton = _choose_pair_plus_singleton(
        width, rng, {witness_col}
    )
    grid[pair_row][left] = pair_color
    grid[pair_row][right] = pair_color
    grid[pair_row][singleton] = singleton_color


def generate(seed, sample_index, *, difficulty=None, **overrides):
    _validate_overrides(overrides)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    anchor_h, anchor_w, anchor_palette = ctx.draw_choice(
        "curriculum_profile", _profile_options(difficulty)
    )
    height = _weighted_axis(ctx, "grid_h", range(6, 17), anchor_h)
    width = _weighted_axis(ctx, "grid_w", range(8, 17), anchor_w)
    palette_count = _weighted_axis(
        ctx, "palette_count", range(6, 8), anchor_palette
    )

    scheduled = schedule_profile(seed, sample_index, difficulty)
    if overrides.get("scene_pattern") is not None:
        scene_pattern = ctx.draw_choice("scene_pattern", SCENE_PATTERNS)
    else:
        scene_pattern = ctx.draw_choice("scene_pattern", (scheduled,))

    default_targets = 3 if scene_pattern == "canonical" else 2
    if overrides.get("n_targets") is not None:
        n_targets = ctx.draw_choice("n_targets", (2, 3))
    else:
        n_targets = ctx.draw_choice("n_targets", (default_targets,))

    colors = tuple(
        ctx.draw_rng("palette").sample(list(range(1, 10)), palette_count - 1)
    )
    grid = full_grid(height, width, 0)
    placement_rng = ctx.draw_rng("placement")
    if scene_pattern == "canonical":
        _draw_canonical_scene(grid, n_targets, colors, placement_rng)
    else:
        _draw_comprehensive_scene(grid, n_targets, colors, placement_rng)
    return grid


def _shape(grid):
    if not isinstance(grid, (list, tuple)) or not grid:
        return None
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return None
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return None
    return len(grid), width


def _row_kind(row) -> str:
    counts = tuple(sorted(Counter(value for value in row if value != 0).values()))
    return {
        (): "blank",
        (1,): "singleton",
        (2,): "target",
        (1, 1): "mismatch",
        (3,): "triple",
        (1, 2): "pair_plus_singleton",
    }.get(counts, "unsupported")


def _target_count(grid) -> int:
    return sum(_row_kind(row) == "target" for row in grid)


def _has_vertical_exact_pair(grid) -> bool:
    shape = _shape(grid)
    if shape is None:
        return False
    height, width = shape
    for col in range(width):
        nonzero = [(row, grid[row][col]) for row in range(height) if grid[row][col] != 0]
        if (
            len(nonzero) == 2
            and nonzero[0][1] == nonzero[1][1]
            and nonzero[1][0] - nonzero[0][0] >= 2
        ):
            return True
    return False


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    del difficulty, meta
    shape = _shape(grid)
    if shape is None:
        return ["expected a nonempty rectangular grid"]
    height, width = shape
    errors: list[str] = []
    if not 6 <= height <= 16:
        errors.append(f"grid_h={height} outside [6,16]")
    if not 8 <= width <= 16:
        errors.append(f"grid_w={width} outside [8,16]")
    if any(
        type(value) is not int or not 0 <= value <= 9
        for row in grid
        for value in row
    ):
        errors.append("cells must be integer ARC colors 0..9")
        return errors

    palette_count = len({value for row in grid for value in row})
    if palette_count not in (6, 7):
        errors.append(f"palette_count={palette_count} outside {{6,7}}")

    kinds = Counter()
    for row_index, row in enumerate(grid):
        kind = _row_kind(row)
        kinds[kind] += 1
        positions = [col for col, value in enumerate(row) if value != 0]
        if kind == "unsupported":
            counts = sorted(Counter(value for value in row if value != 0).values())
            errors.append(f"row {row_index}: unsupported color multiplicities {counts}")
        elif kind in {"target", "mismatch"} and positions[1] - positions[0] < 2:
            errors.append(f"row {row_index}: two-cell row has no zero gap")
        elif kind == "pair_plus_singleton":
            counts = Counter(value for value in row if value != 0)
            repeated = next(color for color, count in counts.items() if count == 2)
            pair = [col for col, value in enumerate(row) if value == repeated]
            singleton = next(
                col for col, value in enumerate(row) if value != 0 and value != repeated
            )
            if pair[1] - pair[0] < 2:
                errors.append(f"row {row_index}: repeated pair has no zero gap")
            if pair[0] < singleton < pair[1]:
                errors.append(f"row {row_index}: singleton lies inside repeated span")

    if not 2 <= kinds["target"] <= 3:
        errors.append(f"target rows={kinds['target']} outside [2,3]")
    if kinds["mismatch"] != 1:
        errors.append(f"mismatch rows={kinds['mismatch']} expected 1")
    if kinds["triple"] != 1:
        errors.append(f"triple rows={kinds['triple']} expected 1")
    if kinds["pair_plus_singleton"] not in (0, 1):
        errors.append(
            f"pair-plus-singleton rows={kinds['pair_plus_singleton']} expected 0 or 1"
        )
    if kinds["singleton"] > 1:
        errors.append(f"singleton rows={kinds['singleton']} exceeds 1")
    if kinds["pair_plus_singleton"] == 1 and not _has_vertical_exact_pair(grid):
        errors.append("comprehensive scene lacks a gapped vertical exact-pair witness")
    return errors


def strict_canonical_like(grid):
    """Return [] exactly for the lawful task-linked manifold used here."""
    return self_check(grid)


def observe_overrides(grid):
    """Recover every advertised exact control from returned pixels."""
    errors = self_check(grid)
    if errors:
        raise ValueError("; ".join(errors))
    comprehensive = any(_row_kind(row) == "pair_plus_singleton" for row in grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_targets": _target_count(grid),
        "scene_pattern": "comprehensive" if comprehensive else "canonical",
        "palette_count": len({value for row in grid for value in row}),
    }


def _intended_row_rule(grid):
    """Pure Python mirror used only to define executable rival behavior."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        nonzero = [(col, value) for col, value in enumerate(row) if value != 0]
        if len(nonzero) == 2 and nonzero[0][1] == nonzero[1][1]:
            left, color = nonzero[0]
            right = nonzero[1][0]
            for col in range(left, right + 1):
                out[row_index][col] = color
    return out


def _per_color_exact_pair(grid):
    """RIVAL: fill a color appearing twice even when its row has extra cells."""
    out = deepcopy(grid)
    for row_index, row in enumerate(grid):
        counts = Counter(value for value in row if value != 0)
        for color, count in counts.items():
            if count == 2:
                cols = [col for col, value in enumerate(row) if value == color]
                for col in range(cols[0], cols[-1] + 1):
                    out[row_index][col] = color
    return out


def _row_or_column(grid):
    """RIVAL: apply the exact-pair predicate horizontally and vertically."""
    out = _intended_row_rule(grid)
    height, width = len(grid), len(grid[0])
    for col in range(width):
        nonzero = [(row, grid[row][col]) for row in range(height) if grid[row][col] != 0]
        if len(nonzero) == 2 and nonzero[0][1] == nonzero[1][1]:
            top, color = nonzero[0]
            bottom = nonzero[1][0]
            for row in range(top, bottom + 1):
                out[row][col] = color
    return out


def _exactly_three_targets(grid):
    """RIVAL: do nothing unless the scene contains exactly three target rows."""
    return _intended_row_rule(grid) if _target_count(grid) == 3 else deepcopy(grid)


def _has_pair_plus_singleton(grid) -> bool:
    return any(_row_kind(row) == "pair_plus_singleton" for row in grid)


def _has_non_three_target_count(grid) -> bool:
    return _target_count(grid) != 3


SEMANTIC_WITNESSES = {
    "pair_plus_singleton": _has_pair_plus_singleton,
    "vertical_exact_pair": _has_vertical_exact_pair,
    "non_three_target_count": _has_non_three_target_count,
}
SEMANTIC_RIVALS = {
    "per_color_exact_pair": _per_color_exact_pair,
    "row_or_column": _row_or_column,
    "exactly_three_targets": _exactly_three_targets,
}
WITNESS_RIVALS = {
    "pair_plus_singleton": ["per_color_exact_pair"],
    "vertical_exact_pair": ["row_or_column"],
    "non_three_target_count": ["exactly_three_targets"],
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def lesson_identifiable(demos, query) -> list[str]:
    """Name any canonical-fitting rival left able to change the query answer."""
    reasons: list[str] = []
    for name, rival in LESSON_COMPETITORS.items():
        try:
            fits_demos = all(
                rival(deepcopy(pair["input"])) == pair["output"] for pair in demos
            )
            disagrees_query = (
                rival(deepcopy(query["input"])) != query["output"]
            )
        except Exception as exc:
            reasons.append(f"{name} raised {type(exc).__name__}: {exc}")
            continue
        if fits_demos and disagrees_query:
            reasons.append(f"{name} fits all demonstrations but changes the query")
    return reasons
