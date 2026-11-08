from __future__ import annotations

import json
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.e9399a9f5b3b import generator as gen


def _canonical_row():
    path = Path(__file__).resolve().parents[1] / "data/canonical/puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            return row
    raise AssertionError("canonical task row not found")


def test_canonical_inputs_and_outputs_are_accepted():
    row = _canonical_row()
    for pair in row["train"]:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
    test_pairs = row["test"] if isinstance(row["test"], list) else [row["test"]]
    for pair in test_pairs:
        assert gen.self_check(pair["input"]) == []


def test_generated_schedule_is_valid_and_axis_observable():
    profiles = set()
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(8):
            grid = gen.generate(1217, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            observed = gen.observe_overrides(grid)
            assert observed["match_count"] in (1, 2)
            assert len(gen.rule_mirror(grid)[0]) == observed["n_cands"]
            profiles.add(gen.schedule_profile(1217, sample_index, difficulty))
    assert profiles == set(gen.SCHEDULE_PROFILES)


def test_semantic_witnesses_and_rivals_disagree():
    seen = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for sample_index in range(16):
        grid = gen.generate(808, sample_index, difficulty="medium")
        truth = gen.rule_mirror(grid)
        for name, witness in gen.SEMANTIC_WITNESSES.items():
            if witness(grid):
                seen[name] += 1
                rivals = gen.WITNESS_RIVALS[name]
                assert any(gen.SEMANTIC_RIVALS[rival](grid) != truth for rival in rivals)
    assert all(count > 0 for count in seen.values()), seen


def test_mutation_fixtures_are_rejected():
    fixtures = gen.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert gen.self_check(grid), name


def test_override_boundaries_and_unknown_key():
    grid = gen.generate(
        99,
        2,
        difficulty="hard",
        panel_h=7,
        template_w=4,
        candidate_w=5,
        n_cands=3,
        template_size=4,
        template_color=8,
        extra_colors=4,
        match_count=2,
    )
    assert gen.observe_overrides(grid) == {
        "panel_h": 7,
        "template_w": 4,
        "candidate_w": 5,
        "n_cands": 3,
        "template_size": 4,
        "template_color": 8,
        "extra_colors": 4,
        "match_count": 2,
    }
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, typo_axis=3)


def test_every_scheduled_lesson_window_is_identifiable():
    for difficulty_index, difficulty in enumerate(("easy", "medium", "hard")):
        for residue in range(4):
            seed = 44000 + difficulty_index * 100 + residue
            start = 1200 + residue
            demos = []
            for offset in range(gen.EXAMPLES_NEEDED):
                grid = gen.generate(seed, start + offset, difficulty=difficulty)
                demos.append({"input": grid, "output": gen.rule_mirror(grid)})
            query_grid = gen.generate(
                seed, start + gen.EXAMPLES_NEEDED, difficulty=difficulty
            )
            assert gen.lesson_identifiable(
                demos,
                {"input": query_grid, "output": gen.rule_mirror(query_grid)},
            ) == []
