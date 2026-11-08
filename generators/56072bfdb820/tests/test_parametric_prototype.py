"""Contract tests for the task-local clip/wrap parameter prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "56072bfdb820"
TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE = TASK_HOME / "workspace" / "parametric" / "prototype.py"
ROOT = find_root(__file__)


def _load_prototype():
    assert PROTOTYPE.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location("parametric_56072bfdb820", PROTOTYPE)
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
        "boundary_mode": {
            "allowed": ("clip", "wrap"),
            "default": "clip",
            "selected_once_per_episode": True,
        }
    }


def test_default_program_is_exact_canonical_authority_and_wrap_is_distinct():
    proto = _load_prototype()
    canonical = _canonical_program()
    assert proto.racket_program("clip", root=ROOT) == canonical
    assert proto.racket_program("wrap", root=ROOT) != canonical
    assert "(modulo (first e) 3)" in proto.racket_program("wrap", root=ROOT)


@pytest.mark.parametrize("bad_mode", [None, True, 0, "", "CLIP", "clipped"])
def test_parameter_mode_is_strictly_bounded(bad_mode):
    proto = _load_prototype()
    with pytest.raises(ValueError, match="boundary_mode"):
        proto.racket_program(bad_mode, root=ROOT)
    with pytest.raises(ValueError, match="boundary_mode"):
        proto.generate_episode(0, boundary_mode=bad_mode, root=ROOT)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, "1"])
def test_episode_seed_is_a_strict_python_integer(bad_seed):
    proto = _load_prototype()
    with pytest.raises(ValueError, match="seed must be a Python int"):
        proto.generate_episode(bad_seed, root=ROOT)


def test_episode_selects_one_parameter_once_and_is_deterministic():
    proto = _load_prototype()
    first = proto.generate_episode(20261019, root=ROOT)
    second = proto.generate_episode(20261019, root=ROOT)
    assert first == second
    assert first["parameter_draw_count"] == 1
    assert first["parameter"]["boundary_mode"] in ("clip", "wrap")
    assert len(first["train"]) == 3
    assert len(first["test"]) == 1
    assert first["program"] == proto.racket_program(
        first["parameter"]["boundary_mode"], root=ROOT
    )


@pytest.mark.parametrize("mode", ["clip", "wrap"])
def test_each_setting_builds_a_complete_identifiable_episode(mode):
    proto = _load_prototype()
    episode = proto.generate_episode(314159, boundary_mode=mode, root=ROOT)
    opposite = "wrap" if mode == "clip" else "clip"
    pairs = _all_pairs(episode)
    assert all(
        proto.apply_python(pair["input"], mode) == pair["output"]
        for pair in pairs
    )
    assert all(
        proto.apply_python(pair["input"], opposite) != pair["output"]
        for pair in episode["train"]
    )
    assert any(
        proto.apply_python(pair["input"], opposite) != pair["output"]
        for pair in episode["test"]
    )


def test_default_setting_preserves_generator_contract_on_episode_inputs():
    proto = _load_prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    episode = proto.generate_episode(271828, boundary_mode="clip", root=ROOT)
    for pair in _all_pairs(episode):
        assert generator.self_check(pair["input"]) == []
        assert generator.observe_overrides(pair["input"])["bad_mask"] == 0
        assert generator.rule_mirror(pair["input"]) == pair["output"]


def test_public_challenge_masks_parameter_program_and_query_answers():
    proto = _load_prototype()
    episode = proto.generate_episode(42, boundary_mode="wrap", root=ROOT)
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    encoded = json.dumps(public, sort_keys=True)
    assert "boundary_mode" not in encoded
    assert "program" not in encoded
    assert "query_answers" not in encoded


def test_materialized_programs_execute_in_included_racket_runtime():
    proto = _load_prototype()
    builder_path = TASK_HOME / "workspace" / "parametric" / "build_evidence.py"
    assert builder_path.is_file(), "Racket evidence builder has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "parametric_evidence_56072bfdb820", builder_path
    )
    assert spec is not None and spec.loader is not None
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)

    episode = proto.generate_episode(161803, boundary_mode="clip", root=ROOT)
    grid = episode["train"][0]["input"]
    runtime_identity = None
    outputs = {}
    for mode in ("clip", "wrap"):
        actual, runtime = builder.execute_program(
            proto.racket_program(mode, root=ROOT), [grid]
        )
        runtime_identity = runtime_identity or runtime
        assert runtime == runtime_identity
        assert actual == [proto.apply_python(grid, mode)]
        outputs[mode] = actual[0]
    assert outputs["clip"] != outputs["wrap"]
