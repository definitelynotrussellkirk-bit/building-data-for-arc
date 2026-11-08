"""Native prototype scope: merge first, then select per-color components."""
import copy
import importlib.util
import random
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
spec = importlib.util.spec_from_file_location("bridge_prototype_tests", HOME / "prototype.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


def test_exact_canonical_default():
    assert p.program({"bridge_mode": "ignore"}).encode() == (HOME / "canonical.rkt").read_bytes()


def test_bridge_changes_winner_only_after_recomputing_components():
    grid = [[2, 2, 8, 2, 2, 0, 0], [0, 0, 0, 0, 0, 3, 3],
            [2, 2, 2, 0, 0, 0, 0]]
    before = p.mirror(grid, {"bridge_mode": "ignore"})
    after = p.mirror(grid, {"bridge_mode": "merge"})
    assert before[2][:3] == [4, 4, 4]
    assert before[0][:5] == [0, 0, 0, 0, 0]
    assert after[0][:5] == [4, 4, 4, 4, 4]
    assert after[2][:3] == [0, 0, 0]
    assert before[1][5:] == after[1][5:] == [1, 1]


@pytest.mark.parametrize("seed", [0, 17, 123, 2**63 - 1])
def test_counts_prefixes_distinct_inputs_and_fixed_settings(seed):
    small = p.generate(seed, {"bridge_mode": "ignore"}, demos=2, queries=1)
    full = p.generate(seed, {"bridge_mode": "ignore"}, demos=6, queries=4)
    other = p.generate(seed, {"bridge_mode": "merge"}, demos=6, queries=4)
    assert small["train"] == full["train"][:2]
    assert small["test"] == full["test"][:1]
    inputs = [x["input"] for x in full["train"] + full["test"]]
    assert inputs == [x["input"] for x in other["train"] + other["test"]]
    assert len({repr(g) for g in inputs}) == 10
    assert all(a["output"] != b["output"] for a, b in zip(full["train"][:2], other["train"][:2]))
    for g in inputs:
        assert not p.analyze(g)["errors"]


def test_large_stress_has_substantive_content_and_border_contacts():
    ep = p.generate(0, {"bridge_mode": "merge"})
    g = next(x["input"] for x in ep["test"] if len(x["input"]) == len(x["input"][0]) == 30)
    assert sum(v != 0 for row in g for v in row) >= 150
    assert all(any(v != 0 for v in edge) for edge in (g[0], g[-1], [r[0] for r in g], [r[-1] for r in g]))
    assert len(p.components(g)) >= 8


def test_global_rng_fresh_returns_and_input_purity():
    random.seed(8917)
    state = random.getstate()
    a = p.generate(7, {"bridge_mode": "merge"})
    b = copy.deepcopy(a)
    assert random.getstate() == state
    g = a["train"][0]["input"]
    saved = copy.deepcopy(g)
    p.mirror(g, {"bridge_mode": "merge"})
    assert g == saved
    a["train"][0]["input"][0][0] = 9
    assert p.generate(7, {"bridge_mode": "merge"}) == b


def test_first_two_teach_against_location_regression():
    for mode in ("ignore", "merge"):
        lesson = p.generate(31337, {"bridge_mode": mode}, demos=2)
        for selector in (lambda o: min(o["cells"]), lambda o: min(r for r, c in o["cells"])):
            predictions = []
            for pair in lesson["train"]:
                g = pair["input"]
                parts = p.components(p.preprocess(g, {"bridge_mode": mode}))
                out = [[0] * len(g[0]) for _ in g]
                for color, target in ((2, 4), (3, 1)):
                    obj = min((o for o in parts if o["color"] == color), key=selector)
                    for r, c in obj["cells"]:
                        out[r][c] = target
                predictions.append(out)
            assert any(a != b["output"] for a, b in zip(predictions, lesson["train"]))


def test_first_demo_defeats_geometric_size_surrogates():
    g = p.generate(101, {"bridge_mode": "ignore"}, demos=2)["train"][0]["input"]
    green = sorted((o for o in p.components(g) if o["color"] == 3), key=lambda o: -o["size"])
    a, b = green[:2]
    assert a["size"] > b["size"]
    def scores(o):
        cells = set(o["cells"])
        h = max(r for r, c in cells) - min(r for r, c in cells) + 1
        w = max(c for r, c in cells) - min(c for r, c in cells) + 1
        perimeter = sum((r + dr, c + dc) not in cells for r, c in cells for dr, dc in p.NEIGHBORS)
        return (h * w, min(h, w), max(h, w), h + w, perimeter)
    assert all(x < y for x, y in zip(scores(a), scores(b)))


def test_standalone_8_control_remains_independent_of_original_red():
    for seed in (7, 17, 101):
        g = p.generate(seed, {"bridge_mode": "merge"}, demos=2)["train"][1]["input"]
        winner = max((o for o in p.components(p.preprocess(g, {"bridge_mode": "merge"})) if o["color"] == 2), key=lambda o: o["size"])
        assert all(g[r][c] == 8 for r, c in winner["cells"])


def test_first_two_teach_four_connectivity_even_after_merge():
    for seed in (1, 101):
        ep = p.generate(seed, {"bridge_mode": "merge"}, demos=2)
        wrong = []
        for pair in ep["train"]:
            g = pair["input"]
            parts = p.components(p.preprocess(g, {"bridge_mode": "merge"}), connectivity=8)
            out = [[0] * len(g[0]) for _ in g]
            for color, target in ((2, 4), (3, 1)):
                winner = max((o for o in parts if o["color"] == color), key=lambda o: o["size"])
                for r, c in winner["cells"]:
                    out[r][c] = target
            wrong.append(out)
        assert any(a != pair["output"] for a, pair in zip(wrong, ep["train"]))


@pytest.mark.parametrize("settings", [{}, {"bridge_mode": 0}, {"bridge_mode": "unknown"},
                                     {"bridge_mode": "ignore", "extra": 1}, None])
def test_bad_settings_rejected(settings):
    with pytest.raises(ValueError):
        p.program(settings)


@pytest.mark.parametrize("kwargs", [{"seed": True}, {"seed": -1}, {"seed": 2**63},
                                    {"demos": 1}, {"demos": 7}, {"demos": True},
                                    {"queries": 0}, {"queries": 5}, {"queries": 2.0}])
def test_request_boundaries(kwargs):
    args = dict(seed=0, settings={"bridge_mode": "ignore"}, demos=3, queries=4)
    args.update(kwargs)
    with pytest.raises(ValueError):
        p.generate(**args)


@pytest.mark.parametrize("bad", [[], [[0], [0, 1]], [[True]], [[1.0]], [[10]]])
def test_strict_grid_rejection(bad):
    with pytest.raises(ValueError):
        p.mirror(bad, {"bridge_mode": "ignore"})


@pytest.mark.parametrize("symmetry", range(8))
def test_all_advertised_dihedral_symmetries(symmetry):
    g = p.generate(17, {"bridge_mode": "merge"})["test"][0]["input"]
    for mode in ("ignore", "merge"):
        assert p.mirror(p.transform(g, symmetry), {"bridge_mode": mode}) == p.transform(p.mirror(g, {"bridge_mode": mode}), symmetry)
