"""Portable semantic regressions tied to retained canonical Racket labels.

The coordinate oracle below shares no transformation, crop, or gallery helper
with production. Canonical pairs and five retained Racket-labeled inputs check
its expectations before the bounded CPU-only schedule census. Every declared
competitor is read from the selected generator rather than reimplemented here.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest


def _add_local_runtime_to_path():
    for ancestor in Path(__file__).resolve().parents:
        for candidate in (ancestor, ancestor / "shared" / "runtime"):
            if (candidate / "reviewer_support.py").is_file():
                sys.path.insert(0, str(candidate))
                return
    raise ImportError("No reviewer_support runtime in this test's own checkout")


_add_local_runtime_to_path()
from reviewer_support import canonical_pairs, find_root


TASK_ID = "2f58238f8bb6"
ROOT = find_root(__file__)
TASK_HOME = next(
    path for path in (
        ROOT / "generators" / TASK_ID,
        ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID,
    ) if (path / "generator.py").is_file()
)
_spec = importlib.util.spec_from_file_location("key_strip_schedule_regression", TASK_HOME / "generator.py")
generator = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(generator)
CANONICAL = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
SHORTCUT_NAMES = tuple(sorted(getattr(generator, "CANONICAL_SHORTCUTS", {})))
COMPETITOR_NAMES = tuple(sorted(getattr(generator, "LESSON_COMPETITORS", {})))
FIXTURE_DIR = Path(__file__).resolve().parents[1] / "workspace" / "fixtures"
FIXTURES = {
    name: json.loads((FIXTURE_DIR / f"{name}.json").read_text())
    for name in ("baseline_key3_ambiguity", "adjacent_repeated_keys")
}
SEEDS = (0, 1, 2, 3, 17, 73, 7919, 65537)
BANDS = ("easy", "medium", "hard")


def _grid_hash(grid):
    return hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()


def _body_pixels(grid):
    points = [(r, c, color) for r in range(1, len(grid))
              for c, color in enumerate(grid[r]) if color]
    assert points, "oracle requires a nonempty body"
    top, left = min(r for r, _, _ in points), min(c for _, c, _ in points)
    height = max(r for r, _, _ in points) - top + 1
    width = max(c for _, c, _ in points) - left + 1
    return height, width, [(r - top, c - left, color) for r, c, color in points]


def _coordinate_output(grid):
    """Place colored coordinates according to the four canonical key actions."""
    height, width, points = _body_pixels(grid)
    keys = [value for value in grid[0] if value]
    dimensions = [(width, height) if key == 2 else (height, width) for key in keys]
    result = [[0] * (sum(w for _, w in dimensions) + len(keys) - 1)
              for _ in range(max(h for h, _ in dimensions))]
    left = 0
    for key, (_, tile_width) in zip(keys, dimensions):
        for r, c, color in points:
            if key == 1:
                rr, cc = r, c
            elif key == 2:
                rr, cc = c, height - 1 - r
            elif key == 3:
                rr, cc = height - 1 - r, width - 1 - c
            elif key == 4:
                rr, cc = r, width - 1 - c
            else:
                raise AssertionError(f"unsupported key in independent oracle: {key}")
            result[rr][left + cc] = color
        left += tile_width + 1
    return result


def _distinct_dihedral_images(grid):
    """Enumerate coordinate images without production's D4 representation."""
    height, width, points = _body_pixels(grid)
    images = set()
    for reflected in (False, True):
        transformed = [(r, width - 1 - c if reflected else c, color) for r, c, color in points]
        h, w = height, width
        for _ in range(4):
            images.add((h, w, tuple(sorted(transformed))))
            transformed = [(c, h - 1 - r, color) for r, c, color in transformed]
            h, w = w, h
    return images


def _predict(rule, grid):
    return rule(deepcopy(grid))


def test_semantic_declarations_are_exercised_not_silently_empty():
    assert CANONICAL
    assert SHORTCUT_NAMES
    assert COMPETITOR_NAMES
    assert callable(getattr(generator, "lesson_identifiable", None))
    assert generator.EXAMPLES_NEEDED == 3
    assert set(SHORTCUT_NAMES) <= set(COMPETITOR_NAMES)
    assert all(callable(generator.CANONICAL_SHORTCUTS[name]) for name in SHORTCUT_NAMES)
    assert all(callable(generator.LESSON_COMPETITORS[name]) for name in COMPETITOR_NAMES)


@pytest.mark.parametrize("name", tuple(FIXTURES))
def test_racket_fixtures_retain_source_and_grid_hashes(name):
    fixture = FIXTURES[name]
    provenance = fixture["provenance"]
    assert fixture["task_id"] == TASK_ID
    assert provenance["generator_version"] == "2.0.1"
    assert provenance["generator_source_sha256"] == "fe1c9c0a903552d997ce36a8ec8e21d454bab1a3b25085f6ff930c0c2c6845a1"
    assert provenance["executed_rule_hash"] == generator.RULE_HASH
    for field in ("source_report_sha256", "source_counterexample_sha256", "rule_text_sha256"):
        value = provenance[field]
        assert len(value) == 64 and set(value) <= set("0123456789abcdef")
    assert "apply" in provenance["apply_command"]
    for pair in fixture["pairs"]:
        assert _grid_hash(pair["input"]) == pair["input_sha256"]
        assert _grid_hash(pair["output"]) == pair["output_sha256"]


ORACLE_PAIRS = [
    (f"canonical-{pair['variant']}-{pair['split']}-{pair['pair_index']}", pair)
    for pair in CANONICAL
] + [
    (f"racket-{name}-{index}", pair)
    for name, fixture in FIXTURES.items()
    for index, pair in enumerate(fixture["pairs"])
]


@pytest.mark.parametrize("name,pair", ORACLE_PAIRS, ids=[name for name, _ in ORACLE_PAIRS])
def test_independent_coordinate_oracle_matches_authoritative_labels(name, pair):
    assert _coordinate_output(pair["input"]) == pair["output"], name


@pytest.mark.parametrize("name", SHORTCUT_NAMES)
@pytest.mark.parametrize("pair", CANONICAL,
                         ids=[f"{p['split']}-{p['pair_index']}" for p in CANONICAL])
def test_each_declared_canonical_shortcut_fits_every_canonical_pair(name, pair):
    assert _predict(generator.CANONICAL_SHORTCUTS[name], pair["input"]) == pair["output"], name


@pytest.mark.parametrize("name", SHORTCUT_NAMES)
def test_actual_racket_repeated_key_witness_refutes_each_declared_shortcut(name):
    pair = FIXTURES["adjacent_repeated_keys"]["pairs"][0]
    assert generator.self_check(pair["input"]) == []
    assert _predict(generator.CANONICAL_SHORTCUTS[name], pair["input"]) != pair["output"], name


def test_preserved_baseline_lesson_exposes_a_real_declared_rival_and_fails_hook():
    fixture = FIXTURES["baseline_key3_ambiguity"]
    pairs = fixture["pairs"]
    demos = [pairs[index] for index in fixture["demonstration_indices"]]
    query = pairs[fixture["query_index"]]
    name = fixture["demonstration_compatible_rival"]
    rival = generator.LESSON_COMPETITORS[name]
    assert all(_predict(rival, pair["input"]) == pair["output"] for pair in demos)
    assert _predict(rival, query["input"]) != query["output"]
    reasons = generator.lesson_identifiable(deepcopy(demos), {"input": deepcopy(query["input"])})
    assert reasons and all(isinstance(reason, str) and reason for reason in reasons)


@lru_cache(maxsize=None)
def _window(band, seed, start):
    grids = [generator.generate(seed, start + offset, difficulty=band) for offset in range(4)]
    pairs = [{"input": grid, "output": _coordinate_output(grid)} for grid in grids]
    predictions = {
        name: [_predict(generator.LESSON_COMPETITORS[name], grid) for grid in grids]
        for name in COMPETITOR_NAMES
    }
    return pairs, predictions


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("start", (0, 1))
def test_default_window_has_two_distinct_asymmetric_teaching_pairs(band, seed, start):
    pairs, predictions = _window(band, seed, start)
    assert len({_grid_hash(pair["input"]) for pair in pairs}) == 4
    profiles = [generator.schedule_profile(seed, start + i, difficulty=band) for i in range(4)]
    assert profiles.count("teaching") == profiles.count("broad") == 2
    teaching_colors = set()
    for index, pair in enumerate(pairs):
        grid = pair["input"]
        assert generator.self_check(grid) == []
        if profiles[index] != "teaching":
            assert len(grid) >= 7
            continue
        assert (len(grid), len(grid[0])) == (6, 8)
        keys = [value for value in grid[0] if value]
        assert len(keys) == 5 and set(keys) == {1, 2, 3, 4}
        assert any(left != 0 and left == right for left, right in zip(grid[0], grid[0][1:]))
        height, width, points = _body_pixels(grid)
        assert height != width and len(_distinct_dihedral_images(grid)) == 8
        colors = {color for _, _, color in points}
        assert len(colors) == 1 and colors <= {1, 2, 3, 4}
        teaching_colors.update(colors)
        for name in COMPETITOR_NAMES:
            assert predictions[name][index] != pair["output"], (name, band, seed, start, index)
    assert len(teaching_colors) == 2


@pytest.mark.parametrize("band", BANDS)
@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("start", (0, 1))
@pytest.mark.parametrize("query_index", range(4))
def test_each_default_query_rotation_is_taught_against_every_declared_competitor(
    band, seed, start, query_index,
):
    pairs, predictions = _window(band, seed, start)
    demo_indices = [index for index in range(4) if index != query_index]
    demos = [deepcopy(pairs[index]) for index in demo_indices]
    query = {"input": deepcopy(pairs[query_index]["input"])}
    reasons = generator.lesson_identifiable(demos, query)
    assert reasons == [], (band, seed, start, query_index, reasons)
    for name in COMPETITOR_NAMES:
        assert any(predictions[name][index] != pairs[index]["output"] for index in demo_indices), (
            "declared competitor survives every demonstration", name, band, seed, start, query_index
        )
