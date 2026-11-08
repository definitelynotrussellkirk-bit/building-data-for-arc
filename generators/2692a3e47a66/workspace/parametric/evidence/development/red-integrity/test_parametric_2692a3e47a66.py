"""Focused tests for the separate, bounded parametric prototype.

These tests do not alter or certify the selected canonical generator.
Racket integration is selected automatically when RACKET_PATH or racket is
available; use -k "not racket" for the independent Python-only controls.
"""
from __future__ import annotations

from collections import Counter
import copy
import importlib.util
import json
import os
from pathlib import Path
import random
import shutil
import sys

import pytest

TASK_ID = "2692a3e47a66"
TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_HOME / "workspace/parametric/prototype.py"


def prototype():
    # A missing implementation is an explicit feature-absence failure, not a
    # collector/import error. The first development receipt retains that red.
    assert PROTOTYPE.is_file(), "bounded parametric prototype is not implemented"
    name = "parametric_2692a3e47a66"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, PROTOTYPE)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def canvas(height=25, width=27):
    return [[7] * width for _ in range(height)]


def paint(grid, row, col, side, color):
    for r in range(row, row + side):
        for c in range(col, col + side):
            grid[r][c] = color


def count_fixture():
    grid = canvas()
    paint(grid, 0, 0, 1, 2)
    paint(grid, 0, 24, 3, 2)
    paint(grid, 21, 0, 4, 5)
    paint(grid, 23, 25, 2, 6)
    return grid


def pair_expected(step):
    result = canvas()
    if step == 1:
        paint(result, 1, 1, 1, 2)
        paint(result, 3, 21, 3, 2)
    else:
        paint(result, 2, 2, 1, 2)
        paint(result, 6, 18, 3, 2)
    paint(result, 21, 0, 4, 5)
    paint(result, 23, 25, 2, 6)
    return result


def triple_fixture():
    grid = canvas()
    paint(grid, 0, 0, 1, 2)
    paint(grid, 0, 24, 3, 2)
    paint(grid, 23, 0, 2, 2)
    paint(grid, 21, 23, 4, 5)
    return grid


def triple_expected(step):
    result = canvas()
    if step == 1:
        paint(result, 1, 1, 1, 2)
        paint(result, 3, 21, 3, 2)
        paint(result, 21, 2, 2, 2)
    else:
        paint(result, 2, 2, 1, 2)
        paint(result, 6, 18, 3, 2)
        paint(result, 19, 4, 2, 2)
    paint(result, 21, 23, 4, 5)
    return result


def test_threshold_counts_components_instead_of_pixel_area():
    p = prototype()
    original = count_fixture()
    assert p.transform_mirror(original, p.Settings(2, 1)) == pair_expected(1)
    # The large singleton contains sixteen cells but only one component.
    assert p.transform_mirror(original, p.Settings(3, 1)) == original
    assert p.transform_mirror(original, p.Settings(4, 2)) == original
    assert original == count_fixture()


def test_displacement_uses_each_objects_own_size_and_preserves_singletons():
    p = prototype()
    assert p.transform_mirror(count_fixture(), p.Settings(2, 2)) == pair_expected(2)
    assert p.transform_mirror(triple_fixture(), p.Settings(3, 1)) == triple_expected(1)
    assert p.transform_mirror(triple_fixture(), p.Settings(3, 2)) == triple_expected(2)
    assert p.transform_mirror(triple_fixture(), p.Settings(4, 1)) == triple_fixture()


def painter_fixtures():
    # Both diagnostics are deliberately outside the collision-free sampler.
    collision = canvas(5, 5)
    collision[0][0] = collision[0][4] = 0
    collision[4][0] = collision[4][4] = 9
    collision_expected = canvas(5, 5)
    collision_expected[2][2] = 9
    clearing = canvas(8, 6)
    paint(clearing, 0, 0, 2, 0)
    paint(clearing, 6, 0, 2, 0)
    paint(clearing, 0, 3, 3, 9)
    paint(clearing, 5, 3, 3, 9)
    clearing_expected = canvas(8, 6)
    for row in range(2, 6):
        for col in range(3):
            clearing_expected[row][col] = 9
    clearing_expected[3][3] = clearing_expected[4][3] = 0
    return [(collision, 2, collision_expected), (clearing, 1, clearing_expected)]


def test_diagnostic_mirror_preserves_numeric_paint_order_and_per_color_source_clearing():
    p = prototype()
    for grid, step, expected in painter_fixtures():
        assert p.input_errors(grid)  # diagnostic, never lawful prototype evidence
        assert p.transform_mirror(grid, p.Settings(2, step)) == expected


def test_four_components_trigger_threshold_four():
    p = prototype()
    original = canvas()
    paint(original, 0, 0, 1, 8)
    paint(original, 0, 25, 2, 8)
    paint(original, 22, 0, 3, 8)
    paint(original, 21, 23, 4, 8)
    expected = canvas()
    paint(expected, 2, 2, 1, 8)
    paint(expected, 4, 21, 2, 8)
    paint(expected, 16, 6, 3, 8)
    paint(expected, 13, 15, 4, 8)
    assert p.transform_mirror(original, p.Settings(4, 2)) == expected


@pytest.mark.parametrize(
    "threshold,step",
    [(True, 1), (2, False), (1, 1), (5, 1), (2, 0), (2, 3),
     (2.0, 1), ("2", 1), (2, 1.0), (None, 1)],
)
def test_rejects_boolean_noninteger_and_out_of_range_settings(threshold, step):
    p = prototype()
    with pytest.raises(ValueError):
        p.Settings(threshold, step)


def test_default_program_is_exact_canonical_text_and_mirror_matches_all_five_pairs():
    p = prototype()
    from reviewer_support import canonical_pairs, canonical_path

    with canonical_path(p.ROOT).open(encoding="utf-8") as source:
        selected = [json.loads(line) for line in source
                    if '"task_id": "2692a3e47a66"' in line
                    or '"task_id":"2692a3e47a66"' in line]
    assert len(selected) == 1
    assert p.emit_program(p.Settings()) == selected[0]["program_solution"]
    pairs = canonical_pairs(TASK_ID, root=p.ROOT)
    assert len(pairs) == 5
    assert {(x["variant"], x["split"], x["pair_index"]) for x in pairs} == {
        (0, "train", 0), (0, "train", 1), (0, "train", 2),
        (0, "train", 3), (0, "test", 0),
    }
    for pair in pairs:
        assert p.transform_mirror(pair["input"], p.Settings()) == pair["output"]


def test_sampler_is_reproducible_rng_local_distinct_and_safe_for_all_six_settings():
    p = prototype()
    random.seed(1907)
    before = random.getstate()
    signatures = set()
    shapes = set()
    colors = set()
    for seed in (0, 71, 20261019):
        plan = p.plan_episode(seed)
        assert plan == p.plan_episode(seed)
        assert set(plan) == {"seed", "settings", "settings_selection", "draws"}
        assert len(plan["draws"]) == 7
        multiplicities = Counter(x["multiplicity"] for x in plan["draws"])
        assert all(multiplicities[n] >= 2 for n in (2, 3, 4))
        for draw in plan["draws"]:
            grid = draw["input"]
            signature = p.grid_sha256(grid)
            assert signature not in signatures
            signatures.add(signature)
            assert p.input_errors(grid) == []
            corner_counts = Counter((grid[0][0], grid[0][-1], grid[-1][0], grid[-1][-1]))
            assert max(corner_counts.values()) == draw["multiplicity"]
            shapes.add((len(grid), len(grid[0])))
            colors.update(cell for row in grid for cell in row)
            for setting in p.ALL_SETTINGS:
                result = p.transform_mirror(grid, setting)
                assert Counter(cell for row in grid for cell in row) == Counter(
                    cell for row in result for cell in row
                ), (seed, draw["draw_index"], setting)
    assert random.getstate() == before
    assert len(shapes) >= 3
    assert len(colors) >= 6


def test_episode_has_one_fixed_setting_and_input_draws_do_not_encode_it():
    p = prototype()
    left = p.plan_episode(71, p.Settings(2, 1))
    right = p.plan_episode(71, p.Settings(4, 2))
    assert left["draws"] == right["draws"]
    assert left["settings"] == {"min_repeat": 2, "step_blocks": 1}
    assert right["settings"] == {"min_repeat": 4, "step_blocks": 2}
    assert all("settings" not in row for row in left["draws"])
    assert p.plan_episode(71)["settings_selection"] == "seeded_once"
    assert p.plan_episode(71)["settings"] == p.select_settings(71).as_dict()


def test_public_projection_contains_only_demonstrations_and_an_unlabelled_query():
    p = prototype()
    pairs = [
        {"input": [[i]], "output": [[9 - i]], "settings": {"secret": i},
         "seed": i, "program": "(rule! secret)", "query_answer": [[9 - i]]}
        for i in range(7)
    ]
    before = copy.deepcopy(pairs)
    for query_index in range(7):
        public = p.public_challenge(pairs, query_index=query_index)
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 6
        assert len(public["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert set(public["test"][0]) == {"input"}
        assert public["test"][0]["input"] == pairs[query_index]["input"]
        public["test"][0]["input"][0][0] = 0
    assert pairs == before


def test_domain_rejects_clipping_risk_and_structural_impostors():
    p = prototype()
    assert p.input_errors(count_fixture()) == []
    small = canvas(7, 7)
    for row, col in ((0, 0), (0, 6), (6, 0), (6, 6)):
        small[row][col] = 2
    assert any("25..30" in error for error in p.input_errors(small))
    noise = count_fixture()
    noise[12][12] = 3
    assert p.input_errors(noise)
    bad = count_fixture()
    bad[1][25] = 7
    assert p.input_errors(bad)
    all_unique = count_fixture()
    all_unique[0][0] = 3
    assert p.input_errors(all_unique)
    boolean = count_fixture()
    boolean[12][12] = False
    assert p.input_errors(boolean)


RACKET_AVAILABLE = bool(os.environ.get("RACKET_PATH") or shutil.which("racket"))


@pytest.fixture(scope="module")
def racket_labeler():
    p = prototype()
    with p.RacketLabeler() as labeler:
        yield labeler


@pytest.mark.skipif(not RACKET_AVAILABLE, reason="Racket integration requires the supported runtime wrapper")
def test_racket_all_six_programs_match_hand_derived_fixtures(racket_labeler):
    p = prototype()
    for setting in p.ALL_SETTINGS:
        expected_pair = pair_expected(setting.step_blocks) if setting.min_repeat == 2 else count_fixture()
        expected_triple = triple_expected(setting.step_blocks) if setting.min_repeat <= 3 else triple_fixture()
        assert racket_labeler.apply(count_fixture(), setting) == expected_pair
        assert racket_labeler.apply(triple_fixture(), setting) == expected_triple


@pytest.mark.skipif(not RACKET_AVAILABLE, reason="Racket integration requires the supported runtime wrapper")
def test_racket_default_matches_every_canonical_pair_including_overlaps(racket_labeler):
    p = prototype()
    from reviewer_support import canonical_pairs
    pairs = canonical_pairs(TASK_ID, root=p.ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        assert racket_labeler.apply(pair["input"], p.Settings()) == pair["output"]


@pytest.mark.skipif(not RACKET_AVAILABLE, reason="Racket integration requires the supported runtime wrapper")
def test_racket_complete_episodes_execute_all_six_candidates_and_every_query_placement(racket_labeler):
    p = prototype()
    signatures = set()
    for index, setting in enumerate(p.ALL_SETTINGS):
        start_count = racket_labeler.application_count
        episode = p.generate_episode(801 + index, setting, labeler=racket_labeler)
        assert racket_labeler.application_count - start_count == 42
        assert episode["private"]["settings"] == setting.as_dict()
        assert episode["private"]["audit"]["candidate_count"] == 6
        assert episode["private"]["audit"]["rule_applications"] == 42
        assert len(episode["private"]["audit"]["query_placements"]) == 7
        for placement in episode["private"]["audit"]["query_placements"]:
            assert len(placement["candidates"]) == 6
            assert placement["selected_consistent"] is True
            assert placement["surviving_alternatives"] == []
            assert placement["status"] == "identified_within_declared_settings"
        assert len(episode["public"]["train"]) == 6
        assert set(episode["public"]["test"][0]) == {"input"}
        for pair in episode["private"]["pairs"]:
            assert pair["output"] == p.transform_mirror(pair["input"], setting)
            signature = p.grid_sha256(pair["input"])
            assert signature not in signatures
            signatures.add(signature)


@pytest.mark.skipif(not RACKET_AVAILABLE, reason="Racket integration requires the supported runtime wrapper")
def test_racket_diagnostic_numeric_paint_order_and_per_color_source_clearing(racket_labeler):
    p = prototype()
    for grid, step, expected in painter_fixtures():
        assert p.input_errors(grid)
        assert racket_labeler.apply(grid, p.Settings(2, step)) == expected


def test_evidence_preflight_failure_retains_request_and_error(tmp_path, monkeypatch):
    p = prototype()
    monkeypatch.setattr(p, "ROOT", tmp_path / "missing-library")
    out = tmp_path / "preflight-evidence"
    with pytest.raises((ValueError, FileNotFoundError)):
        p.build_evidence(out, seed=12345, episodes_per_setting=1)
    failure_path = out / "private/failure.json"
    assert failure_path.is_file(), "preflight failure lost its evidence receipt"
    failure = json.loads(failure_path.read_text())
    assert failure["status"] == "failed_or_incomplete_prototype_evidence"
    assert failure["request"] == {"seed": 12345, "episodes_per_setting": 1}
    assert failure["error"]
    assert not list((out / "public").glob("*.json"))


def test_evidence_unavailable_runtime_preserves_complete_input_plans(tmp_path, monkeypatch):
    p = prototype()
    # Exercise the real bridge's unavailable-executable path. No Racket process
    # can start and no output label is invented by this failure-path control.
    monkeypatch.setenv("RACKET_PATH", str(tmp_path / "missing-racket-executable"))
    out = tmp_path / "unavailable-runtime-evidence"
    with pytest.raises(Exception):
        p.build_evidence(out, seed=12346, episodes_per_setting=1)
    failure = json.loads((out / "private/failure.json").read_text())
    assert failure.get("request") == {"seed": 12346, "episodes_per_setting": 1}
    plans = sorted((out / "private/plans").glob("*.json"))
    assert len(plans) == 7, "a startup failure must retain every planned seed, setting, and input"
    for path in plans:
        plan = json.loads(path.read_text())
        assert len(plan["draws"]) == 7
        assert all(p.input_errors(draw["input"]) == [] for draw in plan["draws"])
        assert set(plan["settings"]) == {"min_repeat", "step_blocks"}
    assert not list((out / "public").glob("*.json"))


@pytest.mark.skipif(not RACKET_AVAILABLE, reason="Racket integration requires the supported runtime wrapper")
def test_racket_ambiguous_episode_withholds_public_projection(racket_labeler, monkeypatch):
    p = prototype()
    original_plan = p.plan_episode

    def ambiguous_plan(seed, settings=None):
        plan = original_plan(seed, settings)
        plan["draws"] = [
            {"draw_index": i, "multiplicity": 4, "input": p.sample_input(seed, i, 4)}
            for i in range(7)
        ]
        return plan

    # Real Racket runs on valid inputs, but this deliberately deficient lesson
    # cannot distinguish the three thresholds. Only the input plan is supplied.
    monkeypatch.setattr(p, "plan_episode", ambiguous_plan)
    episode = p.generate_episode(9871, p.Settings(2, 1), labeler=racket_labeler)
    assert episode["private"]["audit"]["status"] == "ambiguous_or_inconsistent"
    assert episode["public"] is None
