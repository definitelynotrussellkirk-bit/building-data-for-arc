"""Focused checks for the proposed tie-marker prototype, not canonical coverage."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_pairs, find_root


TASK_ID = "1b2b9283b4ab"


def load_prototype():
    root = find_root(__file__)
    path = root / "generators" / TASK_ID / "workspace/parametric/prototype.py"
    assert path.is_file(), "The runnable parametric prototype has not been implemented"
    spec = spec_from_file_location("tie_marker_prototype_tests", path)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, root


def digits(*rows):
    return [[int(cell) for cell in row] for row in rows]


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge(timeout=10) as value:
        yield value


def test_tie_parameter_changes_only_the_equal_distance_room(bridge):
    prototype, root = load_prototype()
    grid = digits(
        "1111111111111",
        "1000100010001",
        "1020700070301",
        "1000100010001",
        "1111111111111",
    )
    expected_default = digits(
        "1111111111111",
        "1222188813331",
        "1222788873331",
        "1222188813331",
        "1111111111111",
    )
    expected_alternative = digits(
        "1111111111111",
        "1222166613331",
        "1222766673331",
        "1222166613331",
        "1111111111111",
    )
    assert prototype.execute(bridge, prototype.materialize_rule(8, root=root), grid) == expected_default
    assert prototype.execute(bridge, prototype.materialize_rule(6, root=root), grid) == expected_alternative


def test_original_setting_matches_every_labelled_canonical_pair(bridge):
    prototype, root = load_prototype()
    program = prototype.materialize_rule(8, root=root)
    pairs = canonical_pairs(TASK_ID, root=root)
    assert pairs
    for pair in pairs:
        assert prototype.execute(bridge, program, pair["input"]) == pair["output"]


@pytest.mark.parametrize("seed,marker", [(0, 8), (1, 6)])
def test_episode_teaches_its_marker_before_every_query_position(bridge, seed, marker):
    prototype, root = load_prototype()
    episode = prototype.build_episode(seed, root=root, bridge=bridge)
    assert episode["parameters"] == {"tie_marker": marker}
    assert episode["demonstration_count"] == 3
    assert len(episode["labelled_pairs"]) == 4
    assert len(episode["parameter_rival_checks"]["refuting_pair_indices"]) >= 2
    assert episode["parameter_rival_checks"]["production"]["identifiable"] is True
    rotations = episode["parameter_rival_checks"]["rotations"]
    assert len(rotations) == 4
    assert all(row["identifiable"] for row in rotations)
    assert all(row["refuting_demo_indices"] for row in rotations)
    public = episode["public_challenge"]
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3 and len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert set(public["test"][0]) == {"input"}
    assert all(set(cell for row in pair["input"] for cell in row) <= {0, 1, 2, 3, 4, 5, 7}
               for pair in episode["labelled_pairs"])
    assert all(row["oracle_match"] for row in episode["execution_checks"])


def test_input_fixtures_are_seed_replayable_and_parameter_independent():
    prototype, _ = load_prototype()
    first = prototype.episode_inputs(19)
    assert first == prototype.episode_inputs(19)
    assert first != prototype.episode_inputs(20)
    assert len(first) == 4
    assert {row["spec"]["room_count"] for row in first} == {3, 4, 5, 7}


def test_invalid_tie_markers_are_rejected_before_execution():
    prototype, root = load_prototype()
    for marker in (True, 0, 1, 2, 5, 7, 9, 10):
        with pytest.raises(ValueError, match="tie_marker"):
            prototype.materialize_rule(marker, root=root)
