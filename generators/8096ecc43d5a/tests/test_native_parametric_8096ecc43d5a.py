from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve()
NATIVE = HERE.parents[1] / "workspace" / "parametric" / "native.py"


def load_native():
    spec = importlib.util.spec_from_file_location("_native_8096_test", NATIVE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_canonical_and_reverse_is_distinct():
    native = load_native()
    canonical = native.program({"script_order": "left_to_right"})
    reverse = native.program({"script_order": "right_to_left"})
    assert hashlib.sha256(canonical.encode()).hexdigest() == (
        "04788c0240d6550baf1344b31b28de075108d0b89dcfe18faf5f1615115fd17c"
    )
    assert reverse != canonical


def test_matched_inputs_prefixes_and_every_pair_exposes_order():
    native = load_native()
    forward = native.generate(17, {"script_order": "left_to_right"}, 2, 4)
    reverse = native.generate(17, {"script_order": "right_to_left"}, 2, 4)
    assert [p["input"] for p in forward["train"] + forward["test"]] == [
        p["input"] for p in reverse["train"] + reverse["test"]
    ]
    assert all(a["output"] != b["output"] for a, b in zip(forward["train"], reverse["train"]))
    assert all(a["output"] != b["output"] for a, b in zip(forward["test"], reverse["test"]))
    assert len(forward["test"][-1]["input"]) == 30
    assert len(forward["test"][-1]["input"][0]) == 30
    assert len(forward["test"][-1]["output"]) in (28, 30)
    assert len(forward["test"][-1]["output"][0]) in (28, 30)

    longer_demos = native.generate(17, {"script_order": "left_to_right"}, 6, 4)
    fewer_queries = native.generate(17, {"script_order": "left_to_right"}, 2, 1)
    assert forward["train"] == longer_demos["train"][:2]
    assert forward["test"] == longer_demos["test"]
    assert forward["train"] == fewer_queries["train"]
    assert forward["test"][:1] == fewer_queries["test"]


def test_large_query_is_substantive_and_touches_boundaries():
    native = load_native()
    episode = native.generate(0, {"script_order": "left_to_right"}, 3, 4)
    grid = episode["test"][-1]["input"]
    body = grid[2:]
    nonzero = sum(v != 0 for row in body for v in row)
    assert nonzero >= 500
    assert any(v != 0 for v in body[-1])
    assert any(row[0] != 0 for row in body)
    assert any(row[-1] != 0 for row in body)


def test_public_turn_masks_private_state_and_is_first_turn_stable():
    native = load_native()
    episode = native.generate(3, {"script_order": "right_to_left"}, 3, 4)
    one_query = native.generate(3, {"script_order": "right_to_left"}, 3, 1)
    turn = native.public_turn(episode, 0)
    assert turn == native.public_turn(one_query, 0)
    assert set(turn) == {"train", "test"}
    assert len(turn["test"]) == 1
    assert set(turn["test"][0]) == {"input"}
    visible = repr(turn).lower()
    for forbidden in ("script_order", "program_solution", "seed", "queries", "answer"):
        assert forbidden not in visible


def test_strict_settings_and_counts_fail_closed():
    native = load_native()
    bad_calls = [
        lambda: native.generate(True, {"script_order": "left_to_right"}, 2, 4),
        lambda: native.generate(-1, {"script_order": "left_to_right"}, 2, 4),
        lambda: native.generate(0, {"script_order": "left_to_right"}, 1, 4),
        lambda: native.generate(0, {"script_order": "left_to_right"}, 2, 5),
        lambda: native.generate(0, {"script_order": "unknown"}, 2, 4),
        lambda: native.generate(0, {"script_order": "left_to_right", "extra": 1}, 2, 4),
    ]
    for call in bad_calls:
        with pytest.raises(ValueError):
            call()


def test_two_demonstrations_reject_order_and_sequence_shortcuts():
    native = load_native()
    rivals = (
        "left_to_right",
        "right_to_left",
        "sorted_codes",
        "deduplicate_codes",
        "collapse_adjacent_codes",
        "first_only",
        "last_only",
        "ignore_script",
    )
    for seed in (0, 17):
        for setting in ("left_to_right", "right_to_left"):
            episode = native.generate(seed, {"script_order": setting}, 2, 4)
            for rival in rivals:
                if rival == setting:
                    continue
                assert not all(
                    native.rival_transform(pair["input"], rival) == pair["output"]
                    for pair in episode["train"]
                ), (seed, setting, rival)
