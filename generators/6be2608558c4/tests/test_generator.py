from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import sys

import pytest

# Portable bootstrap: direct packet checkout and staged task-test runtime.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "6be2608558c4"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = (
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
    )
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", SOURCE)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)


def _component_cells(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    work = deepcopy(grid)
    for row in range(min(5, len(work))):
        for col in range(min(5, len(work[0]))):
            work[row][col] = 0
    height, width = len(work), len(work[0])
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for start_row in range(height):
        for start_col in range(width):
            if work[start_row][start_col] == 0 or (start_row, start_col) in seen:
                continue
            stack = [(start_row, start_col)]
            seen.add((start_row, start_col))
            cells: list[tuple[int, int]] = []
            while stack:
                row, col = stack.pop()
                cells.append((row, col))
                for next_row, next_col in (
                    (row - 1, col),
                    (row + 1, col),
                    (row, col - 1),
                    (row, col + 1),
                ):
                    if not (0 <= next_row < height and 0 <= next_col < width):
                        continue
                    if (next_row, next_col) in seen:
                        continue
                    if work[next_row][next_col] == 0:
                        continue
                    seen.add((next_row, next_col))
                    stack.append((next_row, next_col))
            components.append(sorted(cells))
    return components


def _shape(cells: list[tuple[int, int]]) -> tuple[frozenset[tuple[int, int]], int, int]:
    min_row = min(row for row, _ in cells)
    min_col = min(col for _, col in cells)
    normalized = frozenset((row - min_row, col - min_col) for row, col in cells)
    height = max(row for row, _ in normalized) + 1
    width = max(col for _, col in normalized) + 1
    return normalized, height, width


def _exemplar_shape(grid: list[list[int]]) -> tuple[frozenset[tuple[int, int]], int, int]:
    cells = [
        (row, col)
        for row in range(5)
        for col in range(5)
        if grid[row][col] != 0
    ]
    return _shape(cells)


def _independent_rule(grid: list[list[int]]) -> list[list[int]]:
    exemplar, _, _ = _exemplar_shape(grid)
    matches = [cells for cells in _component_cells(grid) if _shape(cells)[0] == exemplar]
    assert len(matches) == 1
    normalized, height, width = _shape(matches[0])
    return [
        [2 if (row, col) in normalized else 0 for col in range(width)]
        for row in range(height)
    ]


def _labeled(grid: list[list[int]]) -> dict[str, list[list[int]]]:
    return {"input": grid, "output": _independent_rule(grid)}


def test_contract_metadata_is_current_and_minimal():
    assert gen.RULE_HASH == "11381854d14b"
    assert gen.VERSION == "3.0.0"
    assert gen.EXAMPLES_NEEDED == 3
    assert tuple(gen.SCHEDULE_PROFILES) == (0, 1, 2)
    assert set(gen.AXES) == {"grid_h", "grid_w", "exemplar_size"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_unknown_retired_badly_typed_and_out_of_range_overrides_fail_loudly():
    bad = (
        {"typo_axis": 1},
        {"texture": "warm"},
        {"grid_h": True},
        {"grid_w": "13"},
        {"exemplar_size": 4.0},
        {"grid_h": 10},
        {"grid_h": 13},
        {"grid_w": 12},
        {"grid_w": 16},
        {"exemplar_size": 3},
        {"exemplar_size": 7},
    )
    for overrides in bad:
        with pytest.raises((TypeError, ValueError)):
            gen.generate(0, 0, **overrides)


def test_all_canonical_pairs_are_owned_and_match_an_independent_oracle():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        original = deepcopy(pair["input"])
        assert gen.self_check(original) == []
        assert gen.strict_canonical_like(original) == []
        assert _independent_rule(original) == pair["output"]
        assert gen.rule_mirror(original) == pair["output"]
        assert original == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    (
        {"grid_h": 11, "grid_w": 13, "exemplar_size": 4},
        {"grid_h": 12, "grid_w": 15, "exemplar_size": 6},
    ),
)
def test_every_declared_override_is_exact_observable_and_global(band, requested):
    grid = gen.generate(8128, 17, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert _independent_rule(grid) == gen.rule_mirror(grid)


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_constructive_curriculum_requires_exact_shape_not_position_or_signature(band):
    for seed in (0, 17, 99173):
        for sample_index in range(12):
            grid = gen.generate(seed, sample_index, difficulty=band)
            assert gen.self_check(grid) == []
            assert grid == gen.generate(seed, sample_index, difficulty=band)

            exemplar, ex_h, ex_w = _exemplar_shape(grid)
            components = _component_cells(grid)
            assert len(components) == 3
            shapes = [_shape(cells) for cells in components]
            assert all((len(shape), h, w) == (len(exemplar), ex_h, ex_w)
                       for shape, h, w in shapes)
            matches = [index for index, (shape, _, _) in enumerate(shapes)
                       if shape == exemplar]
            assert matches == [gen.schedule_profile(seed, sample_index, band)]
            assert len({shape for shape, _, _ in shapes}) == 3

            intended = gen.rule_mirror(grid)
            assert intended == _independent_rule(grid)
            for name, witness in gen.SEMANTIC_WITNESSES.items():
                if witness(grid):
                    assert any(
                        gen.SEMANTIC_RIVALS[rival](grid) != intended
                        for rival in gen.WITNESS_RIVALS[name]
                    )


def test_every_three_demo_window_and_every_query_rotation_refutes_all_rivals():
    for band in ("easy", "medium", "hard"):
        for seed in (0, 19, 8731):
            for start in range(9):
                lesson = [
                    _labeled(gen.generate(seed, start + offset, difficulty=band))
                    for offset in range(4)
                ]
                for query_index in range(4):
                    query = lesson[query_index]
                    demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                    assert gen.lesson_identifiable(demos, query) == []
                    for rival in gen.LESSON_COMPETITORS.values():
                        survives = all(rival(pair["input"]) == pair["output"] for pair in demos)
                        assert not (survives and rival(query["input"]) != query["output"])


def test_self_check_rejects_destructive_mutations_and_minimal_impostors():
    grid = gen.generate(71, 2, difficulty="medium")
    assert gen.self_check(grid) == []

    blank = [[0 for _ in row] for row in grid]
    no_exemplar = deepcopy(grid)
    for row in range(5):
        for col in range(5):
            no_exemplar[row][col] = 0

    missing_component = deepcopy(grid)
    body_colors = {
        grid[row][col]
        for row, col in sum(_component_cells(grid), [])
    }
    removed_color = min(body_colors)
    for row in range(len(missing_component)):
        for col in range(len(missing_component[0])):
            if missing_component[row][col] == removed_color:
                missing_component[row][col] = 0

    extra_reserved_color = deepcopy(grid)
    extra_reserved_color[-1][-1] = 2

    impostors = [
        blank,
        no_exemplar,
        missing_component,
        extra_reserved_color,
        [[0] * 13 for _ in range(11)],
        [[1] * 13 for _ in range(11)],
    ]
    assert all(gen.self_check(candidate) for candidate in impostors)


@pytest.mark.parametrize("malformed", [None, [], [[]], [[0], [0, 1]], [[True] * 13 for _ in range(11)]])
def test_self_check_returns_diagnostics_instead_of_raising(malformed):
    assert gen.self_check(malformed)


def _decoy_shape_distance(grid: list[list[int]]) -> int:
    exemplar, _, _ = _exemplar_shape(grid)
    shapes = [_shape(cells)[0] for cells in _component_cells(grid)]
    return sum(len(exemplar.symmetric_difference(shape)) for shape in shapes if shape != exemplar)


def test_difficulty_controls_decoy_similarity_without_narrowing_axes():
    strict_improvements = 0
    for seed in range(12):
        requested = {"grid_h": 11, "grid_w": 13, "exemplar_size": 6}
        easy = gen.generate(seed, 4, difficulty="easy", **requested)
        hard = gen.generate(seed, 4, difficulty="hard", **requested)
        assert gen.observe_overrides(easy) == requested
        assert gen.observe_overrides(hard) == requested
        easy_distance = _decoy_shape_distance(easy)
        hard_distance = _decoy_shape_distance(hard)
        assert easy_distance >= hard_distance
        strict_improvements += easy_distance > hard_distance
    assert strict_improvements >= 1


def _load_reference_probe():
    probe_path = ROOT / "generators" / TASK_ID / "workspace" / "reference_probe.py"
    assert probe_path.is_file(), "portable schedule/rival probe is missing"
    spec = importlib.util.spec_from_file_location(f"probe_{TASK_ID}", probe_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_reference_probe_exhausts_windows_and_query_rotations():
    probe = _load_reference_probe()
    report = probe.audit_schedule(gen, seeds=(0,), starts=range(3), bands=("easy",))
    assert report["issues"] == []
    assert report["lessons"] == 3
    assert report["rotations"] == 12
    assert report["unique_inputs"] == 6
    assert set(report["profile_counts"]) == {"0", "1", "2"}


def test_reference_probe_retains_a_fixed_middle_counterexample():
    probe = _load_reference_probe()
    witness = probe.fixed_middle_counterexample(gen, seed=0, band="medium")
    assert witness["truth"] != witness["rival_output"]
    assert witness["rival"] == "always_middle_component"
    assert gen.self_check(witness["input"]) == []
