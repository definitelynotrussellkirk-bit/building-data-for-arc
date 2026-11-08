from __future__ import annotations

import copy
import importlib
import random

import pytest

from pathlib import Path
import importlib.util
import hashlib
import json
from reviewer_support import canonical_pairs, canonical_path, find_root
ROOT = find_root(__file__)
SPEC = importlib.util.spec_from_file_location("rectangle_generator", Path(__file__).parents[1] / "generator.py")
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

def canonical_rule_hash(task_id):
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    rules = {row["program_solution"] for row in rows if row.get("task_id") == task_id}
    assert len(rules) == 1
    return hashlib.sha256(" ".join(rules.pop().split()).encode()).hexdigest()[:12]


def test_rule_hash_and_every_canonical_pair() -> None:
    assert GEN.RULE_HASH == canonical_rule_hash(GEN.TASK_ID)
    pairs = canonical_pairs(GEN.TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_every_exact_override_boundary_and_cross_product_is_observable() -> None:
    cases = [
        {"grid_h": 6},
        {"grid_h": 14},
        {"grid_w": 9},
        {"grid_w": 14},
        {"color": 1},
        {"color": 9},
        {"rect_aspect": "square"},
        {"rect_aspect": "wide"},
        {"rect_aspect": "tall"},
        {"edge_relation": "interior"},
        {"edge_relation": "touch_top"},
        {"edge_relation": "touch_bottom"},
        {"edge_relation": "touch_left"},
        {"edge_relation": "touch_right"},
    ]
    # The smallest dimensions are the tight feasibility boundary for a tall
    # outline; combine every categorical mode with that exact corner.
    for aspect in GEN.RECT_ASPECTS:
        for edge in GEN.EDGE_RELATIONS:
            cases.append(
                {
                    "grid_h": 6,
                    "grid_w": 9,
                    "color": 9,
                    "rect_aspect": aspect,
                    "edge_relation": edge,
                }
            )

    for index, overrides in enumerate(cases):
        band = ("easy", "medium", "hard")[index % 3]
        grid = GEN.generate(70_000 + index, 5, difficulty=band, **overrides)
        observed = GEN.observe_overrides(grid)
        assert GEN.self_check(grid, meta={"overrides": overrides}) == []
        for name, expected in overrides.items():
            assert observed[name] == expected


def test_unknown_and_invalid_override_values_reject_loudly() -> None:
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, unexpected_axis=7)
    with pytest.raises(ValueError, match="outside"):
        GEN.generate(1, 2, grid_h=5)
    with pytest.raises(ValueError, match="not in options"):
        GEN.generate(1, 2, edge_relation="touch_corner")


def test_targeted_impostors_and_negative_recombination_are_rejected() -> None:
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name

    recombined, label = GEN.negative_recombination_fixture()
    assert label == "two_disjoint_outlines"
    assert GEN.self_check(recombined)


def test_every_sliding_three_example_window_is_identifiable() -> None:
    # A complete schedule period plus wraparound, in every difficulty band.
    for band in ("easy", "medium", "hard"):
        pairs = []
        for sample_index in range(12):
            grid = GEN.generate(93_333, sample_index, difficulty=band)
            pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
        for start in range(len(pairs) - GEN.EXAMPLES_NEEDED):
            demos = pairs[start : start + GEN.EXAMPLES_NEEDED]
            query = pairs[start + GEN.EXAMPLES_NEEDED]
            assert GEN.lesson_identifiable(demos, query) == []
            for rival in GEN.LESSON_COMPETITORS.values():
                assert any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                )


def test_declared_witnesses_and_rival_claims_have_real_disagreement() -> None:
    seen = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for sample_index in range(30):
            grid = GEN.generate(
                81_000 + band_index * 1_000 + sample_index,
                sample_index,
                difficulty=band,
            )
            official = GEN.rule_mirror(grid)
            assert GEN.self_check(grid) == []
            for name, witness in GEN.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    seen[name] += 1
                    claimed = GEN.WITNESS_RIVALS.get(name, ())
                    if claimed:
                        assert any(
                            GEN.SEMANTIC_RIVALS[rival](grid) != official
                            for rival in claimed
                        )
    assert all(count > 0 for count in seen.values())


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    state = random.getstate()
    first = GEN.generate(12_345, 8, difficulty="hard")
    second = GEN.generate(12_345, 8, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    third = GEN.generate(12_345, 8, difficulty="hard")
    assert third == second
    assert random.getstate() == state
