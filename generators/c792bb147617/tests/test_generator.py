from __future__ import annotations

import copy
import importlib.util
import os
import sys
from pathlib import Path

import pytest

TASK_ID = "c792bb147617"
EXPECTED_RULE_HASH = "98769b9435a0"
TASK_DIR = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if RUNTIME.is_dir() and str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root  # noqa: E402


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", TASK_DIR / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"test_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def _blue_positions(grid: list[list[int]]) -> list[tuple[int, int]]:
    return [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == 1
    ]


def _has_boundary_blue(grid: list[list[int]]) -> bool:
    height, width = len(grid), len(grid[0])
    return any(
        row in (0, height - 1) or col in (0, width - 1)
        for row, col in _blue_positions(grid)
    )


def test_public_contract_is_small_exact_and_rule_bound() -> None:
    gen = _load_generator()
    assert gen.RULE_HASH == EXPECTED_RULE_HASH
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_blues", "edge_mode"}
    assert gen.AXES["edge_mode"]["valid"] == "none|some"
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()
    assert callable(gen.observe_overrides)
    assert callable(gen.rule_mirror)
    assert set(gen.CANONICAL_SHORTCUTS) == {"first_seven_blues"}


def test_all_labeled_canonical_pairs_are_lawful_and_match_python_mirror() -> None:
    gen = _load_generator()
    pairs = _pairs()
    assert pairs
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 6, "grid_w": 16, "n_blues": 2, "edge_mode": "none"},
        {"grid_h": 16, "grid_w": 6, "n_blues": 8, "edge_mode": "some"},
        {"grid_h": 10, "grid_w": 10, "n_blues": 7, "edge_mode": "some"},
    ],
)
def test_every_advertised_override_is_exact_and_observable(band, options) -> None:
    gen = _load_generator()
    grid = gen.generate(17, 11, difficulty=band, **options)
    assert gen.self_check(grid, difficulty=band) == []
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"typo": 1}, ValueError),
        ({"grid_h": True}, TypeError),
        ({"grid_w": 5}, ValueError),
        ({"n_blues": 9}, ValueError),
        ({"edge_mode": "corners_only"}, ValueError),
    ],
)
def test_invalid_overrides_fail_loudly(kwargs, error) -> None:
    gen = _load_generator()
    with pytest.raises(error):
        gen.generate(0, 0, **kwargs)


def test_invalid_call_scalars_and_difficulty_fail_loudly() -> None:
    gen = _load_generator()
    with pytest.raises(TypeError):
        gen.generate(0, True)
    with pytest.raises(ValueError):
        gen.generate(0, -1)
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty="nightmare")


def test_default_stream_recurrently_covers_canonical_profile_boundary_and_eight() -> None:
    gen = _load_generator()
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(300 + index, index, difficulty=band) for index in range(20)]
        assert any(
            len(grid) == 10
            and len(grid[0]) == 10
            and 5 <= len(_blue_positions(grid)) <= 7
            for grid in grids
        )
        assert any(_has_boundary_blue(grid) for grid in grids)
        assert any(len(_blue_positions(grid)) == 8 for grid in grids)
        assert all(gen.self_check(grid, difficulty=band) == [] for grid in grids)


def test_canonical_shortcut_fits_authority_and_generated_witness_refutes_it() -> None:
    gen = _load_generator()
    rival = gen.CANONICAL_SHORTCUTS["first_seven_blues"]
    assert all(rival(pair["input"]) == pair["output"] for pair in _pairs())

    witness = gen.generate(
        44,
        4,
        grid_h=10,
        grid_w=10,
        n_blues=8,
        edge_mode="some",
    )
    assert gen.SEMANTIC_WITNESSES["eight_blues"](witness)
    assert rival(witness) != gen.rule_mirror(witness)


def test_boundary_witness_refutes_the_skip_boundary_rival() -> None:
    gen = _load_generator()
    witness = gen.generate(
        81,
        0,
        grid_h=10,
        grid_w=10,
        n_blues=5,
        edge_mode="some",
    )
    assert gen.SEMANTIC_WITNESSES["boundary_blue"](witness)
    rival = gen.SEMANTIC_RIVALS["skip_boundary_blues"]
    assert rival(witness) != gen.rule_mirror(witness)


def test_generation_and_semantic_helpers_are_deterministic_and_input_pure() -> None:
    gen = _load_generator()
    grid = gen.generate(912, 17, difficulty="hard")
    assert grid == gen.generate(912, 17, difficulty="hard")
    original = copy.deepcopy(grid)
    assert gen.self_check(grid) == []
    gen.observe_overrides(grid)
    gen.rule_mirror(grid)
    for rival in gen.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == original


def test_cardinally_adjacent_anchor_impostors_are_outside_generator_grammar() -> None:
    gen = _load_generator()
    short_line = [[0 for _ in range(6)] for _ in range(6)]
    short_line[2][1] = 1
    short_line[2][2] = 1
    short_line[2][3] = 1
    errors = gen.self_check(short_line)
    assert any("cardinally adjacent" in error for error in errors)


def test_every_cyclic_schedule_start_and_query_rotation_is_identifiable() -> None:
    gen = _load_generator()
    for band in ("easy", "medium", "hard"):
        for start in range(len(gen.SCHEDULE_PROFILES)):
            pairs = []
            for offset in range(4):
                grid = gen.generate(700 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == []


def test_retained_first_seven_counterexample_replays_exactly() -> None:
    import json

    gen = _load_generator()
    path = TASK_DIR / "counterexamples" / "first-seven-blue-limit.json"
    record = json.loads(path.read_text())
    grid = record["input"]
    assert record["rule_hash"] == gen.RULE_HASH
    assert gen.self_check(grid) == []
    assert gen.rule_mirror(grid) == record["intended_output"]
    assert gen.CANONICAL_SHORTCUTS["first_seven_blues"](grid) == record["rival_output"]
    assert record["intended_output"] != record["rival_output"]
    assert record["differing_cells"]
