"""Task-local regressions for the 0d27a69b5a98 symmetry curriculum."""
from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

HOME = Path(__file__).resolve().parents[1]
MODULE_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
spec = importlib.util.spec_from_file_location("generator_under_test", MODULE_PATH)
assert spec and spec.loader
GEN = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GEN)

TASK_ID = "0d27a69b5a98"


def _normalized_rule_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _canonical_rule_source() -> str:
    root = find_root(__file__)
    path = next(
        candidate
        for candidate in (
            root / "data/canonical/puzzles.jsonl",
            root / "shared/data/canonical/puzzles.jsonl",
        )
        if candidate.is_file()
    )
    import json

    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical row missing")


def _axis(grid):
    height, width = len(grid), len(grid[0])
    rows = [r for r, row in enumerate(grid) if all(value == 9 for value in row)]
    cols = [c for c in range(width) if all(grid[r][c] == 9 for r in range(height))]
    assert len(rows) + len(cols) == 1
    return ("horizontal", rows[0]) if rows else ("vertical", cols[0])


def _object_cells(grid):
    return [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]


def _side_set(grid):
    orientation, axis = _axis(grid)
    if orientation == "vertical":
        return {"primary" if c < axis else "secondary" for r, c, _ in _object_cells(grid)}
    return {"primary" if r < axis else "secondary" for r, c, _ in _object_cells(grid)}


def test_rule_pin_and_python_oracle_match_every_labeled_canonical_pair():
    assert GEN.RULE_HASH == _normalized_rule_hash(_canonical_rule_source()) == "84d7043f128c"
    for pair in canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True):
        assert GEN.self_check(pair["input"]) == []
        assert GEN._intended_output(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("orientation", ["vertical", "horizontal"])
@pytest.mark.parametrize("n_colors", [1, 2, 3])
def test_exact_overrides_are_observable_in_every_band(band, orientation, n_colors):
    grid = GEN.generate(
        71,
        2,
        difficulty=band,
        grid_h=7,
        grid_w=8,
        axis_orientation=orientation,
        n_colors=n_colors,
    )
    assert GEN.self_check(grid) == []
    assert GEN.observe_overrides(grid) == {
        "grid_h": 7,
        "grid_w": 8,
        "axis_orientation": orientation,
        "n_colors": n_colors,
    }


@pytest.mark.parametrize(
    "key,value",
    [
        ("unknown_axis", 1),
        ("grid_h", 6),
        ("grid_h", True),
        ("grid_w", 11),
        ("n_colors", 0),
        ("n_colors", 4),
        ("n_colors", 2.0),
        ("axis_orientation", "diagonal"),
    ],
)
def test_invalid_or_unknown_overrides_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError, KeyError)):
        GEN.generate(0, 0, **{key: value})


def test_four_slot_schedule_covers_both_directions_and_repeats_bilateral_witness():
    grids = [
        GEN.generate(
            13,
            index,
            grid_h=9,
            grid_w=10,
            axis_orientation="vertical",
            n_colors=2,
        )
        for index in range(4)
    ]
    assert [_side_set(grid) for grid in grids] == [
        {"primary"},
        {"primary", "secondary"},
        {"secondary"},
        {"primary", "secondary"},
    ]
    assert [GEN.schedule_profile(13, index) for index in range(4)] == list(GEN.SCHEDULE_PROFILES)
    assert all(GEN._intended_output(grid) != grid for grid in grids)
    assert GEN._rival_primary_only(grids[2]) != GEN._intended_output(grids[2])
    assert GEN._rival_empty_side_only(grids[1]) != GEN._intended_output(grids[1])
    assert GEN._rival_empty_side_only(grids[3]) != GEN._intended_output(grids[3])


@pytest.mark.parametrize("start", range(9))
def test_every_three_consecutive_demonstrations_refute_declared_shortcuts(start):
    demos = []
    for index in range(start, start + GEN.EXAMPLES_NEEDED):
        grid = GEN.generate(101, index, grid_h=10, grid_w=9, n_colors=2)
        demos.append({"input": grid, "output": GEN._intended_output(grid)})
    query_grid = GEN.generate(101, start + GEN.EXAMPLES_NEEDED, grid_h=10, grid_w=9, n_colors=2)
    query = {"input": query_grid, "output": GEN._intended_output(query_grid)}
    assert GEN.lesson_identifiable(demos, query) == []
    for rival in GEN.LESSON_COMPETITORS.values():
        assert not all(rival(pair["input"]) == pair["output"] for pair in demos)


@pytest.mark.parametrize("start", range(8))
def test_every_query_rotation_of_four_pair_window_refutes_declared_shortcuts(start):
    pairs = []
    for index in range(start, start + GEN.EXAMPLES_NEEDED + 1):
        grid = GEN.generate(303, index, grid_h=10, grid_w=9, n_colors=2)
        pairs.append({"input": grid, "output": GEN._intended_output(grid)})
    for query_index, query in enumerate(pairs):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        assert GEN.lesson_identifiable(demos, query) == []
        for rival in GEN.LESSON_COMPETITORS.values():
            assert not (
                all(rival(pair["input"]) == pair["output"] for pair in demos)
                and rival(query["input"]) != query["output"]
            )


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_generated_population_is_deterministic_lawful_and_nonidentity(band):
    for index in range(60):
        first = GEN.generate(2026, index, difficulty=band)
        second = GEN.generate(2026, index, difficulty=band)
        assert first == second
        assert GEN.self_check(first, difficulty=band) == []
        output = GEN._intended_output(first)
        assert output != first
        for r, c, value in _object_cells(first):
            assert output[r][c] == value


def test_declared_witnesses_are_real_counterexamples():
    secondary = GEN.generate(5, 2, grid_h=9, grid_w=10, n_colors=2)
    bilateral = GEN.generate(5, 1, grid_h=9, grid_w=10, n_colors=2)
    assert GEN.SEMANTIC_WITNESSES["secondary_source"](secondary)
    assert GEN.SEMANTIC_WITNESSES["bilateral_source"](bilateral)
    assert GEN._rival_primary_only(secondary) != GEN._intended_output(secondary)
    assert GEN._rival_empty_side_only(bilateral) != GEN._intended_output(bilateral)


def test_generation_is_independent_of_python_hash_seed():
    """Unordered side sets must not consume the layout RNG in a different order."""
    import json
    import subprocess
    import sys

    root = find_root(__file__)
    script = """
import importlib.util, json, os
path = os.environ['GENERATOR_UNDER_TEST']
spec = importlib.util.spec_from_file_location('hashseed_probe', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
print(json.dumps(module.generate(1, 1, difficulty='easy'), separators=(',', ':')))
"""
    outputs = []
    for hash_seed in ("1", "3"):
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = hash_seed
        env["GENERATOR_UNDER_TEST"] = str(MODULE_PATH)
        runtime_paths = [str(root / "shared/runtime"), str(root / "src")]
        env["PYTHONPATH"] = os.pathsep.join(runtime_paths + [env.get("PYTHONPATH", "")])
        result = subprocess.run(
            [sys.executable, "-c", script],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        outputs.append(json.loads(result.stdout))
    assert outputs[0] == outputs[1]


def test_retained_primary_only_counterexample_matches_racket_receipt():
    import json

    base = HOME / "counterexamples/review-d279da981a00a49e-primary-only"
    grid = json.loads((base / "input.json").read_text(encoding="utf-8"))
    oracle = json.loads((base / "python_oracle.json").read_text(encoding="utf-8"))
    rival = json.loads((base / "rival_primary_only.json").read_text(encoding="utf-8"))
    receipt = json.loads((base / "racket.json").read_text(encoding="utf-8"))
    metadata = json.loads((base / "metadata.json").read_text(encoding="utf-8"))

    assert GEN.generate(
        metadata["seed"],
        metadata["sample_index"],
        difficulty=metadata["difficulty"],
        **metadata["overrides"],
    ) == grid
    assert GEN.self_check(grid) == []
    assert GEN.SEMANTIC_WITNESSES[metadata["witness"]](grid)
    assert receipt["generator_sha256"] == hashlib.sha256(MODULE_PATH.read_bytes()).hexdigest()
    assert receipt["executed_rule_hash"] == GEN.RULE_HASH
    assert receipt["results"][0]["output"] == oracle == GEN._intended_output(grid)
    assert rival == GEN._rival_primary_only(grid)
    assert rival != oracle
