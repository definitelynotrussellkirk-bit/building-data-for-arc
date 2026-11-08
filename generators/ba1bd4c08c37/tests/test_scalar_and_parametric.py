"""Focused regressions for strict scalars and the isolated corner prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_path, find_root  # noqa: E402


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


GEN = _load_module(
    "generator_ba1bd4c08c37_strict_tests", HERE.parents[1] / "generator.py"
)
PARAMETRIC_PATH = HERE.parents[1] / "workspace" / "parametric" / "prototype.py"
INVALID_PUBLIC_INTS = (True, False, 1.0, 1.75, "1", None, -1)


def _load_prototype():
    assert PARAMETRIC_PATH.is_file(), "output-corner prototype has not been implemented"
    return _load_module("parametric_ba1bd4c08c37", PARAMETRIC_PATH)


def _canonical_program() -> str:
    root = find_root(HERE)
    programs = {
        row["program_solution"]
        for row in map(json.loads, canonical_path(root).open(encoding="utf-8"))
        if row.get("task_id") == GEN.TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


@pytest.mark.parametrize("bad_seed", INVALID_PUBLIC_INTS)
def test_generate_rejects_non_exact_or_negative_seed(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(bad_seed, 0)


@pytest.mark.parametrize("bad_index", INVALID_PUBLIC_INTS)
def test_generate_rejects_non_exact_or_negative_sample_index(bad_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(0, bad_index)


@pytest.mark.parametrize("bad_seed", INVALID_PUBLIC_INTS)
def test_schedule_profile_rejects_non_exact_or_negative_seed(bad_seed):
    with pytest.raises((TypeError, ValueError)):
        GEN.schedule_profile(bad_seed, 0, "easy")


@pytest.mark.parametrize("bad_index", INVALID_PUBLIC_INTS)
def test_schedule_profile_rejects_non_exact_or_negative_sample_index(bad_index):
    with pytest.raises((TypeError, ValueError)):
        GEN.schedule_profile(0, bad_index, "easy")


def test_valid_zero_public_indices_remain_supported():
    assert GEN.self_check(GEN.generate(0, 0)) == []
    assert GEN.schedule_profile(0, 0) == GEN.SCHEDULE_PROFILES[0]


def test_parametric_contract_keeps_top_left_byte_exact_canonical():
    prototype = _load_prototype()
    assert prototype.PARAMETER_NAME == "output_corner"
    assert prototype.PARAMETER_VALUES == (
        "top_left",
        "top_right",
        "bottom_left",
        "bottom_right",
    )
    assert prototype.DEFAULT_PARAMETER == "top_left"
    assert prototype.racket_program({"output_corner": "top_left"}) == _canonical_program()


def test_parametric_input_separates_all_four_corner_settings():
    prototype = _load_prototype()
    grid = prototype.build_input(17, 0)
    outputs = {
        corner: prototype.python_reference(deepcopy(grid), output_corner=corner)
        for corner in prototype.PARAMETER_VALUES
    }
    assert len({json.dumps(value, separators=(",", ":")) for value in outputs.values()}) == 4
    assert outputs["top_left"] == GEN._correct_crop(grid)


def test_parametric_episode_uses_one_setting_and_public_projection_is_redacted():
    prototype = _load_prototype()
    episode = prototype.generate_episode(9, output_corner="bottom_right")
    assert episode["parameters"] == {"output_corner": "bottom_right"}
    assert len(episode["train"]) == 5
    assert len(episode["test"]) == 1
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == prototype.python_reference(
            pair["input"], output_corner="bottom_right"
        )

    public = prototype.public_challenge(episode)
    encoded = json.dumps(public, sort_keys=True)
    assert "bottom_right" not in encoded
    assert "program" not in public
    assert "parameters" not in public
    assert "seed" not in public
    assert "output" not in public["test"][0]


def test_materialized_racket_programs_match_python_on_one_input():
    prototype = _load_prototype()
    from arc_repl.racket_bridge import RacketBridge
    grid = prototype.build_input(23, 1)
    literal = prototype.grid_literal(grid)
    with RacketBridge(timeout=20, max_calls_before_restart=48) as bridge:
        for corner in prototype.PARAMETER_VALUES:
            source = prototype.racket_program({"output_corner": corner})
            actual = bridge.eval_text(f"({prototype.racket_callable(source)} {literal})")
            expected = prototype.python_reference(grid, output_corner=corner)
            assert actual == expected
