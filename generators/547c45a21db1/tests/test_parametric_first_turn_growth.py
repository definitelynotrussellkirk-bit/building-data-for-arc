from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root


TASK_ID = "547c45a21db1"
TASK_DIR = Path(__file__).resolve().parents[1]
PARAM_DIR = TASK_DIR / "workspace" / "parametric"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    ledger = canonical_path(find_root(__file__))
    matches = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("content_hash") == TASK_ID:
            matches.append(row["program_solution"])
    assert len(matches) == 1
    return matches[0]


def test_native_contract_preserves_exact_canonical_default():
    adapter_path = PARAM_DIR / "adapter.py"
    promotion_path = PARAM_DIR / "promotion.json"
    assert adapter_path.is_file(), "native adapter has not been built"
    assert promotion_path.is_file(), "promotion contract has not been built"

    promotion = json.loads(promotion_path.read_text(encoding="utf-8"))
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/547c45a21db1/workspace/parametric/adapter.py",
        "parameters": {
            "coloring_mode": ["nearest_seed", "first_turn_growth"]
        },
        "default": {"coloring_mode": "nearest_seed"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            "generators/547c45a21db1/workspace/parametric/rules/first_turn_growth.rkt",
            "generators/547c45a21db1/workspace/parametric/rules/fixed_radius_one.rkt",
        ],
    }

    adapter = _load(adapter_path, "_test_547c45a21db1_adapter")
    assert adapter.program({"coloring_mode": "nearest_seed"}) == _canonical_program()


def test_native_contract_rejects_unknown_settings_and_out_of_range_counts():
    adapter_path = PARAM_DIR / "adapter.py"
    assert adapter_path.is_file(), "native adapter has not been built"
    adapter = _load(adapter_path, "_test_547c45a21db1_adapter_validation")

    import pytest

    for bad in (
        None,
        {},
        {"coloring_mode": "nearest_seed", "extra": 1},
        {"coloring_mode": "unknown"},
        {"coloring_mode": 1},
    ):
        with pytest.raises(ValueError):
            adapter.program(bad)

    valid = {"coloring_mode": "nearest_seed"}
    for demos in (1, 7, True, 3.0):
        with pytest.raises(ValueError):
            adapter.generate(0, valid, demos, 4)
    for queries in (0, 5, True, 4.0):
        with pytest.raises(ValueError):
            adapter.generate(0, valid, 3, queries)


def _adapter(name: str = "_test_547c45a21db1_adapter_runtime"):
    return _load(PARAM_DIR / "adapter.py", name)


def _prototype(name: str = "_test_547c45a21db1_prototype_runtime"):
    return _load(PARAM_DIR / "prototype.py", name)


def _episode_inputs(episode):
    return [pair["input"] for pair in episode["train"]], [
        pair["input"] for pair in episode["test"]
    ]


def test_sampler_uses_matched_distinct_prefix_stable_inputs_across_settings():
    adapter = _adapter("_test_547c45a21db1_adapter_sampler")
    nearest = adapter.generate(
        17, {"coloring_mode": "nearest_seed"}, demos=6, queries=4
    )
    growth = adapter.generate(
        17, {"coloring_mode": "first_turn_growth"}, demos=6, queries=4
    )
    nearest_inputs = _episode_inputs(nearest)
    growth_inputs = _episode_inputs(growth)
    assert nearest_inputs == growth_inputs

    short = adapter.generate(
        17, {"coloring_mode": "nearest_seed"}, demos=2, queries=1
    )
    short_train, short_test = _episode_inputs(short)
    full_train, full_test = nearest_inputs
    assert short_train == full_train[:2]
    assert short_test == full_test[:1]

    fingerprints = {
        json.dumps(grid, separators=(",", ":"))
        for grid in [*full_train, *full_test]
    }
    assert len(fingerprints) == 10
    for grid in [*full_train, *full_test]:
        assert 1 <= len(grid) <= 30
        assert 1 <= len(grid[0]) <= 30
        assert all(len(row) == len(grid[0]) for row in grid)
        assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


def test_first_turn_growth_matches_hand_checked_l_path():
    prototype = _prototype("_test_547c45a21db1_prototype_hand")
    grid = [
        [2, 1, 1, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 1, 1, 3],
    ]
    assert prototype.first_turn_intermediate(grid) == {
        "radius": 2,
        "first_turn_cell": [0, 2],
        "incoming": [0, 1],
        "outgoing": [1, 0],
        "turn_found": True,
        "path_length": 7,
    }
    assert prototype.apply_python(grid, "first_turn_growth") == [
        [2, 2, 2, 0, 0],
        [0, 0, 1, 0, 0],
        [0, 0, 3, 3, 3],
    ]
    assert prototype.apply_python(grid, "nearest_seed") == [
        [2, 2, 2, 0, 0],
        [0, 0, 4, 0, 0],
        [0, 0, 3, 3, 3],
    ]


def test_first_turn_depth_varies_and_wrong_intermediate_changes_the_result():
    prototype = _prototype("_test_547c45a21db1_prototype_depth")
    radii = []
    for index in range(6):
        grid = prototype.make_input(0, split="demo", index=index)
        intermediate = prototype.first_turn_intermediate(grid)
        radii.append(intermediate["radius"])
        assert intermediate["turn_found"] is True
        assert prototype.apply_python(grid, "first_turn_growth") != prototype.apply_python(
            grid, "first_turn_growth", radius_override=1
        )
    assert radii == [2, 3, 4, 5, 3, 6]


def test_large_query_is_substantive_30_by_30_and_boundary_touching():
    prototype = _prototype("_test_547c45a21db1_prototype_large")
    grid = prototype.make_input(17, split="query", index=3)
    path = prototype.path_order(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert len(path) == 121
    rows = {row for row, _ in path}
    cols = {col for _, col in path}
    assert len(rows) >= 9
    assert len(cols) >= 20
    assert any(row in (0, 29) or col in (0, 29) for row, col in path)
    assert prototype.apply_python(grid, "first_turn_growth") != prototype.apply_python(
        grid, "first_turn_growth", radius_override=1
    )


def test_two_demos_refute_the_declared_finite_rivals_for_both_settings():
    prototype = _prototype("_test_547c45a21db1_prototype_rivals")
    audit = prototype.bounded_rival_audit(seed=0, demos=2)
    assert audit["scope"] == {
        "seeds": [0],
        "demonstrations_per_setting": 2,
        "settings": ["nearest_seed", "first_turn_growth"],
    }
    assert audit["all_refuted"] is True
    assert audit["survivors"] == {
        "nearest_seed": [],
        "first_turn_growth": [],
    }
    assert set(audit["rivals"]) == {
        "other_setting",
        "fixed_radius_1",
        "fixed_radius_2",
        "first_turn_minus_one",
        "first_turn_plus_one",
        "last_turn_radius",
    }


def test_public_projection_omits_private_fields_and_has_private_field_independent_id():
    prototype = _prototype("_test_547c45a21db1_prototype_public")
    episode = prototype.generate_episode(
        17, coloring_mode="first_turn_growth", demos=3, queries=4
    )
    public = prototype.public_projection(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    original_id = prototype.public_id(episode)
    changed = dict(episode)
    changed["program_solution"] = "private bytes changed"
    changed["settings"] = {"private": "changed"}
    assert prototype.public_id(changed) == original_id


def test_straight_path_has_explicit_total_fallback_and_malformed_paths_fail():
    prototype = _prototype("_test_547c45a21db1_prototype_edges")
    straight = [[2, 1, 1, 1, 3]]
    assert prototype.first_turn_intermediate(straight) == {
        "radius": 4,
        "first_turn_cell": [0, 4],
        "incoming": [0, 1],
        "outgoing": [0, 0],
        "turn_found": False,
        "path_length": 5,
    }
    assert prototype.apply_python(straight, "first_turn_growth") == [[2, 4, 4, 4, 3]]

    import pytest

    with pytest.raises(ValueError):
        prototype.path_order([[2, 1, 3], [0, 1, 0]])


def _racket_apply(bridge, program: str, grid: list[list[int]]):
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def test_protected_racket_programs_match_python_for_both_settings_and_stress():
    from arc_repl.racket_bridge import RacketBridge

    prototype = _prototype("_test_547c45a21db1_prototype_racket")
    first_turn_path = PARAM_DIR / "rules" / "first_turn_growth.rkt"
    wrong_radius_path = PARAM_DIR / "rules" / "fixed_radius_one.rkt"
    assert first_turn_path.is_file(), "first-turn Racket program has not been built"
    assert wrong_radius_path.is_file(), "wrong-intermediate Racket program has not been built"

    first_turn_program = first_turn_path.read_text(encoding="utf-8")
    wrong_radius_program = wrong_radius_path.read_text(encoding="utf-8")
    grids = [
        prototype.make_input(0, split="demo", index=0),
        prototype.make_input(17, split="demo", index=1),
        prototype.make_input(17, split="query", index=3),
    ]

    with RacketBridge(timeout=30.0) as bridge:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket"
        assert identity["protected"] is True
        for mode in prototype.COLORING_MODES:
            program = prototype.program_for(mode)
            for grid in grids:
                assert _racket_apply(bridge, program, grid) == prototype.apply_python(
                    grid, mode
                )
        for grid in grids:
            assert _racket_apply(bridge, wrong_radius_program, grid) == prototype.apply_python(
                grid, "first_turn_growth", radius_override=1
            )
        assert _racket_apply(bridge, first_turn_program, grids[0]) != _racket_apply(
            bridge, wrong_radius_program, grids[0]
        )
