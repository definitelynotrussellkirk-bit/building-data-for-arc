from __future__ import annotations

import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import find_root


ROOT = find_root(__file__)
PARAM_DIR = ROOT / "generators" / "64bd7bc767bb" / "workspace" / "parametric"


def _load_family():
    path = PARAM_DIR / "family.py"
    spec = importlib.util.spec_from_file_location("_parametric_64bd7bc767bb", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_program_contract_and_strict_settings():
    family = _load_family()
    canonical = (PARAM_DIR / "canonical.rkt").read_text()
    assert family.program({"alignment_rule": "bottom"}) == canonical
    alternate = family.program({"alignment_rule": "winner_bbox"})
    assert alternate != canonical
    assert alternate.startswith("(rule!")
    for bad in (
        None,
        {},
        {"alignment_rule": "top"},
        {"alignment_rule": "bottom", "extra": 1},
    ):
        with pytest.raises(ValueError):
            family.program(bad)


def test_matched_inputs_labels_teaching_and_count_boundaries():
    family = _load_family()
    for seed in (0, 17):
        canonical = family.generate(seed, {"alignment_rule": "bottom"}, 2, 4)
        alternate = family.generate(seed, {"alignment_rule": "winner_bbox"}, 2, 4)
        assert [p["input"] for p in canonical["train"]] == [p["input"] for p in alternate["train"]]
        assert [p["input"] for p in canonical["test"]] == [p["input"] for p in alternate["test"]]
        for settings, episode in (
            ({"alignment_rule": "bottom"}, canonical),
            ({"alignment_rule": "winner_bbox"}, alternate),
        ):
            assert len(episode["train"]) == 2
            assert len(episode["test"]) == 4
            assert episode["program_solution"] == family.program(settings)
            all_inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
            assert len({tuple(map(tuple, grid)) for grid in all_inputs}) == len(all_inputs)
            for pair in episode["train"] + episode["test"]:
                assert pair["output"] == family.transform(pair["input"], settings)
            check = family.teaching_check(episode, settings)
            assert check["survivors"] == [settings]
            assert check["surviving_rivals"] == []
        assert any(a["output"] != b["output"] for a, b in zip(canonical["train"], alternate["train"]))
        assert {family.analyze(pair["input"])["winner_orientation"] for pair in alternate["train"]} == {"horizontal", "vertical"}
        large = next(pair for pair in alternate["test"] if len(pair["input"]) == len(pair["input"][0]) == 30)
        assert sum(cell != 0 for row in large["input"] for cell in row) >= 80

    assert len(family.generate(4, {"alignment_rule": "bottom"}, 6, 1)["train"]) == 6
    with pytest.raises(ValueError):
        family.generate(4, {"alignment_rule": "bottom"}, 1, 4)
    with pytest.raises(ValueError):
        family.generate(4, {"alignment_rule": "bottom"}, 2, 5)


def test_winner_bbox_intermediate_controls_final_bar_alignment():
    family = _load_family()
    settings = {"alignment_rule": "winner_bbox"}
    episode = family.generate(23, settings, 4, 4)
    seen = set()
    for pair in episode["train"] + episode["test"]:
        analysis = family.analyze(pair["input"])
        seen.add(analysis["winner_orientation"])
        output = pair["output"]
        counts = analysis["counts"]
        if analysis["winner_orientation"] == "horizontal":
            assert all(output[0][c] == c + 1 for c, count in enumerate(counts) if count)
        else:
            assert all(output[-1][c] == c + 1 for c, count in enumerate(counts) if count)
    assert seen == {"horizontal", "vertical"}


def test_determinism_and_global_rng_purity():
    family = _load_family()
    random.seed(991)
    state = random.getstate()
    first = family.generate(91, {"alignment_rule": "winner_bbox"}, 3, 4)
    assert random.getstate() == state
    second = family.generate(91, {"alignment_rule": "winner_bbox"}, 3, 4)
    assert first == second
    first["train"][0]["input"][0][0] = 9
    assert first != second


def test_bounded_audit_tool_reports_no_findings():
    path = PARAM_DIR / "audit.py"
    spec = importlib.util.spec_from_file_location("_audit_64bd7bc767bb", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run_audit(range(3))
    assert report["task_id"] == "64bd7bc767bb"
    assert report["seed_count"] == 3
    assert report["setting_episodes"] == 6
    assert report["failure_count"] == 0
    assert report["failures"] == []
