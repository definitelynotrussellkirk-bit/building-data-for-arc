"""Independent counts and sequential-state contract for the native extension."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import random

import pytest

HOME = Path(__file__).resolve().parents[1] / "workspace/parametric"
spec = importlib.util.spec_from_file_location("native_cross_family_test", HOME / "family.py")
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


def test_canonical_default_exact_and_legacy_radius_reused():
    assert f.program({"diagonal_radius": 1, "propagation_passes": 1}).encode() == (HOME / "canonical.rkt").read_bytes()
    assert f.program({"diagonal_radius": 2, "propagation_passes": 1}) == f.legacy.rule_source(2)


@pytest.mark.parametrize("radius", [1, 2])
def test_updated_green_state_changes_next_seeds(radius):
    ep = f.generate(0, {"diagonal_radius": radius, "propagation_passes": 2}, demos=2)
    g = ep["train"][0]["input"]
    first = f.first_stage(g, radius)
    seed_grid = f.seed_grid(g, first)
    actual = {(r, c) for r, row in enumerate(seed_grid) for c, v in enumerate(row) if v == 1}
    nominal = {(r + dr, c + dc) for r, row in enumerate(g) for c, v in enumerate(row) if v == 1
               for dr, dc in ((-radius, -radius), (-radius, radius), (radius, -radius), (radius, radius))
               if 0 <= r + dr < len(g) and 0 <= c + dc < len(g[0])}
    assert actual < nominal
    assert actual
    naive = [[1 if (r, c) in nominal else f.background(g) for c in range(len(g[0]))] for r in range(len(g))]
    assert f.first_stage(seed_grid, radius) != f.first_stage(naive, radius)


@pytest.mark.parametrize("seed", [0, 17, 101, 2**63 - 1])
def test_prefixes_novel_queries_and_matched_inputs(seed):
    input_banks = []
    for radius in (1, 2):
        for passes in (1, 2):
            settings = {"diagonal_radius": radius, "propagation_passes": passes}
            ep = f.generate(seed, settings, demos=6, queries=4)
            short = f.generate(seed, settings, demos=2, queries=1)
            assert short["train"] == ep["train"][:2]
            assert short["test"] == ep["test"][:1]
            inputs = [p["input"] for p in ep["train"] + ep["test"]]
            assert len({repr(g) for g in inputs}) == 10
            assert all(not f.analyze(g)["errors"] for g in inputs)
            input_banks.append(inputs)
    assert all(bank == input_banks[0] for bank in input_banks)


def test_genuine_thirty_by_thirty_stress():
    ep = f.generate(17, {"diagonal_radius": 2, "propagation_passes": 2})
    pair = next(p for p in ep["test"] if len(p["input"]) == len(p["input"][0]) == 30)
    g = pair["input"]
    assert sum(v == 1 for row in g for v in row) == 12
    assert all(any(v == 1 for v in edge) for edge in (g[0], g[-1], [row[0] for row in g], [row[-1] for row in g]))
    assert sum(v != f.background(g) for row in pair["output"] for v in row) >= 400


def test_original_marker_snapshot_and_order_are_preserved():
    g = [[0] * 7 for _ in range(7)]
    for r, c in [(0, 0), (0, 4), (2, 4)]:
        g[r][c] = 1
    first = f.first_stage(g, 1)
    assert first[0][0] == 1  # Later marker on same row erased the first red center.
    assert first[0][4] == 1  # Later marker on same column erased this red center.
    assert first[2][4] == 2


def test_first_two_teach_processing_markers_overwritten_by_green():
    ep = f.generate(0, {"diagonal_radius": 1, "propagation_passes": 1}, demos=2)
    for radius in (1, 2):
        assert any(any(abs(r - rr) == abs(c - cc) == radius
                       for r, c in f.analyze(p["input"])["markers"]
                       for rr, cc in f.analyze(p["input"])["markers"])
                   for p in ep["train"])


def test_determinism_freshness_and_global_rng_purity():
    random.seed(418)
    state = random.getstate()
    args = (7, {"diagonal_radius": 2, "propagation_passes": 2})
    ep = f.generate(*args)
    frozen = deepcopy(ep)
    assert random.getstate() == state
    f.mirror(ep["train"][0]["input"], args[1])
    assert ep == frozen
    ep["test"][0]["input"][0][0] = 9
    assert f.generate(*args) == frozen


@pytest.mark.parametrize("settings", [{}, None, {"diagonal_radius": True, "propagation_passes": 1},
    {"diagonal_radius": 1, "propagation_passes": 3}, {"diagonal_radius": 0, "propagation_passes": 1},
    {"diagonal_radius": 1, "propagation_passes": 1, "extra": 0}])
def test_invalid_settings(settings):
    with pytest.raises(ValueError):
        f.program(settings)


@pytest.mark.parametrize("override", [{"seed": True}, {"seed": -1}, {"seed": 2**63},
    {"demos": 1}, {"demos": 7}, {"demos": 2.0}, {"queries": 0}, {"queries": 5}, {"queries": True}])
def test_invalid_counts(override):
    args = dict(seed=0, settings={"diagonal_radius": 1, "propagation_passes": 1}, demos=3, queries=4)
    args.update(override)
    with pytest.raises(ValueError):
        f.generate(**args)
