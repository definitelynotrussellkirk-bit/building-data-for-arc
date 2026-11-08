from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
PROTO = HOME / "workspace" / "parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def _modules():
    return (
        _load("family_4b326abc33f4", PROTO / "family.py"),
        _load("adapter_4b326abc33f4", PROTO / "adapter.py"),
    )


def test_contract_declares_exact_canonical_default_and_supported_counts():
    family, adapter = _modules()
    contract = json.loads((PROTO / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/4b326abc33f4/workspace/parametric/adapter.py",
        "resources": [
            "generators/4b326abc33f4/workspace/parametric/family.py",
            "generators/4b326abc33f4/workspace/parametric/canonical.rkt",
            "generators/4b326abc33f4/workspace/parametric/cyclic-next.rkt",
        ],
        "parameters": {"assignment_mode": ["local", "cyclic_next"]},
        "default": {"assignment_mode": "local"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
    }
    assert adapter.program({"assignment_mode": "local"}) == family.CANONICAL_PROGRAM
    assert adapter.program({"assignment_mode": "cyclic_next"}) == family.CYCLIC_NEXT_PROGRAM


def test_generate_has_matched_inputs_independent_counts_and_distinct_pairs():
    family, adapter = _modules()
    for demos in (2, 3, 6):
        for queries in (1, 4):
            local = adapter.generate(31, {"assignment_mode": "local"}, demos, queries)
            cyclic = adapter.generate(31, {"assignment_mode": "cyclic_next"}, demos, queries)
            assert [p["input"] for p in local["train"] + local["test"]] == [
                p["input"] for p in cyclic["train"] + cyclic["test"]
            ]
            all_inputs = [p["input"] for p in local["train"] + local["test"]]
            assert len(all_inputs) == len({json.dumps(grid) for grid in all_inputs})
            assert len(local["train"]) == demos
            assert len(local["test"]) == queries
            for mode, episode in (("local", local), ("cyclic_next", cyclic)):
                for pair in episode["train"] + episode["test"]:
                    assert pair["output"] == family.apply_mode(pair["input"], mode)


def test_smallest_two_demo_lesson_identifies_settings_and_refutes_named_rivals():
    family, adapter = _modules()
    for seed in range(48):
        for mode in family.MODES:
            episode = adapter.generate(seed, {"assignment_mode": mode}, 2, 4)
            demos = episode["train"]
            assert family.setting_survivors(demos) == [mode]
            assert family.rival_survivors(demos, mode) == []


def test_minimum_lesson_refutes_order_rank_and_seed_side_partial_shortcuts():
    family, adapter = _modules()
    expected = {
        "center_row_order_next",
        "area_order_next",
        "color_rank_order_next",
        "left_side_next_right_local",
        "right_side_next_left_local",
        "rotate_first_three_only",
        "rotate_last_three_only",
    }
    assert expected <= set(family.RIVALS)
    for seed in range(128):
        for mode in family.MODES:
            episode = adapter.generate(seed, {"assignment_mode": mode}, 2, 4)
            assert family.rival_survivors(episode["train"], mode) == []


def test_seed_82_does_not_collapse_cyclic_next_into_numeric_color_sort():
    family, adapter = _modules()
    episode = adapter.generate(82, {"assignment_mode": "cyclic_next"}, 2, 4)
    assert "sort_seed_colors" not in family.rival_survivors(episode["train"], "cyclic_next")


def test_query_bank_covers_boundaries_order_confounds_and_substantive_30x30():
    family, adapter = _modules()
    episode = adapter.generate(91, {"assignment_mode": "cyclic_next"}, 3, 4)
    queries = episode["test"]
    assert [tuple(map(len, (q["input"], q["input"][0]))) for q in queries] == [
        (12, 20),
        (20, 16),
        (24, 24),
        (30, 30),
    ]
    large = queries[-1]["input"]
    frames = family.analyze_frames(large)
    assert len(frames) == 4
    assert all(any(cell != 0 for cell in row) for row in (large[:10] + large[-10:]))
    occupied_cols = {c for row in large for c, cell in enumerate(row) if cell != 0}
    assert min(occupied_cols) <= 2 and max(occupied_cols) >= 27
    assert family.has_reading_order_confound(queries[1]["input"])
    assert any(frame["boundary_contacts"] for frame in family.analyze_frames(queries[0]["input"]))


def test_crossed_controls_change_intermediate_without_nuisance_and_vice_versa():
    family, _ = _modules()
    controls = family.crossed_controls(123)
    same_geometry_a, same_geometry_b = controls["same_geometry_different_intermediate"]
    assert family.geometry_signature(same_geometry_a) == family.geometry_signature(same_geometry_b)
    assert family.seed_sequence(same_geometry_a) != family.seed_sequence(same_geometry_b)
    assert family.apply_mode(same_geometry_a, "cyclic_next") != family.apply_mode(same_geometry_b, "cyclic_next")

    same_intermediate_a, same_intermediate_b = controls["same_intermediate_different_geometry"]
    assert family.seed_sequence(same_intermediate_a) == family.seed_sequence(same_intermediate_b)
    assert family.geometry_signature(same_intermediate_a) != family.geometry_signature(same_intermediate_b)


def test_bad_settings_counts_and_boolean_counts_are_rejected():
    _, adapter = _modules()
    with pytest.raises(ValueError, match="exactly"):
        adapter.program({})
    with pytest.raises(ValueError, match="undeclared"):
        adapter.program({"assignment_mode": "reverse"})
    with pytest.raises(TypeError, match="integer"):
        adapter.generate(0, {"assignment_mode": "local"}, True, 4)
    with pytest.raises(ValueError, match="2..6"):
        adapter.generate(0, {"assignment_mode": "local"}, 1, 4)
    with pytest.raises(ValueError, match="1..4"):
        adapter.generate(0, {"assignment_mode": "local"}, 2, 5)


def test_adapter_is_deterministic_fresh_and_global_rng_neutral():
    _, adapter = _modules()
    random.seed(123456789)
    state = random.getstate()
    first = adapter.generate(19, {"assignment_mode": "cyclic_next"}, 3, 4)
    assert random.getstate() == state
    second = adapter.generate(19, {"assignment_mode": "cyclic_next"}, 3, 4)
    assert first == second
    assert first is not second
    first["train"][0]["input"][0][0] = 9
    assert second == adapter.generate(19, {"assignment_mode": "cyclic_next"}, 3, 4)


def test_causal_intermediate_is_non_collapsing():
    family, adapter = _modules()
    episode = adapter.generate(7, {"assignment_mode": "cyclic_next"}, 2, 4)
    grid = episode["test"][0]["input"]
    sequence = family.seed_sequence(grid)
    assert len(sequence) >= 3 and len(set(sequence)) >= 3
    official = family.apply_mode(grid, "cyclic_next")
    wrong = family.apply_mode(grid, "local")
    assert official != wrong
    assert family.rotated_seed_sequence(sequence) != sequence
