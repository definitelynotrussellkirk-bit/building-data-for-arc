from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from puzzle_generators.runner import _apply_rule, _open_bridge_with_rule
from reviewer_support import canonical_pairs, find_root

TASK_ID = "c5c5f3f84f12"
TEST_FILE = Path(__file__).resolve()
ROOT = find_root(TEST_FILE)


def _load_generator():
    package_name = f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
    try:
        return importlib.import_module(package_name)
    except ModuleNotFoundError:
        path = TEST_FILE.parents[1] / "generator.py"
        spec = importlib.util.spec_from_file_location(package_name, path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[package_name] = module
        spec.loader.exec_module(module)
        return module


GEN = _load_generator()


def _canonical_row() -> dict:
    candidates = (
        ROOT / "data/canonical/puzzles.jsonl",
        ROOT / "shared/data/canonical/puzzles.jsonl",
    )
    path = next(path for path in candidates if path.is_file())
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row missing")



def _callable_rule(source: str) -> str:
    """Wrap this task's body-form rule without depending on runtime scripts."""
    body = strip_rule_wrapper(strip_line_comments(source))
    return f"(lambda (g) (let* ((h (rows g)) (w (cols g))) {body}))"

def _normalized_hash(source: str) -> str:
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _bank_row() -> dict:
    candidates = (
        ROOT / "data/base/solutions/banks/53ccebf2a36f/M121__c5c5f3f84f12.json",
        ROOT / "shared/data/base/solutions/banks/53ccebf2a36f/M121__c5c5f3f84f12.json",
    )
    path = next(path for path in candidates if path.is_file())
    return json.loads(path.read_text(encoding="utf-8"))


def _corner_name(grid: list[list[int]], color: int = 1) -> str:
    h, w = len(grid), len(grid[0])
    by_pos = {
        (0, 0): "tl",
        (0, w - 1): "tr",
        (h - 1, w - 1): "br",
        (h - 1, 0): "bl",
    }
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    assert len(cells) == 1
    return by_pos[cells[0]]


def _pairs() -> list[dict]:
    return canonical_pairs(TASK_ID, root=ROOT)


def test_metadata_and_selected_rule_text_are_pinned_to_canonical_authority():
    row = _canonical_row()
    bank = _bank_row()
    target = bank["racket_target"]

    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.VERSION == "2.0.0"
    assert GEN.RULE_HASH == _normalized_hash(row["program_solution"])
    assert target["target_code"] == target["raw_code"] == row["program_solution"]
    assert _normalized_hash(target["target_code"]) == GEN.RULE_HASH


def test_all_canonical_inputs_validate_and_python_oracle_matches_outputs():
    pairs = _pairs()
    assert len(pairs) == 5
    observed_profiles = set()
    observed_corners = set()
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert GEN.self_check(source) == []
        assert GEN.strict_canonical_like(source) == []
        assert GEN._solve_official(source) == pair["output"]
        observed = GEN.observe_overrides(source)
        observed_profiles.add((observed["grid_h"], observed["grid_w"], len({v for row in source for v in row})))
        observed_corners.add(observed["corner_position"])
    assert observed_profiles == {(8, 8, 4), (8, 9, 4), (9, 8, 4), (9, 9, 4), (10, 10, 4)}
    assert observed_corners == {"tl", "tr", "br", "bl"}


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_schedule_is_lawful_four_color_and_rotation_complete(band: str):
    generated = [GEN.generate(1000 + i, i, difficulty=band) for i in range(20)]
    canonical_profiles = {(8, 8, 4), (8, 9, 4), (9, 8, 4), (9, 9, 4), (10, 10, 4)}

    for grid in generated:
        assert GEN.self_check(grid, difficulty=band) == []
        palette = {value for row in grid for value in row}
        assert len(palette) == 4
        assert {0, 1, 2} < palette
        distractor = next(iter(palette - {0, 1, 2}))
        assert 3 <= distractor <= 7
        assert sum(value == distractor for row in grid for value in row) == 1
        assert _corner_name(grid, 1) != _corner_name(grid, distractor)

    for start in range(0, 17):
        corners = {
            GEN.observe_overrides(grid)["corner_position"]
            for grid in generated[start : start + 4]
        }
        assert corners == {"tl", "tr", "br", "bl"}

    exact_hits = {
        (len(grid), len(grid[0]), len({value for row in grid for value in row}))
        for grid in generated
    } & canonical_profiles
    assert exact_hits


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize(
    "overrides",
    [
        {
            "grid_h": 8,
            "grid_w": 20,
            "corner_position": "tr",
            "distractor_color": 7,
            "blob_size": 8,
        },
        {
            "grid_h": 20,
            "grid_w": 8,
            "corner_position": "bl",
            "distractor_color": 3,
            "blob_size": 3,
        },
    ],
)
def test_every_declared_override_is_exact_and_observable(band: str, overrides: dict):
    grid = GEN.generate(20_000, 73, difficulty=band, **overrides)
    assert GEN.observe_overrides(grid) == overrides
    assert GEN.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize(
    "bad",
    [
        {"unknown_axis": 1},
        {"grid_h": True},
        {"grid_h": 7},
        {"grid_w": 21},
        {"corner_position": "center"},
        {"distractor_color": 2},
        {"distractor_color": 8},
        {"blob_size": 2},
        {"blob_size": 9},
    ],
)
def test_unknown_and_invalid_overrides_fail_closed(bad: dict):
    with pytest.raises((TypeError, ValueError)):
        GEN.generate(30_000, 0, **bad)


def test_shape_is_rotation_observable_for_all_four_control_corners():
    outputs = []
    for corner in ("tl", "tr", "br", "bl"):
        grid = GEN.generate(
            40_000,
            13,
            difficulty="medium",
            grid_h=12,
            grid_w=13,
            corner_position=corner,
            distractor_color=5,
            blob_size=8,
        )
        outputs.append(GEN._solve_official(grid))
    signatures = {tuple(tuple(row) for row in output) for output in outputs}
    assert len(signatures) == 4


def test_deterministic_fresh_results_and_global_rng_clean():
    random.seed(123456)
    before = random.getstate()
    first = GEN.generate(50_000, 9, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(50_000, 9, difficulty="hard")

    assert before == after
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_four_demo_lesson_refutes_every_declared_competitor():
    demos = []
    for index in range(4):
        grid = GEN.generate(60_000, index, difficulty="medium")
        demos.append({"input": grid, "output": GEN._solve_official(grid)})
    query_grid = GEN.generate(60_000, 4, difficulty="medium")
    query = {"input": query_grid, "output": GEN._solve_official(query_grid)}

    assert {
        GEN.observe_overrides(pair["input"])["corner_position"]
        for pair in demos
    } == {"tl", "tr", "br", "bl"}
    assert GEN.lesson_identifiable(demos, query) == []

    for name, rival in GEN.LESSON_COMPETITORS.items():
        assert any(rival(pair["input"]) != pair["output"] for pair in demos), name

    assert set(GEN.SEMANTIC_WITNESSES) == set(GEN.WITNESS_RIVALS)
    witnessed = {
        name
        for name, predicate in GEN.SEMANTIC_WITNESSES.items()
        if any(predicate(pair["input"]) for pair in demos)
    }
    assert witnessed == set(GEN.SEMANTIC_WITNESSES)


def test_mutations_that_destroy_roles_are_rejected():
    source = copy.deepcopy(_pairs()[0]["input"])
    assert GEN.self_check(source) == []

    no_distractor = copy.deepcopy(source)
    no_distractor[-1][-1] = 0
    assert GEN.self_check(no_distractor)

    duplicate_blue = copy.deepcopy(source)
    duplicate_blue[0][-1] = 1
    assert GEN.self_check(duplicate_blue)

    interior_blue = copy.deepcopy(source)
    interior_blue[0][0] = 0
    interior_blue[1][1] = 1
    assert GEN.self_check(interior_blue)

    no_red = copy.deepcopy(source)
    for row in no_red:
        for index, value in enumerate(row):
            if value == 2:
                row[index] = 0
    assert GEN.self_check(no_red)

    repeated_distractor = copy.deepcopy(source)
    repeated_distractor[-1][-2] = 6
    assert GEN.self_check(repeated_distractor)


def test_racket_oracle_matches_canonical_and_generated_inputs_without_mutation():
    bridge, fn_name = _open_bridge_with_rule(_callable_rule(_canonical_row()["program_solution"]))
    try:
        pairs = _pairs()
        for pair in pairs:
            source = copy.deepcopy(pair["input"])
            before = copy.deepcopy(source)
            assert _apply_rule(bridge, fn_name, source) == pair["output"]
            assert source == before

        grids = [
            GEN.generate(70_000 + i, i, difficulty=band)
            for band in ("easy", "medium", "hard")
            for i in range(8)
        ]
        for grid in grids:
            before = copy.deepcopy(grid)
            assert _apply_rule(bridge, fn_name, grid) == GEN._solve_official(grid)
            assert grid == before

        first, last = grids[0], grids[-1]
        first_output = _apply_rule(bridge, fn_name, first)
        _apply_rule(bridge, fn_name, last)
        assert _apply_rule(bridge, fn_name, first) == first_output
    finally:
        bridge.shutdown()


def test_workspace_curriculum_probe_covers_cyclic_queries_and_dynamic_rivals():
    probe_path = TEST_FILE.parents[1] / "workspace" / "probe_curriculum.py"
    assert probe_path.is_file(), "future-agent curriculum probe is missing"
    spec = importlib.util.spec_from_file_location(
        f"{TASK_ID}_curriculum_probe", probe_path
    )
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)

    report = probe.run_probe(gen=GEN, root=ROOT, seeds_per_band=1)
    assert report["status"] == "pass", report["errors"][:3]
    assert report["canonical"]["pairs_checked"] == 5
    assert report["cyclic_lessons"]["lessons_checked"] == 48
    assert report["cyclic_lessons"]["query_corner_counts"] == {
        "bl": 12,
        "br": 12,
        "tl": 12,
        "tr": 12,
    }
    assert report["cyclic_lessons"]["start_residue_counts"] == {
        "0": 12,
        "1": 12,
        "2": 12,
        "3": 12,
    }
    assert set(report["rivals"]["lesson_competitors"]) == set(
        GEN.LESSON_COMPETITORS
    )
    assert all(
        count == 48
        for count in report["rivals"]["refuted_lesson_counts"].values()
    )
    assert report["overrides"]["cases_checked"] == 24
