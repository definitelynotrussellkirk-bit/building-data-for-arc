from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest


TASK_ID = "241567a35764"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"


def _load_adapter():
    spec = importlib.util.spec_from_file_location(f"parametric_{TASK_ID}", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load_adapter()


def _canonical_source():
    from arcpuzzles.catalog import Catalog

    catalog = Catalog(Path("."))
    row = catalog.describe(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in catalog._variants()[row.get("rule_task_id", TASK_ID)]
    }
    assert len(programs) == 1
    return next(iter(programs))


def _key(grid):
    return tuple(tuple(row) for row in grid)


def _all_inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _racket_apply(bridge, program, grid):
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def test_contract_and_default_preserve_exact_catalog_canonical_bytes(adapter):
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"path_mode": ["forward", "bidirectional"]},
        "default": {"path_mode": "forward"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/bidirectional.rkt",
        ],
    }
    assert adapter.program({"path_mode": "forward"}) == _canonical_source()
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == _canonical_source()
    assert adapter.program({"path_mode": "bidirectional"}) == (
        PARAMETRIC / "bidirectional.rkt"
    ).read_text(encoding="utf-8")


def test_settings_and_counts_are_strictly_validated(adapter):
    bad_settings = [None, [], "forward", {}, {"path_mode": "other"},
                    {"path_mode": 1}, {"path_mode": True},
                    {"path_mode": "forward", "extra": 1}]
    for settings in bad_settings:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, 2, 1)
    valid = {"seed": 0, "settings": {"path_mode": "forward"}, "demos": 2, "queries": 1}
    for name, values in {
        "seed": [-1, 2**63, True, 1.5, "0"],
        "demos": [1, 7, False, 2.0, "2"],
        "queries": [0, 5, True, 1.0, "1"],
    }.items():
        for value in values:
            with pytest.raises((TypeError, ValueError)):
                adapter.generate(**{**valid, name: value})


def test_generated_episodes_are_correct_distinct_and_prefix_stable(adapter):
    for mode in adapter.PATH_MODES:
        settings = {"path_mode": mode}
        full = adapter.generate(17, settings, demos=6, queries=4)
        assert len(full["train"]) == 6 and len(full["test"]) == 4
        assert full["program_solution"] == adapter.program(settings)
        keys = [_key(grid) for grid in _all_inputs(full)]
        assert len(keys) == len(set(keys))
        for split in ("train", "test"):
            for pair in full[split]:
                assert pair["output"] == adapter.solve(pair["input"], mode)
                assert adapter.forward_stamp_count(pair["input"]) >= 2
                assert adapter.backward_stamp_count(pair["input"]) >= 1
        for demos in (2, 3, 5):
            shorter = adapter.generate(17, settings, demos=demos, queries=4)
            assert shorter["train"] == full["train"][:demos]
            assert shorter["test"] == full["test"]
        for queries in (1, 2, 3):
            shorter = adapter.generate(17, settings, demos=6, queries=queries)
            assert shorter["train"] == full["train"]
            assert shorter["test"] == full["test"][:queries]


def test_settings_receive_identical_inputs_and_two_demos_identify_direction(adapter):
    forward = adapter.generate(9, {"path_mode": "forward"}, demos=2, queries=4)
    both = adapter.generate(9, {"path_mode": "bidirectional"}, demos=2, queries=4)
    assert _all_inputs(forward) == _all_inputs(both)
    assert all(left["output"] != right["output"]
               for left, right in zip(forward["train"], both["train"]))


def test_two_demos_refute_untransformed_stamp_once_and_wrong_direction_rivals(adapter):
    for mode in adapter.PATH_MODES:
        episode = adapter.generate(23, {"path_mode": mode}, demos=2, queries=4)
        rivals = {name: [] for name in ("untransformed", "stamp_once", "opposite_direction")}
        for pair in episode["train"]:
            grid = pair["input"]
            rivals["untransformed"].append(adapter.solve_with_shape(grid, mode, adapter.raw_template(grid)))
            rivals["stamp_once"].append(adapter.stamp_once(grid, adapter.transformed_template(grid)))
            other = "bidirectional" if mode == "forward" else "forward"
            rivals["opposite_direction"].append(adapter.solve(grid, other))
        for name, predictions in rivals.items():
            assert any(prediction != pair["output"]
                       for prediction, pair in zip(predictions, episode["train"])), (mode, name)


def test_queries_include_substantive_30x30_path_stress(adapter):
    for mode in adapter.PATH_MODES:
        episode = adapter.generate(5, {"path_mode": mode}, demos=2, queries=4)
        shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
        assert shapes == list(adapter.QUERY_SHAPES)
        pair = episode["test"][3]
        assert (len(pair["output"]), len(pair["output"][0])) == (30, 30)
        cells = [(r, c) for r, row in enumerate(pair["output"])
                 for c, value in enumerate(row) if value == 9]
        assert len(cells) >= 24
        assert max(r for r, _ in cells) - min(r for r, _ in cells) >= 14
        assert max(c for _, c in cells) - min(c for _, c in cells) >= 14
        quadrants = {(r >= 15, c >= 15) for r, c in cells}
        assert len(quadrants) >= 3


def test_racket_programs_match_python_claims(adapter):
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=64) as bridge:
        for mode in adapter.PATH_MODES:
            settings = {"path_mode": mode}
            episode = adapter.generate(31, settings, demos=2, queries=2)
            program = adapter.program(settings)
            for pair in episode["train"] + episode["test"]:
                assert _racket_apply(bridge, program, pair["input"]) == pair["output"]


def test_generation_is_deterministic_fresh_and_global_rng_pure(adapter):
    settings = {"path_mode": "bidirectional"}
    state = random.getstate()
    first = adapter.generate(17, settings, demos=6, queries=4)
    assert random.getstate() == state
    second = adapter.generate(17, settings, demos=6, queries=4)
    assert first == second and first is not second
    original = deepcopy(second)
    first["train"][0]["input"][0][0] = 9
    first["test"][0]["output"][0][0] = 9
    assert second == original


def test_minimum_demo_prefix_always_teaches_flip_control(adapter):
    """Removing color 6 must break at least one of the first two demonstrations."""
    for seed in range(32):
        for mode in adapter.PATH_MODES:
            episode = adapter.generate(seed, {"path_mode": mode}, demos=2, queries=1)
            predictions = []
            for pair in episode["train"]:
                grid = pair["input"]
                shape = adapter.raw_template(grid)
                flat = [value for row in grid for value in row]
                control = next(color for color in (2, 3, 4) if color in flat)
                for _ in range({2: 0, 3: 1, 4: 2}[control]):
                    shape = adapter._rotate(shape)
                predictions.append(adapter.solve_with_shape(grid, mode, shape))
            assert predictions != [pair["output"] for pair in episode["train"]], (seed, mode)
