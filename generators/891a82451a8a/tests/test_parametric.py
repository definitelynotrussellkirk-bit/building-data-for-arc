"""Focused contracts for the separate direct/corner-relay family."""
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
SOURCE = HOME / "workspace/parametric/prototype.py"


@pytest.fixture(scope="module")
def proto():
    spec = importlib.util.spec_from_file_location("ring_parameter_tests", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid(h, w, r, c, color, bg=7):
    result = [[bg] * w for _ in range(h)]
    result[r][c] = color
    return result


def test_default_is_exact_canonical_program(proto):
    programs = {
        row["program_solution"]
        for row in map(json.loads, (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines())
        if row["task_id"] == "891a82451a8a"
    }
    assert programs == {proto.program({"mode": "direct"})}


def test_relay_uses_wave_phase_and_row_major_corner_tie(proto):
    # Cycle phases at the corners are 1, 5, 6, 1: TL wins the TL/BR tie.
    g = grid(8, 8, 1, 6, 8)
    state = proto.intermediate(g)
    assert state["corner_phases"] == [1, 5, 6, 1]
    assert state["relay"] == [0, 0]
    assert state["relay_phase"] == 1
    answer = proto.solve(g, {"mode": "corner_relay"})
    assert answer[0] == [5, 2, 8, 9, 6, 1, 3, 4]
    assert answer[7][7] == 1
    changed = grid(8, 8, 1, 6, 4)
    assert proto.intermediate(changed)["relay"] != state["relay"]


@pytest.mark.parametrize("seed", [0, 17, 41, 2**63 - 1])
def test_two_demos_teach_all_declared_rivals_with_matched_inputs(proto, seed):
    episodes = [proto.generate(seed, {"mode": mode}, 2, 4) for mode in proto.MODES]
    assert [[p["input"] for p in e["train"] + e["test"]] for e in episodes][0] == [p["input"] for p in episodes[1]["train"] + episodes[1]["test"]]
    for mode, episode in zip(proto.MODES, episodes):
        assert len(episode["train"]) == 2 and len(episode["test"]) == 4
        inputs = [json.dumps(p["input"]) for p in episode["train"] + episode["test"]]
        assert len(set(inputs)) == 6
        assert proto.teaching_report(episode["train"], {"mode": mode})["all_refuted"]
        assert [(len(p["input"]), len(p["input"][0])) for p in episode["test"]] == [(5, 5), (14, 23), (23, 18), (30, 30)]
        assert len({v for row in episode["test"][-1]["output"] for v in row}) == 9


def test_counts_are_independent_and_first_query_is_prefix_stable(proto):
    for mode in proto.MODES:
        a = proto.generate(4, {"mode": mode}, 2, 1)
        b = proto.generate(4, {"mode": mode}, 6, 8)
        assert a["train"] == b["train"][:2]
        assert a["test"] == proto.generate(4, {"mode": mode}, 2, 8)["test"][:1]
        assert len({json.dumps(p["input"]) for p in b["train"] + b["test"]}) == 14


def test_public_projection_uses_only_visible_fields_and_one_query(proto):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    import copy

    e = proto.generate(17, {"mode": "corner_relay"}, 3, 4)
    first = proto.turn_challenge(e, 0)
    assert len(first["test"]) == 1
    assert set(first) == {"train", "test"}
    assert set(first["test"][0]) == {"input"}
    one = copy.deepcopy(e)
    one["test"] = one["test"][:1]
    assert public_challenge_bytes(first) == public_challenge_bytes(proto.turn_challenge(one, 0))
    e["settings"] = {"secret": "changed"}
    e["seed"] = 999
    e["program_solution"] = "changed"
    e["test"][0]["output"][0][0] = (e["test"][0]["output"][0][0] + 1) % 10
    e["test"][1]["input"][0][0] = (e["test"][1]["input"][0][0] + 1) % 10
    assert public_challenge_id(proto.turn_challenge(e, 0)) == public_challenge_id(first)
    with pytest.raises((ValueError, TypeError)):
        proto.turn_challenge(e, True)


@pytest.mark.parametrize("settings", [{}, {"mode": "bad"}, {"mode": True}, {"mode": "direct", "extra": 1}, None])
def test_bad_settings_rejected(proto, settings):
    with pytest.raises((TypeError, ValueError)):
        proto.program(settings)


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, 1, 4), (0, 7, 4), (0, True, 4), (0, 3, 0), (0, 3, 9), (0, 3, 4.0)])
def test_invalid_counts_fail_loudly(proto, seed, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        proto.generate(seed, {"mode": "direct"}, demos, queries)


@pytest.mark.parametrize("bad", [
    grid(4, 5, 1, 1, 5), grid(31, 5, 1, 1, 5),
    grid(5, 5, 1, 1, 5, bg=0), [[7] * 5 for _ in range(5)],
    grid(5, 5, 1, 1, 7, bg=1), grid(5, 5, 1, 1, True),
])
def test_invalid_input_grammar_rejected(proto, bad):
    with pytest.raises((ValueError, TypeError)):
        proto.solve(bad, {"mode": "corner_relay"})


def test_teaching_rejects_corrupt_demo_and_ignores_query_answers(proto):
    import copy

    e = proto.generate(0, {"mode": "corner_relay"}, 2, 4)
    demos = copy.deepcopy(e["train"])
    demos[0]["output"][0][0] = (demos[0]["output"][0][0] + 1) % 10
    with pytest.raises(ValueError, match="label"):
        proto.teaching_report(demos, {"mode": "corner_relay"})


def test_teaching_rejects_boolean_output_even_when_equal_to_zero(proto):
    import copy

    e = proto.generate(0, {"mode": "direct"}, 2, 4)
    demos = copy.deepcopy(e["train"])
    out = demos[0]["output"]
    r, c = next((r, c) for r, row in enumerate(out) for c, value in enumerate(row) if value == 0)
    out[r][c] = False
    with pytest.raises(ValueError, match="label"):
        proto.teaching_report(demos, {"mode": "direct"})


@pytest.mark.parametrize("demos", [2, 3, 4, 6])
def test_omit_corner_shortcuts_cannot_change_queries(proto, demos):
    settings = {"mode": "corner_relay"}
    episode = proto.generate(0, settings, demos, 4)
    taught = {proto.intermediate(p["input"])["selected_corner_index"] for p in episode["train"]}
    queried = {proto.intermediate(p["input"])["selected_corner_index"] for p in episode["test"]}
    assert len(taught) == min(demos, 4)
    assert queried == taught
    for omitted in range(4):
        name = f"omit_corner_{omitted}"
        if all(proto.solve(p["input"], settings, name) == p["output"] for p in episode["train"]):
            assert all(proto.solve(p["input"], settings, name) == p["output"] for p in episode["test"])


def test_ties_teach_row_major_not_distance_or_column_order(proto):
    settings = {"mode": "corner_relay"}
    near = grid(9, 10, 5, 1, 1)
    far = grid(12, 9, 2, 3, 9)
    assert proto.intermediate(near)["selected_corner_index"] == 1
    assert proto.intermediate(far)["selected_corner_index"] == 0
    for name in ("nearest_tie", "column_major_tie"):
        assert proto.solve(near, settings, name) != proto.solve(near, settings)
    assert proto.solve(far, settings, "farthest_tie") != proto.solve(far, settings)


def test_all_fixed_priority_survivors_agree_on_queries(proto):
    from itertools import permutations

    episode = proto.generate(3, {"mode": "corner_relay"}, 3, 4)
    for order in permutations(range(4)):
        def winner(g):
            phases = proto.intermediate(g)["corner_phases"]
            return min(order, key=lambda i: phases[i])
        if all(winner(p["input"]) == proto.intermediate(p["input"])["selected_corner_index"] for p in episode["train"]):
            assert all(winner(p["input"]) == proto.intermediate(p["input"])["selected_corner_index"] for p in episode["test"])
