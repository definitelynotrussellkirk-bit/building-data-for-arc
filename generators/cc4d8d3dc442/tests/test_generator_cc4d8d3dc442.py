from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from collections import deque
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GENERATOR_PATH = Path(__file__).resolve().parents[1] / "generator.py"
SPEC = importlib.util.spec_from_file_location("review_cc4d8d3dc442", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def canonical_pairs() -> list[dict]:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if '"task_id": "cc4d8d3dc442"' not in line:
                continue
            row = json.loads(line)
            return [*row["train"], *row["test"]]
    raise AssertionError("canonical task row missing")


def open_regions(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    regions: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] == 5 or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and grid[nr][nc] != 5
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            regions.append(cells)
    return regions


def full_dividers(grid: list[list[int]]) -> tuple[list[int], list[int]]:
    h, w = len(grid), len(grid[0])
    rows = [r for r in range(h) if all(v == 5 for v in grid[r])]
    cols = [c for c in range(w) if all(grid[r][c] == 5 for r in range(h))]
    return rows, cols


def key_counts(grid: list[list[int]]) -> list[int]:
    return [
        sum(grid[r][c] == 2 for r, c in region)
        for region in open_regions(grid)
    ]


def test_authority_metadata_and_public_contract_are_present() -> None:
    assert getattr(GEN, "RULE_HASH", None) == "cdefe31a4be3"
    assert callable(getattr(GEN, "rule_mirror", None))
    assert callable(getattr(GEN, "observe_overrides", None))
    assert callable(getattr(GEN, "strict_canonical_like", None))


def test_every_canonical_input_is_accepted_and_mirrors_exact_output() -> None:
    mirror = getattr(GEN, "rule_mirror", None)
    assert callable(mirror), "generator must expose a Python parity-rule oracle"
    for index, pair in enumerate(canonical_pairs()):
        assert GEN.self_check(pair["input"]) == [], f"canonical input #{index} rejected"
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert mirror(pair["input"]) == pair["output"], f"canonical pair #{index} mismatch"


def test_default_generation_contains_local_separators_not_only_rectangular_cells() -> None:
    for band in ("easy", "medium", "hard"):
        for seed in range(8):
            grid = GEN.generate(seed, seed * 17 + 3, difficulty=band)
            assert GEN.self_check(grid) == []
            rows, cols = full_dividers(grid)
            base_cells = (len(rows) - 1) * (len(cols) - 1)
            assert len(open_regions(grid)) > base_cells, (
                band,
                seed,
                "the task-defining local separator is missing",
            )
            assert GEN.rule_mirror(grid) != grid


def test_all_declared_override_extremes_work_in_every_band_and_are_observable() -> None:
    cases = [
        {
            "ch_h": 3,
            "ch_w": 3,
            "n_rows": 2,
            "n_cols": 2,
            "split_count": 1,
            "count_profile": "mixed",
        },
        {
            "ch_h": 6,
            "ch_w": 6,
            "n_rows": 3,
            "n_cols": 3,
            "split_count": 3,
            "count_profile": "high_parity",
        },
        {
            "ch_h": 4,
            "ch_w": 5,
            "n_rows": 2,
            "n_cols": 3,
            "split_count": 2,
            "count_profile": "zero_even",
        },
        {
            "ch_h": 5,
            "ch_w": 4,
            "n_rows": 3,
            "n_cols": 2,
            "split_count": 2,
            "count_profile": "zero_odd",
        },
    ]
    for band in ("easy", "medium", "hard"):
        for index, case in enumerate(cases):
            grid = GEN.generate(100 + index, 700 + index, difficulty=band, **case)
            assert GEN.self_check(grid) == []
            assert GEN.observe_overrides(grid) == case


def test_unknown_override_is_rejected_loudly() -> None:
    with pytest.raises((TypeError, ValueError, KeyError)):
        GEN.generate(0, 0, difficulty="medium", typo_axis=123)


def test_count_profiles_are_semantically_real_and_refute_one_vs_many_shortcut() -> None:
    expected_required = {
        "mixed": {0, 1, 2},
        "zero_even": {0, 2, 4},
        "zero_odd": {0, 1, 3},
        "high_parity": {0, 3, 4},
    }
    for index, (profile, required) in enumerate(expected_required.items()):
        grid = GEN.generate(
            44 + index,
            900 + index,
            difficulty="medium",
            ch_h=4,
            ch_w=4,
            n_rows=2,
            n_cols=2,
            split_count=1,
            count_profile=profile,
        )
        counts = set(key_counts(grid))
        assert required <= counts
        assert GEN.observe_overrides(grid)["count_profile"] == profile

    witness_grid = GEN.generate(
        71,
        5,
        difficulty="hard",
        ch_h=4,
        ch_w=4,
        n_rows=2,
        n_cols=2,
        split_count=1,
        count_profile="high_parity",
    )
    witness = GEN.SEMANTIC_WITNESSES["three_key_region"]
    rival = GEN.SEMANTIC_RIVALS["one_vs_many"]
    assert witness(witness_grid)
    assert rival(witness_grid) != GEN.rule_mirror(witness_grid)


def test_generation_is_independent_of_global_random_state() -> None:
    random.seed(1)
    first = GEN.generate(1234, 56, difficulty="hard")
    random.seed(999999)
    second = GEN.generate(1234, 56, difficulty="hard")
    assert first == second


def test_self_check_rejects_minimal_impostors() -> None:
    lawful = GEN.generate(
        3,
        4,
        difficulty="medium",
        ch_h=4,
        ch_w=4,
        n_rows=2,
        n_cols=2,
        split_count=1,
        count_profile="mixed",
    )
    assert GEN.self_check(lawful) == []

    blank = [[0 for _ in row] for row in lawful]
    assert GEN.self_check(blank)

    no_local_separator = copy.deepcopy(lawful)
    rows, cols = full_dividers(no_local_separator)
    for i in range(len(rows) - 1):
        for j in range(len(cols) - 1):
            for r in range(rows[i] + 1, rows[i + 1]):
                for c in range(cols[j] + 1, cols[j + 1]):
                    if no_local_separator[r][c] == 5:
                        no_local_separator[r][c] = 0
    assert GEN.self_check(no_local_separator)

    bad_color = copy.deepcopy(lawful)
    for r, row in enumerate(bad_color):
        for c, value in enumerate(row):
            if value == 0:
                bad_color[r][c] = 9
                break
        else:
            continue
        break
    assert GEN.self_check(bad_color)


def test_small_cells_with_three_splits_are_total_not_greedy_rejections() -> None:
    for seed in range(30):
        grid = GEN.generate(
            seed,
            seed * 17 + 3,
            difficulty="easy",
            ch_h=3,
            split_count=3,
        )
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid)["ch_h"] == 3
        assert GEN.observe_overrides(grid)["split_count"] == 3
