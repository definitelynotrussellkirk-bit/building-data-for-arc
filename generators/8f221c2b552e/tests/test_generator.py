"""Source-bound regression tests for generator 8f221c2b552e."""
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
    analyze,
    bridge_rows,
    canonical_pairs,
    cyclic_lessons,
    load_generator,
    profile,
)

import reference_probe as probe  # noqa: E402

gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
BANDS = (None, "easy", "medium", "hard")
CANONICAL_PROFILES = {profile(pair["input"]) for pair in canonical_pairs()}


def test_rule_hash_and_contract_surface_are_pinned():
    assert gen.RULE_HASH == "df008460a237"
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []
    assert set(gen.AXES) == {
        "grid_h",
        "grid_w",
        "n_pairs",
        "color_mode",
        "distractor_count",
        "span_style",
    }


@pytest.mark.parametrize("pair", canonical_pairs(), ids=lambda p: f"{p['split']}{p['pair_index']}")
def test_all_canonical_pairs_are_accepted_and_match_independent_rule(pair):
    before = deepcopy(pair["input"])
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert bridge_rows(pair["input"]) == pair["output"]
    assert pair["input"] == before


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize(
    "requested",
    [
        {
            "grid_h": 6,
            "grid_w": 8,
            "n_pairs": 2,
            "color_mode": "distinct",
            "distractor_count": 0,
            "span_style": "short",
        },
        {
            "grid_h": 10,
            "grid_w": 14,
            "n_pairs": 5,
            "color_mode": "shared",
            "distractor_count": 3,
            "span_style": "long",
        },
        {
            "grid_h": 6,
            "grid_w": 8,
            "n_pairs": 5,
            "color_mode": "distinct",
            "distractor_count": 3,
            "span_style": "mixed",
        },
    ],
)
def test_every_exact_override_combination_round_trips_in_every_band(band, requested):
    grid = gen.generate(8317, 19, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert analyze(grid) == requested
    assert gen.observe_overrides(grid) == requested
    assert bridge_rows(grid) != grid


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo_axis", 1),
        ("grid_h", 5),
        ("grid_h", 11),
        ("grid_w", 7),
        ("grid_w", 15),
        ("n_pairs", 1),
        ("n_pairs", 6),
        ("distractor_count", -1),
        ("distractor_count", 4),
        ("color_mode", "partial"),
        ("span_style", "medium"),
        ("grid_h", True),
        ("n_pairs", 2.0),
        ("distractor_count", "2"),
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(key, value):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **{key: value})


def test_unknown_difficulty_fails_loudly():
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(1, 0, difficulty="expert")


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_default_schedule_has_canonical_support_and_is_deterministic(band):
    exact = 0
    seen = set()
    modes = set()
    styles = set()
    for index in range(60):
        grid = gen.generate(41_000 + index, index, difficulty=band)
        assert grid == gen.generate(41_000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        observed = analyze(grid)
        modes.add(observed["color_mode"])
        styles.add(observed["span_style"])
        exact += profile(grid) in CANONICAL_PROFILES
        seen.add(json.dumps(grid, separators=(",", ":")))
    assert exact >= 12
    assert modes == {"distinct", "shared"}
    assert styles == {"short", "long", "mixed"}
    assert len(seen) >= 54


def test_canonical_shortcut_really_fits_canonical_and_generated_witness_refutes_it():
    assert set(gen.CANONICAL_SHORTCUTS) == {"global_exactly_two"}
    rival = gen.CANONICAL_SHORTCUTS["global_exactly_two"]
    assert all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
    for band in ("easy", "medium", "hard"):
        for index in range(1, 40, 2):
            grid = gen.generate(7200 + index, index, difficulty=band)
            assert gen.SEMANTIC_WITNESSES["reused_pair_color"](grid)
            assert rival(grid) != bridge_rows(grid)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_every_three_demo_sliding_lesson_refutes_declared_competitors(band):
    for demos, query in cyclic_lessons(gen, seed=90_000, band=band, starts=36):
        assert gen.lesson_identifiable(demos, query) == []
        for rival in gen.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos)


@pytest.mark.parametrize("band", ("easy", "medium", "hard"))
def test_cyclic_query_rotations_leave_three_identifying_demos(band):
    helper = getattr(probe, "cyclic_lesson_rotations", None)
    assert callable(helper), "reference probe must expose cyclic_lesson_rotations"
    cases = list(helper(gen, seed=91_000, band=band, starts=6, window_size=4))
    assert len(cases) == 24
    assert {case["query_index"] for case in cases} == {0, 1, 2, 3}
    for case in cases:
        assert len(case["demos"]) == 3
        assert gen.lesson_identifiable(case["demos"], case["query"]) == []
        for rival in gen.LESSON_COMPETITORS.values():
            assert any(rival(pair["input"]) != pair["output"] for pair in case["demos"])


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 8 for _ in range(6)],
        [[1, 1], [1, 1]],
        [[0] * 8 for _ in range(6)],
        [[1, 1, 0, 0, 0, 0, 0, 0] for _ in range(6)],
    ],
)
def test_validator_rejects_malformed_or_minimal_impostor_grids(bad):
    assert gen.self_check(bad)


@pytest.mark.parametrize(
    "mutation",
    ["fill_interior", "third_endpoint", "partial_color_reuse", "reuse_distractor", "too_many_distractors"],
)
def test_validator_rejects_task_specific_destructive_mutations(mutation):
    grid = gen.generate(
        144,
        8,
        grid_h=8,
        grid_w=12,
        n_pairs=3,
        color_mode="distinct",
        distractor_count=2,
        span_style="mixed",
    )
    rows = []
    distractor_cells = []
    for r, row in enumerate(grid):
        positions = [(c, value) for c, value in enumerate(row) if value]
        if len(positions) == 2 and positions[0][1] == positions[1][1]:
            rows.append((r, positions))
        else:
            distractor_cells.extend((r, c, value) for c, value in positions)
    if mutation == "fill_interior":
        r, positions = rows[0]
        grid[r][positions[0][0] + 1] = positions[0][1]
    elif mutation == "third_endpoint":
        r, positions = rows[0]
        free = next(c for c, value in enumerate(grid[r]) if value == 0 and c not in range(positions[0][0], positions[1][0] + 1))
        grid[r][free] = positions[0][1]
    elif mutation == "partial_color_reuse":
        r, positions = rows[1]
        grid[r][positions[0][0]] = rows[0][1][0][1]
        grid[r][positions[1][0]] = rows[0][1][0][1]
    elif mutation == "reuse_distractor":
        assert len(distractor_cells) >= 2
        r, c, _ = distractor_cells[1]
        grid[r][c] = distractor_cells[0][2]
    elif mutation == "too_many_distractors":
        pair_rows = {r for r, _ in rows}
        target = next(r for r in range(len(grid)) if r not in pair_rows)
        used = {value for row in grid for value in row}
        colors = [value for value in range(1, 10) if value not in used]
        zeros = [c for c, value in enumerate(grid[target]) if value == 0]
        for c, value in zip(zeros, colors):
            grid[target][c] = value
            if sum(value != 0 for row in grid for value in row) >= 2 * 3 + 4:
                break
    assert gen.self_check(grid)


def test_fresh_return_objects_and_python_hash_seed_independence():
    first = gen.generate(412, 111, difficulty="hard")
    second = gen.generate(412, 111, difficulty="hard")
    assert first == second and first is not second
    assert all(a is not b for a, b in zip(first, second))

    script = (
        "import json,sys;sys.path.insert(0,sys.argv[1]);"
        "from reference_probe import load_generator;"
        "print(json.dumps(load_generator().generate(412,111,difficulty='hard')))"
    )
    results = []
    for hash_seed in ("1", "901"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed, PYTHONDONTWRITEBYTECODE="1")
        results.append(
            subprocess.check_output(
                [sys.executable, "-B", "-c", script, str(HOME / "workspace")],
                env=env,
                text=True,
            )
        )
    assert results[0] == results[1]


def test_real_racket_authority_matches_independent_oracle_when_available():
    from arc_repl.racket_bridge import racket_runtime_status
    from reference_probe import racket_outputs

    status = racket_runtime_status()
    if not status["available"]:
        pytest.skip(status["reason"])
    grids = [pair["input"] for pair in canonical_pairs()]
    grids += [gen.generate(9981 + index, index, difficulty="hard") for index in range(12)]
    assert racket_outputs(grids) == [bridge_rows(grid) for grid in grids]


def test_qualification_cli_emits_machine_readable_clean_report(tmp_path):
    out = tmp_path / "qualification.json"
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            str(HOME / "workspace" / "qualification.py"),
            "--samples-per-band",
            "6",
            "--starts-per-band",
            "3",
            "--skip-racket",
            "--out",
            str(out),
        ],
        cwd=ROOT if (ROOT := HOME.parents[2]) else HOME,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(out.read_text())
    assert report["status"] == "pass"
    assert report["generated"]["total"] == 18
    assert report["cyclic_query_rotations"]["total"] == 36
    assert report["cyclic_query_rotations"]["failures"] == []
    assert report["racket_parity"]["status"] == "skipped"
