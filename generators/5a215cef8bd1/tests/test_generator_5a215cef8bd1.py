"""Task-local regressions for the transform-panel generator."""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (
    CONTROL_ORDERS,
    canonical_pairs,
    crop_template,
    fixed_3x3_panel,
    load_generator,
    observed,
    panel_output,
    racket_outputs,
    rectangular_counterexample,
    template_cells,
    template_size,
    transform_signatures,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))

EXPECTED_AXES = {"grid_h", "grid_w", "template_size", "control_order", "layout_mode"}
LAYOUTS = ("controls_above", "controls_below", "controls_left", "controls_right")


def test_metadata_pins_rule_and_declares_only_observable_axes():
    assert gen.RULE_HASH == "b5c73de1606e"
    assert set(gen.AXES) == EXPECTED_AXES
    assert tuple(gen.SCHEDULE_PROFILES) == tuple(range(12))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_canonical_inputs_are_owned_and_python_oracle_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert panel_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("layout", LAYOUTS)
@pytest.mark.parametrize("size", [2, 3, 4])
def test_exact_semantic_overrides_are_realized_and_observed(band, layout, size):
    options = {
        "grid_h": 8 if layout in ("controls_above", "controls_below") else 11,
        "grid_w": 8 if layout in ("controls_left", "controls_right") else 12,
        "template_size": size,
        "control_order": (size * 7 + LAYOUTS.index(layout)) % 24,
        "layout_mode": layout,
    }
    grid = gen.generate(179, 31, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize("order", range(24))
def test_all_control_permutations_are_exact(order):
    grid = gen.generate(61, order, control_order=order)
    assert gen.self_check(grid) == []
    assert observed(grid)["control_order"] == order


@pytest.mark.parametrize(
    "key,value",
    [
        ("unknown_axis", 1),
        ("grid_h", 7), ("grid_h", 19), ("grid_h", True),
        ("grid_w", 7), ("grid_w", 19), ("grid_w", "10"),
        ("template_size", 1), ("template_size", 5), ("template_size", 3.0),
        ("control_order", -1), ("control_order", 24), ("control_order", False),
        ("layout_mode", "diagonal"), ("layout_mode", 1),
    ],
)
def test_invalid_overrides_fail_loudly(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_distribution_is_deterministic_lossless_and_covers_semantics(band):
    sizes, layouts, orders, shapes = set(), set(), set(), set()
    for index in range(180):
        seed = 50_000 + index
        sample_index = index * 13 + 2
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert grid == gen.generate(seed, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        stats = observed(grid)
        sizes.add(stats["template_size"])
        layouts.add(stats["layout_mode"])
        orders.add(stats["control_order"])
        shapes.add((len(grid), len(grid[0])))
        assert len(set(transform_signatures(grid))) == 4
        out = panel_output(grid)
        assert sum(value == 7 for row in out for value in row) == 4 * len(template_cells(grid))
    assert sizes == {2, 3, 4}
    assert layouts == set(LAYOUTS)
    assert len(orders) >= 20
    assert len(shapes) >= 12


def test_rectangular_template_is_rejected_before_rotation_can_clip_slots():
    grid = rectangular_counterexample()
    assert len(crop_template(grid)) == 2 and len(crop_template(grid)[0]) == 3
    assert gen.self_check(grid)
    output = panel_output(grid)
    th, tw = len(crop_template(grid)), len(crop_template(grid)[0])
    assert any(value == 7 for value in output[th]) or any(row[tw] == 7 for row in output)


def test_canonical_fixed_3x3_shortcut_is_refuted_in_every_three_draw_window():
    assert all(fixed_3x3_panel(pair["input"]) == pair["output"] for pair in canonical_pairs())
    generated = [gen.generate(404, index, difficulty="hard") for index in range(36)]
    for start in range(len(generated) - 3):
        demos = [
            {"input": grid, "output": panel_output(grid)}
            for grid in generated[start:start + 3]
        ]
        query = {"input": generated[start + 3], "output": panel_output(generated[start + 3])}
        assert any(template_size(demo["input"]) != 3 for demo in demos)
        assert gen.lesson_identifiable(demos, query) == []
    witnesses = [grid for grid in generated if template_size(grid) != 3]
    assert witnesses
    for grid in witnesses:
        assert gen.SEMANTIC_WITNESSES["non_3x3_template"](grid)
        assert gen.SEMANTIC_RIVALS["fixed_3x3_panel"](deepcopy(grid)) == fixed_3x3_panel(grid)
        assert fixed_3x3_panel(grid) != panel_output(grid)


@pytest.mark.parametrize(
    "mutation",
    ["unknown_color", "missing_control", "duplicate_control", "split_template"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(88, 7, grid_h=12, grid_w=12, template_size=3)
    if mutation == "unknown_color":
        grid[0][0] = 9
    elif mutation == "missing_control":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 6:
                    grid[r][c] = 0
                    break
    elif mutation == "duplicate_control":
        for r, row in enumerate(grid):
            for c, value in enumerate(row):
                if value == 6:
                    grid[r][c] = 1
                    break
    elif mutation == "split_template":
        cells = sorted(template_cells(grid))
        r, c = cells[len(cells) // 2]
        grid[r][c] = 0
        # Make a remote second color-2 component without disturbing controls.
        for rr, row in enumerate(grid):
            for cc, value in enumerate(row):
                if value == 0 and all(abs(rr-r0) + abs(cc-c0) > 1 for r0, c0 in template_cells(grid)):
                    grid[rr][cc] = 2
                    break
            else:
                continue
            break
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(8)]])
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_real_racket_reference_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(777, index, difficulty="hard") for index in range(18)]
    assert racket_outputs(grids) == [panel_output(grid) for grid in grids]
