"""Focused opt-in family tests; production generation is unchanged."""
from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
SPEC = importlib.util.spec_from_file_location("tally_parameters", HOME / "workspace/parametric/prototype.py")
P = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(P)


def test_cancellation_precedes_saturation():
    assert P.residual_counts(8, 3, "cancel_opposites") == (5, 0)
    assert P.emblem(5, 0) == P.emblem(4, 0)
    assert P.emblem(*P.residual_counts(8, 3, "cancel_opposites")) != P.emblem(1, 0)
    assert P.residual_counts(3, 3, "cancel_opposites") == (0, 0)
    assert P.residual_counts(3, 8, "cancel_opposites") == (0, 5)
    assert P.residual_counts(3, 8, "raw") == (3, 8)


def test_default_demos_refute_each_color_saturation_shortcut():
    """The prior seed17 three-demo lesson admitted green-cap3 on query1."""
    episode = P.generate(17, {"count_mode": "cancel_opposites"})
    for color, last in ((1, P.BLUE[-1]), (3, P.GREEN[-1])):
        rival_predictions = []
        for pair in episode["train"]:
            prediction = deepcopy(pair["output"])
            if sum(v == color for row in prediction for v in row) == 4:
                prediction[last[0]][last[1]] = 0
            rival_predictions.append(prediction)
        assert any(prediction != pair["output"]
                   for prediction, pair in zip(rival_predictions, episode["train"]))


@pytest.mark.parametrize("mode", P.SETTINGS)
def test_matching_inputs_prefixes_novelty_and_no_mutation(mode):
    settings = {"count_mode": mode}
    short = P.generate(17, settings, demos=4, queries=1)
    full = P.generate(17, settings, demos=6, queries=4)
    assert short["train"] == full["train"][:4]
    assert short["test"] == full["test"][:1]
    assert full == P.generate(17, settings, demos=6, queries=4)
    assert len({str(pair["input"]) for pair in full["train"] + full["test"]}) == 10
    for pair in full["train"] + full["test"]:
        before = deepcopy(pair["input"])
        assert P.solve(pair["input"], count_mode=mode) == pair["output"]
        assert pair["input"] == before
        assert len(pair["output"]) == 3 and len(pair["output"][0]) == 6


def test_shared_bank_teaches_two_winners_ties_and_order():
    raw = P.generate(0, {"count_mode": "raw"})
    cancel = P.generate(0, {"count_mode": "cancel_opposites"})
    assert [p["input"] for p in raw["train"] + raw["test"]] == [p["input"] for p in cancel["train"] + cancel["test"]]
    first = [P.counts(p["input"]) for p in cancel["train"]]
    assert abs(first[0][0] - first[0][1]) >= 4
    assert abs(first[1][0] - first[1][1]) >= 4
    assert (first[0][0] > first[0][1]) != (first[1][0] > first[1][1])
    assert 1 <= abs(first[2][0] - first[2][1]) <= 3
    assert first[3][0] == first[3][1] > 0
    assert all(a["output"] != b["output"] for a, b in zip(raw["train"], cancel["train"]))
    correct = cancel["train"][0]["output"]
    before_cap = tuple(min(v, 4) for v in first[0])
    wrong = P.emblem(*P.residual_counts(*before_cap, "cancel_opposites"))
    assert wrong != correct
    assert cancel["train"][3]["output"] == [[0] * 6 for _ in range(3)]


def test_minimum_and_dense_boundary_are_real_scenes():
    episode = P.generate(0, {"count_mode": "cancel_opposites"})
    small, large = episode["test"][0]["input"], episode["test"][3]["input"]
    assert (len(small), len(small[0])) == (2, 3)
    assert sum(P.counts(small)) == 1
    assert (len(large), len(large[0])) == (30, 30)
    assert sum(P.counts(large)) == 54
    assert sum(v == 2 for row in large for v in row) == 216
    assert any(large[0]) and any(large[-1])
    assert any(row[0] for row in large) and any(row[-1] for row in large)
    assert P.validate_grid(large)


def test_first_four_teach_four_connectivity_in_both_modes():
    for mode in P.SETTINGS:
        episode = P.generate(22, {"count_mode": mode})
        wrong = [P.emblem(*P.residual_counts(*P.counts(p["input"], connectivity=8), mode)) for p in episode["train"]]
        assert any(out != pair["output"] for out, pair in zip(wrong, episode["train"]))


def test_exact_catalog_default_and_declared_four_demo_minimum():
    from arcpuzzles import Catalog
    record = Catalog(ROOT).get("e971e0773705")
    source = {v["program_solution"] for v in record["variants"] if isinstance(v.get("program_solution"), str)}
    assert source == {P.program({"count_mode": "raw"})}
    with pytest.raises(ValueError):
        P.generate(0, {"count_mode": "cancel_opposites"}, demos=3)


@pytest.mark.parametrize("settings", [{}, None, {"count_mode": True}, {"count_mode": "other"}, {"count_mode": "raw", "extra": 1}])
def test_invalid_settings_fail(settings):
    with pytest.raises(ValueError):
        P.generate(0, settings)


@pytest.mark.parametrize("seed,demos,queries", [(-1, 4, 4), (True, 4, 4), (2**63, 4, 4), (0, 3, 4), (0, 7, 4), (0, True, 4), (0, 4, 0), (0, 4, 5), (0, 4, False)])
def test_invalid_requests_fail(seed, demos, queries):
    with pytest.raises(ValueError):
        P.generate(seed, {"count_mode": "raw"}, demos=demos, queries=queries)


@pytest.mark.parametrize("bad", [[], [[0]], [[True, 2, 2], [0, 2, 0]], [[2, 2], [2, 2]], [[2, 2, 2], [0, 2]], [[1, 1, 1], [0, 1, 0]]])
def test_strict_exact_t_grammar(bad):
    with pytest.raises(ValueError):
        P.validate_grid(bad)


def test_racket_sources_execute_and_match_at_boundaries():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator
    from puzzle_generators.rule_wrap import wrap_rule
    runtime = ROOT / "shared/runtime"
    with _local_imports(runtime, HOME / "workspace/parametric"):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            for mode in P.SETTINGS:
                source = P.program({"count_mode": mode})
                assert wrap_rule(source)
                episode = P.generate(0, {"count_mode": mode})
                for pair in (episode["train"][0], episode["test"][0], episode["test"][-1]):
                    assert apply(source, pair["input"]) == pair["output"]
            pair = P.generate(0, {"count_mode": "cancel_opposites"})["train"][0]
            wrong = P.rule_program("cancel_opposites", cap_before_cancel=True)
            assert wrap_rule(wrong)
            assert apply(wrong, pair["input"]) != pair["output"]
        finally:
            bridge.close()
