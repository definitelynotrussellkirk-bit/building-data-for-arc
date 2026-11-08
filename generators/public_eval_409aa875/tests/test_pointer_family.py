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
    return load(HOME / "workspace/parametric/adapter.py", "adapter_409aa875")


def test_official_labels(a):
    challenges = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_challenges.json").read_text())["409aa875"]
    solutions = json.loads((ROOT / "shared/data/raw/arc-agi_evaluation_solutions.json").read_text())["409aa875"]
    for split in ("train", "test"):
        for i, pair in enumerate(challenges[split]):
            expected = pair["output"] if split == "train" else solutions[i]
            assert a.solve(pair["input"], "forward") == expected


def test_default_program_and_canonical_are_exact(a):
    assert a.program({"travel": "forward"}) == (HOME / "reference.rkt").read_text()
    assert (HOME / "reference.rkt").read_bytes() == (HOME / "workspace/parametric/canonical.rkt").read_bytes()


@pytest.mark.parametrize("settings", [None, {}, {"travel": "bad"}, {"travel": True}, {"travel": "forward", "x": 1}])
def test_rejects_bad_settings(a, settings):
    with pytest.raises(ValueError):
        a.program(settings)


@pytest.mark.parametrize("field,value", [("seed", True), ("seed", -1), ("demos", 1), ("demos", 7), ("queries", 0), ("queries", 5), ("queries", 1.0)])
def test_rejects_bad_requests(a, field, value):
    kw = dict(seed=3, settings={"travel": "forward"}, demos=2, queries=4)
    kw[field] = value
    with pytest.raises(ValueError):
        a.generate(**kw)


def test_pointer_shapes_cover_cardinal_and_diagonal_directions(a):
    cases = {
        (-1, 0): {(5, 5), (6, 4), (6, 6)},
        (1, 0): {(5, 5), (4, 4), (4, 6)},
        (0, -1): {(5, 5), (4, 6), (6, 6)},
        (0, 1): {(5, 5), (4, 4), (6, 4)},
        (-1, -1): {(5, 5), (6, 5), (5, 6)},
        (-1, 1): {(5, 5), (6, 5), (5, 4)},
        (1, -1): {(5, 5), (4, 5), (5, 6)},
        (1, 1): {(5, 5), (4, 5), (5, 4)},
    }
    for direction, cells in cases.items():
        assert a.pointer(cells) == ((5, 5), direction)


def test_collision_and_hit_are_sequential(a):
    g = [[7] * 20 for _ in range(20)]
    cells = []
    for origin, direction in [((10, 5), (0, 1)), ((5, 10), (1, 0)), ((9, 9), (1, 1)), ((14, 14), (-1, 0))]:
        cells.append(a.pointer_cells(origin, direction))
    for obj in cells:
        for r, c in obj:
            g[r][c] = 6
    out = a.solve(g, "forward")
    assert out[10][10] == 1  # two pointers collide on empty background
    assert all(out[r][c] == 9 for r, c in cells[3])  # the diagonal pointer hits this object
    info = a.intermediate(g, "forward")
    assert info["endpoint_counts"]["10,10"] == 2
    assert [14, 14] in info["endpoints"]


def test_matched_streams_prefixes_distinct_and_stress(a):
    for seed in (0, 17, 43):
        base = a.generate(seed, {"travel": "forward"}, 2, 4)
        assert base == a.generate(seed, {"travel": "forward"}, 2, 4)
        long = a.generate(seed, {"travel": "forward"}, 6, 4)
        assert base["train"] == long["train"][:2]
        assert base["test"] == long["test"]
        alt = a.generate(seed, {"travel": "backward"}, 2, 4)
        for split in ("train", "test"):
            assert [p["input"] for p in base[split]] == [p["input"] for p in alt[split]]
        assert any(x["output"] != y["output"] for x, y in zip(base["train"], alt["train"]))
        all_inputs = [p["input"] for split in ("train", "test") for p in base[split]]
        assert len({json.dumps(g) for g in all_inputs}) == 6
        assert len(base["test"][-1]["input"]) == 30
        assert len(base["test"][-1]["input"][0]) == 30


def test_public_turn_hides_private_fields_and_future_queries(a):
    episode = a.generate(17, {"travel": "forward"}, 2, 4)
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
    g = load(HOME / "generator.py", "generator_409aa875")
    assert g.RULE_TASK_ID == "ee_409aa875"
    assert g.GENERATOR_ID == "public_eval_409aa875"
    for i in range(12):
        grid = g.generate(17, i, difficulty="medium")
        assert g.self_check(grid) == []
    with pytest.raises(ValueError):
        g.generate(0, 0, made_up=1)
