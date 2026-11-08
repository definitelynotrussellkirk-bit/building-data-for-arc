"""Regression contract for the repaired 0eb83be0298d generator.

The oracle and component shortcut below are independent transcriptions; tests
must not merely compare generator helpers with one another.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
RUNTIME = REPO / "shared" / "runtime"
if RUNTIME.is_dir():
    sys.path.insert(0, str(RUNTIME))

from reviewer_support import canonical_pairs, find_root

spec = importlib.util.spec_from_file_location("generator_under_test", HOME / "generator.py")
assert spec is not None and spec.loader is not None
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)

ROOT = find_root(__file__)
PAIRS = canonical_pairs(gen.TASK_ID, root=ROOT, labeled_only=True)
BANDS = (None, "easy", "medium", "hard")


def _split(grid):
    h = len(grid)
    dividers = [c for c in range(len(grid[0])) if all(grid[r][c] == 9 for r in range(h))]
    assert len(dividers) == 1
    divider = dividers[0]
    return [row[:divider] for row in grid], [row[divider + 1:] for row in grid]


def _crop(panel):
    cells = [
        (r, c)
        for r, row in enumerate(panel)
        for c, value in enumerate(row)
        if value not in (0, 9)
    ]
    assert cells
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    return [row[c0:c1 + 1] for row in panel[r0:r1 + 1]]


def _rule_mirror(grid):
    """Independent transcription of the selected Racket rule."""
    panel, board = _split(grid)
    template = _crop(panel)
    th, tw = len(template), len(template[0])
    out = [[0 for _ in row] for row in board]
    for r0 in range(len(board) - th + 1):
        for c0 in range(len(board[0]) - tw + 1):
            if all(
                value == 0 or board[r0 + r][c0 + c] == value
                for r, row in enumerate(template)
                for c, value in enumerate(row)
            ):
                out[r0 + th - 1][c0 + tw - 1] = 8
    return out


def _literal_zero_rival(grid):
    """Wrong canonical-fitting rule: template zeroes must remain blank."""
    panel, board = _split(grid)
    template = _crop(panel)
    th, tw = len(template), len(template[0])
    out = [[0 for _ in row] for row in board]
    for r0 in range(len(board) - th + 1):
        for c0 in range(len(board[0]) - tw + 1):
            if all(
                board[r0 + r][c0 + c] == template[r][c]
                for r in range(th)
                for c in range(tw)
            ):
                out[r0 + th - 1][c0 + tw - 1] = 8
    return out


def _component_corner_rival(grid):
    """Wrong template-free rule found by the previous source-bound audit."""
    _, board = _split(grid)
    h, w = len(board), len(board[0])
    out = [[0] * w for _ in range(h)]
    seen = set()
    for r in range(h):
        for c in range(w):
            color = board[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and board[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            out[max(rr for rr, _ in cells)][max(cc for _, cc in cells)] = 8
    return out



_BOARD_ONLY_FAMILY = (
    ((0, 1), (0, 2), (1, 1), (2, 0), (2, 1)),
    ((0, 0), (0, 1), (0, 2), (1, 1), (2, 1)),
    ((0, 0), (1, 0), (2, 0), (2, 1), (2, 2)),
    ((0, 0), (1, 0), (1, 1), (2, 1), (2, 2)),
    ((0, 0), (0, 1), (1, 1), (2, 1), (2, 2)),
)


def _normalise_cells(cells):
    cells = tuple(cells)
    r0 = min(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    return tuple(sorted((r - r0, c - c0) for r, c in cells))


def _rotate_cells(cells):
    return _normalise_cells((c, -r) for r, c in cells)


def _family_variants():
    variants = []
    seen = set()
    for shape in _BOARD_ONLY_FAMILY:
        local = set()
        for reflected in (False, True):
            work = _normalise_cells((r, -c if reflected else c) for r, c in shape)
            for _ in range(4):
                local.add(work)
                work = _rotate_cells(work)
        for variant in sorted(local):
            if variant not in seen:
                seen.add(variant)
                variants.append(variant)
    return tuple(variants)


_BOARD_ONLY_VARIANTS = _family_variants()


def _shape_dims(shape):
    return max(r for r, _ in shape) + 1, max(c for _, c in shape) + 1


def _shape_matches(board, shape, color):
    sh, sw = _shape_dims(shape)
    return [
        (r0, c0)
        for r0 in range(len(board) - sh + 1)
        for c0 in range(len(board[0]) - sw + 1)
        if all(board[r0 + dr][c0 + dc] == color for dr, dc in shape)
    ]


def _board_only_family_rival(grid):
    """Ignore the template; infer the most repeated known-family board motif."""
    _, board = _split(grid)
    counts = Counter(value for row in board for value in row if value not in (0, 9))
    assert counts
    color = max(counts, key=lambda value: (counts[value], -value))
    candidates = []
    for index, shape in enumerate(_BOARD_ONLY_VARIANTS):
        matches = _shape_matches(board, shape, color)
        if not matches:
            continue
        sh, sw = _shape_dims(shape)
        occupied = set(shape)
        clutter = sum(
            board[r0 + r][c0 + c] != 0
            for r0, c0 in matches
            for r in range(sh)
            for c in range(sw)
            if (r, c) not in occupied
        )
        score = (clutter > 0, len(matches), clutter, -index)
        candidates.append((score, shape, matches))
    if not candidates:
        return [[0 for _ in row] for row in board]
    _, shape, matches = max(candidates, key=lambda item: item[0])
    sh, sw = _shape_dims(shape)
    output = [[0 for _ in row] for row in board]
    for r0, c0 in matches:
        output[r0 + sh - 1][c0 + sw - 1] = 8
    return output

def _palette_size(grid):
    return len({value for row in grid for value in row})


def _all_competitors():
    competitors = {}
    for namespace in ("CANONICAL_SHORTCUTS", "LESSON_COMPETITORS", "SEMANTIC_RIVALS"):
        mapping = getattr(gen, namespace)
        assert isinstance(mapping, dict)
        for name, rule in mapping.items():
            assert isinstance(name, str) and callable(rule)
            competitors.setdefault(name, rule)
    return competitors


def _per_draw_competitors():
    competitors = {}
    for namespace in ("CANONICAL_SHORTCUTS", "SEMANTIC_RIVALS"):
        competitors.update(getattr(gen, namespace))
    return competitors


def test_selected_rule_hash_and_contract_are_pinned():
    assert gen.RULE_HASH == "4be3f14f70ed"
    assert gen.EXAMPLES_NEEDED == 3
    assert gen.LESSON_SCHEDULE_PERIOD == 4
    assert gen.MIN_STRICT_FRAC == 1.0
    assert set(gen.SEMANTIC_WITNESSES) == {
        "template_required_component_decoy",
        "wildcard_slot_clutter",
        "original_orientation_only",
    }
    assert _all_competitors()


def test_all_labeled_canonical_pairs_are_accepted_and_match_independent_oracle():
    assert [(pair["split"], pair["pair_index"]) for pair in PAIRS] == [
        ("train", 0),
        ("train", 1),
        ("test", 0),
    ]
    for pair in PAIRS:
        expected = _rule_mirror(pair["input"])
        assert expected == pair["output"]
        assert gen.rule_mirror(pair["input"]) == expected
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []


def test_literal_zero_shortcut_is_declared_and_really_fits_every_canonical_pair():
    assert set(gen.CANONICAL_SHORTCUTS) == {"literal_zero_matching"}
    shortcut = gen.CANONICAL_SHORTCUTS["literal_zero_matching"]
    for pair in PAIRS:
        assert _literal_zero_rival(pair["input"]) == pair["output"]
        assert shortcut(pair["input"]) == pair["output"]


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("shape_id", range(5))
@pytest.mark.parametrize("match_count", (1, 2, 3))
@pytest.mark.parametrize("grid_h,board_w", ((6, 7), (6, 14), (12, 7), (12, 14)))
@pytest.mark.parametrize("template_color", (1, 7))
def test_joint_boundary_overrides_are_exact_and_observable(
    difficulty, shape_id, match_count, grid_h, board_w, template_color
):
    requested = {
        "grid_h": grid_h,
        "board_w": board_w,
        "shape_id": shape_id,
        "match_count": match_count,
        "template_color": template_color,
    }
    grid = gen.generate(911, 37, difficulty=difficulty, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert gen.rule_mirror(grid) == _rule_mirror(grid)


def test_invalid_calls_are_rejected_instead_of_silently_coerced():
    with pytest.raises((TypeError, ValueError), match="unknown"):
        gen.generate(1, 0, typo_axis=1)
    with pytest.raises((TypeError, ValueError), match="difficulty"):
        gen.generate(1, 0, difficulty="extreme")
    with pytest.raises((TypeError, ValueError), match="integer|bool"):
        gen.generate(1, 0, grid_h=True)
    with pytest.raises((TypeError, ValueError), match="integer"):
        gen.generate(1, 0, match_count="2")
    with pytest.raises((TypeError, ValueError), match="outside|range|between|valid"):
        gen.generate(1, 0, template_color=8)


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("seed", range(8))
def test_every_default_draw_refutes_every_declared_per_draw_competitor(seed, difficulty):
    competitors = _per_draw_competitors()
    for index in range(8):
        grid = gen.generate(20261008 + seed, index, difficulty=difficulty)
        expected = _rule_mirror(grid)
        assert _component_corner_rival(grid) != expected
        assert _literal_zero_rival(grid) != expected
        assert all(predicate(grid) for predicate in gen.SEMANTIC_WITNESSES.values())
        for name, rival in competitors.items():
            assert rival(grid) != expected, (seed, difficulty, index, name)


@pytest.mark.parametrize("difficulty", BANDS)
def test_four_slot_schedule_hits_the_three_canonical_profiles(difficulty):
    expected = {
        0: ((6, 11, 3), "canonical_6x11_palette3"),
        1: ((7, 11, 4), "canonical_7x11_palette4"),
        2: ((7, 12, 3), "canonical_7x12_palette3"),
        3: (None, "broad"),
    }
    for index, (profile, schedule_name) in expected.items():
        grid = gen.generate(73, index, difficulty=difficulty)
        assert gen.schedule_profile(73, index, difficulty) == schedule_name
        if profile is not None:
            assert (len(grid), len(grid[0]), _palette_size(grid)) == profile


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("seed", range(5))
def test_every_four_pair_window_contains_two_board_only_refutations(seed, difficulty):
    assert "board_only_family_frequency" in gen.LESSON_COMPETITORS
    declared = gen.LESSON_COMPETITORS["board_only_family_frequency"]
    grids = [gen.generate(seed, index, difficulty=difficulty) for index in range(12)]
    for grid in grids:
        assert declared(grid) == _board_only_family_rival(grid)
    for start in range(9):
        window = grids[start:start + 4]
        refutations = [
            _board_only_family_rival(grid) != _rule_mirror(grid)
            for grid in window
        ]
        # Any one query can be held out while one refuting demonstration remains.
        assert sum(refutations) >= 2, (seed, difficulty, start, refutations)


@pytest.mark.parametrize("difficulty", BANDS)
@pytest.mark.parametrize("seed", range(5))
def test_every_four_pair_window_is_identifiable_under_all_query_rotations(seed, difficulty):
    grids = [gen.generate(seed, index, difficulty=difficulty) for index in range(12)]
    for start in range(9):
        pairs = [
            {"input": grid, "output": _rule_mirror(grid)}
            for grid in grids[start:start + 4]
        ]
        for query_index in range(4):
            demos = [pair for index, pair in enumerate(pairs) if index != query_index]
            query = deepcopy(pairs[query_index])
            # Query labels are hidden in real lessons and must not affect the hook.
            query["output"] = [[9]]
            assert gen.lesson_identifiable(demos, query) == [], (
                seed,
                difficulty,
                start,
                query_index,
            )


def test_generation_and_diagnostics_are_deterministic_fresh_and_input_pure():
    first = gen.generate(73, 11, difficulty="hard")
    second = gen.generate(73, 11, difficulty="hard")
    assert first == second
    original = deepcopy(first)
    expected = _rule_mirror(first)
    assert gen.rule_mirror(first) == expected
    for rival in _all_competitors().values():
        rival(first)
    for predicate in gen.SEMANTIC_WITNESSES.values():
        predicate(first)
    assert first == original
    first[0][0] = (first[0][0] + 1) % 10
    assert first != second


def test_retained_literal_zero_counterexample_is_source_bound_and_reproducible():
    import json
    import hashlib

    path = HOME / "counterexamples" / "review-44a14bf0056d7e03" / "literal-zero-shortcut.json"
    item = json.loads(path.read_text())
    assert item["task_id"] == gen.TASK_ID
    assert item["rule_hash"] == gen.RULE_HASH
    assert item["generator_sha256"] == hashlib.sha256((HOME / "generator.py").read_bytes()).hexdigest()
    grid = item["input"]
    assert gen.self_check(grid) == []
    assert _rule_mirror(grid) == item["racket_output"]
    assert _literal_zero_rival(grid) == item["literal_zero_rival_output"]
    assert item["racket_output"] != item["literal_zero_rival_output"]
