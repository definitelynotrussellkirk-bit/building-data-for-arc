"""Focused regressions for the same-color, four-connected odd-area task."""
from __future__ import annotations

import importlib.util
import copy
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
from functools import lru_cache

import pytest

from reviewer_support import canonical_pairs, canonical_path, find_root


TASK_ID = "ceef568b1cd4"
ROOT = find_root(__file__)
BANDS = ("easy", "medium", "hard")
ORIGINAL_RIVAL_NAMES = {
    "global_color_parity",
    "diagonal_component_parity",
    "colorblind_component_parity",
    "observed_odd_sizes_only",
    "observed_even_sizes_only",
}
RIVAL_NAMES = ORIGINAL_RIVAL_NAMES | {
    "odd_area_and_odd_color_total",
    "odd_area_and_odd_diagonal_total",
}


def _load_generator():
    home = Path(__file__).resolve().parent.parent
    path = Path(os.environ.get("GENERATOR_UNDER_TEST", home / "generator.py")).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_ceef568b1cd4", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load_generator()


def _load_probe():
    path = Path(__file__).resolve().parent.parent / "workspace" / "reference_probe.py"
    spec = importlib.util.spec_from_file_location("reference_probe_ceef568b1cd4", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


probe = _load_probe()


@lru_cache(maxsize=1)
def canonical():
    return canonical_pairs(TASK_ID, root=ROOT)


def declared_rivals():
    """Read all actual declarations, retaining their separate namespaces."""
    declarations = {}
    for namespace in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        rivals = getattr(gen, namespace)
        assert isinstance(rivals, dict) and rivals, namespace
        for name, predictor in rivals.items():
            assert isinstance(name, str) and callable(predictor), (namespace, name)
            declarations[namespace, name] = predictor
    return declarations


def isolated_scene(sizes, *, colors=None, height=20, width=20):
    colors = list(range(1, len(sizes) + 1)) if colors is None else colors
    grid = [[0] * width for _ in range(height)]
    for index, (size, color) in enumerate(zip(sizes, colors, strict=True)):
        for col in range(1, size + 1):
            grid[1 + 2 * index][col] = color
    return grid


def test_regression_exact_canonical_dimensions():
    grid = gen.generate(814, 0, difficulty="easy", grid_h=7, grid_w=7)
    assert (len(grid), len(grid[0])) == (7, 7)


def test_regression_unknown_override_rejected():
    with pytest.raises(ValueError):
        gen.generate(814, 0, unrecognized_axis=3)


def test_regression_blank_grid_rejected():
    assert gen.self_check([[0] * 7 for _ in range(7)])


@pytest.mark.parametrize("difficulty", BANDS)
def test_default_witness_refutes_joint_component_and_global_color_parity_shortcut(difficulty):
    grid = gen.generate(0, 1, difficulty=difficulty)
    rival = probe.expected_rival("odd_area_and_odd_color_total", grid)
    assert rival != probe.odd_area_output(grid)


@pytest.mark.parametrize("difficulty", BANDS)
def test_default_witness_refutes_joint_component_and_diagonal_parity_shortcut(difficulty):
    grid = gen.generate(0, 1, difficulty=difficulty)
    rival = probe.expected_rival("odd_area_and_odd_diagonal_total", grid)
    assert rival != probe.odd_area_output(grid)


def test_rule_pin_and_axis_contract():
    assert gen.TASK_ID == TASK_ID and gen.GENERATOR_ID == TASK_ID
    assert gen.RULE_HASH == "8abfb7183f00"
    assert gen.EXAMPLES_NEEDED == 3
    assert set(gen.AXES) == {"grid_h", "grid_w", "n", "n_distinct_colors"}
    for name, valid in {"grid_h": "7..20", "grid_w": "7..20",
                        "n": "2..6", "n_distinct_colors": "1..6"}.items():
        assert gen.AXES[name]["type"] == "int"
        assert gen.AXES[name]["valid"] == valid
    hashes = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                normalized = " ".join(row["program_solution"].split())
                hashes.add(hashlib.sha256(normalized.encode()).hexdigest()[:12])
    assert hashes == {gen.RULE_HASH}


def test_all_four_canonical_pairs_are_accepted_and_observable():
    assert len(canonical()) == 4
    profiles = set()
    for pair in canonical():
        grid = copy.deepcopy(pair["input"])
        original = copy.deepcopy(grid)
        expected_profile = probe.profile(grid)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == expected_profile
        assert probe.odd_area_output(grid) == pair["output"]
        assert grid == original
        profiles.add((expected_profile["grid_h"], expected_profile["grid_w"],
                      expected_profile["n"], expected_profile["n_distinct_colors"]))
    assert profiles == {(7, 8, 4, 4), (8, 8, 3, 3), (7, 7, 3, 3), (8, 9, 4, 4)}


@pytest.mark.parametrize("difficulty", BANDS)
def test_exact_override_joint_corners_and_every_count(difficulty):
    counts = ((2, 1), (2, 2), (3, 2), (3, 3), (4, 1),
              (4, 3), (5, 4), (6, 1), (6, 5), (6, 6))
    for height, width in ((7, 7), (7, 20), (20, 7), (20, 20)):
        for count, colors in counts:
            overrides = dict(grid_h=height, grid_w=width, n=count, n_distinct_colors=colors)
            grid = gen.generate(9131, count + colors, difficulty=difficulty, **overrides)
            assert probe.profile(grid) == overrides
            assert gen.observe_overrides(grid) == overrides
            assert gen.self_check(grid, difficulty=difficulty) == []
            sizes = [item["size"] for item in probe.components(grid)]
            assert all(1 <= size <= 9 for size in sizes)
            assert any(size % 2 for size in sizes) and any(size % 2 == 0 for size in sizes)


def test_every_integer_dimension_and_canonical_profile_is_realizable():
    for height in range(7, 21):
        overrides = dict(grid_h=height, grid_w=27 - height, n=2, n_distinct_colors=1)
        grid = gen.generate(71, height, **overrides)
        assert probe.profile(grid) == overrides
    for pair in canonical():
        overrides = probe.profile(pair["input"])
        for difficulty in BANDS:
            grid = gen.generate(19, 1, difficulty=difficulty, **overrides)
            assert probe.profile(grid) == overrides


@pytest.mark.parametrize("key,value", [
    ("palette_kind", "default"), ("palette_size", 3),
    ("position_bias", "scattered"), ("density", "sparse"),
    ("texture", "no_motifs"), ("texture", "single_motif"),
    ("texture", "identical_motif_colors"), ("unknown_axis", 3),
])
def test_removed_and_unknown_axes_raise_value_error(key, value):
    with pytest.raises(ValueError):
        gen.generate(18, 0, **{key: value})


@pytest.mark.parametrize("key,value", [
    ("grid_h", 6), ("grid_h", 21), ("grid_w", 6), ("grid_w", 21),
    ("n", 1), ("n", 7), ("n_distinct_colors", 0), ("n_distinct_colors", 7),
])
def test_out_of_range_exact_overrides_raise_value_error(key, value):
    for difficulty in BANDS:
        with pytest.raises(ValueError):
            gen.generate(18, 0, difficulty=difficulty, **{key: value})


@pytest.mark.parametrize("key,valid", [("grid_h", 7), ("grid_w", 7),
                                      ("n", 2), ("n_distinct_colors", 1)])
def test_exact_overrides_reject_booleans_floats_strings_and_containers(key, valid):
    for value in (True, False, float(valid), str(valid), [valid], {"value": valid}):
        with pytest.raises(ValueError):
            gen.generate(18, 0, **{key: value})


@pytest.mark.parametrize("count,colors", [(2, 3), (2, 6), (3, 4), (5, 6)])
def test_incompatible_exact_object_and_color_counts_raise(count, colors):
    with pytest.raises(ValueError):
        gen.generate(21, 1, n=count, n_distinct_colors=colors)


@pytest.mark.parametrize("grid", [None, 42, "000", [], [[]],
                                  [None], [[0] * 7, [0] * 6], [[0] * 7, 0]])
def test_self_check_reports_malformed_grids_without_raising(grid):
    errors = gen.self_check(grid)
    assert isinstance(errors, list) and errors
    assert all(isinstance(error, str) for error in errors)


@pytest.mark.parametrize("value", [True, False, 1.0, "2", None, -1, 10])
def test_self_check_rejects_invalid_cell_values(value):
    grid = probe.manual_witness()
    grid[5][0] = value
    assert gen.self_check(grid)


def test_self_check_rejects_outside_scope_and_vacuous_parity_examples():
    grids = {
        "single_odd": isolated_scene([3]),
        "single_even": isolated_scene([2]),
        "only_odd": isolated_scene([1, 3]),
        "only_even": isolated_scene([2, 4]),
        "seven_objects": isolated_scene([1, 1, 1, 1, 1, 1, 2]),
        "component_size_ten": isolated_scene([3, 10]),
        "height_above_twenty": isolated_scene([1, 2], height=21),
        "width_above_twenty": isolated_scene([1, 2], width=21),
        "height_below_seven": isolated_scene([1, 2], height=6),
        "width_below_seven": isolated_scene([1, 2], width=6),
    }
    for name, grid in grids.items():
        assert gen.self_check(grid), name


def test_self_check_accepts_same_color_reuse_touching_colors_and_all_area_limits():
    for odd, even in ((1, 2), (3, 4), (5, 6), (7, 8), (9, 2)):
        for colors in ([2, 2], [2, 5]):
            grid = isolated_scene([odd, even], colors=colors)
            assert gen.self_check(grid) == []
            assert gen.observe_overrides(grid) == probe.profile(grid)
    for grid in (probe.manual_witness(), probe.manual_witness(9, 3, 4)):
        assert probe.is_original_witness(grid)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == {"grid_h": 7, "grid_w": 7,
                                               "n": 4, "n_distinct_colors": 3}
    grid = probe.manual_full_witness()
    assert probe.is_full_witness(grid)
    assert gen.self_check(grid) == []
    assert gen.observe_overrides(grid) == {"grid_h": 7, "grid_w": 7,
                                           "n": 5, "n_distinct_colors": 3}


@pytest.mark.parametrize("difficulty", BANDS)
def test_default_core_and_full_witness_schedule(difficulty):
    core_profiles = set()
    core_sizes = set()
    all_sizes = set()
    for seed in (0, 137):
        flags = []
        for index in range(24):
            grid = gen.generate(seed, index, difficulty=difficulty)
            assert gen.self_check(grid, difficulty=difficulty) == []
            assert gen.observe_overrides(grid) == probe.profile(grid)
            all_sizes.update(item["size"] for item in probe.components(grid))
            full_witness = probe.is_full_witness(grid)
            flags.append(full_witness)
            if full_witness:
                assert index % 2 == 1
                assert probe.profile(grid)["n"] == 5
                assert probe.profile(grid)["n_distinct_colors"] == 3
            else:
                observed = probe.profile(grid)
                assert observed["n"] == observed["n_distinct_colors"]
                assert observed["n"] in (3, 4)
                assert 7 <= observed["grid_h"] <= 9 and 7 <= observed["grid_w"] <= 9
                core_profiles.add((observed["grid_h"], observed["grid_w"], observed["n"]))
                core_sizes.update(item["size"] for item in probe.components(grid))
        assert flags[0] != flags[1]
        assert all(flags[index] == flags[index + 2] for index in range(len(flags) - 2))
        assert all(any(flags[start:start + 3]) for start in range(len(flags) - 2))
    assert {(7, 7, 3), (7, 8, 4), (8, 8, 3), (8, 9, 4)} <= core_profiles
    assert {1, 2, 3, 4} <= core_sizes
    assert all_sizes == set(range(1, 10))


def test_strict_canonical_profile_is_distinct_from_the_broad_input_domain():
    assert gen.MIN_STRICT_FRAC == 0.4
    for pair in canonical():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
    for difficulty in BANDS:
        for index in range(12):
            grid = gen.generate(53, index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            if index % 2 == 0:
                assert gen.strict_canonical_like(grid) == []
            else:
                assert probe.is_full_witness(grid)
                assert gen.strict_canonical_like(grid)


def test_core_layout_support_includes_canonical_geometry_without_full_blank_cuts():
    first_training = next(pair for pair in canonical()
                          if pair["split"] == "train" and pair["pair_index"] == 0)
    assert not probe.has_full_blank_interior_cut(first_training["input"])
    supported = []
    for index in range(300):
        grid = gen.generate(46200 + index, 2 * index, difficulty="medium")
        assert gen.strict_canonical_like(grid) == []
        if not probe.has_full_blank_interior_cut(grid):
            supported.append((46200 + index, 2 * index))
    assert supported, "core placement excludes the canonical train0 no-blank-cut topology"


@pytest.mark.parametrize("height,width", [(7, 7), (7, 20), (20, 7)])
def test_forced_witness_fallback_preserves_pixels_and_refutes_every_rival(monkeypatch, height, width):
    original_place = gen._place
    blocked = []

    def fail_contact_placement(*args, **kwargs):
        if kwargs.get("contact") is not None:
            blocked.append(kwargs["contact"])
            return None
        return original_place(*args, **kwargs)

    monkeypatch.setattr(gen, "_place", fail_contact_placement)
    expected_profile = dict(grid_h=height, grid_w=width, n=5, n_distinct_colors=3)
    for difficulty in BANDS:
        for seed in (0, 29):
            grid = gen.generate(seed, 1, difficulty=difficulty, **expected_profile)
            assert probe.profile(grid) == expected_profile
            assert gen.observe_overrides(grid) == expected_profile
            assert gen.self_check(grid) == []
            assert probe.is_full_witness(grid)
            truth = probe.odd_area_output(grid)
            for identity, rival in declared_rivals().items():
                assert rival(copy.deepcopy(grid)) != truth, (difficulty, seed, identity)
    assert blocked, "contact placement was not forced to fail"


def test_actual_declared_rivals_fit_canonicals_but_each_fails_the_contact_witness():
    rivals = declared_rivals()
    assert {name for _, name in rivals} == RIVAL_NAMES
    assert RIVAL_NAMES <= set(gen.LESSON_COMPETITORS)
    assert RIVAL_NAMES <= set(gen.CANONICAL_SHORTCUTS)
    old_witness = probe.manual_witness()
    witness = probe.manual_full_witness()
    for (namespace, name), rival in rivals.items():
        for pair in canonical():
            assert rival(copy.deepcopy(pair["input"])) == pair["output"], (namespace, name)
        old_actual = rival(copy.deepcopy(old_witness))
        assert old_actual == probe.expected_rival(name, old_witness), (namespace, name)
        if name in ORIGINAL_RIVAL_NAMES:
            assert old_actual != probe.odd_area_output(old_witness), (namespace, name)
        else:
            assert old_actual == probe.odd_area_output(old_witness), (namespace, name)
        actual = rival(copy.deepcopy(witness))
        assert actual == probe.expected_rival(name, witness), (namespace, name)
        assert actual != probe.odd_area_output(witness), (namespace, name)


def test_rivals_are_pure_deterministic_and_match_their_declared_meanings():
    inputs = [probe.manual_witness(), probe.manual_witness(9, 3, 4), probe.manual_full_witness()]
    inputs += [gen.generate(47, index, difficulty="hard") for index in range(6)]
    for (namespace, name), rival in declared_rivals().items():
        for grid in inputs:
            source = copy.deepcopy(grid)
            state = random.getstate()
            first = rival(source)
            assert source == grid and random.getstate() == state, (namespace, name)
            rival(copy.deepcopy(inputs[-1]))
            assert rival(copy.deepcopy(grid)) == first, (namespace, name)
            assert first == probe.expected_rival(name, grid), (namespace, name)


@pytest.mark.parametrize("difficulty", BANDS)
def test_all_cyclic_starts_and_query_rotations_refute_every_actual_rival(difficulty):
    rivals = declared_rivals()
    for seed in (0, 91):
        for start in range(8):
            lesson = []
            for index in range(start, start + 4):
                grid = gen.generate(seed, index, difficulty=difficulty)
                lesson.append({"input": grid, "output": probe.odd_area_output(grid)})
            for query_index in range(4):
                demos = [pair for index, pair in enumerate(lesson) if index != query_index]
                query = lesson[query_index]
                assert any(probe.is_full_witness(pair["input"]) for pair in demos)
                for identity, rival in rivals.items():
                    assert any(rival(copy.deepcopy(pair["input"])) != pair["output"]
                               for pair in demos), (difficulty, seed, start, query_index, identity)
                original = copy.deepcopy((demos, query))
                assert gen.lesson_identifiable(demos, query) == []
                assert (demos, query) == original
                assert gen.lesson_identifiable(demos, query) == []


def test_geometry_and_color_renaming_preserve_domain_counts_and_parity():
    inputs = [pair["input"] for pair in canonical()]
    inputs.append(probe.manual_full_witness())
    inputs += [gen.generate(63, 1, difficulty=band) for band in BANDS]
    for grid in inputs:
        expected = probe.odd_area_output(grid)
        original_profile = probe.profile(grid)
        for reflected in (False, True):
            for rotation in range(4):
                changed = probe.recolor(probe.transform(grid, rotation, reflected))
                changed_output = probe.recolor(probe.transform(expected, rotation, reflected))
                assert gen.self_check(changed) == []
                assert gen.observe_overrides(changed) == probe.profile(changed)
                assert probe.odd_area_output(changed) == changed_output
                assert probe.profile(changed)["n"] == original_profile["n"]
                assert probe.profile(changed)["n_distinct_colors"] == original_profile["n_distinct_colors"]


def test_generation_is_deterministic_fresh_and_does_not_touch_global_rng():
    state = random.getstate()
    first = gen.generate(912, 1, difficulty="hard")
    assert random.getstate() == state
    second = gen.generate(912, 1, difficulty="hard")
    assert first == second
    assert first is not second and all(left is not right for left, right in zip(first, second))
    first[0][0] = (first[0][0] + 1) % 10
    assert gen.generate(912, 1, difficulty="hard") == second
    assert random.getstate() == state


def test_determinism_across_fresh_python_hash_seeds():
    script = """import hashlib, importlib.util, json, sys
spec = importlib.util.spec_from_file_location('hash_seed_generator', sys.argv[1])
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
grids = [gen.generate(119, index, difficulty=band)
         for band in ('easy', 'medium', 'hard') for index in range(6)]
print(hashlib.sha256(json.dumps(grids, separators=(',', ':')).encode()).hexdigest())
"""
    outputs = []
    for hash_seed in ("0", "1", "731"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        env["PYTHONPATH"] = os.pathsep.join(str(Path(path or '.').resolve()) for path in sys.path)
        result = subprocess.run([sys.executable, "-c", script, str(Path(gen.__file__).resolve())],
                                env=env, text=True, capture_output=True, check=True, timeout=30)
        outputs.append(result.stdout.strip())
    assert len(set(outputs)) == 1
    assert len(outputs[0]) == 64


def test_public_racket_authority_matches_independent_probe_in_one_batch():
    report = probe.reference_check(gen, root=ROOT, timeout=180)
    assert report["status"] == "pass", report["failures"]
    assert report["case_count"] == 54
    assert report["authority"]["executed_rule_hash"] == "8abfb7183f00"
    assert report["generator_sha256"] == hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest()
