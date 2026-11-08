"""Native overlap-family contracts, authored before the new implementation.

Run this file directly through the packet's protected-Racket review launcher.
These checks do not modify or qualify the production generator.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
PARAMETRIC = ROOT / "generators/0ae119475d57/workspace/parametric"
RUNTIME = ROOT / "shared/runtime"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(PARAMETRIC))
SETTINGS = ("lower_wins", "upper_wins", "denser_wins", "sparser_wins")
CANONICAL_SHA = "d9187ff88e80c4f19b71b0b33eb220d5115aa0703e2b675c9ceeb1a532d0bdd1"


def setting(name):
    return {"overlap_precedence": name}


@pytest.fixture(scope="module")
def family():
    return importlib.import_module("native_family")


@pytest.fixture(scope="module")
def adapter():
    return importlib.import_module("adapter")


def canonical_row():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        rows = [json.loads(line) for line in handle]
    selected = [row for row in rows if row.get("task_id") == "0ae119475d57"]
    assert len(selected) == 1
    return selected[0]


def test_settings_and_canonical_program_are_exact(family, adapter):
    assert tuple(family.SETTINGS) == SETTINGS
    text = family.program(setting("lower_wins"))
    assert text == canonical_row()["program_solution"]
    assert hashlib.sha256(text.encode()).hexdigest() == CANONICAL_SHA
    for name in SETTINGS:
        assert adapter.program(setting(name)) == family.program(setting(name))


@pytest.fixture(scope="module")
def racket():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    with _local_imports(RUNTIME, PARAMETRIC):
        apply_program, identity, bridge = _real_evaluator(RUNTIME)
        assert identity["backend"] == "racket"
        assert identity["protected"] is True
        try:
            yield apply_program
        finally:
            bridge.close()


def panels(kind="tied", height=5, width=4):
    """Four branch categories, with independently authored count imbalances."""
    top = [[0] * width for _ in range(height)]
    bottom = [[0] * width for _ in range(height)]
    top[0][0] = top[0][1] = 1
    bottom[0][0] = bottom[0][2] = 2
    if kind == "top_heavy":
        top[-1][-1] = 1
    elif kind == "bottom_heavy":
        bottom[-1][-1] = 2
    else:
        assert kind == "tied"
    return top, bottom


def pair_inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def split_panels(grid):
    """Read the specified equal-panel/one-or-two-row separator geometry."""
    separator_height = 1 if len(grid) % 2 else 2
    panel_height = (len(grid) - separator_height) // 2
    separator = grid[panel_height:panel_height + separator_height]
    assert separator[0][0] != 0
    assert all(value == separator[0][0] for row in separator for value in row)
    top, bottom = grid[:panel_height], grid[panel_height + separator_height:]
    assert len(top) == len(bottom)
    return top, bottom


def occupied(panel):
    return sum(value != 0 for row in panel for value in row)


def test_fixed_programs_preserve_exact_legacy_materialization(family):
    from arcpuzzles.parametric_worker import _local_imports

    with _local_imports(RUNTIME, PARAMETRIC):
        spec = importlib.util.spec_from_file_location(
            "legacy_overlap_for_native_tests", PARAMETRIC / "prototype.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for name in SETTINGS[:2]:
            assert family.program(setting(name)) == module.materialize_rule(name, root=ROOT)


def test_default_protected_racket_replays_all_four_official_pairs(family, racket):
    row = canonical_row()
    pairs = row["train"] + row["test"]
    assert len(pairs) == 4
    for pair in pairs:
        actual = racket(family.program(setting("lower_wins")), pair["input"])
        assert actual == pair["output"]
        assert family.apply_claim(pair["input"], setting("lower_wins")) == actual


@pytest.mark.parametrize("kind,winners", [
    ("tied", (2, 1, 2, 2)),
    ("top_heavy", (2, 1, 1, 2)),
    ("bottom_heavy", (2, 1, 2, 1)),
])
def test_all_settings_preserve_nonoverlap_and_use_correct_count_ties(family, racket, kind, winners):
    top, bottom = panels(kind)
    grid = family.make_input(top, bottom)
    untouched = copy.deepcopy(grid)
    for name, overlap_color in zip(SETTINGS, winners):
        expected = [[0] * 4 for _ in range(5)]
        expected[0] = [overlap_color, 1, 2, 0]
        if kind != "tied":
            expected[-1][-1] = 1 if kind == "top_heavy" else 2
        assert family.apply_claim(grid, setting(name)) == expected
        assert racket(family.program(setting(name)), grid) == expected
    assert grid == untouched


def test_remote_occupancy_changes_overlap_without_changing_local_pair(family, racket):
    top_heavy = family.make_input(*panels("top_heavy", width=6))
    bottom_heavy = family.make_input(*panels("bottom_heavy", width=6))
    assert (top_heavy[0][0], top_heavy[6][0]) == (bottom_heavy[0][0], bottom_heavy[6][0]) == (1, 2)
    for name, expected in (("denser_wins", (1, 2)), ("sparser_wins", (2, 1))):
        predicted = [racket(family.program(setting(name)), grid)
                     for grid in (top_heavy, bottom_heavy)]
        assert tuple(output[0][0] for output in predicted) == expected
        assert predicted == [family.apply_claim(grid, setting(name))
                             for grid in (top_heavy, bottom_heavy)]
        descriptions = [family.describe(grid, setting(name)) for grid in (top_heavy, bottom_heavy)]
        assert all(isinstance(value, dict) for value in descriptions)
        assert descriptions[0] != descriptions[1]


@pytest.mark.parametrize("seed", [0, 17])
def test_ties_constructively_reject_local_and_color_weighted_counts(family, racket, seed):
    """Dedicated ties teach global counts and color-invariant occupancy."""
    for name in SETTINGS[2:]:
        selected = setting(name)
        episode = family.generate(seed, selected, 4, 4)
        rivals = family.rivals(selected)
        for rival, index in (("row_local_counts", 2),
                             ("color_sum", 2 if name == "denser_wins" else 3)):
            pair = episode["train"][index]
            assert racket(rivals[rival], pair["input"]) != pair["output"]


def test_make_input_and_claim_outputs_are_fresh(family):
    top, bottom = panels()
    top_before, bottom_before = copy.deepcopy(top), copy.deepcopy(bottom)
    grid = family.make_input(top, bottom)
    assert len(grid) == 11 and grid[5] == [5] * 4
    grid[0][0] = 3
    assert top == top_before and bottom == bottom_before
    grid = family.make_input(top, bottom)
    before = copy.deepcopy(grid)
    first = family.apply_claim(grid, setting("denser_wins"))
    expected = copy.deepcopy(first)
    first[0][0] = 9
    assert grid == before
    assert family.apply_claim(grid, setting("denser_wins")) == expected


def test_fixed_and_selector_geometry_domains_are_separate(family, racket):
    for panel_height, separator_height in ((5, 2), (14, 1), (14, 2)):
        top, bottom = panels("top_heavy", height=panel_height, width=30)
        grid = family.make_input(top, bottom, separator_height=separator_height)
        assert len(grid) == 2 * panel_height + separator_height
        for name in SETTINGS[2:]:
            result = family.apply_claim(grid, setting(name))
            assert (len(result), len(result[0])) == (panel_height, 30)
            assert racket(family.program(setting(name)), grid) == result
        for name in SETTINGS[:2]:
            with pytest.raises((ValueError, TypeError)):
                family.apply_claim(grid, setting(name))


@pytest.mark.parametrize("seed", [True, False, -1, 2**63, 1.5, "1", None])
def test_generation_rejects_nonliteral_or_out_of_range_seeds(family, seed):
    with pytest.raises((ValueError, TypeError)):
        family.generate(seed, setting("lower_wins"), 4, 1)


@pytest.mark.parametrize("bad", [None, {}, {"overlap_precedence": True},
                                 {"overlap_precedence": "unknown"},
                                 {"overlap_precedence": "lower_wins", "extra": 1}])
def test_settings_require_one_exact_declared_key(family, bad):
    grid = family.make_input(*panels())
    for call in (lambda: family.program(bad),
                 lambda: family.generate(0, bad, 4, 1),
                 lambda: family.apply_claim(grid, bad),
                 lambda: family.describe(grid, bad)):
        with pytest.raises((ValueError, TypeError)):
            call()


@pytest.mark.parametrize("demos,queries", [(3, 1), (7, 1), (True, 1), (4.0, 1),
                                          (4, 0), (4, 5), (4, True), (4, 1.0)])
def test_demo_and_query_bounds_reject_coercions(family, demos, queries):
    with pytest.raises((ValueError, TypeError)):
        family.generate(0, setting("lower_wins"), demos, queries)


def test_strict_grid_and_constructor_validation(family):
    valid = family.make_input(*panels())
    malformed = [[], [[]], tuple(valid), [tuple(row) for row in valid], valid[:-1],
                 [row[:] for row in valid[:-1]] + [[0]], "not-a-grid"]
    for value in (True, -1, 10, 1.0, "1"):
        grid = copy.deepcopy(valid)
        grid[0][0] = value
        malformed.append(grid)
    for grid in malformed:
        for name in SETTINGS:
            with pytest.raises((ValueError, TypeError)):
                family.apply_claim(grid, setting(name))
            with pytest.raises((ValueError, TypeError)):
                family.describe(grid, setting(name))
    for height, width in ((4, 4), (15, 4), (5, 3), (5, 31)):
        top, bottom = panels(height=height, width=width)
        with pytest.raises((ValueError, TypeError)):
            family.make_input(top, bottom)
    for separator_height in (0, 3, True, 1.0):
        with pytest.raises((ValueError, TypeError)):
            family.make_input(*panels(), separator_height=separator_height)
    top, bottom = panels()
    top[0][0] = True
    with pytest.raises((ValueError, TypeError)):
        family.make_input(top, bottom)


def test_counts_have_independent_prefixes_and_generation_does_not_touch_global_rng(family, adapter):
    before_rng = random.getstate()
    for name in SETTINGS:
        selected = setting(name)
        full = family.generate(23, selected, 6, 4)
        assert len(full["train"]) == 6 and len(full["test"]) == 4
        assert all(len(pair["input"]) == 11 and len(pair["output"]) == 5
                   for pair in full["train"])
        assert family.generate(23, selected, 6, 4) == full
        for demos, queries in ((4, 1), (4, 4), (6, 1), (4, 2), (5, 3)):
            smaller = family.generate(23, selected, demos, queries)
            assert smaller["train"] == full["train"][:demos]
            assert smaller["test"] == full["test"][:queries]
        fingerprints = [json.dumps(pair["input"]) for pair in full["train"] + full["test"]]
        assert len(set(fingerprints)) == 10
        assert adapter.generate(23, selected, 4, 1) == family.generate(23, selected, 4, 1)
        fresh = family.generate(23, selected, 6, 4)
        full["train"][0]["input"][0][0] = 9 - full["train"][0]["input"][0][0]
        full["test"][0]["output"][0][0] = 9 - full["test"][0]["output"][0][0]
        assert family.generate(23, selected, 6, 4) == fresh
    assert random.getstate() == before_rng
    assert len(family.generate(2**63 - 1, setting("lower_wins"), 4, 1)["train"]) == 4


def test_teaching_inputs_are_matched_and_four_demos_identify_the_setting(family):
    episodes = {name: family.generate(0, setting(name), 4, 4) for name in SETTINGS}
    reference = episodes["lower_wins"]
    for name, episode in episodes.items():
        assert pair_inputs(episode, "train") == pair_inputs(reference, "train")
        assert pair_inputs(episode, "test")[:2] == pair_inputs(reference, "test")[:2]
        for other in SETTINGS:
            fits = all(family.apply_claim(pair["input"], setting(other)) == pair["output"]
                       for pair in episode["train"])
            assert fits == (name == other)
    for first, second in (("lower_wins", "upper_wins"), ("denser_wins", "sparser_wins")):
        assert pair_inputs(episodes[first], "test")[2:] == pair_inputs(episodes[second], "test")[2:]
    palettes = []
    for index, pair in enumerate(reference["train"]):
        top, bottom = split_panels(pair["input"])
        counts = occupied(top), occupied(bottom)
        assert counts == ((10, 7), (7, 10), (5, 5), (20, 20))[index]
        top_colors = {value for row in top for value in row if value}
        bottom_colors = {value for row in bottom for value in row if value}
        assert len(top_colors) == len(bottom_colors) == 1
        top_color, bottom_color = next(iter(top_colors)), next(iter(bottom_colors))
        palettes.append((top_color, bottom_color))
        if index < 2:
            assert top_color < bottom_color
        elif index == 2:
            assert top_color > bottom_color
        branches = {(bool(a), bool(b)) for upper, lower in zip(top, bottom) for a, b in zip(upper, lower)}
        assert branches == {(False, False), (True, False), (False, True), (True, True)}
    assert palettes[0] == palettes[1]


def test_both_selector_tie_scales_choose_lower(family, racket):
    for name in SETTINGS[2:]:
        selected = setting(name)
        episode = family.generate(0, selected, 4, 1)
        for index, count in ((2, 5), (3, 20)):
            pair = episode["train"][index]
            top, bottom = split_panels(pair["input"])
            assert occupied(top) == occupied(bottom) == count
            expected = [[b if b else a for a, b in zip(upper, lower)]
                        for upper, lower in zip(top, bottom)]
            assert pair["output"] == expected
            assert racket(family.program(selected), pair["input"]) == expected


def test_query_geometry_and_all_episode_labels_have_protected_racket_parity(family, racket):
    for name in SETTINGS:
        selected = setting(name)
        episode = family.generate(0, selected, 4, 4)
        queries = episode["test"]
        assert (len(queries[0]["input"]), len(queries[0]["input"][0])) == (11, 4)
        assert len(queries[1]["input"]) == 11
        assert len(queries[2]["input"]) == (11 if name in SETTINGS[:2] else 19)
        assert (len(queries[3]["input"]), len(queries[3]["input"][0])) == ((11, 30) if name in SETTINGS[:2] else (30, 30))
        assert (len(queries[3]["output"]), len(queries[3]["output"][0])) == ((5, 30) if name in SETTINGS[:2] else (14, 30))
        if name in SETTINGS[2:]:
            top, bottom = split_panels(queries[3]["input"])
            for panel in (top, bottom):
                assert occupied(panel) >= 60
                assert any(panel[0]) and any(panel[-1])
                assert any(row[0] for row in panel) and any(row[-1] for row in panel)
        for pair in episode["train"] + queries:
            expected = racket(family.program(selected), pair["input"])
            assert pair["output"] == expected
            assert family.apply_claim(pair["input"], selected) == expected


def test_public_turn_reveals_one_query_and_is_independent_of_private_or_future_data(family):
    selected = setting("denser_wins")
    episode = family.generate(0, selected, 4, 4)
    original = copy.deepcopy(episode)
    for index in range(4):
        public = family.public_turn(episode, index)
        assert set(public) == {"train", "test"}
        assert len(public["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in public["train"])
        assert public["test"] == [{"input": episode["test"][index]["input"]}]
        assert public["train"] == [{"input": pair["input"], "output": pair["output"]}
                                   for pair in episode["train"]]
    first = family.public_turn(episode, 0)
    assert first == family.public_turn(family.generate(0, selected, 4, 1), 0)
    tainted = copy.deepcopy(episode)
    tainted.update(seed=12345, settings=setting("sparser_wins"), program="private-program-marker")
    tainted["test"][0]["output"] = [[9]]
    tainted["test"][1]["input"] = [[8]]
    assert family.public_turn(tainted, 0) == first
    first["train"][0]["input"][0][0] = 9 - first["train"][0]["input"][0][0]
    first["train"][0]["output"][0][0] = 9 - first["train"][0]["output"][0][0]
    first["test"][0]["input"][0][0] = 9 - first["test"][0]["input"][0][0]
    assert episode == original
    for index in (-1, 4, True, 0.0, None):
        with pytest.raises((ValueError, TypeError, IndexError)):
            family.public_turn(episode, index)
