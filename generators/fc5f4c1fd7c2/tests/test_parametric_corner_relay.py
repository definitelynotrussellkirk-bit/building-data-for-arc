from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"
CANONICAL = "(rule! (let ((dummy 0)) (for/fold ((out g)) ((obj (in-list (filter (lambda (obj) (= (obj-color obj) 4)) (objects g 0))))) (let ((bb (obj-bbox obj))) (paint-cells out (list (list (first bb) (second bb)) (list (first bb) (fourth bb)) (list (third bb) (second bb)) (list (third bb) (fourth bb))) 1)))))"


def load_module():
    path = PARAM / "prototype.py"
    spec = importlib.util.spec_from_file_location("fc5_parametric_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture_grid():
    grid = [[0] * 9 for _ in range(7)]
    grid[1][0] = 2
    for r, c in [(1, 5), (2, 5), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7), (4, 5), (5, 5)]:
        grid[r][c] = 4
    return grid


def test_program_preserves_exact_canonical_default_and_changes_alternate():
    module = load_module()
    assert module.program({"finish_mode": "mark_only"}) == CANONICAL
    alternate = module.program({"finish_mode": "selector_frame"})
    assert alternate != CANONICAL
    assert alternate.lstrip().startswith("(rule!")


def test_small_fixture_marks_corners_then_frames_selected_box():
    module = load_module()
    grid = fixture_grid()
    canonical = module.transform(grid, {"finish_mode": "mark_only"})
    relay = module.transform(grid, {"finish_mode": "selector_frame"})
    for cell in [(1, 3), (1, 7), (5, 3), (5, 7)]:
        assert canonical[cell[0]][cell[1]] == 1
        assert relay[cell[0]][cell[1]] == 1
    assert relay[1][4] == 3
    assert relay[2][3] == 3
    assert relay[2][4] == 0
    assert canonical[1][4] == 0
    assert relay[1][0] == 2


@pytest.mark.parametrize("seed", [0, 1, 17, 99991])
def test_inputs_are_setting_independent_distinct_and_prefix_stable(seed):
    module = load_module()
    full_default = module.generate(seed, {"finish_mode": "mark_only"}, 6, 4)
    full_relay = module.generate(seed, {"finish_mode": "selector_frame"}, 6, 4)
    short = module.generate(seed, {"finish_mode": "selector_frame"}, 2, 1)
    assert [p["input"] for p in full_default["train"]] == [p["input"] for p in full_relay["train"]]
    assert [p["input"] for p in full_default["test"]] == [p["input"] for p in full_relay["test"]]
    assert short["train"] == full_relay["train"][:2]
    assert short["test"] == full_relay["test"][:1]
    visible = [json.dumps(p["input"], separators=(",", ":")) for p in full_relay["train"] + full_relay["test"]]
    assert len(visible) == len(set(visible))
    assert module.fit_settings(full_relay["train"][:2]) == [{"finish_mode": "selector_frame"}]
    assert module.fit_settings(full_default["train"][:2]) == [{"finish_mode": "mark_only"}]


def test_fourth_query_is_substantive_30_by_30_and_selector_varies():
    module = load_module()
    episodes = [module.generate(seed, {"finish_mode": "selector_frame"}, 2, 4) for seed in (0, 17, 91)]
    selected = []
    for episode in episodes:
        grid = episode["test"][3]["input"]
        assert (len(grid), len(grid[0])) == (30, 30)
        assert sum(cell != 0 for row in grid for cell in row) >= 80
        analysis = module.analyze(grid)
        assert analysis["selected_bbox"] is not None
        assert len(analysis["frame_cells"]) >= 12
        selected.append(tuple(analysis["selected_bbox"]))
    assert len(set(selected)) >= 2


def test_generated_lessons_refute_simple_object_selection_shortcuts():
    module = load_module()
    for seed in (0, 7, 17, 101):
        episode = module.generate(seed, {"finish_mode": "selector_frame"}, 2, 4)
        rivals = module.simple_rival_outputs(episode["train"])
        gold = [pair["output"] for pair in episode["train"]]
        assert rivals
        assert all(outputs != gold for outputs in rivals.values())


@pytest.mark.parametrize(
    "args",
    [
        (True, {"finish_mode": "mark_only"}, 2, 1),
        (0, {"finish_mode": "unknown"}, 2, 1),
        (0, {"finish_mode": "mark_only", "extra": 1}, 2, 1),
        (0, {"finish_mode": "mark_only"}, 1, 1),
        (0, {"finish_mode": "mark_only"}, 2, 5),
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
    spec = importlib.util.spec_from_file_location("fc5_base_generator_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_base_generator_default_and_varied_textures_are_behaviorally_distinct():
    base = load_base_generator()
    common = dict(
        difficulty="easy",
        grid_h=18,
        grid_w=20,
        n=4,
        n_distractor=3,
    )
    default = base.generate(7, 0, texture="default", **common)
    varied = base.generate(7, 0, texture="varied", **common)
    assert default != varied


def test_base_generator_honors_exact_global_overrides_and_palette_texture():
    base = load_base_generator()
    grid = base.generate(
        7,
        0,
        difficulty="easy",
        grid_h=18,
        grid_w=20,
        n=4,
        n_distractor=3,
        texture="warm",
    )
    assert (len(grid), len(grid[0])) == (18, 20)
    assert len(base._components_by_color(grid, 4)) == 4
    nonzero_colors = {cell for row in grid for cell in row if cell not in (0, 4)}
    assert nonzero_colors <= {2, 3, 5, 9}
    assert len(nonzero_colors) >= 1
    assert base.self_check(grid) == []


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


def test_base_self_check_rejects_unlabelled_solid_target_impostors():
    base = load_base_generator()
    assert any("solid rectangle" in error for error in base.self_check([[4, 4], [4, 4]]))
    assert any("solid rectangle" in error for error in base.self_check([[4] * 5 for _ in range(4)]))


def test_base_self_check_allows_explicit_solid_rectangle_fixture_only_with_metadata():
    base = load_base_generator()
    grid = base.generate(7, 0, difficulty="easy", grid_h=7, grid_w=9, texture="solid_rects")
    assert base.self_check(grid, meta={"texture": "solid_rects"}) == []
    assert any("solid rectangle" in error for error in base.self_check(grid))
