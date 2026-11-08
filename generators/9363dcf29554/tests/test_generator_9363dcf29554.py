"""Focused regression, oracle-parity, and curriculum tests for 9363dcf29554."""
from __future__ import annotations

import copy
import importlib
import itertools
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.runner import _apply_rule, _load_bundle, _open_bridge_with_rule
from scripts.canonical_profile_gate import (
    canonical_pairs,
    canonical_rule_hash,
    canonical_rule_source,
)


TASK_ID = "9363dcf29554"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK_ID}.generator")
ROOT = Path(__file__).resolve().parents[1]
AUGMENTED_BASE = ROOT / "data/base/solutions/augmented/fd096ab6__b6853a262038.json"
TRAINING_BASE = ROOT / "data/base/solutions/training/fd096ab6__9363dcf29554.json"


def _pair(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _generated_window(
    *, seed: int, start: int, difficulty: str
) -> tuple[list[dict[str, list[list[int]]]], dict[str, list[list[int]]]]:
    demos = [
        _pair(GEN.generate(seed, start + offset, difficulty=difficulty))
        for offset in range(GEN.EXAMPLES_NEEDED)
    ]
    query_grid = GEN.generate(
        seed, start + GEN.EXAMPLES_NEEDED, difficulty=difficulty
    )
    return demos, _pair(query_grid)


def test_rule_pin_all_canonical_pairs_and_selected_sources_are_synchronized() -> None:
    source = canonical_rule_source(TASK_ID)
    assert GEN.RULE_HASH == canonical_rule_hash(TASK_ID) == "1f1739de6279"

    pairs = canonical_pairs(TASK_ID)
    assert len(pairs) == 6  # train + test from both canonical source rows
    for pair in pairs:
        frozen = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == frozen

    training = json.loads(TRAINING_BASE.read_text(encoding="utf-8"))["racket_target"]
    augmented = json.loads(AUGMENTED_BASE.read_text(encoding="utf-8"))["racket_target"]
    assert training["raw_code"] == training["target_code"] == source
    assert augmented["target_code"] == source
    assert augmented["raw_code"] != source  # executable archival search evidence
    assert augmented["canonicalization_status"] == (
        "selected_canonical_sync_archival_preserved"
    )
    assert augmented["target_status"] == (
        "selected_exact_canonical; archival_raw_execution_parity_required"
    )


def test_racket_oracle_exactness_input_purity_and_a_b_a_repeat() -> None:
    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        for pair in canonical_pairs(TASK_ID):
            grid = copy.deepcopy(pair["input"])
            before = copy.deepcopy(grid)
            assert _apply_rule(bridge, fn_name, grid) == pair["output"]
            assert grid == before

        generated = [
            GEN.generate(7100 + index, index, difficulty=band)
            for index, band in enumerate(("easy", "medium", "hard", "easy"))
        ]
        for grid in generated:
            before = copy.deepcopy(grid)
            assert _apply_rule(bridge, fn_name, grid) == GEN.rule_mirror(grid)
            assert grid == before

        grid_a = GEN.generate(8101, 0, difficulty="easy", branch_mode="merged")
        grid_b = GEN.generate(8102, 2, difficulty="hard", branch_mode="mixed")
        answer_a = _apply_rule(bridge, fn_name, grid_a)
        answer_b = _apply_rule(bridge, fn_name, grid_b)
        assert answer_a == GEN.rule_mirror(grid_a)
        assert answer_b == GEN.rule_mirror(grid_b)
        assert _apply_rule(bridge, fn_name, grid_a) == answer_a
    finally:
        bridge.shutdown()


def test_complete_override_cartesian_product_is_exact_in_every_band() -> None:
    domains = (
        GEN.SCENE_PROFILES,
        GEN.TEMPLATE_COLORS,
        GEN.BRANCH_MODES,
        GEN.TEMPLATE_FAMILIES,
        GEN.TEMPLATE_ZONES,
    )
    keys = tuple(GEN.AXES)
    assert keys == (
        "scene_profile",
        "template_color",
        "branch_mode",
        "template_family",
        "template_zone",
    )

    for band_index, difficulty in enumerate(("easy", "medium", "hard")):
        for case_index, values in enumerate(itertools.product(*domains)):
            requested = dict(zip(keys, values))
            grid = GEN.generate(
                20_000 + 1000 * band_index + case_index,
                case_index % 17,
                difficulty=difficulty,
                **requested,
            )
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert GEN.observe_overrides(grid) == requested

    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 2, typo_axis="accepted-by-the-broken-baseline")
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 2, difficulty="extreme")
    with pytest.raises(ValueError):
        GEN.generate(1, 2, scene_profile="canonical_23")
    with pytest.raises(ValueError):
        GEN.generate(1, 2, template_color=1)


def test_profiles_template_roles_and_branch_semantics_are_observable() -> None:
    for profile, (size, template_size, palette_size) in GEN.PROFILE_SPECS.items():
        for branch in GEN.BRANCH_MODES:
            grid = GEN.generate(
                404,
                template_size,
                difficulty="medium",
                scene_profile=profile,
                template_color=2,
                branch_mode=branch,
                template_family="novel",
                template_zone="center",
            )
            facts = GEN._analyze(grid)
            observed = GEN.observe_overrides(grid)
            assert facts["errors"] == []
            assert (len(grid), len(grid[0])) == (size, size)
            assert facts["template_size"] == template_size
            assert facts["palette_size"] == palette_size
            assert facts["template_color"] == 2
            assert 4 in facts["colors"]  # yellow is deliberately only a fragment
            assert facts["branch_mode"] == branch
            assert observed == {
                "scene_profile": profile,
                "template_color": 2,
                "branch_mode": branch,
                "template_family": "novel",
                "template_zone": "center",
            }
            assert GEN.rule_mirror(grid) != grid

            if branch in {"merged", "mixed"}:
                merged = [
                    item
                    for item in facts["color_facts"].values()
                    if item["mode"] == "merged"
                ]
                assert merged
                assert all(item["component_count"] > 1 for item in merged)
                assert all(item["whole_origin_count"] > 0 for item in merged)
                assert all(len(item["selected_origins"]) == 1 for item in merged)
                assert GEN.SEMANTIC_RIVALS["connected fragments only"](grid) != (
                    GEN.rule_mirror(grid)
                )
            if branch in {"fallback", "mixed"}:
                fallback = [
                    item
                    for item in facts["color_facts"].values()
                    if item["mode"] == "fallback"
                ]
                assert fallback
                assert all(item["whole_origin_count"] == 0 for item in fallback)
                assert all(item["component_count"] >= 2 for item in fallback)
                assert all(len(item["selected_origins"]) >= 2 for item in fallback)
                assert GEN.SEMANTIC_RIVALS["whole color only"](grid) != (
                    GEN.rule_mirror(grid)
                )


def test_every_sliding_lesson_window_identifies_rule_and_kills_named_rivals() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(15):
            demos, query = _generated_window(
                seed=30_000 + start, start=start, difficulty=difficulty
            )
            assert GEN.lesson_identifiable(demos, query) == []
            facts = [GEN.semantic_observables(demo["input"]) for demo in demos]
            assert {item["scene_profile"] for item in facts} == set(GEN.SCENE_PROFILES)
            assert {item["template_family"] for item in facts} == set(
                GEN.TEMPLATE_FAMILIES
            )
            assert any(item["has_merged"] for item in facts)
            assert any(item["has_fallback"] for item in facts)
            assert any(item["yellow_is_fragment"] for item in facts)

            for witness_name, rival_names in GEN.WITNESS_RIVALS.items():
                witness = next(
                    demo["input"]
                    for demo in demos
                    if GEN.SEMANTIC_WITNESSES[witness_name](demo["input"])
                )
                truth = GEN.rule_mirror(witness)
                for rival_name in rival_names:
                    assert GEN.SEMANTIC_RIVALS[rival_name](witness) != truth


def test_structural_mutations_and_negative_recombination_fail_closed() -> None:
    fixtures = GEN.mutation_fixtures()
    assert len(fixtures) >= 4
    for name, grid in fixtures:
        assert GEN.self_check(grid), name
        with pytest.raises(ValueError, match="invalid template-completion input"):
            GEN.rule_mirror(grid)

    grid = GEN.generate(93_621, 2, difficulty="medium", branch_mode="mixed")
    facts = GEN._analyze(grid)
    template_color = facts["template_color"]
    fragment_color = next(color for color in facts["colors"] if color != template_color)
    recombined = copy.deepcopy(grid)
    for row_index, row in enumerate(recombined):
        for col_index, value in enumerate(row):
            if value == fragment_color:
                recombined[row_index][col_index] = GEN.BACKGROUND

    # Replace the removed fragment with a singleton feature. No remaining color
    # has that one-cell morphology, so this is a true absent-feature recombination.
    replacement = next(
        (row, col)
        for row in range(len(recombined))
        for col in range(len(recombined[0]))
        if recombined[row][col] == GEN.BACKGROUND
    )
    recombined[replacement[0]][replacement[1]] = fragment_color
    assert all(
        len(GEN._positions_of(recombined, color)) != 1
        for color in GEN._present_colors(recombined)
        if color != fragment_color
    )
    assert GEN.self_check(recombined)

    bundle = _load_bundle(TASK_ID)
    bridge, fn_name = _open_bridge_with_rule(bundle.rule_callable_text)
    try:
        before = copy.deepcopy(recombined)
        output = _apply_rule(bridge, fn_name, recombined)
    finally:
        bridge.shutdown()
    assert recombined == before
    assert len(output) == len(recombined)
    assert all(len(row) == len(recombined[0]) for row in output)


def test_determinism_fresh_returns_input_purity_and_global_rng_purity() -> None:
    random.seed(20260815)
    state = random.getstate()
    first = GEN.generate(12345, 678, difficulty="hard")
    assert random.getstate() == state
    frozen = copy.deepcopy(first)
    assert GEN.rule_mirror(first) != first
    assert GEN.observe_overrides(first)
    assert first == frozen
    assert random.getstate() == state

    second = GEN.generate(12345, 678, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == GEN.generate(12345, 678, difficulty="hard")
