from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


ROOT = find_root(__file__)
PROTOTYPE_PATH = ROOT / "generators/78645c33b002/workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("ring_thickness_prototype", PROTOTYPE_PATH)
assert SPEC and SPEC.loader
PROTOTYPE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTOTYPE)


def canonical_program():
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == PROTOTYPE.TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def test_parameter_is_bounded_and_default_program_is_exact_canonical_authority():
    assert PROTOTYPE.ALLOWED_RING_THICKNESSES == (1, 2)
    assert PROTOTYPE.DEFAULT_RING_THICKNESS == 1
    assert PROTOTYPE.program_for(1) == canonical_program()
    assert PROTOTYPE.program_for(2) != canonical_program()
    with pytest.raises(ValueError):
        PROTOTYPE.program_for(0)
    with pytest.raises(ValueError):
        PROTOTYPE.program_for(True)


def test_ring_thickness_changes_executed_output_not_input_sampling():
    grid = PROTOTYPE.build_inputs(seed=20261019, count=1)[0]
    thin = PROTOTYPE.apply_python(grid, 1)
    thick = PROTOTYPE.apply_python(grid, 2)
    layer_count = len(PROTOTYPE.GENERATOR._extract_layers(grid)["layers"])

    assert thin != thick
    assert len(thin) == 2 * layer_count - 1
    assert len(thick) == 4 * (layer_count - 1) + 1
    assert thin[len(thin) // 2][len(thin) // 2] == thick[len(thick) // 2][len(thick) // 2]


def test_episode_parameter_is_chosen_once_and_all_demos_distinguish_both_settings():
    for seed in (0, 1):
        episode = PROTOTYPE.build_episode(seed, n_train=3, n_test=1)
        chosen = episode["private"]["ring_thickness"]
        assert chosen in PROTOTYPE.ALLOWED_RING_THICKNESSES
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 1
        for pair in episode["train"] + episode["test"]:
            assert pair["output"] == PROTOTYPE.apply_python(pair["input"], chosen)
            assert PROTOTYPE.apply_python(pair["input"], 1) != PROTOTYPE.apply_python(pair["input"], 2)


def test_public_challenge_omits_parameter_program_and_query_answer():
    public = PROTOTYPE.public_challenge(PROTOTYPE.build_episode(0, n_train=3, n_test=1))
    blob = json.dumps(public, sort_keys=True)
    assert "ring_thickness" not in blob
    assert "program" not in blob
    assert all("output" in pair for pair in public["train"])
    assert all("output" not in pair for pair in public["test"])
