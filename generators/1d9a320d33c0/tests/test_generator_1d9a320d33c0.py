from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import sys
from collections import Counter, deque
from itertools import combinations
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

from puzzle_generators import base  # noqa: E402

MODULE_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_1d9a320d33c0", MODULE_PATH)
assert SPEC and SPEC.loader
GENERATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GENERATOR)


def _canonical_row() -> dict:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GENERATOR.TASK_ID:
                return row
    raise AssertionError(f"canonical row not found for {GENERATOR.TASK_ID}")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    pairs = list(row["train"])
    pairs.extend(row["test"] if isinstance(row["test"], list) else [row["test"]])
    return pairs


def _components(grid: list[list[int]]) -> list[tuple[int, tuple[tuple[int, int], ...]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[tuple[int, tuple[tuple[int, int], ...]]] = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells: list[tuple[int, int]] = []
            while queue:
                current = queue.popleft()
                cells.append(current)
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = (current[0] + drow, current[1] + dcol)
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and neighbor not in seen
                        and grid[neighbor[0]][neighbor[1]] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            components.append((color, tuple(sorted(cells))))
    return components


def _orientation(cells: tuple[tuple[int, int], ...]) -> str:
    rows = {row for row, _ in cells}
    cols = {col for _, col in cells}
    if len(cells) == 2 and len(rows) == 1 and len(cols) == 2:
        return "h"
    if len(cells) == 2 and len(rows) == 2 and len(cols) == 1:
        return "v"
    return "invalid"


def _independent_rule(grid: list[list[int]]) -> list[list[int]]:
    """Independent component-based mirror of the documented transformation."""
    output = [row[:] for row in grid]
    for color, cells in _components(grid):
        orientation = _orientation(cells)
        if orientation == "h":
            row = cells[0][0]
            for _, col in cells:
                output[row + 1][col] = color
        elif orientation == "v":
            col = cells[0][1]
            for row, _ in cells:
                output[row][col + 1] = color
    return output


def _has_diagonal_pair(grid: list[list[int]]) -> bool:
    components = _components(grid)
    for (_, left), (_, right) in combinations(components, 2):
        if any(
            abs(r1 - r2) == 1 and abs(c1 - c2) == 1
            for r1, c1 in left
            for r2, c2 in right
        ):
            return True
    return False


def _scene_signature(grid: list[list[int]]) -> tuple[int, int, int, tuple[str, ...]]:
    components = _components(grid)
    return (
        len(grid),
        len(grid[0]),
        len(components),
        tuple(sorted(_orientation(cells) for _, cells in components)),
    )


def test_rule_hash_and_every_canonical_pair_are_owned():
    row = _canonical_row()
    expected_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode("utf-8")
    ).hexdigest()[:12]
    assert GENERATOR.RULE_HASH == expected_hash

    pairs = _canonical_pairs()
    assert len(pairs) == 4
    signatures = set()
    for pair in pairs:
        grid = pair["input"]
        before = [source_row[:] for source_row in grid]
        assert GENERATOR.self_check(grid) == []
        assert GENERATOR.strict_canonical_like(grid) == []
        assert GENERATOR.rule_mirror(grid) == pair["output"]
        assert _independent_rule(grid) == pair["output"]
        assert grid == before
        signatures.add((len(grid), len(grid[0]), len(_components(grid))))
    assert signatures == {(7, 9, 3), (8, 8, 3), (7, 10, 3), (8, 9, 3)}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_axis_boundary_cross_is_exact_observable_and_lawful(band: str):
    for height in range(7, 11):
        for width in range(8, 13):
            for domino_count in range(2, 5):
                seed = height * 10_000 + width * 100 + domino_count
                grid = GENERATOR.generate(
                    seed,
                    17,
                    difficulty=band,
                    grid_h=height,
                    grid_w=width,
                    domino_count=domino_count,
                )
                assert GENERATOR.self_check(grid) == []
                assert GENERATOR.observe_overrides(grid) == {
                    "grid_h": height,
                    "grid_w": width,
                    "domino_count": domino_count,
                }
                components = _components(grid)
                assert len(components) == domino_count
                assert {_orientation(cells) for _, cells in components} == {"h", "v"}
                assert len({color for color, _ in components}) == domino_count
                assert GENERATOR.rule_mirror(grid) == _independent_rule(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_curriculum_covers_profiles_orientations_and_spacing(band: str):
    strict = 0
    diagonal = 0
    separated = 0
    counts: Counter[int] = Counter()
    signatures = set()
    for seed in range(160):
        grid = GENERATOR.generate(seed, seed * 19 + 3, difficulty=band)
        assert GENERATOR.self_check(grid) == []
        components = _components(grid)
        orientations = {_orientation(cells) for _, cells in components}
        assert orientations == {"h", "v"}
        assert len({color for color, _ in components}) == len(components)
        assert GENERATOR.rule_mirror(grid) == _independent_rule(grid)
        strict += not GENERATOR.strict_canonical_like(grid)
        has_diagonal = _has_diagonal_pair(grid)
        diagonal += has_diagonal
        separated += not has_diagonal
        counts[len(components)] += 1
        signatures.add(_scene_signature(grid))

    assert strict >= 64
    assert diagonal >= 24
    assert separated >= 24
    assert 3 in counts
    if band == "easy":
        assert {2, 3} <= set(counts)
    elif band == "medium":
        assert {2, 3, 4} <= set(counts)
    else:
        assert {3, 4} <= set(counts)
    assert len(signatures) >= 12


def test_self_check_rejects_minimal_impostors_and_blocked_growth():
    invalid = [
        [],
        [[0, 0], [0]],
        [[0] * 8 for _ in range(7)],
        [[0, 0, 0], [0, 4, 0], [0, 0, 0]],
        [[0, 0, 0, 0], [0, 4, 4, 0], [0, 4, 4, 0], [0, 0, 0, 0]],
    ]

    horizontal_only = [[0] * 8 for _ in range(7)]
    horizontal_only[1][1:3] = [2, 2]
    horizontal_only[4][4:6] = [7, 7]
    invalid.append(horizontal_only)

    repeated_color = [[0] * 8 for _ in range(7)]
    repeated_color[1][1:3] = [6, 6]
    repeated_color[4][4] = 6
    repeated_color[5][4] = 6
    invalid.append(repeated_color)

    blocked = [[0] * 8 for _ in range(7)]
    blocked[1][1:3] = [2, 2]
    blocked[2][1:3] = [7, 7]
    blocked[4][5] = 4
    blocked[5][5] = 4
    invalid.append(blocked)

    for grid in invalid:
        assert GENERATOR.self_check(grid), grid

    for name in ("no_dominoes", "single_cell", "growth_blocked"):
        assert GENERATOR.self_check(GENERATOR._draw_from_degenerate(name, None)), name


@pytest.mark.parametrize(
    "kwargs",
    [
        {"difficulty": "expert"},
        {"bogus": 1},
        {"texture": "warm"},
        {"palette_kind": "cool"},
        {"palette_size": 2},
        {"n_distinct_colors": 2},
        {"position_bias": "scattered_axis_dominoes"},
        {"density": "sparse"},
        {"grid_h": 6},
        {"grid_h": 11},
        {"grid_h": True},
        {"grid_h": "8"},
        {"grid_w": 7},
        {"grid_w": 13},
        {"domino_count": 1},
        {"domino_count": 5},
    ],
)
def test_invalid_and_removed_controls_reject_loudly(kwargs: dict):
    with pytest.raises((TypeError, ValueError)):
        GENERATOR.generate(0, 0, **kwargs)


def test_draw_provenance_matches_every_returned_grid():
    for band in ("easy", "medium", "hard"):
        for seed in range(30):
            captured = []
            base.set_ctx_observer(captured.append)
            try:
                grid = GENERATOR.generate(seed, seed * 23 + 5, difficulty=band)
            finally:
                base.set_ctx_observer(None)
            assert len(captured) == 1
            observed = GENERATOR.observe_overrides(grid)
            assert captured[0].recorded_draws() == observed

    overrides = {"grid_h": 10, "grid_w": 12, "domino_count": 4}
    captured = []
    base.set_ctx_observer(captured.append)
    try:
        grid = GENERATOR.generate(91, 117, difficulty="easy", **overrides)
    finally:
        base.set_ctx_observer(None)
    assert captured[0].recorded_draws() == overrides
    assert captured[0].overrides_used() == overrides
    assert GENERATOR.observe_overrides(grid) == overrides


def test_semantic_rivals_are_refuted_by_every_mixed_scene():
    for seed in range(20):
        grid = GENERATOR.generate(seed, seed * 31 + 7, difficulty="medium")
        expected = GENERATOR.rule_mirror(grid)
        assert GENERATOR.SEMANTIC_WITNESSES["has_horizontal"](grid)
        assert GENERATOR.SEMANTIC_WITNESSES["has_vertical"](grid)
        assert GENERATOR.SEMANTIC_RIVALS["horizontal_only"](grid) != expected
        assert GENERATOR.SEMANTIC_RIVALS["vertical_only"](grid) != expected


def test_generation_is_deterministic_fresh_and_global_rng_isolated():
    random.seed(98431)
    expected_state = random.getstate()
    first = GENERATOR.generate(19, 31, difficulty="hard")
    assert random.getstate() == expected_state
    second = GENERATOR.generate(19, 31, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GENERATOR.generate(19, 31, difficulty="hard") == second
