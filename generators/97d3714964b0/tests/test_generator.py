"""Focused regressions for 97d3714964b0.

The oracle below is intentionally independent of the production generator helpers.
It implements the selected rule over 4-connected color-7 components.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK = "97d3714964b0"
HOME = Path(__file__).resolve().parents[1]


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _components7(grid):
    h, w = len(grid), len(grid[0])
    remaining = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == 7}
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        stack = [start]
        cells = {start}
        while stack:
            r, c = stack.pop()
            for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (rr, cc) in remaining:
                    remaining.remove((rr, cc))
                    cells.add((rr, cc))
                    stack.append((rr, cc))
        rows = [r for r, _ in cells]
        cols = [c for _, c in cells]
        bbox = (min(rows), min(cols), max(rows), max(cols))
        r0, c0, r1, c1 = bbox
        interior = [(r, c) for r in range(r0 + 1, r1) for c in range(c0 + 1, c1)]
        hollow = any(grid[r][c] == 0 and (r, c) not in cells for r, c in interior)
        result.append({"cells": cells, "bbox": bbox, "hollow": hollow})
    return sorted(result, key=lambda obj: obj["bbox"])


def _oracle(grid):
    out = deepcopy(grid)
    for obj in _components7(grid):
        color = 4 if obj["hollow"] else 2
        for r, c in obj["cells"]:
            out[r][c] = color
    return out


def _observed(grid):
    objects = _components7(grid)
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_hollow": sum(obj["hollow"] for obj in objects),
        "n_solid": sum(not obj["hollow"] for obj in objects),
    }


def _canonical_pairs():
    return canonical_pairs(TASK, root=find_root(__file__))


@pytest.mark.parametrize("pair", _canonical_pairs(), ids=["train0", "train1", "test0"])
def test_accepts_every_canonical_input_and_oracle_matches_label(pair):
    assert gen.self_check(pair["input"]) == []
    assert _oracle(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_and_honored_in_every_band(band):
    expected = {"grid_h": 7, "grid_w": 9, "n_hollow": 2, "n_solid": 2}
    grid = gen.generate(17, 9, difficulty=band, **expected)
    assert gen.self_check(grid) == []
    assert _observed(grid) == expected
    assert gen.observe_overrides(grid) == expected


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 15),
        ("grid_w", 8),
        ("grid_w", 15),
        ("n_hollow", 0),
        ("n_hollow", 3),
        ("n_solid", 0),
        ("n_solid", 3),
        ("grid_h", True),
        ("grid_w", 9.0),
        ("n_hollow", "1"),
    ],
)
def test_rejects_unknown_out_of_range_and_non_integer_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_each_generated_grid_contains_a_size_shortcut_counterexample(band):
    for index in range(32):
        grid = gen.generate(700 + index, index * 13, difficulty=band)
        assert gen.self_check(grid) == []
        objects = _components7(grid)
        hollow_dims = {
            (obj["bbox"][2] - obj["bbox"][0] + 1, obj["bbox"][3] - obj["bbox"][1] + 1)
            for obj in objects
            if obj["hollow"]
        }
        solid_dims = {
            (obj["bbox"][2] - obj["bbox"][0] + 1, obj["bbox"][3] - obj["bbox"][1] + 1)
            for obj in objects
            if not obj["hollow"]
        }
        assert hollow_dims & solid_dims, "one hollow and one solid must share bbox dimensions"
        assert any(len(obj["cells"]) >= 8 for obj in objects if not obj["hollow"])
        assert _oracle(grid) != grid


def test_declared_canonical_shortcuts_fit_canonical_but_fail_generated_witnesses():
    names = {"bbox_area_gt4", "component_size_ge8", "bbox_height_ge3"}
    assert set(gen.CANONICAL_SHORTCUTS) == names
    assert set(gen.LESSON_COMPETITORS) == names
    assert set(gen.SEMANTIC_RIVALS) == names
    for rival in gen.CANONICAL_SHORTCUTS.values():
        assert all(rival(pair["input"]) == pair["output"] for pair in _canonical_pairs())
    for index in range(24):
        grid = gen.generate(911, index)
        expected = _oracle(grid)
        assert all(rival(grid) != expected for rival in gen.LESSON_COMPETITORS.values())
        assert gen.SEMANTIC_WITNESSES["same_bbox_hollow_and_solid"](grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_each_band_has_exact_canonical_shape_palette_support(band):
    canonical_profiles = {
        (len(pair["input"]), len(pair["input"][0]), len({v for row in pair["input"] for v in row}))
        for pair in _canonical_pairs()
    }
    profiles = set()
    for index in range(64):
        grid = gen.generate(1200 + index, index * 7, difficulty=band)
        profiles.add((len(grid), len(grid[0]), len({v for row in grid for v in row})))
        assert {v for row in grid for v in row} <= {0, 7}
    assert profiles & canonical_profiles


def test_generation_is_deterministic_and_does_not_return_aliases():
    first = gen.generate(412, 111, difficulty="hard")
    second = gen.generate(412, 111, difficulty="hard")
    assert first == second
    assert first is not second
    before = deepcopy(first)
    first[0][0] = 9
    assert second == before


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(7)], [[0] * 9 for _ in range(7)]],
)
def test_malformed_or_semantically_empty_grids_are_diagnostic_not_exceptions(grid):
    assert gen.self_check(grid)


def test_real_racket_reference_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])

    # The public apply command is covered separately in the retained audit tool;
    # task tests exercise the same selected authority through the portable runner.
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process
    import json
    import sys
    import tempfile

    root = find_root(__file__)
    grids = [pair["input"] for pair in _canonical_pairs()]
    grids += [gen.generate(319, index, difficulty="hard") for index in range(16)]
    program = None
    with (root / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                program = row["program_solution"]
                break
    assert program is not None

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(root), stage, TASK)
        (stage / "request.json").write_text(json.dumps({"program": program, "grids": grids}))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        assert not result["timed_out"]
        assert result["exit_code"] == 0, result
        outputs = json.loads(result["stdout"])
    assert outputs == [_oracle(grid) for grid in grids]
