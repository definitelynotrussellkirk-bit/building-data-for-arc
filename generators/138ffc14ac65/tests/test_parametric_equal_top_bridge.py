from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"
CANONICAL = "(rule! (let ((dummy 0)) (for*/fold ((out (empty-grid (rows g) (cols g) 0))) ((r (in-range (rows g))) (c (in-range (cols g)))) (let ((v (at g r c))) (if (= v 0) out (for/fold ((acc out)) ((rr (in-range 0 (+ r 1)))) (set-cell acc rr c v)))))))"


def load_module():
    path = PARAM / "prototype.py"
    spec = importlib.util.spec_from_file_location("bridge_parametric_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_grid():
    grid = [[0] * 10 for _ in range(7)]
    grid[4][2] = 2
    grid[5][7] = 2
    grid[3][9] = 4
    return grid


def test_program_preserves_exact_canonical_default_and_changes_alternate():
    module = load_module()
    assert module.program({"finish_rule": "up_only"}) == CANONICAL
    alternate = module.program({"finish_rule": "equal_top_bridge"})
    assert alternate != CANONICAL
    assert alternate.lstrip().startswith("(rule!")


def test_small_fixture_projects_up_then_bridges_equal_top_endpoints():
    module = load_module()
    grid = fixture_grid()
    canonical = module.transform(grid, {"finish_rule": "up_only"})
    relay = module.transform(grid, {"finish_rule": "equal_top_bridge"})
    assert [canonical[0][c] for c in range(10)] == [0, 0, 2, 0, 0, 0, 0, 2, 0, 4]
    assert [relay[0][c] for c in range(10)] == [0, 0, 2, 2, 2, 2, 2, 2, 0, 4]
    assert relay[1:] == canonical[1:]


@pytest.mark.parametrize("seed", [0, 1, 17, 99991])
def test_inputs_are_setting_independent_distinct_and_prefix_stable(seed):
    module = load_module()
    full_default = module.generate(seed, {"finish_rule": "up_only"}, 6, 4)
    full_relay = module.generate(seed, {"finish_rule": "equal_top_bridge"}, 6, 4)
    short = module.generate(seed, {"finish_rule": "equal_top_bridge"}, 2, 1)
    assert [p["input"] for p in full_default["train"]] == [p["input"] for p in full_relay["train"]]
    assert [p["input"] for p in full_default["test"]] == [p["input"] for p in full_relay["test"]]
    assert short["train"] == full_relay["train"][:2]
    assert short["test"] == full_relay["test"][:1]
    visible = [json.dumps(p["input"], separators=(",", ":")) for p in full_relay["train"] + full_relay["test"]]
    assert len(visible) == len(set(visible))
    assert module.fit_settings(full_relay["train"][:2]) == [{"finish_rule": "equal_top_bridge"}]
    assert module.fit_settings(full_default["train"][:2]) == [{"finish_rule": "up_only"}]


def test_fourth_query_is_substantive_30_by_30_with_multiple_relays():
    module = load_module()
    pair_counts = []
    for seed in (0, 17, 91):
        episode = module.generate(seed, {"finish_rule": "equal_top_bridge"}, 2, 4)
        grid = episode["test"][3]["input"]
        assert (len(grid), len(grid[0])) == (30, 30)
        assert sum(cell != 0 for row in grid for cell in row) >= 9
        analysis = module.analyze(grid)
        assert len(analysis["pair_intervals"]) >= 4
        assert len(analysis["bridge_cells"]) >= 12
        pair_counts.append(len(analysis["pair_intervals"]))
    assert min(pair_counts) >= 4


def test_generated_lessons_refute_simple_bridge_shortcuts():
    module = load_module()
    for seed in (0, 7, 17, 101):
        episode = module.generate(seed, {"finish_rule": "equal_top_bridge"}, 2, 4)
        rivals = module.simple_rival_outputs(episode["train"])
        gold = [pair["output"] for pair in episode["train"]]
        assert rivals
        assert all(outputs != gold for outputs in rivals.values())


@pytest.mark.parametrize(
    "args",
    [
        (True, {"finish_rule": "up_only"}, 2, 1),
        (0, {"finish_rule": "unknown"}, 2, 1),
        (0, {"finish_rule": "up_only", "extra": 1}, 2, 1),
        (0, {"finish_rule": "up_only"}, 1, 1),
        (0, {"finish_rule": "up_only"}, 2, 5),
    ],
)
def test_invalid_contract_values_fail_closed(args):
    module = load_module()
    with pytest.raises(ValueError):
        module.generate(*args)


def load_base_generator():
    runtime = HOME.parents[1] / "shared" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    path = HOME / "generator.py"
    spec = importlib.util.spec_from_file_location("bridge_base_generator_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_base_generator_honors_global_overrides_in_easy_mode_and_textures_are_real():
    base = load_base_generator()
    warm = base.generate(7, 0, difficulty="easy", grid_h=14, grid_w=14, seed_count=8, texture="warm")
    cool = base.generate(7, 0, difficulty="easy", grid_h=14, grid_w=14, seed_count=8, texture="cool")
    assert (len(warm), len(warm[0])) == (14, 14)
    assert sum(cell != 0 for row in warm for cell in row) == 8
    assert len({c for row in warm for c in row if c}) == 8
    assert warm != cool
    assert base.observe_overrides(warm) == {"grid_h": 14, "grid_w": 14, "seed_count": 8}
    assert base.self_check(warm) == []


@pytest.mark.parametrize(
    "seed,sample_index",
    [
        (True, 0),
        (1.0, 0),
        ("1", 0),
        (0, True),
        (0, 1.0),
        (0, "1"),
        (0, -1),
    ],
)
def test_base_generator_rejects_invalid_scalar_call_arguments(seed, sample_index):
    base = load_base_generator()
    with pytest.raises((TypeError, ValueError)):
        base.generate(seed, sample_index, difficulty="easy")


def test_base_generator_rejects_singleton_seed_override_outside_ordinary_grammar():
    base = load_base_generator()
    with pytest.raises(ValueError):
        base.generate(7, 0, difficulty="easy", grid_h=8, grid_w=8, seed_count=1)


def test_base_self_check_rejects_unlabelled_singleton_impostor():
    base = load_base_generator()
    grid = [[0] * 8 for _ in range(8)]
    grid[4][3] = 2
    assert any("2..8" in error for error in base.self_check(grid))
