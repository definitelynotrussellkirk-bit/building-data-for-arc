from __future__ import annotations

from collections import deque
import importlib.util
import random

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "a78185b4bd20"
ROOT = find_root(__file__)
GENERATOR_PATH = next(
    path
    for path in (
        ROOT / "generators" / TASK_ID / "generator.py",
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
    )
    if path.is_file()
)
SPEC = importlib.util.spec_from_file_location("target_generator", GENERATOR_PATH)
gen = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(gen)


def test_rule_mirror_selects_first_lr_symmetric_component_not_largest():
    # Row-major components: asymmetric L, symmetric singleton (the target),
    # then a larger symmetric plus of the same color.  A largest-symmetric
    # shortcut returns the plus; the Racket authority returns the singleton.
    grid = [
        [3, 0, 0, 0, 0, 0, 0, 0, 0],
        [3, 3, 0, 0, 2, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0, 2, 2, 2, 0],
        [0, 0, 0, 0, 0, 0, 2, 0, 0],
        [0, 0, 0, 0, 0, 0, 0, 0, 4],
        [0, 0, 0, 0, 0, 0, 0, 4, 4],
        [0, 0, 0, 0, 0, 0, 0, 0, 0],
    ]

    assert gen.rule_mirror(grid) == [[8]]


def test_rule_hash_and_all_canonical_pairs_are_owned():
    assert getattr(gen, "RULE_HASH", None) == "4f60736ed86a"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_self_check_rejects_missing_symmetric_or_asymmetric_roles():
    no_objects = [[0] * 11 for _ in range(9)]

    all_symmetric = [[0] * 11 for _ in range(9)]
    all_symmetric[1][1] = 2
    for r, c in ((1, 7), (2, 6), (2, 7), (2, 8), (3, 7)):
        all_symmetric[r][c] = 3
    for r, c in ((5, 1), (5, 2), (6, 1), (6, 2)):
        all_symmetric[r][c] = 4

    all_asymmetric = [[0] * 11 for _ in range(9)]
    for color, cells in (
        (2, ((1, 1), (2, 1), (2, 2))),
        (3, ((1, 7), (1, 8), (2, 8))),
        (4, ((5, 4), (6, 4), (6, 5), (7, 5))),
    ):
        for r, c in cells:
            all_asymmetric[r][c] = color

    assert any("object" in message for message in gen.self_check(no_objects))
    assert any("asymmetric" in message for message in gen.self_check(all_symmetric))
    assert any("LR-symmetric" in message for message in gen.self_check(all_asymmetric))


def test_self_check_rejects_four_component_curriculum_gap():
    grid = [[0] * 11 for _ in range(9)]
    for color, cells in (
        (3, ((0, 0), (1, 0), (1, 1))),
        (2, ((0, 8),)),
        (2, ((5, 1), (6, 0), (6, 1), (6, 2), (7, 1))),
        (4, ((6, 9), (7, 9), (7, 10))),
    ):
        for row, col in cells:
            grid[row][col] = color

    assert any("3 or 5" in message for message in gen.self_check(grid))



def _component_facts(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    facts = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] == 0 or (row, col) in seen:
                continue
            color = grid[row][col]
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    neighbor = (current_row + delta_row, current_col + delta_col)
                    nr, nc = neighbor
                    if (
                        0 <= nr < height
                        and 0 <= nc < width
                        and neighbor not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add(neighbor)
                        queue.append(neighbor)
            min_row = min(r for r, _ in cells)
            max_row = max(r for r, _ in cells)
            min_col = min(c for _, c in cells)
            max_col = max(c for _, c in cells)
            crop = [
                source[min_col:max_col + 1]
                for source in grid[min_row:max_row + 1]
            ]
            binary = [[value != 0 for value in source] for source in crop]
            facts.append(
                {
                    "color": color,
                    "size": len(cells),
                    "first": (row, col),
                    "crop": crop,
                    "lr_symmetric": all(source == source[::-1] for source in binary),
                }
            )
    return facts


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_three_component_profiles_anchor_the_canonical_11x11_palette(difficulty):
    for sample_index in (0, 3, 4, 7):
        grid = gen.generate(20261023, sample_index, difficulty=difficulty)
        facts = _component_facts(grid)
        assert (len(grid), len(grid[0])) == (11, 11)
        assert len({value for row in grid for value in row}) == 4
        assert len(facts) == 3


@pytest.mark.parametrize("height,width", [(7, 9), (7, 16), (14, 9), (14, 16)])
def test_declared_grid_size_overrides_are_exact_and_unknown_keys_reject(height, width):
    grid = gen.generate(61, 2, difficulty="hard", grid_h=height, grid_w=width)
    assert (len(grid), len(grid[0])) == (height, width)
    assert gen.observe_overrides(grid) == {"grid_h": height, "grid_w": width}
    assert gen.self_check(grid) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(61, 2, typo_axis=1)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_schedule_covers_canonical_object_counts_and_ordered_competitor_lessons(difficulty):
    observed_counts = set()
    for sample_index in range(8):
        grid = gen.generate(20261023, sample_index, difficulty=difficulty)
        assert gen.self_check(grid) == []
        facts = _component_facts(grid)
        observed_counts.add(len(facts))
        expected_count = 5 if sample_index % 4 in (1, 2) else 3
        assert len(facts) == expected_count

        target_index = next(
            index for index, fact in enumerate(facts) if fact["lr_symmetric"]
        )
        target = facts[target_index]
        later_same_color = [
            fact
            for fact in facts[target_index + 1:]
            if fact["lr_symmetric"] and fact["color"] == target["color"]
        ]
        if expected_count == 3:
            assert target_index == 1
            assert sum(fact["lr_symmetric"] for fact in facts) == 1
            assert later_same_color == []
        else:
            assert later_same_color
            competitor = later_same_color[0]
            if sample_index % 2 == 0:
                assert target["size"] < competitor["size"]
            else:
                assert target["size"] > competitor["size"]

    assert observed_counts == {3, 5}



def test_declared_output_codomain_is_complete():
    expected = {
        ((8,),),
        ((8,), (8,)),
        ((8, 8),),
        ((8, 8, 8), (0, 8, 0)),
        ((0, 8, 0), (8, 8, 8)),
        ((0, 8, 0), (8, 8, 8), (0, 8, 0)),
        ((8, 0, 8), (8, 0, 8), (8, 8, 8)),
        ((8, 8, 8), (8, 0, 8), (8, 0, 8)),
        ((8, 8, 8), (8, 0, 8), (8, 8, 8)),
    }
    observed = {
        tuple(tuple(row) for row in gen.rule_mirror(gen.generate(seed, sample_index)))
        for seed in range(16)
        for sample_index in range(16)
    }

    assert gen.EXPECTED_OUTPUT_CODOMAIN == 9
    assert observed == expected


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    random.seed(77123)
    state = random.getstate()
    first = gen.generate(811, 5, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(811, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 0
    assert second == gen.generate(811, 5, difficulty="hard")
