"""Native rotation/scale promotion contract for 5e8e4691afde."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root

TASK_ID = "5e8e4691afde"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"
SELF_AUDIT_PATH = PARAMETRIC / "self_audit.py"


def _load(name: str, path: Path):
    if not path.is_file():
        pytest.skip(f"source not implemented yet: {path.relative_to(ROOT)}")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load("test_5e8e_native_prototype", PROTOTYPE_PATH)


@pytest.fixture(scope="module")
def adapter():
    return _load("test_5e8e_native_adapter", ADAPTER_PATH)


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        programs = {
            row["program_solution"]
            for line in handle
            if (row := json.loads(line)).get("task_id") == TASK_ID
        }
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in [*episode["train"], *episode["test"]]]


def _serialized_inputs(episode: dict) -> list[str]:
    return [json.dumps(grid, separators=(",", ":")) for grid in _inputs(episode)]


def test_native_sources_exist():
    missing = [
        path.relative_to(ROOT).as_posix()
        for path in (PROTOTYPE_PATH, ADAPTER_PATH, PROMOTION_PATH, SELF_AUDIT_PATH)
        if not path.is_file()
    ]
    assert not missing, f"missing native parametric sources: {missing}"


def test_program_space_preserves_exact_default_and_has_eight_distinct_rules(prototype):
    canonical = _canonical_program()
    programs = {prototype.program_for(setting) for setting in prototype.SETTINGS}
    assert prototype.program_for(prototype.DEFAULT) == canonical
    assert len(prototype.SETTINGS) == 8
    assert len(programs) == 8


def test_native_episode_supports_two_through_six_demos_and_exactly_four_queries(prototype):
    setting = prototype.Setting(quarter_turns=3, distance_scale=2)
    for demos in range(2, 7):
        episode = prototype.generate_episode(41, setting, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == prototype.program_for(setting)
        assert len(set(_serialized_inputs(episode))) == demos + 4


def test_same_seed_has_matched_inputs_and_demo_labels_identify_every_setting(prototype):
    episodes = [prototype.generate_episode(1729, setting, 3, 4) for setting in prototype.SETTINGS]
    common_inputs = _inputs(episodes[0])
    assert all(_inputs(episode) == common_inputs for episode in episodes)

    first_demo = common_inputs[0]
    predictions = [prototype.mirror(first_demo, setting) for setting in prototype.SETTINGS]
    assert len({json.dumps(output, separators=(",", ":")) for output in predictions}) == 8
    for setting, episode in zip(prototype.SETTINGS, episodes):
        assert prototype.fit_candidates(episode["train"]) == (setting,)


def test_queries_include_substantive_30x30_and_boundary_path_surface(prototype):
    for seed in (0, 17):
        episode = prototype.generate_episode(seed, prototype.Setting(1, 2), 3, 4)
        stress = episode["test"][0]
        assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
        assert (len(stress["output"]), len(stress["output"][0])) == (30, 30)
        assert sum(cell != 0 for row in stress["input"] for cell in row) >= 13
        assert sum(cell != 0 for row in stress["output"] for cell in row) == 900

        infos = [prototype.scene_info(pair["input"]) for pair in episode["test"]]
        assert any(
            r in (0, info["height"] - 1) or c in (0, info["width"] - 1)
            for info in infos
            for r, c in (info["indicator"], info["endpoint"])
        )


def test_native_generation_is_deterministic_fresh_and_strictly_validated(prototype):
    setting = prototype.Setting(2, 1)
    first = prototype.generate_episode(99, setting, 6, 4)
    second = prototype.generate_episode(99, setting, 6, 4)
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    first["train"][0]["input"][0][0] = (first["train"][0]["input"][0][0] + 1) % 10
    assert first != second

    for bad_seed in (True, -1, 2**63, 1.0, "1", None):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(bad_seed, setting, 3, 4)
    for bad_setting in ({"quarter_turns": 0, "distance_scale": 1}, None, 1):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(1, bad_setting, 3, 4)
    for bad_demos in (True, 1, 7, 3.0, "3", None):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(1, setting, bad_demos, 4)
    for bad_queries in (True, 1, 3, 5, 4.0, "4", None):
        with pytest.raises((TypeError, ValueError)):
            prototype.generate_episode(1, setting, 3, bad_queries)


def test_adapter_and_contract_expose_only_declared_settings(adapter, prototype):
    contract = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {
            "quarter_turns": [0, 1, 2, 3],
            "distance_scale": [1, 2],
        },
        "default": {"quarter_turns": 0, "distance_scale": 1},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
    }
    settings = {"quarter_turns": 1, "distance_scale": 2}
    assert adapter.program(copy.deepcopy(settings)) == prototype.program_for(prototype.Setting(1, 2))
    episode = adapter.generate(13, copy.deepcopy(settings), 2, 4)
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    for invalid in (
        {},
        {"quarter_turns": 0},
        {"quarter_turns": 0, "distance_scale": 1, "extra": 1},
        {"quarter_turns": 4, "distance_scale": 1},
        {"quarter_turns": 0, "distance_scale": 3},
        {"quarter_turns": True, "distance_scale": 1},
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(invalid)


def test_bounded_self_audit_refutes_declared_shortcuts_from_demos_only():
    audit = _load("test_5e8e_native_self_audit", SELF_AUDIT_PATH)
    report = audit.audit_family(seeds=(0, 17), demo_counts=(2, 3, 6), queries=4)
    assert report["schema"] == "arcpuzzles-rotation-scale-self-audit-v1"
    assert report["status"] == "passed"
    assert report["limits"] == {
        "seeds": [0, 17],
        "demo_counts": [2, 3, 6],
        "queries": 4,
        "candidate_family": "declared transforms plus endpoint, center, copy, fill, frame, and diagonal shortcuts",
    }
    assert len(report["cases"]) == 48
    for case in report["cases"]:
        selected = f"setting:{case['settings']['quarter_turns']}:{case['settings']['distance_scale']}"
        assert case["demo_survivors"] == [selected]
        assert case["ambiguous_query_rivals"] == []
        assert case["rival_count"] >= 15
        assert set(case["refutations"]) == set(case["rivals"]) - {selected}
        for row in case["refutations"].values():
            assert 0 <= row["first_failing_demo"] < case["demos"]
            assert row["reason"] == "label mismatch"


def test_self_audit_is_deterministic_and_rejects_bad_limits():
    audit = _load("test_5e8e_native_self_audit_validation", SELF_AUDIT_PATH)
    first = audit.audit_family(seeds=(41,), demo_counts=(2,), queries=4)
    second = audit.audit_family(seeds=(41,), demo_counts=(2,), queries=4)
    assert first == second
    for seeds, demo_counts, queries in (
        ((), (2,), 4),
        ((0,), (), 4),
        ((0,), (1,), 4),
        ((0,), (2,), 3),
    ):
        with pytest.raises((TypeError, ValueError)):
            audit.audit_family(seeds=seeds, demo_counts=demo_counts, queries=queries)
