from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path

import pytest

TASK = "9adaf46a8128"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def load_family():
    path = PARAMETRIC / "prototype.py"
    spec = importlib.util.spec_from_file_location("_parametric_9ada_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_base_generator_has_honest_strict_controls_and_role_schedule():
    assert GEN.RULE_HASH == "97f1e4b799fa"
    assert "palette_size" not in GEN.AXES
    assert "n_distinct_colors" not in GEN.AXES
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, definitely_unknown_axis=1)
    for difficulty in (None, "easy", "medium", "hard"):
        for h, w in ((8, 10), (14, 16)):
            grid = GEN.generate(3, 5, difficulty=difficulty, grid_h=h, grid_w=w, n_markers=4)
            assert (len(grid), len(grid[0])) == (h, w)
            assert GEN.self_check(grid) == []
    for start in range(12):
        roles = set()
        for index in range(start, start + 3):
            grid = GEN.generate(19, index, difficulty="easy")
            sep = next(r for r, row in enumerate(grid) if set(row) == {5})
            roles.update(v for row in grid[sep + 1 :] for v in row if v in (1, 2, 3, 4))
        assert roles == {1, 2, 3, 4}


def test_default_program_is_exact_catalog_program_and_contract_is_bounded():
    family = load_family()
    canonical = (PARAMETRIC / "canonical.rkt").read_text()
    assert family.program({"transform_mode": "per_marker"}) == canonical
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert promotion["default"] == {"transform_mode": "per_marker"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    with pytest.raises(ValueError):
        family.program({"transform_mode": "bogus"})
    with pytest.raises(ValueError):
        family.program({"transform_mode": "per_marker", "extra": 1})


def test_episode_is_prefix_stable_setting_independent_and_has_four_queries():
    family = load_family()
    settings = (
        {"transform_mode": "per_marker"},
        {"transform_mode": "leader_composed"},
    )
    episodes = [family.generate(17, setting, 6, 4) for setting in settings]
    assert [[p["input"] for p in ep["train"] + ep["test"]] for ep in episodes][0] == [
        [p["input"] for p in ep["train"] + ep["test"]] for ep in episodes
    ][1]
    for setting, episode in zip(settings, episodes):
        assert len(episode["train"]) == 6
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == family.program(setting)
        assert len({repr(p["input"]) for p in episode["train"] + episode["test"]}) == 10
        assert any(len(p["input"]) == 30 and len(p["input"][0]) == 30 for p in episode["test"])
        prefix = family.generate(17, setting, 2, 1)
        assert prefix["train"] == episode["train"][:2]
        assert prefix["test"] == episode["test"][:1]


def test_python_claims_match_rule_semantics_and_two_demos_refute_other_setting():
    family = load_family()
    direct = {"transform_mode": "per_marker"}
    composed = {"transform_mode": "leader_composed"}
    for setting in (direct, composed):
        episode = family.generate(0, setting, 2, 4)
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == family.solve(pair["input"], setting)
        other = composed if setting == direct else direct
        assert any(family.solve(pair["input"], other) != pair["output"] for pair in episode["train"])


def test_leader_composed_has_real_intermediate_and_skip_a_changes_output():
    family = load_family()
    setting = {"transform_mode": "leader_composed"}
    episode = family.generate(0, setting, 2, 4)
    pair = episode["train"][0]
    analysis = family.analyze(pair["input"])
    assert analysis["leader_marker"] in (2, 3, 4)
    assert analysis["intermediate_template"] != analysis["template"]
    assert family.solve(pair["input"], setting) != family.solve(
        pair["input"], {"transform_mode": "per_marker"}
    )
