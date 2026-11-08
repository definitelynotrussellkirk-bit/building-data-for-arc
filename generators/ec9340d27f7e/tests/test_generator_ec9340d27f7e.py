from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

TASK = "ec9340d27f7e"
ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

SPEC = importlib.util.spec_from_file_location(
    f"review_{TASK}", ROOT / "generators" / TASK / "generator.py"
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CANONICAL = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"


def _norm(grid):
    return [
        [int(ch) for ch in row] if isinstance(row, str) else list(row)
        for row in grid
    ]


def canonical_row():
    matches = []
    for line in CANONICAL.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK:
            matches.append(row)
    assert len(matches) == 1
    return matches[0]


def canonical_pairs():
    row = canonical_row()
    tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [*row["train"], *tests]


def independent_oracle(grid):
    values = _norm(grid)
    out = [row[:] for row in values]
    for r, row in enumerate(values):
        for c in range(1, len(row) - 1):
            if row[c] == 0 and row[c - 1] != 0 and row[c - 1] == row[c + 1]:
                out[r][c] = row[c - 1]
    return out


def pair(grid):
    return {"input": grid, "output": independent_oracle(grid)}


def frozen(grid):
    return tuple(map(tuple, grid))


def test_rule_pin_and_exact_axis_surface_are_minimal():
    program = canonical_row()["program_solution"]
    normalized = " ".join(program.split())
    assert hashlib.sha256(normalized.encode()).hexdigest()[:12] == MODULE.RULE_HASH
    assert MODULE.VERSION == "3.0.0"
    assert set(MODULE.AXES) == {"grid_h", "grid_w", "n_gaps"}
    assert MODULE.HELPFUL_TEXTURES == ()
    assert MODULE.DEGENERATE_TEXTURES == ()
    assert MODULE.INCOMPATIBLE_OVERRIDE_COMBINATIONS == ()


def test_every_canonical_input_is_owned_and_oracle_exact():
    signatures = {
        (6, 8): (3, [1, 1, 1]),
        (5, 9): (5, [1, 1, 3]),
        (7, 7): (3, [1, 1, 1]),
        (6, 10): (4, [1, 1, 2]),
    }
    for raw in canonical_pairs():
        grid, expected = _norm(raw["input"]), _norm(raw["output"])
        analysis = MODULE._analysis(grid)
        dims = (len(grid), len(grid[0]))
        assert MODULE.self_check(grid) == []
        assert MODULE.strict_canonical_like(grid) == []
        assert MODULE.rule_mirror(grid) == independent_oracle(grid) == expected
        assert analysis["target_count"] == signatures[dims][0]
        assert sorted(count for count in analysis["row_target_counts"] if count) == signatures[dims][1]


def test_default_schedule_covers_all_canonical_profiles_and_contrast_bundles():
    expected_profiles = set(MODULE.SCHEDULE_PROFILES)
    seen_profiles = set()
    strict_dims = set()
    contrast_grids = []
    all_grids = []
    for difficulty in (None, "easy", "medium", "hard"):
        for sample_index in range(32):
            seed = 100_000 + 101 * sample_index
            grid = MODULE.generate(seed, sample_index, difficulty=difficulty)
            all_grids.append(grid)
            seen_profiles.add(MODULE.schedule_profile(seed, sample_index, difficulty))
            assert MODULE.self_check(grid) == []
            assert MODULE.rule_mirror(grid) == independent_oracle(grid)
            analysis = MODULE._analysis(grid)
            assert MODULE.observe_overrides(grid) == {
                "grid_h": analysis["height"],
                "grid_w": analysis["width"],
                "n_gaps": analysis["target_count"],
            }
            if MODULE.strict_canonical_like(grid) == []:
                strict_dims.add((analysis["height"], analysis["width"]))
            else:
                contrast_grids.append(grid)
    assert seen_profiles == expected_profiles
    assert strict_dims == {(6, 8), (5, 9), (7, 7), (6, 10)}
    assert len(contrast_grids) == len(all_grids) // 2
    assert len({frozen(grid) for grid in all_grids}) >= len(all_grids) * 0.9

    required = {
        "multiple_targets",
        "multiple_target_colors",
        "unequal_horizontal_control",
        "vertical_equal_control",
        "long_equal_gap_control",
        "blocked_midpoint_control",
        "same_color_opposite_fate",
    }
    for grid in contrast_grids:
        fired = {name for name, pred in MODULE.SEMANTIC_WITNESSES.items() if pred(grid)}
        assert required <= fired
        intended = MODULE.rule_mirror(grid)
        for rival in MODULE.SEMANTIC_RIVALS.values():
            assert rival(grid) != intended


def test_all_cartesian_exact_axis_boundaries_are_honored_and_observable():
    for h in (5, 8):
        for w in (7, 10):
            for n_gaps in (3, 5):
                for difficulty in (None, "easy", "medium", "hard"):
                    grid = MODULE.generate(
                        7301,
                        19,
                        difficulty=difficulty,
                        grid_h=h,
                        grid_w=w,
                        n_gaps=n_gaps,
                    )
                    assert MODULE.self_check(grid) == []
                    assert MODULE.observe_overrides(grid) == {
                        "grid_h": h,
                        "grid_w": w,
                        "n_gaps": n_gaps,
                    }
                    assert MODULE.rule_mirror(grid) == independent_oracle(grid)


@pytest.mark.parametrize(
    "kwargs, error_type",
    [
        ({"unknown_axis": 1}, TypeError),
        ({"grid_h": 4}, ValueError),
        ({"grid_w": 11}, ValueError),
        ({"n_gaps": 2}, ValueError),
        ({"difficulty": "expert"}, ValueError),
    ],
)
def test_unknown_and_out_of_range_controls_fail_closed(kwargs, error_type):
    with pytest.raises(error_type):
        MODULE.generate(1, 0, **kwargs)


def test_each_three_demo_window_identifies_the_rule():
    # The semantic gate consumes consecutive sample indexes.  Every such
    # three-demo window must contain a complete contrast bundle.
    for difficulty in ("easy", "medium", "hard"):
        for start in range(24):
            pairs = []
            for offset in range(4):
                grid = MODULE.generate(50_000 + start, start + offset, difficulty=difficulty)
                pairs.append(pair(grid))
            assert MODULE.lesson_identifiable(pairs[:3], pairs[3]) == []


def test_named_canonical_shortcuts_really_fit_canonical_and_are_refuted_generated():
    canonical = canonical_pairs()
    for name, shortcut in MODULE.CANONICAL_SHORTCUTS.items():
        assert name in MODULE.SEMANTIC_RIVALS
        assert all(shortcut(_norm(item["input"])) == _norm(item["output"]) for item in canonical)
        assert any(
            shortcut(MODULE.generate(90_000 + index, 8 * index + 1))
            != MODULE.rule_mirror(MODULE.generate(90_000 + index, 8 * index + 1))
            for index in range(8)
        )


def test_determinism_fresh_returns_and_global_random_isolation():
    random.seed(123_456)
    before = random.getstate()
    first = MODULE.generate(731, 19, difficulty="hard")
    assert random.getstate() == before
    second = MODULE.generate(731, 19, difficulty="hard")
    assert first == second
    assert first is not second and first[0] is not second[0]
    original = second[0][0]
    first[0][0] = 9
    assert second[0][0] == original
    assert MODULE.generate(731, 20, difficulty="hard") != second


def test_self_check_rejects_structural_mutations():
    grid = MODULE.generate(404, 1)
    broken = [row[:] for row in grid]
    # Delete one endpoint from a target.  The teaching grammar must notice the
    # missing target/control support rather than merely accepting a rectangle.
    r, c = MODULE._analysis(grid)["targets"][0]
    broken[r][c - 1] = 0
    assert MODULE.self_check(broken)

    malformed = [row[:] for row in grid]
    malformed[0] = malformed[0][:-1]
    assert MODULE.self_check(malformed)


def test_semantic_probe_emits_reusable_machine_readable_report(tmp_path):
    import subprocess

    probe = ROOT / "generators" / TASK / "workspace" / "semantic_probe.py"
    report_path = tmp_path / "probe.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(probe),
            "--samples-per-band",
            "8",
            "--json-out",
            str(report_path),
        ],
        cwd=ROOT,
        env={**__import__("os").environ, "PYTHONPATH": str(RUNTIME)},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["task_id"] == TASK
    assert report["draws"] == 24
    assert set(report["profile_counts"]) == set(MODULE.SCHEDULE_PROFILES)
    assert report["strict"]["count"] > 0
    assert report["contrast"]["count"] > 0
    assert report["lesson_failures"] == []
    assert all(count > 0 for count in report["witness_counts"].values())
    assert all(count > 0 for count in report["rival_disagreements"].values())
