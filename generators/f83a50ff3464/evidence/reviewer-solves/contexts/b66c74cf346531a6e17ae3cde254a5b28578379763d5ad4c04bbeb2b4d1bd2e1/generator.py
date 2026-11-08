"""Semantic generator for ARC task ``f83a50ff3464``.

Authoritative rule: fill an interior zero cell exactly when its four cardinal
neighbors are the same non-zero color.  The curriculum deliberately includes
near misses that distinguish equality of all four arms from tempting shortcuts
such as a 3-of-4 majority, equal opposite pairs, or three visible arms.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid


GENERATOR_ID = "f83a50ff3464"
TASK_ID = GENERATOR_ID
VERSION = "3.0.0"
RULE_HASH = "14c360998abe"

SUMMARY = (
    "Zero-background grids contain two or three incomplete plus motifs whose "
    "zero centers have four equal non-zero cardinal arms; the rule fills only "
    "those centers. A four-profile curriculum also supplies exact negative "
    "controls: 3+1 arm colors, 2+2 opposite-pair colors, and three-arm partial "
    "pluses. Repeated-color targets and isolated noise prevent per-color and "
    "object-count shortcuts."
)

INVARIANTS = [
    "the background is 0 and every ordinary sample has at least two true plus centers",
    "a true center is 0 with four equal non-zero cardinal neighbors",
    "3+1, 2+2, and three-arm near misses remain unchanged",
    "the Python mirror changes exactly the true plus centers",
    "every four consecutive default lessons falsify all declared shortcut rules",
]

EXAMPLES_NEEDED = 4
MIN_STRICT_FRAC = 1.0
HELPFUL_TEXTURES: tuple[str, ...] = ()
DEGENERATE_TEXTURES: tuple[str, ...] = ()

_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DECOY_KINDS = ("three_plus_one", "two_plus_two", "partial")

# name, band, h, w, true centers, decoy kind, isolated noise, target colors
#
# In every band the four-slot cycle is:
#   clean canonical morphology -> 3+1 + repeated target color -> 2+2 -> partial.
# Thus every consecutive four-demo lesson contains a counterexample to every
# declared canonical shortcut while retaining one profile close to the source.
_PROFILE_ROWS = (
    ("e_clean_7x9", "easy", 7, 9, 2, None, 0, "unique"),
    ("e_majority_8x8", "easy", 8, 8, 2, "three_plus_one", 0, "repeated"),
    ("e_pairs_7x7", "easy", 7, 7, 2, "two_plus_two", 0, "unique"),
    ("e_partial_9x9", "easy", 9, 9, 3, "partial", 0, "unique"),
    ("m_clean_8x8", "medium", 8, 8, 2, None, 2, "unique"),
    ("m_majority_7x9", "medium", 7, 9, 3, "three_plus_one", 0, "repeated"),
    ("m_pairs_9x9", "medium", 9, 9, 3, "two_plus_two", 1, "unique"),
    ("m_partial_7x7", "medium", 7, 7, 2, "partial", 1, "unique"),
    ("h_clean_9x9", "hard", 9, 9, 3, None, 0, "unique"),
    ("h_majority_9x9", "hard", 9, 9, 3, "three_plus_one", 1, "repeated"),
    ("h_pairs_8x8", "hard", 8, 8, 3, "two_plus_two", 0, "unique"),
    ("h_partial_7x9", "hard", 7, 9, 3, "partial", 1, "unique"),
)

SCENE_PROFILES = tuple(row[0] for row in _PROFILE_ROWS)
SCHEDULE_PROFILES = SCENE_PROFILES
_PROFILE_BY_NAME = {
    name: {
        "band": band,
        "height": height,
        "width": width,
        "target_count": target_count,
        "decoy_kind": decoy_kind,
        "noise_count": noise_count,
        "target_color_mode": target_color_mode,
    }
    for (
        name,
        band,
        height,
        width,
        target_count,
        decoy_kind,
        noise_count,
        target_color_mode,
    ) in _PROFILE_ROWS
}
_PROFILES_BY_BAND = {
    band: tuple(row[0] for row in _PROFILE_ROWS if row[1] == band)
    for band in ("easy", "medium", "hard")
}

AXES = {
    "scene_profile": {
        "type": "str",
        "default": "deterministic four-slot curriculum for the selected difficulty band",
        "valid": "e_clean_7x9|e_majority_8x8|e_pairs_7x7|e_partial_9x9|m_clean_8x8|m_majority_7x9|m_pairs_9x9|m_partial_7x7|h_clean_9x9|h_majority_9x9|h_pairs_8x8|h_partial_7x9",
    }
}


def _band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError(f"unknown difficulty: {difficulty!r}")


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Return the deterministic four-slot curriculum profile."""
    del seed
    profiles = _PROFILES_BY_BAND[_band(difficulty)]
    return profiles[int(sample_index) % len(profiles)]


def _grid_errors(grid: Any) -> list[str]:
    if not isinstance(grid, (list, tuple)) or not grid:
        return ["grid must be a non-empty sequence of rows"]
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        return ["grid rows must be non-empty sequences"]
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        return ["grid must be rectangular"]
    if not 5 <= len(grid) <= 30 or not 5 <= width <= 30:
        return [f"grid dimensions must be in 5..30, found {len(grid)}x{width}"]
    for row in grid:
        for value in row:
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 9:
                return ["cells must be literal ARC integers 0..9"]
    return []


def _motif_kind(values: Sequence[int]) -> str | None:
    nonzero = [value for value in values if value != 0]
    counts = sorted(Counter(nonzero).values())
    if len(nonzero) == 4 and counts == [4]:
        return "target"
    if len(nonzero) == 4 and counts == [1, 3]:
        return "three_plus_one"
    if (
        len(nonzero) == 4
        and counts == [2, 2]
        and values[0] == values[1]
        and values[2] == values[3]
        and values[0] != values[2]
    ):
        # The rival is specifically “equal vertical pair plus equal horizontal
        # pair”.  Adjacent-color 2+2 arrangements can arise incidentally when
        # canonical pluses are placed diagonally and are not counterexamples
        # to that rival.
        return "two_plus_two"
    if len(nonzero) == 3 and counts == [3]:
        return "partial"
    return None


def _analyze(grid: Any) -> dict[str, Any]:
    errors = _grid_errors(grid)
    if errors:
        return {"errors": errors}
    height, width = len(grid), len(grid[0])
    centers: dict[str, list[tuple[int, int]]] = {
        "target": [],
        **{name: [] for name in _DECOY_KINDS},
    }
    arm_cells: set[tuple[int, int]] = set()
    target_colors: list[int] = []

    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            values = [grid[row + dr][col + dc] for dr, dc in _CARDINAL]
            kind = _motif_kind(values)
            if kind is None:
                # Other four-arm color arrangements are lawful background
                # neighborhoods.  The canonical third training grid contains
                # two adjacent-pair 2+2 cases between diagonal target pluses.
                continue
            centers[kind].append((row, col))
            for (dr, dc), value in zip(_CARDINAL, values):
                if value != 0:
                    arm_cells.add((row + dr, col + dc))
            if kind == "target":
                target_colors.append(values[0])

    if not centers["target"]:
        errors.append("no true four-equal-arm plus center")

    all_nonzero = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    }
    noise = sorted(all_nonzero - arm_cells)
    if target_colors and len(set(target_colors)) == len(target_colors):
        color_mode = "unique"
    elif target_colors:
        color_mode = "repeated"
    else:
        color_mode = None

    signature = (
        height,
        width,
        len(centers["target"]),
        tuple(len(centers[name]) for name in _DECOY_KINDS),
        len(noise),
        color_mode,
    )
    return {
        "errors": errors,
        "height": height,
        "width": width,
        "centers": centers,
        "target_colors": target_colors,
        "target_color_mode": color_mode,
        "noise": noise,
        "signature": signature,
    }


def _profile_signature(profile: dict[str, Any]) -> tuple[Any, ...]:
    return (
        profile["height"],
        profile["width"],
        profile["target_count"],
        tuple(
            1 if profile["decoy_kind"] == name else 0
            for name in _DECOY_KINDS
        ),
        profile["noise_count"],
        profile["target_color_mode"],
    )


_PROFILE_BY_SIGNATURE = {
    _profile_signature(profile): name for name, profile in _PROFILE_BY_NAME.items()
}


def _fires(grid: Sequence[Sequence[int]]) -> set[tuple[int, int]]:
    """Return exactly the cells changed by the authoritative rule."""
    if _grid_errors(grid):
        return set()
    height, width = len(grid), len(grid[0])
    result: set[tuple[int, int]] = set()
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            values = [grid[row + dr][col + dc] for dr, dc in _CARDINAL]
            if values[0] != 0 and all(value == values[0] for value in values):
                result.add((row, col))
    return result


def rule_mirror(grid: Sequence[Sequence[int]]) -> list[list[int]]:
    """Python mirror of the synchronized canonical Racket rule."""
    errors = _grid_errors(grid)
    if errors:
        raise ValueError("invalid input: " + "; ".join(errors))
    output = [list(row) for row in grid]
    for row, col in _fires(grid):
        output[row][col] = grid[row - 1][col]
    return output


def observe_overrides(grid) -> dict[str, str]:
    """Recover the exact declared scene profile from a returned grid."""
    analysis = _analyze(grid)
    if analysis["errors"]:
        return {}
    profile = _PROFILE_BY_SIGNATURE.get(analysis["signature"])
    return {"scene_profile": profile} if profile else {}


def _meta_overrides(meta: Any) -> dict[str, Any]:
    if not isinstance(meta, dict):
        return {}
    nested = meta.get("overrides")
    return nested if isinstance(nested, dict) else meta


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Reject malformed, identity, or override-clamped lessons."""
    del difficulty
    analysis = _analyze(grid)
    errors = list(analysis["errors"])
    if errors:
        return errors
    if len(analysis["centers"]["target"]) < 1:
        errors.append("the rule would be an identity")
    observed = observe_overrides(grid)
    for name, requested in _meta_overrides(meta).items():
        if name in AXES and observed.get(name) != requested:
            errors.append(
                f"override {name}={requested!r} realized as {observed.get(name)!r}"
            )
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Require the source morphology plus explicit lawful negative controls."""
    errors = self_check(grid)
    if errors:
        return errors
    analysis = _analyze(grid)
    if not 7 <= analysis["height"] <= 9 or not 7 <= analysis["width"] <= 9:
        errors.append("shape is outside the canonical 7..9 by 7..9 envelope")
    target_count = len(analysis["centers"]["target"])
    if not 2 <= target_count <= 3:
        errors.append(f"expected 2..3 true plus centers, found {target_count}")
    if len(analysis["noise"]) > 2:
        errors.append("more than two isolated distractor cells")
    if sum(len(analysis["centers"][name]) for name in _DECOY_KINDS) > 1:
        errors.append("more than one negative-control motif")
    if rule_mirror(grid) == [list(row) for row in grid]:
        errors.append("canonical rule would be an identity")
    return errors


def _centers_far_enough(candidate: tuple[int, int], chosen: Sequence[tuple[int, int]]) -> bool:
    row, col = candidate
    return all(max(abs(row - rr), abs(col - cc)) >= 3 for rr, cc in chosen)


def _place_centers(height: int, width: int, count: int, rng) -> list[tuple[int, int]] | None:
    candidates = [
        (row, col)
        for row in range(1, height - 1)
        for col in range(1, width - 1)
    ]
    rng.shuffle(candidates)
    chosen: list[tuple[int, int]] = []
    for candidate in candidates:
        if _centers_far_enough(candidate, chosen):
            chosen.append(candidate)
            if len(chosen) == count:
                return chosen
    return None


def _target_colors(profile: dict[str, Any], rng) -> list[int]:
    count = profile["target_count"]
    if profile["target_color_mode"] == "unique":
        return rng.sample(list(range(1, 10)), count)
    base = rng.choice(list(range(1, 10)))
    colors = [base, base]
    if count > 2:
        colors.extend(rng.sample([value for value in range(1, 10) if value != base], count - 2))
    rng.shuffle(colors)
    return colors


def _paint_target(grid: list[list[int]], center: tuple[int, int], color: int) -> None:
    row, col = center
    for dr, dc in _CARDINAL:
        grid[row + dr][col + dc] = color


def _paint_decoy(
    grid: list[list[int]],
    center: tuple[int, int],
    kind: str,
    target_colors: Sequence[int],
    rng,
) -> None:
    row, col = center
    base = rng.choice(list(target_colors))
    if kind == "three_plus_one":
        outlier = rng.choice([value for value in range(1, 10) if value != base])
        values = [base, base, base, outlier]
        rng.shuffle(values)
    elif kind == "two_plus_two":
        other = rng.choice([value for value in range(1, 10) if value != base])
        # Vertical pair and horizontal pair are internally equal but disagree.
        values = [base, base, other, other]
    elif kind == "partial":
        values = [base, base, base, 0]
        rng.shuffle(values)
    else:
        raise ValueError(f"unknown decoy kind: {kind!r}")
    for (dr, dc), value in zip(_CARDINAL, values):
        if value:
            grid[row + dr][col + dc] = value


def _place_noise(
    grid: list[list[int]],
    centers: Sequence[tuple[int, int]],
    count: int,
    target_colors: Sequence[int],
    rng,
) -> bool:
    if count == 0:
        return True
    height, width = len(grid), len(grid[0])
    forbidden = {
        (row + dr, col + dc)
        for row, col in centers
        for dr in (-1, 0, 1)
        for dc in (-1, 0, 1)
        if 0 <= row + dr < height and 0 <= col + dc < width
    }
    palette = [value for value in range(1, 10) if value not in set(target_colors)]
    candidates = [
        (row, col)
        for row in range(height)
        for col in range(width)
        if grid[row][col] == 0 and (row, col) not in forbidden
    ]
    rng.shuffle(candidates)
    placed: list[tuple[int, int]] = []
    for row, col in candidates:
        if any(
            0 <= row + dr < height
            and 0 <= col + dc < width
            and grid[row + dr][col + dc] != 0
            for dr, dc in _CARDINAL
        ):
            continue
        if any(abs(row - rr) + abs(col - cc) <= 1 for rr, cc in placed):
            continue
        grid[row][col] = rng.choice(palette)
        placed.append((row, col))
        if len(placed) == count:
            return True
    return count == 0


def generate(seed, sample_index, *, difficulty=None, **overrides):
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise ValueError(f"unknown override(s): {', '.join(unknown)}")
    band = _band(difficulty)
    requested = overrides.get("scene_profile")
    if requested is not None and requested not in _PROFILE_BY_NAME:
        raise ValueError(f"unknown scene_profile: {requested!r}")
    selected = requested or schedule_profile(seed, sample_index, band)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=band,
        overrides=overrides,
    )
    profile_name = ctx.draw_choice("scene_profile", (selected,))
    profile = _PROFILE_BY_NAME[profile_name]
    rng = ctx.draw_rng("scene")
    motif_count = profile["target_count"] + (1 if profile["decoy_kind"] else 0)

    for _attempt in range(240):
        centers = _place_centers(profile["height"], profile["width"], motif_count, rng)
        if centers is None:
            continue
        grid = full_grid(profile["height"], profile["width"], 0)
        colors = _target_colors(profile, rng)
        for center, color in zip(centers[: profile["target_count"]], colors):
            _paint_target(grid, center, color)
        if profile["decoy_kind"]:
            _paint_decoy(
                grid,
                centers[-1],
                profile["decoy_kind"],
                colors,
                rng,
            )
        if not _place_noise(
            grid,
            centers,
            profile["noise_count"],
            colors,
            rng,
        ):
            continue
        analysis = _analyze(grid)
        if analysis["errors"]:
            continue
        if _PROFILE_BY_SIGNATURE.get(analysis["signature"]) != profile_name:
            continue
        if _fires(grid) != set(centers[: profile["target_count"]]):
            continue
        return grid
    raise RuntimeError(f"could not realize scene profile {profile_name!r}")


def _rival_majority_three_nonzero(grid):
    """Fill a zero with the majority color when all four arms are non-zero."""
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            values = [grid[row + dr][col + dc] for dr, dc in _CARDINAL]
            counts = Counter(values)
            color, frequency = counts.most_common(1)[0]
            if all(values) and color != 0 and frequency >= 3:
                output[row][col] = color
    return output


def _rival_opposite_pairs(grid):
    """Fill when vertical arms match and horizontal arms match, even if colors differ."""
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            up, down, left, right = [
                grid[row + dr][col + dc] for dr, dc in _CARDINAL
            ]
            if up != 0 and up == down and left != 0 and left == right:
                output[row][col] = up
    return output


def _rival_three_visible_arms(grid):
    """Fill when at least three visible arms share one non-zero color."""
    output = [list(row) for row in grid]
    height, width = len(grid), len(grid[0])
    for row in range(1, height - 1):
        for col in range(1, width - 1):
            if grid[row][col] != 0:
                continue
            values = [grid[row + dr][col + dc] for dr, dc in _CARDINAL]
            nonzero = [value for value in values if value != 0]
            if len(nonzero) >= 3 and len(set(nonzero)) == 1:
                output[row][col] = nonzero[0]
    return output


def _rival_one_center_per_color(grid):
    """Fill only the first valid center encountered for each arm color."""
    output = [list(row) for row in grid]
    seen: set[int] = set()
    for row, col in sorted(_fires(grid)):
        color = grid[row - 1][col]
        if color in seen:
            continue
        seen.add(color)
        output[row][col] = color
    return output


SEMANTIC_RIVALS: dict[str, Callable[[Any], Any]] = {
    "majority_three_nonzero": _rival_majority_three_nonzero,
    "opposite_pairs": _rival_opposite_pairs,
    "three_visible_arms": _rival_three_visible_arms,
    "one_center_per_color": _rival_one_center_per_color,
}
CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)


def _has_decoy(kind: str):
    def witness(grid) -> bool:
        analysis = _analyze(grid)
        return not analysis["errors"] and bool(analysis["centers"][kind])
    return witness


def _has_repeated_target_color(grid) -> bool:
    analysis = _analyze(grid)
    return not analysis["errors"] and analysis["target_color_mode"] == "repeated"


SEMANTIC_WITNESSES = {
    "three_plus_one_decoy": _has_decoy("three_plus_one"),
    "two_plus_two_decoy": _has_decoy("two_plus_two"),
    "partial_three_arm_decoy": _has_decoy("partial"),
    "repeated_target_color": _has_repeated_target_color,
}
WITNESS_RIVALS = {
    "three_plus_one_decoy": ["majority_three_nonzero"],
    "two_plus_two_decoy": ["opposite_pairs"],
    "partial_three_arm_decoy": ["three_visible_arms"],
    "repeated_target_color": ["one_center_per_color"],
}


def lesson_identifiable(demos, query) -> list[str]:
    """Report any named shortcut that survives the demonstrations."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    if not isinstance(query, dict) or "input" not in query or "output" not in query:
        return ["query must contain input and oracle output"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"demo {index} must contain input and output")
            continue
        if rule_mirror(pair["input"]) != pair["output"]:
            reasons.append(f"demo {index} disagrees with the four-equal-arm rule")
    if rule_mirror(query["input"]) != query["output"]:
        reasons.append("query disagrees with the four-equal-arm rule")
    if reasons:
        return reasons
    for name, competitor in LESSON_COMPETITORS.items():
        survives = all(
            competitor(pair["input"]) == pair["output"] for pair in demos
        )
        if survives and competitor(query["input"]) != query["output"]:
            reasons.append(f"demos do not falsify rival: {name}")
    return reasons
