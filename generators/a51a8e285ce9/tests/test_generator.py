"""Task-local regression suite for a51a8e285ce9.

The geometry oracle lives in workspace and shares no production helpers.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    CODES,
    REFLECTIONS,
    canonical_pairs,
    geometry_output,
    load_generator,
    object_offsets,
    observed,
    orbit,
    parse,
    racket_outputs,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_accepts_canonical_inputs_including_color8_object(pair):
    assert gen.self_check(pair["input"]) == []
    assert geometry_output(pair["input"]) == pair["output"]


def test_pins_selected_rule_hash():
    assert getattr(gen, "RULE_HASH", None) == "d76e03446f2a"


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        dict(grid_h=4, panel_w=4, prototype_size=5, match_index=0, transform="id", palette_size=4),
        dict(grid_h=5, panel_w=6, prototype_size=7, match_index=1, transform="tr", palette_size=5),
        dict(grid_h=7, panel_w=7, prototype_size=8, match_index=1, transform="atr", palette_size=4),
    ],
)
def test_exact_overrides_are_pixel_observable_in_every_band(band, options):
    grid = gen.generate(17, 9, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert observed(grid) == options
    assert gen.observe_overrides(grid) == options


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 3),
        ("grid_h", 8),
        ("panel_w", 3),
        ("panel_w", 8),
        ("prototype_size", 4),
        ("prototype_size", 9),
        ("match_index", -1),
        ("match_index", 2),
        ("transform", "rot90"),
        ("palette_size", 3),
        ("palette_size", 6),
        ("grid_h", True),
        ("panel_w", 4.0),
        ("prototype_size", "5"),
        ("match_index", 1.0),
    ],
)
def test_rejects_unknown_out_of_range_and_wrong_type_overrides(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_instances_require_symmetry_not_cell_count(band):
    for index in range(48):
        grid = gen.generate(2000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert geometry_output(grid)
        info = parse(grid)
        a, b = (p["support"] for p in info["protos"])
        assert len(a) == len(b)
        assert orbit(a).isdisjoint(orbit(b))
        assert len(orbit(a)) == len(orbit(b)) == 8
        assert len({p["color"] for p in info["panels"]}) == 3
        assert geometry_output(grid) == gen.rule_mirror(grid)


def test_objects_are_not_all_top_left_anchored():
    offsets = set()
    for index in range(80):
        offsets.update(object_offsets(gen.generate(3100 + index, index, grid_h=7, panel_w=7)))
    assert len(offsets) >= 8
    assert any(r > 0 for r, _ in offsets)
    assert any(c > 0 for _, c in offsets)


def test_four_consecutive_demos_refute_every_declared_competitor():
    competitors = getattr(gen, "LESSON_COMPETITORS", None)
    assert isinstance(competitors, dict) and competitors
    for start in range(16):
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(8001, start + offset, difficulty="medium")
            demos.append({"input": grid, "output": geometry_output(grid)})
        query_grid = gen.generate(8001, start + gen.EXAMPLES_NEEDED, difficulty="medium")
        assert gen.lesson_identifiable(demos, {"input": query_grid}) == []
        for name, rival in competitors.items():
            assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_reflection_witness_really_requires_reflection():
    witnesses = getattr(gen, "SEMANTIC_WITNESSES", None)
    rivals = getattr(gen, "SEMANTIC_RIVALS", None)
    assert isinstance(witnesses, dict) and isinstance(rivals, dict)
    for code in REFLECTIONS:
        grid = gen.generate(97, CODES.index(code), match_index=1, transform=code)
        assert witnesses["reflection_required"](grid)
        assert rivals["rotations_only"](grid) != geometry_output(grid)


@pytest.mark.parametrize(
    "mutator",
    ["erase_separator", "empty_query", "duplicate_prototypes", "third_shape", "mixed_panel_colors"],
)
def test_validator_rejects_rule_precondition_violations(mutator):
    grid = gen.generate(44, 7, grid_h=6, panel_w=6, prototype_size=7, palette_size=5)
    info = parse(grid)
    pw = info["panel_w"]
    if mutator == "erase_separator":
        grid[0][pw] = 0
    elif mutator == "empty_query":
        left = 2 * (pw + 1)
        for r in range(len(grid)):
            for c in range(left, left + pw):
                grid[r][c] = 0
    elif mutator == "duplicate_prototypes":
        for r in range(len(grid)):
            for c in range(pw):
                grid[r][pw + 1 + c] = 0
        p0 = info["protos"][0]
        for r, c in p0["raw"]:
            grid[r][pw + 1 + c] = p0["color"]
    elif mutator == "third_shape":
        left = 2 * (pw + 1)
        for r in range(len(grid)):
            for c in range(left, left + pw):
                grid[r][c] = 0
        color = info["query"]["color"]
        for r, c in ((0, 0), (1, 0), (2, 0), (2, 1)):
            grid[r][left + c] = color
    else:
        p0 = info["protos"][0]
        r, c = p0["raw"][0]
        grid[r][c] = 9 if p0["color"] != 9 else 7
    assert gen.self_check(grid)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 14 for _ in range(4)]])
def test_malformed_grid_returns_diagnostics_not_exceptions(grid):
    assert gen.self_check(grid)


def test_keyed_generation_is_hashseed_independent():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(31,8,difficulty='hard')))"
    )
    results = []
    for hashseed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hashseed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_difficulty_changes_default_complexity_without_removing_override_support():
    means = {}
    for band in ("easy", "medium", "hard"):
        sizes = [observed(gen.generate(7200 + i, i, difficulty=band))["prototype_size"] for i in range(80)]
        means[band] = sum(sizes) / len(sizes)
        # Every endpoint remains constructively available by exact override.
        for size in (5, 8):
            assert observed(gen.generate(3, size, difficulty=band, prototype_size=size))["prototype_size"] == size
    assert means["easy"] < means["medium"] < means["hard"]


def test_each_band_has_canonical_profile_support_on_pinned_like_census():
    for band in ("easy", "medium", "hard"):
        profiles = {
            (len(g), len(g[0]), len({v for row in g for v in row}))
            for i in range(40)
            for g in [gen.generate(9300 + i * 17, (9300 + i * 17) % 7919 + i, difficulty=band)]
        }
        assert profiles & {(4, 14, 4), (4, 14, 5)}


def test_real_racket_reference_agrees_with_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(6021, i, difficulty="hard") for i in range(24)]
    assert racket_outputs(grids) == [geometry_output(grid) for grid in grids]
