from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "4dd0b3ed33ee"
REPO = find_root(__file__)
HERE = REPO / "generators" / TASK_ID / "workspace" / "parametric"
FIRST = {"match_selector": "first"}
LARGEST = {"match_selector": "largest_area"}


def _load(name: str, filename: str):
    path = HERE / filename
    assert path.is_file(), f"missing parametric artifact: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def proto():
    return _load("parametric_4dd0_match_selector", "prototype.py")


def _canonical_program() -> str:
    programs = []
    with canonical_path(REPO).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    assert programs and len(set(programs)) == 1
    return programs[0]


def test_default_program_is_exact_canonical_authority(proto):
    assert proto.DEFAULT == FIRST
    assert proto.SETTINGS == [FIRST, LARGEST]
    assert proto.program(FIRST) == _canonical_program()
    assert proto.program(LARGEST) != _canonical_program()


def test_inputs_are_matched_prefix_stable_and_counts_are_strict(proto):
    for bad in (
        {},
        {"match_selector": "other"},
        {"match_selector": 1},
        {"match_selector": "first", "extra": 0},
    ):
        with pytest.raises(ValueError):
            proto.program(bad)

    for key, value in (("seed", True), ("demos", 1), ("demos", 7), ("queries", 3), ("queries", 5)):
        kwargs = dict(seed=19, settings=FIRST, demos=2, queries=4)
        kwargs[key] = value
        with pytest.raises(ValueError):
            proto.generate(**kwargs)

    short = proto.generate(19, FIRST, demos=2, queries=4)
    long = proto.generate(19, FIRST, demos=6, queries=4)
    alternate = proto.generate(19, LARGEST, demos=2, queries=4)
    assert short == proto.generate(19, FIRST, demos=2, queries=4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"]
    assert [pair["input"] for pair in short["train"] + short["test"]] == [
        pair["input"] for pair in alternate["train"] + alternate["test"]
    ]
    inputs = [pair["input"] for pair in short["train"] + short["test"]]
    assert len({proto.digest(grid) for grid in inputs}) == len(inputs)


def test_each_scene_requires_header_filter_then_selector(proto):
    episode = proto.generate(7, LARGEST, demos=6, queries=4)
    for pair in episode["train"] + episode["test"]:
        summary = proto.scene_summary(pair["input"])
        assert summary["matching_count"] >= 4
        assert summary["first_match_index"] != summary["largest_area_match_index"]
        assert summary["largest_area_match_index"] != summary["last_match_index"]
        assert summary["largest_overall_index"] not in summary["matching_indices"]
        assert summary["largest_boundary_match_index"] != summary["largest_area_match_index"]
        assert summary["smallest_area_match_index"] != summary["first_match_index"]
        assert proto.transform(pair["input"], FIRST) != proto.transform(pair["input"], LARGEST)


def test_two_demo_minimum_identifies_both_settings_and_refutes_shortcuts(proto):
    for seed in range(64):
        first = proto.generate(seed, FIRST, demos=2, queries=4)
        largest = proto.generate(seed, LARGEST, demos=2, queries=4)
        for episode, selected in ((first, FIRST), (largest, LARGEST)):
            certificate = proto.certify(episode)
            assert certificate["survivors"] == [selected]
            assert certificate["shortcut_survivors"] == []
            assert len(certificate["queries"]) == 4


def test_hole_controls_defeat_missing_cell_and_eight_connected_shortcuts(proto):
    # Demo 1 uses two 4-connected holes joined only diagonally, and both
    # selected dense candidates contain a multi-cell hole region.
    for setting in proto.SETTINGS:
        episode = proto.generate(3, setting, demos=2, queries=4)
        assert any(
            proto._shortcut("missing_cells_equal_header", pair["input"], setting) != pair["output"]
            for pair in episode["train"]
        )
        assert any(
            proto._shortcut("eight_connected_holes", pair["input"], setting) != pair["output"]
            for pair in episode["train"]
        )


def test_four_queries_include_substantive_30x30_and_boundary_contacts(proto):
    for setting in proto.SETTINGS:
        episode = proto.generate(29, setting, demos=2, queries=4)
        assert len(episode["test"]) == 4
        assert len({proto.digest(pair["input"]) for pair in episode["test"]}) == 4
        stress = episode["test"][3]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        body_nonzero = [(r, c) for r, row in enumerate(stress[1:], start=1) for c, value in enumerate(row) if value]
        assert len(body_nonzero) >= 120
        assert {"top", "bottom", "left", "right"} <= proto.boundary_contacts(stress)
        assert proto.scene_summary(stress)["matching_count"] >= 4


def test_public_turn_contains_only_demos_and_one_current_query(proto):
    episode = proto.generate(41, LARGEST, demos=3, queries=4)
    views = [proto.public_turn(episode, index) for index in range(4)]
    for index, view in enumerate(views):
        assert set(view) == {"train", "test"}
        assert len(view["train"]) == 3
        assert view["test"] == [{"input": episode["test"][index]["input"]}]
        assert "settings" not in json.dumps(view)
        assert public_challenge_id(view) == proto.public_id(episode, index)
        assert public_challenge_bytes(view).endswith(b"\n")

    mutated = copy.deepcopy(episode)
    mutated["settings"] = FIRST
    mutated["program_solution"] = "private mutation"
    mutated["certificate"] = {"private": True}
    mutated["test"][1]["output"] = [[9]]
    mutated["test"][2]["input"] = [[9]]
    assert public_challenge_bytes(proto.public_turn(mutated, 0)) == public_challenge_bytes(views[0])


def test_python_claims_match_protected_racket(proto):
    with proto.RacketRunner() as execute:
        assert execute.identity["backend"] == "racket"
        assert execute.identity["protected"] is True
        for setting in proto.SETTINGS:
            episode = proto.generate(17, setting, demos=2, queries=4)
            certificate = proto.certify(episode, execute=execute)
            assert certificate["racket_checked"] is True
            for pair in episode["train"] + episode["test"]:
                assert execute(proto.program(setting), pair["input"]) == pair["output"]


def test_minimum_lessons_refute_density_interior_aspect_and_missing_shortcuts(proto):
    added = (
        "fewest_missing_match",
        "highest_density_match",
        "most_interior_match",
        "smallest_aspect_match",
    )
    assert set(added) <= set(proto.SHORTCUTS)
    for seed in range(32):
        for setting in proto.SETTINGS:
            episode = proto.generate(seed, setting, demos=2, queries=4)
            for name in added:
                assert any(
                    proto._shortcut(name, pair["input"], setting) != pair["output"]
                    for pair in episode["train"]
                ), (seed, setting, name)


def test_fixed_dimensions_do_not_encode_largest_match_rank_or_color(proto):
    ranks = set()
    colors = set()
    outputs = set()
    for seed in range(32):
        grid = proto.generate(seed, LARGEST, demos=2, queries=4)["train"][0]["input"]
        summary = proto.scene_summary(grid)
        rank = summary["matching_indices"].index(summary["largest_area_match_index"])
        ranks.add(rank)
        colors.add(summary["components"][summary["largest_area_match_index"]]["color"])
        outputs.add(proto.digest(proto.transform(grid, LARGEST)))
    assert len(ranks) >= 2
    assert len(colors) >= 2
    assert len(outputs) >= 4


def test_minimum_crosses_largest_winner_vertical_shelf(proto):
    assert "top_shelf_largest_match" in proto.SHORTCUTS
    for seed in range(24):
        episode = proto.generate(seed, LARGEST, demos=2, queries=4)
        first = proto.scene_summary(episode["train"][0]["input"])
        second = proto.scene_summary(episode["train"][1]["input"])
        first_components = first["components"]
        second_components = second["components"]
        assert (
            first_components[first["largest_area_match_index"]]["bbox"][0]
            > first_components[first["first_match_index"]]["bbox"][0]
        )
        assert (
            second_components[second["largest_area_match_index"]]["bbox"][0]
            == second_components[second["first_match_index"]]["bbox"][0]
        )


def test_certificate_rejects_stale_program_hash(proto):
    episode = proto.generate(11, LARGEST, demos=2, queries=4)
    episode["program_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="program hash"):
        proto.certify(episode)
