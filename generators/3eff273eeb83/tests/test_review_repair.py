"""Source-bound regressions for the 3eff273eeb83 review repair."""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root

TASK_ID = "3eff273eeb83"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", HOME / "generator.py")
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _pair(grid):
    return {"input": grid, "output": GEN._transform(grid)}


def _canonical_row():
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _selected_solution_path():
    relative = Path("data/base/solutions/training/c074846d__3eff273eeb83.json")
    for prefix in (Path("shared"), Path()):
        path = ROOT / prefix / relative
        if path.is_file():
            return path
    raise AssertionError("missing selected training solution")


@pytest.mark.parametrize("sample_index", [True, False, 1.0, "1", -1])
def test_sample_index_must_be_a_nonnegative_plain_integer(sample_index):
    with pytest.raises(ValueError, match="sample_index"):
        GEN.generate(7, sample_index)


def test_active_target_code_exactly_matches_canonical_while_raw_is_archival():
    canonical = _canonical_row()["program_solution"]
    record = json.loads(_selected_solution_path().read_text(encoding="utf-8"))
    target = record["racket_target"]
    assert target["target_code"] == canonical
    assert target["raw_code"] != canonical
    assert sha256(target["raw_code"].encode()).hexdigest() == (
        "3ac43b22416f1daa79a893286c0acc399b149b2d685a5bb2d7fdd9c5db9e0d2c"
    )


def test_max_three_copy_is_train_equivalent_but_canonical_test_refutes_it():
    pairs = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    train = [pair for pair in pairs if pair["split"] == "train"]
    tests = [pair for pair in pairs if pair["split"] == "test"]
    rival = GEN.SEMANTIC_RIVALS["copy_at_most_three"]
    assert all(rival(pair["input"]) == pair["output"] for pair in train)
    witness = next(
        pair for pair in tests if GEN.observe_overrides(pair["input"])["line_length"] == 4
    )
    assert rival(witness["input"]) != witness["output"]
    assert GEN.CANONICAL_SHORTCUTS == {}


@pytest.mark.parametrize("difficulty", [None, "easy", "medium", "hard"])
def test_every_four_pair_window_survives_every_three_demo_query_rotation(difficulty):
    assert GEN.EXAMPLES_NEEDED == 3
    assert GEN.SCHEDULE_CYCLE == 20
    assert not hasattr(GEN, "LESSON_SCHEDULE_PERIOD")
    for start in range(GEN.SCHEDULE_CYCLE):
        grids = [
            GEN.generate(1207, start + offset, difficulty=difficulty)
            for offset in range(GEN.EXAMPLES_NEEDED + 1)
        ]
        lengths = [GEN.observe_overrides(grid)["line_length"] for grid in grids]
        assert lengths.count(4) >= 2, (difficulty, start, lengths)
        pairs = [_pair(grid) for grid in grids]
        for query_index, query in enumerate(pairs):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert any(
                GEN.observe_overrides(demo["input"])["line_length"] == 4
                for demo in demos
            )
            assert GEN.lesson_identifiable(demos, query) == []
            for name, rival in GEN.LESSON_COMPETITORS.items():
                assert any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                ), (difficulty, start, query_index, name)


def test_default_schedule_preserves_full_direction_and_length_support():
    grids = [GEN.generate(991, index, difficulty="medium") for index in range(60)]
    observed = [GEN.observe_overrides(grid) for grid in grids]
    assert {item["line_direction"] for item in observed} == set(GEN.LINE_DIRECTIONS)
    assert {item["line_length"] for item in observed} == {1, 2, 3, 4}
    assert "length_four" in GEN.SEMANTIC_WITNESSES
    assert "copy_at_most_three" in GEN.WITNESS_RIVALS["length_four"]


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1"])
@pytest.mark.parametrize("difficulty", [None, "easy", "hard"])
def test_seed_must_be_a_plain_integer(seed, difficulty):
    with pytest.raises(ValueError, match="seed"):
        GEN.generate(seed, 0, difficulty=difficulty)


@pytest.mark.parametrize(
    "difficulty", [True, False, 0, 1.0, "__invalid_difficulty__"]
)
def test_difficulty_must_be_a_standard_band_or_none(difficulty):
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(7, 0, difficulty=difficulty)
