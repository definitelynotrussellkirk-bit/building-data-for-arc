"""Focused regressions for the proposed output-order parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
HOME = ROOT / "generators/1b7cbdffd485"
PARAMETRIC = HOME / "workspace/parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
PROMOTION_PATH = PARAMETRIC / "promotion.json"


def _adapter():
    assert ADAPTER_PATH.is_file(), "output-order adapter has not been built"
    spec = importlib.util.spec_from_file_location(
        "_task_1b7cbdffd485_output_order_adapter", ADAPTER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _outputs(episode):
    return [pair["output"] for pair in episode["train"] + episode["test"]]


def _flatten(value):
    return [cell for row in value for cell in row]


def test_contract_declares_only_two_output_orders_and_required_bounds():
    assert PROMOTION_PATH.is_file(), "promotion contract has not been built"
    contract = json.loads(PROMOTION_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/1b7cbdffd485/workspace/parametric/adapter.py",
        "parameters": {"output_order": ["first_seen", "reverse_first_seen"]},
        "default": {"output_order": "first_seen"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "resources": [
            "generators/1b7cbdffd485/workspace/parametric/reverse_first_seen.rkt"
        ],
    }


def test_default_program_is_exact_canonical_and_alternative_is_distinct():
    adapter = _adapter()
    canonical = adapter.canonical_program()
    assert adapter.program({"output_order": "first_seen"}) == canonical
    alternate = adapter.program({"output_order": "reverse_first_seen"})
    assert alternate.strip()
    assert alternate != canonical
    with pytest.raises(ValueError):
        adapter.program({"output_order": "numeric"})
    with pytest.raises(ValueError):
        adapter.program({"output_order": "first_seen", "extra": True})


def test_handcrafted_grids_preserve_orientation_but_reverse_the_first_seen_sequence():
    adapter = _adapter()
    horizontal = [
        [8, 8, 8, 2, 2, 2],
        [8, 8, 8, 2, 2, 2],
        [8, 8, 8, 2, 2, 2],
        [5, 5, 5, 2, 2, 2],
        [5, 5, 5, 2, 2, 2],
        [5, 5, 5, 2, 2, 2],
    ]
    assert adapter.transform(horizontal, "first_seen") == [[8], [2], [5]]
    assert adapter.transform(horizontal, "reverse_first_seen") == [[5], [2], [8]]

    sloped = [
        [6, 6, 6, 1, 1, 9],
        [6, 6, 6, 1, 1, 9],
        [6, 6, 6, 1, 9, 9],
        [6, 6, 1, 1, 9, 9],
        [6, 1, 1, 9, 9, 9],
        [6, 1, 1, 9, 9, 9],
    ]
    assert adapter.transform(sloped, "first_seen") == [[6, 1, 9]]
    assert adapter.transform(sloped, "reverse_first_seen") == [[9, 1, 6]]


def test_generation_uses_identical_inputs_across_settings_and_teaches_the_choice():
    adapter = _adapter()
    first = adapter.generate(17, {"output_order": "first_seen"}, 3, 4)
    reverse = adapter.generate(17, {"output_order": "reverse_first_seen"}, 3, 4)

    assert _inputs(first) == _inputs(reverse)
    assert len({json.dumps(value, separators=(",", ":")) for value in _inputs(first)}) == 7
    assert all(a != b for a, b in zip(_outputs(first), _outputs(reverse)))
    assert all(
        (len(a), len(a[0])) == (len(b), len(b[0]))
        for a, b in zip(_outputs(first), _outputs(reverse))
    )
    assert all(_flatten(a) == list(reversed(_flatten(b))) for a, b in zip(_outputs(first), _outputs(reverse)))

    for setting, episode in (("first_seen", first), ("reverse_first_seen", reverse)):
        assert episode["program_solution"] == adapter.program({"output_order": setting})
        certificate = adapter.certificate(
            episode["train"], [pair["input"] for pair in episode["test"]]
        )
        assert certificate["survivors"] == [setting]
        assert certificate["demos"] == 3
        assert certificate["queries"] == 4
        assert certificate["query_labels_used_for_inference"] is False
        assert certificate["row_output_witness"] is True
        assert certificate["column_output_witness"] is True
        assert certificate["tie_boundary_witness"] is True


def test_supported_counts_are_exact_and_every_episode_has_real_30x30_stress():
    adapter = _adapter()
    for demos in range(2, 7):
        for setting in adapter.OUTPUT_ORDERS:
            episode = adapter.generate(901 + demos, {"output_order": setting}, demos, 4)
            assert len(episode["train"]) == demos
            assert len(episode["test"]) == 4
            assert len(_inputs(episode)) == demos + 4
            assert len({json.dumps(value, separators=(",", ":")) for value in _inputs(episode)}) == demos + 4
            assert sum(len(pair["input"]) == len(pair["input"][0]) == 30 for pair in episode["test"]) >= 2
            for pair in episode["train"] + episode["test"]:
                observed = adapter.observe(pair["input"])
                assert observed["errors"] == []
                assert 3 <= len(observed["colors"]) <= 6
                assert pair["output"] == adapter.transform(pair["input"], setting)

    for demos, queries in ((1, 4), (7, 4), (2, 3), (2, 5)):
        with pytest.raises(ValueError):
            adapter.generate(3, {"output_order": "first_seen"}, demos, queries)


def test_generation_is_deterministic_fresh_and_does_not_touch_global_random_state():
    import random

    adapter = _adapter()
    random.seed(20261024)
    state = random.getstate()
    first = adapter.generate(101, {"output_order": "first_seen"}, 6, 4)
    assert random.getstate() == state
    second = adapter.generate(101, {"output_order": "first_seen"}, 6, 4)
    assert first == second
    assert first is not second
    assert first["train"] is not second["train"]
    assert all(a is not b for a, b in zip(_inputs(first), _inputs(second)))


def test_minimum_lesson_identifies_each_setting_across_bounded_seed_sweep():
    adapter = _adapter()
    for seed in range(32):
        for setting in adapter.OUTPUT_ORDERS:
            episode = adapter.generate(seed, {"output_order": setting}, 2, 4)
            certificate = adapter.certificate(
                episode["train"], [pair["input"] for pair in episode["test"]]
            )
            assert certificate["survivors"] == [setting]


def test_declared_shortcuts_do_not_survive_the_two_demo_lesson():
    adapter = _adapter()
    rivals = set(adapter.HYPOTHESES) - set(adapter.OUTPUT_ORDERS)
    assert {
        "numeric_order",
        "frequency_order",
        "column_major_order",
        "always_row_first_seen",
        "always_column_first_seen",
        "always_row_reverse_first_seen",
        "always_column_reverse_first_seen",
        "strict_tie_first_seen",
        "strict_tie_reverse_first_seen",
    } <= rivals
    for seed in (0, 17, 29, 71, 905):
        for setting in adapter.OUTPUT_ORDERS:
            episode = adapter.generate(seed, {"output_order": setting}, 2, 4)
            certificate = adapter.certificate(
                episode["train"], [pair["input"] for pair in episode["test"]]
            )
            assert certificate["survivors"] == [setting]
            assert all(rival not in certificate["survivors"] for rival in rivals)


def test_causal_witness_changes_output_when_the_first_hit_order_is_wrong():
    adapter = _adapter()
    witness = adapter.causal_witness()
    assert witness["step_a"] == "scan row-major and record ordered first-hit color/coordinate triples"
    assert witness["step_b"] == "compare coordinate spans, orient the output, and place colors in the episode order"
    assert witness["actual_intermediate"] == list(reversed(witness["wrong_intermediate"]))
    assert witness["actual_output"] != witness["counterfactual_output"]
    assert witness["actual_output"] == adapter.transform(
        witness["input"], witness["output_order"]
    )
    assert witness["counterfactual_output"] == adapter.transform(
        witness["input"], witness["counterfactual_output_order"]
    )


def test_public_projection_reveals_only_demonstration_labels_and_one_query_input():
    adapter = _adapter()
    episode = adapter.generate(19, {"output_order": "reverse_first_seen"}, 3, 4)
    for query_index in range(4):
        public = adapter.public_turn(episode, query_index)
        assert set(public) == {"train", "test"}
        assert public["train"] == episode["train"]
        assert public["test"] == [{"input": episode["test"][query_index]["input"]}]
        encoded = json.dumps(public, sort_keys=True)
        assert "output_order" not in encoded
        assert "program_solution" not in encoded
        for pair in episode["test"]:
            assert pair["output"] not in public["test"]
    before = copy.deepcopy(episode)
    adapter.public_turn(episode, 0)
    assert episode == before
