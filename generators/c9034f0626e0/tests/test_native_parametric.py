"""Native-adapter behavior, with executed labels tested by qualification."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace/parametric"


def load_adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "MAIN needs a native parametric adapter"
    spec = importlib.util.spec_from_file_location("_c9034_native_tests", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_native_default_is_exact_selected_canonical_and_other_rules_differ():
    from arcpuzzles import Catalog
    a = load_adapter()
    catalog = Catalog()
    source = {v["program_solution"] for v in catalog._variants()["c9034f0626e0"]}
    assert {a.program({"lattice_rule": "period2"})} == source
    assert len({a.program({"lattice_rule": mode}) for mode in a.MODES}) == 4


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("mode", ["period2", "period3", "ray_size"])
def test_counts_distinct_queries_matched_inputs_and_constructive_teaching(demos, mode):
    # Retain the original curriculum-specific profile/selector guarantees.
    a = load_adapter().PARITY
    e = a.generate(17, {"lattice_rule": mode}, demos, 4)
    assert len(e["train"]) == demos and len(e["test"]) == 4
    inputs = [p["input"] for p in e["train"] + e["test"]]
    assert len({json.dumps(g) for g in inputs}) == demos + 4
    assert {a.core.effective_period(p["input"], "ray_size") for p in e["train"][:2]} == {2, 3}
    assert {(len(g), len(g[0])) for g in inputs} >= {(9, 9), (30, 30)}
    for candidate in a.MODES:
        fits = all(a.core.mirror(p["input"], candidate) == p["output"] for p in e["train"])
        assert fits == (candidate == mode)
    reference = a.generate(17, {"lattice_rule": "period2"}, demos, 4)
    assert [p["input"] for p in e["test"]] == [p["input"] for p in reference["test"]]
    if demos >= 3:
        assert inputs == [p["input"] for p in reference["train"] + reference["test"]]
    single = a.generate(17, {"lattice_rule": mode}, demos, 1)
    assert single["train"] == e["train"] and single["test"] == e["test"][:1]


def test_ray_counts_whole_first_component_and_preserves_blockers():
    a = load_adapter()
    g = [[0] * 11 for _ in range(9)]
    g[3][1] = 8
    for r, c in [(3, 5), (3, 6), (4, 5), (4, 6), (5, 5), (5, 6), (5, 7)]:
        g[r][c] = 5
    # An earlier row-major object and a later east hit are irrelevant.
    for r, c in [(0, 0), (0, 1), (3, 9), (4, 9)]:
        g[r][c] = 5
    before = deepcopy(g)
    info = a.core.ray_component(g)
    assert info["hit"] == [3, 5] and info["size"] == 7
    assert a.core.effective_period(g, "ray_size") == 3
    out = a.core.mirror(g, "ray_size")
    assert out[0][1] == 5 and out[0][4] == 8 and out[1][1] == 0
    assert g == before
    for r, row in enumerate(g):
        for c, v in enumerate(row):
            if v != 0:
                assert out[r][c] == v
    g[5][7] = 0
    assert a.core.ray_component(g)["size"] == 6
    assert a.core.effective_period(g, "ray_size") == 2
    assert a.core.mirror(g, "ray_size")[1][1] == 8


def test_maximum_profile_has_substantive_content_and_boundary_coverage():
    a = load_adapter()
    for seed in [0, 17, 44]:
        e = a.generate(seed, {"lattice_rule": "ray_size"}, 3, 4)
        g = e["test"][-1]["input"]
        out = e["test"][-1]["output"]
        assert len(g) == len(g[0]) == 30
        assert 100 <= sum(v == 5 for row in g for v in row) <= 600
        changed = {(r, c) for r in range(30) for c in range(30) if g[r][c] != out[r][c]}
        assert len(changed) >= 35
        assert {r // 15 for r, c in changed} == {0, 1}
        assert {c // 15 for r, c in changed} == {0, 1}
        assert any(g[r][c] == 5 for r, c in [(0, 0), (0, 29), (29, 0), (29, 29)])


@pytest.mark.parametrize("seed,demos,queries", [
    (True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, True, 4),
    (0, 1, 4), (0, 7, 4), (0, 3, False), (0, 3, 0), (0, 3, 5),
])
def test_strict_request_boundary(seed, demos, queries):
    with pytest.raises(ValueError):
        load_adapter().generate(seed, {"lattice_rule": "ray_size"}, demos, queries)


@pytest.mark.parametrize("settings", [{}, {"lattice_rule": True}, {"lattice_rule": "bogus"},
                                         {"lattice_rule": "period2", "extra": 1}, None])
def test_settings_fail_closed(settings):
    with pytest.raises(ValueError):
        load_adapter().program(settings)


def test_public_projection_hides_private_state_and_has_stable_first_turn():
    from reviewer_support import public_challenge_bytes, public_challenge_id
    a = load_adapter()
    episode = a.generate(44, {"lattice_rule": "ray_size"}, 3, 4)
    public = a.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(p) == {"input"} for p in public["test"])
    private_changed = deepcopy(episode)
    private_changed["settings"] = {"lattice_rule": "private-only"}
    private_changed["program_solution"] = "private-only"
    private_changed["test"][0]["output"] = [[9]]
    private_changed["train"][0]["private_metadata"] = {"answer": 9}
    assert all(set(p) == {"input", "output"} for p in a.public_challenge(private_changed)["train"])
    assert public_challenge_bytes(public) == public_challenge_bytes(a.public_challenge(private_changed))
    assert public_challenge_id(public) == public_challenge_id(a.public_challenge(private_changed))
    assert a.public_challenge(episode, query_index=0) == a.public_challenge(
        a.generate(44, {"lattice_rule": "ray_size"}, 3, 1), query_index=0)
    first = a.public_challenge(episode, query_index=0)
    assert len(first["test"]) == 1
    first["train"][0]["input"][0][0] = 9
    assert first != a.public_challenge(episode, query_index=0)


@pytest.mark.parametrize("seed", [0, 17, 44])
@pytest.mark.parametrize("demos", [2, 3])
@pytest.mark.parametrize("mode", ["period2", "period3", "ray_size"])
def test_demonstrations_refute_reproduced_structural_shortcuts(seed, demos, mode):
    spec = importlib.util.spec_from_file_location("_c9034_independent_rivals", PARAMETRIC / "rivals.py")
    rivals = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rivals)
    episode = load_adapter().generate(seed, {"lattice_rule": mode}, demos, 4)
    surviving = set(rivals.fitting_rivals(episode["train"], mode))
    assert not surviving.intersection(rivals.EMPIRICAL_RISK_RIVALS)
