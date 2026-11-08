"""Behavioral contract for the separate match/contrast frame-crop family."""
from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes


HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def module():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.is_file(), "The native parametric adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("test_frame_crop_adapter", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def test_native_default_is_exact_canonical_authority():
    adapter = module()
    canonical = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(ROOT).read_text().splitlines())
        if row["task_id"] == "4512012999bb"
    }
    assert canonical == {adapter.program({"alignment": "match"})}
    assert adapter.program({"alignment": "contrast"}) not in canonical


@pytest.mark.parametrize("demos,queries", [(3, 1), (3, 4), (6, 1), (6, 4)])
def test_independent_counts_unique_inputs_and_matched_setting_grammar(demos, queries):
    adapter = module()
    match = adapter.generate(17, {"alignment": "match"}, demos, queries)
    contrast = adapter.generate(17, {"alignment": "contrast"}, demos, queries)
    assert len(match["train"]) == demos and len(match["test"]) == queries
    assert [p["input"] for p in match["train"] + match["test"]] == [
        p["input"] for p in contrast["train"] + contrast["test"]
    ]
    inputs = [json.dumps(p["input"]) for p in match["train"] + match["test"]]
    assert len(set(inputs)) == demos + queries
    assert any(a["output"] != b["output"] for a, b in zip(match["train"], contrast["train"]))


def test_first_query_prefix_is_independent_of_future_queries():
    adapter = module()
    one = adapter.generate(5, {"alignment": "match"}, 3, 1)
    four = adapter.generate(5, {"alignment": "match"}, 3, 4)
    assert public_challenge_bytes(one) == public_challenge_bytes({
        "train": four["train"], "test": [four["test"][0]]
    })


def test_large_query_has_real_content_and_boundary_contacts():
    episode = module().generate(0, {"alignment": "match"}, 3, 4)
    grid = episode["test"][3]["input"]
    output = episode["test"][3]["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert (len(output), len(output[0])) == (30, 16)
    assert any(grid[0]) and any(grid[-1])
    assert any(row[0] for row in grid) and any(row[-1] for row in grid)
    assert sum(cell != 0 for row in grid for cell in row) > 200


def test_teaching_demonstrations_reject_all_declared_shortcuts():
    adapter = module()
    for alignment in ("match", "contrast"):
        episode = adapter.generate(0, {"alignment": alignment}, 3, 4)
        certificate = episode["teaching"]
        assert certificate["used_query_answers"] is False
        assert certificate["surviving_shortcuts"] == []
        assert len(certificate["rejected_shortcuts"]) >= 8
        assert set(certificate["score_relations"]) == {"direct", "mirror", "tie"}


def test_sampler_is_deterministic_fresh_and_does_not_touch_global_rng():
    adapter = module()
    random.seed(5678)
    before = random.getstate()
    first = adapter.generate(42, {"alignment": "contrast"}, 3, 4)
    assert random.getstate() == before
    second = adapter.generate(42, {"alignment": "contrast"}, 3, 4)
    assert first == second
    first["train"][0]["input"][0][0] = 99
    assert adapter.generate(42, {"alignment": "contrast"}, 3, 4) == second


@pytest.mark.parametrize("settings", [{}, {"alignment": "unknown"}, {"alignment": True},
                                      {"alignment": "match", "extra": 1}])
def test_undeclared_settings_fail_before_sampling(settings):
    with pytest.raises(ValueError):
        module().generate(0, settings, 3, 4)


@pytest.mark.parametrize("seed,demos,queries", [(-1, 3, 4), (True, 3, 4), (2**63, 3, 4),
                                               (0, 2, 4), (0, 7, 4), (0, 3, 0),
                                               (0, 3, 5), (0, 3, True), (0, 3.0, 4)])
def test_invalid_requests_fail_without_silent_count_coercion(seed, demos, queries):
    with pytest.raises(ValueError):
        module().generate(seed, {"alignment": "match"}, demos, queries)
