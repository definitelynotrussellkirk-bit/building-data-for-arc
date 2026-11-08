"""Behavioral checks for the opt-in ranked-barrier family."""
import copy
import importlib.util
import json
import random

import pytest

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


ROOT = find_root(__file__)
HOME = ROOT / "generators/eb373570e72b/workspace/parametric"
SEED = 37


def load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "Native ranked-barrier adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("_test_eb373570e72b_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return load_adapter()


@pytest.fixture(scope="module")
def episodes(adapter):
    """Two short lessons share inputs but teach different executed rules."""
    return {
        rank: adapter.generate(SEED, {"blocker_rank": rank}, 2, 4)
        for rank in (1, 2)
    }


@pytest.fixture(scope="module")
def racket_apply():
    # Import and start the reference runtime only during a test, never collection.
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    bridge = RacketBridge(max_calls_before_restart=128)
    assert bridge.runtime_identity["backend"] == "racket"
    assert bridge.runtime_identity["protected"] is True

    def apply(program, grid):
        literal = "'(" + " ".join(
            "(" + " ".join(map(str, row)) + ")" for row in grid
        ) + ")"
        output = bridge.eval_text(f"({wrap_rule(program)} {literal})")
        assert type(output) is list and output
        assert all(type(row) is list and len(row) == len(output[0]) for row in output)
        assert all(type(cell) is int and 0 <= cell <= 9 for row in output for cell in row)
        return output

    try:
        yield apply
    finally:
        bridge.close()


def _inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def _old_masked_rich_scene():
    """Independent original scene whose other floor runs conceal endpoints."""
    grid = [[0] * 28 for _ in range(8)]
    markers = {1: 2, 4: 1, 8: 2, 11: 2, 15: 1, 18: 2, 22: 2, 25: 1}
    for row in range(2, 8):
        for col, color in markers.items():
            grid[row][col] = color
    grid[0][8] = grid[1][8] = 2
    grid[3][0] = grid[4][10] = grid[5][16] = 1
    return grid


def test_default_program_is_exact_canonical_source(adapter):
    sources = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text().splitlines()
        if (row := json.loads(line)).get("task_id") == "eb373570e72b"
    }
    assert sources == {adapter.program({"blocker_rank": 1})}
    assert adapter.program({"blocker_rank": 2}) not in sources


@pytest.mark.parametrize(
    "settings",
    [
        None,
        [],
        {},
        {"rank": 1},
        {"blocker_rank": 0},
        {"blocker_rank": 3},
        {"blocker_rank": True},
        {"blocker_rank": 1.0},
        {"blocker_rank": "1"},
        {"blocker_rank": 1, "extra": 2},
    ],
)
def test_program_rejects_undeclared_or_mistyped_settings(adapter, settings):
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)


@pytest.mark.parametrize(
    "replacement",
    [
        {"seed": True},
        {"seed": -1},
        {"seed": 2**63},
        {"seed": 1.5},
        {"demos": True},
        {"demos": 1},
        {"demos": 7},
        {"queries": True},
        {"queries": 0},
        {"queries": 5},
        {"settings": {"blocker_rank": False}},
    ],
)
def test_episode_rejects_invalid_seed_counts_and_settings(adapter, replacement):
    request = dict(seed=SEED, settings={"blocker_rank": 1}, demos=2, queries=4)
    request.update(replacement)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(**request)


def test_counts_have_independent_input_streams_and_no_duplicate_inputs(adapter):
    prototype = adapter.prototype
    shortest = prototype.sample_inputs(SEED, 2, 1)
    ordinary = prototype.sample_inputs(SEED, 2, 4)
    assert shortest["train"] == ordinary["train"]
    assert shortest["test"] == ordinary["test"][:1]
    for demos in range(2, 7):
        sampled = prototype.sample_inputs(SEED, demos, 4)
        assert len(sampled["train"]) == demos
        assert len(sampled["test"]) == 4
        assert sampled["train"][:2] == ordinary["train"]
        assert sampled["test"] == ordinary["test"]
        inputs = sampled["train"] + sampled["test"]
        assert len({_frozen(grid) for grid in inputs}) == len(inputs)
    maximum_seed = prototype.sample_inputs(2**63 - 1, 2, 4)
    assert len(maximum_seed["train"]) == 2 and len(maximum_seed["test"]) == 4


def test_rank_settings_share_inputs_and_change_a_demonstrated_output(adapter, episodes):
    for split in ("train", "test"):
        assert _inputs(episodes[1], split) == _inputs(episodes[2], split)
    for rank, episode in episodes.items():
        assert len(episode["train"]) == 2 and len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program({"blocker_rank": rank})
        for pair in episode["train"] + episode["test"]:
            assert len(pair["output"]) == len(pair["input"])
            assert all(len(row) == len(pair["input"][0]) for row in pair["output"])
            assert all(type(cell) is int and 0 <= cell <= 9
                       for row in pair["input"] + pair["output"] for cell in row)
    assert any(left["output"] != right["output"]
               for left, right in zip(episodes[1]["train"], episodes[2]["train"]))


def test_generation_is_deterministic_fresh_and_preserves_global_rng(adapter):
    before = random.getstate()
    first = adapter.generate(SEED, {"blocker_rank": 1}, 2, 1)
    second = adapter.generate(SEED, {"blocker_rank": 1}, 2, 1)
    assert random.getstate() == before
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    saved = copy.deepcopy(second)
    first["train"][0]["input"][0][0] = 9
    first["test"][0]["output"][0][0] = 9
    assert second == saved


def test_four_queries_cover_real_minimum_and_substantive_30_by_30(adapter, episodes):
    queries = _inputs(episodes[1], "test")
    shapes = {(len(grid), len(grid[0])) for grid in queries}
    assert (3, 7) in shapes and (30, 30) in shapes
    assert len({_frozen(grid) for grid in queries}) == 4
    stress = next(grid for grid in queries if len(grid) == len(grid[0]) == 30)
    occupied = [(row, col) for row in range(30) for col in range(30) if stress[row][col]]
    assert len(occupied) >= 120, "30x30 stress must contain substantive marker geometry"
    assert len({row for row, _ in occupied}) >= 24
    assert max(col for _, col in occupied) - min(col for _, col in occupied) >= 24
    assert any(row == 0 for row, _ in occupied)
    assert any(row == 29 for row, _ in occupied)
    facts = adapter.prototype.analyze(stress)
    assert len(facts["vertical_cols"]) >= 2


def test_first_query_projection_is_identical_for_one_or_four_queries(adapter, episodes):
    short = adapter.generate(SEED, {"blocker_rank": 1}, 2, 1)
    first_short = adapter.prototype.visible_query(short, 0)
    first_long = adapter.prototype.visible_query(episodes[1], 0)
    assert public_challenge_bytes(first_short) == public_challenge_bytes(first_long)


def test_visible_turn_hides_labels_settings_and_all_future_inputs(adapter, episodes):
    original = episodes[1]
    visible = adapter.prototype.visible_query(original, 0)
    assert visible == {
        "train": original["train"],
        "test": [{"input": original["test"][0]["input"]}],
    }
    altered = copy.deepcopy(original)
    altered["seed"] = SEED + 100
    altered["settings"] = {"blocker_rank": 2}
    altered["program_solution"] += "\n"
    altered["private_note"] = "a hidden setting and the next answer"
    for pair in altered["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    altered["test"][1]["input"] = [[9]]
    assert adapter.prototype.visible_query(altered, 0) == visible
    assert public_challenge_id(adapter.prototype.visible_query(altered, 0)) == public_challenge_id(visible)


@pytest.mark.parametrize("index", [-1, 4, True, 0.0])
def test_visible_turn_rejects_invalid_query_index(adapter, episodes, index):
    with pytest.raises((TypeError, ValueError, IndexError)):
        adapter.prototype.visible_query(episodes[1], index)


def test_export_names_and_bytes_depend_only_on_visible_content(adapter, episodes, tmp_path):
    original = copy.deepcopy(episodes[1])
    altered = copy.deepcopy(original)
    altered["seed"] = SEED + 1
    altered["settings"] = {"blocker_rank": 2}
    altered["program_solution"] += "\n"
    for pair in altered["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    assert public_challenge_bytes(original) == public_challenge_bytes(altered)
    expected_id = public_challenge_id(original)
    first = adapter.prototype.write_export(tmp_path / "original", [original])
    second = adapter.prototype.write_export(tmp_path / "altered", [altered])
    assert first["episode_count"] == second["episode_count"] == 1
    assert first["public_files"] == second["public_files"]
    row = first["public_files"][0]
    assert row["id"] == row["sha256"] == expected_id
    assert row["path"] == f"public/{expected_id}.json"
    assert (tmp_path / "original" / row["path"]).read_bytes() == public_challenge_bytes(original)
    public = json.loads((tmp_path / "original" / row["path"]).read_bytes())
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in public["test"])
    private = json.loads((tmp_path / "original/private.jsonl").read_text().strip())
    assert private["id"] == expected_id
    assert (tmp_path / "original/manifest.json").is_file()


def test_export_rejects_duplicate_public_lessons_before_creating_destination(adapter, episodes, tmp_path):
    duplicate = copy.deepcopy(episodes[1])
    duplicate["seed"] = SEED + 200
    duplicate["test"][0]["output"] = [[9 for _ in row] for row in duplicate["test"][0]["output"]]
    destination = tmp_path / "duplicate"
    with pytest.raises(ValueError):
        adapter.prototype.write_export(destination, [episodes[1], duplicate])
    assert not destination.exists()


def test_export_refuses_existing_destination_without_overwriting(adapter, episodes, tmp_path):
    destination = tmp_path / "existing"
    destination.mkdir()
    sentinel = destination / "keep.txt"
    sentinel.write_text("previous artifact")
    with pytest.raises((ValueError, FileExistsError)):
        adapter.prototype.write_export(destination, [episodes[1]])
    assert sentinel.read_text() == "previous artifact"
    assert sorted(path.name for path in destination.iterdir()) == ["keep.txt"]


def test_hand_computed_racket_witness_covers_rank_shortage_and_gap_closure(adapter, racket_apply):
    # The early evidence fixes active row 2. Only columns 8 and 11 are vertical:
    # red 1 is joined to blue 4, red 18 to blue 15, and red 22 to blue 25.
    grid = _old_masked_rich_scene()
    facts = adapter.prototype.analyze(grid)
    assert facts["active_row"] == 2
    assert facts["vertical_cols"] == [8, 11]
    snapshot = copy.deepcopy(grid)

    # These complete floor rows are hand-computed. Rank 2 skips column 8 for
    # loose blue 0; blue 10 has only one later blocker, so it gets length 3.
    # Blue 16 has no later blocker under either rank. Red gap 21 closes.
    floors = {
        1: [1, 1, 1, 1, 1, 1, 1, 0, 2, 0, 0, 2, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1],
        2: [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 1, 1, 1],
    }
    for rank in (1, 2):
        expected = [[0] * 28 for _ in range(8)]
        for row in range(8):
            expected[row][8] = 2
        for row in range(2, 8):
            expected[row][11] = 2
        expected[-1] = floors[rank]
        assert racket_apply(adapter.program({"blocker_rank": rank}), grid) == expected
    assert grid == snapshot


@pytest.mark.parametrize("rank", [1, 2])
def test_first_two_demos_reject_each_declared_wrong_rule(adapter, episodes, racket_apply, rank):
    rivals = adapter.prototype.rival_programs({"blocker_rank": rank})
    assert rivals, "The bounded self-audit must declare its plausible wrong rules"
    survivors = []
    for name, program in rivals.items():
        predictions = [racket_apply(program, pair["input"]) for pair in episodes[rank]["train"]]
        if all(predicted == pair["output"]
               for predicted, pair in zip(predictions, episodes[rank]["train"])):
            survivors.append(name)
    assert survivors == [], f"Wrong rules still fit both demonstrations: {survivors}"


@pytest.mark.parametrize(
    "rank,rival_name",
    [(1, "barrier_clearance_2"), (2, "barrier_clearance_0")],
)
def test_unmasked_second_demo_resolves_old_two_demo_clearance_ambiguity(
    adapter, racket_apply, rank, rival_name
):
    # Preserve the discovered failure mechanism without a dependency on audit
    # receipts: the original rich geometry conceals an incorrect endpoint.
    # A replacement second demo must expose it without increasing context.
    episode = adapter.generate(17, {"blocker_rank": rank}, 2, 4)
    rival = adapter.prototype.rival_programs({"blocker_rank": rank})[rival_name]
    old_grid = _old_masked_rich_scene()
    old_demos = [
        episode["train"][0],
        {"input": old_grid, "output": racket_apply(adapter.program({"blocker_rank": rank}), old_grid)},
    ]
    for pair in old_demos:
        assert racket_apply(rival, pair["input"]) == pair["output"]
    assert any(
        racket_apply(rival, pair["input"]) != pair["output"]
        for pair in episode["test"]
    ), "The original two-demo geometry must still permit a wrong query answer"
    anchor = episode["train"][1]
    assert racket_apply(rival, anchor["input"]) != anchor["output"]
