"""Focused tests for the proposed layer-selection prototype, not canonical repairs.

Fixtures are hand-painted or drawn from the unchanged canonical ledger. Labels
are independently executed in Racket; public identifiers are checked against the
shared projection of visible demonstrations and query inputs.
"""
from __future__ import annotations

from copy import deepcopy
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "7b0cb3b9a618"
TASK_HOME = Path(__file__).resolve().parents[1]
ROOT = TASK_HOME.parents[1]
SOURCE = TASK_HOME / "workspace/parametric/layer_selection.py"
LEDGER = ROOT / "shared/data/canonical/puzzles.jsonl"
CANONICAL = next(
    json.loads(line) for line in LEDGER.read_text().splitlines()
    if json.loads(line).get("task_id") == TASK_ID
)
CANONICAL_PAIRS = CANONICAL["train"] + CANONICAL["test"]
BACK_COLORS = [2, 3, 1, 1, 3, 1]
PROFILES = [(3, 3, 2), (8, 12, 4), (9, 11, 4),
            (11, 11, 5), (11, 12, 5), (11, 13, 4)]


@pytest.fixture(scope="session")
def prototype():
    assert SOURCE.is_file(), "proposed layer-selection prototype is not implemented"
    spec = importlib.util.spec_from_file_location("layer_selection_under_test", SOURCE)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def labeler(prototype):
    with prototype.RacketLabeler() as instance:
        assert instance.runtime_identity
        yield instance


@pytest.fixture(scope="session")
def episodes(prototype, labeler):
    # Omitting the parameter in the first call also exercises the canonical default.
    return {
        "front": prototype.build_episode(190807, demo_count=3, query_count=4, labeler=labeler),
        "back": prototype.build_episode(190807, target_layer="back", demo_count=3,
                                        query_count=4, labeler=labeler),
    }


def _paint(height, width, bands):
    """Independent fixture painter: each tuple is (orientation, span, color)."""
    grid = [[0] * width for _ in range(height)]
    for orientation, span, color in bands:
        if orientation == "h":
            for row in span:
                grid[row] = [color] * width
        else:
            for col in span:
                for row in range(height):
                    grid[row][col] = color
    return grid


def _uniform_row_rival(grid):
    """The retained canonical rival incorrectly chooses a dirty row's majority."""
    width = len(grid[0])
    for row in grid:
        if row[0] and len(set(row)) == 1:
            return [[row[0]]]
    for row in grid:
        if row[0] and row.count(row[0]) > width - 2:
            return [[row[0]]]
    return [[0]]


def _grid_key(grid):
    return tuple(tuple(row) for row in grid)


def test_prototype_source_is_available():
    assert SOURCE.is_file(), "proposed layer-selection prototype is not implemented"


@pytest.mark.parametrize("index", range(6))
def test_original_front_labels_and_visible_back_endpoints(prototype, labeler, index):
    pair = CANONICAL_PAIRS[index]
    endpoints = prototype.visible_endpoints(pair["input"])
    assert endpoints["front"] == pair["output"][0][0]
    assert endpoints["back"] == BACK_COLORS[index]
    assert labeler.label(prototype.program_for("front"), pair["input"]) == pair["output"]
    assert labeler.label(prototype.program_for("back"), pair["input"]) == [[BACK_COLORS[index]]]


def test_front_program_preserves_exact_selected_authority(prototype):
    # Exact text is the authority contract, separate from semantic label parity.
    assert prototype.program_for("front") == CANONICAL["program_solution"]


@pytest.mark.parametrize(
    "grid, front, back, edges",
    [
        ([[0, 1, 0], [3, 3, 3], [0, 1, 0]], 3, 1, {(1, 3)}),
        ([[0, 1, 0], [3, 1, 3], [0, 1, 0]], 1, 3, {(3, 1)}),
        (_paint(9, 11, [("h", (2,), 2), ("v", (3,), 6),
                       ("h", (6,), 4), ("v", (7,), 8)]),
         8, 2, {(2, 6), (2, 8), (6, 4), (4, 8)}),
        # Middle vertical layers are incomparable. Endpoint selection must not
        # mistakenly demand a unique complete topological order.
        (_paint(11, 11, [("h", (1,), 1), ("v", (2,), 2),
                        ("v", (7,), 8), ("h", (6,), 4), ("v", (4,), 6)]),
         6, 1, {(1, 2), (1, 8), (1, 6), (2, 4), (8, 4), (4, 6)}),
    ],
)
def test_hand_painted_pixels_determine_endpoints(prototype, labeler, grid, front, back, edges):
    observed = prototype.visible_endpoints(grid)
    assert observed["front"] == front
    assert observed["back"] == back
    assert {tuple(edge) for edge in observed["edges"]} == edges
    assert front != back
    assert labeler.label(prototype.program_for("front"), grid) == [[front]]
    assert labeler.label(prototype.program_for("back"), grid) == [[back]]


def test_twelve_input_slots_retain_profiles_and_both_front_orientations(prototype, labeler):
    for index in range(12):
        grid = prototype.sample_input(61317, index)
        assert grid == prototype.sample_input(61317, index)
        colors = {cell for row in grid for cell in row}
        assert (len(grid), len(grid[0]), len(colors - {0})) == PROFILES[index // 2]
        assert 0 in colors
        endpoints = prototype.visible_endpoints(grid)
        front = endpoints["front"]
        clean_rows = [r for r, row in enumerate(grid) if set(row) == {front}]
        clean_cols = [c for c in range(len(grid[0]))
                      if {row[c] for row in grid} == {front}]
        if index % 2 == 0:
            assert clean_rows and not clean_cols
        else:
            assert not clean_rows and len(clean_cols) == 1 and clean_cols[0] != 0
        assert labeler.label(prototype.program_for("front"), grid) == [[front]]


@pytest.mark.parametrize("grid", [None, [], [[]], [[0], [0, 1]], [[True]],
                                  [[10]], [[-1]], [[0, 0], [0, 0]], [[2, 2], [2, 2]]])
def test_visible_endpoints_reject_malformed_or_non_band_grids(prototype, grid):
    with pytest.raises(ValueError):
        prototype.visible_endpoints(grid)


def test_nonunique_endpoints_and_cyclic_crossings_are_rejected(prototype):
    several_sources = _paint(11, 12, [("h", (1,), 1), ("h", (3,), 2),
                                     ("v", (2,), 3), ("v", (8,), 4), ("h", (7,), 5)])
    several_sinks = _paint(11, 12, [("v", (2,), 1), ("h", (1,), 2),
                                   ("h", (6,), 3), ("v", (7,), 4), ("v", (9,), 5)])
    cycle = _paint(8, 12, [("h", (2,), 1), ("h", (6,), 2),
                          ("v", (3,), 3), ("v", (8,), 4)])
    cycle[2][3], cycle[6][3], cycle[6][8], cycle[2][8] = 1, 3, 2, 4
    for grid in (several_sources, several_sinks, cycle):
        with pytest.raises(ValueError):
            prototype.visible_endpoints(grid)


@pytest.mark.parametrize("target", [None, True, 1, "", "FRONT", "front ", "middle"])
def test_unknown_or_ill_typed_rule_settings_fail(prototype, target):
    with pytest.raises((TypeError, ValueError)):
        prototype.program_for(target)
    with pytest.raises((TypeError, ValueError)):
        prototype.build_episode(0, target_layer=target)


@pytest.mark.parametrize("seed,index", [(True, 0), ("1", 0), (1.5, 0),
                                        (1, True), (1, "0"), (1, 0.5)])
def test_sample_input_requires_literal_integer_seed_and_index(prototype, seed, index):
    with pytest.raises((TypeError, ValueError)):
        prototype.sample_input(seed, index)


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": "1"}, {"seed": 1.5},
    {"demo_count": True}, {"demo_count": 1}, {"demo_count": 13}, {"demo_count": "3"},
    {"query_count": True}, {"query_count": 0}, {"query_count": 33}, {"query_count": "4"},
])
def test_episode_counts_and_seed_are_strictly_validated(prototype, kwargs):
    arguments = {"seed": 1, **kwargs}
    with pytest.raises((TypeError, ValueError)):
        prototype.build_episode(**arguments)


@pytest.mark.parametrize("setting", ["front", "back"])
def test_each_setting_has_four_distinct_racket_labeled_identifiable_queries(
    prototype, labeler, episodes, setting,
):
    episode = episodes[setting]
    assert episode["target_layer"] == setting
    assert episode["seed"] == 190807
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({_grid_key(pair["input"]) for pair in pairs}) == len(pairs)
    program = prototype.program_for(setting)
    assert episode["program"] == program
    assert episode["program_sha256"] == hashlib.sha256(program.encode()).hexdigest()
    for pair in pairs:
        assert pair["output"] == labeler.label(program, pair["input"])
        assert pair["output"] == [[prototype.visible_endpoints(pair["input"])[setting]]]

    # Derive the surviving settings solely from demonstrations, then apply them
    # to each query. No query label participates in hypothesis elimination.
    survivors = [candidate for candidate in ("front", "back")
                 if all([[prototype.visible_endpoints(pair["input"])[candidate]]] == pair["output"]
                        for pair in episode["train"])]
    assert survivors == [setting]
    assert any(_uniform_row_rival(pair["input"]) != pair["output"]
               for pair in episode["train"])
    report = episode["identifiability"]
    assert report["surviving_settings"] == survivors
    assert report["surviving_rivals"] == []
    assert len(report["queries"]) == 4
    assert all(row["identifiable"] is True for row in report["queries"])
    for query in episode["test"]:
        predictions = {prototype.visible_endpoints(query["input"])[candidate]
                       for candidate in survivors}
        assert predictions == {query["output"][0][0]}


def test_demonstration_and_query_counts_are_independent(prototype, labeler):
    episode = prototype.build_episode(923, target_layer="back", demo_count=2,
                                      query_count=1, labeler=labeler)
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 1
    for pair in episode["train"] + episode["test"]:
        assert pair["output"] == labeler.label(episode["program"], pair["input"])


def test_writer_uses_exact_public_projection_and_retains_private_labels(prototype, episodes, tmp_path):
    folder = tmp_path / "batch"
    batch = list(episodes.values())
    manifest = prototype.write_batch(batch, folder)
    expected_ids = sorted(public_challenge_id(episode) for episode in batch)
    assert manifest["public_ids"] == expected_ids
    assert json.loads((folder / "private/manifest.json").read_text()) == manifest
    assert sorted(path.stem for path in (folder / "public").glob("*.json")) == expected_ids
    for episode in batch:
        public_id = public_challenge_id(episode)
        public_path = folder / "public" / (public_id + ".json")
        assert public_path.read_bytes() == public_challenge_bytes(episode)
        visible = json.loads(public_path.read_text())
        assert set(visible) == {"train", "test"}
        assert all(set(pair) == {"input", "output"} for pair in visible["train"])
        assert all(set(pair) == {"input"} for pair in visible["test"])
        private = json.loads((folder / "private" / (public_id + ".json")).read_text())
        assert private["target_layer"] == episode["target_layer"]
        assert private["train"] == episode["train"] and private["test"] == episode["test"]
        assert (folder / "private/programs" / (episode["program_sha256"] + ".rkt")).read_text() == episode["program"]


def test_private_seed_metadata_and_query_answers_cannot_change_public_filename(prototype, episodes, tmp_path):
    original = deepcopy(episodes["front"])
    changed = deepcopy(original)
    changed["seed"] = -983
    changed["private_test_note"] = "not visible supervision"
    changed["test"][0]["output"] = [[(original["test"][0]["output"][0][0] % 9) + 1]]
    public_id = public_challenge_id(original)
    first = prototype.write_batch([original], tmp_path / "first")
    second = prototype.write_batch([changed], tmp_path / "second")
    assert first["public_ids"] == second["public_ids"] == [public_id]
    assert (tmp_path / "first/public" / (public_id + ".json")).read_bytes() == (
        tmp_path / "second/public" / (public_id + ".json")
    ).read_bytes()


def test_duplicate_visible_payloads_are_rejected_before_any_write(prototype, episodes, tmp_path):
    original = deepcopy(episodes["front"])
    duplicate = deepcopy(original)
    duplicate["seed"] += 1
    folder = tmp_path / "duplicates"
    with pytest.raises(ValueError):
        prototype.write_batch([original, duplicate], folder)
    assert not folder.exists()


def test_existing_output_directory_is_not_overwritten(prototype, episodes, tmp_path):
    folder = tmp_path / "existing"
    folder.mkdir()
    sentinel = folder / "keep.txt"
    sentinel.write_text("existing data")
    with pytest.raises((FileExistsError, ValueError)):
        prototype.write_batch(list(episodes.values()), folder)
    assert sentinel.read_text() == "existing data"
    assert sorted(path.name for path in folder.iterdir()) == ["keep.txt"]


@pytest.mark.parametrize("target", ["front", "back"])
@pytest.mark.parametrize("queries", [10, 22])
def test_retry_schedule_is_independent_of_requested_pair_count(prototype, labeler, target, queries):
    # A total of 12 or 24 pairs used to lock both demos to the 3x3 slots.
    # Frequency then exactly identifies front/back without learning crossings.
    episode = prototype.build_episode(190807, target_layer=target, demo_count=2,
                                      query_count=queries, labeler=labeler)
    assert len(episode["train"]) == 2 and len(episode["test"]) == queries
    assert episode["identifiability"]["surviving_rivals"] == []
    pairs = episode["train"] + episode["test"]
    assert len({_grid_key(pair["input"]) for pair in pairs}) == len(pairs)
    assert all(pair["output"] == [[prototype.visible_endpoints(pair["input"])[target]]]
               for pair in pairs)


def test_documented_upper_count_boundary(prototype, labeler):
    episode = prototype.build_episode(90210, target_layer="back", demo_count=12,
                                      query_count=32, labeler=labeler)
    pairs = episode["train"] + episode["test"]
    assert len(episode["train"]) == 12 and len(episode["test"]) == 32
    assert len({_grid_key(pair["input"]) for pair in pairs}) == 44
    assert all(pair["output"] == [[prototype.visible_endpoints(pair["input"])["back"]]]
               for pair in pairs)
    assert episode["runtime_identity"]["protected"] is True
