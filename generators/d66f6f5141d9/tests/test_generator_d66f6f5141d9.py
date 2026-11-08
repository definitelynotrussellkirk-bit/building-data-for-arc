from __future__ import annotations

import copy
import hashlib
import json
import random
from pathlib import Path

import pytest

from puzzle_generators.per_puzzle.d66f6f5141d9 import generator as gen

ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "d66f6f5141d9"
SOLUTION_FILES = (
    ROOT / "data/base/solutions/augmented/f3e62deb__b87e1e60d845.json",
    ROOT / "data/base/solutions/training/f3e62deb__d66f6f5141d9.json",
)


def _canonical_rows():
    rows = []
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                rows.append(row)
    return rows


def _canonical_pairs():
    for row in _canonical_rows():
        for split in ("train", "test"):
            yield from row.get(split, [])


def _blank(h=10, w=10):
    return [[0 for _ in range(w)] for _ in range(h)]


def _paint(grid, cells, color):
    out = copy.deepcopy(grid)
    for r, c in cells:
        out[r][c] = color
    return out


def _bbox(grid):
    cells = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def test_canonical_inventory_acceptance_parity_and_input_purity():
    rows = _canonical_rows()
    pairs = list(_canonical_pairs())
    assert len(rows) == 2
    assert len(pairs) == 16
    assert {(len(row.get("train", [])), len(row.get("test", []))) for row in rows} == {(6, 2), (8, 0)}

    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_rule_hash_and_selected_task_local_authorities_are_canonical():
    canonical_programs = {row["program_solution"] for row in _canonical_rows()}
    assert len(canonical_programs) == 1
    canonical = canonical_programs.pop()
    normalized_hash = hashlib.sha256(" ".join(canonical.split()).encode()).hexdigest()[:12]
    assert normalized_hash == gen.RULE_HASH == "8df4c346e899"

    for path in SOLUTION_FILES:
        data = json.loads(path.read_text())
        target = data["racket_target"]
        assert target["target_code"] == canonical
        assert target["target_code_role"] == "selected_task_rule"
        assert target["raw_code_role"] == "archival_executable_source"
        assert target["raw_code"]
        assert target["canonicalization_status"] == "selected_canonical_with_preserved_archival_raw"


def test_every_axis_boundary_and_branch_survives_every_band():
    cases = []
    for difficulty in ("easy", "medium", "hard"):
        for grid_h in (5, 14):
            for grid_w in (6, 18):
                for color in gen.COLORS:
                    for shape_kind in gen.SHAPE_KINDS:
                        for distance_profile in gen.DISTANCE_PROFILES:
                            cases.append((difficulty, grid_h, grid_w, color, shape_kind, distance_profile))

    for index, (difficulty, grid_h, grid_w, color, shape_kind, distance_profile) in enumerate(cases):
        grid = gen.generate(
            seed=100_000 + index,
            sample_index=index,
            difficulty=difficulty,
            grid_h=grid_h,
            grid_w=grid_w,
            color=color,
            shape_kind=shape_kind,
            distance_profile=distance_profile,
        )
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {
            "grid_h": grid_h,
            "grid_w": grid_w,
            "color": color,
            "shape_kind": shape_kind,
            "distance_profile": distance_profile,
        }
        out = gen.rule_mirror(grid)
        assert out != grid
        rmin, cmin, rmax, cmax = _bbox(out)
        assert {
            3: cmin == 0,
            4: rmax == grid_h - 1,
            6: rmin == 0,
            8: cmax == grid_w - 1,
        }[color]


def test_default_distribution_has_all_semantic_branches_and_shortcut_rebuttals():
    for difficulty in ("easy", "medium", "hard"):
        seen_colors = set()
        seen_shapes = set()
        seen_distances = set()
        seen_dims = set()
        distinct_inputs = set()
        far_target_not_nearest = 0
        rings = 0
        canonical_profiles = 0
        for offset in range(240):
            grid = gen.generate(200_000 + offset, 0, difficulty=difficulty)
            info = gen.semantic_observables(grid)
            assert info["valid"]
            seen_colors.add(info["color"])
            seen_shapes.add(info["shape_kind"])
            seen_distances.add(info["distance_profile"])
            seen_dims.add((info["grid_h"], info["grid_w"]))
            distinct_inputs.add(json.dumps(grid, separators=(",", ":")))
            rings += info["shape_kind"] == "ring"
            canonical_profiles += (
                info["grid_h"] == 10
                and info["grid_w"] == 10
                and info["shape_kind"] == "ring"
            )
            far_target_not_nearest += (
                info["distance_profile"] == "far" and not info["target_is_nearest_edge"]
            )
        assert seen_colors == set(gen.COLORS)
        assert seen_shapes == set(gen.SHAPE_KINDS)
        assert seen_distances == set(gen.DISTANCE_PROFILES)
        assert len(seen_dims) >= 20
        assert len(distinct_inputs) >= 210
        assert far_target_not_nearest >= 80
        assert rings >= 100
        assert canonical_profiles >= 25


def test_self_check_rejects_targeted_structural_impostors():
    base = _blank()
    ring = tuple(gen._SHAPES["ring"])
    valid = _paint(base, ((r + 3, c + 3) for r, c in ring), 6)
    assert gen.self_check(valid) == []

    short_line = _paint(base, ((4, 3), (4, 4), (4, 5)), 6)
    solid_2x2 = _paint(base, ((3, 3), (3, 4), (4, 3), (4, 4)), 6)
    disconnected = copy.deepcopy(valid)
    disconnected[8][8] = 6
    mixed_colors = copy.deepcopy(valid)
    mixed_colors[3][3] = 4
    wrong_color = _paint(base, ((r + 3, c + 3) for r, c in ring), 2)
    already_target = _paint(base, ((r, c + 3) for r, c in ring), 6)

    impostors = {
        "short_line": short_line,
        "solid_2x2": solid_2x2,
        "disconnected": disconnected,
        "mixed_colors": mixed_colors,
        "wrong_color": wrong_color,
        "already_target": already_target,
    }
    for name, grid in impostors.items():
        assert gen.self_check(grid), f"self_check accepted {name}"

    # The selected Racket operation is total enough to translate the 2x2 block,
    # but that does not make it a valid teaching-distribution scene.
    assert gen.rule_mirror(valid) != valid
    with pytest.raises(ValueError, match="off-contract"):
        gen.rule_mirror(solid_2x2)


def test_lesson_schedule_makes_three_and_four_demo_queries_identifiable():
    query_counts_3 = {color: 0 for color in gen.COLORS}
    query_counts_4 = {color: 0 for color in gen.COLORS}
    three_demo_identifiable = 0
    four_demo_identifiable = 0
    distance_transfer_3 = 0
    distance_transfer_4 = 0
    for seed in range(300_000, 300_200):
        lesson = [gen.generate(seed, sample_index) for sample_index in range(5)]
        observations = [gen.observe_overrides(grid) for grid in lesson]
        train3 = observations[:3]
        train4 = observations[:4]
        query3 = observations[3]
        query4 = observations[4]
        three_demo_identifiable += (
            len({item["color"] for item in train3}) == 3
            and query3["color"] in {item["color"] for item in train3}
        )
        four_demo_identifiable += query4["color"] in {item["color"] for item in train4}
        same3 = next(item for item in train3 if item["color"] == query3["color"])
        same4 = next(item for item in train4 if item["color"] == query4["color"])
        distance_transfer_3 += same3["distance_profile"] != query3["distance_profile"]
        distance_transfer_4 += same4["distance_profile"] != query4["distance_profile"]
        query_counts_3[query3["color"]] += 1
        query_counts_4[query4["color"]] += 1
    assert three_demo_identifiable == 200
    assert four_demo_identifiable == 200
    assert distance_transfer_3 == 200
    assert distance_transfer_4 == 200
    assert query_counts_3 == {3: 50, 4: 50, 6: 50, 8: 50}
    assert query_counts_4 == {3: 50, 4: 50, 6: 50, 8: 50}


def test_determinism_fresh_returns_and_process_global_rng_isolation():
    kwargs = dict(
        seed=987_654,
        sample_index=17,
        difficulty="hard",
        grid_h=14,
        grid_w=18,
        color=8,
        shape_kind="L",
        distance_profile="far",
    )
    state_before = random.getstate()
    first = gen.generate(**kwargs)
    state_after = random.getstate()
    second = gen.generate(**kwargs)
    assert state_before == state_after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))

    first[0][0] = 9
    replay = gen.generate(**kwargs)
    assert replay == second

    source = copy.deepcopy(second)
    gen.rule_mirror(second)
    assert second == source


def test_unknown_and_invalid_overrides_reject_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, include_decoy=True)
    with pytest.raises(ValueError):
        gen.generate(0, 0, grid_h=4)
    with pytest.raises(ValueError):
        gen.generate(0, 0, grid_w=19)
    with pytest.raises(ValueError):
        gen.generate(0, 0, color=2)
    with pytest.raises(ValueError):
        gen.generate(0, 0, shape_kind="rect")
    with pytest.raises(ValueError):
        gen.generate(0, 0, distance_profile="middle")
    with pytest.raises(ValueError, match="unsupported difficulty"):
        gen.generate(0, 0, difficulty="nightmare")


def test_distribution_change_is_versioned():
    assert gen.VERSION == "3.0.0"
