"""Focused semantic, distribution, and shortcut regressions for fa55db418c9d."""
from __future__ import annotations

import copy
import importlib.util
import itertools
import json
from pathlib import Path
import random
import sys

import pytest


TASK_ID = "fa55db418c9d"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = TASK_DIR.parents[1]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))

SPEC = importlib.util.spec_from_file_location(
    f"review_{TASK_ID}_generator", TASK_DIR / "generator.py"
)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_record():
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record
    raise AssertionError("canonical task row not found")


def _canonical_pairs():
    row = _canonical_record()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def _pair(seed: int, sample_index: int, difficulty: str):
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def test_rule_hash_and_all_canonical_pairs_are_accepted_and_mirrored():
    assert GEN.RULE_HASH == "eeee12543bcc"
    pairs = _canonical_pairs()
    assert len(pairs) == 5
    for pair in pairs:
        grid = copy.deepcopy(pair["input"])
        original = copy.deepcopy(grid)
        assert GEN.self_check(grid) == []
        assert GEN.strict_canonical_like(grid) == []
        assert GEN.rule_mirror(grid) == pair["output"]
        assert grid == original


def test_five_profile_schedule_teaches_shape_color_position_and_orientation():
    assert GEN.EXAMPLES_NEEDED == 5
    assert tuple(GEN.SCHEDULE_PROFILES) == (0, 1, 2, 3, 4)
    for band in ("easy", "medium", "hard"):
        grids = [GEN.generate(101, index, difficulty=band) for index in range(5)]
        observations = [GEN.semantic_observables(grid) for grid in grids]
        assert sum(bool(row["canonical_anchor"]) for row in observations) == 1
        assert set().union(*(set(row["target_orientations"]) for row in observations)) == set(
            GEN._ORIENTATIONS
        )
        kinds = set().union(*(set(row["blue_decoy_kinds"]) for row in observations))
        assert {"straight_triomino", "square", "size6_blob", "long_l_tetromino"} <= kinds
        assert any(row["n_colored_l_decoys"] for row in observations)
        assert any(row["target_position"] == "edge" for row in observations)
        assert all(GEN.self_check(grid) == [] for grid in grids)


def test_default_anchor_reaches_four_color_canonical_palette():
    for band in ("easy", "medium", "hard"):
        anchor = GEN.generate(20261002, 0, difficulty=band)
        assert set(GEN.semantic_observables(anchor)["palette"]) == {0, 1, 6, 7}
        assert GEN.strict_canonical_like(anchor) == []


def test_all_declared_axis_boundaries_are_exactly_observable():
    axis_values = {
        "grid_h": (9, 20),
        "grid_w": (10, 22),
        "n_target_l": (1, 4),
        "n_blue_decoys": (0, 1),
        "n_colored_l_decoys": (0, 1),
        "target_position": ("interior", "edge"),
    }
    for band in ("easy", "medium", "hard"):
        for values in itertools.product(*axis_values.values()):
            overrides = dict(zip(axis_values, values))
            grid = GEN.generate(7, 3, difficulty=band, **overrides)
            assert GEN.self_check(grid, difficulty=band, meta={"overrides": overrides}) == []
            assert GEN.observe_overrides(grid) == overrides


def test_unknown_difficulty_and_unknown_or_retired_overrides_reject_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="impossible")
    for key, value in (
        ("texture", "warm"),
        ("palette_kind", "varied"),
        ("typo_axis", 3),
    ):
        with pytest.raises(ValueError, match="unknown override"):
            GEN.generate(0, 0, **{key: value})


def test_strongest_canonical_shortcut_fits_all_public_pairs_and_has_exact_counterexample():
    name = "recolor every blue size-three component"
    shortcut = GEN.CANONICAL_SHORTCUTS[name]
    for pair in _canonical_pairs():
        assert shortcut(pair["input"]) == pair["output"]

    # One intended missing-SE L and one blue horizontal I-triomino.  The exact
    # rule recolors only the L to 2; the size-only shortcut recolors both to 2.
    witness = [
        [1, 1, 0, 0, 0, 0],
        [1, 0, 0, 1, 1, 1],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 7, 7, 7],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    # Width is padded to the admitted minimum without changing the objects.
    witness = [row + [0, 0, 0, 0] for row in witness]
    intended = GEN.rule_mirror(witness)
    rival = shortcut(witness)
    assert intended[1][3:6] == [1, 1, 1]
    assert rival[1][3:6] == [2, 2, 2]
    assert intended != rival


def test_every_declared_witness_fires_and_its_named_rival_disagrees():
    seen = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for band in ("easy", "medium", "hard"):
        for sample_index in range(15):
            grid = GEN.generate(17_000 + sample_index, sample_index, difficulty=band)
            truth = GEN.rule_mirror(grid)
            for name, predicate in GEN.SEMANTIC_WITNESSES.items():
                if not predicate(grid):
                    continue
                seen[name] += 1
                rivals = GEN.WITNESS_RIVALS[name]
                assert any(GEN.LESSON_COMPETITORS[rival](grid) != truth for rival in rivals), name
    assert all(count > 0 for count in seen.values()), seen


def test_every_cyclic_five_example_lesson_is_identifiable_and_refutes_all_competitors():
    for band in ("easy", "medium", "hard"):
        for start in range(5):
            demos = [_pair(31_337 + start, start + offset, band) for offset in range(5)]
            query = _pair(31_337 + start, start + 5, band)
            assert GEN.lesson_identifiable(demos, query) == []
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                assert any(
                    competitor(demo["input"]) != demo["output"] for demo in demos
                ), (band, start, name)


def test_strict_anchor_occurs_in_every_band_and_recombinations_are_distinguished():
    for band in ("easy", "medium", "hard"):
        strict = [
            grid
            for index in range(5)
            if not GEN.strict_canonical_like(
                grid := GEN.generate(44, index, difficulty=band)
            )
        ]
        assert len(strict) == 1

    canonical = GEN.generate(44, 0, difficulty="medium")
    assert GEN.strict_canonical_like(canonical) == []
    recombined = GEN.generate(
        44,
        0,
        difficulty="medium",
        grid_h=20,
        grid_w=22,
        n_target_l=4,
        n_blue_decoys=0,
        n_colored_l_decoys=1,
        target_position="edge",
    )
    assert GEN.self_check(recombined) == []
    assert GEN.strict_canonical_like(recombined)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(1927)
    before = random.getstate()
    first = GEN.generate(42, 7, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(42, 7, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 7
    assert first != second
