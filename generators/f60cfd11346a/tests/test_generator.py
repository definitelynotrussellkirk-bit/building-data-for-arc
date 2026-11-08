"""Focused contract tests for the selective flood-fill generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "f60cfd11346a"
HOME = Path(__file__).resolve().parents[1]
ROOT = find_root(__file__)


def _load_generator():
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()
PAIRS = canonical_pairs(TASK_ID, root=ROOT)
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
OBSERVED_CANONICAL_BLOCKERS = frozenset({3, 4, 5, 6, 7})


def flood_output(grid, *, passable=frozenset({0, 2})):
    """Independent rule oracle: traverse passable cells, paint reached zeros 8."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    seeds = [(r, c) for r in range(h) for c in range(w) if grid[r][c] == 2]
    if len(seeds) != 1:
        raise ValueError(f"expected one seed, found {len(seeds)}")
    seen = {seeds[0]}
    stack = [seeds[0]]
    while stack:
        r, c = stack.pop()
        if grid[r][c] == 0:
            out[r][c] = 8
        for dr, dc in CARDINAL:
            nr, nc = r + dr, c + dc
            if (0 <= nr < h and 0 <= nc < w and (nr, nc) not in seen
                    and grid[nr][nc] in passable):
                seen.add((nr, nc))
                stack.append((nr, nc))
    return out


def canonical_palette_shortcut(grid):
    """Wrong rival: only blocker colors observed in canonical are impassable."""
    passable = frozenset(v for v in range(10) if v not in OBSERVED_CANONICAL_BLOCKERS)
    return flood_output(grid, passable=passable)


def coarse_partition_shortcut(grid):
    """Wrong rival: fill the seed's rectangle between full wall rows/columns."""
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    seed = next((r, c) for r in range(h) for c in range(w) if grid[r][c] == 2)
    full_rows = [
        r for r in range(1, h - 1)
        if all(grid[r][c] not in (0, 2) for c in range(1, w - 1))
    ]
    full_cols = [
        c for c in range(1, w - 1)
        if all(grid[r][c] not in (0, 2) for r in range(1, h - 1))
    ]
    row_edges = [0, *full_rows, h - 1]
    col_edges = [0, *full_cols, w - 1]
    r0 = max(edge for edge in row_edges if edge < seed[0])
    r1 = min(edge for edge in row_edges if edge > seed[0])
    c0 = max(edge for edge in col_edges if edge < seed[1])
    c1 = min(edge for edge in col_edges if edge > seed[1])
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if grid[r][c] == 0:
                out[r][c] = 8
    return out


def selected_rule_hash() -> str:
    from arcpuzzles import Catalog

    return Catalog(ROOT).describe(TASK_ID)["rule_hash"]


def test_rule_pin_matches_selected_canonical_authority():
    assert gen.RULE_HASH == selected_rule_hash() == "23823efe5a14"


@pytest.mark.parametrize(
    "pair",
    PAIRS,
    ids=[f"{pair['split']}{pair['pair_index']}" for pair in PAIRS],
)
def test_canonical_pairs_are_owned_and_match_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert flood_output(pair["input"]) == pair["output"]


def test_shortcut_really_fits_every_labeled_canonical_pair():
    assert len(PAIRS) == 5
    assert all(canonical_palette_shortcut(pair["input"]) == pair["output"] for pair in PAIRS)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "options",
    [
        {"grid_h": 7, "grid_w": 8, "layout_style": "vertical", "accent_color": 1},
        {"grid_h": 9, "grid_w": 11, "layout_style": "horizontal", "accent_color": 9},
        {"grid_h": 15, "grid_w": 22, "layout_style": "cross", "accent_color": 6},
    ],
)
def test_exact_observable_overrides_in_every_band(band, options):
    grid = gen.generate(1701, 29, difficulty=band, **options)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == options
    assert (len(grid), len(grid[0])) == (options["grid_h"], options["grid_w"])


def test_small_cross_layouts_always_leave_floor_beside_the_seed():
    """Regression for override-contract seeds that selected a 1-cell quadrant."""
    for band in ("easy", "medium", "hard"):
        for height in (7, 8):
            for width in (8, 9, 10, 11):
                for seed in range(30):
                    sample_index = seed * 17 + 3
                    grid = gen.generate(
                        seed,
                        sample_index,
                        difficulty=band,
                        grid_h=height,
                        grid_w=width,
                        layout_style="cross",
                        accent_color=1,
                    )
                    assert gen.self_check(grid) == [], (
                        band, height, width, seed, sample_index, grid
                    )


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo_axis", 1),
        ("grid_h", 6), ("grid_h", 16), ("grid_h", True),
        ("grid_h", 8.0), ("grid_h", "8"),
        ("grid_w", 7), ("grid_w", 23), ("grid_w", False),
        ("layout_style", "diagonal"), ("layout_style", 1),
        ("accent_color", 0), ("accent_color", 2), ("accent_color", 5),
        ("accent_color", 8), ("accent_color", 10), ("accent_color", 1.0),
    ],
)
def test_invalid_and_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("layout", ["vertical", "horizontal", "cross"])
@pytest.mark.parametrize("accent", [1, 3, 4, 6, 7, 9])
def test_all_layout_and_accent_values_are_realized(layout, accent):
    options = {"grid_h": 10, "grid_w": 12, "layout_style": layout, "accent_color": accent}
    grid = gen.generate(71, accent, difficulty="hard", **options)
    assert gen.observe_overrides(grid) == options
    assert set(value for row in grid for value in row) == {0, 2, 5, accent}
    assert flood_output(grid) != grid


@pytest.mark.parametrize("index", range(96))
def test_default_generation_is_deterministic_lawful_and_selective(index):
    band = ("easy", "medium", "hard")[index % 3]
    grid = gen.generate(9100 + index, index * 13 + 7, difficulty=band)
    assert grid == gen.generate(9100 + index, index * 13 + 7, difficulty=band)
    assert gen.self_check(grid) == []
    assert set(gen.observe_overrides(grid)) == set(gen.AXES)
    output = flood_output(grid)
    assert output != grid
    assert any(value == 0 for row in output for value in row), "generated case lost selectivity"
    assert len({value for row in grid for value in row}) == 4


def test_default_schedule_regularly_refutes_the_canonical_palette_shortcut():
    disagreements = 0
    for index in range(128):
        grid = gen.generate(31000 + index, index * 5, difficulty=("easy", "medium", "hard")[index % 3])
        disagreements += flood_output(grid) != canonical_palette_shortcut(grid)
    assert disagreements >= 96


def test_every_default_draw_refutes_the_coarse_partition_shortcut():
    for index in range(128):
        grid = gen.generate(41000 + index, index * 7 + 1, difficulty=("easy", "medium", "hard")[index % 3])
        assert flood_output(grid) != coarse_partition_shortcut(grid), index
        assert gen.SEMANTIC_WITNESSES["internal_branch_pocket"](grid)
        assert gen.SEMANTIC_RIVALS["coarse_partition_only"](grid) == coarse_partition_shortcut(grid)


@pytest.mark.parametrize("layout", ["vertical", "horizontal", "cross"])
@pytest.mark.parametrize("accent", [1, 9])
def test_unseen_color_is_a_critical_wall_counterexample(layout, accent):
    grid = gen.generate(
        43, 2, grid_h=9, grid_w=11, layout_style=layout, accent_color=accent
    )
    intended = flood_output(grid)
    rival = canonical_palette_shortcut(grid)
    assert intended != rival
    assert gen.SEMANTIC_WITNESSES["unseen_blocker_color"](grid)
    assert gen.SEMANTIC_RIVALS["canonical_blocker_palette_only"](grid) == rival


@pytest.mark.parametrize(
    "mutation",
    ["second_seed", "input_fill_color", "open_border", "erase_all_zeros"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(811, 4, grid_h=9, grid_w=11, accent_color=1)
    changed = deepcopy(grid)
    if mutation == "second_seed":
        for r, row in enumerate(changed):
            for c, value in enumerate(row):
                if value == 0:
                    changed[r][c] = 2
                    break
            else:
                continue
            break
    elif mutation == "input_fill_color":
        changed[1][1] = 8
    elif mutation == "open_border":
        changed[0][1] = 0
    elif mutation == "erase_all_zeros":
        changed = [[5 if value == 0 else value for value in row] for row in changed]
    assert gen.self_check(changed)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(7)]])
def test_malformed_inputs_return_diagnostics_instead_of_crashing(grid):
    assert gen.self_check(grid)


def test_generation_is_python_hash_seed_independent():
    script = (
        "import importlib.util,json,sys;"
        "p=sys.argv[1];s=importlib.util.spec_from_file_location('g',p);"
        "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
        "print(json.dumps(m.generate(717,19,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "991"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "generator.py")],
                env=env,
                text=True,
            )
        )
    assert outputs[0] == outputs[1]


def test_selected_racket_authority_matches_independent_oracle():
    from arcpuzzles import Catalog
    from arc_repl.racket_bridge import racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])

    grids = [pair["input"] for pair in PAIRS]
    grids += [
        gen.generate(52000 + index, index, difficulty=("easy", "medium", "hard")[index % 3], accent_color=(1, 9)[index % 2])
        for index in range(12)
    ]
    receipt = Catalog(ROOT).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert all(item["error"] is None for item in receipt["results"])
    assert [item["output"] for item in receipt["results"]] == [flood_output(grid) for grid in grids]


def test_semantic_contract_names_the_canonical_fitting_rival():
    palette_rival = "canonical_blocker_palette_only"
    geometry_rival = "coarse_partition_only"
    assert set(gen.SEMANTIC_WITNESSES) == {
        "unseen_blocker_color",
        "internal_branch_pocket",
    }
    assert set(gen.SEMANTIC_RIVALS) == {palette_rival, geometry_rival}
    assert gen.WITNESS_RIVALS == {
        "unseen_blocker_color": [palette_rival],
        "internal_branch_pocket": [geometry_rival],
    }
    assert set(gen.CANONICAL_SHORTCUTS) == {palette_rival}
    assert set(gen.LESSON_COMPETITORS) == {palette_rival, geometry_rival}


def test_reference_probe_reports_canonical_fit_and_emitted_counterexample():
    path = HOME / "workspace" / "reference_probe.py"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    report = module.build_report(include_racket=False)
    rival = report["rivals"]["canonical_blocker_palette_only"]
    geometry_rival = report["rivals"]["coarse_partition_only"]
    assert rival["fits_all_canonical_pairs"]
    assert rival["canonical_pairs_checked"] == 5
    assert rival["witness_disagrees"]
    assert geometry_rival["witness_disagrees"]
    assert report["witness"]["self_check"] == []
    assert report["witness"]["ordinary_sampler_emits_this_class"]
    for competitor in report["ordinary_sampler_probe"]["competitors"].values():
        assert competitor["disagreements"] == report["ordinary_sampler_probe"]["draws"]
