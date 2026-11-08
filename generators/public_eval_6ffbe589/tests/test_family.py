from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def a():
    return load(HOME / "workspace/parametric/adapter.py", "adapter_6ffbe589")


def test_official_labels(a):
    challenges = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())["6ffbe589"]
    solutions = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_solutions.json").read_text())["6ffbe589"]
    for split in ("train", "test"):
        for i, pair in enumerate(challenges[split]):
            expected = pair["output"] if split == "train" else solutions[i]
            assert a.solve(pair["input"], "clockwise") == expected


def test_default_program_and_canonical_are_exact(a):
    assert a.program({"turn_direction": "clockwise"}) == (HOME / "reference.rkt").read_text()
    assert (HOME / "reference.rkt").read_bytes() == (HOME / "workspace/parametric/canonical.rkt").read_bytes()


@pytest.mark.parametrize("settings", [None, {}, {"turn_direction": "bad"}, {"turn_direction": True}, {"turn_direction": "clockwise", "x": 1}])
def test_rejects_bad_settings(a, settings):
    with pytest.raises(ValueError):
        a.program(settings)


@pytest.mark.parametrize("field,value", [("seed", True), ("seed", -1), ("demos", 1), ("demos", 7), ("queries", 0), ("queries", 5), ("queries", 1.0)])
def test_rejects_bad_requests(a, field, value):
    kw = dict(seed=3, settings={"turn_direction": "clockwise"}, demos=2, queries=4)
    kw[field] = value
    with pytest.raises(ValueError):
        a.generate(**kw)


def test_matched_streams_prefixes_distinct_and_stress(a):
    for seed in (0, 17, 43):
        base = a.generate(seed, {"turn_direction": "clockwise"}, 2, 4)
        assert base == a.generate(seed, {"turn_direction": "clockwise"}, 2, 4)
        long = a.generate(seed, {"turn_direction": "clockwise"}, 6, 4)
        assert base["train"] == long["train"][:2]
        assert base["test"] == long["test"]
        alt = a.generate(seed, {"turn_direction": "counterclockwise"}, 2, 4)
        for split in ("train", "test"):
            assert [p["input"] for p in base[split]] == [p["input"] for p in alt[split]]
        assert any(x["output"] != y["output"] for x, y in zip(base["train"], alt["train"]))
        all_inputs = [p["input"] for split in ("train", "test") for p in base[split]]
        assert len({json.dumps(g) for g in all_inputs}) == 6
        assert len(base["test"][-1]["input"]) == 30
        assert len(base["test"][-1]["input"][0]) == 30


def test_cue_count_drives_independent_layer_turns(a):
    g = [[0] * 13 for _ in range(13)]
    # 7x7 main square at (1,1), radius-two connected and with two disjoint annuli.
    for c in range(1, 8):
        g[1][c] = 3
        g[7][c] = 3
    for r in range(2, 7):
        g[r][1] = 3
        g[r][7] = 3
    g[1][2] = 0  # asymmetric outer notch
    for p in ((3, 3), (3, 4), (4, 3), (5, 3)):
        g[p[0]][p[1]] = 8
    g[10][1] = 3          # one clockwise turn for color 3
    g[10][5] = g[10][6] = g[10][7] = 8  # three turns for color 8
    out = a.solve(g, "clockwise")
    assert out != a.solve(g, "counterclockwise")
    assert a.intermediate(g)["turns"] == {"3": 1, "8": 3}


def test_public_turn_hides_private_fields_and_future_queries(a):
    episode = a.generate(17, {"turn_direction": "clockwise"}, 2, 4)
    visible = a.public_turn(episode, 0, presentation_seed=9)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"secret": 1}
    changed["program_solution"] = "secret"
    for i, pair in enumerate(changed["test"]):
        pair["output"] = [[9]]
        if i != a.query_order(9)[0]:
            pair["input"] = [[8]]
    assert a.public_turn(changed, 0, presentation_seed=9) == visible
    assert set(visible) == {"train", "test"}
    assert len(visible["test"]) == 1 and set(visible["test"][0]) == {"input"}


def test_base_generator_contract():
    g = load(HOME / "generator.py", "generator_6ffbe589")
    assert g.RULE_TASK_ID == "ee_6ffbe589"
    assert g.GENERATOR_ID == "public_eval_6ffbe589"
    for i in range(12):
        grid = g.generate(17, i, difficulty="medium")
        assert g.self_check(grid) == []
    with pytest.raises(ValueError):
        g.generate(0, 0, made_up=1)
