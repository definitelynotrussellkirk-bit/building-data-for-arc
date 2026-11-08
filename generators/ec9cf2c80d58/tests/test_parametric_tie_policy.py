"""Contract tests for the task-local extent-tie policy prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "ec9cf2c80d58"
TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_HOME / "workspace" / "parametric" / "prototype.py"
ROOT = find_root(__file__)


def _load_prototype():
    assert PROTOTYPE.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_ec9cf2c80d58", PROTOTYPE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            record = json.loads(line)
            if record.get("task_id") == TASK_ID:
                return record["program_solution"]
    raise AssertionError(f"missing canonical record for {TASK_ID}")


def _all_pairs(episode):
    return [*episode["train"], *episode["test"]]


def test_parametric_prototype_exists_and_declares_bounded_contract():
    proto = _load_prototype()
    assert proto.TASK_ID == TASK_ID
    assert proto.PARAMETERS == {
        "tie_policy": {
            "allowed": ("column", "row"),
            "default": "column",
            "selected_once_per_episode": True,
        }
    }


def test_default_program_is_exact_canonical_authority_and_row_tie_is_distinct():
    proto = _load_prototype()
    canonical = _canonical_program()
    column = proto.racket_program("column", root=ROOT)
    row = proto.racket_program("row", root=ROOT)
    assert column == canonical
    assert row != canonical
    assert "(if (> row-ext col-ext)" in row
    assert row.replace("(if (> row-ext col-ext)",
                       "(if (>= row-ext col-ext)", 1) == canonical


@pytest.mark.parametrize("bad_policy", [None, True, 0, "", "COLUMN", "columns"])
def test_parameter_policy_is_strictly_bounded(bad_policy):
    proto = _load_prototype()
    with pytest.raises(ValueError, match="tie_policy"):
        proto.racket_program(bad_policy, root=ROOT)
    with pytest.raises(ValueError, match="tie_policy"):
        proto.generate_episode(0, tie_policy=bad_policy, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, "1"])
def test_episode_seed_is_a_strict_python_integer(bad_seed):
    proto = _load_prototype()
    with pytest.raises(ValueError, match="seed must be a Python int"):
        proto.generate_episode(bad_seed, root=ROOT)


def test_episode_selects_one_parameter_once_and_is_deterministic():
    proto = _load_prototype()
    first = proto.generate_episode(20261022, root=ROOT)
    second = proto.generate_episode(20261022, root=ROOT)
    assert first == second
    assert first["parameter_draw_count"] == 1
    assert first["parameter"]["tie_policy"] in ("column", "row")
    assert len(first["train"]) == 3
    assert len(first["test"]) == 4
    inputs = [pair["input"] for pair in _all_pairs(first)]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 7
    assert first["program"] == proto.racket_program(
        first["parameter"]["tie_policy"], root=ROOT
    )


@pytest.mark.parametrize("policy", ["column", "row"])
def test_each_setting_builds_a_complete_identifiable_episode(policy):
    proto = _load_prototype()
    episode = proto.generate_episode(314159, tie_policy=policy, root=ROOT)
    opposite = "row" if policy == "column" else "column"
    pairs = _all_pairs(episode)
    assert all(proto.apply_python(pair["input"], policy) == pair["output"]
               for pair in pairs)
    assert all(proto.apply_python(pair["input"], opposite) != pair["output"]
               for pair in episode["train"])
    assert all(proto.apply_python(pair["input"], opposite) != pair["output"]
               for pair in episode["test"])


def test_default_setting_preserves_generator_contract_on_episode_inputs():
    proto = _load_prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    episode = proto.generate_episode(271828, tie_policy="column", root=ROOT)
    for pair in _all_pairs(episode):
        assert generator.self_check(pair["input"]) == []
        assert generator.rule_model(pair["input"]) == pair["output"]


def test_public_challenge_masks_parameter_program_metadata_and_query_answers():
    proto = _load_prototype()
    episode = proto.generate_episode(42, tie_policy="row", root=ROOT)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    encoded = json.dumps(public, sort_keys=True)
    for hidden in ("tie_policy", "program", "sample_index", "difficulty"):
        assert hidden not in encoded


def test_materialized_programs_execute_in_included_racket_runtime():
    proto = _load_prototype()
    builder_path = TASK_HOME / "workspace" / "parametric" / "build_evidence.py"
    assert builder_path.is_file(), "Racket evidence builder has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_evidence_ec9cf2c80d58", builder_path
    )
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    episode = proto.generate_episode(161803, tie_policy="column", root=ROOT)
    grid = episode["train"][0]["input"]
    runtime_identity = None
    outputs = {}
    for policy in ("column", "row"):
        actual, runtime = builder.execute_program(
            proto.racket_program(policy, root=ROOT), [grid]
        )
        runtime_identity = runtime_identity or runtime
        assert runtime == runtime_identity
        assert actual == [proto.apply_python(grid, policy)]
        outputs[policy] = actual[0]
    assert outputs["column"] != outputs["row"]
