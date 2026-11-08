"""Focused MAIN prototype tests; protected Racket qualification is separate."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import sys

import pytest


TASK_ID = "0f801939eff6"
TASK_HOME = Path(__file__).resolve().parents[1]
ROOT = TASK_HOME.parents[1]
SOURCE = TASK_HOME / "workspace/parametric/prototype.py"
SETTINGS = ({"merge": "none"}, {"merge": "2_into_1"})


def _load_exact(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    if not SOURCE.is_file():
        pytest.skip("the dedicated existence assertion diagnoses the missing prototype")
    return _load_exact(SOURCE, "_test_area_sorted_parametric_prototype")


@pytest.fixture(scope="module")
def support():
    return _load_exact(
        ROOT / "shared/runtime/reviewer_support.py",
        "_test_area_sorted_reviewer_support",
    )


def test_parametric_prototype_exists():
    assert SOURCE.is_file(), "MAIN merge-before-ranking prototype is missing"


def _cluster_local_recolor(grid):
    """Independent rival: recolor only foreground clusters that contain 1."""
    remaining = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    result = deepcopy(grid)
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        cells, todo = {start}, [start]
        while todo:
            r, c = todo.pop()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    position = (r+dr, c+dc)
                    if position in remaining:
                        remaining.remove(position)
                        cells.add(position)
                        todo.append(position)
        if any(grid[r][c] == 1 for r, c in cells):
            for r, c in cells:
                if result[r][c] == 2:
                    result[r][c] = 1
    return _expected(result, SETTINGS[0])


@pytest.mark.parametrize("seed", [17, 34, 813])
def test_two_demos_teach_recoloring_an_isolated_source_color(prototype, seed):
    episode = prototype.generate(seed, SETTINGS[1], demos=2, queries=4)
    assert any(_cluster_local_recolor(pair["input"]) != pair["output"]
               for pair in episode["train"]), "local-only recoloring survives all demonstrations"
    assert _cluster_local_recolor(episode["test"][2]["input"]) != episode["test"][2]["output"]


def test_unserializable_private_metadata_fails_before_publication(prototype, tmp_path):
    episode = prototype.generate(17, SETTINGS[1], demos=2, queries=4)
    episode["private_metadata"] = {1: "integer key", "x": "string key"}
    target = tmp_path / "bad-metadata"
    with pytest.raises((ValueError, TypeError)):
        prototype.export_batch([episode], target)
    assert not target.exists(), "failed private serialization must not leave a public challenge"


def _components(grid):
    """An independent pixel flood-fill for the expected component-area rule."""
    remaining = {
        (r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value
    }
    parts = []
    while remaining:
        first = min(remaining)
        color = grid[first[0]][first[1]]
        cells, pending = {first}, [first]
        remaining.remove(first)
        while pending:
            r, c = pending.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining and grid[neighbor[0]][neighbor[1]] == color:
                    remaining.remove(neighbor)
                    cells.add(neighbor)
                    pending.append(neighbor)
        parts.append((len(cells), color))
    return parts


def _expected(grid, settings):
    recolored = [
        [1 if value == 2 and settings["merge"] == "2_into_1" else value for value in row]
        for row in grid
    ]
    row = [
        color
        for size, color in sorted(_components(recolored), key=lambda item: (-item[0], item[1]))
        for _ in range(size)
    ]
    return [row or [0]]


def _assert_grid(grid):
    assert type(grid) is list and 1 <= len(grid) <= 30
    assert type(grid[0]) is list and 1 <= len(grid[0]) <= 30
    assert all(type(row) is list and len(row) == len(grid[0]) for row in grid)
    assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)


def _dicts(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _dicts(child)


def test_settings_and_default_program_preserve_exact_canonical_authority(prototype, support):
    assert list(prototype.SETTINGS) == list(SETTINGS)
    with support.canonical_path(ROOT).open(encoding="utf-8") as stream:
        programs = {
            row["program_solution"]
            for row in map(json.loads, stream)
            if row.get("task_id") == TASK_ID
        }
    assert len(programs) == 1
    canonical = programs.pop()
    assert prototype.program(SETTINGS[0]) == canonical
    alternative = prototype.program(SETTINGS[1])
    assert isinstance(alternative, str) and alternative.strip() and alternative != canonical
    pairs = support.canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    assert pairs
    for pair in pairs:
        assert prototype.rule_mirror(pair["input"], SETTINGS[0]) == pair["output"]
        assert _expected(pair["input"], SETTINGS[0]) == pair["output"]


def test_recoloring_changes_connectivity_before_area_ranking(prototype):
    # Two singleton 1s join the size-three 2 component, overtaking size-four 3.
    grid = [[1, 2, 1, 0, 0, 0], [0, 2, 0, 0, 3, 3], [0, 2, 0, 0, 3, 3]]
    untouched = deepcopy(grid)
    assert prototype.rule_mirror(grid, SETTINGS[0]) == [[3, 3, 3, 3, 2, 2, 2, 1, 1]]
    assert prototype.rule_mirror(grid, SETTINGS[1]) == [[1, 1, 1, 1, 1, 3, 3, 3, 3]]
    assert prototype.rival_outputs(grid, SETTINGS[1])["rank_then_recolor"] == [
        [3, 3, 3, 3, 1, 1, 1, 1, 1]
    ]
    assert grid == untouched


@pytest.mark.parametrize(
    "name,grid,expected",
    [
        ("color_frequency", [[1, 1, 0, 2, 2, 2, 0, 1, 1]], [[1, 1, 1, 1, 2, 2, 2]]),
        ("position_tie", [[3, 3, 0, 1, 1]], [[3, 3, 1, 1]]),
        (
            "eight_connected",
            [[1, 0, 0, 2, 2, 2], [0, 1, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0], [0, 0, 0, 1, 0, 0]],
            [[1, 1, 1, 1, 2, 2, 2]],
        ),
        (
            "bbox_rank",
            [[1, 1, 1, 0, 0, 0, 0], [1, 0, 0, 0, 2, 2, 2], [1, 0, 0, 0, 2, 2, 2]],
            [[1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2]],
        ),
    ],
)
def test_named_rivals_are_real_semantically_distinct_shortcuts(prototype, name, grid, expected):
    assert prototype.rival_outputs(grid, SETTINGS[0])[name] == expected
    assert expected != _expected(grid, SETTINGS[0])


@pytest.mark.parametrize(
    "settings",
    [None, {}, "none", {"merge": True}, {"merge": 0}, {"merge": "NONE"},
     {"merge": "unknown"}, {"merge": "none", "extra": 0}, {"MERGE": "none"}],
)
def test_invalid_settings_are_rejected_at_rule_and_generation_boundaries(prototype, settings):
    with pytest.raises((TypeError, ValueError)):
        prototype.program(settings)
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(0, settings)
    with pytest.raises((TypeError, ValueError)):
        prototype.rule_mirror([[1]], settings)


@pytest.mark.parametrize("seed", [None, True, False, 1.0, "1", -1, 2**63])
def test_seed_must_be_a_bounded_literal_integer(prototype, seed):
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(seed, SETTINGS[0])


@pytest.mark.parametrize(
    "control,value",
    [("demos", value) for value in (True, False, 1, 7, 2.0, "3")]
    + [("queries", value) for value in (True, False, 0, 5, 1.0, "1")],
)
def test_demo_and_query_counts_are_separately_strict(prototype, control, value):
    with pytest.raises((TypeError, ValueError)):
        prototype.generate(17, SETTINGS[0], **{control: value})


@pytest.mark.parametrize(
    "grid", [None, [], [[]], [[0], [0, 1]], [[True]], [[1.0]], [[-1]], [[10]], [[0] * 31], [[0]] * 31],
)
def test_malformed_and_boolean_grids_cannot_cross_rule_or_public_boundaries(prototype, grid):
    with pytest.raises((TypeError, ValueError)):
        prototype.rule_mirror(grid, SETTINGS[0])
    baseline = {
        "train": [{"input": [[1]], "output": [[1]]}, {"input": [[1, 1]], "output": [[1, 1]]}],
        "test": [{"input": [[2]], "output": [[2]]}],
    }
    for split, field in (("train", "input"), ("train", "output"), ("test", "input")):
        malformed = deepcopy(baseline)
        malformed[split][0][field] = grid
        with pytest.raises((TypeError, ValueError)):
            prototype.public_challenge(malformed)


@pytest.mark.parametrize("settings", SETTINGS)
@pytest.mark.parametrize("seed,demos,queries", [(0, 2, 1), (2**63 - 1, 6, 4)])
def test_valid_count_and_seed_boundaries_produce_complete_distinct_labeled_pairs(
    prototype, settings, seed, demos, queries
):
    episode = prototype.generate(seed, settings, demos=demos, queries=queries)
    assert len(episode["train"]) == demos and len(episode["test"]) == queries
    assert episode["program_solution"] == prototype.program(settings)
    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == len(pairs)
    for pair in pairs:
        _assert_grid(pair["input"])
        _assert_grid(pair["output"])
        assert pair["output"] == _expected(pair["input"], settings)
        assert len(pair["output"]) == 1


@pytest.mark.parametrize("settings", SETTINGS)
def test_generation_is_deterministic_without_mutating_caller_settings(prototype, settings):
    request = deepcopy(settings)
    episode = prototype.generate(173, request)
    assert request == settings
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4
    repeated = prototype.generate(173, request)
    assert episode == repeated
    episode["train"][0]["input"][0][0] = 99
    assert repeated["train"][0]["input"][0][0] != 99


@pytest.mark.parametrize("seed", [17, 813])
def test_input_sampling_is_matched_across_settings_and_demos_teach_the_difference(prototype, seed):
    episodes = [prototype.generate(seed, setting, demos=2, queries=4) for setting in SETTINGS]
    for split in ("train", "test"):
        assert [pair["input"] for pair in episodes[0][split]] == [
            pair["input"] for pair in episodes[1][split]
        ]
    assert any(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))


@pytest.mark.parametrize("settings", SETTINGS)
def test_query_stream_and_first_turn_do_not_depend_on_requested_counts(prototype, settings):
    episodes = {
        (demos, queries): prototype.generate(31, settings, demos=demos, queries=queries)
        for demos in (2, 6)
        for queries in (1, 4)
    }
    for demos in (2, 6):
        short, full = episodes[demos, 1], episodes[demos, 4]
        assert short["train"] == full["train"]
        assert short["test"] == full["test"][:1]
        assert prototype.public_challenge(short) == prototype.public_challenge(full)
    assert episodes[2, 4]["test"] == episodes[6, 4]["test"]
    assert episodes[2, 1]["test"] == episodes[6, 1]["test"]


@pytest.mark.parametrize("settings", SETTINGS)
def test_four_query_bank_contains_substantive_full_canvas_thirty_square_stress(prototype, settings):
    episode = prototype.generate(409, settings, demos=2, queries=4)
    stress = [pair for pair in episode["test"] if (len(pair["input"]), len(pair["input"][0])) == (30, 30)]
    assert stress, "four-query requests must contain a 30x30 input"
    for pair in episode["train"] + episode["test"]:
        assert 1 <= sum(value != 0 for row in pair["input"] for value in row) <= 30
    for pair in stress:
        occupied = [(r, c) for r, row in enumerate(pair["input"]) for c, value in enumerate(row) if value]
        assert (min(r for r, _ in occupied), max(r for r, _ in occupied)) == (0, 29)
        assert (min(c for _, c in occupied), max(c for _, c in occupied)) == (0, 29)
        assert pair["output"] == _expected(pair["input"], settings)


@pytest.mark.parametrize("settings", SETTINGS)
@pytest.mark.parametrize("seed", [17, 34])
def test_two_visible_demos_refute_every_declared_rival_without_query_labels(prototype, settings, seed):
    episode = prototype.generate(seed, settings, demos=2, queries=4)
    predictions = [prototype.rival_outputs(pair["input"], settings) for pair in episode["train"]]
    required = {"color_frequency", "position_tie", "eight_connected", "bbox_rank"}
    if settings["merge"] != "none":
        required.add("rank_then_recolor")
    assert required <= predictions[0].keys()
    assert predictions[0].keys() == predictions[1].keys()
    report = prototype.teaching_check(episode)
    assert report["status"] == "identified"
    assert report["surviving_rivals"] == []
    assert set(report["refuted_by"]) == set(predictions[0])
    for name in predictions[0]:
        witnesses = [
            index for index, pair in enumerate(episode["train"])
            if predictions[index][name] != pair["output"]
        ]
        assert witnesses, f"{name} fits every visible demo"
        assert report["refuted_by"][name] == witnesses[0]


@pytest.mark.parametrize("settings", SETTINGS)
def test_teaching_certificate_does_not_consult_private_query_answers(prototype, settings):
    episode = prototype.generate(67, settings, demos=2, queries=4)
    expected = prototype.teaching_check(episode)
    changed, stripped = deepcopy(episode), deepcopy(episode)
    for pair in changed["test"]:
        pair["output"] = [[9]]
    for pair in stripped["test"]:
        pair.pop("output")
    assert prototype.teaching_check(changed) == expected
    assert prototype.teaching_check(stripped) == expected


@pytest.mark.parametrize("settings", SETTINGS)
def test_teaching_check_reports_ambiguous_demos_instead_of_certifying_the_query(prototype, settings):
    episode = prototype.generate(83, settings, demos=2, queries=4)
    episode["train"] = [
        {"input": [[1, 1]], "output": [[1, 1]]},
        {"input": [[1], [1], [1]], "output": [[1, 1, 1]]},
    ]
    predictions = [prototype.rival_outputs(pair["input"], settings) for pair in episode["train"]]
    survivors = sorted(
        name for name in predictions[0]
        if all(prediction[name] == pair["output"] for prediction, pair in zip(predictions, episode["train"]))
    )
    assert survivors
    report = prototype.teaching_check(episode)
    assert report["status"] == "ambiguous"
    assert sorted(report["surviving_rivals"]) == survivors


@pytest.mark.parametrize("settings", SETTINGS)
def test_one_query_projection_is_pure_and_private_metadata_cannot_change_visible_identity(
    prototype, support, settings
):
    episode = prototype.generate(97, settings, demos=2, queries=4)
    untouched = deepcopy(episode)
    for index, pair in enumerate(episode["test"]):
        public = prototype.public_challenge(episode, query_index=index)
        expected = {
            "train": [{"input": item["input"], "output": item["output"]} for item in episode["train"]],
            "test": [{"input": pair["input"]}],
        }
        assert public == expected
        support.public_challenge_bytes(public)
    first = prototype.public_challenge(episode)
    changed = deepcopy(episode)
    changed.update(seed=2**63 - 1, settings={"merge": "private sentinel"}, program_solution="private rule")
    changed["private"] = {"query_count": 4, "last_turn": True}
    for pair in changed["test"]:
        pair["output"] = [[9]]
    for pair in changed["test"][1:]:
        pair["input"] = [[8]]
    changed["train"][0]["private_note"] = "must not be projected"
    assert prototype.public_challenge(changed) == first
    assert support.public_challenge_id(prototype.public_challenge(changed)) == support.public_challenge_id(first)
    first["train"][0]["input"][0][0] = 99
    first["test"][0]["input"][0][0] = 99
    assert episode == untouched


@pytest.mark.parametrize("index", [True, False, 0.0, "0", None, -1, 4])
def test_query_projection_index_is_strict_and_bounded(prototype, index):
    episode = prototype.generate(101, SETTINGS[0])
    with pytest.raises((TypeError, ValueError, IndexError)):
        prototype.public_challenge(episode, query_index=index)


def test_export_publishes_exact_visible_hashes_and_retains_full_private_query_banks(prototype, support, tmp_path):
    episodes = [prototype.generate(109, setting) for setting in SETTINGS]
    destination = tmp_path / "publication"
    prototype.export_batch(episodes, destination)
    expected = {
        support.public_challenge_id(prototype.public_challenge(episode)): support.public_challenge_bytes(
            prototype.public_challenge(episode)
        )
        for episode in episodes
    }
    public_files = [path for path in (destination / "public").rglob("*") if path.is_file()]
    assert {path.relative_to(destination / "public").as_posix() for path in public_files} == {
        digest + ".json" for digest in expected
    }
    assert {path.stem: path.read_bytes() for path in public_files} == expected
    private_nodes = []
    for path in (destination / "private").rglob("*"):
        if path.is_file() and path.suffix in {".json", ".jsonl"}:
            text = path.read_text(encoding="utf-8")
            values = [json.loads(line) for line in text.splitlines() if line.strip()] if path.suffix == ".jsonl" else [json.loads(text)]
            for value in values:
                private_nodes.extend(_dicts(value))
    for episode in episodes:
        assert any(
            all(key in node and node[key] == value for key, value in episode.items())
            for node in private_nodes
        ), "private export must retain the complete labeled episode and exact program"


def test_export_refuses_overwrites_and_duplicate_visibility_before_creating_destination(prototype, tmp_path):
    episode = prototype.generate(127, SETTINGS[0])
    existing = tmp_path / "existing"
    existing.mkdir()
    sentinel = existing / "keep.txt"
    sentinel.write_bytes(b"preserve existing data\n")
    with pytest.raises((FileExistsError, ValueError)):
        prototype.export_batch([episode], existing)
    assert list(existing.iterdir()) == [sentinel]
    assert sentinel.read_bytes() == b"preserve existing data\n"
    duplicate = deepcopy(episode)
    duplicate["seed"] = 999
    duplicate["private_note"] = "different private record, same visible puzzle"
    for pair in duplicate["test"]:
        pair["output"] = [[9]]
    destination = tmp_path / "duplicate_publication"
    with pytest.raises(ValueError, match="(?i)duplicate"):
        prototype.export_batch([episode, duplicate], destination)
    assert not destination.exists()
