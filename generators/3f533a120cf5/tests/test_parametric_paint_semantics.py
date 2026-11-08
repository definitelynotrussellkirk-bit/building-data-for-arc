from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


REPO = find_root(__file__)
TASK_ID = "3f533a120cf5"
PROTOTYPE_PATH = (
    REPO / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)


def load_prototype():
    name = "generator_3f533a120cf5_parametric_prototype"
    spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


HAND_GRID = [
    [0, 2, 3, 3, 4, 0],
    [0, 9, 9, 9, 9, 0],
    [0, 0, 0, 0, 0, 0],
    [5, 5, 5, 5, 0, 0],
    [5, 0, 5, 5, 0, 0],
    [5, 5, 5, 0, 0, 0],
    [0, 0, 0, 0, 0, 0],
]

EXPECTED = {
    ("gray_cells", "forward"): [
        [2, 3, 3, 4],
        [2, 9, 3, 4],
        [2, 3, 3, 9],
    ],
    ("gray_cells", "reverse"): [
        [4, 3, 3, 2],
        [4, 9, 3, 2],
        [4, 3, 3, 9],
    ],
    ("bbox_holes", "forward"): [
        [9, 9, 9, 9],
        [9, 3, 9, 9],
        [9, 9, 9, 4],
    ],
    ("bbox_holes", "reverse"): [
        [9, 9, 9, 9],
        [9, 3, 9, 9],
        [9, 9, 9, 2],
    ],
}


def test_four_parameter_settings_produce_hand_checked_outputs():
    prototype = load_prototype()
    observed = {
        setting: prototype.python_transform(
            HAND_GRID,
            key_target=setting[0],
            key_order=setting[1],
        )
        for setting in EXPECTED
    }
    assert observed == EXPECTED
    assert len({repr(output) for output in observed.values()}) == 4


def test_canonical_default_matches_all_supplied_pairs_and_exact_racket():
    prototype = load_prototype()
    assert prototype.DEFAULT_PARAMETERS == {
        "key_target": "gray_cells",
        "key_order": "forward",
    }
    canonical = prototype.canonical_rule()
    assert prototype.instantiate_rule(**prototype.DEFAULT_PARAMETERS) == canonical
    for pair in canonical_pairs(TASK_ID, root=REPO):
        assert prototype.python_transform(
            pair["input"], **prototype.DEFAULT_PARAMETERS
        ) == pair["output"]


@pytest.mark.parametrize(
    "key_target,key_order",
    [
        ("gray", "forward"),
        ("gray_cells", "backward"),
        (True, "forward"),
        ("gray_cells", False),
    ],
)
def test_invalid_parameter_values_fail_loudly(key_target, key_order):
    prototype = load_prototype()
    with pytest.raises((TypeError, ValueError)):
        prototype.validate_parameters(key_target, key_order)


def test_only_declared_racket_paint_expression_edits_restore_to_canonical():
    prototype = load_prototype()
    canonical = prototype.canonical_rule()
    for key_target, key_order in EXPECTED:
        program = prototype.instantiate_rule(
            key_target=key_target,
            key_order=key_order,
        )
        assert prototype.restore_canonical(program) == canonical

    undeclared = prototype.instantiate_rule(
        key_target="bbox_holes", key_order="reverse"
    ).replace("(rows g)", "(cols g)", 1)
    with pytest.raises(ValueError, match="declared"):
        prototype.restore_canonical(undeclared)


def test_generated_inputs_are_distinct_lawful_and_expose_all_four_settings():
    prototype = load_prototype()
    inputs = prototype.generate_inputs(90210, demo_count=2, query_count=4)
    assert len(inputs) == 6
    assert len({repr(grid) for grid in inputs}) == 6
    for grid in inputs:
        assert prototype.GEN.self_check(grid) == []
        outputs = {
            repr(
                prototype.python_transform(
                    grid,
                    key_target=key_target,
                    key_order=key_order,
                )
            )
            for key_target, key_order in prototype.SETTINGS
        }
        assert len(outputs) == 4


def test_racket_episode_uses_one_setting_and_demos_identify_every_query():
    from arc_repl.racket_bridge import RacketBridge

    prototype = load_prototype()
    seed = 90211
    with RacketBridge(timeout=30) as bridge:
        episode = prototype.make_episode(
            bridge,
            seed,
            demo_count=2,
            query_count=4,
        )
        parameters = prototype.choose_parameters(seed)
        program = prototype.instantiate_rule(**parameters)
        for pair in [*episode["train"], *episode["test"]]:
            assert prototype.evaluate(bridge, program, pair["input"]) == pair["output"]
            assert prototype.python_transform(pair["input"], **parameters) == pair["output"]

    assert episode["parameters"] == parameters
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert all("parameters" not in pair for pair in [*episode["train"], *episode["test"]])

    visible_inputs = [pair["input"] for pair in [*episode["train"], *episode["test"]]]
    assert len({repr(grid) for grid in visible_inputs}) == 6

    selected = prototype.setting_id(**parameters)
    analysis = episode["analysis"]
    assert analysis["demo_compatible_settings"] == [selected]
    assert analysis["demos_refute_all_rivals"] is True
    assert len(analysis["query_identifiability"]) == 4
    assert all(
        row == {
            "query_index": index,
            "compatible_settings_from_demos": [selected],
            "identified": True,
        }
        for index, row in enumerate(analysis["query_identifiability"])
    )


def test_materialization_covers_all_settings_and_public_projection_is_opaque(tmp_path):
    import json
    import re

    from reviewer_support import public_challenge_bytes, public_challenge_id

    prototype = load_prototype()
    report = prototype.materialize(
        tmp_path,
        seed_start=90212,
        episode_count=4,
        demo_count=2,
        query_count=4,
    )

    assert report["status"] == "prototype"
    assert {row["setting_id"] for row in report["episodes"]} == {
        prototype.setting_id(key_target, key_order)
        for key_target, key_order in prototype.SETTINGS
    }
    assert [row["public_id"] for row in report["episodes"]] == sorted(
        row["public_id"] for row in report["episodes"]
    )

    public_files = sorted((tmp_path / "public").glob("*.json"))
    assert len(public_files) == 4
    assert all(re.fullmatch(r"challenge-[0-9a-f]{64}\.json", path.name) for path in public_files)

    for row in report["episodes"]:
        private = json.loads((tmp_path / row["private_path"]).read_text())
        public_path = tmp_path / row["public_path"]
        expected_public = prototype.public_challenge(private)
        assert public_path.read_bytes() == public_challenge_bytes(expected_public)
        assert row["public_id"] == public_challenge_id(expected_public)
        public = json.loads(public_path.read_text())
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 2
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert all(set(pair) == {"input"} for pair in public["test"])
        rendered = public_path.read_text().lower()
        assert "parameters" not in rendered
        assert "seed" not in rendered
        assert "racket" not in rendered

    verified = prototype.verify_materialized(tmp_path)
    assert verified == {
        "status": "verified",
        "episode_count": 4,
        "demo_count": 2,
        "query_count": 4,
        "all_settings_covered": True,
        "all_labels_match_racket": True,
        "all_queries_identified_from_demos": True,
        "public_projection_valid": True,
    }
