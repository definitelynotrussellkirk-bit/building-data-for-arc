from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path

import pytest

TASK = "fa2e57ec3fa2"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
GEN = importlib.import_module(f"puzzle_generators.per_puzzle.{TASK}.generator")


def load_family():
    path = PARAMETRIC / "prototype.py"
    spec = importlib.util.spec_from_file_location("_parametric_fa2e_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_base_generator_has_strict_consumed_controls_and_real_wall_regimes():
    assert GEN.RULE_HASH == "1eb5cb474942"
    for inert in ("wall_colors", "palette_size", "n_distinct_colors", "wall_density"):
        assert inert not in GEN.AXES
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, definitely_unknown_axis=1)
    with pytest.raises(TypeError):
        GEN.generate(True, 0)

    for difficulty in (None, "easy", "medium", "hard"):
        for h, w, count in ((5, 6, 1), (22, 26, 6)):
            grid = GEN.generate(
                13,
                7,
                difficulty=difficulty,
                grid_h=h,
                grid_w=w,
                emitter_count=count,
                palette_kind="many_walls",
            )
            assert (len(grid), len(grid[0])) == (h, w)
            assert GEN.self_check(grid) == []

    no_walls = GEN.generate(91, 4, difficulty="medium", palette_kind="no_walls")
    many_walls = GEN.generate(91, 4, difficulty="medium", palette_kind="many_walls")
    assert no_walls != many_walls
    assert {v for row in no_walls for v in row} <= {0, 2}
    assert any(v not in (0, 2) for row in many_walls for v in row)
    assert GEN.self_check(no_walls) == []
    assert GEN.self_check(many_walls) == []


def test_default_program_is_exact_catalog_program_and_contract_is_bounded():
    family = load_family()
    canonical = (PARAMETRIC / "canonical.rkt").read_text()
    assert family.program({"ray_mode": "stop"}) == canonical
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert promotion["default"] == {"ray_mode": "stop"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    with pytest.raises(ValueError):
        family.program({"ray_mode": "bogus"})
    with pytest.raises(ValueError):
        family.program({"ray_mode": "stop", "extra": 1})


def test_episode_is_prefix_stable_setting_independent_and_has_four_queries():
    family = load_family()
    settings = ({"ray_mode": "stop"}, {"ray_mode": "mirror_turn"})
    episodes = [family.generate(17, setting, 6, 4) for setting in settings]
    inputs = [[p["input"] for p in ep["train"] + ep["test"]] for ep in episodes]
    assert inputs[0] == inputs[1]
    for setting, episode in zip(settings, episodes):
        assert len(episode["train"]) == 6
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == family.program(setting)
        assert len({repr(p["input"]) for p in episode["train"] + episode["test"]}) == 10
        assert (len(episode["test"][-1]["input"]), len(episode["test"][-1]["input"][0])) == (30, 30)
        prefix = family.generate(17, setting, 2, 1)
        assert prefix["train"] == episode["train"][:2]
        assert prefix["test"] == episode["test"][:1]


def test_python_claims_match_semantics_and_two_demos_refute_other_setting():
    family = load_family()
    stop = {"ray_mode": "stop"}
    turn = {"ray_mode": "mirror_turn"}
    for setting in (stop, turn):
        episode = family.generate(0, setting, 2, 4)
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == family.solve(pair["input"], setting)
        other = turn if setting == stop else stop
        assert any(family.solve(pair["input"], other) != pair["output"] for pair in episode["train"])


def test_mirror_turn_consumes_first_hit_intermediate_and_skip_a_changes_output():
    family = load_family()
    episode = family.generate(0, {"ray_mode": "mirror_turn"}, 2, 4)
    pair = episode["train"][0]
    facts = family.analyze(pair["input"])
    turned = [ray for ray in facts["rays"] if ray["turn_direction"] is not None]
    assert {tuple(ray["turn_direction"]) for ray in turned} == {(-1, 0), (1, 0)}
    assert all(ray["first_hit"][2] in (6, 8) and ray["vertical_path"] for ray in turned)
    assert pair["output"] != family.solve(pair["input"], {"ray_mode": "stop"})


def test_30_by_30_query_has_substantive_content_and_long_composed_paths():
    family = load_family()
    pair = family.generate(5, {"ray_mode": "mirror_turn"}, 2, 4)["test"][-1]
    grid, output = pair["input"], pair["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(v != 0 for row in grid for v in row) >= 20
    assert sum(a != b for ra, rb in zip(grid, output) for a, b in zip(ra, rb)) >= 80
    facts = family.analyze(grid)
    assert len(facts["rays"]) == 8
    assert all(ray["first_hit"] is not None for ray in facts["rays"])


def test_task_local_preflight_compat_normalizes_legacy_single_test_pair():
    path = PARAMETRIC / "base_preflight_compat.py"
    spec = importlib.util.spec_from_file_location("_fa2e_preflight_compat_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    pair = {"input": [[0]], "output": [[0]]}
    record = {"train": [pair], "test": pair}
    assert module.normalized_split(record, "train") == [pair]
    assert module.normalized_split(record, "test") == [pair]
    assert record["test"] is pair
