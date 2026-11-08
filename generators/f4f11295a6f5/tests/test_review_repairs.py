from __future__ import annotations

import json
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", ROOT / "generator.py"))
SPEC = importlib.util.spec_from_file_location("review_generator_f4f11295a6f5", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


def _canonical_pairs():
    return [
        {"input": row["input"], "output": row["output"]}
        for row in canonical_pairs(
            generator.TASK_ID,
            root=find_root(__file__),
            labeled_only=True,
        )
    ]


def _pair(grid):
    return {"input": grid, "output": generator.rule_mirror(grid)}


@pytest.mark.parametrize("seed", [True, False, 1.0, 1.75, "1", None])
def test_seed_requires_exact_integer(seed):
    with pytest.raises(TypeError):
        generator.generate(seed, 0)


@pytest.mark.parametrize("sample_index", [True, False, 1.0, 1.75, "1", None])
def test_sample_index_requires_exact_integer(sample_index):
    with pytest.raises(TypeError):
        generator.generate(0, sample_index)


def test_sample_index_rejects_negative_values():
    with pytest.raises(ValueError):
        generator.generate(0, -1)


def test_selector_colored_tiles_is_an_exact_canonical_shortcut_with_counterexample():
    rival_name = "selector_colored_tiles"
    assert rival_name in generator.CANONICAL_SHORTCUTS
    assert rival_name in generator.SEMANTIC_RIVALS
    rival = generator.CANONICAL_SHORTCUTS[rival_name]

    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    witness = [
        [1, 2, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    intended = [
        [1, 2, 1, 2],
        [0, 1, 0, 1],
        [0, 0, 1, 2],
        [0, 0, 0, 1],
    ]
    rival_output = [
        [1, 1, 2, 2],
        [0, 1, 0, 2],
        [0, 0, 1, 1],
        [0, 0, 0, 1],
    ]
    assert generator.self_check(witness) == []
    assert generator.rule_mirror(witness) == intended
    assert rival(witness) == rival_output
    assert generator.SEMANTIC_WITNESSES["multicolor_tile_copy"](witness)
    assert generator.WITNESS_RIVALS["multicolor_tile_copy"] == [rival_name]


def test_schedule_refutes_selector_colored_tiles_in_every_three_demo_rotation():
    assert generator.LESSON_SCHEDULE_PERIOD == 7
    assert set(generator.SCHEDULE_PROFILES) == {
        "canonical_profile",
        "multicolor_general",
    }
    rival = generator.LESSON_COMPETITORS["selector_colored_tiles"]

    for band in ("easy", "medium", "hard"):
        for seed in (0, 17, 101):
            for start in range(generator.LESSON_SCHEDULE_PERIOD):
                pairs = [
                    _pair(generator.generate(seed, start + offset, difficulty=band))
                    for offset in range(4)
                ]
                for query_index in range(4):
                    demos = [
                        pair for index, pair in enumerate(pairs)
                        if index != query_index
                    ]
                    query = pairs[query_index]
                    assert any(
                        rival(demo["input"]) != demo["output"]
                        for demo in demos
                    )
                    assert generator.lesson_identifiable(demos, query) == []


def test_saved_selector_counterexample_matches_executable_contract():
    path = ROOT / "counterexamples" / "selector_colored_tiles.json"
    record = json.loads(path.read_text())
    assert record["task_id"] == generator.TASK_ID
    assert generator.self_check(record["input"]) == []
    assert generator.rule_mirror(record["input"]) == record["intended_output"]
    rival = generator.CANONICAL_SHORTCUTS[record["rival_name"]]
    assert rival(record["input"]) == record["rival_output"]
    assert record["intended_output"] != record["rival_output"]
