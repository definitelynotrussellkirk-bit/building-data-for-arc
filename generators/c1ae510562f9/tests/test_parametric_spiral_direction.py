"""Prototype-only tests for the episode-level spiral-direction parameter."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "workspace"
    / "parametric"
    / "spiral_direction.py"
)


def load_proto():
    assert MODULE_PATH.is_file(), "missing spiral-direction prototype"
    spec = importlib.util.spec_from_file_location(
        "parametric_spiral_direction_c1ae510562f9", MODULE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_default_materialization_matches_selected_rule_and_variant_is_distinct():
    proto = load_proto()
    clockwise = proto.materialize_rule("clockwise")
    counterclockwise = proto.materialize_rule("counterclockwise")
    assert proto.ALLOWED_DIRECTIONS == ("clockwise", "counterclockwise")
    assert proto.DEFAULT_DIRECTION == "clockwise"
    assert proto.normalized_hash(clockwise) == "7a7c1a560527"
    assert counterclockwise != clockwise
    assert proto.normalized_hash(counterclockwise) != proto.normalized_hash(clockwise)


def test_lawful_fixtures_distinguish_both_spiral_directions():
    proto = load_proto()
    cases = proto.fixtures()
    assert [case["empty_rows"] for case in cases] == [2, 3, 4, 6, 5]
    for case in cases:
        grid = case["input"]
        assert proto.empty_row_count(grid) == case["empty_rows"]
        clockwise = proto.python_mirror(grid, "clockwise")
        counterclockwise = proto.python_mirror(grid, "counterclockwise")
        assert clockwise != counterclockwise
        assert sum(value == 8 for row in clockwise for value in row) == case["empty_rows"]
        assert sum(value == 8 for row in counterclockwise for value in row) == case["empty_rows"]


def test_episode_chooses_one_direction_and_public_view_hides_private_data():
    proto = load_proto()
    assert proto.choose_direction(0) == "counterclockwise"
    assert proto.choose_direction(1) == "clockwise"
    for seed in range(16):
        episode = proto.build_episode(seed)
        direction = proto.choose_direction(seed)
        assert episode["parameter"] == {"spiral_direction": direction}
        assert episode["seed"] == seed
        assert len(episode["demonstrations"]) == 4
        pairs = episode["demonstrations"] + [episode["query"]]
        other = next(value for value in proto.ALLOWED_DIRECTIONS if value != direction)
        for pair in pairs:
            assert pair["output"] == proto.python_mirror(pair["input"], direction)
            assert pair["output"] != proto.python_mirror(pair["input"], other)
        public = proto.public_challenge(episode)
        assert set(public) == {"schema", "task_id", "train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert public["test"] == [{"input": episode["query"]["input"]}]


def test_racket_verifier_materializes_source_bound_evidence(tmp_path):
    proto = load_proto()
    summary = proto.run_prototype(tmp_path)
    assert summary["passed"] is True
    assert summary["checks"] == {
        "default_hash_matches_selected_rule": True,
        "racket_python_parity": True,
        "all_demonstrations_distinguish_settings": True,
        "all_queries_distinguish_settings": True,
        "public_records_hide_parameter_source_seed_and_query_answer": True,
    }
    assert (tmp_path / "summary.json").is_file()
    for direction in proto.ALLOWED_DIRECTIONS:
        assert (tmp_path / "rules" / f"{direction}.rkt").is_file()
        assert (tmp_path / "episodes" / direction / "private.json").is_file()
        assert (tmp_path / "episodes" / direction / "public.json").is_file()
