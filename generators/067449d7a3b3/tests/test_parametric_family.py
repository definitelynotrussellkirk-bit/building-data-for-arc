"""Focused contract tests for the native parametric family of 067449d7a3b3."""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_ID = "067449d7a3b3"
TASK_DIR = Path(__file__).resolve().parents[1]
PARAMETRIC = TASK_DIR / "workspace" / "parametric"
ROOT = TASK_DIR.parents[1]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


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
    return _load_module("prototype.py", "parametric_067449d7a3b3_under_test")


def _canonical_program() -> str:
    path = ROOT / "shared" / "data" / "base" / "solutions" / "training" / "db93a21d__067449d7a3b3.json"
    return json.loads(path.read_text(encoding="utf-8"))["racket_target"]["target_code"]


def _signature(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def test_default_program_is_the_exact_selected_canonical_source(family):
    assert family.DEFAULT_SETTINGS == {"border_basis": "max_side", "connectivity": 8}
    assert family.program(family.DEFAULT_SETTINGS) == _canonical_program()
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == _canonical_program()


def test_cartesian_space_materializes_four_distinct_nearby_programs(family):
    expected = [
        {"border_basis": "max_side", "connectivity": 4},
        {"border_basis": "max_side", "connectivity": 8},
        {"border_basis": "min_side", "connectivity": 4},
        {"border_basis": "min_side", "connectivity": 8},
    ]
    assert family.settings_space() == expected
    programs = {tuple(sorted(setting.items())): family.program(setting) for setting in expected}
    assert len(set(programs.values())) == 4
    for setting, source in ((dict(key), value) for key, value in programs.items()):
        if setting["connectivity"] == 8:
            assert source.count("(objects-8 g bg)") == 1
            assert "(objects g bg)" not in source
        else:
            assert source.count("(objects g bg)") == 1
            assert "(objects-8 g bg)" not in source
        basis = "max" if setting["border_basis"] == "max_side" else "min"
        other = "min" if basis == "max" else "max"
        assert source.count(f"({basis} rh rw)") == 1
        assert f"({other} rh rw)" not in source


@pytest.mark.parametrize(
    "settings",
    [
        None,
        [],
        {},
        {"connectivity": 8},
        {"border_basis": "max_side", "connectivity": 8, "extra": 0},
        {"border_basis": "mean", "connectivity": 8},
        {"border_basis": "max_side", "connectivity": 6},
        {"border_basis": "max_side", "connectivity": True},
    ],
)
def test_settings_are_exact_and_typed(family, settings):
    with pytest.raises(ValueError):
        family.program(settings)


def test_python_rule_exposes_both_causal_axes(family):
    grid = [[0] * 13 for _ in range(11)]
    # Same-color 2x3 blocks touch only at one diagonal corner.  Their combined
    # 4x6 bounding box also makes min/max halo width observably different.
    for r in range(1, 3):
        for c in range(1, 4):
            grid[r][c] = 7
    for r in range(3, 5):
        for c in range(4, 7):
            grid[r][c] = 7
    # A separate 5x2 object keeps the halo-basis axis visible even when
    # 4-connectivity splits the diagonal compound into 2x3 lobes.
    for r in range(1, 6):
        for c in range(10, 12):
            grid[r][c] = 9
    outputs = {
        _signature(family.transform(grid, setting)): setting
        for setting in family.settings_space()
    }
    assert len(outputs) == 4


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
        (10, 10),
        (16, 18),
        (21, 14),
        (30, 30),
    ]


@pytest.mark.parametrize("seed", [0, 17, 9917])
@pytest.mark.parametrize("demos", [2, 6])
def test_demonstrations_identify_each_setting_without_query_answers(family, seed, demos):
    for setting in family.settings_space():
        episode = family.generate_episode(seed, setting, demos=demos, queries=4)
        certificate = family.lesson_certificate(episode["train"], [pair["input"] for pair in episode["test"]])
        assert certificate["surviving_settings"] == [setting]
        assert certificate["surviving_shortcuts"] == []
        assert certificate["query_outputs_consulted"] is False
        assert certificate["scope"].startswith("finite")


@pytest.mark.parametrize("seed", [0, 17])
def test_every_demo_separates_all_four_declared_programs_and_shortcuts(family, seed):
    inputs = family.sample_inputs(seed, demos=6, queries=4)["train"]
    for grid in inputs:
        outputs = [family.transform(grid, setting) for setting in family.settings_space()]
        assert len({_signature(output) for output in outputs}) == 4
        for setting in family.settings_space():
            intended = family.transform(grid, setting)
            for name, rival in family.shortcut_outputs(grid, setting).items():
                assert rival != intended, (setting, name)


def test_four_queries_cover_anchor_transfer_boundary_and_maximum_stress(family):
    episode = family.generate_episode(23, family.DEFAULT_SETTINGS, demos=3, queries=4)
    queries = [pair["input"] for pair in episode["test"]]
    assert len(queries) == 4
    assert (len(queries[-1]), len(queries[-1][0])) == (30, 30)
    # Anchor query is ordinary maroon rectangles; later queries deliberately
    # add non-maroon, diagonal, irregular, singleton, boundary, and dense cases.
    assert {cell for row in queries[0] for cell in row} <= {0, 9}
    assert any(cell not in {0, 9} for grid in queries[1:] for row in grid for cell in row)
    assert any(queries[2][r][c] != 0 for r, c in [(0, 0), (0, len(queries[2][0]) - 1), (len(queries[2]) - 1, 0)])
    assert sum(cell != 0 for row in queries[-1] for cell in row) >= 40


def test_public_projection_and_id_ignore_private_rule_and_query_labels(family):
    episode = family.generate_episode(41, family.DEFAULT_SETTINGS, demos=3, queries=4)
    public = family.public_projection(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    identifier = family.episode_id(episode)

    changed = copy.deepcopy(episode)
    changed["settings"] = {"border_basis": "min_side", "connectivity": 4}
    changed["program_solution"] = "private replacement"
    changed["certificate"] = {"private": True}
    changed["test"][0]["output"][0][0] = (changed["test"][0]["output"][0][0] + 1) % 10
    assert family.public_projection(changed) == public
    assert family.episode_id(changed) == identifier


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "settings": {"border_basis": "max_side", "connectivity": 8}, "demos": 3, "queries": 4},
        {"seed": 0, "settings": {"border_basis": "max_side", "connectivity": 8}, "demos": 1, "queries": 4},
        {"seed": 0, "settings": {"border_basis": "max_side", "connectivity": 8}, "demos": 7, "queries": 4},
        {"seed": 0, "settings": {"border_basis": "max_side", "connectivity": 8}, "demos": 3, "queries": 3},
    ],
)
def test_generation_rejects_invalid_counts_and_types(family, kwargs):
    with pytest.raises(ValueError):
        family.generate_episode(**kwargs)


def test_native_adapter_delegates_exact_program_and_episode(family):
    adapter = _load_module("adapter.py", "parametric_adapter_067449d7a3b3_under_test")
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
        "parameters": {
            "border_basis": ["max_side", "min_side"],
            "connectivity": [4, 8],
        },
        "default": family.DEFAULT_SETTINGS,
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }


def test_replayable_audit_tool_summarizes_family_invariants(family, tmp_path):
    audit = _load_module("audit.py", "parametric_audit_067449d7a3b3_under_test")
    report = audit.build_report(seeds=[0], demo_counts=[2])
    assert report["schema"] == "arcpuzzles-parametric-prototype-audit-v1"
    assert report["task_id"] == TASK_ID
    assert report["summary"] == {
        "cases": 4,
        "programs": 4,
        "all_programs_distinct": True,
        "all_lessons_unique": True,
        "all_shortcuts_rejected": True,
        "all_inputs_setting_independent": True,
        "query_outputs_consulted": False,
    }
    assert all(case["query_shapes"][-1] == [30, 30] for case in report["cases"])
    target = tmp_path / "audit.json"
    audit.write_report(target, report)
    assert json.loads(target.read_text(encoding="utf-8")) == report


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
    changed["settings"] = {"border_basis": "min_side", "connectivity": 4}
    changed["program_solution"] = "private replacement"
    changed["test"][1]["input"][0][0] = 8
    changed["test"][3]["output"][0][0] = 7
    assert family.visible_turn_bytes(changed, 0) == expected_bytes
    assert family.visible_turn_id(changed, 0) == family.visible_turn_id(episode, 0)
