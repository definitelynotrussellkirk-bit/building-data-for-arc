"""Contract tests for the 6b5d8752c5c4 divider-source family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest
from reviewer_support import canonical_path, find_root


TASK_ID = "6b5d8752c5c4"
REPO_ROOT = find_root(__file__)
GENERATOR_HOME = REPO_ROOT / "generators" / TASK_ID
PARAMETRIC = GENERATOR_HOME / "workspace" / "parametric"
PROTOTYPE_PATH = PARAMETRIC / "prototype.py"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"


def _load(path: Path, name: str):
    if not path.is_file():
        pytest.fail(f"missing implementation file: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load(PROTOTYPE_PATH, "_test_6b5d8752c5c4_parametric_prototype")


@pytest.fixture(scope="module")
def adapter():
    return _load(ADAPTER_PATH, "_test_6b5d8752c5c4_parametric_adapter")


def _canonical_program() -> str:
    with canonical_path(REPO_ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise KeyError(TASK_ID)


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _episode_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_contract_declares_exact_canonical_default_and_one_distinct_neighbor(adapter):
    promotion = json.loads(PROMOTION_PATH.read_text(encoding="utf-8"))
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {
            "divider_source": ["bbox_midpoint", "lane_marker"],
        },
        "default": {"divider_source": "bbox_midpoint"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
        ],
    }
    canonical = adapter.program({"divider_source": "bbox_midpoint"})
    marker = adapter.program({"divider_source": "lane_marker"})
    assert canonical == _canonical_program()
    assert marker != canonical
    assert marker.strip().startswith("(rule!")


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_generation_counts_determinism_freshness_and_setting_neutral_inputs(
    prototype, adapter, demos
):
    midpoint = adapter.generate(
        17, {"divider_source": "bbox_midpoint"}, demos, 4
    )
    marker = adapter.generate(
        17, {"divider_source": "lane_marker"}, demos, 4
    )
    assert len(midpoint["train"]) == demos
    assert len(midpoint["test"]) == 4
    assert len(marker["train"]) == demos
    assert len(marker["test"]) == 4
    midpoint_inputs = _episode_inputs(midpoint)
    marker_inputs = _episode_inputs(marker)
    assert midpoint_inputs == marker_inputs
    assert len({_frozen(grid) for grid in midpoint_inputs}) == demos + 4
    assert midpoint["program_solution"] == prototype.program(
        {"divider_source": "bbox_midpoint"}
    )
    assert marker["program_solution"] == prototype.program(
        {"divider_source": "lane_marker"}
    )

    again = adapter.generate(
        17, {"divider_source": "bbox_midpoint"}, demos, 4
    )
    assert again == midpoint
    assert again is not midpoint
    assert again["train"][0]["input"] is not midpoint["train"][0]["input"]
    changed = copy.deepcopy(midpoint)
    changed["train"][0]["input"][0][0] = 7
    assert adapter.generate(
        17, {"divider_source": "bbox_midpoint"}, demos, 4
    ) == midpoint


@pytest.mark.parametrize("source", ["bbox_midpoint", "lane_marker"])
def test_two_demos_identify_only_the_chosen_setting_and_reject_named_shortcuts(
    prototype, adapter, source
):
    episode = adapter.generate(0, {"divider_source": source}, 2, 4)
    assessment = prototype.assess_demos(episode["train"], source)
    assert assessment["declared_survivors"] == [source]
    assert assessment["all_named_shortcuts_rejected"] is True
    assert set(assessment["shortcuts"]) == {
        "global_first_marker",
        "wrong_axis",
        "toward_marker",
        "canvas_midpoint",
    }
    assert all(not row["fits_all_demos"] for row in assessment["shortcuts"].values())


@pytest.mark.parametrize("seed", [0, 17, 271828])
def test_input_grammar_covers_minimum_and_stress_surfaces(prototype, seed):
    inputs = prototype.episode_inputs(seed, demos=6, queries=4)
    analyses = [prototype.analyze_input(grid) for grid in inputs]
    assert [row["canvas"] for row in analyses[:6]] == [8, 12, 16, 20, 24, 28]
    assert [row["canvas"] for row in analyses[6:]] == [30, 22, 18, 26]
    assert all(row["off_center_marker_count"] > 0 for row in analyses)
    stress = analyses[6]
    assert stress["canvas"] == 30
    assert stress["object_count"] >= 6
    assert stress["orientations"] == ["tall", "wide"]
    assert stress["edge_contact_count"] >= 2
    assert stress["colors"] == [0, 9, stress["marker_color"]]


@pytest.mark.parametrize("source", ["bbox_midpoint", "lane_marker"])
def test_python_labels_are_exact_arc_grids_and_preserve_inputs(prototype, source):
    episode = prototype.generate(31, {"divider_source": source}, 6, 4)
    for pair in episode["train"] + episode["test"]:
        before = copy.deepcopy(pair["input"])
        expected = prototype.apply_setting(pair["input"], source)
        assert pair["output"] == expected
        assert pair["input"] == before
        assert 1 <= len(expected) <= 30
        assert 1 <= len(expected[0]) <= 30
        assert all(
            type(value) is int and 0 <= value <= 9
            for row in expected
            for value in row
        )


def test_global_rng_isolation(prototype):
    random.seed(271828)
    state = random.getstate()
    first = prototype.generate(77, {"divider_source": "lane_marker"}, 6, 4)
    assert random.getstate() == state
    second = prototype.generate(77, {"divider_source": "lane_marker"}, 6, 4)
    assert first == second
    assert random.getstate() == state


@pytest.mark.parametrize(
    "bad_settings",
    [
        None,
        {},
        {"divider_source": "unknown"},
        {"divider_source": True},
        {"divider_source": "bbox_midpoint", "extra": 1},
    ],
)
def test_invalid_settings_reject(adapter, bad_settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(bad_settings)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, bad_settings, 3, 4)


@pytest.mark.parametrize(
    "args",
    [
        (True, {"divider_source": "bbox_midpoint"}, 3, 4),
        (-1, {"divider_source": "bbox_midpoint"}, 3, 4),
        (0, {"divider_source": "bbox_midpoint"}, 1, 4),
        (0, {"divider_source": "bbox_midpoint"}, 7, 4),
        (0, {"divider_source": "bbox_midpoint"}, 3, 3),
        (0, {"divider_source": "bbox_midpoint"}, 3, 5),
    ],
)
def test_invalid_scalar_requests_reject(adapter, args):
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(*args)


def test_bounded_self_audit_covers_all_counts_settings_and_public_projection():
    audit = _load(
        PARAMETRIC / "audit.py",
        "_test_6b5d8752c5c4_parametric_audit",
    )
    report = audit.build_report(seed_start=0, seed_count=8)
    assert report["schema"] == "6b5d8752c5c4-parametric-self-audit-v1"
    assert report["status"] == "passed"
    assert report["episodes_checked"] == 8 * 5 * 2
    assert report["failures"] == []
    assert report["all_inputs_setting_neutral"] is True
    assert report["all_declared_settings_identified"] is True
    assert report["all_named_shortcuts_rejected"] is True
    assert report["all_public_projections_private_invariant"] is True
    assert report["all_first_turn_views_exact"] is True
    assert report["surface_counts"]["30x30"] == 8 * 5 * 2
    assert report["retained_case"]["settings"] == {
        "divider_source": "bbox_midpoint"
    }
    assert report["retained_case"]["changes_final_output"] is True
