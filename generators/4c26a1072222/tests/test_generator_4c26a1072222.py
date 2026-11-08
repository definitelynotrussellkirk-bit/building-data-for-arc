"""Focused semantic regressions for generator 4c26a1072222."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import random
import sys

import pytest


HOME = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared" / "runtime"))
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("reviewed_4c26a1072222", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _canonical_path() -> Path:
    candidates = (
        ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl",
        ROOT / "data" / "canonical" / "puzzles.jsonl",
        Path.cwd() / "shared" / "data" / "canonical" / "puzzles.jsonl",
        Path.cwd() / "data" / "canonical" / "puzzles.jsonl",
    )
    for path in candidates:
        if path.exists():
            return path
    raise AssertionError(f"canonical puzzles.jsonl not found in {candidates}")


def canonical_pairs() -> list[dict]:
    for line in _canonical_path().read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == GEN.TASK_ID:
            tests = row.get("test", [])
            if isinstance(tests, dict):
                tests = [tests]
            return [*row.get("train", []), *tests]
    raise AssertionError("canonical task not found")


def test_rule_hash_and_all_canonical_pairs_are_exact() -> None:
    assert GEN.RULE_HASH == "a86a18b84011"
    pairs = canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_exact_overrides_select_all_eight_authority_transforms() -> None:
    assert len(GEN.TRANSFORM_NAMES) == 8
    for difficulty in (None, "easy", "medium", "hard"):
        for index, transform in enumerate(GEN.TRANSFORM_NAMES):
            for n_bands in (3, 4):
                grid = GEN.generate(
                    8100 + index,
                    index,
                    difficulty=difficulty,
                    n_bands=n_bands,
                    first_transform=transform,
                )
                assert GEN.self_check(grid) == []
                assert GEN.observe_overrides(grid) == {
                    "n_bands": n_bands,
                    "first_transform": transform,
                }
                signature = GEN.semantic_signature(grid)
                assert signature["transforms"][0] == transform
                assert signature["n_bands"] == n_bands


@pytest.mark.parametrize(
    "overrides",
    [
        {"typo": 1},
        {"n_bands": 2},
        {"n_bands": 5},
        {"n_bands": True},
        {"n_bands": 3.0},
        {"first_transform": "rotate_45"},
        {"first_transform": 0},
    ],
)
def test_invalid_or_unknown_overrides_reject_loudly(overrides: dict) -> None:
    with pytest.raises(ValueError):
        GEN.generate(1, 2, **overrides)


def test_default_distribution_hits_both_canonical_profiles_and_every_transform() -> None:
    for difficulty in (None, "easy", "medium", "hard"):
        shapes: set[tuple[int, int]] = set()
        transforms: set[str] = set()
        unique_inputs: set[str] = set()
        for sample_index in range(64):
            grid = GEN.generate(2600, sample_index, difficulty=difficulty)
            assert GEN.self_check(grid, difficulty=difficulty) == []
            assert GEN.strict_canonical_like(grid) == []
            shapes.add((len(grid), len(grid[0])))
            values = {value for row in grid for value in row}
            assert 0 in values and len(values) == 9
            signature = GEN.semantic_signature(grid)
            transforms.update(signature["transforms"])
            assert 3 in signature["source_color_counts"]
            assert signature["recolored_bands"] >= 1
            assert len(set(signature["relations"])) >= 2
            output = GEN.rule_mirror(grid)
            assert len(output) == len(grid)
            assert all(len(row) == 2 for row in output)
            unique_inputs.add(json.dumps(grid, separators=(",", ":")))
        assert shapes == {(8, 9), (11, 9)}
        assert transforms == set(GEN.TRANSFORM_NAMES)
        assert len(unique_inputs) >= 60


def test_source_color_count_is_decoupled_from_transform_family() -> None:
    transpose_family = {"transpose", "anti_transpose"}
    cases = (
        ("transpose", 3, 0),
        ("anti_transpose", 3, 1),
        ("rotate_cw", 3, 2),
        ("identity", 4, 3),
    )
    for first_transform, n_bands, sample_index in cases:
        grid = GEN.generate(
            62001,
            sample_index,
            difficulty="hard",
            n_bands=n_bands,
            first_transform=first_transform,
        )
        signature = GEN.semantic_signature(grid)
        assert any(
            color_count == 3 and transform not in transpose_family
            for transform, color_count in zip(
                signature["transforms"], signature["source_color_counts"]
            )
        )



def test_source_count_gate_is_a_declared_shortcut_and_generated_rival() -> None:
    rival_name = "source_count_transform_gate"
    witness_name = "source_count_decorrelation"
    assert rival_name in GEN.CANONICAL_SHORTCUTS
    assert rival_name in GEN.SEMANTIC_RIVALS
    assert GEN.WITNESS_RIVALS[witness_name] == [rival_name]

    rival = GEN.SEMANTIC_RIVALS[rival_name]
    for pair in canonical_pairs():
        assert rival(pair["input"]) == pair["output"]

    for sample_index in range(16):
        grid = GEN.generate(62002, sample_index, difficulty="hard")
        assert GEN.SEMANTIC_WITNESSES[witness_name](grid)
        assert rival(grid) != GEN.rule_mirror(grid)



def test_declared_witnesses_refute_linked_rivals_and_shortcuts_fit_canonical() -> None:
    for pair in canonical_pairs():
        for shortcut in GEN.CANONICAL_SHORTCUTS.values():
            assert shortcut(pair["input"]) == pair["output"]

    for sample_index in range(24):
        grid = GEN.generate(9901, sample_index, difficulty="hard")
        true_output = GEN.rule_mirror(grid)
        for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
            assert predicate(grid), witness_name
            for rival_name in GEN.WITNESS_RIVALS[witness_name]:
                assert GEN.SEMANTIC_RIVALS[rival_name](grid) != true_output


def test_every_sliding_four_demo_window_eliminates_named_competitors() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for seed in (0, 17, 991):
            pairs = []
            for sample_index in range(12):
                grid = GEN.generate(seed, sample_index, difficulty=difficulty)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            for start in range(8):
                demos = pairs[start : start + GEN.EXAMPLES_NEEDED]
                query = pairs[start + GEN.EXAMPLES_NEEDED]
                assert GEN.lesson_identifiable(demos, query) == []


def test_self_check_rejects_destructive_and_structural_mutations() -> None:
    valid = GEN.generate(613, 5, difficulty="medium", n_bands=4)
    assert GEN.self_check(valid) == []

    blank = [[0 for _ in row] for row in valid]
    assert GEN.self_check(blank)

    wrong_width = [row[:-1] for row in valid]
    assert GEN.self_check(wrong_width)

    missing_band = copy.deepcopy(valid[:8])
    assert GEN.self_check(missing_band) == []  # 3-band profile remains lawful
    single_band = copy.deepcopy(valid[:2])
    assert GEN.self_check(single_band)

    broken_separator = copy.deepcopy(valid)
    broken_separator[2][0] = 1
    assert GEN.self_check(broken_separator)

    structural_column = copy.deepcopy(valid)
    structural_column[0][2] = 1
    assert GEN.self_check(structural_column)

    missing_block_cell = copy.deepcopy(valid)
    missing_block_cell[0][0] = 0
    assert GEN.self_check(missing_block_cell)

    dropped_palette_color = copy.deepcopy(valid)
    victim = next(value for value in dropped_palette_color[0] if value)
    replacement = next(value for row in dropped_palette_color for value in row if value and value != victim)
    for r, row in enumerate(dropped_palette_color):
        for c, value in enumerate(row):
            if value == victim:
                dropped_palette_color[r][c] = replacement
    assert GEN.self_check(dropped_palette_color)

    ragged = copy.deepcopy(valid)
    ragged[0].pop()
    assert GEN.self_check(ragged)


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True] * 9 for _ in range(8)]])
def test_malformed_grids_are_diagnostic_not_exceptions(grid) -> None:
    assert GEN.self_check(grid)


def test_determinism_fresh_copies_and_global_rng_purity() -> None:
    random.seed(20261003)
    state = random.getstate()
    first = GEN.generate(71, 13, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(71, 13, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert second == GEN.generate(71, 13, difficulty="hard")


def _object_count(grid: list[list[int]]) -> int:
    seen: set[tuple[int, int]] = set()
    count = 0
    for row, values in enumerate(grid):
        for col, value in enumerate(values):
            if value == 0 or (row, col) in seen:
                continue
            count += 1
            seen.add((row, col))
            stack = [(row, col)]
            while stack:
                current_row, current_col = stack.pop()
                for drow, dcol in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    next_row = current_row + drow
                    next_col = current_col + dcol
                    if not (
                        0 <= next_row < len(grid)
                        and 0 <= next_col < len(grid[0])
                    ):
                        continue
                    point = (next_row, next_col)
                    if point in seen or grid[next_row][next_col] != value:
                        continue
                    seen.add(point)
                    stack.append(point)
    return count


def test_distribution_reaches_canonical_object_density() -> None:
    # Canonical train inputs have object counts 18 and 24.  The generator must
    # reach that neighborhood rather than always emitting 26+ tiny components.
    for difficulty in ("easy", "medium", "hard"):
        counts = [
            _object_count(GEN.generate(4400 + index, index, difficulty=difficulty))
            for index in range(32)
        ]
        assert min(counts) <= 22
        assert max(counts) <= 34


def test_difficulty_bands_are_not_dead_aliases() -> None:
    for sample_index in range(12):
        grids = {
            json.dumps(
                GEN.generate(7123, sample_index, difficulty=difficulty),
                separators=(",", ":"),
            )
            for difficulty in ("easy", "medium", "hard")
        }
        assert len(grids) >= 2


def _normalized_rule_hash(source: str) -> str:
    import hashlib

    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def test_selected_base_authorities_are_synchronized_to_canonical() -> None:
    candidates = (
        ROOT / "shared" / "data" / "base" / "solutions",
        ROOT / "data" / "base" / "solutions",
        Path.cwd() / "shared" / "data" / "base" / "solutions",
        Path.cwd() / "data" / "base" / "solutions",
    )
    solution_root = next((path for path in candidates if path.exists()), None)
    assert solution_root is not None
    records = []
    for path in solution_root.rglob("*.json"):
        row = json.loads(path.read_text(encoding="utf-8"))
        if row.get("task_id") == GEN.TASK_ID:
            records.append(row)
    assert len(records) == 2
    for row in records:
        target = row["racket_target"]
        assert _normalized_rule_hash(target["target_code"]) == GEN.RULE_HASH
        assert target["canonicalization_status"] == "selected_exact_canonical_raw_preserved"
