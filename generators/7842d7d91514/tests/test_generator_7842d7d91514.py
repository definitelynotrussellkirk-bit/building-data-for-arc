"""Focused source-bound contract tests for generator 7842d7d91514."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator

TASK_ID = "7842d7d91514"
ROOT = find_root(__file__)
gen, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
_NEIGHBORS = ((-1, 0), (1, 0), (0, -1), (0, 1))


def _components(grid, color):
    """Independent four-neighbor component parser used as a test oracle."""
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            pending = [(row, col)]
            seen.add((row, col))
            component = []
            while pending:
                current = pending.pop()
                component.append(current)
                cr, cc = current
                for dr, dc in _NEIGHBORS:
                    nxt = (cr + dr, cc + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        pending.append(nxt)
            result.append(component)
    return result


def _normalize(cells):
    cells = tuple(cells)
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _rotate(shape):
    shape = _normalize(shape)
    height = max(row for row, _ in shape) + 1
    return _normalize((col, height - 1 - row) for row, col in shape)


def _reflect(shape):
    shape = _normalize(shape)
    width = max(col for _, col in shape) + 1
    return _normalize((row, width - 1 - col) for row, col in shape)


def _orbit(shape):
    current = _normalize(shape)
    variants = set()
    for _ in range(4):
        variants.add(current)
        variants.add(_reflect(current))
        current = _rotate(current)
    return variants


def _intended(grid):
    """Independent exact-orientation rule mirror; it does not call generator code."""
    templates = _components(grid, 5)
    assert len(templates) == 1
    target = _normalize(templates[0])
    output = [list(row) for row in grid]
    for component in _components(grid, 2):
        color = 4 if _normalize(component) == target else 1
        for row, col in component:
            output[row][col] = color
    return output


def _canonical_rows():
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    assert rows
    return rows


def _canonical_inputs():
    result = []
    for row in _canonical_rows():
        for split in ("train", "test"):
            pairs = row.get(split, [])
            if isinstance(pairs, dict):
                pairs = [pairs]
            result.extend(pair["input"] for pair in pairs)
    return result


def _canonical_rule_source():
    for row in _canonical_rows():
        if row.get("program_solution"):
            return row["program_solution"]
    raise AssertionError("canonical program_solution missing")


def _analysis(grid):
    template = _normalize(_components(grid, 5)[0])
    candidates = [_normalize(component) for component in _components(grid, 2)]
    return template, candidates


def test_rule_hash_is_pinned_to_selected_authority():
    assert gen.RULE_HASH == "9d86bc23e927"


def test_selected_authority_is_byte_equivalent_to_canonical_source():
    authority_path = (
        ROOT
        / "shared/data/base/solutions/banks/d1c8811eb453"
        / "find_the_candidate_matching_the_template__7842d7d91514.json"
    )
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    target = authority["racket_target"]
    assert target["raw_code"] == _canonical_rule_source()
    assert target["target_code"] == target["raw_code"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_every_exact_override_is_realized_at_constructive_boundary(band):
    requested = {
        "grid_h": 11,
        "grid_w": 12,
        "n_matches": 2,
        "n_distractors": 2,
        "shape_size": 5,
    }
    grid = gen.generate(17, 31, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested


@pytest.mark.parametrize(
    "kwargs",
    [
        {"unknown_axis": 1},
        {"grid_h": True},
        {"grid_w": "12"},
        {"n_matches": 0},
        {"n_matches": 3},
        {"n_distractors": 0},
        {"n_distractors": 3},
        {"shape_size": 2},
        {"shape_size": 6},
    ],
)
def test_invalid_overrides_are_rejected(kwargs):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **kwargs)


@pytest.mark.parametrize(
    "seed,sample_index,difficulty",
    [
        (True, 0, None),
        (0, True, None),
        (0, -1, None),
        (0, 0, "expert"),
    ],
)
def test_invalid_public_controls_are_rejected(seed, sample_index, difficulty):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(seed, sample_index, difficulty=difficulty)


@pytest.mark.parametrize(
    "pair",
    canonical_pairs(TASK_ID, root=ROOT, labeled_only=True),
    ids=lambda pair: f"{pair['split']}{pair['pair_index']}",
)
def test_canonical_inputs_are_owned_and_independent_rule_matches(pair):
    assert gen.self_check(pair["input"]) == []
    assert gen.strict_canonical_like(pair["input"]) == []
    assert _intended(pair["input"]) == pair["output"]
    assert gen.rule_match(pair["input"]) == pair["output"]


def test_every_unlabeled_canonical_input_is_inside_the_declared_manifold():
    for grid in _canonical_inputs():
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_default_distribution_is_lawful_deterministic_and_refutes_shape_shortcuts(band):
    canonical_profiles = {(11, 12, 3), (12, 12, 3), (12, 13, 3)}
    seen = set()
    saw_profile = False
    template_slots = set()
    for index in range(64):
        seed = 90_000 + index
        sample_index = index * 13 + 7
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert grid == gen.generate(seed, sample_index, difficulty=band)
        assert gen.self_check(grid) == []
        assert {value for row in grid for value in row} == {0, 2, 5}

        observed = gen.observe_overrides(grid)
        assert observed["grid_h"] == len(grid)
        assert observed["grid_w"] == len(grid[0])
        template, candidates = _analysis(grid)
        assert len(template) == observed["shape_size"]
        assert candidates.count(template) == observed["n_matches"]
        assert len(candidates) - candidates.count(template) == observed["n_distractors"]
        assert all(len(shape) == len(template) for shape in candidates)
        assert any(shape != template and shape in _orbit(template) for shape in candidates)

        component = _components(grid, 5)[0]
        template_slots.add((min(r for r, _ in component) // 4, min(c for _, c in component) // 4))
        profile = (len(grid), len(grid[0]), len({v for row in grid for v in row}))
        saw_profile |= profile in canonical_profiles
        seen.add(json.dumps(grid, separators=(",", ":")))

    assert saw_profile
    assert len(seen) >= 60
    assert len(template_slots) >= 3


def test_declared_canonical_shortcut_fits_train_pairs_and_generated_witness_refutes_it():
    rival = gen.CANONICAL_SHORTCUTS["match_up_to_dihedral"]
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        assert rival(pair["input"]) == pair["output"]
    grid = gen.generate(71, 19, n_distractors=1)
    assert gen.SEMANTIC_WITNESSES["same_size_dihedral_distractor"](grid)
    assert rival(grid) != _intended(grid)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_three_example_lessons_refute_every_declared_competitor_under_all_query_rotations(band):
    for ordinal in range(24):
        seed = 120_000 + ordinal
        start = ordinal * 11
        pairs = []
        for offset in range(4):
            grid = gen.generate(seed, start + offset, difficulty=band)
            pairs.append({"input": grid, "output": _intended(grid)})
        for query_index in range(len(pairs)):
            query = pairs[query_index]
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            assert gen.lesson_identifiable(demos, query) == []
            for competitor in gen.LESSON_COMPETITORS.values():
                assert not all(competitor(demo["input"]) == demo["output"] for demo in demos)


@pytest.mark.parametrize(
    "bad",
    [
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 12 for _ in range(11)],
        [[0] * 12 for _ in range(11)],
    ],
)
def test_self_check_reports_malformed_grids_without_crashing(bad):
    assert gen.self_check(bad)
