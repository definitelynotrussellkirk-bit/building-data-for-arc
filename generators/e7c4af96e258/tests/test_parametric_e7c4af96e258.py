from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

TASK_HOME = Path(__file__).resolve().parents[1]
REPO = TASK_HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
PARAMETRIC = TASK_HOME / "workspace" / "parametric"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def load_adapter():
    path = PARAMETRIC / "adapter.py"
    spec = importlib.util.spec_from_file_location("parametric_e7c4af96e258", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_source() -> str:
    record = REPO / "shared" / "data" / "base" / "solutions" / "training" / "ac0c5833__e7c4af96e258.json"
    return json.loads(record.read_text(encoding="utf-8"))["racket_target"]["target_code"]


def test_contract_and_default_program_are_source_exact():
    adapter = load_adapter()
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["parameters"] == {"target_policy": ["all_matches", "farthest_match"]}
    assert promotion["default"] == {"target_policy": "all_matches"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert adapter.program({"target_policy": "all_matches"}) == canonical_source()
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == canonical_source()
    assert adapter.program({"target_policy": "farthest_match"}) == (PARAMETRIC / "farthest.rkt").read_text(encoding="utf-8")


@pytest.mark.parametrize("seed", [0, 17])
def test_generation_is_matched_identifying_distinct_and_count_independent(seed: int):
    adapter = load_adapter()
    all_episode = adapter.generate(seed, {"target_policy": "all_matches"}, 2, 4)
    far_episode = adapter.generate(seed, {"target_policy": "farthest_match"}, 2, 4)

    assert [pair["input"] for pair in all_episode["train"] + all_episode["test"]] == [
        pair["input"] for pair in far_episode["train"] + far_episode["test"]
    ]
    assert all(a["output"] != b["output"] for a, b in zip(all_episode["train"], far_episode["train"]))

    one_query = adapter.generate(seed, {"target_policy": "all_matches"}, 2, 1)
    assert one_query["train"] == all_episode["train"]
    assert one_query["test"][0] == all_episode["test"][0]

    encoded = [json.dumps(pair["input"], separators=(",", ":")) for pair in all_episode["train"] + all_episode["test"]]
    assert len(encoded) == len(set(encoded)) == 6


@pytest.mark.parametrize("setting", ["all_matches", "farthest_match"])
def test_four_query_lesson_contains_substantive_30_by_30_stress(setting: str):
    adapter = load_adapter()
    episode = adapter.generate(31, {"target_policy": setting}, 2, 4)
    stress = episode["test"][3]
    assert (len(stress["input"]), len(stress["input"][0])) == (30, 30)
    assert (len(stress["output"]), len(stress["output"][0])) == (30, 30)
    assert sum(cell == 4 for row in stress["input"] for cell in row) >= 12
    assert sum(cell == 2 for row in stress["output"] for cell in row) >= 2


def test_farthest_stage_depends_on_candidate_enumeration_and_rejects_nearest_counterfactual():
    adapter = load_adapter()
    prototype = adapter._impl
    episode = adapter.generate(43, {"target_policy": "farthest_match"}, 2, 4)
    grid = episode["train"][0]["input"]
    candidates = prototype.candidate_footprints(grid)
    assert len(candidates) >= 3
    farthest = prototype.transform(grid, {"target_policy": "farthest_match"})
    nearest = prototype.transform_with_selector(grid, "nearest_non_source")
    assert farthest == episode["train"][0]["output"]
    assert farthest != nearest
    assert prototype.counterfactual_program("nearest_non_source") == (PARAMETRIC / "nearest.rkt").read_text(encoding="utf-8")


def test_adapter_rejects_malformed_requests():
    adapter = load_adapter()
    with pytest.raises(ValueError, match="settings"):
        adapter.program({})
    with pytest.raises(ValueError, match="target_policy"):
        adapter.program({"target_policy": "nearest"})
    with pytest.raises(ValueError, match="demos"):
        adapter.generate(0, {"target_policy": "all_matches"}, 1, 4)
    with pytest.raises(ValueError, match="queries"):
        adapter.generate(0, {"target_policy": "all_matches"}, 2, 5)


@pytest.mark.parametrize("seed", [0, 1, 3, 17, 43, 75])
@pytest.mark.parametrize("policy", ["all_matches", "farthest_match"])
def test_minimum_demos_identify_policy_against_declared_shortcuts(seed: int, policy: str):
    adapter = load_adapter()
    episode = adapter.generate(seed, {"target_policy": policy}, 2, 4)
    certificate = adapter._impl.teaching_certificate(
        episode["train"], {"target_policy": policy}
    )

    assert certificate["survivors"] == [policy]
    assert episode["certificate"] == certificate


def test_bounded_probe_reports_finite_teaching_certificate():
    path = PARAMETRIC / "probe.py"
    spec = importlib.util.spec_from_file_location("_marker_probe_test", path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run()

    assert report["checks"]["finite_declared_shortcut_certificate"] is True
    assert report["teaching_certificates"]
    assert all(
        row["survivors"] == [row["selected"]]
        for row in report["teaching_certificates"]
    )


def test_candidate_cache_is_bounded_for_multi_seed_audits():
    adapter = load_adapter()
    info = adapter._impl._candidate_footprints_payload.cache_info()

    assert info.maxsize is not None
    assert info.maxsize <= 256
