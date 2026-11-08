"""Behavioral contract for the template-width marker-selection family."""
from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes

TASK = "06b4c496c6cf"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK
ADAPTER_PATH = HOME / "workspace" / "parametric" / "adapter.py"
ALL = {"marker_selection": "all"}
WIDTH = {"marker_selection": "template_width"}


def _load_adapter():
    assert ADAPTER_PATH.is_file(), "parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location(
        "_06b4c496c6cf_parametric_tests", ADAPTER_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        rows = (json.loads(line) for line in handle)
        return next(row["program_solution"] for row in rows if row["task_id"] == TASK)


def _input_bytes(episode):
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for pair in episode["train"] + episode["test"]
    ]


def _public(episode, queries=None):
    tests = episode["test"] if queries is None else episode["test"][:queries]
    return {"train": episode["train"], "test": tests}


def test_default_program_is_exact_canonical_and_alternative_is_distinct():
    adapter = _load_adapter()
    canonical = _canonical_program()
    assert adapter.program(ALL) == canonical
    assert adapter.program(WIDTH) != canonical
    assert adapter.program(WIDTH).startswith("(rule! ")


def test_template_width_selects_target_marker_color_before_stamping():
    adapter = _load_adapter()
    witness = adapter.sequential_witness()
    assert witness["settings"] == WIDTH
    assert witness["step_a"] == "measure the bounding-box width of the unique color-2 template"
    assert witness["intermediate_name"] == "target marker color = template width + 5"
    assert witness["intermediate_value"] in (6, 7, 8, 9)
    assert witness["correct_output"] != witness["wrong_intermediate_output"]
    assert adapter.solve(witness["input"], WIDTH) == witness["correct_output"]


@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_all_supported_demo_counts_identify_each_setting_and_refute_declared_rivals(demos):
    adapter = _load_adapter()
    inputs_by_setting = []
    for settings in (ALL, WIDTH):
        episode = adapter.generate(17, settings, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program(settings)
        assert len(_input_bytes(episode)) == len(set(_input_bytes(episode)))
        report = adapter.lesson_report(episode, settings)
        assert report["surviving_rivals"] == []
        assert report["query_disagreements"] == []
        inputs_by_setting.append(_input_bytes(episode))
    assert inputs_by_setting[0] == inputs_by_setting[1]


@pytest.mark.parametrize("queries", [1, 2, 3, 4])
def test_query_counts_are_prefix_stable_and_first_turn_matches_single_query(queries):
    adapter = _load_adapter()
    one = adapter.generate(33, WIDTH, 3, 1)
    many = adapter.generate(33, WIDTH, 3, queries)
    assert one["train"] == many["train"]
    assert one["test"][0] == many["test"][0]
    assert public_challenge_bytes(_public(one)) == public_challenge_bytes(_public(many, 1))


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    adapter = _load_adapter()
    state = random.getstate()
    first = adapter.generate(9, WIDTH, 3, 4)
    assert random.getstate() == state
    second = adapter.generate(9, WIDTH, 3, 4)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 9
    assert adapter.generate(9, WIDTH, 3, 4) == second


def test_claim_labels_follow_each_python_rule_semantics():
    adapter = _load_adapter()
    for seed in (0, 17, 81):
        for settings in (ALL, WIDTH):
            episode = adapter.generate(seed, settings, 2, 4)
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == adapter.solve(pair["input"], settings)


def test_canonical_python_solver_uses_higher_color_precedence_on_overlap():
    adapter = _load_adapter()
    pair = adapter.generate(17, ALL, 3, 4)["test"][0]
    facts = adapter.analyze(pair["input"])
    assert (9, 21) in {(r, c) for r, c, color in facts["markers"] if color == 9}
    assert (17, 21) in {(r, c) for r, c, color in facts["markers"] if color == 7}
    assert pair["output"][17][21] == 9


def test_seed4_minimum_curriculum_refutes_selected_marker_cells_only():
    adapter = _load_adapter()
    episode = adapter.generate(4, WIDTH, 2, 4)
    marker_only_differs = [
        pair["output"]
        != adapter.rival_outputs(pair["input"])["selected_marker_cells_only"]
        for pair in episode["train"]
    ]
    assert any(marker_only_differs)
    assert adapter.lesson_report(episode, WIDTH)["surviving_rivals"] == []


def test_width_selected_rule_stamps_every_marker_of_the_selected_color():
    adapter = _load_adapter()
    episode = adapter.generate(17, WIDTH, 2, 4)
    first = episode["train"][0]
    facts = adapter.analyze(first["input"])
    assert facts["target_color"] == 7
    assert facts["marker_color_counts"][7] == 2
    expected_cells = adapter.stamped_cells(first["input"], target_color=7)
    assert expected_cells
    assert {first["output"][r][c] for r, c in expected_cells} == {7}
    assert len(expected_cells) > len(facts["template_offsets"])


def test_30x30_query_has_substantive_spread_density_and_boundary_contacts():
    adapter = _load_adapter()
    grid = adapter.generate(7, WIDTH, 3, 4)["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    facts = adapter.analyze(grid)
    assert facts["template_width"] == 3
    assert len(facts["template_offsets"]) >= 24
    assert facts["marker_count"] == 6
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(occupied) >= 30
    assert {r // 15 for r, _ in occupied} == {0, 1}
    assert {c // 15 for _, c in occupied} == {0, 1}
    assert any(r in (0, 29) or c in (0, 29) for r, c in facts["marker_cells"])


def test_demo_and_query_profiles_cover_all_template_widths_and_target_colors():
    adapter = _load_adapter()
    episode = adapter.generate(29, WIDTH, 6, 4)
    facts = [adapter.analyze(pair["input"]) for pair in episode["train"] + episode["test"]]
    assert {row["template_width"] for row in facts} == {1, 2, 3, 4}
    assert {row["target_color"] for row in facts} == {6, 7, 8, 9}


@pytest.mark.parametrize("settings", [
    {},
    {"marker_selection": True},
    {"marker_selection": "other"},
    {"marker_selection": "all", "extra": 1},
])
def test_invalid_settings_are_rejected(settings):
    adapter = _load_adapter()
    with pytest.raises(ValueError):
        adapter.generate(0, settings, 3, 4)


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 3, 4),
    (-1, 3, 4),
    (0, 1, 4),
    (0, 7, 4),
    (0, True, 4),
    (0, 3, 0),
    (0, 3, 5),
    (0, 3, True),
])
def test_invalid_seed_and_count_boundaries_are_rejected(seed, demos, queries):
    adapter = _load_adapter()
    with pytest.raises(ValueError):
        adapter.generate(seed, WIDTH, demos, queries)


def test_analysis_rejects_malformed_or_out_of_grammar_grids():
    adapter = _load_adapter()
    bad = [
        [],
        [[0, 0], [0]],
        [[True]],
        [[0] * 31],
        [[0, 3], [0, 0]],
        [[2, 2], [2, 2]],
    ]
    for grid in bad:
        with pytest.raises(ValueError):
            adapter.analyze(grid)


def test_declared_programs_match_python_claims_under_protected_racket():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    adapter = _load_adapter()
    runtime = ROOT / "shared" / "runtime"
    with _local_imports(runtime, ADAPTER_PATH.parent):
        execute, identity, bridge = _real_evaluator(runtime)
        assert identity["backend"] == "racket"
        assert identity["protected"] is True
        try:
            for seed in (0, 17):
                for settings in (ALL, WIDTH):
                    episode = adapter.generate(seed, settings, 2, 4)
                    for pair in episode["train"] + episode["test"]:
                        assert execute(adapter.program(settings), pair["input"]) == pair["output"]
        finally:
            bridge.close()


def test_reusable_audit_covers_seed_demo_setting_matrix_without_findings():
    path = HOME / "workspace" / "parametric" / "audit.py"
    assert path.is_file(), "bounded audit tool has not been built"
    spec = importlib.util.spec_from_file_location("_06b4c496c6cf_audit_tests", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.audit(seeds=range(4), demo_counts=range(2, 7))
    assert report["status"] == "passed"
    assert report["episodes"] == 40
    assert report["pairs"] == sum((demos + 4) * 2 * 4 for demos in range(2, 7))
    assert report["findings"] == []
