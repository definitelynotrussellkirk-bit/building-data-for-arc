from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import find_root, load_selected_generator


TASK_ID = "997c17fd6870"
ROOT = find_root(__file__)
GENERATOR, _GENERATOR_PATH, _GENERATOR_SHA = load_selected_generator(TASK_ID, root=ROOT)
PROTOTYPE_PATH = Path(__file__).resolve().parents[1] / "workspace/parametric/prototype.py"
SPEC = importlib.util.spec_from_file_location("tile_width_prototype", PROTOTYPE_PATH)
assert SPEC is not None and SPEC.loader is not None
PROTOTYPE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROTOTYPE)


def _first_seed_for(value: int) -> int:
    for seed in range(10_000):
        if PROTOTYPE.choose_parameters(seed)[PROTOTYPE.PARAMETER_NAME] == value:
            return seed
    raise AssertionError(f"no seed found for tile_width={value}")


def test_parameter_contract_and_seed_choice_cover_both_settings():
    assert PROTOTYPE.PARAMETER_NAME == "tile_width"
    assert PROTOTYPE.DEFAULT_TILE_WIDTH == 2
    assert PROTOTYPE.ALLOWED_TILE_WIDTHS == (2, 3)
    assert {
        PROTOTYPE.choose_parameters(_first_seed_for(width))["tile_width"]
        for width in PROTOTYPE.ALLOWED_TILE_WIDTHS
    } == {2, 3}
    for seed in range(20):
        assert PROTOTYPE.choose_parameters(seed) == PROTOTYPE.choose_parameters(seed)
    with pytest.raises(TypeError, match="episode seed"):
        PROTOTYPE.choose_parameters(True)


def test_reference_reverses_tile_order_without_reversing_tile_contents():
    grid = [[1, 2, 3, 4, 5, 6], [7, 8, 9, 0, 1, 2]]
    assert PROTOTYPE.python_reference(grid, tile_width=2) == [
        [5, 6, 3, 4, 1, 2],
        [1, 2, 9, 0, 7, 8],
    ]
    assert PROTOTYPE.python_reference(grid, tile_width=3) == [
        [4, 5, 6, 1, 2, 3],
        [0, 1, 2, 7, 8, 9],
    ]
    with pytest.raises(ValueError, match="divisible"):
        PROTOTYPE.python_reference([[1, 2, 3, 4]], tile_width=3)
    with pytest.raises(ValueError, match="tile_width"):
        PROTOTYPE.python_reference(grid, tile_width=4)
    with pytest.raises(ValueError, match="tile_width"):
        PROTOTYPE.python_reference(grid, tile_width=True)


def test_episode_inputs_remain_in_family_and_distinguish_settings():
    seen = set()
    for episode_seed in range(4):
        for pair_index in range(4):
            grid = PROTOTYPE.build_input(episode_seed, pair_index)
            frozen = tuple(map(tuple, grid))
            seen.add(frozen)
            assert len(grid) == len(grid[0]) == 12
            assert GENERATOR.self_check(grid) == []
            default = PROTOTYPE.python_reference(grid, tile_width=2)
            alternative = PROTOTYPE.python_reference(grid, tile_width=3)
            assert default == GENERATOR.rule_mirror(grid)
            assert default != alternative
    assert len(seen) == 16


def test_racket_materialization_is_setting_specific_and_public_redaction_is_complete():
    programs = {
        width: PROTOTYPE.racket_program({"tile_width": width})
        for width in PROTOTYPE.ALLOWED_TILE_WIDTHS
    }
    assert programs[2] != programs[3]
    assert "remainder c 2" in programs[2]
    assert "remainder c 3" in programs[3]

    episode = {
        "demos": [
            {"input": [[1, 2, 3, 4, 5, 6]], "output": [[5, 6, 3, 4, 1, 2]]}
            for _ in range(3)
        ],
        "query": {
            "input": [[7, 8, 9, 0, 1, 2]],
            "output": [[1, 2, 9, 0, 7, 8]],
        },
    }
    challenge = PROTOTYPE.public_challenge(episode)
    assert challenge["demos"] == episode["demos"]
    assert challenge["query"] == {"input": episode["query"]["input"]}
    assert "output" not in challenge["query"]
    challenge["demos"][0]["input"][0][0] = 9
    assert episode["demos"][0]["input"][0][0] == 1
    serialized = repr(challenge)
    assert "tile_width" not in serialized
    assert "racket" not in serialized.lower()
