"""Focused behavior tests for the proposed episode-level output-scale extension."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_id,
)


ROOT = find_root(__file__)
TASK_ID = "8e6c44aee812"
TASK_DIR = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_DIR / "workspace" / "parametric" / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.exists(), f"missing parametric prototype: {PROTOTYPE_PATH}"
    spec = importlib.util.spec_from_file_location(
        "staircase_output_scale_parametric", PROTOTYPE_PATH
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_scale_reproduces_canonical_labels_and_custom_counts():
    proto = _load_prototype()
    assert proto.ALLOWED_OUTPUT_SCALES == (2, 3)
    assert proto.DEFAULT_OUTPUT_SCALE == 2

    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert proto.solve(pair["input"], output_scale=2) == pair["output"]

    episode = proto.generate_episode(
        0,
        output_scale=2,
        demo_count=5,
        query_count=4,
        difficulty="medium",
    )
    assert episode["parameters"] == {"output_scale": 2}
    assert len(episode["train"]) == 5
    assert len(episode["test"]) == 4
    assert episode["meta"]["selection_scope"] == "once_per_episode"

    for pair in [*episode["train"], *episode["test"]]:
        height = len(pair["input"])
        width = len(pair["input"][0])
        assert len(pair["output"]) == 2 * height
        assert all(len(row) == 2 * width for row in pair["output"])



def _grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


@pytest.mark.parametrize(("seed", "output_scale"), ((20, 2), (21, 3)))
def test_each_setting_masks_answers_and_is_identifiable_for_four_unique_queries(
    seed: int, output_scale: int
):
    proto = _load_prototype()
    episode = proto.generate_episode(
        seed,
        output_scale=output_scale,
        demo_count=5,
        query_count=4,
        difficulty="medium",
    )
    pairs = [*episode["train"], *episode["test"]]
    assert len({_grid_key(pair["input"]) for pair in pairs}) == 9
    assert all(max(len(pair["output"]), len(pair["output"][0])) <= 30 for pair in pairs)

    for query in episode["test"]:
        assert proto.lesson_identifiable(
            episode["train"], query, output_scale=output_scale
        ) == []

    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    visible_id = public_challenge_id(public)

    private_only_change = deepcopy(episode)
    private_only_change["parameters"]["output_scale"] = 99
    private_only_change["meta"]["seed"] = 999999
    private_only_change["program"] = "private replacement"
    private_only_change["test"][0]["output"] = [[9]]
    assert public_challenge_id(proto.public_challenge(private_only_change)) == visible_id

    visible_change = deepcopy(public)
    visible_change["test"][0]["input"][0][0] = (
        visible_change["test"][0]["input"][0][0] + 1
    ) % 10
    assert public_challenge_id(visible_change) != visible_id


def test_parameter_selection_and_public_controls_fail_closed():
    proto = _load_prototype()
    assert proto.select_setting(0) == 2
    assert proto.select_setting(1) == 3
    assert proto.select_setting(2) == 2

    for bad in (False, True, 1, 4, 2.0, "2", None):
        with pytest.raises(ValueError):
            proto.solve([[1, 1, 2, 3], [1, 1, 2, 3], [2, 2, 2, 3], [3, 3, 3, 3]], output_scale=bad)

    for kwargs in (
        {"seed": -1},
        {"seed": True},
        {"seed": 0, "demo_count": 0},
        {"seed": 0, "demo_count": True},
        {"seed": 0, "query_count": 0},
        {"seed": 0, "query_count": False},
        {"seed": 0, "difficulty": "extreme"},
    ):
        seed = kwargs.pop("seed")
        with pytest.raises(ValueError):
            proto.generate_episode(seed, **kwargs)



def test_query_equivalent_surviving_rival_is_not_reported_as_ambiguity():
    proto = _load_prototype()
    demos = []
    for index in range(5):
        grid = proto._GEN.generate(7, index, difficulty="medium", period=4)
        demos.append({"input": grid, "output": proto.solve(grid, output_scale=2)})
    query_grid = proto._GEN.generate(7, 5, difficulty="medium", period=4)

    reasons = proto.lesson_identifiable(
        demos, {"input": query_grid}, output_scale=2
    )

    assert "named rival 'fixed_period_four' survives every demonstration" not in reasons

def _load_verifier():
    verifier_path = TASK_DIR / "workspace" / "parametric" / "verify.py"
    assert verifier_path.exists(), f"missing parametric verifier: {verifier_path}"
    spec = importlib.util.spec_from_file_location(
        "staircase_output_scale_parametric_verify", verifier_path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_exact_racket_verifier_materializes_both_settings_with_visible_only_ids(tmp_path):
    verifier = _load_verifier()
    report = verifier.build_report(artifact_root=tmp_path)

    assert report["schema"] == "8e6c44aee812-parametric-output-scale-v1"
    assert report["canonical_scale_two_exact"] is True
    assert report["all_racket_exact"] is True
    assert report["all_python_exact"] is True
    assert report["all_lessons_identifiable"] is True
    assert report["all_public_challenges_masked"] is True
    assert report["all_public_ids_visible_only"] is True
    assert report["unique_input_count"] == 18
    assert {row["output_scale"] for row in report["settings"]} == {2, 3}
    distinction = report["parameter_distinction"]
    assert distinction["outputs_differ"] is True
    assert distinction["scale_2"]["racket_matches_python"] is True
    assert distinction["scale_3"]["racket_matches_python"] is True
    assert distinction["scale_2"]["shape"] == [10, 10]
    assert distinction["scale_3"]["shape"] == [15, 15]

    for row in report["settings"]:
        assert row["demo_count"] == 5
        assert row["query_count"] == 4
        assert len(row["public_id"]) == 64
        assert row["all_racket_exact"] is True
        assert row["all_python_exact"] is True
        assert row["lesson_identifiable_for_every_query"] is True
        assert row["public_answer_masked"] is True
        assert row["public_id_visible_only"] is True
        assert (tmp_path / row["program_path"]).is_file()
        assert (tmp_path / row["private_episode_path"]).is_file()
        public_path = tmp_path / row["public_challenge_path"]
        assert public_path.is_file()
        assert public_path.parent.parent.name == f"episode-{row['public_id']}"
