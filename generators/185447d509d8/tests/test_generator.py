from __future__ import annotations

from collections import deque

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


TASK_ID = "185447d509d8"
ROOT = find_root(__file__)
GEN, SOURCE_PATH, SOURCE_SHA256 = load_selected_generator(TASK_ID, root=ROOT)


def _components(grid):
    height = len(grid)
    width = len(grid[0])
    seen = set()
    found = []
    for row in range(height):
        for col in range(width):
            color = grid[row][col]
            if color == 0 or (row, col) in seen:
                continue
            queue = deque([(row, col)])
            seen.add((row, col))
            cells = []
            while queue:
                current_row, current_col = queue.popleft()
                cells.append((current_row, current_col))
                for delta_row, delta_col in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + delta_row
                    next_col = current_col + delta_col
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if grid[next_row][next_col] != color:
                        continue
                    seen.add((next_row, next_col))
                    queue.append((next_row, next_col))
            bbox_key = (
                min(cell_row for cell_row, _ in cells),
                min(cell_col for _, cell_col in cells),
            )
            found.append((bbox_key, color, cells))
    return sorted(found)


def _normalize(cells):
    cells = tuple(cells)
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    return tuple(sorted((row - min_row, col - min_col) for row, col in cells))


def _rotate(cells):
    normalized = _normalize(cells)
    max_row = max(row for row, _ in normalized)
    return _normalize((col, max_row - row) for row, col in normalized)


def _flip(cells):
    normalized = _normalize(cells)
    max_col = max(col for _, col in normalized)
    return _normalize((row, max_col - col) for row, col in normalized)


def _rotation_forms(cells):
    current = _normalize(cells)
    forms = set()
    for _ in range(4):
        forms.add(current)
        current = _rotate(current)
    return forms


def _dihedral_forms(cells):
    rotations = _rotation_forms(cells)
    return rotations | {_flip(form) for form in rotations}


def _oracle(grid):
    shapes = [_normalize(cells) for _, _, cells in _components(grid)]
    return [
        [2 if right in _dihedral_forms(left) else 0 for right in shapes]
        for left in shapes
    ]


def test_rule_hash_and_canonical_inputs_are_bound():
    assert GEN.RULE_HASH == "9586787e3555"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert pairs
    for pair in pairs:
        assert GEN.self_check(pair["input"]) == []
        assert _oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_normal_draws_have_four_complete_objects_and_pass_self_check(difficulty):
    for sample_index in range(24):
        grid = GEN.generate(seed=17, sample_index=sample_index, difficulty=difficulty)
        components = _components(grid)
        assert len(components) == 4
        assert len({color for _, color, _ in components}) == 4
        assert all(len(cells) == 4 for _, _, cells in components)
        assert GEN.self_check(grid, difficulty=difficulty) == []


def test_every_advertised_override_is_observable_and_honored():
    size_profiles = GEN.AXES["size_profile"]["valid"].split("|")
    partitions = GEN.AXES["partition"]["valid"].split("|")
    assert size_profiles == ["12x14", "13x15", "12x16", "14x14", "12x15"]
    assert partitions == ["one_pair", "two_pairs"]

    sample_index = 0
    for size_profile in size_profiles:
        for partition in partitions:
            grid = GEN.generate(
                seed=31,
                sample_index=sample_index,
                difficulty="medium",
                size_profile=size_profile,
                partition=partition,
            )
            assert GEN.observe_overrides(grid) == {
                "size_profile": size_profile,
                "partition": partition,
            }
            assert GEN.self_check(
                grid,
                difficulty="medium",
                meta={"overrides": {"size_profile": size_profile, "partition": partition}},
            ) == []
            sample_index += 1


def test_removed_all_same_partition_is_rejected_not_silently_generated():
    assert "all_same" not in GEN.AXES["partition"]["valid"].split("|")
    with pytest.raises(ValueError, match="partition"):
        GEN.generate(seed=0, sample_index=0, difficulty="medium", partition="all_same")


@pytest.mark.parametrize(
    "kwargs",
    [
        {"sample_index": True},
        {"sample_index": 1.0},
        {"sample_index": "1"},
        {"sample_index": -1},
        {"seed": True},
        {"size_profile": 12},
        {"partition": 1},
        {"unknown_axis": "value"},
    ],
)
def test_invalid_controls_fail_loudly(kwargs):
    arguments = {"seed": 0, "sample_index": 0, "difficulty": "medium"}
    arguments.update(kwargs)
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(**arguments)


@pytest.mark.parametrize("partition", ["one_pair", "two_pairs"])
def test_each_generated_input_refutes_declared_shortcuts(partition):
    for sample_index in range(12):
        grid = GEN.generate(
            seed=43,
            sample_index=sample_index,
            difficulty="hard",
            partition=partition,
        )
        expected = _oracle(grid)
        assert GEN.SEMANTIC_WITNESSES
        assert GEN.SEMANTIC_RIVALS
        for witness in GEN.SEMANTIC_WITNESSES.values():
            assert witness(grid) is True
        for rival in GEN.SEMANTIC_RIVALS.values():
            assert rival(grid) != expected


def test_generation_is_repeatable_and_call_order_independent():
    first = GEN.generate(seed=101, sample_index=7, difficulty="easy")
    GEN.generate(seed=999, sample_index=999, difficulty="hard")
    second = GEN.generate(seed=101, sample_index=7, difficulty="easy")
    assert first == second


def test_declared_output_codomain_is_complete_and_reachable():
    # Four labelled positions admit C(4,2)=6 one-pair matrices and exactly
    # three perfect-matchings (two-pair matrices), for a complete codomain of 9.
    assert GEN.EXPECTED_OUTPUT_CODOMAIN == 9
    outputs = set()
    for partition in ("one_pair", "two_pairs"):
        for sample_index in range(200):
            grid = GEN.generate(
                seed=211,
                sample_index=sample_index,
                difficulty="medium",
                partition=partition,
            )
            outputs.add(tuple(tuple(row) for row in _oracle(grid)))
    assert len(outputs) == GEN.EXPECTED_OUTPUT_CODOMAIN


def test_difficulty_bands_schedule_distinct_visible_profiles():
    expected_profiles = {
        "easy": {"12x14", "12x15"},
        "medium": {"13x15", "14x14"},
        "hard": {"12x16"},
    }
    expected_partitions = {
        "easy": {"one_pair"},
        "medium": {"one_pair", "two_pairs"},
        "hard": {"two_pairs"},
    }
    for sample_index in range(12):
        observed_by_band = {}
        for difficulty in ("easy", "medium", "hard"):
            grid = GEN.generate(seed=307, sample_index=sample_index, difficulty=difficulty)
            observed = GEN.observe_overrides(grid)
            assert observed["size_profile"] in expected_profiles[difficulty]
            assert observed["partition"] in expected_partitions[difficulty]
            assert GEN.self_check(grid, difficulty=difficulty) == []
            observed_by_band[difficulty] = observed
        assert len({item["size_profile"] for item in observed_by_band.values()}) == 3
