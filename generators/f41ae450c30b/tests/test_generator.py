from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK_ID = "f41ae450c30b"
GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
CANONICAL = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"

if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    name = "test_target_f41ae450c30b"
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, GENERATOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


def _canonical_pairs() -> list[dict]:
    with CANONICAL.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [*row["train"], *row["test"]]
    raise AssertionError(f"missing canonical row for {TASK_ID}")


def _profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def test_rule_hash_and_python_mirror_match_every_canonical_pair(gen):
    assert gen.RULE_HASH == "8601bafc35ff"
    for pair in _canonical_pairs():
        assert gen.self_check(copy.deepcopy(pair["input"])) == []
        assert gen.rule_mirror(copy.deepcopy(pair["input"])) == pair["output"]


def test_declared_axes_are_exact_observable_and_legal_in_every_band(gen):
    assert set(gen.AXES) == {"scene_profile", "n", "layout_axis"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []

    for band_index, band in enumerate(("easy", "medium", "hard")):
        case_index = 0
        for profile in gen.SCENE_PROFILES:
            for n in (3, 4):
                for layout_axis in gen.LAYOUT_AXES:
                    requested = {
                        "scene_profile": profile,
                        "n": n,
                        "layout_axis": layout_axis,
                    }
                    grid = gen.generate(
                        1000 + band_index,
                        case_index,
                        difficulty=band,
                        **requested,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == requested
                    case_index += 1


def test_unknown_invalid_and_wrong_typed_overrides_fail_loudly(gen):
    invalid_cases = (
        {"unknown_axis": 1},
        {"scene_profile": "not-a-profile"},
        {"scene_profile": 7},
        {"n": 2},
        {"n": 5},
        {"n": 3.0},
        {"n": True},
        {"layout_axis": "diagonal"},
        {"layout_axis": 1},
    )
    for overrides in invalid_cases:
        with pytest.raises(ValueError):
            gen.generate(7, 11, difficulty="hard", **overrides)


def test_every_default_draw_contains_real_third_object_occlusion(gen):
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for index in range(80):
            grid = gen.generate(2000 + band_index * 1000 + index, index, difficulty=band)
            assert gen.self_check(grid) == []
            assert gen.has_occluded_aligned_pair(grid)
            assert gen.rule_mirror(grid) != gen.SEMANTIC_RIVALS["alignment_ignores_blockers"](grid)


def test_semantic_contract_names_and_verifies_the_canonical_shortcut(gen):
    rival_name = "alignment_ignores_blockers"
    assert set(gen.SEMANTIC_WITNESSES) == {"third_component_occlusion"}
    assert gen.WITNESS_RIVALS == {"third_component_occlusion": [rival_name]}
    assert gen.CANONICAL_SHORTCUTS == {rival_name: gen.SEMANTIC_RIVALS[rival_name]}
    assert gen.LESSON_COMPETITORS == {rival_name: gen.SEMANTIC_RIVALS[rival_name]}

    rival = gen.SEMANTIC_RIVALS[rival_name]
    for pair in _canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    for index in range(12):
        grid = gen.generate(3000 + index, index)
        assert gen.SEMANTIC_WITNESSES["third_component_occlusion"](grid)
        assert rival(grid) != gen.rule_mirror(grid)


def test_default_distribution_has_canonical_profile_support_in_every_band(gen):
    canonical_profiles = {_profile(pair["input"]) for pair in _canonical_pairs()}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        observed = {
            _profile(gen.generate(4000 + band_index * 100 + index, index, difficulty=band))
            for index in range(40)
        }
        assert observed & canonical_profiles


def test_generation_is_deterministic_fresh_and_does_not_touch_global_random(gen):
    before = random.getstate()
    first = gen.generate(5150, 17, difficulty="medium")
    after = random.getstate()
    second = gen.generate(5150, 17, difficulty="medium")

    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 1
    assert second == gen.generate(5150, 17, difficulty="medium")


def test_generated_components_are_separated_dominoes_with_distinct_colors(gen):
    for index in range(60):
        grid = gen.generate(6000 + index, index, difficulty=("easy", "medium", "hard")[index % 3])
        components = gen.analyze_grid(grid)["components"]
        assert len(components) in (3, 4)
        assert len({component["color"] for component in components}) == len(components)
        assert all(len(component["cells"]) == 2 for component in components)


def test_strict_hook_accepts_canonical_and_generated_inputs(gen):
    for pair in _canonical_pairs():
        assert gen.strict_canonical_like(pair["input"]) == []
    for index in range(30):
        assert gen.strict_canonical_like(gen.generate(7000 + index, index)) == []
