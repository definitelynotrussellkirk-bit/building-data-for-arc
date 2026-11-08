from __future__ import annotations

from copy import deepcopy
import importlib
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_pairs, find_root


TASK_ID = "3adf11522bf5"
gen = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
RUNTIME_ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    all_square_cells_output,
    color_five_only_output,
    first_largest_only_output,
    largest_only_output,
    observed,
    reference_output,
    square_facts,
)


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=RUNTIME_ROOT, variant=0)


def test_rule_pin_canonical_examples_and_independent_oracle():
    assert gen.VERSION == "3.0.0"
    assert gen.RULE_HASH == "a18583a5c8f2"
    pairs = _pairs()
    assert len(pairs) == 4
    for pair in pairs:
        grid = pair["input"]
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert reference_output(grid) == pair["output"]
        assert gen.rule_mirror(grid) == pair["output"]


def test_override_boundaries_are_exact_observable_and_band_safe():
    requests = [
        {"grid_h": 7, "grid_w": 8, "obstacle_color": 2, "scene_profile": "teaching"},
        {"grid_h": 10, "grid_w": 10, "obstacle_color": 5, "scene_profile": "canonical2"},
        {"grid_h": 16, "grid_w": 18, "obstacle_color": 9, "scene_profile": "teaching"},
    ]
    for difficulty in (None, "easy", "medium", "hard"):
        for index, request in enumerate(requests):
            grid = gen.generate(901 + index, index, difficulty=difficulty, **request)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == request
            assert observed(grid) == request

    with pytest.raises((TypeError, ValueError), match="unknown override"):
        gen.generate(1, 0, misspelled_axis=10)
    for bad in (True, 7.5, "10"):
        with pytest.raises(ValueError):
            gen.generate(1, 0, grid_h=bad)
    with pytest.raises(ValueError):
        gen.generate(1, 0, grid_h=6)
    with pytest.raises(ValueError):
        gen.generate(1, 0, scene_profile="unknown")


def test_generated_distribution_is_deterministic_strict_and_teaching():
    for difficulty in ("easy", "medium", "hard"):
        exact_profiles = 0
        witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        colors: set[int] = set()
        shapes: set[tuple[int, int]] = set()
        for sample_index in range(80):
            grid = gen.generate(2401, sample_index, difficulty=difficulty)
            assert grid == gen.generate(2401, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            obs = gen.observe_overrides(grid)
            colors.add(int(obs["obstacle_color"]))
            shapes.add((len(grid), len(grid[0])))
            exact_profiles += (len(grid), len(grid[0])) == (10, 10)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                witness_hits[name] += bool(witness(grid))
        assert exact_profiles >= 8
        assert len(colors) >= 5
        assert len(shapes) >= 12
        assert all(count >= 10 for count in witness_hits.values())


def test_self_check_rejects_minimal_impostors_and_destructive_mutations():
    assert gen.self_check([[0] * 8 for _ in range(7)])
    assert gen.self_check([[5] * 8 for _ in range(7)])

    singleton = [[0] * 8 for _ in range(7)]
    singleton[3][4] = 5
    assert gen.self_check(singleton)

    two_colors = gen.generate(7, 1, grid_h=10, grid_w=10)
    changed = deepcopy(two_colors)
    for r, row in enumerate(changed):
        for c, value in enumerate(row):
            if value != 0:
                changed[r][c] = 6 if value != 6 else 7
                assert gen.self_check(changed)
                return
    raise AssertionError("generated grid unexpectedly has no obstacle")


def test_named_witnesses_are_real_counterexamples_to_named_rivals():
    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = gen.generate(1709, sample_index, difficulty=difficulty)
            intended = reference_output(grid)
            for witness_name, rival_names in gen.WITNESS_RIVALS.items():
                if not gen.SEMANTIC_WITNESSES[witness_name](grid):
                    continue
                for rival_name in rival_names:
                    assert gen.SEMANTIC_RIVALS[rival_name](grid) != intended

    teaching = gen.generate(91, 0, scene_profile="teaching", obstacle_color=7)
    assert square_facts(teaching).max_side == 3
    assert largest_only_output(teaching) != reference_output(teaching)
    assert all_square_cells_output(teaching) != reference_output(teaching)
    assert first_largest_only_output(teaching) != reference_output(teaching)
    assert color_five_only_output(teaching) != reference_output(teaching)


def test_every_four_demo_window_and_every_rotation_refutes_declared_competitors():
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            examples = []
            for sample_index in range(start, start + 5):
                grid = gen.generate(3301, sample_index, difficulty=difficulty)
                examples.append({"input": grid, "output": reference_output(grid)})
            for query_index in range(5):
                demos = [item for i, item in enumerate(examples) if i != query_index]
                query = examples[query_index]
                assert gen.lesson_identifiable(demos, query) == []
                for rival in gen.LESSON_COMPETITORS.values():
                    fits = all(rival(item["input"]) == item["output"] for item in demos)
                    if fits:
                        assert rival(query["input"]) == query["output"]


def test_selected_racket_authority_matches_canonical_text_exactly():
    canonical = None
    with (RUNTIME_ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                canonical = row
                break
    assert canonical is not None
    base = json.loads(
        (RUNTIME_ROOT / "shared/data/base/solutions/training/31adaf00__3adf11522bf5.json").read_text()
    )
    assert base["racket_target"]["target_code"] == canonical["program_solution"]
