from __future__ import annotations

import importlib.util
import random
from pathlib import Path

import pytest

from reviewer_support import find_root


ROOT = find_root(__file__)
PARAM_DIR = ROOT / "generators" / "6ecd8be24495" / "workspace" / "parametric"


def _load_family():
    path = PARAM_DIR / "family.py"
    spec = importlib.util.spec_from_file_location("_parametric_6ecd8be24495", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_program_contract_and_strict_settings():
    family = _load_family()
    canonical = (PARAM_DIR / "canonical.rkt").read_text()
    assert family.program({"selection_metric": "total_seeds"}) == canonical
    alternate = family.program({"selection_metric": "distinct_colors"})
    assert alternate != canonical
    assert alternate.startswith("(rule!")
    for bad in (
        None,
        {},
        {"selection_metric": "largest_area"},
        {"selection_metric": "total_seeds", "extra": 1},
    ):
        with pytest.raises(ValueError):
            family.program(bad)


def test_matched_inputs_labels_teaching_and_count_boundaries():
    family = _load_family()
    for seed in (0, 17):
        total = family.generate(seed, {"selection_metric": "total_seeds"}, 2, 4)
        distinct = family.generate(seed, {"selection_metric": "distinct_colors"}, 2, 4)
        assert [p["input"] for p in total["train"]] == [p["input"] for p in distinct["train"]]
        assert [p["input"] for p in total["test"]] == [p["input"] for p in distinct["test"]]
        for settings, episode in (
            ({"selection_metric": "total_seeds"}, total),
            ({"selection_metric": "distinct_colors"}, distinct),
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
        for total_pair, distinct_pair in zip(total["train"], distinct["train"]):
            assert total_pair["output"] != distinct_pair["output"]
            analysis = family.analyze(total_pair["input"])
            assert analysis["total_winner"] != analysis["distinct_winner"]
        large = next(pair for pair in distinct["test"] if len(pair["input"]) == len(pair["input"][0]) == 30)
        changed = sum(a != b for ra, rb in zip(large["input"], large["output"]) for a, b in zip(ra, rb))
        assert changed >= 100

    assert len(family.generate(4, {"selection_metric": "total_seeds"}, 6, 1)["train"]) == 6
    with pytest.raises(ValueError):
        family.generate(4, {"selection_metric": "total_seeds"}, 1, 4)
    with pytest.raises(ValueError):
        family.generate(4, {"selection_metric": "total_seeds"}, 2, 5)


def test_selected_chamber_intermediate_controls_local_majority_fill():
    family = _load_family()
    for settings in (
        {"selection_metric": "total_seeds"},
        {"selection_metric": "distinct_colors"},
    ):
        episode = family.generate(31, settings, 4, 4)
        selected_ranks = set()
        for pair in episode["train"] + episode["test"]:
            analysis = family.analyze(pair["input"])
            rank = analysis["total_winner"] if settings["selection_metric"] == "total_seeds" else analysis["distinct_winner"]
            selected_ranks.add(rank)
            selected = analysis["chambers"][rank]
            changed = {
                (r, c)
                for r in range(len(pair["input"]))
                for c in range(len(pair["input"][0]))
                if pair["input"][r][c] != pair["output"][r][c]
            }
            assert changed
            assert changed <= set(selected["cells"])
            assert {pair["output"][r][c] for r, c in changed} == {selected["majority_color"]}
        assert len(selected_ranks) >= 2


def test_determinism_and_global_rng_purity():
    family = _load_family()
    random.seed(224)
    state = random.getstate()
    first = family.generate(81, {"selection_metric": "distinct_colors"}, 3, 4)
    assert random.getstate() == state
    second = family.generate(81, {"selection_metric": "distinct_colors"}, 3, 4)
    assert first == second
    first["train"][0]["input"][0][0] = 0
    assert first != second


def test_bounded_audit_tool_reports_no_findings():
    path = PARAM_DIR / "audit.py"
    spec = importlib.util.spec_from_file_location("_audit_6ecd8be24495", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run_audit(range(3))
    assert report["task_id"] == "6ecd8be24495"
    assert report["seed_count"] == 3
    assert report["setting_episodes"] == 6
    assert report["failure_count"] == 0
    assert report["failures"] == []
