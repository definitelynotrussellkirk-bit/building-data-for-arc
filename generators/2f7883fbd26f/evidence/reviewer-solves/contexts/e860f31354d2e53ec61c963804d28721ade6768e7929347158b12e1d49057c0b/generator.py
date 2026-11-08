"""Generator for ARC task 1fad071e / content hash 2f7883fbd26f.

Intended rule
-------------
Count every sliding 2 x 2 window whose four cells are color 1, then encode the
count as a length-five bar (ones followed by zeros).  Color-2 blocks and
isolated cells are distractors.

The public examples contain only separated 2 x 2 target objects.  That leaves a
strong shortcut: count qualifying connected components instead of sliding
windows.  Ordinary lessons use a three-slot cycle with two 2 x (n + 1) overlap strips
and one canonical-separated profile.  A strip has n target windows but only one
qualifying component, so every two-demo lesson and every query rotation of a
three-pair lesson refutes the shortcut while retaining canonical-shaped support.
"""
from __future__ import annotations

from collections.abc import Callable

from puzzle_generators.base import gen_ctx
from puzzle_generators.helpers.grid import full_grid

GENERATOR_ID = "2f7883fbd26f"
TASK_ID = "2f7883fbd26f"
RULE_HASH = "6de5b0b7a0a5"
VERSION = "2.0.0"
EXPECTED_OUTPUT_CODOMAIN = 6
EXAMPLES_NEEDED = 2
MIN_STRICT_FRAC = 0.95

SUMMARY = (
    "Canonical-scale 0/1/2 grid with color-1 target windows, color-2 decoy "
    "blocks, and isolated noise. Count every sliding 2x2 all-1 window and "
    "encode the count as a 1x5 bar. A three-slot lesson cycle contains two "
    "overlap counterexamples and one separated canonical-shaped scene."
)

INVARIANTS = [
    "input dimensions are 9..12 and the palette is exactly {0,1,2}",
    "0..5 sliding 2x2 all-1 target windows",
    "1..4 separated 2x2 all-2 decoy blocks",
    "1..4 isolated color-1 cells and 0..4 isolated color-2 cells",
    "every default two-demo lesson and every three-pair query rotation contains an overlap counterexample",
]

AXES = {
    "grid_h": {
        "type": "int",
        "default": "difficulty-weighted choice in 9..12",
        "valid": "9..12",
        "doc": "Input-grid height.",
    },
    "grid_w": {
        "type": "int",
        "default": "difficulty-weighted choice in 9..12",
        "valid": "9..12",
        "doc": "Input-grid width.",
    },
    "n_target_blocks": {
        "type": "int",
        "default": "schedule-weighted 0..5; overlap lessons use 2..5",
        "valid": "0..5",
        "doc": "Exact number of sliding 2x2 all-1 windows.",
    },
    "n_decoy_blocks": {
        "type": "int",
        "default": "rng 2..4; exact overrides also admit 1",
        "valid": "1..4",
        "doc": "Exact number of separated 2x2 all-2 windows.",
    },
    "n_singleton_ones": {
        "type": "int",
        "default": "rng 2..4; exact overrides also admit 1",
        "valid": "1..4",
        "doc": "Exact number of isolated color-1 components.",
    },
    "n_singleton_twos": {
        "type": "int",
        "default": "rng 0..4",
        "valid": "0..4",
        "doc": "Exact number of isolated color-2 components.",
    },
}

# The constructor accepts the full Cartesian product; declaring the empty list
# opts the override checker into strict rejection classification.
INCOMPATIBLE_OVERRIDE_COMBINATIONS: list[dict[str, object]] = []

SCHEDULE_PROFILES = ("canonical_separated", "overlap_counterexample")
SCHEDULE_ROLES = (
    "overlap_counterexample",
    "overlap_counterexample",
    "canonical_separated",
)
SCHEDULE_PERIOD = len(SCHEDULE_ROLES)


def schedule_profile(seed: int, sample_index: int, difficulty=None) -> str:
    """Three-slot role cycle; seed/difficulty affect scene content only."""
    del seed, difficulty
    return SCHEDULE_ROLES[int(sample_index) % SCHEDULE_PERIOD]


def _count_windows(grid: list[list[int]], color: int) -> int:
    if not grid or not grid[0]:
        return 0
    return sum(
        all(grid[r + dr][c + dc] == color for dr in (0, 1) for dc in (0, 1))
        for r in range(len(grid) - 1)
        for c in range(len(grid[0]) - 1)
    )


def _window_anchors(grid: list[list[int]], color: int) -> list[tuple[int, int]]:
    if not grid or not grid[0]:
        return []
    return [
        (r, c)
        for r in range(len(grid) - 1)
        for c in range(len(grid[0]) - 1)
        if all(grid[r + dr][c + dc] == color for dr in (0, 1) for dc in (0, 1))
    ]


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = remaining.pop()
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        components.append(component)
    return components


def _is_filled_rectangle(component: set[tuple[int, int]]) -> tuple[bool, int, int]:
    rows = [r for r, _ in component]
    cols = [c for _, c in component]
    h = max(rows) - min(rows) + 1
    w = max(cols) - min(cols) + 1
    expected = {
        (r, c)
        for r in range(min(rows), max(rows) + 1)
        for c in range(min(cols), max(cols) + 1)
    }
    return component == expected, h, w


def _singleton_count(grid: list[list[int]], color: int) -> int:
    return sum(len(component) == 1 for component in _components(grid, color))


def _encode_bar(count: int) -> list[list[int]]:
    if not 0 <= count <= 5:
        raise ValueError(f"target-window count {count} outside encodable range 0..5")
    return [[1] * count + [0] * (5 - count)]


def _reference_output(grid: list[list[int]]) -> list[list[int]]:
    """Pure Python mirror used by tests/audit hooks, never as rule authority."""
    return _encode_bar(_count_windows(grid, 1))


def _qualifying_component_count(grid: list[list[int]]) -> int:
    """Wrong rival: count color-1 components containing any 2x2 window."""
    anchors = _window_anchors(grid, 1)
    window_cells = [
        {(r + dr, c + dc) for dr in (0, 1) for dc in (0, 1)}
        for r, c in anchors
    ]
    return sum(
        any(cells <= component for cells in window_cells)
        for component in _components(grid, 1)
    )


def _exact_square_component_count(grid: list[list[int]]) -> int:
    """Wrong rival: count isolated color-1 components that are exactly 2x2."""
    count = 0
    for component in _components(grid, 1):
        if len(component) != 4:
            continue
        rectangle, h, w = _is_filled_rectangle(component)
        count += rectangle and (h, w) == (2, 2)
    return int(count)


def _rival_count_qualifying_components(grid: list[list[int]]) -> list[list[int]]:
    return _encode_bar(_qualifying_component_count(grid))


def _rival_count_exact_square_components(grid: list[list[int]]) -> list[list[int]]:
    return _encode_bar(_exact_square_component_count(grid))


SEMANTIC_RIVALS: dict[str, Callable[[list[list[int]]], list[list[int]]]] = {
    "count_qualifying_one_components": _rival_count_qualifying_components,
    "count_exact_2x2_one_components": _rival_count_exact_square_components,
}
LESSON_COMPETITORS = SEMANTIC_RIVALS
CANONICAL_SHORTCUTS = SEMANTIC_RIVALS


def _has_overlapping_target_windows(grid: list[list[int]]) -> bool:
    return _count_windows(grid, 1) > _qualifying_component_count(grid)


SEMANTIC_WITNESSES: dict[str, Callable[[list[list[int]]], bool]] = {
    "overlapping_target_windows": _has_overlapping_target_windows,
}
WITNESS_RIVALS = {
    "overlapping_target_windows": list(SEMANTIC_RIVALS),
}


def _draw_int_axis(ctx, name: str, lo: int, hi: int, defaults: list[int]) -> int:
    """Accept the full declared domain while using a narrower default support."""
    if name in ctx.overrides and ctx.overrides[name] is not None:
        return ctx.draw_int_strict(name, lo, hi)
    return int(ctx.draw_choice(name, defaults))


def _dimension_defaults(difficulty) -> list[int]:
    # Every band keeps substantial exact 9x9 canonical-profile support while
    # still exploring the declared 10..12 extension.
    if difficulty == "easy":
        return [9, 9, 9, 9, 9, 9, 10, 11, 12]
    if difficulty == "medium":
        return [9, 9, 9, 9, 9, 10, 10, 11, 12]
    if difficulty == "hard":
        return [9, 9, 9, 9, 9, 10, 11, 12, 12]
    return [9, 9, 9, 9, 9, 10, 11, 12]


def _paint_block(grid: list[list[int]], anchor: tuple[int, int], color: int) -> None:
    r, c = anchor
    for dr in (0, 1):
        for dc in (0, 1):
            grid[r + dr][c + dc] = color


def _slot_anchors(h: int, w: int) -> list[tuple[int, int]]:
    return [(r, c) for r in range(0, h - 1, 3) for c in range(0, w - 1, 3)]


def _place_separated_blocks(
    grid: list[list[int]],
    n_target: int,
    n_decoy: int,
    rng,
) -> None:
    slots = _slot_anchors(len(grid), len(grid[0]))
    rng.shuffle(slots)
    needed = n_target + n_decoy
    if len(slots) < needed:
        raise RuntimeError(f"need {needed} separated slots, found {len(slots)}")
    for anchor in slots[:n_target]:
        _paint_block(grid, anchor, 1)
    for anchor in slots[n_target:needed]:
        _paint_block(grid, anchor, 2)


def _overlap_cells(
    h: int,
    w: int,
    n_target: int,
    rng,
) -> set[tuple[int, int]]:
    if n_target == 0:
        return set()
    orientations = ["horizontal", "vertical"]
    rng.shuffle(orientations)
    orientation = orientations[0]
    if orientation == "horizontal":
        strip_h, strip_w = 2, n_target + 1
    else:
        strip_h, strip_w = n_target + 1, 2
    r0 = rng.randrange(h - strip_h + 1)
    c0 = rng.randrange(w - strip_w + 1)
    return {
        (r, c)
        for r in range(r0, r0 + strip_h)
        for c in range(c0, c0 + strip_w)
    }


def _place_overlap_and_decoys(
    grid: list[list[int]],
    n_target: int,
    n_decoy: int,
    rng,
) -> None:
    h, w = len(grid), len(grid[0])
    target_cells = _overlap_cells(h, w, n_target, rng)
    for r, c in target_cells:
        grid[r][c] = 1

    slots = []
    for anchor in _slot_anchors(h, w):
        r, c = anchor
        cells = {(r + dr, c + dc) for dr in (0, 1) for dc in (0, 1)}
        if cells.isdisjoint(target_cells):
            slots.append(anchor)
    rng.shuffle(slots)
    if len(slots) < n_decoy:
        raise RuntimeError(f"need {n_decoy} decoy slots, found {len(slots)}")
    for anchor in slots[:n_decoy]:
        _paint_block(grid, anchor, 2)


def _isolated_candidate(grid: list[list[int]], r: int, c: int, color: int) -> bool:
    if grid[r][c] != 0:
        return False
    h, w = len(grid), len(grid[0])
    return all(
        not (0 <= r + dr < h and 0 <= c + dc < w)
        or grid[r + dr][c + dc] != color
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))
    )


def _add_isolated_cells(grid: list[list[int]], color: int, count: int, rng) -> bool:
    if count == 0:
        return True
    candidates = [
        (r, c)
        for r in range(len(grid))
        for c in range(len(grid[0]))
        if grid[r][c] == 0
    ]
    rng.shuffle(candidates)
    placed = 0
    for r, c in candidates:
        if not _isolated_candidate(grid, r, c, color):
            continue
        grid[r][c] = color
        placed += 1
        if placed == count:
            return True
    return placed == count


def _construct_grid(
    h: int,
    w: int,
    n_target: int,
    n_decoy: int,
    n_singleton_ones: int,
    n_singleton_twos: int,
    profile: str,
    rng,
) -> list[list[int]]:
    for _ in range(128):
        grid = full_grid(h, w, 0)
        if profile == "canonical_separated":
            _place_separated_blocks(grid, n_target, n_decoy, rng)
        elif profile == "overlap_counterexample":
            _place_overlap_and_decoys(grid, n_target, n_decoy, rng)
        else:
            raise ValueError(f"unknown schedule profile: {profile!r}")

        if not _add_isolated_cells(grid, 1, n_singleton_ones, rng):
            continue
        if not _add_isolated_cells(grid, 2, n_singleton_twos, rng):
            continue
        observed = observe_overrides(grid)
        expected = {
            "grid_h": h,
            "grid_w": w,
            "n_target_blocks": n_target,
            "n_decoy_blocks": n_decoy,
            "n_singleton_ones": n_singleton_ones,
            "n_singleton_twos": n_singleton_twos,
        }
        if observed != expected:
            continue
        if self_check(grid):
            continue
        return grid
    raise RuntimeError(
        "could not construct exact block/noise grammar after 128 deterministic attempts"
    )


def generate(seed, sample_index, *, difficulty=None, **overrides):
    if type(seed) is not int or seed < 0:
        raise ValueError(f"seed must be a nonnegative literal integer, got {seed!r}")
    if type(sample_index) is not int or sample_index < 0:
        raise ValueError(
            f"sample_index must be a nonnegative literal integer, got {sample_index!r}"
        )
    unknown = sorted(set(overrides) - set(AXES))
    if unknown:
        raise TypeError(f"unknown override(s): {', '.join(unknown)}")
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(
            f"difficulty must be one of None/easy/medium/hard, got {difficulty!r}"
        )

    ctx = gen_ctx(
        seed=seed,
        sample_index=sample_index,
        version=VERSION,
        task_id=TASK_ID,
        difficulty=difficulty,
        overrides=overrides,
    )
    profile = schedule_profile(seed, sample_index, difficulty)
    dim_defaults = _dimension_defaults(difficulty)
    h = _draw_int_axis(ctx, "grid_h", 9, 12, dim_defaults)
    w = _draw_int_axis(ctx, "grid_w", 9, 12, list(reversed(dim_defaults)))
    target_defaults = (
        [0, 1, 2, 3, 4, 5]
        if profile == "canonical_separated"
        else [2, 3, 4, 5]
    )
    n_target = _draw_int_axis(ctx, "n_target_blocks", 0, 5, target_defaults)
    n_decoy = _draw_int_axis(ctx, "n_decoy_blocks", 1, 4, [2, 3, 4])
    n_singleton_ones = _draw_int_axis(ctx, "n_singleton_ones", 1, 4, [2, 3, 4])
    n_singleton_twos = _draw_int_axis(ctx, "n_singleton_twos", 0, 4, [0, 1, 2, 3, 4])
    return _construct_grid(
        h,
        w,
        n_target,
        n_decoy,
        n_singleton_ones,
        n_singleton_twos,
        profile,
        ctx.draw_rng("construction"),
    )


def observe_overrides(grid) -> dict[str, int]:
    """Recover all exact public axes from a returned grid."""
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_target_blocks": _count_windows(grid, 1),
        "n_decoy_blocks": _count_windows(grid, 2),
        "n_singleton_ones": _singleton_count(grid, 1),
        "n_singleton_twos": _singleton_count(grid, 2),
    }


def self_check(grid, *, difficulty=None, meta=None) -> list[str]:
    """Validate the canonical-anchored constructive lesson grammar."""
    del difficulty, meta
    errors: list[str] = []
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        return ["grid must be a non-empty 2D list"]
    h, w = len(grid), len(grid[0])
    if any(not isinstance(row, list) or len(row) != w for row in grid):
        return ["grid rows must be rectangular"]
    if not (9 <= h <= 12 and 9 <= w <= 12):
        errors.append(f"expected dimensions 9..12 x 9..12, got {h}x{w}")

    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if (
                not isinstance(value, int)
                or isinstance(value, bool)
                or value not in (0, 1, 2)
            ):
                errors.append(f"cell ({r},{c}) has invalid task color {value!r}")
    if errors:
        return errors

    palette = {value for row in grid for value in row}
    if palette != {0, 1, 2}:
        errors.append(f"expected exact palette [0, 1, 2], got {sorted(palette)}")

    counts = {
        color: sum(value == color for row in grid for value in row)
        for color in (0, 1, 2)
    }
    if counts[0] <= max(counts[1], counts[2]):
        errors.append(
            f"background 0 must be the unique most frequent color, got {counts}"
        )

    n_target = _count_windows(grid, 1)
    n_decoy = _count_windows(grid, 2)
    if not 0 <= n_target <= 5:
        errors.append(f"target-window count {n_target} outside 0..5")
    if not 1 <= n_decoy <= 4:
        errors.append(f"decoy-window count {n_decoy} outside 1..4")

    components_one = _components(grid, 1)
    components_two = _components(grid, 2)
    singleton_ones = sum(len(component) == 1 for component in components_one)
    singleton_twos = sum(len(component) == 1 for component in components_two)
    if not 1 <= singleton_ones <= 4:
        errors.append(f"isolated color-1 count {singleton_ones} outside 1..4")
    if not 0 <= singleton_twos <= 4:
        errors.append(f"isolated color-2 count {singleton_twos} outside 0..4")

    for index, component in enumerate(components_one):
        if len(component) == 1:
            continue
        rectangle, ch, cw = _is_filled_rectangle(component)
        if not rectangle or min(ch, cw) != 2 or max(ch, cw) > 6:
            errors.append(
                f"color-1 component {index} must be a filled 2xk/kx2 strip with 2<=k<=6"
            )
    for index, component in enumerate(components_two):
        if len(component) == 1:
            continue
        rectangle, ch, cw = _is_filled_rectangle(component)
        if not rectangle or (ch, cw) != (2, 2):
            errors.append(f"color-2 component {index} must be an isolated filled 2x2 block")
    return errors


def strict_canonical_like(grid) -> list[str]:
    """The strict teaching domain: canonical palette/morphology plus overlap strips."""
    return self_check(grid)


def lesson_identifiable(demos, query) -> list[str]:
    """Require labelled demos to refute every named canonical-fitting shortcut."""
    if not isinstance(demos, list) or not demos:
        return ["at least one demonstration is required"]
    reasons: list[str] = []
    pairs = [*demos, query]
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            reasons.append(f"pair {index} is missing input/output")
            continue
        try:
            expected = _reference_output(pair["input"])
        except Exception as exc:  # malformed pair should be loud, not crash gate
            reasons.append(f"pair {index} reference evaluation raised {exc!r}")
            continue
        if pair["output"] != expected:
            reasons.append(f"pair {index} output disagrees with sliding-window count")

    if reasons:
        return reasons
    for name, rival in LESSON_COMPETITORS.items():
        survives = all(rival(demo["input"]) == demo["output"] for demo in demos)
        if survives:
            rival_query = rival(query["input"])
            if rival_query != query["output"]:
                reasons.append(f"demonstrations do not refute rival: {name}")
            else:
                reasons.append(f"rival remains answer-equivalent on query: {name}")
    return reasons


def mutation_fixtures():
    """Must-reject impostors for self-check mutation-sensitivity evidence."""
    valid = generate(
        91001,
        0,
        grid_h=9,
        grid_w=9,
        n_target_blocks=3,
        n_decoy_blocks=2,
        n_singleton_ones=2,
        n_singleton_twos=1,
    )
    missing_color_two = [row[:] for row in valid]
    for row in missing_color_two:
        for c, value in enumerate(row):
            if value == 2:
                row[c] = 0

    solid_three = full_grid(9, 9, 0)
    for r in range(3):
        for c in range(3):
            solid_three[r][c] = 1
    _paint_block(solid_three, (4, 4), 2)
    solid_three[8][8] = 1

    no_one_singleton = [row[:] for row in valid]
    for component in _components(no_one_singleton, 1):
        if len(component) == 1:
            r, c = next(iter(component))
            no_one_singleton[r][c] = 0

    malformed_decoy = [row[:] for row in valid]
    for component in _components(malformed_decoy, 2):
        if len(component) == 4:
            r, c = min(component)
            malformed_decoy[r][c] = 0
            break

    wrong_palette = [row[:] for row in valid]
    wrong_palette[0][0] = 9

    return [
        ("empty", []),
        ("too_small", [[0, 1], [2, 0]]),
        ("missing_color_two", missing_color_two),
        ("solid_3x3_target", solid_three),
        ("no_color_one_singleton", no_one_singleton),
        ("malformed_decoy_component", malformed_decoy),
        ("wrong_palette", wrong_palette),
    ]
