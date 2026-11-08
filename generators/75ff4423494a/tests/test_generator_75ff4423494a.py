"""Task-local regression tests for 75ff4423494a.

The independent oracle below mirrors the canonical rule from the public task
record; it intentionally does not call the generator's own analysis helpers.
"""
from __future__ import annotations

import copy
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "75ff4423494a"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gen
SPEC.loader.exec_module(gen)

CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    remaining = {
        (r, c) for r in range(h) for c in range(w) if grid[r][c] != 0
    }
    result = []
    while remaining:
        start = min(remaining)
        stack = [start]
        remaining.remove(start)
        component = []
        while stack:
            cell = stack.pop()
            component.append(cell)
            for dr, dc in CARDINAL:
                nxt = (cell[0] + dr, cell[1] + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    stack.append(nxt)
        result.append(component)
    return result


def independent_oracle(grid: list[list[int]]) -> list[list[int]]:
    """Exact independent mirror of the canonical Racket authority."""
    h, w = len(grid), len(grid[0])
    components = _components(grid)
    candidates = [
        cells
        for cells in components
        if len(cells) > 1 and any(grid[r][c] == 8 for r, c in cells)
    ]
    proto = sorted(
        candidates,
        key=lambda cells: (
            -len(cells),
            min(r for r, _ in cells),
            min(c for _, c in cells),
        ),
    )[0]
    top = min(r for r, _ in proto)
    left = min(c for _, c in proto)
    bottom = max(r for r, _ in proto)
    right = max(c for _, c in proto)
    template = [row[left : right + 1] for row in grid[top : bottom + 1]]
    origin = next(
        (r, c)
        for r, row in enumerate(template)
        for c, value in enumerate(row)
        if value == 8
    )
    abs_origin = (top + origin[0], left + origin[1])
    proto_set = set(proto)
    targets = [
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] == 8 and (r, c) not in proto_set
    ]
    output = [[0] * w for _ in range(h)]
    for anchor in [abs_origin, *targets]:
        shift_r = anchor[0] - origin[0]
        shift_c = anchor[1] - origin[1]
        for r, row in enumerate(template):
            for c, value in enumerate(row):
                if value == 0:
                    continue
                rr, cc = shift_r + r, shift_c + c
                if not (0 <= rr < h and 0 <= cc < w):
                    continue
                old = output[rr][cc]
                if old == 0:
                    output[rr][cc] = value
                elif old != value:
                    output[rr][cc] = 9
    return output


def _analysis(grid: list[list[int]]) -> dict:
    components = _components(grid)
    candidates = [
        cells
        for cells in components
        if len(cells) > 1 and any(grid[r][c] == 8 for r, c in cells)
    ]
    proto = sorted(
        candidates,
        key=lambda cells: (
            -len(cells),
            min(r for r, _ in cells),
            min(c for _, c in cells),
        ),
    )[0]
    proto_set = set(proto)
    targets = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 8 and (r, c) not in proto_set
    ]
    target_components = [set(cells) for cells in components if not set(cells) <= proto_set]
    payload = {grid[r][c] for r, c in proto if grid[r][c] != 8}
    return {
        "proto": proto_set,
        "targets": targets,
        "target_components": target_components,
        "payload": payload,
    }


def _pair(grid: list[list[int]]) -> dict:
    return {"input": grid, "output": independent_oracle(grid)}


def test_rule_pin_and_all_canonical_pairs_are_owned_exactly():
    assert gen.RULE_HASH == "0124781298a5"
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    for pair in pairs:
        source = copy.deepcopy(pair["input"])
        assert gen.self_check(source) == []
        assert gen.strict_canonical_like(source) == []
        assert independent_oracle(source) == pair["output"]
        assert gen.oracle_output(source) == pair["output"]
        assert source == pair["input"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize(
    "requested",
    [
        {"grid_h": 9, "grid_w": 10, "n_anchors": 1, "template_kind": "step5"},
        {"grid_h": 10, "grid_w": 11, "n_anchors": 2, "template_kind": "cross6"},
        {"grid_h": 12, "grid_w": 14, "n_anchors": 3, "template_kind": "hook6"},
    ],
)
def test_declared_overrides_are_exact_observable_and_global(band, requested):
    grid = gen.generate(8128, 17, difficulty=band, **requested)
    assert gen.observe_overrides(grid) == requested
    assert gen.self_check(grid) == []
    assert gen.oracle_output(grid) == independent_oracle(grid)


def test_invalid_and_unknown_overrides_fail_loudly():
    with pytest.raises((TypeError, ValueError), match="unknown override"):
        gen.generate(1, 0, typo_axis=2)
    for name, value in (
        ("grid_h", 8),
        ("grid_w", 15),
        ("n_anchors", 0),
        ("n_anchors", 4),
        ("template_kind", "not-a-template"),
        ("grid_h", True),
        ("n_anchors", 2.5),
    ):
        with pytest.raises((TypeError, ValueError)):
            gen.generate(1, 0, **{name: value})


def test_default_schedule_hits_canonical_profiles_and_missing_semantic_branches():
    canonical_profiles = {(9, 10, 4), (10, 11, 4), (9, 12, 4), (10, 10, 4)}
    for band_index, band in enumerate(("easy", "medium", "hard")):
        grids = [gen.generate(9000 + band_index, index, difficulty=band) for index in range(12)]
        observed_profiles = {
            (len(grid), len(grid[0]), len({value for row in grid for value in row}))
            for grid in grids
        }
        assert canonical_profiles <= observed_profiles
        assert all(gen.self_check(grid) == [] for grid in grids)
        assert all(gen.strict_canonical_like(grid) == [] for grid in grids)
        assert all(gen.oracle_output(grid) == independent_oracle(grid) for grid in grids)
        assert any(9 in {value for row in gen.oracle_output(grid) for value in row} for grid in grids)
        assert any(
            any(len(component) >= 2 for component in _analysis(grid)["target_components"])
            for grid in grids
        )
        assert all(_analysis(grid)["payload"] != {2, 3} for grid in grids)
        assert all(len(_analysis(grid)["targets"]) >= 2 for grid in grids)


def test_named_canonical_shortcuts_fit_public_pairs_and_generated_witnesses_refute_them():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name

    grids = [gen.generate(441, index, difficulty="medium") for index in range(12)]
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert any(rival(grid) != independent_oracle(grid) for grid in grids), name


def test_every_rotated_three_demo_window_identifies_all_declared_competitors():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(12):
            examples = [
                _pair(gen.generate(12000 + band_index, start + offset, difficulty=band))
                for offset in range(4)
            ]
            for query_index, query in enumerate(examples):
                demos = [
                    example
                    for index, example in enumerate(examples)
                    if index != query_index
                ]
                assert gen.lesson_identifiable(demos, query) == []


def test_self_check_rejects_malformed_or_semantically_ambiguous_inputs():
    valid = gen.generate(44, 3, difficulty="medium")
    ragged = copy.deepcopy(valid)
    ragged[-1].pop()
    illegal = copy.deepcopy(valid)
    illegal[0][0] = 10
    blank = [[0] * 10 for _ in range(9)]
    no_target = copy.deepcopy(valid)
    analysis = _analysis(no_target)
    for r, c in analysis["targets"]:
        no_target[r][c] = 0
    tied_proto = copy.deepcopy(valid)
    # Add a competing six-cell all-8 component when a blank 2x3 patch exists.
    placed = False
    for r in range(len(tied_proto) - 1):
        for c in range(len(tied_proto[0]) - 2):
            cells = {(r + dr, c + dc) for dr in range(2) for dc in range(3)}
            if all(tied_proto[rr][cc] == 0 for rr, cc in cells):
                for rr, cc in cells:
                    tied_proto[rr][cc] = 8
                placed = True
                break
        if placed:
            break
    for grid in (ragged, illegal, blank, no_target, tied_proto):
        errors = gen.self_check(grid)
        assert isinstance(errors, list) and errors
        assert all(isinstance(error, str) and error for error in errors)


def test_replay_is_fresh_and_global_random_state_is_untouched():
    random.seed(321)
    before = random.getstate()
    first = gen.generate(404, 5, difficulty="hard")
    after = random.getstate()
    second = gen.generate(404, 5, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 8 if first[0][0] != 8 else 7
    assert first != second


def test_real_racket_authority_matches_independent_oracle_on_generated_conflicts():
    from arcpuzzles import Catalog

    grids = [
        gen.generate(51000 + band_index, index, difficulty=band)
        for band_index, band in enumerate(("easy", "medium", "hard"))
        for index in range(6)
    ]
    receipt = Catalog(ROOT).apply(TASK_ID, grids, reference="canonical", timeout=180)
    assert receipt["rule_hash_matches_catalog"]
    assert [item["output"] for item in receipt["results"]] == [
        independent_oracle(grid) for grid in grids
    ]
