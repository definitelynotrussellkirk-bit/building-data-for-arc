from __future__ import annotations

import copy
import random

import pytest

from puzzle_generators.generic.concepts.tile_blueprint import gen1 as mod


def _rotate90(grid):
    return [list(row) for row in zip(*grid[::-1])]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _d4(grid):
    r0 = [row[:] for row in grid]
    r1 = _rotate90(r0)
    r2 = _rotate90(r1)
    r3 = _rotate90(r2)
    f0 = _flip_lr(r0)
    f1 = _rotate90(f0)
    f2 = _rotate90(f1)
    f3 = _rotate90(f2)
    return (r0, r1, r2, r3, f0, f1, f2, f3)


def _palette_shift(grid, amount=3):
    return [[(value + amount) % 10 for value in row] for row in grid]


def test_generated_tasks_are_strict_exact_and_fresh():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(8):
            first = mod.generate_task(seed, difficulty=difficulty)
            second = mod.generate_task(seed, difficulty=difficulty)
            assert first == second
            assert first is not second
            assert mod.self_check_task(first) == []
            assert first["meta"]["rule_hash"] == mod.RULE_HASH
            assert first["meta"]["version"] == mod.VERSION
            seen = set()
            for pair in first["train"] + first["test"]:
                assert mod.strict_canonical_like(pair["input"]) == []
                assert mod._apply(pair["input"]) == pair["output"]
                assert pair["input"] != pair["output"]
                key = repr(pair["input"])
                assert key not in seen
                seen.add(key)
                for witness in mod.SEMANTIC_WITNESSES.values():
                    assert witness(pair["input"])
                for rival in mod.SEMANTIC_RIVALS.values():
                    assert rival(pair["input"]) != pair["output"]


def test_every_two_demo_window_identifies_the_rule():
    for difficulty in ("easy", "medium", "hard"):
        for seed in range(6):
            task = mod.generate_task(100 + seed, difficulty=difficulty)
            train = task["train"]
            for start in range(len(train) - mod.EXAMPLES_NEEDED + 1):
                demos = train[start : start + mod.EXAMPLES_NEEDED]
                for query in task["test"]:
                    assert mod.lesson_identifiable(demos, query) == []


def test_self_check_rejects_output_corruption_and_duplicate_pair():
    task = mod.generate_task(211, difficulty="medium")
    bad_output = copy.deepcopy(task)
    bad_output["train"][0]["output"][0][0] ^= 1
    assert any("output is not exact" in msg for msg in mod.self_check_task(bad_output))

    duplicate = copy.deepcopy(task)
    duplicate["test"][0] = copy.deepcopy(duplicate["train"][0])
    assert any("duplicates an earlier input" in msg for msg in mod.self_check_task(duplicate))


def test_strict_profile_rejects_four_rule_hiding_or_malformed_impostors():
    task = mod.generate_task(313, difficulty="medium")
    grid = task["train"][0]["input"]
    scene, reasons = mod._parse_scene(grid)
    assert not reasons and scene is not None

    # 1) Reveal the entire target.  Then completion is an identity/no-op lesson.
    dr, dc = scene["selected_offset"]
    full_target = {(r + dr, c + dc) for r, c in scene["mask"]}
    full_blueprint = mod._paint_target(grid, scene, full_target)
    assert any("strict subset" in msg or "change" in msg for msg in mod.strict_canonical_like(full_blueprint))

    # 2) Move the same partial evidence back to the tile origin.  This makes the
    #    no-translation shortcut viable and must be outside the teaching grammar.
    origin_shown = {(r - dr, c - dc) for r, c in scene["anomalies"]}
    origin_anchored = mod._paint_target(grid, scene, origin_shown)
    assert mod.strict_canonical_like(origin_anchored)

    # 3) Break the separator lattice itself.
    broken_lattice = copy.deepcopy(grid)
    replacement = next(v for v in range(10) if v != scene["sep"])
    broken_lattice[0][1] = replacement
    assert mod.strict_canonical_like(broken_lattice)

    # 4) Reduce the visible evidence until more than one translation fits.
    ambiguous = None
    mask = list(scene["mask"])
    target = [(r + dr, c + dc) for r, c in mask]
    for i in range(len(target)):
        for j in range(i + 1, len(target)):
            shown = {target[i], target[j]}
            if len(mod._valid_offsets(mask, scene["nr"], scene["nc"], shown)) > 1:
                ambiguous = mod._paint_target(grid, scene, shown)
                break
        if ambiguous is not None:
            break
    if ambiguous is None:
        for seed in range(314, 380):
            candidate = mod.generate_task(seed, difficulty="medium")["train"][0]["input"]
            cand_scene, cand_reasons = mod._parse_scene(candidate)
            assert not cand_reasons and cand_scene is not None
            cdr, cdc = cand_scene["selected_offset"]
            cmask = list(cand_scene["mask"])
            ctarget = [(r + cdr, c + cdc) for r, c in cmask]
            for i in range(len(ctarget)):
                for j in range(i + 1, len(ctarget)):
                    shown = {ctarget[i], ctarget[j]}
                    if len(mod._valid_offsets(cmask, cand_scene["nr"], cand_scene["nc"], shown)) > 1:
                        ambiguous = mod._paint_target(candidate, cand_scene, shown)
                        break
                if ambiguous is not None:
                    break
            if ambiguous is not None:
                break
    assert ambiguous is not None, "expected to find a deliberately ambiguous two-marker mutation"
    assert any("exactly one" in msg for msg in mod.strict_canonical_like(ambiguous))


def test_unknown_difficulty_rejects_without_mutating_global_rng():
    before = random.getstate()
    with pytest.raises(ValueError, match="unsupported difficulty"):
        mod.generate_task(0, difficulty="impossible")
    assert random.getstate() == before


def test_rule_is_d4_covariant_and_palette_permutation_safe_on_strict_scenes():
    for difficulty, seed in (("easy", 401), ("medium", 402), ("hard", 403)):
        pair = mod.generate_task(seed, difficulty=difficulty)["train"][0]
        for transformed_input, transformed_output in zip(_d4(pair["input"]), _d4(pair["output"])):
            assert mod._apply(transformed_input) == transformed_output
        shifted_input = _palette_shift(pair["input"])
        shifted_output = _palette_shift(pair["output"])
        assert mod._apply(shifted_input) == shifted_output
