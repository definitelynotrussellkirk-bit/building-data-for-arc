"""Source-bound regressions for Connect Aligned Pairs (97dd5f3c96b9)."""
from __future__ import annotations

import copy
import importlib
import json
import os
import importlib.util
import random
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import pytest

TASK_ID = "97dd5f3c96b9"
EXPECTED_RULE_HASH = "8d1d1f690046"
HERE = Path(__file__).resolve()
LIBRARY = next((p for p in HERE.parents if (p / "shared/runtime").is_dir()), None)
if LIBRARY is not None:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))
    from reviewer_support import canonical_pairs, find_root

    SPEC = importlib.util.spec_from_file_location(
        f"review_subject_{TASK_ID}",
        LIBRARY / "generators" / TASK_ID / "generator.py",
    )
    assert SPEC is not None and SPEC.loader is not None
    GEN = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(GEN)
else:
    from reviewer_support import canonical_pairs, find_root

    GEN = importlib.import_module(
        f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    )

ROOT = find_root(__file__)


def _positions(grid):
    positions = defaultdict(list)
    for row_index, row in enumerate(grid):
        for column_index, color in enumerate(row):
            if color:
                positions[color].append((row_index, column_index))
    return dict(positions)


def _span_cells(cells):
    (r0, c0), (r1, c1) = cells
    if r0 == r1:
        return {(r0, column) for column in range(min(c0, c1), max(c0, c1) + 1)}
    if c0 == c1:
        return {(row, c0) for row in range(min(r0, r1), max(r0, r1) + 1)}
    raise AssertionError(f"unaligned pair: {cells}")


def _assert_declared_scene(grid):
    positions = _positions(grid)
    assert len(positions) == 3
    assert all(len(cells) == 2 for cells in positions.values())
    orientations = {
        "horizontal" if cells[0][0] == cells[1][0] else "vertical"
        for cells in positions.values()
    }
    assert orientations == {"horizontal", "vertical"}
    spans = [_span_cells(cells) for cells in positions.values()]
    for index, first in enumerate(spans):
        assert len(first) >= 3
        for second in spans[index + 1 :]:
            assert first.isdisjoint(second)


def _overlapping_fixture():
    grid = [[0 for _ in range(10)] for _ in range(8)]
    grid[3][1] = grid[3][6] = 7
    grid[3][4] = grid[3][8] = 4
    grid[0][0] = grid[2][0] = 2
    return grid


def test_rule_hash_and_all_canonical_pairs_are_exact():
    assert GEN.RULE_HASH == EXPECTED_RULE_HASH
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_self_check_rejects_overlapping_pair_segments():
    errors = GEN.self_check(_overlapping_fixture())
    assert errors
    assert any("overlap" in error.lower() for error in errors)


@pytest.mark.parametrize(
    "name,grid",
    [
        ("blank", [[0 for _ in range(10)] for _ in range(8)]),
        (
            "adjacent",
            [
                [2, 2, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 3, 0, 0, 0, 3, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 4, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 4, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            ],
        ),
        (
            "diagonal",
            [
                [2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 3, 0, 0, 0, 3, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 4, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 4, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            ],
        ),
        ("ragged", [[0, 0], [0]]),
        ("bad_cell", [[False for _ in range(10)] for _ in range(8)]),
    ],
)
def test_self_check_rejects_structural_impostors(name, grid):
    assert GEN.self_check(grid), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_default_generation_is_lawful_and_marker_preserving(band):
    for sample_index in range(48):
        grid = GEN.generate(10_000 + sample_index, sample_index, difficulty=band)
        assert GEN.self_check(grid) == []
        _assert_declared_scene(grid)
        output = GEN.rule_mirror(grid)
        assert output != grid
        for color, cells in _positions(grid).items():
            for row, column in cells:
                assert output[row][column] == color


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_scene_profile_override_is_exact_and_observable_in_every_band(band):
    for profile in GEN.SCENE_PROFILES:
        requested = {"scene_profile": profile}
        grid = GEN.generate(71, 9, difficulty=band, **requested)
        assert GEN.self_check(grid, meta={"overrides": requested}) == []
        assert GEN.observe_overrides(grid) == requested


def test_unknown_overrides_invalid_profile_types_and_unknown_difficulty_are_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, typo_axis="accepted")
    with pytest.raises((TypeError, ValueError), match="scene_profile"):
        GEN.generate(1, 2, scene_profile=8)
    with pytest.raises(ValueError, match="scene_profile"):
        GEN.generate(1, 2, scene_profile="not-a-profile")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 2, difficulty="impossible")


def test_each_single_demo_refutes_declared_competitors_and_supplies_witnesses():
    for band in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = GEN.generate(700 + sample_index, sample_index, difficulty=band)
            official = GEN.rule_mirror(grid)
            pair = {"input": grid, "output": official}
            assert all(predicate(grid) for predicate in GEN.SEMANTIC_WITNESSES.values())
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert rival(grid) != official, name
            assert GEN.lesson_identifiable([pair], pair) == []


def test_mutation_fixtures_are_rejected():
    fixtures = GEN.mutation_fixtures()
    assert fixtures
    for name, grid in fixtures:
        assert GEN.self_check(grid), name


def test_replay_is_independent_of_python_hash_seed():
    script = f"""
import importlib.util, json
spec = importlib.util.spec_from_file_location('subject', {str(Path(GEN.__file__).resolve())!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(json.dumps(module.generate(0, 0, difficulty='medium'), separators=(',', ':')))
"""
    outputs = []
    for hash_seed in ("1", "2", "3"):
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = hash_seed
        env["PYTHONPATH"] = os.pathsep.join(entry for entry in sys.path if entry)
        completed = subprocess.run(
            [sys.executable, "-c", script],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        outputs.append(json.loads(completed.stdout))
    assert outputs[0] == outputs[1] == outputs[2]


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(1927)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(first_row is not second_row for first_row, second_row in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert first != second
