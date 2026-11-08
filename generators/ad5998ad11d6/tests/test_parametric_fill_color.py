"""Focused tests for the proposed episode-level fill-color prototype."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
TASK_ROOT = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_ROOT / "workspace" / "parametric" / "prototype.py"
CANONICAL_PATH = canonical_path(ROOT)


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "parametric prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "ad5998ad11d6_parametric_fill_color", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == "ad5998ad11d6":
                return row["program_solution"]
    raise AssertionError("canonical task row missing")


def test_default_program_is_byte_exact_canonical_and_alternative_is_narrow():
    module = _load_prototype()
    canonical = _canonical_program()
    assert module.render_program(canonical, 4) == canonical
    alternative = module.render_program(canonical, 2)
    assert alternative != canonical
    assert canonical.count("(fill-all-enclosed g 4)") == 1
    assert alternative.count("(fill-all-enclosed g 2)") == 1
    assert alternative.replace("(fill-all-enclosed g 2)", "(fill-all-enclosed g 4)") == canonical


@pytest.mark.parametrize("value", [True, False, 0, 1, 3, 5, 4.0, "4"])
def test_fill_color_validation_rejects_values_outside_declared_domain(value):
    module = _load_prototype()
    with pytest.raises((TypeError, ValueError)):
        module.render_program(_canonical_program(), value)


def test_fixture_inputs_are_distinct_lawful_family_members():
    module = _load_prototype()
    grids = module.fixture_inputs(73)
    assert len(grids) == 4
    assert len({json.dumps(grid, separators=(",", ":")) for grid in grids}) == 4
    generator = module.generator_module()
    for grid in grids:
        assert generator.self_check(grid) == []
        assert generator._analyze(grid)["enclosed_regions"] >= 1


def test_complete_episodes_use_one_setting_and_racket_distinguishes_the_rival():
    module = _load_prototype()
    with RacketBridge(max_calls_before_restart=64) as bridge:
        episodes = [
            module.generate_episode(73, fill_color=4, bridge=bridge),
            module.generate_episode(74, fill_color=2, bridge=bridge),
        ]
    for episode in episodes:
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        assert episode["rival"]["demo_differences"] == [0, 1, 2]
        assert episode["rival"]["query_differs"] is True
        selected = episode["parameters"]["fill_color"]
        assert selected in (4, 2)
        assert all(
            selected in {value for row in pair["output"] for value in row}
            for pair in episode["train"] + episode["test"]
        )


def test_public_challenge_masks_parameter_program_and_query_answer():
    module = _load_prototype()
    episode = {
        "parameters": {"fill_color": 2},
        "program": "secret",
        "train": [{"input": [[0]], "output": [[2]]}],
        "test": [{"input": [[0]], "output": [[2]]}],
    }
    public = module.public_challenge(episode)
    assert public == {
        "train": [{"input": [[0]], "output": [[2]]}],
        "test": [{"input": [[0]]}],
    }
    assert "parameters" not in public and "program" not in public
