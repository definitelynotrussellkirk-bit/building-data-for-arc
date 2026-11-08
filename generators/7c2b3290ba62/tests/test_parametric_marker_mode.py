"""Native parametric regression suite for 7c2b3290ba62 marker roles."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

TASK = "7c2b3290ba62"
HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"
ROOT = next(path for path in Path(__file__).resolve().parents if (path / "shared/runtime").is_dir())
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "shared/runtime")]


def _load(name: str):
    path = PARAM / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"test_{TASK}_{name}", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    from arcpuzzles import Catalog

    record = Catalog(ROOT).get(TASK)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return programs.pop()


def test_parametric_source_exists_before_behavior_checks():
    assert (PARAM / "prototype.py").is_file()
    assert (PARAM / "adapter.py").is_file()
    assert (PARAM / "promotion.json").is_file()


def test_canonical_program_is_byte_exact_and_contract_is_bounded():
    prototype = _load("prototype")
    assert prototype.program({"marker_mode": "pair_cyan"}) == _canonical_program()
    contract = json.loads((PARAM / "promotion.json").read_text())
    assert contract["parameters"] == {"marker_mode": ["pair_cyan", "size_roles"]}
    assert contract["default"] == {"marker_mode": "pair_cyan"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [4, 4]}


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("seed", [0, 17])
def test_generation_is_deterministic_matched_distinct_and_lawful(seed: int, demos: int):
    prototype = _load("prototype")
    canonical = prototype.generate(seed, {"marker_mode": "pair_cyan"}, demos, 4)
    alternate = prototype.generate(seed, {"marker_mode": "size_roles"}, demos, 4)
    assert canonical == prototype.generate(seed, {"marker_mode": "pair_cyan"}, demos, 4)
    assert canonical["settings"] == {"marker_mode": "pair_cyan"}
    assert alternate["settings"] == {"marker_mode": "size_roles"}
    assert [p["input"] for p in canonical["train"] + canonical["test"]] == [
        p["input"] for p in alternate["train"] + alternate["test"]
    ]
    frozen = {
        tuple(tuple(row) for row in pair["input"])
        for pair in canonical["train"] + canonical["test"]
    }
    assert len(frozen) == demos + 4
    for split in ("train", "test"):
        for pair_c, pair_a in zip(canonical[split], alternate[split], strict=True):
            grid = pair_c["input"]
            assert 1 <= len(grid) <= 30 and 1 <= len(grid[0]) <= 30
            assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
            assert 8 not in {value for row in grid for value in row}
            facts = prototype.analyze(grid)
            assert len(facts["good_pairs"]) == 1
            left, right = facts["good_pairs"][0]
            assert facts["candidate_sizes"][left] != facts["candidate_sizes"][right]
            assert pair_c["output"] == prototype.solve_python(grid, "pair_cyan")
            assert pair_a["output"] == prototype.solve_python(grid, "size_roles")
            assert pair_c["output"] != pair_a["output"]


def test_minimum_lesson_exercises_both_role_orientations_and_breaks_global_size_shortcut():
    prototype = _load("prototype")
    episode = prototype.generate(0, {"marker_mode": "size_roles"}, 2, 4)
    left_is_larger = []
    global_top_two_disagrees = []
    for pair in episode["train"]:
        facts = prototype.analyze(pair["input"])
        left, right = facts["good_pairs"][0]
        sizes = facts["candidate_sizes"]
        left_is_larger.append(sizes[left] > sizes[right])
        global_top_two_disagrees.append(set(sorted(range(len(sizes)), key=lambda i: (-sizes[i], i))[:2]) != {left, right})
    assert set(left_is_larger) == {False, True}
    assert any(global_top_two_disagrees)


def test_alternate_output_assigns_roles_only_inside_the_semantic_pair():
    prototype = _load("prototype")
    episode = prototype.generate(17, {"marker_mode": "size_roles"}, 3, 4)
    for pair in episode["train"] + episode["test"]:
        facts = prototype.analyze(pair["input"])
        left, right = facts["good_pairs"][0]
        sizes = facts["candidate_sizes"]
        output = pair["output"][0]
        assert {index for index, value in enumerate(output) if value != 0} == {left, right}
        larger, smaller = (left, right) if sizes[left] > sizes[right] else (right, left)
        assert output[larger] == 8
        assert output[smaller] == 2


def test_query_profiles_include_substantive_boundary_spread_at_height_30():
    prototype = _load("prototype")
    episode = prototype.generate(31, {"marker_mode": "size_roles"}, 2, 4)
    large = next(pair["input"] for pair in episode["test"] if len(pair["input"]) == 30)
    assert len(large[0]) == 29  # exact 30-wide equal-panel geometry is impossible
    facts = prototype.analyze(large)
    target = facts["target"]
    assert len(target) >= 30
    assert {row for row, _ in target} >= {0, 29}
    assert {col for _, col in target} >= {0, facts["panel_w"] - 1}
    nonzero = sum(value not in (0, 9) for row in large for value in row)
    assert nonzero >= 100


def test_public_turn_masks_answers_settings_program_and_future_queries():
    prototype = _load("prototype")
    episode = prototype.generate(5, {"marker_mode": "size_roles"}, 3, 4)
    frozen = deepcopy(episode)
    turn = prototype.public_turn(episode, 2)
    assert episode == frozen
    assert set(turn) == {"train", "test"}
    assert len(turn["train"]) == 3 and len(turn["test"]) == 1
    assert turn["test"][0] == {"input": episode["test"][2]["input"]}
    assert all(set(pair) == {"input", "output"} for pair in turn["train"])
    assert "settings" not in turn and "program_solution" not in turn and "seed" not in turn


@pytest.mark.parametrize(
    "settings,demos,queries,error",
    [
        ({}, 2, 4, ValueError),
        ({"marker_mode": "pair_cyan", "extra": 1}, 2, 4, ValueError),
        ({"marker_mode": "unknown"}, 2, 4, ValueError),
        ({"marker_mode": "pair_cyan"}, 1, 4, ValueError),
        ({"marker_mode": "pair_cyan"}, 7, 4, ValueError),
        ({"marker_mode": "pair_cyan"}, 2, 3, ValueError),
        ({"marker_mode": "pair_cyan"}, True, 4, ValueError),
    ],
)
def test_invalid_requests_fail_closed(settings, demos, queries, error):
    prototype = _load("prototype")
    with pytest.raises(error):
        prototype.generate(0, settings, demos, queries)


def test_two_demo_teaching_rejects_every_named_shortcut():
    audit = _load("audit")
    for seed in (0, 17):
        for mode in ("pair_cyan", "size_roles"):
            report = audit.teaching_audit(seed, mode, 2)
            assert report["query_answers_used"] is False
            assert report["survivors"] == []
            assert all(indices for indices in report["rejected_by_demo"].values())
