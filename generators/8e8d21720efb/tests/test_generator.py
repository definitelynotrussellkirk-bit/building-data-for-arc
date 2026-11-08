"""Task-local contract tests for 8e8d21720efb.

These tests intentionally use an independent rule mirror and portable canonical
helpers.  They do not import private repository scripts or a sibling checkout.
"""
from __future__ import annotations

from collections import Counter, deque
import importlib.util
import json
import os
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root

TASK_ID = "8e8d21720efb"


def _load_generator():
    configured = os.environ.get("GENERATOR_UNDER_TEST")
    path = Path(configured) if configured else Path(__file__).resolve().parents[1] / "generator.py"
    spec = importlib.util.spec_from_file_location("generator_under_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _reference_output(grid):
    h, w = len(grid), len(grid[0])
    out = [[0 for _ in range(w)] for _ in range(h)]
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0:
                continue
            if any(
                0 <= r + dr < h
                and 0 <= c + dc < w
                and grid[r + dr][c + dc] == color
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
            ):
                out[r][c] = color
    return out


def _components(grid):
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    found = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        color = grid[start[0]][start[1]]
        cells = {start}
        queue = deque([start])
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (r + dr, c + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    cells.add(nxt)
                    queue.append(nxt)
        found.append((color, cells))
    return found


@pytest.fixture(scope="module")
def canon():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def test_rule_hash_is_pinned():
    assert gen.RULE_HASH == "76b667ae03a8"


def test_canonical_pairs_are_accepted_and_match_independent_rule(canon):
    assert len(canon) == 5
    for pair in canon:
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert _reference_output(pair["input"]) == pair["output"]
        assert gen.strict_canonical_like(pair["input"]) == []


def test_canonical_shortcuts_really_fit_every_labeled_canonical_pair(canon):
    assert {
        "global_color_frequency",
        "same_color_eight_neighbor",
        "any_nonzero_cardinal_neighbor",
    } <= set(gen.CANONICAL_SHORTCUTS)
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in canon), name


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("profile", ["canonical", "witness"])
@pytest.mark.parametrize("shape", [(7, 8), (9, 10), (12, 13)])
def test_exact_overrides_are_observable_and_honored(band, profile, shape):
    requested = {
        "grid_h": shape[0],
        "grid_w": shape[1],
        "lesson_profile": profile,
    }
    grid = gen.generate(31, 7, difficulty=band, **requested)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == requested
    assert gen.classify_profile(grid) == profile
    assert _reference_output(grid) == gen.rule_mirror(grid)


@pytest.mark.parametrize(
    "key,value",
    [
        ("typo", 1),
        ("grid_h", 6),
        ("grid_h", 13),
        ("grid_w", 7),
        ("grid_w", 14),
        ("grid_h", True),
        ("grid_w", 9.5),
        ("lesson_profile", "unknown"),
        ("lesson_profile", 1),
    ],
)
def test_invalid_overrides_are_rejected(key, value):
    with pytest.raises(ValueError):
        gen.generate(0, 0, **{key: value})


def test_ten_slot_schedule_alternates_profiles_and_covers_canonical_cases():
    assert gen.LESSON_SCHEDULE_PERIOD == 10
    profiles = [gen.schedule_profile(0, i, difficulty="medium") for i in range(10)]
    assert profiles == ["canonical" if i % 2 == 0 else "witness" for i in range(10)]
    for start in range(10):
        window = [profiles[(start + offset) % 10] for offset in range(4)]
        assert window.count("witness") == 2
        assert window.count("canonical") == 2


def test_witness_profile_refutes_every_declared_competitor():
    for band in ("easy", "medium", "hard"):
        for index in range(1, 20, 2):
            grid = gen.generate(1000 + index, index, difficulty=band)
            assert gen.classify_profile(grid) == "witness"
            expected = _reference_output(grid)
            assert gen.rule_mirror(grid) == expected
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert rival(grid) != expected, (band, index, name)
            for name, predicate in gen.SEMANTIC_WITNESSES.items():
                assert predicate(grid), (band, index, name)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("start", range(10))
def test_every_four_pair_window_supports_every_query_rotation(band, start):
    pairs = []
    for offset in range(4):
        grid = gen.generate(700 + start, start + offset, difficulty=band)
        pairs.append({"input": grid, "output": _reference_output(grid)})
    for query_index in range(4):
        query = pairs[query_index]
        demos = [pair for i, pair in enumerate(pairs) if i != query_index]
        assert gen.lesson_identifiable(demos, query) == []


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
def test_distribution_is_deterministic_lawful_and_has_strict_support(band):
    profiles = Counter()
    strict = 0
    shapes = set()
    component_size_signatures = set()
    for index in range(60):
        grid = gen.generate(5000 + index, index, difficulty=band)
        assert grid == gen.generate(5000 + index, index, difficulty=band)
        assert gen.self_check(grid) == []
        assert gen.rule_mirror(grid) == _reference_output(grid)
        profiles[gen.classify_profile(grid)] += 1
        strict += not gen.strict_canonical_like(grid)
        shapes.add((len(grid), len(grid[0])))
        component_size_signatures.add(tuple(sorted(len(cells) for _, cells in _components(grid))))
    assert profiles == Counter({"canonical": 30, "witness": 30})
    assert strict >= 25
    assert len(shapes) >= 6
    assert len(component_size_signatures) >= 5


def test_witness_profile_contains_the_locality_counterexamples():
    grid = gen.generate(12345, 1, difficulty="medium")
    components = _components(grid)
    sizes_by_color = {}
    for color, cells in components:
        sizes_by_color.setdefault(color, []).append(len(cells))
    assert any(1 in sizes and any(size >= 2 for size in sizes) for sizes in sizes_by_color.values())
    assert any(sizes.count(1) >= 2 for sizes in sizes_by_color.values())
    assert any(
        grid[r][c] != 0
        and grid[nr][nc] != 0
        and grid[r][c] != grid[nr][nc]
        for r in range(len(grid))
        for c in range(len(grid[0]))
        for nr, nc in ((r + 1, c), (r, c + 1))
        if nr < len(grid) and nc < len(grid[0])
    )


def test_validator_rejects_minimal_impostors_and_mutation_fixtures():
    for name, grid in gen.mutation_fixtures():
        assert gen.self_check(grid), name

    assert gen.self_check([[0] * 8 for _ in range(7)])
    assert gen.self_check([[1] * 8 for _ in range(7)])


@pytest.mark.parametrize(
    "grid",
    [None, [], [[]], [[0], [0, 1]], [[True] * 8 for _ in range(7)]],
)
def test_malformed_grid_is_diagnostic_not_exception(grid):
    assert gen.self_check(grid)


def test_retained_global_frequency_counterexample():
    path = Path(__file__).resolve().parents[1] / "counterexamples" / "global_frequency_shortcut.json"
    record = json.loads(path.read_text())
    grid = record["input"]
    expected = record["authority_output"]
    assert gen.self_check(grid) == []
    assert _reference_output(grid) == expected
    assert gen.rule_mirror(grid) == expected
    rival = gen.CANONICAL_SHORTCUTS["global_color_frequency"]
    assert rival(grid) == record["rival_output"]
    assert rival(grid) != expected
