from __future__ import annotations

import copy
import importlib
import importlib.util
import json
import random
import sys
from pathlib import Path

import pytest

from puzzle_generators.helpers.selfcheck import components
ROOT = Path(__file__).resolve().parents[1]
LIBRARY = next((p for p in Path(__file__).resolve().parents if (p / "shared/runtime").is_dir()), None)
if LIBRARY is None:
    gen = importlib.import_module("puzzle_generators.per_puzzle.95fb3503a9be.generator")
else:
    sys.path.insert(0, str(LIBRARY / "shared/runtime"))
    spec = importlib.util.spec_from_file_location(
        "review_95fb3503a9be", LIBRARY / "generators/95fb3503a9be/generator.py"
    )
    assert spec is not None and spec.loader is not None
    gen = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gen)
    ROOT = LIBRARY / "shared"


def _canonical_row():
    with (ROOT / "data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError("canonical task row missing")


def _grid(value):
    if value and isinstance(value[0], str):
        return [[int(ch) for ch in row] for row in value]
    return copy.deepcopy(value)


def _pairs():
    row = _canonical_row()
    pairs = list(row["train"])
    test = row["test"]
    pairs.extend(test if isinstance(test, list) else [test])
    return [(_grid(pair["input"]), _grid(pair["output"])) for pair in pairs]


def _recolor_component(grid, comp, color):
    out = copy.deepcopy(grid)
    for r, c in comp["cells"]:
        out[r][c] = color
    return out


def test_rule_hash_is_pinned_to_assigned_authority():
    assert gen.RULE_HASH == "6d794ce158dc"


def test_all_canonical_inputs_are_accepted_and_mirrored_exactly():
    for inp, out in _pairs():
        assert gen.self_check(inp) == []
        assert gen.strict_canonical_like(inp) == []
        snapshot = copy.deepcopy(inp)
        assert gen.rule_mirror(inp) == out
        assert inp == snapshot


def test_schedule_exposes_every_semantic_witness():
    grids = [gen.generate(12345, i, difficulty="medium") for i in range(4)]
    for name, predicate in gen.SEMANTIC_WITNESSES.items():
        assert any(predicate(grid) for grid in grids), name


def test_equal_area_objects_use_color_ascending_tiebreak():
    grid = gen.generate(7, 0, difficulty="easy")
    records = gen._object_records(grid)
    tied_sizes = {rec["size"] for rec in records if sum(r["size"] == rec["size"] for r in records) > 1}
    assert tied_sizes
    order = gen._canonical_order(records)
    for size in tied_sizes:
        tied_colors = [records[i]["color"] for i in order if records[i]["size"] == size]
        assert tied_colors == sorted(tied_colors)


def test_exact_dimension_overrides_are_observable_across_bands():
    for band in ("easy", "medium", "hard"):
        for h in (gen.H_LO, gen.H_HI):
            for w in (gen.W_LO, gen.W_HI):
                grid = gen.generate(991, 1, difficulty=band, grid_h=h, grid_w=w)
                assert gen.observe_overrides(grid) == {"grid_h": h, "grid_w": w}


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = gen.generate(314159, 2, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(314159, 2, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert gen.generate(314159, 2, difficulty="hard") == second


def test_self_check_rejects_targeted_structural_impostors():
    grid = gen.generate(2026, 1, difficulty="medium")
    comps = components(grid, same_color=True)

    # 1. Missing object.
    missing = copy.deepcopy(grid)
    for r, c in comps[0]["cells"]:
        missing[r][c] = 0
    assert gen.self_check(missing)

    # 2. Duplicate object colors while keeping components spatially separate.
    duplicate_color = _recolor_component(grid, comps[1], comps[0]["color"])
    assert any("distinct" in reason for reason in gen.self_check(duplicate_color))

    # 3. Collapse one object to a singleton.
    singleton = copy.deepcopy(grid)
    for r, c in comps[2]["cells"][1:]:
        singleton[r][c] = 0
    assert any("sizes" in reason for reason in gen.self_check(singleton))

    # 4. Remove every hole/indent by filling each object's bbox.
    solid = copy.deepcopy(grid)
    for comp in comps:
        r1, c1, r2, c2 = comp["bbox"]
        for r in range(r1, r2 + 1):
            for c in range(c1, c2 + 1):
                solid[r][c] = comp["color"]
    assert any("non-rectangular" in reason for reason in gen.self_check(solid))

    # 5. Violate the object moat without merging colors.
    touching = copy.deepcopy(grid)
    left = min(comps, key=lambda comp: comp["bbox"][1])
    middle = sorted(comps, key=lambda comp: comp["bbox"][1])[1]
    lr1, lc1, lr2, lc2 = left["bbox"]
    mr1, mc1, mr2, mc2 = middle["bbox"]
    row = max(lr1, mr1)
    if row > min(lr2, mr2):
        row = lr1
    for c in range(lc2 + 1, mc1):
        touching[row][c] = left["color"]
    assert gen.self_check(touching)


def test_four_sample_lesson_rejects_named_rivals():
    demos = []
    for sample_index in range(4):
        inp = gen.generate(4321, sample_index, difficulty="medium")
        demos.append({"input": inp, "output": gen.rule_mirror(inp)})
    query_in = gen.generate(4321, 4, difficulty="medium")
    query = {"input": query_in, "output": gen.rule_mirror(query_in)}
    assert gen.lesson_identifiable(demos, query) == []


def test_public_semantic_rival_contract_is_complete_and_true_on_every_firing():
    # The semantic gate only verifies public declarations.  A witness without a
    # named executable rival proves feature presence, not rule discrimination.
    assert set(gen.SEMANTIC_WITNESSES) == set(gen.WITNESS_RIVALS)
    assert gen.LESSON_COMPETITORS
    assert set(gen.LESSON_COMPETITORS) == set(gen.SEMANTIC_RIVALS)
    assert "column_bands" in gen.SEMANTIC_RIVALS

    fired = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for band in ("easy", "medium", "hard"):
        for seed in range(32):
            for sample_index in range(4):
                grid = gen.generate(seed, sample_index, difficulty=band)
                official = gen.rule_mirror(grid)
                for witness_name, predicate in gen.SEMANTIC_WITNESSES.items():
                    if not predicate(grid):
                        continue
                    fired[witness_name] += 1
                    named_rivals = gen.WITNESS_RIVALS[witness_name]
                    assert named_rivals, witness_name
                    assert any(
                        gen.SEMANTIC_RIVALS[rival_name](grid) != official
                        for rival_name in named_rivals
                    ), (witness_name, band, seed, sample_index)

    assert all(count > 0 for count in fired.values()), fired


def _has_overlapping_bbox_columns(grid):
    records = gen._object_records(grid)
    return any(
        max(records[i]["bbox"][1], records[j]["bbox"][1])
        <= min(records[i]["bbox"][3], records[j]["bbox"][3])
        for i in range(len(records))
        for j in range(i + 1, len(records))
    )


def _max_crop_width(grid):
    return max(rec["bbox"][3] - rec["bbox"][1] + 1 for rec in gen._object_records(grid))


def test_each_four_sample_lesson_breaks_disjoint_vertical_band_segmentation():
    # Every canonical input has at least two objects whose bbox column ranges
    # overlap.  A curriculum made only of three disjoint x-bands teaches a
    # shortcut that does not generalize back to the source task.
    for seed in (0, 1, 7, 12345):
        lesson = [gen.generate(seed, i, difficulty="medium") for i in range(4)]
        assert any(_has_overlapping_bbox_columns(grid) for grid in lesson)


def test_each_four_sample_lesson_covers_the_canonical_four_column_crop():
    # Two canonical demonstrations contain a horizontal 1x4 crop.  The
    # generator's prior schedule declared that tetromino but never emitted it.
    for seed in (0, 1, 7, 12345):
        lesson = [gen.generate(seed, i, difficulty="medium") for i in range(4)]
        assert max(_max_crop_width(grid) for grid in lesson) >= 4


def test_unknown_override_keys_are_rejected():
    with pytest.raises(TypeError, match="unknown override"):
        gen.generate(11, 0, difficulty="medium", grid_width=12)
