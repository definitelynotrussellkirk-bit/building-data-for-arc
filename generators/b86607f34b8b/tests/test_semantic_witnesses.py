"""Independent, portable semantic regressions for the selected closure task.

The eleven fixed outputs came from the public Racket apply command retained in
workspace/semantic_review/authority_fixtures.json. Generated lesson comparisons
below use an independent diagnostic mirror for fast regression coverage; the
public, Racket-backed lesson census is the authoritative production check.
"""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest
from reviewer_support import canonical_pairs, find_root


ROOT = find_root(__file__)
TASK = "b86607f34b8b"
SOURCE = next(path for path in (
    ROOT / "generators" / TASK / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
) if path.is_file())
AUTHORING = next(path for path in (
    SOURCE.parent / "workspace" / "semantic_review",
    ROOT / "generators" / TASK / "workspace" / "semantic_review",
) if path.is_dir())


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


gen = _load("semantic_witness_selected_generator", SOURCE)
diagnostics = _load("semantic_witness_independent_mirror",
                    AUTHORING / "closure_diagnostics.py")
FIXTURES = json.loads((AUTHORING / "authority_fixtures.json").read_text())["cases"]


def _declared_rivals():
    declarations = []
    for namespace in ("SEMANTIC_RIVALS", "LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        rivals = getattr(gen, namespace, {})
        assert isinstance(rivals, dict), namespace
        for name, rival in rivals.items():
            assert isinstance(name, str) and name and callable(rival), (namespace, name)
            declarations.append((namespace, name, rival))
    assert declarations, "The generator must declare executable semantic rivals."
    return declarations


@pytest.mark.parametrize("case", FIXTURES, ids=lambda case: case["name"])
def test_racket_witness_is_lawful_and_matches_diagnostic_oracles(case):
    # Valid reference-domain inputs include simple one/two-color scenes, even
    # though the production teaching distribution may deliberately use more.
    assert gen.self_check(copy.deepcopy(case["input"])) == []
    assert diagnostics.predict(case["input"]) == case["output"]
    oracle = getattr(gen, "diagnostic_output", None)
    assert callable(oracle), "Missing diagnostic_output contract."
    assert oracle(copy.deepcopy(case["input"]), variant="reference") == case["output"]
    for row, column, value in case["assertions_global_rc_value"]:
        assert case["output"][row][column] == value


def test_every_declared_canonical_shortcut_fits_every_canonical_pair():
    shortcuts = getattr(gen, "CANONICAL_SHORTCUTS", None)
    assert isinstance(shortcuts, dict) and shortcuts, "Missing canonical shortcut declarations."
    pairs = canonical_pairs(TASK, root=ROOT)
    assert pairs, "Missing canonical authoring pairs."
    for name, rival in shortcuts.items():
        assert callable(rival), name
        for pair in pairs:
            predicted = rival(copy.deepcopy(pair["input"]))
            assert predicted == pair["output"], (name, pair["variant"],
                                                  pair["split"], pair["pair_index"])


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_declared_rivals_have_counterexamples_and_no_ambiguous_query_rotation(band):
    declarations = _declared_rivals()
    refuted_in_demos = {(namespace, name): 0 for namespace, name, _ in declarations}
    prediction_cache = {}
    label_cache = {}
    for seed in (101, 211):
        for start in range(6):
            pairs = []
            for index in range(start, start + 4):
                grid = gen.generate(seed, index, difficulty=band)
                assert gen.self_check(grid) == [], (band, seed, index)
                key = json.dumps(grid, separators=(",", ":"))
                if key not in label_cache:
                    label_cache[key] = diagnostics.predict(grid)
                pairs.append((grid, label_cache[key], key))
            for query_index in range(4):
                demo_indexes = [index for index in range(4) if index != query_index]
                for namespace, name, rival in declarations:
                    matches = []
                    for grid, expected, key in pairs:
                        cache_key = (namespace, name, key)
                        if cache_key not in prediction_cache:
                            prediction_cache[cache_key] = rival(copy.deepcopy(grid))
                        matches.append(prediction_cache[cache_key] == expected)
                    fits_demos = all(matches[index] for index in demo_indexes)
                    if not fits_demos:
                        refuted_in_demos[(namespace, name)] += 1
                    assert not (fits_demos and not matches[query_index]), (
                        "Ambiguous diagnostic lesson rotation", band, seed, start,
                        query_index, namespace, name,
                        {"inputs": [pair[0] for pair in pairs],
                         "demo_indexes": demo_indexes},
                    )
    absent = [key for key, count in refuted_in_demos.items() if count == 0]
    assert absent == [], ("Declared rivals never distinguished in demonstrations", band, absent)


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
def test_generated_support_teaches_mode3_order_one_pass_and_mode4_erasure(band):
    observed = {"mode3_order": False, "mode3_one_pass": False,
                "mode4_erasure": False, "mode4_new_bridge": False}
    for seed in (101, 211):
        for index in range(6):
            grid = gen.generate(seed, index, difficulty=band)
            expected = diagnostics.predict(grid)
            observed["mode3_order"] |= diagnostics.predict(grid, "mode3_reverse") != expected
            observed["mode3_one_pass"] |= diagnostics.predict(grid, "mode3_fixedpoint") != expected
            bridge_colors = {color for color, mode in zip(grid[0], grid[1])
                             if color and mode == 4}
            for color in bridge_colors:
                observed["mode4_erasure"] |= any(
                    grid[row][column] == color and expected[row][column] == 0
                    for row in range(3, len(grid)) for column in range(len(grid[0]))
                )
                observed["mode4_new_bridge"] |= any(
                    expected[row][column] == color and grid[row][column] != color
                    for row in range(3, len(grid)) for column in range(len(grid[0]))
                )
    assert all(observed.values()), (band, observed)


def test_explicit_four_color_override_preserves_rotated_lesson_teaching():
    pairs = []
    for index in range(4):
        grid = gen.generate(0, index, difficulty='easy', n_colors=4)
        pairs.append({'input': grid, 'output': diagnostics.predict(grid)})
    for query_index in range(4):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        for namespace, name, rival in _declared_rivals():
            assert not (all(rival(pair['input']) == pair['output'] for pair in demos)
                        and rival(pairs[query_index]['input']) != pairs[query_index]['output']), (query_index, namespace, name)


def test_four_color_tie_direction_is_not_encoded_by_mode_presence():
    # This independent conditional rival survived the earlier parity-based
    # curriculum. Two counterexamples per window survive any query holdout.
    pairs = []
    for index in range(4):
        grid = gen.generate(0, index, difficulty='easy', n_colors=4)
        pairs.append((grid, diagnostics.predict(grid)))
    for left_when_mode1 in (True, False):
        counterexamples = 0
        for grid, expected in pairs:
            has_mode1 = any(color and mode == 1 for color, mode in zip(grid[0], grid[1]))
            variant = ('legend_leftmost_tie' if has_mode1 == left_when_mode1
                       else 'legend_rightmost_tie')
            counterexamples += diagnostics.predict(grid, variant) != expected
        assert counterexamples >= 2, ('mode-presence tie shortcut', left_when_mode1, counterexamples)


@pytest.mark.parametrize('seed,index,band,overrides', [
    (0, 5, 'easy', {'n_colors': 4}),
    (23, 394, 'hard', {'grid_h': 14, 'grid_w': 11}),
    (1, 20, 'hard', {'grid_h': 13, 'grid_w': 10}),
])
def test_narrow_grid_duplicate_modes_do_not_exhaust_generation(seed, index, band, overrides):
    grid = gen.generate(seed, index, difficulty=band, **overrides)
    assert gen.self_check(grid) == []
    observed = gen.observe_overrides(grid)
    for name, value in overrides.items():
        assert observed[name] == value
