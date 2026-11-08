from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from reviewer_support import canonical_path, find_root

ROOT = find_root(__file__)
TASK_ID = "bf5bed969a6d"
GEN_PATH = ROOT / "generators" / TASK_ID / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"test_gen_{TASK_ID}", GEN_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row():
    for line in canonical_path(ROOT).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def test_canonical_pairs_are_accepted_and_oracle_exact():
    generator = _load_generator()
    row = _canonical_row()
    signatures = set()
    for split in ("train", "test"):
        for pair in row[split]:
            before = [r[:] for r in pair["input"]]
            assert generator.self_check(pair["input"]) == []
            assert generator.oracle_output(pair["input"]) == pair["output"]
            assert pair["input"] == before
            signature = generator.canonical_profile_signature(pair["input"])
            assert signature is not None
            signatures.add(signature[:2])
    assert signatures == {
        ("canonical_0", "disjoint"),
        ("canonical_1", "disjoint"),
        ("canonical_2", "disjoint"),
        ("canonical_3", "occluded"),
    }


def test_strict_linked_profiles_reach_every_band_and_exclude_unlinked_profile():
    generator = _load_generator()
    for band in ("easy", "medium", "hard"):
        seen = set()
        matches = 0
        for sample_index in range(120):
            grid = generator.generate(7301, sample_index, difficulty=band)
            assert generator.self_check(grid, difficulty=band) == []
            signature = generator.canonical_profile_signature(grid)
            if signature is not None:
                matches += 1
                seen.add(signature[:2])
        assert matches >= 30
        assert seen == {
            ("canonical_0", "disjoint"),
            ("canonical_1", "disjoint"),
            ("canonical_2", "disjoint"),
            ("canonical_3", "occluded"),
        }

    recombined = generator.generate(
        19,
        2,
        grid_h=20,
        grid_w=22,
        profile_kind="canonical_3",
        overlap_kind="disjoint",
        palette_kind="mid",
    )
    assert generator.self_check(recombined) == []
    assert generator.canonical_profile_signature(recombined) is None


def test_exact_axes_are_observable_and_override_stable():
    generator = _load_generator()
    requested = {
        "grid_h": 20,
        "grid_w": 22,
        "profile_kind": "canonical_3",
        "overlap_kind": "occluded",
        "palette_kind": "split",
    }
    a = generator.generate(123, 7, difficulty="hard", **requested)
    b = generator.generate(123, 7, difficulty="hard", **requested)
    assert a == b
    assert a is not b
    assert a[0] is not b[0]
    assert generator.observe_overrides(a) == requested


def test_self_check_rejects_targeted_impostors():
    generator = _load_generator()
    good = generator.generate(
        88,
        3,
        grid_h=20,
        grid_w=22,
        profile_kind="canonical_0",
        overlap_kind="disjoint",
        palette_kind="low",
    )
    assert generator.self_check(good) == []

    all_bg = [[0 for _ in row] for row in good]
    assert generator.self_check(all_bg)

    no_template = [row[:] for row in good]
    for r, row in enumerate(no_template):
        for c, value in enumerate(row):
            if value == 2:
                no_template[r][c] = 0
    assert generator.self_check(no_template)

    broken_border = [row[:] for row in good]
    frame = generator._frame_descriptors(broken_border)[0]
    r, c = next(iter(frame["cells"]))
    broken_border[r][c] = 0
    assert generator.self_check(broken_border)

    interior_noise = [row[:] for row in good]
    frame = generator._frame_descriptors(interior_noise)[0]
    r0, c0, r1, c1 = frame["bbox"]
    interior_noise[r0 + 1][c0 + 1] = frame["color"]
    assert generator.self_check(interior_noise)

    bad_template = [row[:] for row in good]
    template = next(cells for color, cells in generator._components_4_same_color(bad_template) if color == 2)
    tr0, tc0, _, _ = generator._bbox(template)
    for r, c in template:
        bad_template[r][c] = 0
    for dc in range(3):
        bad_template[tr0][tc0 + dc] = 2
    assert generator.self_check(bad_template)

    novel_border = [row[:] for row in good]
    used = {value for row in novel_border for value in row}
    novel = next(value for value in range(1, 10) if value not in used and value != 2)
    frame = generator._frame_descriptors(novel_border)[0]
    r, c = frame["cells"][0]
    novel_border[r][c] = novel
    errors = generator.self_check(novel_border)
    assert errors
    assert any("three" in error or "exactly two" in error for error in errors)
