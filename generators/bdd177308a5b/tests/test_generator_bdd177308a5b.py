"""Regression tests for the canonical shape-matching generator repair."""
from __future__ import annotations

import copy
import hashlib
import json
import random
from collections import Counter
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.bdd177308a5b import generator as gen
from puzzle_generators.runner import _load_rule

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "bdd177308a5b"
BASE_PATHS = (
    ROOT / "data/base/solutions/training/63613498__bdd177308a5b.json",
    ROOT / "data/base/solutions/augmented/63613498__273d6c768d85.json",
)


def _canonical_rows():
    return [
        json.loads(line)
        for line in (ROOT / "data/canonical/puzzles.jsonl").read_text().splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    ]


def _pairs(row):
    out = []
    for split in ("train", "test"):
        value = row.get(split)
        out.extend(value if isinstance(value, list) else [value])
    return [pair for pair in out if isinstance(pair, dict)]


def _parts(grid):
    template = gen._normalize(gen._template_cells(grid))
    outside = [
        obj
        for obj in gen._components(grid)
        if not any(r < 3 and c < 3 for r, c in obj["cells"])
    ]
    matches = [obj for obj in outside if obj["norm"] == template]
    return template, outside, matches


def _expected_output(grid):
    _, _, matches = _parts(grid)
    assert len(matches) == 1
    output = copy.deepcopy(grid)
    for r, c in matches[0]["cells"]:
        output[r][c] = 5
    return output


def test_every_canonical_occurrence_has_exact_frame_and_exact_target():
    rows = _canonical_rows()
    assert {row["source"] for row in rows} == {"training", "augmented"}
    assert sum(len(_pairs(row)) for row in rows) == 8

    for row in rows:
        for pair in _pairs(row):
            grid = pair["input"]
            assert gen.self_check(grid) == []
            assert {
                (r, c)
                for r, line in enumerate(grid)
                for c, value in enumerate(line)
                if value == 5
            } == gen._CUE_CELLS
            template, outside, matches = _parts(grid)
            assert len(template) in {3, 4, 5}
            assert 3 <= len(outside) <= 5
            assert len(matches) == 1
            assert _expected_output(grid) == pair["output"]


def test_default_distribution_exercises_linked_semantic_branches():
    by_band = {}
    all_inputs = set()
    for band in ("easy", "medium", "hard"):
        sizes = Counter()
        distractors = Counter()
        zones = Counter()
        template_shapes = Counter()
        band_inputs = set()
        for seed in range(240):
            grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            observed = gen.observe_overrides(grid)
            template, outside, matches = _parts(grid)
            assert len(matches) == 1
            orbit = set(gen._dihedral(template))
            decoys = [obj for obj in outside if obj not in matches]
            assert any(obj["norm"] in orbit and obj["norm"] != template for obj in decoys)
            assert any(len(obj["cells"]) != len(template) for obj in decoys)
            sizes[observed["template_size"]] += 1
            distractors[observed["distractor_count"]] += 1
            zones[observed["target_zone"]] += 1
            template_shapes[template] += 1
            key = tuple(map(tuple, grid))
            band_inputs.add(key)
            all_inputs.add(key)
        by_band[band] = (sizes, distractors, zones, template_shapes, band_inputs)

    assert set(by_band["easy"][0]) == {3, 4}
    assert set(by_band["medium"][0]) == {4}
    assert set(by_band["hard"][0]) == {4, 5}
    assert set(by_band["easy"][1]) == {2, 3}
    assert set(by_band["medium"][1]) == {3}
    assert set(by_band["hard"][1]) == {3, 4}
    for band in by_band:
        assert set(by_band[band][2]) == set(gen.TARGET_ZONES)
        assert len(by_band[band][3]) >= 4
        assert len(by_band[band][4]) >= 235
    assert len(all_inputs) >= 710


def test_override_boundaries_are_exact_and_observable():
    cases = [
        {"grid_h": 10},
        {"grid_h": 14},
        {"grid_w": 10},
        {"grid_w": 14},
        {"template_size": 3},
        {"template_size": 5},
        {"distractor_count": 2},
        {"distractor_count": 4},
        *({"target_zone": zone} for zone in gen.TARGET_ZONES),
        {
            "grid_h": 10,
            "grid_w": 10,
            "template_size": 5,
            "distractor_count": 4,
            "target_zone": "top_right",
        },
        {
            "grid_h": 14,
            "grid_w": 14,
            "template_size": 3,
            "distractor_count": 2,
            "target_zone": "bottom_left",
        },
    ]
    for band in ("easy", "medium", "hard"):
        for case in cases:
            for seed in range(15):
                grid = gen.generate(
                    seed,
                    seed * 19 + 5,
                    difficulty=band,
                    **case,
                )
                assert gen.self_check(grid, difficulty=band) == []
                observed = gen.observe_overrides(grid)
                assert all(observed[key] == value for key, value in case.items())


@pytest.mark.parametrize(
    "case",
    [
        {"grid_h": 9},
        {"grid_w": 15},
        {"template_size": 2},
        {"distractor_count": 5},
        {"target_zone": "center"},
        {"texture": "no_cue"},
    ],
)
def test_invalid_or_unknown_overrides_fail_loudly(case):
    with pytest.raises(ValueError):
        gen.generate(1, 2, difficulty="medium", **case)


def test_self_check_rejects_targeted_semantic_impostors():
    grid = gen.generate(
        9201,
        71,
        difficulty="hard",
        grid_h=14,
        grid_w=14,
        template_size=5,
        distractor_count=4,
        target_zone="bottom_right",
    )
    template, outside, matches = _parts(grid)
    assert len(matches) == 1
    target = matches[0]
    decoys = [obj for obj in outside if obj not in matches]
    same_size_decoys = [obj for obj in decoys if len(obj["cells"]) == len(template)]
    assert same_size_decoys

    missing_cue = copy.deepcopy(grid)
    for r, c in gen._CUE_CELLS:
        missing_cue[r][c] = 0

    missing_target = copy.deepcopy(grid)
    for r, c in target["cells"]:
        missing_target[r][c] = 0

    changed_template = copy.deepcopy(grid)
    tr, tc = gen._template_cells(grid)[0]
    changed_template[tr][tc] = 0

    missing_same_size_decoys = copy.deepcopy(grid)
    for obj in same_size_decoys:
        for r, c in obj["cells"]:
            missing_same_size_decoys[r][c] = 0

    singleton = [[0 for _ in row] for row in grid]
    singleton[7][7] = 2

    duplicate_target = copy.deepcopy(grid)
    used = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    placement = None
    for zone in gen.TARGET_ZONES:
        for r0, c0 in gen._anchors_for_zone(template, len(grid), len(grid[0]), zone):
            cells = {(r0 + dr, c0 + dc) for dr, dc in template}
            if not cells & used:
                placement = (r0, c0)
                break
        if placement:
            break
    assert placement is not None
    unused_color = next(color for color in range(1, 10) if color not in {5, *[v for row in grid for v in row]})
    gen._paint(duplicate_target, template, *placement, unused_color)

    cases = {
        "missing_cue": missing_cue,
        "missing_target": missing_target,
        "changed_template": changed_template,
        "missing_same_size_decoys": missing_same_size_decoys,
        "singleton_only": singleton,
        "duplicate_target": duplicate_target,
    }
    for name, bad in cases.items():
        assert gen.self_check(bad, difficulty="hard", meta={"probe": name}), name


def test_determinism_freshness_and_global_random_state():
    random.seed(341)
    before = random.getstate()
    first = gen.generate(77, 33, difficulty="hard")
    assert random.getstate() == before
    second = gen.generate(77, 33, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    old = second[0][0]
    first[0][0] = (first[0][0] + 1) % 10
    assert second[0][0] == old


def test_rule_hash_and_both_task_local_sources_are_synced():
    rows = _canonical_rows()
    canonical = rows[0]["program_solution"]
    assert all(row["program_solution"] == canonical for row in rows)
    digest = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert gen.RULE_HASH == digest
    active, source = _load_rule(TASK_ID)
    assert active == canonical
    assert source.endswith("63613498__273d6c768d85.json")
    for path in BASE_PATHS:
        base = json.loads(path.read_text())
        assert base["racket_target"]["raw_code"] == canonical
        assert base["racket_target"]["target_code"] == canonical
