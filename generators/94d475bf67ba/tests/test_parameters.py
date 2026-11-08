"""Focused contract, teaching, and privacy tests for the separate native family."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"


@pytest.fixture(scope="module")
def prototype():
    spec = importlib.util.spec_from_file_location("_frames_parameters_test", PARAMETRIC / "prototype.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_program_is_exact_selected_canonical(prototype):
    from reviewer_support import canonical_path, find_root
    with canonical_path(find_root(__file__)).open() as source:
        row = next(json.loads(line) for line in source if json.loads(line)["task_id"] == "94d475bf67ba")
    assert prototype.program({"mode": "all"}) == row["program_solution"]
    assert prototype.program({"mode": "largest_owned"}) != row["program_solution"]


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_counts_matched_inputs_and_constructive_teaching(prototype, demos, queries):
    episodes = [prototype.generate(17, {"mode": mode}, demos, queries) for mode in prototype.MODES]
    for mode, episode in zip(prototype.MODES, episodes):
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        inputs = [p["input"] for p in episode["train"] + episode["test"]]
        assert len({json.dumps(grid) for grid in inputs}) == demos + queries
        assert all(prototype.analyze(grid)["frames"] for grid in inputs)
        certificate = prototype.teaching_report(episode["train"], [p["input"] for p in episode["test"]], mode)
        assert certificate["survivors"] == [mode]
        assert certificate["ambiguous_queries"] == []
    for split in ("train", "test"):
        assert [p["input"] for p in episodes[0][split]] == [p["input"] for p in episodes[1][split]]


def test_two_demonstrations_cover_tie_and_deepest_winner(prototype):
    episode = prototype.generate(0, {"mode": "largest_owned"}, 2, 4)
    first = prototype.analyze(episode["train"][0]["input"])
    second = prototype.analyze(episode["train"][1]["input"])
    assert first["owned_counts"][0] == first["owned_counts"][1] > first["owned_counts"][2]
    assert second["owned_counts"][2] > max(second["owned_counts"][:2])
    assert all(frame["operative"] for frame in first["frames"] + second["frames"])


def test_queries_include_substantive_minimum_terminal_and_30_boundary(prototype):
    episode = prototype.generate(17, {"mode": "largest_owned"}, 3, 4)
    grids = [p["input"] for p in episode["test"]]
    assert (len(grids[0]), len(grids[0][0])) == (7, 7)
    assert any(not frame["operative"] for frame in prototype.analyze(grids[1])["frames"])
    large = grids[3]
    assert (len(large), len(large[0])) == (30, 30)
    assert all(v != 0 for v in large[0] + large[-1])
    assert all(row[0] != 0 and row[-1] != 0 for row in large)
    assert sum(v != 0 for row in large for v in row) >= 150
    for pair in episode["train"] + episode["test"]:
        assert all(v == pair["output"][r][c] for r, row in enumerate(pair["input"]) for c, v in enumerate(row) if v)


def test_query_and_demo_prefixes_do_not_depend_on_total_counts(prototype):
    short = prototype.generate(5, {"mode": "largest_owned"}, 2, 1)
    long = prototype.generate(5, {"mode": "largest_owned"}, 6, 4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    short_same_demos = prototype.generate(5, {"mode": "largest_owned"}, 6, 1)
    assert prototype.public_challenge(short_same_demos) == prototype.public_challenge(long)


@pytest.mark.parametrize("settings", [{}, {"mode": True}, {"mode": "unknown"}, {"mode": "all", "x": 1}])
def test_invalid_settings_fail(prototype, settings):
    with pytest.raises(ValueError):
        prototype.generate(0, settings, 3, 4)


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4), (0, True, 4), (0, 1, 4), (0, 7, 4), (0, 3, 0), (0, 3, 5), (0, 3, 4.0)])
def test_invalid_requests_fail(prototype, seed, demos, queries):
    with pytest.raises(ValueError):
        prototype.generate(seed, {"mode": "all"}, demos, queries)


def test_public_projection_ignores_private_and_future_data(prototype):
    episode = prototype.generate(21, {"mode": "all"}, 3, 4)
    expected = prototype.public_challenge(episode)
    mutated = deepcopy(episode)
    mutated["program_solution"] = "private reference"
    mutated["settings"] = {"secret": 987}
    mutated["seed"] = 999
    for pair in mutated["test"]:
        pair["output"] = [[9]]
    mutated["test"][1]["input"] = [[8]]
    assert prototype.public_challenge(mutated) == expected
    assert set(expected) == {"train", "test"}
    assert len(expected["test"]) == 1
    assert set(expected["test"][0]) == {"input"}
    assert prototype.public_challenge(episode, all_queries=True)["test"] == [{"input": p["input"]} for p in episode["test"]]


def test_shortcut_survivor_is_reported_when_decisive_demo_is_removed(prototype):
    episode = prototype.generate(0, {"mode": "largest_owned"}, 2, 4)
    # The second demo has a single winner: "choose one max" fits it, but fails ties.
    report = prototype.teaching_report(episode["train"][1:], [episode["train"][0]["input"]], "largest_owned")
    assert "tie_first_only" in report["survivors"]
    assert report["ambiguous_queries"]


def test_grammar_rejects_broken_border_and_typed_cells(prototype):
    grid = prototype.generate(1, {"mode": "all"}, 2, 4)["test"][0]["input"]
    broken = deepcopy(grid)
    broken[0][0] = 0
    with pytest.raises(ValueError):
        prototype.analyze(broken)
    bad_type = deepcopy(grid)
    bad_type[1][1] = False
    with pytest.raises(ValueError):
        prototype.analyze(bad_type)


def test_selected_frames_do_not_paint_the_losing_inner_region(prototype):
    pair = prototype.generate(0, {"mode": "largest_owned"}, 2, 4)["train"][0]
    candidates = prototype.candidate_outputs(pair["input"])
    assert "selected_containment_paint" in candidates
    assert candidates["selected_containment_paint"] != pair["output"]
    inner = prototype.analyze(pair["input"])["frames"][-1]
    r, c = inner["box"][0] + 1, inner["box"][1] + 1
    assert pair["output"][r][c] == 0
    assert candidates["selected_containment_paint"][r][c] != 0
