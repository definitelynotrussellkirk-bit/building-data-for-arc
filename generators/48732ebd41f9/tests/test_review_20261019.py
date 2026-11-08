"""Regressions for the 2026-10-19 review repair and parametric prototype."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge


TASK_ID = "48732ebd41f9"
TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_ROOT / "workspace" / "parametric" / "prototype.py"


def _load_module(name: str, path: Path):
    assert path.is_file(), f"missing module: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _generator():
    selected = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(selected) if selected else TASK_ROOT / "generator.py"
    return _load_module(f"generator_{TASK_ID}_review", path)


def _prototype():
    return _load_module(f"generator_{TASK_ID}_parametric", PROTOTYPE_PATH)


@pytest.mark.parametrize("bad_seed", [True, False, 1.0, 1.75, "1", None])
def test_generate_rejects_non_integer_seed(bad_seed: object) -> None:
    gen = _generator()
    with pytest.raises(TypeError, match="seed"):
        gen.generate(bad_seed, 0, difficulty="easy")


@pytest.mark.parametrize("bad_index", [True, False, 1.0, 1.75, "1", None, -1])
def test_generate_and_schedule_reject_invalid_sample_index(bad_index: object) -> None:
    gen = _generator()
    error = ValueError if type(bad_index) is int else TypeError
    with pytest.raises(error, match="sample_index"):
        gen.generate(991, bad_index, difficulty="hard")
    with pytest.raises(error, match="sample_index"):
        gen.schedule_profile(991, bad_index, difficulty="hard")


def test_valid_replay_identity_remains_deterministic() -> None:
    gen = _generator()
    first = gen.generate(991, 0, difficulty="medium")
    second = gen.generate(991, 0, difficulty="medium")
    assert first == second
    assert gen.self_check(first) == []


def test_minimum_height_parameter_preserves_canonical_default_and_changes_rule() -> None:
    proto = _prototype()
    assert proto.ALLOWED_MIN_HEIGHTS == (2, 3)
    assert proto.DEFAULT_MIN_HEIGHT == 2
    canonical = proto.program_for(2)
    alternative = proto.program_for(3)
    assert "(tallest-rect g 0 2)" in canonical
    assert "(tallest-rect g 0 3)" in alternative
    assert canonical != alternative


def test_complete_episodes_use_one_setting_and_refute_the_other_threshold() -> None:
    proto = _prototype()
    for minimum_height in proto.ALLOWED_MIN_HEIGHTS:
        episode = proto.build_episode(6200 + minimum_height, minimum_height=minimum_height)
        assert episode["meta"]["minimum_height"] == minimum_height
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert proto.parameter_rival_findings(episode) == []
        rival = next(
            value for value in proto.ALLOWED_MIN_HEIGHTS if value != minimum_height
        )
        assert all(
            proto.apply_python(pair["input"], rival) != pair["output"]
            for pair in episode["train"]
        )


def test_exact_racket_programs_match_python_and_diverge() -> None:
    proto = _prototype()
    grid = proto.make_input(6200, 0)
    outputs = {}
    with RacketBridge(max_calls_before_restart=32) as bridge:
        for minimum_height in proto.ALLOWED_MIN_HEIGHTS:
            program = proto.program_for(minimum_height)
            outputs[minimum_height] = proto.apply_racket(bridge, program, grid)
            assert outputs[minimum_height] == proto.apply_python(
                grid, minimum_height
            )
    assert outputs[2] != outputs[3]


def test_materialized_public_challenges_hide_parameter_program_and_query_answer(
    tmp_path: Path,
) -> None:
    proto = _prototype()
    evidence_path = tmp_path / "evidence.json"
    public_dir = tmp_path / "public"
    report = proto.materialize(
        evidence_path,
        public_dir=public_dir,
        seed_start=6200,
    )
    assert report["status"] == "prototype"
    assert {row["minimum_height"] for row in report["episodes"]} == {2, 3}
    for row in report["episodes"]:
        public = json.loads((public_dir / row["public_filename"]).read_text())
        assert "meta" not in public
        assert "program" not in public
        assert all("output" not in pair for pair in public["test"])
        assert len(public["train"]) == 3
