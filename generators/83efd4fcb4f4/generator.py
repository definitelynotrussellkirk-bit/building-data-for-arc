"""Input sampler for task 83efd4fcb4f4 — fill hollow green-plus centers.

The selected Racket rule is the authority.  This module samples only inputs and
provides independent review hooks: exact observable axes, a Python mirror for
tests, strict validation, semantic witnesses, and finite wrong-rule rivals.
"""
from __future__ import annotations

from collections import deque
from typing import Any, Callable, Sequence

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "83efd4fcb4f4"
TASK_ID = GENERATOR_ID
RULE_HASH = "a8ddd603c662"
VERSION = "3.1.0"
SUMMARY = (
    "On a 0-background, every zero cell whose four cardinal neighbours are "
    "green (3) becomes cyan (8). Inputs contain 1..5 hollow green pluses, "
    "including sparse, overlapping, boundary-adjacent, and near-miss layouts, "
    "plus two small color-6/7 distractor components."
)

INVARIANTS = [
    "1..5 zero centers have all four cardinal neighbours equal to color 3",
    "two monochromatic 4-connected distractor components of colors 6/7 have size 3..4",
    "input colors are only 0,3,6,7; color 8 appears only in the output",
]

AXES = {
    "grid_h": {"type": "int", "default": "scheduled canonical-scale mix", "valid": "8..12"},
    "grid_w": {"type": "int", "default": "scheduled canonical-scale mix", "valid": "9..13"},
    "n_targets": {"type": "int", "default": "scheduled 2|2|5|3|2", "valid": "1..5"},
}
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, Any]] = []

EXAMPLES_NEEDED = 5
MIN_STRICT_FRAC = 1.0
SCHEDULE_PROFILES = ("sparse", "shared", "boundary", "three_arm", "diagonal")
_PROFILE_CYCLE = SCHEDULE_PROFILES
_TARGET_CYCLE = (2, 2, 5, 3, 2)
_SHAPE_CYCLES = {
    "easy": ((8, 10), (8, 11), (9, 10), (9, 12), (10, 11)),
    "medium": ((10, 10), (8, 10), (11, 12), (9, 11), (11, 10)),
    "hard": ((11, 12), (12, 13), (10, 12), (11, 13), (9, 11)),
}

_ALLOWED = frozenset((0, 3, 6, 7))
_CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
_DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))
_DISTRACTOR_SHAPES = (
    ((0, 0), (1, 0), (1, 1)),       # L triomino
    ((0, 0), (0, 1), (0, 2)),       # horizontal triomino
    ((0, 0), (1, 0), (2, 0)),       # vertical triomino
    ((0, 0), (0, 1), (1, 0), (1, 1)),  # square tetromino
    ((0, 0), (1, 0), (2, 0), (2, 1)),  # L tetromino
)

Grid = Sequence[Sequence[int]]
Point = tuple[int, int]


def _difficulty_band(difficulty: Any) -> str:
    if difficulty in (None, "medium"):
        return "medium"
    if difficulty in ("easy", "hard"):
        return str(difficulty)
    raise ValueError("difficulty must be None, 'easy', 'medium', or 'hard'")


def _validate_call(difficulty: Any, overrides: dict[str, Any]) -> None:
    _difficulty_band(difficulty)
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    for name, lo, hi in (("grid_h", 8, 12), ("grid_w", 9, 13), ("n_targets", 1, 5)):
        value = overrides.get(name)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError(f"{name} must be an integer in {lo}..{hi}")
        if not lo <= value <= hi:
            raise ValueError(f"{name} must be in {lo}..{hi}")


def schedule_profile(seed: int, sample_index: int, difficulty: Any = None) -> str:
    """Every consecutive five examples contain every teaching profile once."""
    del seed
    _difficulty_band(difficulty)
    return _PROFILE_CYCLE[int(sample_index) % len(_PROFILE_CYCLE)]


def _scheduled_choice(ctx, label: str, options: Sequence[Any], scheduled: Any) -> Any:
    """Use a full-domain GenCtx draw while deterministically choosing a profile.

    The scheduled value is moved to the index the keyed RNG would choose. This
    preserves complete provenance and exact override behavior without allowing
    curriculum profiles to disappear by chance.
    """
    options = tuple(options)
    if scheduled not in options:
        raise ValueError(f"scheduled value {scheduled!r} not in {label} domain")
    if label in ctx.overrides and ctx.overrides[label] is not None:
        return ctx.draw_choice(label, options)
    selected_index = ctx.draw_rng(label).randrange(len(options))
    remaining = [option for option in options if option != scheduled]
    arranged: list[Any] = [None] * len(options)
    arranged[selected_index] = scheduled
    cursor = 0
    for index, value in enumerate(arranged):
        if value is None:
            arranged[index] = remaining[cursor]
            cursor += 1
    return ctx.draw_choice(label, tuple(arranged))


def _is_rectangular(grid: Any) -> bool:
    return (
        isinstance(grid, (list, tuple))
        and bool(grid)
        and isinstance(grid[0], (list, tuple))
        and bool(grid[0])
        and all(isinstance(row, (list, tuple)) and len(row) == len(grid[0]) for row in grid)
    )


def _true_centers(grid: Grid) -> list[Point]:
    if not _is_rectangular(grid):
        return []
    h, w = len(grid), len(grid[0])
    return [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 0
        and all(grid[r + dr][c + dc] == 3 for dr, dc in _CARDINAL)
    ]


def _arm_cells(center: Point) -> set[Point]:
    r, c = center
    return {(r + dr, c + dc) for dr, dc in _CARDINAL}


def _paint_targets(h: int, w: int, centers: Sequence[Point]) -> list[list[int]]:
    grid = full_grid(h, w, 0)
    for r, c in centers:
        for dr, dc in _CARDINAL:
            grid[r + dr][c + dc] = 3
    return grid


def _has_shared_arm_targets(grid: Grid) -> bool:
    centers = _true_centers(grid)
    return any(
        _arm_cells(left) & _arm_cells(right)
        for index, left in enumerate(centers)
        for right in centers[index + 1 :]
    )


def _has_boundary_target(grid: Grid) -> bool:
    if not _is_rectangular(grid):
        return False
    h, w = len(grid), len(grid[0])
    return any(min(r, c, h - 1 - r, w - 1 - c) == 1 for r, c in _true_centers(grid))


def _cardinal_three_count(grid: Grid, r: int, c: int) -> int:
    h, w = len(grid), len(grid[0])
    return sum(
        0 <= r + dr < h and 0 <= c + dc < w and grid[r + dr][c + dc] == 3
        for dr, dc in _CARDINAL
    )


def _has_three_arm_decoy(grid: Grid) -> bool:
    if not _is_rectangular(grid):
        return False
    h, w = len(grid), len(grid[0])
    return any(
        grid[r][c] == 0 and _cardinal_three_count(grid, r, c) == 3
        for r in range(1, h - 1)
        for c in range(1, w - 1)
    )


def _has_diagonal_decoy(grid: Grid) -> bool:
    if not _is_rectangular(grid):
        return False
    h, w = len(grid), len(grid[0])
    return any(
        grid[r][c] == 0
        and all(grid[r + dr][c + dc] == 3 for dr, dc in _DIAGONAL)
        and _cardinal_three_count(grid, r, c) < 4
        for r in range(1, h - 1)
        for c in range(1, w - 1)
    )


def _target_layout(h: int, w: int, n_targets: int, profile: str, rng) -> tuple[list[list[int]], set[Point]]:
    candidates = [(r, c) for r in range(1, h - 1) for c in range(1, w - 1)]
    boundary_candidates = [
        point
        for point in candidates
        if min(point[0], point[1], h - 1 - point[0], w - 1 - point[1]) == 1
    ]
    shared_pairs = [
        pair
        for r in range(1, h - 2)
        for c in range(1, w - 2)
        for pair in (((r, c), (r + 1, c + 1)), ((r, c + 1), (r + 1, c)))
    ]

    for _attempt in range(1024):
        forced: list[Point] = []
        if profile in ("shared", "three_arm") and n_targets >= 2:
            forced = list(rng.choice(shared_pairs))
        elif profile in ("boundary", "diagonal"):
            forced = [rng.choice(boundary_candidates)]

        available = [point for point in candidates if point not in forced]
        if profile == "sparse":
            chosen = list(forced)
            while len(chosen) < n_targets:
                options = [point for point in available if point not in chosen]
                scored = sorted(
                    options,
                    key=lambda point: min(
                        (
                            max(abs(point[0] - other[0]), abs(point[1] - other[1]))
                            for other in chosen
                        ),
                        default=99,
                    ),
                    reverse=True,
                )
                top = max(1, len(scored) // 4)
                chosen.append(rng.choice(scored[:top]))
        else:
            chosen = forced + rng.sample(available, n_targets - len(forced))

        if len(set(chosen)) != n_targets:
            continue
        grid = _paint_targets(h, w, chosen)
        if set(_true_centers(grid)) != set(chosen):
            continue
        if profile in ("shared", "three_arm") and n_targets >= 2 and not _has_shared_arm_targets(grid):
            continue
        if profile in ("boundary", "diagonal") and not _has_boundary_target(grid):
            continue
        return grid, set(chosen)

    raise RuntimeError(
        f"could not place {n_targets} exact plus targets for {profile} at {h}x{w}"
    )


def _add_three_arm_decoy(
    grid: list[list[int]], targets: set[Point], rng, *, forbidden: set[Point] | None = None
) -> tuple[list[list[int]], Point]:
    h, w = len(grid), len(grid[0])
    forbidden = set(forbidden or ())
    candidates = [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 0 and (r, c) not in targets and (r, c) not in forbidden
    ]
    rng.shuffle(candidates)
    for center in candidates:
        missing_options = list(_CARDINAL)
        rng.shuffle(missing_options)
        for missing in missing_options:
            cells = [
                (center[0] + dr, center[1] + dc)
                for dr, dc in _CARDINAL
                if (dr, dc) != missing
            ]
            if any(grid[r][c] != 0 for r, c in cells) or set(cells) & forbidden:
                continue
            candidate = [row[:] for row in grid]
            for r, c in cells:
                candidate[r][c] = 3
            if set(_true_centers(candidate)) == targets and _has_three_arm_decoy(candidate):
                return candidate, center
    raise RuntimeError("could not place a three-arm decoy without changing target count")


def _add_diagonal_decoy(
    grid: list[list[int]], targets: set[Point], rng, *, forbidden: set[Point] | None = None
) -> tuple[list[list[int]], Point]:
    h, w = len(grid), len(grid[0])
    forbidden = set(forbidden or ())
    candidates = [
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if grid[r][c] == 0 and (r, c) not in targets and (r, c) not in forbidden
    ]
    rng.shuffle(candidates)
    for center in candidates:
        cells = [(center[0] + dr, center[1] + dc) for dr, dc in _DIAGONAL]
        if any(grid[r][c] != 0 for r, c in cells) or set(cells) & forbidden:
            continue
        candidate = [row[:] for row in grid]
        for r, c in cells:
            candidate[r][c] = 3
        if set(_true_centers(candidate)) == targets and _has_diagonal_decoy(candidate):
            return candidate, center
    raise RuntimeError("could not place a diagonal decoy without changing target count")


def _add_green_clutter(
    grid: list[list[int]], targets: set[Point], reserved: set[Point], count: int, rng
) -> list[list[int]]:
    result = [row[:] for row in grid]
    for _ in range(count):
        candidates = [
            (r, c)
            for r in range(len(result))
            for c in range(len(result[0]))
            if result[r][c] == 0 and (r, c) not in targets and (r, c) not in reserved
        ]
        rng.shuffle(candidates)
        for r, c in candidates:
            candidate = [row[:] for row in result]
            candidate[r][c] = 3
            if set(_true_centers(candidate)) == targets:
                result = candidate
                break
    return result


def _shape_placements(
    grid: Grid,
    shape: Sequence[Point],
    reserved: set[Point],
    prior_component: set[Point],
) -> list[set[Point]]:
    h, w = len(grid), len(grid[0])
    max_r = max(r for r, _ in shape)
    max_c = max(c for _, c in shape)
    placements: list[set[Point]] = []
    for base_r in range(h - max_r):
        for base_c in range(w - max_c):
            cells = {(base_r + r, base_c + c) for r, c in shape}
            if cells & reserved or any(grid[r][c] != 0 for r, c in cells):
                continue
            if any(
                (r + dr, c + dc) in prior_component
                for r, c in cells
                for dr, dc in _CARDINAL
            ):
                continue
            placements.append(cells)
    return placements


def _place_distractors(grid: list[list[int]], reserved: set[Point], rng) -> list[list[int]]:
    for _attempt in range(256):
        candidate = [row[:] for row in grid]
        occupied: set[Point] = set()
        colors = (6, 7) if rng.randrange(5) < 2 else (6, 6)
        success = True
        for color in colors:
            shape = rng.choice(_DISTRACTOR_SHAPES)
            placements = _shape_placements(candidate, shape, reserved, occupied)
            if not placements:
                success = False
                break
            cells = rng.choice(placements)
            for r, c in cells:
                candidate[r][c] = color
            occupied.update(cells)
        if success:
            return candidate
    raise RuntimeError("could not place two separated distractor components")


def generate(seed, sample_index, *, difficulty=None, **overrides):
    """Construct a deterministic input while honoring all exact axes."""
    _validate_call(difficulty, overrides)
    band = _difficulty_band(difficulty)
    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )

    scheduled_h, scheduled_w = _SHAPE_CYCLES[band][int(sample_index) % 5]
    h = int(_scheduled_choice(ctx, "grid_h", tuple(range(8, 13)), scheduled_h))
    w = int(_scheduled_choice(ctx, "grid_w", tuple(range(9, 14)), scheduled_w))
    scheduled_targets = _TARGET_CYCLE[int(sample_index) % len(_TARGET_CYCLE)]
    n_targets = int(
        _scheduled_choice(ctx, "n_targets", tuple(range(1, 6)), scheduled_targets)
    )
    profile = schedule_profile(seed, sample_index, difficulty)

    expected = {"grid_h": h, "grid_w": w, "n_targets": n_targets}
    last_error = "no construction attempted"
    for attempt in range(256):
        try:
            grid, targets = _target_layout(
                h,
                w,
                n_targets,
                profile,
                ctx.draw_rng(f"target_layout:{profile}:{attempt}"),
            )
            reserved: set[Point] = set(targets)
            # Redundant teaching evidence makes any five-of-six query rotation safe:
            # each finite rival is refuted by at least two profiles in every cycle.
            if profile in ("sparse", "three_arm"):
                grid, decoy_center = _add_three_arm_decoy(
                    grid,
                    targets,
                    ctx.draw_rng(f"three_arm_decoy:{attempt}"),
                    forbidden=reserved,
                )
                reserved.add(decoy_center)
            if profile in ("sparse", "shared", "boundary", "diagonal"):
                grid, decoy_center = _add_diagonal_decoy(
                    grid,
                    targets,
                    ctx.draw_rng(f"diagonal_decoy:{attempt}"),
                    forbidden=reserved,
                )
                reserved.add(decoy_center)

            clutter_base = {"easy": 0, "medium": 1, "hard": 2}[band]
            clutter_rng = ctx.draw_rng(f"green_clutter:{attempt}")
            grid = _add_green_clutter(
                grid,
                targets,
                reserved,
                clutter_base + clutter_rng.randrange(2),
                clutter_rng,
            )
            grid = _place_distractors(
                grid, reserved, ctx.draw_rng(f"distractors:{attempt}")
            )

            errors = self_check(grid, difficulty=difficulty)
            if errors:
                raise RuntimeError("constructed invalid grid: " + "; ".join(errors))
            observed = observe_overrides(grid)
            if observed != expected:
                raise RuntimeError(
                    f"exact-axis drift: expected {expected}, observed {observed}"
                )
            required: list[Callable[[Grid], bool]] = []
            if profile in ("shared", "three_arm") and n_targets >= 2:
                required.append(_has_shared_arm_targets)
            if profile in ("boundary", "diagonal"):
                required.append(_has_boundary_target)
            if profile in ("sparse", "three_arm"):
                required.append(_has_three_arm_decoy)
            if profile in ("sparse", "shared", "boundary", "diagonal"):
                required.append(_has_diagonal_decoy)
            if any(not predicate(grid) for predicate in required):
                raise RuntimeError(
                    f"profile {profile!r} lost required semantic evidence"
                )
            return [row[:] for row in grid]
        except RuntimeError as exc:
            last_error = str(exc)

    raise RuntimeError(
        f"could not construct {profile!r} at {h}x{w} with "
        f"n_targets={n_targets} after 256 attempts: {last_error}"
    )


def _distractor_components(grid: Grid) -> list[list[tuple[int, int, int]]]:
    if not _is_rectangular(grid):
        return []
    h, w = len(grid), len(grid[0])
    seen: set[Point] = set()
    components: list[list[tuple[int, int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in (6, 7) or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            component: list[tuple[int, int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                component.append((rr, cc, int(grid[rr][cc])))
                for dr, dc in _CARDINAL:
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] in (6, 7)
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)
    return components


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the reviewed task manifold, including all canonical inputs."""
    del meta
    if not _is_rectangular(grid):
        return ["expected a nonempty rectangular grid"]
    errors: list[str] = []
    try:
        _difficulty_band(difficulty)
    except ValueError as exc:
        errors.append(str(exc))

    h, w = len(grid), len(grid[0])
    if not (8 <= h <= 12 and 9 <= w <= 13):
        errors.append(f"shape {h}x{w} outside 8..12 by 9..13")

    values = [value for row in grid for value in row]
    bad_cells = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if isinstance(value, bool) or not isinstance(value, int) or value not in _ALLOWED
    ]
    if bad_cells:
        r, c, value = bad_cells[0]
        errors.append(f"cell ({r},{c})={value!r}; input colors must be integer 0,3,6,7")
        return errors

    targets = _true_centers(grid)
    if not 1 <= len(targets) <= 5:
        errors.append(f"expected 1..5 hollow green-plus centers, found {len(targets)}")
    if values.count(3) < 4:
        errors.append("expected at least four color-3 arm cells")
    if 6 not in values:
        errors.append("expected color 6 in the distractor palette")

    components = _distractor_components(grid)
    if len(components) != 2:
        errors.append(f"expected exactly two color-6/7 distractor components, found {len(components)}")
    for index, component in enumerate(components):
        if not 3 <= len(component) <= 4:
            errors.append(
                f"distractor component {index} has size {len(component)}; expected 3..4"
            )
        colors = {value for _, _, value in component}
        if len(colors) != 1:
            errors.append(f"distractor component {index} mixes colors {sorted(colors)}")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """Lawful inputs in the declared reviewed manifold."""
    return self_check(grid)


def observe_overrides(grid) -> dict[str, int]:
    errors = self_check(grid)
    if errors:
        raise ValueError("cannot observe overrides: " + "; ".join(errors))
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_targets": len(_true_centers(grid)),
    }


def rule_mirror(grid: Grid) -> list[list[int]]:
    """Python mirror used only by review tests; Racket remains authoritative."""
    out = [list(row) for row in grid]
    for r, c in _true_centers(grid):
        out[r][c] = 8
    return out


def _at_least_three_arms_rival(grid: Grid) -> list[list[int]]:
    """Wrong: fills a missing-arm near miss as though three arms were enough."""
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] == 0 and _cardinal_three_count(grid, r, c) >= 3:
                out[r][c] = 8
    return out


def _cardinal_or_diagonal_rival(grid: Grid) -> list[list[int]]:
    """Wrong: accepts either a cardinal plus or a diagonal X."""
    out = rule_mirror(grid)
    h, w = len(grid), len(grid[0])
    for r in range(1, h - 1):
        for c in range(1, w - 1):
            if grid[r][c] == 0 and all(
                grid[r + dr][c + dc] == 3 for dr, dc in _DIAGONAL
            ):
                out[r][c] = 8
    return out


def _separated_targets_only_rival(grid: Grid) -> list[list[int]]:
    """Wrong: treats overlapping pluses as one noisy object and skips them."""
    centers = _true_centers(grid)
    out = [list(row) for row in grid]
    for center in centers:
        if not any(
            _arm_cells(center) & _arm_cells(other)
            for other in centers
            if other != center
        ):
            r, c = center
            out[r][c] = 8
    return out


def _margin_two_only_rival(grid: Grid) -> list[list[int]]:
    """Wrong: scans only cells at least two positions from every border."""
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for r, c in _true_centers(grid):
        if min(r, c, h - 1 - r, w - 1 - c) >= 2:
            out[r][c] = 8
    return out


SEMANTIC_RIVALS: dict[str, Callable[[Grid], list[list[int]]]] = {
    "at_least_three_arms": _at_least_three_arms_rival,
    "cardinal_or_diagonal": _cardinal_or_diagonal_rival,
    "separated_targets_only": _separated_targets_only_rival,
    "margin_two_only": _margin_two_only_rival,
}
LESSON_COMPETITORS = dict(SEMANTIC_RIVALS)
# Every public canonical pair lacks a diagonal-X counterexample, so this wrong
# overgeneralization is genuinely canonical-ambiguous and must be refuted by
# the generated diagonal-decoy profile.
CANONICAL_SHORTCUTS: dict[str, Callable[[Grid], list[list[int]]]] = {
    "cardinal_or_diagonal": _cardinal_or_diagonal_rival,
}


def _witness(predicate: Callable[[Grid], bool], rival_name: str):
    rival = SEMANTIC_RIVALS[rival_name]

    def checked(grid: Grid) -> bool:
        return not self_check(grid) and predicate(grid) and rival(grid) != rule_mirror(grid)

    return checked


SEMANTIC_WITNESSES = {
    "shared_arm_targets": _witness(_has_shared_arm_targets, "separated_targets_only"),
    "boundary_target": _witness(_has_boundary_target, "margin_two_only"),
    "three_arm_decoy": _witness(_has_three_arm_decoy, "at_least_three_arms"),
    "diagonal_decoy": _witness(_has_diagonal_decoy, "cardinal_or_diagonal"),
}
WITNESS_RIVALS = {
    "shared_arm_targets": ["separated_targets_only"],
    "boundary_target": ["margin_two_only"],
    "three_arm_decoy": ["at_least_three_arms"],
    "diagonal_decoy": ["cardinal_or_diagonal"],
}


def _pair_errors(pair: Any, label: str, *, output_optional: bool = False) -> list[str]:
    if not isinstance(pair, dict) or "input" not in pair:
        return [f"{label} must contain an input grid"]
    errors = self_check(pair["input"])
    if errors:
        return [f"{label} input: {error}" for error in errors]
    if "output" not in pair:
        return [] if output_optional else [f"{label} must contain an output grid"]
    if pair["output"] != rule_mirror(pair["input"]):
        return [f"{label} output does not match the hollow-plus rule"]
    return []


def lesson_identifiable(demos, query) -> list[str]:
    """Finite-rival diagnostic for a generated five-demonstration lesson."""
    if not isinstance(demos, (list, tuple)) or len(demos) < EXAMPLES_NEEDED:
        return [f"need at least {EXAMPLES_NEEDED} demonstrations"]
    reasons: list[str] = []
    for index, pair in enumerate(demos):
        reasons.extend(_pair_errors(pair, f"demo {index}"))
    reasons.extend(_pair_errors(query, "query", output_optional=True))
    if reasons:
        return reasons

    for name, witness in SEMANTIC_WITNESSES.items():
        if not any(witness(pair["input"]) for pair in demos):
            reasons.append(f"demonstrations omit semantic witness {name!r}")
    for name, competitor in LESSON_COMPETITORS.items():
        if all(competitor(pair["input"]) == pair["output"] for pair in demos):
            reasons.append(f"competitor {name!r} fits every demonstration")
    return reasons
