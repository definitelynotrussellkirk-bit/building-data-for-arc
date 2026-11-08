"""Task-local regression tests for the normalized-XOR stamp generator."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HOME / "workspace"))
from reference_probe import (  # noqa: E402
    TASK_ID,
    canonical_pairs,
    cells,
    load_generator,
    normalized_shapes,
    observed,
    reference_output,
    role_order,
    shape_signature,
)

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))


def test_rule_identity_and_axis_surface_are_exact():
    assert gen.RULE_HASH == "75fe298a62dd"
    assert set(gen.AXES) == {"grid_h", "grid_w"}
    assert gen.HELPFUL_TEXTURES == ()
    assert gen.DEGENERATE_TEXTURES == ()


@pytest.mark.parametrize("pair", canonical_pairs(), ids=["train0", "train1", "test0"])
def test_accepts_canonical_pairs_and_independent_oracle(pair):
    assert gen.self_check(pair["input"]) == []
    assert reference_output(pair["input"]) == pair["output"]
    assert gen.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("height,width", [(10, 13), (10, 22), (18, 13), (18, 22), (14, 17)])
def test_exact_overrides_work_in_every_band(band, height, width):
    grid = gen.generate(913, height * 100 + width, difficulty=band, grid_h=height, grid_w=width)
    assert gen.self_check(grid) == []
    assert observed(grid) == {"grid_h": height, "grid_w": width}
    assert gen.observe_overrides(grid) == observed(grid)
    assert gen.rule_mirror(grid) == reference_output(grid)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"typo": 10},
        {"grid_h": 9},
        {"grid_h": 19},
        {"grid_w": 12},
        {"grid_w": 23},
        {"grid_h": True},
        {"grid_w": False},
        {"grid_h": 10.5},
        {"grid_w": "15"},
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(kwargs):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize("difficulty", ["trivial", 0.5, True])
def test_invalid_difficulty_is_rejected(difficulty):
    with pytest.raises(ValueError):
        gen.generate(0, 0, difficulty=difficulty)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_examples_are_valid_deterministic_and_oracle_exact(band):
    for index in range(80):
        grid = gen.generate(12000 + index, index, difficulty=band)
        assert grid == gen.generate(12000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert set(value for row in grid for value in row) == {0, 1, 2, 3}
        red, green = normalized_shapes(grid)
        assert red & green
        assert red - green
        assert green - red
        assert gen.rule_mirror(grid) == reference_output(grid)


def test_default_distribution_has_canonical_anchors_and_real_geometry_breadth():
    signatures = set()
    dimensions = set()
    orders = set()
    strict_hits = {band: 0 for band in ("easy", "medium", "hard")}
    for band in strict_hits:
        for index in range(120):
            grid = gen.generate(33000 + index, index, difficulty=band)
            signatures.add(shape_signature(grid))
            dimensions.add((len(grid), len(grid[0])))
            orders.add(role_order(grid))
            if not gen.strict_canonical_like(grid):
                strict_hits[band] += 1
    assert len(signatures) >= 120
    assert len(dimensions) >= 12
    assert len(orders) >= 5
    assert all(count >= 40 for count in strict_hits.values())


def test_declared_canonical_size_shortcut_fits_all_public_pairs():
    rival = gen.CANONICAL_SHORTCUTS["canonical_size_lookup"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_every_schedule_cycle_refutes_size_lookup_and_contains_no_crop_witness(band):
    size_rival = gen.SEMANTIC_RIVALS["canonical_size_lookup"]
    crop_rival = gen.SEMANTIC_RIVALS["crop_xor_to_bbox"]
    for start in range(8):
        block = [gen.generate(41000 + start, start + offset, difficulty=band) for offset in range(4)]
        assert all(size_rival(grid) != reference_output(grid) for grid in block)
        assert any(crop_rival(grid) != reference_output(grid) for grid in block)


@pytest.mark.parametrize(
    "band,seed,sample_index,witness",
    [
        ("medium", 238746783387979, 550, "set_operation"),
        ("hard", 248164116119424, 4392, "geometry_not_size_lookup"),
    ],
)
def test_pinned_semantic_census_examples_do_not_alias_through_edge_clipping(
    band, seed, sample_index, witness
):
    grid = gen.generate(seed, sample_index, difficulty=band)
    assert gen.SEMANTIC_WITNESSES[witness](grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(4))
def test_four_demo_lessons_refute_every_declared_competitor(band, start):
    grids = [gen.generate(52000 + start, start + offset, difficulty=band) for offset in range(5)]
    demos = [{"input": grid, "output": reference_output(grid)} for grid in grids[:4]]
    query = {"input": grids[4], "output": reference_output(grids[4])}
    assert gen.lesson_identifiable(demos, query) == []
    for name, rival in gen.LESSON_COMPETITORS.items():
        assert any(rival(demo["input"]) != demo["output"] for demo in demos), name


def test_100_lessons_per_band_survive_every_cyclic_query_rotation():
    for band in ("easy", "medium", "hard"):
        for lesson_index in range(100):
            digest = hashlib.sha256(
                f"cyclic-lesson:v1:{TASK_ID}:{band}:{lesson_index}".encode()
            ).hexdigest()
            seed = int(digest[:8], 16)
            pairs = []
            for offset in range(gen.EXAMPLES_NEEDED + 1):
                grid = gen.generate(seed, lesson_index + offset, difficulty=band)
                pairs.append({"input": grid, "output": reference_output(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                assert gen.lesson_identifiable(demos, query) == [], (
                    band,
                    lesson_index,
                    query_index,
                )
                for name, rival in gen.LESSON_COMPETITORS.items():
                    assert any(
                        rival(demo["input"]) != demo["output"] for demo in demos
                    ), (band, lesson_index, query_index, name)


@pytest.mark.parametrize(
    "mutation",
    ["unknown_color", "second_marker", "erase_red", "split_red", "clipped_stamp"],
)
def test_validator_rejects_destructive_mutations(mutation):
    grid = gen.generate(700, 3, grid_h=10, grid_w=15)
    if mutation == "unknown_color":
        grid[0][0] = 9
    elif mutation == "second_marker":
        blank = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 0)
        grid[blank[0]][blank[1]] = 1
    elif mutation == "erase_red":
        for r, c in cells(grid, 2):
            grid[r][c] = 0
    elif mutation == "split_red":
        blank = next(
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if value == 0 and all(abs(r - rr) + abs(c - cc) > 1 for rr, cc in cells(grid, 2))
        )
        grid[blank[0]][blank[1]] = 2
    elif mutation == "clipped_stamp":
        for r, c in cells(grid, 1):
            grid[r][c] = 0
        grid[-1][-1] = 1
    assert gen.self_check(grid)


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 15 for _ in range(10)], [[0] * 12 for _ in range(9)]],
)
def test_malformed_inputs_return_diagnostics_instead_of_raising(grid):
    assert gen.self_check(grid)


def test_cyclic_lesson_probe_writes_replayable_json(tmp_path):
    output = tmp_path / "cyclic.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(HOME / "workspace" / "cyclic_lesson_probe.py"),
            "--generator",
            str(HOME / "generator.py"),
            "--per-band",
            "2",
            "--out",
            str(output),
        ],
        check=False,
        text=True,
        capture_output=True,
        env=dict(os.environ, ARCPUZZLES_HOME=str(HOME.parents[1])),
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(output.read_text())
    assert report["status"] == "pass"
    assert report["counts"] == {
        "bands": 3,
        "lessons": 6,
        "pairs": 30,
        "rotations": 30,
        "ambiguous_rotations": 0,
        "errors": 0,
    }
    assert report["seed_recipe"].startswith("sha256('cyclic-lesson:v1:")
    assert report["generator_sha256"]
    assert report["competitors"] == sorted(gen.LESSON_COMPETITORS)


def test_keyed_rng_is_independent_of_python_hash_seed():
    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator(sys.argv[2]).generate(31,8,difficulty='hard')))"
    )
    outputs = []
    for hash_seed in ("1", "991"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        outputs.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace"), str(HOME / "generator.py")],
                text=True,
                env=env,
            )
        )
    assert outputs[0] == outputs[1]


def test_real_racket_rule_matches_independent_oracle_when_available():
    try:
        from arc_repl.racket_bridge import racket_runtime_status
        from arcpuzzles import Catalog
    except ImportError as exc:
        pytest.skip(str(exc))
    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(8300, index, difficulty="hard") for index in range(12)]
    result = Catalog().apply(TASK_ID, grids, timeout=180)
    assert result["rule_hash_matches_catalog"]
    assert [item["output"] for item in result["results"]] == [reference_output(grid) for grid in grids]
