from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

gen = importlib.import_module("puzzle_generators.per_puzzle.1c1b8aa6505e.generator")


def _canonical_rows():
    path = Path(__file__).resolve().parents[3] / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == gen.TASK_ID:
            yield row


def test_canonical_inputs_are_accepted_and_mirror_outputs():
    seen = 0
    for row in _canonical_rows():
        for split in ("train", "test"):
            for pair in row.get(split) or []:
                if "output" not in pair:
                    continue
                seen += 1
                assert gen.self_check(pair["input"]) == []
                assert gen.strict_canonical_like(pair["input"]) == []
                assert gen.rule_mirror(pair["input"]) == pair["output"]
    assert seen == 10


@pytest.mark.parametrize("height", [9, 18])
@pytest.mark.parametrize("width", [9, 18])
@pytest.mark.parametrize("position", gen.DIVIDER_POSITIONS)
@pytest.mark.parametrize("profile", gen.PROFILE_SEQUENCE)
@pytest.mark.parametrize("scale", gen.COUNT_SCALES)
def test_override_round_trip(height, width, position, profile, scale):
    grid = gen.generate(
        17,
        23,
        difficulty="easy",
        grid_h=height,
        grid_w=width,
        divider_position=position,
        count_profile=profile,
        count_scale=scale,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": height,
        "grid_w": width,
        "divider_position": position,
        "count_profile": profile,
        "count_scale": scale,
    }


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, typo_axis=123)


def test_every_three_consecutive_demos_kill_named_shortcuts():
    for start in range(8):
        demos = []
        for index in range(start, start + gen.EXAMPLES_NEEDED):
            grid = gen.generate(101, index, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(101, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == []


def test_witness_rival_claims_hold_on_default_schedule():
    fired = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            grid = gen.generate(300 + index, index, difficulty=band)
            canonical = gen.rule_mirror(grid)
            for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
                if not witness(grid):
                    continue
                fired[witness_name] += 1
                rivals = gen.WITNESS_RIVALS[witness_name]
                assert any(gen.SEMANTIC_RIVALS[name](grid) != canonical for name in rivals)
    assert all(count > 0 for count in fired.values())
