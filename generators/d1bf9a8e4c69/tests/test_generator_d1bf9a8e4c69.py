"""Focused regressions for the d1bf9a8e4c69 bbox-corner generator."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import random
import sys
from collections import Counter
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "shared" / "runtime"))
SPEC = importlib.util.spec_from_file_location(
    "review_d1bf9a8e4c69",
    REPO / "generators" / "d1bf9a8e4c69" / "generator.py",
)
assert SPEC is not None and SPEC.loader is not None
gen = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gen)


def _canonical_row() -> dict:
    path = REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == gen.TASK_ID:
                return row
    raise AssertionError(f"canonical task {gen.TASK_ID} not found")


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    return [*row["train"], *row["test"]]


def _episode(seed: int, start: int, band: str):
    demos = []
    for offset in range(gen.EXAMPLES_NEEDED):
        grid = gen.generate(seed, start + offset, difficulty=band)
        demos.append({"input": grid, "output": gen.rule_mirror(grid)})
    query_grid = gen.generate(seed, start + gen.EXAMPLES_NEEDED, difficulty=band)
    query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
    return demos, query


def test_rule_hash_canonical_inputs_and_python_mirror() -> None:
    row = _canonical_row()
    actual_hash = hashlib.sha256(
        " ".join(row["program_solution"].split()).encode()
    ).hexdigest()[:12]
    assert gen.RULE_HASH == actual_hash == "dc30ef9952c0"

    pairs = _canonical_pairs()
    assert len(pairs) == 3
    for pair in pairs:
        original = copy.deepcopy(pair["input"])
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == original


def test_canonical_shortcuts_really_fit_every_canonical_pair() -> None:
    pairs = _canonical_pairs()
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        assert all(rival(pair["input"]) == pair["output"] for pair in pairs), name


@pytest.mark.parametrize("shape_family", ["l_shape", "zigzag", "irregular", "mixed"])
@pytest.mark.parametrize("palette_pattern", ["distinct", "repeat_pair"])
def test_exact_axis_overrides_are_observable(
    shape_family: str, palette_pattern: str
) -> None:
    grid = gen.generate(
        41,
        7,
        difficulty="hard",
        grid_h=13,
        grid_w=14,
        object_count=4,
        shape_family=shape_family,
        palette_pattern=palette_pattern,
    )
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {
        "grid_h": 13,
        "grid_w": 14,
        "object_count": 4,
        "shape_family": shape_family,
        "palette_pattern": palette_pattern,
    }


def test_unknown_override_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown override axis"):
        gen.generate(0, 0, difficulty="easy", misspelled_axis=1)


def test_repeated_color_pair_refutes_per_color_bbox_shortcut() -> None:
    grid = gen.generate(
        73,
        9,
        difficulty="hard",
        grid_h=13,
        grid_w=14,
        object_count=4,
        shape_family="mixed",
        palette_pattern="repeat_pair",
    )
    components = gen._components(grid)
    counts = Counter(color for color, _ in components)
    assert sorted(counts.values()) == [1, 1, 2]
    assert gen._per_color_bbox(grid) != gen.rule_mirror(grid)


def test_irregular_family_has_nontrivial_shape_and_size_diversity() -> None:
    shapes = set()
    sizes = set()
    for sample_index in range(80):
        grid = gen.generate(
            211,
            sample_index,
            difficulty="hard",
            grid_h=13,
            grid_w=14,
            object_count=2,
            shape_family="irregular",
            palette_pattern="distinct",
        )
        for _, cells in gen._components(grid):
            shape = gen._normalize(cells)
            shapes.add(shape)
            sizes.add(len(shape))
    assert max(sizes) >= 8
    assert len(shapes) >= 24


def test_every_default_two_demo_window_refutes_named_competitors() -> None:
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for start in range(8):
            demos, query = _episode(90_000 + band_index * 100 + start, start, band)
            assert gen.lesson_identifiable(demos, query) == []
            for name, rival in gen.LESSON_COMPETITORS.items():
                assert any(
                    rival(demo["input"]) != demo["output"] for demo in demos
                ), (band, start, name)


def test_default_schedule_has_canonical_profile_support_in_every_band() -> None:
    for band in ("easy", "medium", "hard"):
        grids = [gen.generate(31337, index, difficulty=band) for index in range(24)]
        supported = sum(not gen.strict_canonical_like(grid) for grid in grids)
        assert supported >= 5, (band, supported)


def test_self_check_rejects_targeted_impostors() -> None:
    line_objects = [[0] * 9 for _ in range(8)]
    line_objects[1][1:5] = [2, 2, 2, 2]
    line_objects[6][4:8] = [3, 3, 3, 3]
    assert any("bbox" in error for error in gen.self_check(line_objects))

    full_rectangles = [[0] * 9 for _ in range(8)]
    for row in (1, 2):
        for col in (1, 2, 3):
            full_rectangles[row][col] = 2
    for row in (5, 6):
        for col in (5, 6, 7):
            full_rectangles[row][col] = 3
    assert any("fills its bbox" in error for error in gen.self_check(full_rectangles))

    touching_colors = [[0] * 9 for _ in range(8)]
    touching_colors[1][1:4] = [2, 2, 2]
    touching_colors[2][1] = 2
    touching_colors[2][2:5] = [3, 3, 3]
    touching_colors[3][4] = 3
    assert any("touch" in error for error in gen.self_check(touching_colors))


def test_determinism_fresh_returns_and_global_rng_purity() -> None:
    random.seed(9917)
    state = random.getstate()
    first = gen.generate(72, 5, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(72, 5, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second, strict=True))

    changed = copy.deepcopy(first)
    changed[0][0] = 9 if changed[0][0] != 9 else 8
    assert second != changed


def test_pinned_profile_census_meets_repository_envelope_floor() -> None:
    """Mirror the profile gate's public pinned-census contract."""
    hits = 0
    per_band = {}
    for band in ("easy", "medium", "hard"):
        band_hits = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{gen.TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = gen.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            if 8 <= profile[0] <= 9 and 9 <= profile[1] <= 11 and profile[2] == 3:
                band_hits += 1
        per_band[band] = band_hits
        hits += band_hits
    assert hits >= 15, per_band
    assert all(value >= 1 for value in per_band.values()), per_band


def test_distribution_probe_reports_source_bound_census() -> None:
    probe_path = (
        REPO
        / "generators"
        / "d1bf9a8e4c69"
        / "workspace"
        / "distribution_probe.py"
    )
    assert probe_path.exists(), "reusable distribution probe is missing"

    probe_spec = importlib.util.spec_from_file_location(
        "review_d1bf9a8e4c69_distribution_probe", probe_path
    )
    assert probe_spec is not None and probe_spec.loader is not None
    probe = importlib.util.module_from_spec(probe_spec)
    probe_spec.loader.exec_module(probe)

    report = probe.build_report(samples_per_band=4, lesson_starts=4)
    assert report["task_id"] == gen.TASK_ID
    assert report["generator_sha256"] == hashlib.sha256(
        (REPO / "generators" / gen.TASK_ID / "generator.py").read_bytes()
    ).hexdigest()
    assert report["sample_census"]["samples_per_band"] == 4
    assert report["sample_census"]["total_samples"] == 12
    assert report["canonical_shortcuts"]
    assert all(
        item["fits_all_canonical_pairs"]
        for item in report["canonical_shortcuts"].values()
    )
    assert report["lesson_windows"]["starts_per_band"] == 4
    assert report["lesson_windows"]["all_windows_identifiable"]
    assert report["profile_floor"]["total_samples"] == 60
    assert report["profile_floor"]["total_hits"] >= 15
