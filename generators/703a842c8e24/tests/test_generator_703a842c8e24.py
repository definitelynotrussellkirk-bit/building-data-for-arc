from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest


TASK_ID = "703a842c8e24"
REPO = Path(__file__).resolve().parents[3]
RUNTIME = REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))


def _load_generator():
    path = REPO / "generators" / TASK_ID / "generator.py"
    spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _norm_grid(value):
    if isinstance(value, list) and value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return value


def _canonical_row():
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in path.read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError("canonical row not found")


def _canonical_pairs():
    row = _canonical_row()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return [
        {"input": _norm_grid(pair["input"]), "output": _norm_grid(pair["output"])}
        for pair in [*row["train"], *test]
    ]


def _components(grid):
    background = 0
    seen = set()
    count = 0
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] == background or (row, col) in seen:
                continue
            count += 1
            stack = [(row, col)]
            seen.add((row, col))
            while stack:
                rr, cc = stack.pop()
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < len(grid)
                        and 0 <= nc < len(grid[0])
                        and grid[nr][nc] != background
                        and (nr, nc) not in seen
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
    return count


def test_canonical_parity_and_rule_hash_pin():
    row = _canonical_row()
    expected_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == expected_hash
    for pair in _canonical_pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_four_consecutive_samples_cover_the_semantic_curriculum():
    for start in range(8):
        grids = [gen.generate(2026, start + offset, difficulty="medium") for offset in range(4)]
        profiles = [gen.schedule_profile(2026, start + offset, "medium") for offset in range(4)]
        assert set(profiles) == set(gen.SCHEDULE_PROFILES)
        demos = [{"input": grid, "output": gen.rule_mirror(grid)} for grid in grids]
        query_grid = gen.generate(2026, start + 4, difficulty="medium")
        assert gen.lesson_identifiable(
            demos, {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        ) == []
        for witness in gen.SEMANTIC_WITNESSES.values():
            assert any(witness(grid) for grid in grids)


def test_override_boundaries_are_exact_observable_and_composable():
    for band in ("easy", "medium", "hard"):
        for grid_h in (3, 8):
            for grid_w in (6, 13):
                for n_body_colors in (2, 6):
                    grid = gen.generate(
                        91,
                        7,
                        difficulty=band,
                        grid_h=grid_h,
                        grid_w=grid_w,
                        n_body_colors=n_body_colors,
                    )
                    assert gen.self_check(grid) == []
                    assert gen.observe_overrides(grid) == {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "n_body_colors": n_body_colors,
                    }


@pytest.mark.parametrize("profile", ("canonical", "wraparound", "mixed_modulo", "dense_scattered"))
def test_each_profile_is_lawful_and_has_a_visible_effect(profile):
    grids = [gen.generate(seed, seed, profile=profile) for seed in range(12)]
    assert all(gen.self_check(grid) == [] for grid in grids)
    assert len({tuple(map(tuple, grid)) for grid in grids}) >= 8
    if profile == "canonical":
        assert all((len(grid), len(grid[0])) == (4, 9) for grid in grids)
        assert all(5 <= len({cell for row in grid for cell in row}) <= 7 for grid in grids)
    elif profile == "wraparound":
        assert all(gen.semantic_observables(grid)["wraparound_row"] for grid in grids)
    elif profile == "mixed_modulo":
        assert all(gen.semantic_observables(grid)["identity_modulo_row"] for grid in grids)
    else:
        assert all(gen.semantic_observables(grid)["scattered_row"] for grid in grids)


def test_generated_distribution_breaks_the_single_object_shortcut():
    counts = []
    canonical_support = {band: 0 for band in ("easy", "medium", "hard")}
    for band in canonical_support:
        for sample_index in range(40):
            grid = gen.generate(700 + sample_index, sample_index, difficulty=band)
            counts.append(_components(grid))
            palette_size = len({cell for row in grid for cell in row})
            if (len(grid), len(grid[0]), palette_size) in {(4, 9, 5), (4, 9, 6), (4, 9, 7)}:
                canonical_support[band] += 1
    assert min(canonical_support.values()) >= 8
    assert sum(count >= 2 for count in counts) >= int(0.9 * len(counts))


def test_declared_shortcut_is_canonical_ambiguous_but_generated_counterexample_exists():
    shortcut = gen.CANONICAL_SHORTCUTS["headers_1_to_4_else_identity"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _canonical_pairs())
    witness = gen.SEMANTIC_WITNESSES["large_header_counterexample"]
    counterexamples = [
        gen.generate(55, index, profile="wraparound") for index in range(12)
    ]
    assert any(witness(grid) and shortcut(grid) != gen.rule_mirror(grid) for grid in counterexamples)


def test_self_check_rejects_structural_impostors():
    good = gen.generate(44, 3, profile="dense_scattered")
    cases = [
        [],
        [[0]],
        [[1, 1, 1], [1, 1, 1], [1, 1, 1]],
        [[0, 1, 0, 0, 0, 0] for _ in range(3)],
    ]
    ragged = copy.deepcopy(good)
    ragged[0].pop()
    cases.append(ragged)
    zero_header = copy.deepcopy(good)
    zero_header[0][0] = 0
    cases.append(zero_header)
    empty_body = copy.deepcopy(good)
    empty_body[0][1:] = [0] * (len(empty_body[0]) - 1)
    cases.append(empty_body)
    for case in cases:
        assert gen.self_check(case)


def test_replay_is_deterministic_fresh_and_global_rng_pure():
    random.seed(90210)
    state = random.getstate()
    first = gen.generate(17, 4, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(17, 4, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 0
    assert gen.generate(17, 4, difficulty="hard") == second
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 0, imaginary_axis=3)
