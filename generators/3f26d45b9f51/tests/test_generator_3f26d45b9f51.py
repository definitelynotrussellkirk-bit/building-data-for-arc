from __future__ import annotations

import hashlib
import importlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


gen = importlib.import_module("puzzle_generators.per_puzzle.3f26d45b9f51.generator")


def _pair(seed: int, index: int, band: str = "medium"):
    grid = gen.generate(seed, index, difficulty=band)
    return {"input": grid, "output": gen._solve_python(grid)}


def _nearest_pair_counterexample():
    fixture = Path(__file__).resolve().parents[1] / "counterexamples" / "nearest_pair_only.json"
    return json.loads(fixture.read_text())["input"]


def test_canonical_inputs_are_accepted_and_python_mirror_matches_outputs():
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    assert len(pairs) == 4
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen._solve_python(pair["input"]) == pair["output"]


def test_exact_axes_round_trip_full_declared_domain_in_every_band():
    for band in ("easy", "medium", "hard"):
        for K in (7, 8, 9):
            for n_colors in (2, 3, 4):
                grid = gen.generate(31, 7, difficulty=band, K=K, n_colors=n_colors)
                assert gen.observe_overrides(grid) == {"K": K, "n_colors": n_colors}


def test_unknown_override_is_rejected():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, difficulty="easy", typo_axis=7)


@pytest.mark.parametrize(
    ("axis", "value"),
    [
        ("K", "7"),
        ("K", 7.5),
        ("K", True),
        ("n_colors", "3"),
        ("n_colors", 2.9),
        ("n_colors", False),
    ],
)
def test_exact_integer_axes_reject_coercible_non_integers(axis, value):
    kwargs = {"K": 7, "n_colors": 3, axis: value}
    with pytest.raises(TypeError, match="override must be an integer"):
        gen.generate(0, 0, difficulty="easy", **kwargs)


def test_generated_lessons_expose_all_decisive_semantic_cues():
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            grid = gen.generate(seed, seed + 2, difficulty=band)
            info = gen._analyze(grid)
            assert info["errors"] == []
            assert info["horizontal_lines"] >= 1
            assert info["vertical_lines"] >= 1
            assert info["dual_axis_colors"]
            assert info["unconnected_markers"]
            assert gen._w_three_collinear(grid)
            expected = gen._solve_python(grid)
            for rival in (
                "row_only",
                "column_only",
                "bounding_box_fill",
                "drop_unconnected_markers",
                "nearest_pair_only",
            ):
                assert gen.SEMANTIC_RIVALS[rival](grid) != expected


def test_nearest_pair_shortcut_fits_canonical_but_fails_exact_lawful_witness():
    pairs = canonical_pairs(gen.TASK_ID, root=find_root(__file__))
    rival = gen.SEMANTIC_RIVALS["nearest_pair_only"]
    assert all(rival(pair["input"]) == pair["output"] for pair in pairs)

    grid = _nearest_pair_counterexample()
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid) == []
    assert gen._w_three_collinear(grid)
    assert rival(grid) != gen._solve_python(grid)


def test_every_three_demo_sliding_window_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = [_pair(100 + start, start + offset, band) for offset in range(3)]
            query = _pair(100 + start, start + 3, band)
            assert gen.lesson_identifiable(demos, query) == []


def test_declared_schedule_period_covers_every_deterministic_slot_branch():
    assert gen.LESSON_SCHEDULE_PERIOD == 12
    assert gen.SCHEDULE_PROFILES == tuple(range(12))
    for band in ("easy", "medium", "hard"):
        signatures = []
        for index in range(24):
            grid = gen.generate(17, index, difficulty=band)
            info = gen._analyze(grid)
            signatures.append((info["divider"], len(info["markers"])))
            assert gen.schedule_profile(17, index, band) == index % 12
        assert len(set(signatures[:12])) == 12
        assert signatures[:12] == signatures[12:]


def test_self_check_rejects_targeted_structural_impostors():
    base = gen.generate(7, 3, difficulty="medium", K=8, n_colors=3)

    broken_divider = [row[:] for row in base]
    broken_divider[2][0] = 0
    assert any("divider" in error for error in gen.self_check(broken_divider))

    torn_marker = [row[:] for row in base]
    info = gen._analyze(torn_marker)
    color, cells = next(iter(info["markers"].items()))
    row, col = cells[0]
    torn_marker[3 * row][3 * col] = 0
    assert any("uniform 2x2" in error for error in gen.self_check(torn_marker))

    identity = [[0] * 20 for _ in range(20)]
    for r in range(20):
        if r % 3 == 2:
            identity[r] = [8] * 20
    for c in range(20):
        if c % 3 == 2:
            for r in range(20):
                identity[r][c] = 8
    gen._place_2x2(identity, 1, 1, 2)
    gen._place_2x2(identity, 3, 4, 3)
    assert any("identity" in error for error in gen.self_check(identity))

    overlap = [[0] * 20 for _ in range(20)]
    for r in range(20):
        if r % 3 == 2:
            overlap[r] = [8] * 20
    for c in range(20):
        if c % 3 == 2:
            for r in range(20):
                overlap[r][c] = 8
    gen._place_2x2(overlap, 2, 1, 2)
    gen._place_2x2(overlap, 2, 5, 2)
    gen._place_2x2(overlap, 0, 3, 3)
    gen._place_2x2(overlap, 4, 3, 3)
    assert any("overlap" in error for error in gen.self_check(overlap))


def test_semantic_probe_runs_directly_without_packet_wrapper(tmp_path):
    script = Path(__file__).resolve().parents[1] / "workspace" / "semantic_probe.py"
    output = tmp_path / "semantic-probe.json"
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, str(script), "--out", str(output), "--seeds", "1"],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(output.read_text())
    assert report["generator_sha256"] == hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
    assert report["axis_stress"]["cases"] == 324
    assert report["axis_stress"]["failures"] == []



def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    random.seed(9191)
    before = random.getstate()
    first = gen.generate(55, 6, difficulty="hard")
    after = random.getstate()
    second = gen.generate(55, 6, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
