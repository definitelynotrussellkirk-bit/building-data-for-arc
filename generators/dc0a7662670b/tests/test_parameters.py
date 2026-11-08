"""Native parametric-family regressions for dc0a7662670b.

The canonical setting must remain byte-for-byte identical to the selected
Racket authority.  The alternate setting performs a real relay:
perimeter-rank components -> width of the first ranked crop -> select and
recolor that ranked crop.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root, public_challenge_bytes

TASK_ID = "dc0a7662670b"
ROOT = find_root(__file__)
PARAMETRIC = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing parametric source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _adapter():
    return _load("dc0a7662670b_parametric_adapter_test", "adapter.py")


def _prototype():
    return _load("dc0a7662670b_parametric_prototype_test", "prototype.py")


def _canonical_program() -> str:
    record = Catalog(ROOT).get(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def _assert_grid(grid: object) -> None:
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    width = len(grid[0])
    for row in grid:
        assert type(row) is list and len(row) == width
        assert all(type(cell) is int and 0 <= cell <= 9 for cell in row)


def _input_sequence(episode: dict) -> list[list[list[int]]]:
    return [
        pair["input"]
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_promotion_contract_and_exact_canonical_default():
    adapter = _adapter()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/dc0a7662670b/workspace/parametric/adapter.py",
        "parameters": {"mode": ["canonical", "winner_width_relay"]},
        "default": {"mode": "canonical"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            "generators/dc0a7662670b/workspace/parametric/prototype.py",
            "generators/dc0a7662670b/workspace/parametric/canonical.rkt",
            "generators/dc0a7662670b/workspace/parametric/winner_width_relay.rkt",
        ],
    }
    canonical = _canonical_program()
    assert (PARAMETRIC / "canonical.rkt").read_text() == canonical
    assert adapter.program({"mode": "canonical"}) == canonical
    assert adapter.program({"mode": "winner_width_relay"}) != canonical

    for bad in (
        {},
        {"mode": "unknown"},
        {"mode": True},
        {"mode": "canonical", "extra": 1},
        None,
    ):
        with pytest.raises((TypeError, ValueError)):
            adapter.program(bad)


def test_generate_is_deterministic_count_bounded_matched_and_prefix_stable():
    adapter = _adapter()
    settings = [{"mode": "canonical"}, {"mode": "winner_width_relay"}]

    for demos in (2, 3, 6):
        for queries in (1, 4):
            episodes = [adapter.generate(17, item, demos, queries) for item in settings]
            assert episodes == [adapter.generate(17, item, demos, queries) for item in settings]
            assert _input_sequence(episodes[0]) == _input_sequence(episodes[1])
            for episode, item in zip(episodes, settings):
                assert len(episode["train"]) == demos
                assert len(episode["test"]) == queries
                assert episode["program_solution"] == adapter.program(item)
                serialized = []
                for split in ("train", "test"):
                    for pair in episode[split]:
                        assert set(pair) == {"input", "output"}
                        _assert_grid(pair["input"])
                        _assert_grid(pair["output"])
                        serialized.append(json.dumps(pair["input"], separators=(",", ":")))
                assert len(serialized) == len(set(serialized))

    for item in settings:
        one = adapter.generate(1234, item, 3, 1)
        four = adapter.generate(1234, item, 3, 4)
        assert one["train"] == four["train"]
        assert one["test"][0] == four["test"][0]

    for bad_demos in (1, 7, True, 2.0):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings[0], bad_demos, 4)
    for bad_queries in (0, 5, True, 1.0):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings[0], 3, bad_queries)
    for bad_seed in (-1, True, 1.5, "1"):
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(bad_seed, settings[0], 3, 4)


def test_width_relay_uses_ranked_winner_width_and_marks_only_selected_crop():
    adapter = _adapter()
    prototype = _prototype()
    canonical = adapter.generate(29, {"mode": "canonical"}, 6, 4)
    relay = adapter.generate(29, {"mode": "winner_width_relay"}, 6, 4)
    assert _input_sequence(canonical) == _input_sequence(relay)

    selectors = set()
    for canonical_pair, relay_pair in zip(
        canonical["train"] + canonical["test"], relay["train"] + relay["test"]
    ):
        facts = prototype.analyze(canonical_pair["input"])
        selectors.add(facts["winner_width"])
        assert facts["winner_width"] in {1, 2, 3}
        assert canonical_pair["output"] == prototype.transform(
            canonical_pair["input"], {"mode": "canonical"}
        )
        assert relay_pair["output"] == prototype.transform(
            relay_pair["input"], {"mode": "winner_width_relay"}
        )
        assert 8 not in {cell for row in canonical_pair["output"] for cell in row}
        assert prototype.highlighted_rank(relay_pair["output"], facts) == facts["winner_width"]
    assert selectors == {1, 2, 3}


def test_large_query_is_a_substantive_30_by_30_boundary_case():
    adapter = _adapter()
    prototype = _prototype()
    pair = adapter.generate(41, {"mode": "winner_width_relay"}, 3, 4)["test"][-1]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    facts = prototype.analyze(grid)
    assert len(facts["ranked"]) == 7
    assert sum(cell != 0 for row in grid for cell in row) >= 60
    assert any(grid[0][col] != 0 for col in range(30))
    assert any(grid[29][col] != 0 for col in range(30))
    assert any(row[0] != 0 for row in grid)
    assert any(row[29] != 0 for row in grid)
    assert len(pair["output"]) <= 30 and len(pair["output"][0]) <= 30


def test_public_turn_masks_private_material_and_is_first_turn_stable():
    adapter = _adapter()
    prototype = _prototype()
    one = adapter.generate(53, {"mode": "winner_width_relay"}, 3, 1)
    four = adapter.generate(53, {"mode": "winner_width_relay"}, 3, 4)
    public_one = prototype.public_turn(one, 0)
    public_four = prototype.public_turn(four, 0)
    assert public_one == public_four
    assert set(public_one) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public_one["train"])
    assert all(set(pair) == {"input"} for pair in public_one["test"])

    payload = public_challenge_bytes(public_one)
    mutated = deepcopy(four)
    mutated["program_solution"] = "private replacement"
    mutated["settings"] = {"mode": "canonical"}
    mutated["seed"] = 999999
    assert public_challenge_bytes(prototype.public_turn(mutated, 0)) == payload
    assert prototype.public_id(four, 0) == hashlib.sha256(payload).hexdigest()

    with pytest.raises((TypeError, ValueError, IndexError)):
        prototype.public_turn(four, True)
    with pytest.raises((TypeError, ValueError, IndexError)):
        prototype.public_turn(four, 4)


def test_wrong_height_intermediate_counterfactual_changes_final_output():
    prototype = _prototype()
    witness = prototype.causal_witness(seed=71)
    assert witness["step_a"] == "rank_components_by_true_perimeter_then_color"
    assert witness["intermediate_name"] == "winner_crop_width"
    assert witness["step_b"] == "recolor_the_width_ranked_crop_to_8"
    assert witness["actual_intermediate"] != witness["counterfactual_intermediate"]
    assert witness["program_output"] != witness["counterfactual_output"]
    assert witness["input_shape"] == [30, 30]
    assert witness["changed_cells"] > 0
