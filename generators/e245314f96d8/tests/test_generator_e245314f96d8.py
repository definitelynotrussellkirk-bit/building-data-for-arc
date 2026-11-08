from __future__ import annotations

import copy
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
_GENERATOR_PATH = ROOT / "generators" / "e245314f96d8" / "generator.py"
_SPEC = importlib.util.spec_from_file_location("review_e245314f96d8_generator", _GENERATOR_PATH)
assert _SPEC and _SPEC.loader
gen = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = gen
_SPEC.loader.exec_module(gen)


def _binary_crop(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    top = min(r for r, _ in cells)
    bottom = max(r for r, _ in cells)
    left = min(c for _, c in cells)
    right = max(c for _, c in cells)
    return tuple(
        tuple(1 if grid[r][c] else 0 for c in range(left, right + 1))
        for r in range(top, bottom + 1)
    )


def _rotate(grid):
    return tuple(tuple(row) for row in zip(*grid[::-1]))


def _flip(grid):
    return tuple(tuple(reversed(row)) for row in grid)


def _d4_normalized_binary_key(grid):
    cropped = _binary_crop(grid)
    variants = []
    for reflected in (False, True):
        current = _flip(cropped) if reflected else cropped
        for _ in range(4):
            variants.append(current)
            current = _rotate(current)
    return min(variants)


def _internal_topology_signature(grid):
    facts = gen._analyze(grid)["facts"]
    by_degree = {
        degree: next(index for index, value in enumerate(facts["degrees"]) if value == degree)
        for degree in (2, 3, 4)
    }
    return tuple(
        by_degree[right] in facts["graph"][by_degree[left]]
        for left, right in ((4, 3), (4, 2), (3, 2))
    )


def _canonical_row():
    pairs = canonical_pairs(gen.TASK_ID, root=ROOT)
    assert len(pairs) >= 2
    return {"train": pairs[:-1], "test": pairs[-1]}


def _pairs(seed: int, start: int, band: str):
    pairs = []
    for sample_index in range(start, start + 4):
        grid = gen.generate(seed, sample_index, difficulty=band)
        pairs.append({"input": grid, "output": gen.rule_mirror(grid)})
    return pairs


def test_canonical_pairs_are_owned_and_mirror_matches():
    row = _canonical_row()
    pairs = row["train"] + [row["test"]]
    assert [gen.observe_overrides(pair["input"])["scene_profile"] for pair in pairs] == [
        "chain",
        "star",
        "star",
    ]
    for pair in pairs:
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]


def test_default_schedule_and_exact_override_are_observable():
    for band in ("easy", "medium", "hard"):
        observed = [
            gen.observe_overrides(gen.generate(91, index, difficulty=band))[
                "scene_profile"
            ]
            for index in range(6)
        ]
        assert observed == ["chain", "star", "all_degrees"] * 2
        for profile in gen.SCENE_PROFILES:
            grid = gen.generate(17, 23, difficulty=band, scene_profile=profile)
            assert gen.observe_overrides(grid) == {"scene_profile": profile}
            assert gen.self_check(grid, meta={"scene_profile": profile}) == []

    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, difficulty="easy", height=8)
    with pytest.raises(ValueError, match="difficulty"):
        gen.generate(0, 0, difficulty="extreme")


def test_all_degrees_scene_refutes_color_and_size_lookups():
    grid = gen.generate(123, 2, difficulty="hard")
    signature = gen.semantic_signature(grid)
    assert signature["scene_profile"] == "all_degrees"
    assert set(signature["degree_histogram"]) == {0, 1, 2, 3, 4}
    assert any(len(values) >= 3 for values in signature["repeated_color_degrees"].values())

    analysis = gen._analyze(grid)
    facts = analysis["facts"]
    by_color = {}
    by_size = {}
    for obj, degree in zip(facts["components"], facts["degrees"]):
        by_color.setdefault(obj["color"], set()).add(gen._degree_color(degree))
        by_size.setdefault(obj["size"], set()).add(gen._degree_color(degree))
    assert any(len(outputs) >= 3 for outputs in by_color.values())
    assert any(len(outputs) >= 4 for outputs in by_size.values())


def test_all_degrees_sampler_breaks_the_retained_finite_template_shortcut():
    normalized_masks = set()
    internal_topologies = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(64):
            grid = gen.generate(
                10_000 + seed,
                band_index * 10_000 + seed * 3 + 2,
                difficulty=band,
                scene_profile="all_degrees",
            )
            normalized_masks.add(_d4_normalized_binary_key(grid))
            internal_topologies.add(_internal_topology_signature(grid))

    # The retained reviewer reproduced the old sampler with only one
    # all_degrees morphology (eight D4 keys).  Require broad morphology and
    # every non-isomorphic ordering of the unique degree-2/3/4 spine.
    assert len(normalized_masks) >= 48
    assert len(internal_topologies) == 3


def test_self_check_rejects_structural_impostors():
    base = gen.generate(314, 0, difficulty="easy", scene_profile="chain")
    analysis = gen._analyze(base)
    facts = analysis["facts"]

    ragged = copy.deepcopy(base)
    ragged[0].pop()
    assert gen.self_check(ragged)

    missing_isolate = copy.deepcopy(base)
    isolated_index = facts["degrees"].index(0)
    for row, col in facts["components"][isolated_index]["cells"]:
        missing_isolate[row][col] = 0
    assert gen.self_check(missing_isolate)

    merged_objects = copy.deepcopy(base)
    first = next(index for index, neighbors in enumerate(facts["graph"]) if neighbors)
    second = next(iter(facts["graph"][first]))
    replacement = facts["components"][first]["color"]
    for row, col in facts["components"][second]["cells"]:
        merged_objects[row][col] = replacement
    assert gen.self_check(merged_objects)

    extra_contact = copy.deepcopy(base)
    isolate = facts["components"][isolated_index]
    occupied = {
        cell for component in facts["components"] for cell in component["cells"]
    }
    target = None
    for row, col in isolate["cells"]:
        for delta_row, delta_col in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            candidate = (row + delta_row, col + delta_col)
            if (
                0 <= candidate[0] < len(base)
                and 0 <= candidate[1] < len(base[0])
                and candidate not in occupied
            ):
                target = candidate
                break
        if target is not None:
            break
    assert target is not None
    used = {value for row in base for value in row}
    new_color = next(color for color in gen.INPUT_COLORS if color not in used)
    extra_contact[target[0]][target[1]] = new_color
    assert gen.self_check(extra_contact)


def test_determinism_fresh_returns_input_purity_and_global_rng():
    state = random.getstate()
    first = gen.generate(2026, 8, difficulty="medium")
    assert random.getstate() == state
    snapshot = copy.deepcopy(first)
    second = gen.generate(2026, 8, difficulty="medium")
    assert first == second == snapshot
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))

    first[0][0] = 9 if first[0][0] != 9 else 1
    replay = gen.generate(2026, 8, difficulty="medium")
    assert replay == snapshot
    before = copy.deepcopy(replay)
    gen.rule_mirror(replay)
    gen.self_check(replay)
    gen.observe_overrides(replay)
    assert replay == before
    assert random.getstate() == state


def test_every_sequential_three_demo_lesson_is_identifiable():
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for start in range(3):
                pairs = _pairs(seed, start, band)
                assert gen.lesson_identifiable(pairs[:3], pairs[3]) == []
