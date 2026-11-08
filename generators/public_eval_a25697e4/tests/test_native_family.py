"""General socket fitting, chirality-dependent colors and native contracts."""
import importlib.util
import json
from pathlib import Path
import pytest

HOME = Path(__file__).parents[1]
SOURCE = HOME / "workspace/parametric/native_family.py"


def test_implementation_exists():
    assert SOURCE.is_file()
    assert (HOME / "reference.rkt").is_file()


@pytest.fixture(scope="module")
def native():
    spec = importlib.util.spec_from_file_location("socket_native_under_test", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def originals():
    root = HOME.parents[1]
    parent = json.loads((root / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())["a25697e4"]
    gold = json.loads((root / "shared/data/raw/arc-agi_evaluation_solutions.json").read_text())["a25697e4"]
    return parent["train"] + [{"input": p["input"], "output": answer} for p, answer in zip(parent["test"], gold)]


@pytest.mark.parametrize("index", range(5))
def test_all_original_train_and_test_gold(native, index):
    pair = originals()[index]
    before = [row[:] for row in pair["input"]]
    assert native.solve(pair["input"]) == pair["output"]
    assert pair["input"] == before


def test_reflection_parity_is_input_derived(native):
    first, second, third, *_ = originals()
    assert native.plan(first["input"])[0]["reflected"] is True
    assert native.plan(second["input"])[0]["reflected"] is False
    assert native.plan(third["input"])[0]["reflected"] is False
    assert native.solve(first["input"], "preserve") != first["output"]
    assert native.solve(second["input"], "preserve") == second["output"]


def test_same_color_sockets_and_shared_piece_color(native):
    for index in (3, 4):
        grid = originals()[index]["input"]
        extracted = native.extract(grid)
        assert len(extracted["sockets"]) == len(extracted["pieces"]) == 2
        assert len({p["socket_index"] for p in native.plan(grid)}) == 2
    sockets = native.extract(originals()[3]["input"])["sockets"]
    assert sockets[0]["color"] == sockets[1]["color"]


def test_whole_piece_collision_resolves_symmetric_plug(native):
    grid = originals()[2]["input"]
    parts = native.extract(grid)
    valid = native.candidates(parts, 0)
    loose = native.candidates(parts, 0, check_collision=False)
    assert len(valid) == 1 and len(loose) > len(valid)
    assert any(set((r, c) for r, c, _ in p["cells"]) & parts["anchor_cells"] for p in loose)


@pytest.mark.parametrize("grid", [[], [[]], [[True]], [[0.0]], [[10]], [[-1]], [[0, 1], [0]], [[0] * 31], [[0]] * 31, ((0,),), [[0]], [[0, 1]]])
def test_invalid_grammar_rejected(native, grid):
    with pytest.raises(ValueError):
        native.solve(grid)


@pytest.mark.parametrize("settings", [None, {}, {"reflection_colors": "bad"}, {"reflection_colors": True},
    {"reflection_colors": 1}, {"reflection_colors": "swap", "extra": 0}])
def test_strict_settings(native, settings):
    with pytest.raises(ValueError):
        native.program(settings)


def test_exact_default_and_distinct_parameter(native):
    assert native.program({"reflection_colors": "swap"}) == (HOME / "reference.rkt").read_text()
    assert native.program({"reflection_colors": "preserve"}) != native.program({"reflection_colors": "swap"})


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"seed": 2**63}, {"seed": 0.5},
    {"demos": 1}, {"demos": 7}, {"demos": True}, {"queries": 0}, {"queries": 5}, {"queries": 1.0}])
def test_strict_episode_controls(native, kwargs):
    arguments = {"seed": 0, "settings": {"reflection_colors": "swap"}, "demos": 3, "queries": 4}
    arguments.update(kwargs)
    with pytest.raises(ValueError):
        native.generate(**arguments)


@pytest.mark.parametrize("seed", [0, 17, 43, 2**63 - 1])
def test_full_bank_is_matched_novel_and_prefix_stable(native, seed):
    one = native.generate(seed, {"reflection_colors": "swap"}, 6, 4)
    two = native.generate(seed, {"reflection_colors": "preserve"}, 6, 4)
    grids = [p["input"] for p in one["train"] + one["test"]]
    assert grids == [p["input"] for p in two["train"] + two["test"]]
    assert len({tuple(map(tuple, grid)) for grid in grids}) == 10
    assert len(native.generate(seed, {"reflection_colors": "swap"})["train"]) == 3
    for demos, queries in ((2, 1), (3, 4), (6, 2)):
        short = native.generate(seed, {"reflection_colors": "swap"}, demos, queries)
        assert short["train"] == one["train"][:demos] and short["test"] == one["test"][:queries]
    for a, b in zip(one["train"][:2], two["train"][:2]):
        assert a["output"] != b["output"]
        assert {p["reflected"] for p in native.plan(a["input"])} == {False, True}
    before = native.generate(seed, {"reflection_colors": "swap"}, 2, 1)
    one["train"][0]["input"][0][0] = (one["train"][0]["input"][0][0] + 1) % 10
    assert native.generate(seed, {"reflection_colors": "swap"}, 2, 1) == before


@pytest.mark.parametrize("seed", [0, 17, 43])
def test_large_scenes_have_substantive_structure(native, seed):
    train, test = native.input_bank(seed)
    large = [g for g in train + test if len(g) == len(g[0]) == 30]
    assert len(large) == 2 and large[0] != large[1]
    for grid in large:
        parts = native.extract(grid)
        assert len(parts["pieces"]) == 2
        assert len(parts["source_cells"]) >= 45
        assert len(parts["anchor_cells"]) + len(parts["source_cells"]) >= 150
        assert len(native.plan(grid)) == 2


def test_query_order_changes_with_seed(native):
    orders = {tuple(tuple(sorted((len(g), len(g[0])))) for g in native.input_bank(seed)[1]) for seed in range(5)}
    assert len(orders) > 1


def test_second_core_teaches_both_numeric_color_orders(native):
    grid = native.input_bank(17)[0][1]
    placements = native.plan(grid)
    assert {p["head_color"] == min(p["colors"]) for p in placements} == {False, True}


def test_selected_generator_contract():
    source = HOME / "generator.py"
    assert source.is_file()
    spec = importlib.util.spec_from_file_location("socket_selected_generator", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    grid = module.generate(seed=17, sample_index=0, difficulty="hard")
    assert module.self_check(grid) == []
    assert module.generate(seed=17, sample_index=0, difficulty="hard") == grid
    assert module.generate(seed=17, sample_index=1) != grid
    with pytest.raises(ValueError):
        module.generate(seed=17, unsupported=1)
    with pytest.raises(ValueError):
        module.generate(seed=17, sample_index=True)
