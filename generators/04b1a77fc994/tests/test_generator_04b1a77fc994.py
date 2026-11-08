from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import os
import random
from pathlib import Path

import pytest

TASK_ID = "04b1a77fc994"
ROOT = Path(__file__).resolve().parents[1]


def _load_module():
    override = os.environ.get("GENERATOR_UNDER_TEST")
    if not override:
        return importlib.import_module(
            f"puzzle_generators.per_puzzle.{TASK_ID}.generator"
        )
    path = Path(override)
    spec = importlib.util.spec_from_file_location(
        f"generator_under_test_{TASK_ID}", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


mod = _load_module()


def _canonical_pairs():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return [
                    pair
                    for split in ("train", "test")
                    for pair in row[split]
                ]
    raise AssertionError("canonical task row not found")


def _components(grid):
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for sr in range(h):
        for sc in range(w):
            color = grid[sr][sc]
            if color == 0 or (sr, sc) in seen:
                continue
            stack = [(sr, sc)]
            seen.add((sr, sc))
            cells = []
            while stack:
                r, c = stack.pop()
                cells.append((r, c))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            touches = sum(
                (
                    any(r == 0 for r, _ in cells),
                    any(r == h - 1 for r, _ in cells),
                    any(c == 0 for _, c in cells),
                    any(c == w - 1 for _, c in cells),
                )
            )
            result.append((color, tuple(sorted(cells)), touches))
    return result


def _independent_rule(grid):
    out = [[0 for _ in row] for row in grid]
    for _, cells, touches in _components(grid):
        target = 1 if touches == 0 else 2 if touches == 1 else 3 if touches == 2 else 4
        for r, c in cells:
            out[r][c] = target
    return out


def test_rule_hash_and_version_are_pinned():
    assert mod.RULE_HASH == "20e8206868a6"
    assert mod.VERSION == "4.0.0"
    assert set(mod.AXES) == {"scene_profile"}


def test_all_canonical_pairs_pass_and_match_exact_rule():
    for pair in _canonical_pairs():
        source = copy.deepcopy(pair["input"])
        assert mod.self_check(source) == []
        assert mod.rule_mirror(source) == pair["output"]
        assert _independent_rule(source) == pair["output"]


def test_every_declared_profile_is_exactly_observable():
    seen = set()
    for index, profile in enumerate(mod.SCENE_PROFILES):
        grid = mod.generate(
            seed=1000 + index,
            sample_index=17 + index,
            difficulty=("easy", "medium", "hard")[index % 3],
            scene_profile=profile,
        )
        assert mod.self_check(grid) == []
        observed = mod.observe_overrides(grid)
        assert observed == {"scene_profile": profile}
        assert _independent_rule(grid) == mod.rule_mirror(grid)
        seen.add(observed["scene_profile"])
    assert seen == set(mod.SCENE_PROFILES)


def test_four_demo_schedule_always_identifies_all_rule_branches():
    for band in ("easy", "medium", "hard"):
        for start in range(32):
            counts = set()
            for sample_index in range(start, start + 4):
                grid = mod.generate(73, sample_index, difficulty=band)
                counts.update(touches for _, _, touches in _components(grid))
            assert {0, 1, 2}.issubset(counts)
            assert counts.intersection({3, 4})


def test_exact_override_contract_and_unknown_values_reject():
    for band in ("easy", "medium", "hard"):
        for profile in mod.SCENE_PROFILES:
            grid = mod.generate(91, 5, difficulty=band, scene_profile=profile)
            assert mod.observe_overrides(grid) == {"scene_profile": profile}
    with pytest.raises((ValueError, KeyError, AssertionError)):
        mod.generate(91, 5, difficulty="medium", scene_profile="not_a_profile")
    with pytest.raises((ValueError, KeyError, TypeError, AssertionError)):
        mod.generate(91, 5, difficulty="medium", undeclared_axis=1)


def test_determinism_freshness_and_global_random_purity():
    before = random.getstate()
    a = mod.generate(123, 6, difficulty="hard")
    after_a = random.getstate()
    b = mod.generate(123, 6, difficulty="hard")
    after_b = random.getstate()
    assert a == b
    assert a is not b
    assert all(row_a is not row_b for row_a, row_b in zip(a, b))
    assert before == after_a == after_b
    a[0][0] = 9 if a[0][0] != 9 else 8
    assert mod.generate(123, 6, difficulty="hard") == b


def test_self_check_rejects_four_targeted_impostors():
    base = mod.generate(37, 0, difficulty="medium", scene_profile="public_1")
    assert mod.self_check(base) == []

    # 1. Remove the only interior component entirely.
    no_interior = copy.deepcopy(base)
    interior = next(cells for _, cells, touches in _components(base) if touches == 0)
    for r, c in interior:
        no_interior[r][c] = 0
    assert mod.self_check(no_interior)

    # 2. Split a monochromatic component by deleting one articulation cell.
    split_component = copy.deepcopy(base)
    largest = max(_components(base), key=lambda item: len(item[1]))[1]
    for r, c in largest:
        trial = copy.deepcopy(base)
        trial[r][c] = 0
        if len(_components(trial)) != len(_components(base)):
            split_component = trial
            break
    assert split_component != base
    assert mod.self_check(split_component)

    # 3. Merge two disconnected objects with a new-color bridge.
    merged = copy.deepcopy(base)
    comps = _components(base)
    (_, left, _), (_, right, _) = comps[0], comps[1]
    lr, lc = left[0]
    rr, rc = right[0]
    bridge_color = merged[lr][lc]
    r, c = lr, lc
    while c != rc:
        c += 1 if rc > c else -1
        merged[r][c] = bridge_color
    while r != rr:
        r += 1 if rr > r else -1
        merged[r][c] = bridge_color
    assert mod.self_check(merged)

    # 4. Introduce an invalid ARC color without changing dimensions.
    invalid_color = copy.deepcopy(base)
    invalid_color[0][0] = 10
    assert mod.self_check(invalid_color)


def test_negative_recombination_is_rejected_by_distribution():
    # Replace the public_1 interior triomino with a feature absent from all
    # remaining scene parts: an isolated one-cell object at a new location.
    impostor = mod.generate(55, 0, difficulty="easy", scene_profile="public_1")
    interior = next(cells for _, cells, touches in _components(impostor) if touches == 0)
    for r, c in interior:
        impostor[r][c] = 0
    h, w = len(impostor), len(impostor[0])
    placement = next(
        (r, c)
        for r in range(1, h - 1)
        for c in range(1, w - 1)
        if impostor[r][c] == 0
        and all(
            impostor[r + dr][c + dc] == 0
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1))
        )
    )
    impostor[placement[0]][placement[1]] = 9
    assert mod.observe_overrides(impostor) == {}
    assert mod.self_check(impostor)
    # The output rule remains total: rejection is pedagogical, not an oracle crash.
    assert _independent_rule(impostor) == mod.rule_mirror(impostor)
