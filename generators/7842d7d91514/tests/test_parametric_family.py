"""Focused contract tests for the native parametric family of 7842d7d91514."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_ID = "7842d7d91514"
TASK_DIR = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_DIR / "workspace" / "parametric"
ROOT = TASK_DIR.parents[1]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

_NEIGHBORS = ((-1, 0), (0, -1), (0, 1), (1, 0))


def _load_module(filename: str, name: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing native parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def family():
    return _load_module("prototype.py", "parametric_7842d7d91514_under_test")


def _canonical_program() -> str:
    path = (
        ROOT
        / "shared/data/base/solutions/banks/d1c8811eb453"
        / "find_the_candidate_matching_the_template__7842d7d91514.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))["racket_target"]["target_code"]


def _signature(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _components(grid: list[list[int]], color: int) -> list[list[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r0 in range(height):
        for c0 in range(width):
            if grid[r0][c0] != color or (r0, c0) in seen:
                continue
            todo = [(r0, c0)]
            seen.add((r0, c0))
            cells: list[tuple[int, int]] = []
            while todo:
                r, c = todo.pop()
                cells.append((r, c))
                for dr, dc in _NEIGHBORS:
                    point = (r + dr, c + dc)
                    if (
                        0 <= point[0] < height
                        and 0 <= point[1] < width
                        and point not in seen
                        and grid[point[0]][point[1]] == color
                    ):
                        seen.add(point)
                        todo.append(point)
            result.append(sorted(cells))
    return result


def _normalize(cells: list[tuple[int, int]] | tuple[tuple[int, int], ...]):
    top = min(r for r, _ in cells)
    left = min(c for _, c in cells)
    return tuple(sorted((r - top, c - left) for r, c in cells))


def _rotate(shape):
    normalized = _normalize(shape)
    height = max(r for r, _ in normalized) + 1
    return _normalize([(c, height - 1 - r) for r, c in normalized])


def _reflect(shape):
    normalized = _normalize(shape)
    width = max(c for _, c in normalized) + 1
    return _normalize([(r, width - 1 - c) for r, c in normalized])


def _rotations(shape):
    current = _normalize(shape)
    result = []
    for _ in range(4):
        result.append(current)
        current = _rotate(current)
    return tuple(result)


def _dihedral(shape):
    rotations = _rotations(shape)
    return set(rotations) | {_reflect(item) for item in rotations}


def _target_shapes(input_grid, output_grid):
    return {_normalize(component) for component in _components(output_grid, 4)}


def test_default_program_is_the_exact_selected_canonical_source(family):
    assert family.DEFAULT_SETTINGS == {"target_rule": "exact"}
    assert family.program(family.DEFAULT_SETTINGS) == _canonical_program()
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == _canonical_program()


def test_finite_space_materializes_two_distinct_complete_programs(family):
    expected = [
        {"target_rule": "exact"},
        {"target_rule": "selector_rotation"},
    ]
    assert family.settings_space() == expected
    programs = [family.program(setting) for setting in expected]
    assert len(set(programs)) == 2
    assert all(source.startswith("(rule! (lambda") for source in programs)
    assert all(source.endswith("))))") for source in programs)


@pytest.mark.parametrize(
    "settings",
    [
        None,
        [],
        {},
        {"target_rule": "clockwise"},
        {"target_rule": "exact", "extra": 0},
        {"target_rule": 1},
        {"target_rule": True},
    ],
)
def test_settings_are_exact_and_typed(family, settings):
    with pytest.raises(ValueError):
        family.program(settings)


def test_selector_count_drives_a_real_two_step_rotation_then_match(family):
    inputs = family.sample_inputs(seed=17, demos=2, queries=4)["train"]
    assert [len(_components(grid, 8)[0]) for grid in inputs] == [2, 4]
    expected_turns = [1, 3]
    for grid, turns in zip(inputs, expected_turns):
        template = _normalize(_components(grid, 5)[0])
        expected_target = template
        for _ in range(turns):
            expected_target = _rotate(expected_target)
        exact = family.transform(grid, {"target_rule": "exact"})
        selected = family.transform(grid, {"target_rule": "selector_rotation"})
        assert exact != selected
        assert _target_shapes(grid, exact) == {template}
        assert _target_shapes(grid, selected) == {expected_target}
        trace = family.causal_trace(grid)
        assert trace["selector_cells"] == len(_components(grid, 8)[0])
        assert trace["quarter_turns"] == turns
        assert tuple(map(tuple, trace["target_shape"])) == expected_target


def test_wrong_intermediate_changes_the_downstream_candidate_decision(family):
    grid = family.sample_inputs(seed=0, demos=2, queries=4)["train"][1]
    assert family.causal_trace(grid)["quarter_turns"] == 3
    intended = family.transform(grid, {"target_rule": "selector_rotation"})
    wrong = family.transform_with_turns(grid, 1)
    assert intended != wrong
    assert _target_shapes(grid, intended) != _target_shapes(grid, wrong)


def test_sampler_is_deterministic_setting_independent_and_count_stable(family):
    first = family.sample_inputs(seed=17, demos=2, queries=4)
    second = family.sample_inputs(seed=17, demos=2, queries=4)
    extended = family.sample_inputs(seed=17, demos=6, queries=4)
    assert first == second
    assert first["train"] == extended["train"][:2]
    assert first["test"] == extended["test"]
    all_inputs = first["train"] + first["test"]
    assert len({_signature(grid) for grid in all_inputs}) == len(all_inputs)
    assert [(len(grid), len(grid[0])) for grid in first["test"]] == [
        (13, 15),
        (18, 22),
        (24, 27),
        (30, 30),
    ]


@pytest.mark.parametrize("seed", [0, 17, 9917])
def test_every_scene_has_a_chiral_template_all_rotations_and_both_output_branches(family, seed):
    sampled = family.sample_inputs(seed=seed, demos=6, queries=4)
    for grid in sampled["train"] + sampled["test"]:
        assert {cell for row in grid for cell in row} == {0, 2, 5, 8}
        templates = _components(grid, 5)
        selectors = _components(grid, 8)
        candidates = _components(grid, 2)
        assert len(templates) == 1
        assert len(selectors) == 1
        assert len(selectors[0]) in {2, 4}
        assert len(candidates) >= 4
        template = _normalize(templates[0])
        candidate_shapes = {_normalize(component) for component in candidates}
        assert len(set(_rotations(template))) == 4
        assert len(_dihedral(template)) == 8
        assert set(_rotations(template)) <= candidate_shapes
        assert all(len(component) == len(templates[0]) for component in candidates)
        for setting in family.settings_space():
            output = family.transform(grid, setting)
            assert _components(output, 4)
            assert _components(output, 1)
            assert _components(output, 5) == templates
            assert _components(output, 8) == selectors


def test_minimum_demonstrations_teach_both_selector_cases(family):
    for seed in (0, 17, 9917):
        demos = family.sample_inputs(seed=seed, demos=2, queries=4)["train"]
        assert [len(_components(grid, 8)[0]) for grid in demos] == [2, 4]


@pytest.mark.parametrize("seed", [0, 17, 9917])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_demonstrations_identify_each_setting_and_reject_named_shortcuts(family, seed, demos):
    for setting in family.settings_space():
        episode = family.generate_episode(seed, setting, demos=demos, queries=4)
        certificate = family.lesson_certificate(
            episode["train"], [pair["input"] for pair in episode["test"]]
        )
        assert certificate["surviving_settings"] == [setting]
        assert certificate["surviving_shortcuts"] == []
        assert certificate["ambiguous_queries"] == []
        assert certificate["query_outputs_consulted"] is False
        assert certificate["scope"].startswith("finite")


def test_shortcut_audit_has_specific_competitors_and_two_demo_rejections(family):
    expected = {
        "identity",
        "all_candidates_yellow",
        "all_candidates_blue",
        "same_cell_count",
        "dihedral_match",
        "fixed_clockwise",
        "fixed_counterclockwise",
        "fixed_half_turn",
        "reversed_selector_mapping",
        "topmost_candidate_only",
    }
    for setting in family.settings_space():
        episode = family.generate_episode(41, setting, demos=2, queries=4)
        observed = set(family.shortcut_outputs(episode["train"][0]["input"], setting))
        assert observed == expected
        for name in expected:
            assert not all(
                family.shortcut_outputs(pair["input"], setting)[name] == pair["output"]
                for pair in episode["train"]
            ), (setting, name)


def test_queries_cover_transfer_boundary_and_maximum_stress(family):
    episode = family.generate_episode(23, family.DEFAULT_SETTINGS, demos=3, queries=4)
    queries = [pair["input"] for pair in episode["test"]]
    assert (len(queries[-1]), len(queries[-1][0])) == (30, 30)
    assert len(_components(queries[0], 2)) == 6
    assert len(_components(queries[1], 2)) == 10
    assert len(_components(queries[2], 2)) == 14
    assert len(_components(queries[3], 2)) == 20
    boundary = queries[2]
    assert any(cell == 2 for cell in boundary[0])
    assert any(cell == 2 for cell in boundary[-1])
    assert any(row[0] == 2 for row in boundary)
    assert any(row[-1] == 2 for row in boundary)
    stress = queries[-1]
    assert sum(cell != 0 for row in stress for cell in row) >= 120
    assert sum(cell == 2 for row in stress for cell in row) >= 100


def test_public_projection_and_id_ignore_private_rule_and_query_labels(family):
    episode = family.generate_episode(41, family.DEFAULT_SETTINGS, demos=3, queries=4)
    public = family.public_projection(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    identifier = family.episode_id(episode)

    changed = copy.deepcopy(episode)
    changed["settings"] = {"target_rule": "selector_rotation"}
    changed["program_solution"] = "private replacement"
    changed["certificate"] = {"private": True}
    changed["test"][0]["output"][0][0] = (changed["test"][0]["output"][0][0] + 1) % 10
    assert family.public_projection(changed) == public
    assert family.episode_id(changed) == identifier


def test_single_query_turn_hides_future_queries_and_uses_public_bytes(family):
    from reviewer_support import public_challenge_bytes, public_challenge_id

    episode = family.generate_episode(41, family.DEFAULT_SETTINGS, demos=3, queries=4)
    expected_challenge = {"train": episode["train"], "test": [episode["test"][0]]}
    expected_bytes = public_challenge_bytes(expected_challenge)
    assert family.visible_turn_bytes(episode, 0) == expected_bytes
    assert family.visible_turn(episode, 0) == json.loads(expected_bytes)
    assert family.visible_turn_id(episode, 0) == public_challenge_id(expected_challenge)
    visible = family.visible_turn(episode, 0)
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1
    assert set(visible["test"][0]) == {"input"}
    assert not ({"settings", "program_solution", "seed", "query_index", "query_count"} & set(visible))

    changed = copy.deepcopy(episode)
    changed["settings"] = {"target_rule": "selector_rotation"}
    changed["program_solution"] = "private replacement"
    changed["test"][1]["input"][0][0] = 7
    changed["test"][3]["output"][0][0] = 6
    assert family.visible_turn_bytes(changed, 0) == expected_bytes
    assert family.visible_turn_id(changed, 0) == family.visible_turn_id(episode, 0)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "settings": {"target_rule": "exact"}, "demos": 3, "queries": 4},
        {"seed": 0, "settings": {"target_rule": "exact"}, "demos": 1, "queries": 4},
        {"seed": 0, "settings": {"target_rule": "exact"}, "demos": 7, "queries": 4},
        {"seed": 0, "settings": {"target_rule": "exact"}, "demos": 3, "queries": 3},
        {"seed": 0, "settings": {"target_rule": "exact"}, "demos": 3, "queries": True},
    ],
)
def test_generation_rejects_invalid_counts_and_types(family, kwargs):
    with pytest.raises(ValueError):
        family.generate_episode(**kwargs)


def test_native_adapter_delegates_exact_program_and_episode(family):
    adapter = _load_module("adapter.py", "parametric_adapter_7842d7d91514_under_test")
    for setting in family.settings_space():
        assert adapter.program(setting) == family.program(setting)
        generated = adapter.generate(17, setting, 3, 4)
        assert generated == family.generate_episode(17, setting, demos=3, queries=4)


def test_promotion_contract_declares_the_exact_finite_family(family):
    path = PARAMETRIC / "promotion.json"
    assert path.is_file(), "missing native promotion contract"
    contract = json.loads(path.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"target_rule": ["exact", "selector_rotation"]},
        "default": family.DEFAULT_SETTINGS,
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 2,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
        ],
    }


def test_replayable_audit_preflight_summarizes_finite_teaching_scope(family, tmp_path):
    audit = _load_module("audit.py", "parametric_audit_7842d7d91514_under_test")
    report = audit.build_report(seeds=[0], demo_counts=[2], run_racket=False)
    assert report["schema"] == "arcpuzzles-parametric-prototype-audit-v1"
    assert report["task_id"] == TASK_ID
    assert report["summary"] == {
        "cases": 2,
        "programs": 2,
        "all_programs_distinct": True,
        "all_lessons_unique": True,
        "all_shortcuts_rejected": True,
        "all_inputs_setting_independent": True,
        "query_outputs_consulted": False,
        "racket_checked": False,
        "racket_labels_match": None,
        "racket_declared_unique": None,
        "racket_rivals_rejected": None,
    }
    assert all(case["query_shapes"][-1] == [30, 30] for case in report["cases"])
    target = tmp_path / "audit.json"
    audit.write_report(target, report)
    assert json.loads(target.read_text(encoding="utf-8")) == report
