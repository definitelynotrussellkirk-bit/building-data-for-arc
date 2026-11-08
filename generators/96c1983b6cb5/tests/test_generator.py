"""Regression suite for 96c1983b6cb5; workspace helpers are independent."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CANONICAL_TRANSFORMS,
    PALETTE_PAIRS,
    canonical_pairs,
    canonical_subset_rival,
    foreground,
    infer_transform,
    load_generator,
    normalized_rule_hash,
    observed,
    racket_outputs,
    reference_output,
    split_panels,
    transform_cells,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_pin_and_all_canonical_pairs() -> None:
    assert gen.RULE_HASH == normalized_rule_hash() == "9c8ca59a982a"
    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert reference_output(pair["input"]) == pair["output"]
        assert gen.reference_output(pair["input"]) == pair["output"]
        assert pair["input"] == original


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_exact_overrides_are_observable_and_band_safe(band: str | None) -> None:
    requested = {
        "panel_n": 5,
        "transform": 7,
        "a_cells": 3,
        "c_cells": 6,
        "palette_id": 4,
    }
    grid = gen.generate(17, 9, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert observed(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert reference_output(grid) != split_panels(grid)[2]


@pytest.mark.parametrize(
    "axis,value",
    [
        ("unknown_axis", 1),
        ("panel_n", 2),
        ("panel_n", 6),
        ("transform", -1),
        ("transform", 8),
        ("a_cells", 2),
        ("a_cells", 7),
        ("c_cells", 2),
        ("c_cells", 7),
        ("palette_id", -1),
        ("palette_id", len(PALETTE_PAIRS)),
        ("panel_n", True),
        ("transform", "1"),
        ("a_cells", 3.5),
    ],
)
def test_invalid_overrides_reject(axis: str, value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        gen.generate(1, 2, difficulty="hard", **{axis: value})


@pytest.mark.parametrize("difficulty", ["invalid", 0, True])
def test_invalid_difficulty_rejects(difficulty: object) -> None:
    with pytest.raises(ValueError):
        gen.generate(1, 2, difficulty=difficulty)


@pytest.mark.parametrize("code", range(8))
def test_every_transform_uses_canonical_order(code: int) -> None:
    grid = gen.generate(
        70 + code,
        code,
        difficulty="hard",
        panel_n=5,
        transform=code,
        a_cells=5,
        c_cells=6,
        palette_id=code % len(PALETTE_PAIRS),
    )
    assert infer_transform(grid) == code
    assert gen.reference_output(grid) == reference_output(grid)


@pytest.mark.parametrize("band_index,band", enumerate(("easy", "medium", "hard")))
def test_default_distribution_covers_rule_branches_and_canonical_scale(
    band_index: int, band: str
) -> None:
    panel_sizes: set[int] = set()
    transforms: set[int] = set()
    palettes: set[int] = set()
    distinct_inputs: set[str] = set()
    noncanonical_per_window: list[bool] = []
    grids = []
    for index in range(84):
        seed = 20_000 + band_index * 1000 + index
        sample_index = index
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        assert grid == gen.generate(seed, sample_index, difficulty=band)
        facts = observed(grid)
        assert gen.observe_overrides(grid) == facts
        assert gen.reference_output(grid) == reference_output(grid)
        if facts["transform"] == 0:
            assert reference_output(grid) == split_panels(grid)[2]
        else:
            assert reference_output(grid) != split_panels(grid)[2]
        panel_a, _, panel_c = split_panels(grid)
        _, a = foreground(panel_a)
        _, c = foreground(panel_c)
        assert c not in {transform_cells(a, len(panel_a), code) for code in range(8)}
        panel_sizes.add(facts["panel_n"])
        transforms.add(facts["transform"])
        palettes.add(facts["palette_id"])
        distinct_inputs.add(json.dumps(grid, separators=(",", ":")))
        grids.append(grid)
    for start in range(0, 70):
        noncanonical_per_window.append(
            any(infer_transform(grids[(start + offset) % len(grids)]) not in CANONICAL_TRANSFORMS for offset in range(3))
        )
    assert panel_sizes == {3, 4, 5}
    assert transforms == set(range(8))
    assert palettes == set(range(len(PALETTE_PAIRS)))
    assert len(distinct_inputs) >= 82
    assert all(noncanonical_per_window)


def test_difficulty_changes_defaults_without_restricting_domains() -> None:
    rows = [gen.generate(998, 13, difficulty=band) for band in ("easy", "medium", "hard")]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in rows}) > 1
    requested = {"panel_n": 3, "transform": 5, "a_cells": 6, "c_cells": 3, "palette_id": 3}
    for band in ("easy", "medium", "hard"):
        assert observed(gen.generate(998, 13, difficulty=band, **requested)) == requested


def test_validator_rejects_structural_impostors() -> None:
    base = gen.generate(99, 14, panel_n=4, transform=3, a_cells=5, c_cells=4, palette_id=0)
    assert gen.self_check(base) == []

    cases: dict[str, object] = {
        "empty": [],
        "ragged": [[0], [0, 0]],
        "bool_cells": [[True] * 14 for _ in range(4)],
        "all_background": [[0] * 14 for _ in range(4)],
    }
    missing_separator = deepcopy(base)
    for row in missing_separator:
        row[4] = 0
    cases["missing_separator"] = missing_separator

    extra_separator = deepcopy(base)
    for row in extra_separator:
        row[0] = 8
    cases["extra_separator"] = extra_separator

    mismatched_b_color = deepcopy(base)
    for row in mismatched_b_color:
        for col in range(5, 9):
            if row[col] not in (0, 8):
                row[col] = 3
    cases["mismatched_b_color"] = mismatched_b_color

    symmetric_demo = deepcopy(base)
    for row in range(4):
        symmetric_demo[row][0:4] = [0, 0, 0, 0]
        symmetric_demo[row][5:9] = [0, 0, 0, 0]
    for row, col in ((1, 1), (1, 2), (2, 1), (2, 2)):
        symmetric_demo[row][col] = PALETTE_PAIRS[0][0]
        symmetric_demo[row][col + 5] = PALETTE_PAIRS[0][0]
    cases["symmetric_demo"] = symmetric_demo

    symmetric_query = deepcopy(base)
    for row in range(4):
        symmetric_query[row][10:14] = [0, 0, 0, 0]
    symmetric_query[1][11] = symmetric_query[1][12] = PALETTE_PAIRS[0][1]
    symmetric_query[2][11] = symmetric_query[2][12] = PALETTE_PAIRS[0][1]
    cases["symmetric_query"] = symmetric_query

    unknown_color = deepcopy(base)
    unknown_color[0][0] = 9
    cases["unknown_color"] = unknown_color

    for name, grid in cases.items():
        assert gen.self_check(grid), name


def test_canonical_fitting_shortcut_has_generated_counterexamples() -> None:
    pairs = canonical_pairs()
    assert all(canonical_subset_rival(pair["input"]) == pair["output"] for pair in pairs)
    assert "canonical_transform_subset_only" in gen.CANONICAL_SHORTCUTS
    witnesses = []
    for code in sorted(set(range(8)) - CANONICAL_TRANSFORMS):
        grid = gen.generate(401, code, transform=code, panel_n=4, a_cells=5, c_cells=6, palette_id=0)
        truth = reference_output(grid)
        rival = gen.SEMANTIC_RIVALS["canonical_transform_subset_only"](grid)
        assert gen.SEMANTIC_WITNESSES["noncanonical_transform"](grid)
        assert rival == canonical_subset_rival(grid)
        assert rival != truth
        witnesses.append(grid)
    assert len(witnesses) == 5


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_consecutive_three_demo_lesson_refutes_declared_rival(band: str) -> None:
    for start in range(28):
        grids = [gen.generate(90_000 + start, start + offset, difficulty=band) for offset in range(4)]
        demos = [{"input": grid, "output": reference_output(grid)} for grid in grids[:3]]
        query = {"input": grids[3], "output": reference_output(grids[3])}
        assert gen.lesson_identifiable(demos, query) == [], (band, start)
        assert any(
            canonical_subset_rival(demo["input"]) != demo["output"]
            for demo in demos
        )


def test_global_rng_and_python_hash_seed_do_not_change_generation() -> None:
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


def test_real_racket_reference_when_available() -> None:
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [
        gen.generate(55_000 + code, code, transform=code, panel_n=3 + code % 3, palette_id=code % len(PALETTE_PAIRS))
        for code in range(1, 8)
    ]
    assert racket_outputs(grids) == [reference_output(grid) for grid in grids]
