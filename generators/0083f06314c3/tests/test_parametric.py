"""Behavioral regressions for the two template-search orientation policies."""
from __future__ import annotations

import importlib.util
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import sys

import pytest


TASK_HOME = Path(__file__).resolve().parents[1]
PROTOTYPE_PATH = TASK_HOME / "workspace" / "parametric" / "prototype.py"
SETTINGS = ({"orientation": "fixed"}, {"orientation": "rotations"})
RIVALS = {
    "other_setting", "always_a", "always_b", "literal_zero", "color_blind",
    "dihedral", "first_match", "disjoint_matches", "xor_matches",
    "mark_all_nonzero", "fill_bounding_boxes", "few_groups", "most_frequent_template",
}


def _load_prototype():
    name = "test_0083f06314c3_parametric_prototype"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, PROTOTYPE_PATH)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def test_declared_orientation_settings_have_canonical_default():
    assert PROTOTYPE_PATH.is_file(), "The orientation prototype has not been implemented"
    prototype = _load_prototype()
    assert prototype.SETTINGS == ({"orientation": "fixed"}, {"orientation": "rotations"})
    assert prototype.DEFAULT == {"orientation": "fixed"}


@pytest.fixture(scope="module")
def prototype():
    return _load_prototype()


def _blank(h, w):
    return [[0] * w for _ in range(h)]


def _painted(h, w, cells):
    out = _blank(h, w)
    for r, c in cells:
        out[r][c] = 8
    return out


def _component_count(grid):
    remaining = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v}
    count = 0
    while remaining:
        count += 1
        frontier = [remaining.pop()]
        while frontier:
            r, c = frontier.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    frontier.append(neighbor)
    return count


def _scene(template_a, template_b, selector, board):
    """Only assemble panels; expected matching footprints are hand-authored."""
    height = len(board)
    assert height >= max(len(template_a), len(template_b))
    panels = []
    for template in (template_a, template_b):
        panel = _blank(height, len(template[0]))
        panel[:len(template)] = deepcopy(template)
        panels.append(panel)
    selector_panel = [[0] for _ in range(height)]
    selector_panel[-1][0] = selector
    panels.extend((selector_panel, deepcopy(board)))
    return [panels[0][r] + [9] + panels[1][r] + [9]
            + panels[2][r] + [9] + panels[3][r] for r in range(height)]


def _split(grid):
    width = len(grid[0])
    dividers = [c for c in range(width) if all(row[c] == 9 for row in grid)]
    assert len(dividers) == 3
    bounds = [-1, *dividers, width]
    return [[row[left + 1:right] for row in grid]
            for left, right in zip(bounds, bounds[1:])]


def _orientation_scene(selector=2):
    # Original L4, clockwise L4, mirror-only L4, wrong-color L4, and template B.
    board = _blank(8, 13)
    original = {(0, 0), (1, 0), (2, 0), (2, 1)}
    rotated = {(0, 4), (0, 5), (0, 6), (1, 4)}
    reflected = {(0, 10), (1, 10), (2, 9), (2, 10)}
    wrong_color = {(4, 0), (5, 0), (6, 0), (6, 1)}
    template_b = {(4, 5), (4, 6), (5, 5)}
    for cells, color in ((original | rotated | reflected, 4),
                         (wrong_color, 7), (template_b, 6)):
        for r, c in cells:
            board[r][c] = color
    board[0][1] = 7  # Occupied wildcard cell; it must not be painted.
    return _scene([[4, 0], [4, 0], [4, 4]], [[6, 6], [6, 0]], selector, board)


def test_default_program_is_exact_selected_authority(prototype):
    canonical = TASK_HOME.parents[1] / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with canonical.open() as source:
        rows = [json.loads(line) for line in source if '"0083f06314c3"' in line]
    selected = [row for row in rows if row.get("task_id") == "0083f06314c3"]
    assert len(selected) == 1
    authority = selected[0]["program_solution"]
    assert prototype.program(SETTINGS[0]) == authority
    assert authority.count("(find-matches board template 0)") == 1
    assert prototype.program(SETTINGS[1]) == authority.replace(
        "(find-matches board template 0)", "(find-matches board template 1)")


@pytest.mark.parametrize("settings,expected_cells", [
    (SETTINGS[0], {(0, 0), (1, 0), (2, 0), (2, 1)}),
    (SETTINGS[1], {(0, 0), (1, 0), (2, 0), (2, 1),
                   (0, 4), (0, 5), (0, 6), (1, 4)}),
])
def test_exact_colors_wildcards_and_allowed_orientations(prototype, settings, expected_cells):
    grid = _orientation_scene()
    before = deepcopy(grid)
    assert prototype.rule_mirror(grid, settings) == _painted(8, 13, expected_cells)
    assert grid == before


@pytest.mark.parametrize("selector", [1, 3, 4, 5, 6, 7, 8])
@pytest.mark.parametrize("settings", SETTINGS)
def test_every_non_two_selector_chooses_template_b(prototype, selector, settings):
    assert prototype.rule_mirror(_orientation_scene(selector), settings) == _painted(
        8, 13, {(4, 5), (4, 6), (5, 5)})


@pytest.mark.parametrize("settings,expected_cells", [
    (SETTINGS[0], {(0, 0), (1, 0), (2, 0), (2, 1)}),
    (SETTINGS[1], {(0, 0), (1, 0), (2, 0), (2, 1),
                   (0, 4), (0, 5), (0, 6), (1, 4)}),
])
def test_rotations_preserve_each_multicolor_template_cell(prototype, settings, expected_cells):
    board = _blank(6, 10)
    for r, c, color in ((0, 0, 4), (1, 0, 5), (2, 0, 6), (2, 1, 7),
                         (0, 4, 6), (0, 5, 5), (0, 6, 4), (1, 4, 7)):
        board[r][c] = color
    # Matching silhouette, but swapped colors, is not a valid third copy.
    for r, c, color in ((3, 8, 5), (4, 8, 4), (5, 8, 6), (5, 9, 7)):
        board[r][c] = color
    board[0][1] = 3
    grid = _scene([[4, 0], [5, 0], [6, 7]], [[1]], 2, board)
    assert prototype.rule_mirror(grid, settings) == _painted(6, 10, expected_cells)


@pytest.mark.parametrize("settings", SETTINGS)
def test_overlapping_matches_use_union_without_erasing_shared_cells(prototype, settings):
    cells = {(0, 0), (1, 0), (2, 0), (2, 1), (3, 0), (3, 1)}
    board = _blank(5, 6)
    for r, c in cells:
        board[r][c] = 4
    grid = _scene([[4, 0], [4, 0], [4, 4]], [[6]], 2, board)
    expected = _painted(5, 6, cells)
    assert prototype.rule_mirror(grid, settings) == expected
    rivals = prototype.rival_outputs(grid, settings)
    for name in ("first_match", "disjoint_matches", "xor_matches"):
        assert rivals[name] != expected, name


def test_dependency_intermediate_drives_the_downstream_result(prototype):
    grid_a, grid_b = _orientation_scene(2), _orientation_scene(1)
    a = prototype.dependency_intermediate(grid_a)
    b = prototype.dependency_intermediate(grid_b)
    assert a == {"selector_color": 2, "selected_panel": 0,
                 "template": [[4, 0], [4, 0], [4, 4]],
                 "other_template": [[6, 6], [6, 0]]}
    assert b == {"selector_color": 1, "selected_panel": 1,
                 "template": [[6, 6], [6, 0]],
                 "other_template": [[4, 0], [4, 0], [4, 4]]}
    assert _split(grid_a)[3] == _split(grid_b)[3]
    for settings in SETTINGS:
        assert prototype.rule_mirror(grid_a, settings) != prototype.rule_mirror(grid_b, settings)
    a["template"][0][0] = 1
    assert prototype.dependency_intermediate(grid_a)["template"][0][0] == 4


@pytest.mark.parametrize("settings", SETTINGS)
@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (6, 1), (6, 4)])
def test_demo_and_query_count_boundaries_are_independent(prototype, settings, demos, queries):
    episode = prototype.generate(0, settings, demos=demos, queries=queries)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == queries
    assert episode["settings"] == settings


def test_same_seed_matches_inputs_across_settings_and_count_prefixes(prototype):
    fixed = prototype.generate(17, SETTINGS[0], demos=6, queries=4)
    rotations = prototype.generate(17, SETTINGS[1], demos=6, queries=4)
    for split in ("train", "test"):
        assert [p["input"] for p in fixed[split]] == [p["input"] for p in rotations[split]]
    assert any(a["output"] != b["output"] for a, b in zip(fixed["train"][:2], rotations["train"][:2]))
    for settings, full in zip(SETTINGS, (fixed, rotations)):
        few_demos = prototype.generate(17, settings, demos=2, queries=4)
        few_queries = prototype.generate(17, settings, demos=6, queries=1)
        assert few_demos["train"] == full["train"][:2]
        assert few_demos["test"] == full["test"]
        assert few_queries["train"] == full["train"]
        assert few_queries["test"] == full["test"][:1]


def test_query_scales_are_novel_and_reach_a_30_by_30_input(prototype):
    episode = prototype.generate(0, SETTINGS[1], demos=6, queries=4)
    input_shapes = [(len(p["input"]), len(p["input"][0])) for p in episode["test"]]
    assert input_shapes[0] == (12, 28)
    assert 19 <= input_shapes[1][0] <= 27 and input_shapes[1][1] == 29
    assert input_shapes[2:] == [(16, 30), (30, 30)]
    for pair, board_width in zip(episode["test"], (18, 19, 20, 20)):
        assert (len(pair["output"]), len(pair["output"][0])) == (len(pair["input"]), board_width)
    all_inputs = [json.dumps(p["input"]) for p in episode["train"] + episode["test"]]
    assert len(set(all_inputs)) == 10
    demo_outputs = [p["output"] for p in episode["train"]]
    assert all(p["output"] not in demo_outputs for p in episode["test"])
    # The enlarged search board is occupied at distant coordinates, not empty padding.
    large_board = _split(episode["test"][-1]["input"])[3]
    assert any(v for row in large_board[25:] for v in row)
    assert any(v for row in large_board for v in row[17:])


@pytest.mark.parametrize("settings", SETTINGS)
@pytest.mark.parametrize("seed", [0, 17])
def test_two_demo_positive_group_counts_vary_and_cover_query_counts(prototype, settings, seed):
    episode = prototype.generate(seed, settings, demos=2, queries=4)
    demos = [_component_count(p["output"]) for p in episode["train"]]
    queries = [_component_count(p["output"]) for p in episode["test"]]
    assert 0 < min(demos) < max(demos)
    assert all(0 < count <= max(demos) for count in queries)
    many = episode["train"][1]
    assert prototype.rival_outputs(many["input"], settings)["few_groups"] != many["output"]


@pytest.mark.parametrize("settings", SETTINGS)
def test_selector_is_taught_with_both_minority_and_majority_template_colors(prototype, settings):
    episode = prototype.generate(0, settings, demos=2, queries=4)
    counts = []
    for index, pair in enumerate(episode["train"]):
        panels = _split(pair["input"])
        colors = [next(v for row in panel for v in row if v) for panel in panels[:2]]
        flat = [v for row in panels[3] for v in row]
        counts.append((flat.count(colors[index]), flat.count(colors[1-index])))
    assert counts[0][0] < counts[0][1]
    assert counts[1][0] > counts[1][1]
    pair = episode["train"][0]
    assert prototype.rival_outputs(pair["input"], settings)["most_frequent_template"] != pair["output"]


def test_episode_teaches_its_single_non_two_selector_code(prototype):
    for seed, b_code in enumerate((1, 3, 4, 5, 6, 7, 8)):
        episode = prototype.generate(seed, SETTINGS[0], demos=2, queries=4)
        observed = []
        for pair in episode["train"] + episode["test"]:
            selector = [v for row in _split(pair["input"])[2] for v in row if v]
            assert len(selector) == 1
            observed.append(selector[0])
        assert observed[:2] == [2, b_code]
        assert set(observed) == {2, b_code}


@pytest.mark.parametrize("settings", SETTINGS)
def test_two_demos_refute_all_named_parameter_aware_rivals(prototype, settings):
    episode = prototype.generate(0, settings, demos=2, queries=4)
    certificate = prototype.teaching_check(episode)
    assert certificate["status"] == "identified"
    assert certificate["surviving_rivals"] == []
    assert set(certificate["refuted_by"]) == RIVALS
    assert set(prototype.rival_programs(settings)) == RIVALS
    for name, demo_index in certificate["refuted_by"].items():
        assert type(demo_index) is int and 0 <= demo_index < 2
        pair = episode["train"][demo_index]
        assert prototype.rival_outputs(pair["input"], settings)[name] != pair["output"]


def test_teaching_certificate_never_reads_private_queries(prototype):
    episode = prototype.generate(0, SETTINGS[1], demos=2, queries=4)
    expected = prototype.teaching_check(episode)
    no_queries = {**episode, "test": []}
    poisoned_queries = {**episode, "test": [{"input": None, "output": object()}]}
    assert prototype.teaching_check(no_queries) == expected
    assert prototype.teaching_check(poisoned_queries) == expected


def test_uninformative_demos_leave_rivals_alive(prototype):
    grid = _scene([[4, 0], [4, 0], [4, 4]], [[6]], 2, _blank(5, 6))
    pair = {"input": grid, "output": _blank(5, 6)}
    certificate = prototype.teaching_check({"settings": SETTINGS[0],
                                            "train": [pair, deepcopy(pair)], "test": []})
    assert certificate["status"] == "ambiguous"
    assert set(certificate["surviving_rivals"]) == RIVALS
    assert certificate["refuted_by"] == {}


def test_wrong_demonstration_label_is_not_a_teaching_certificate(prototype):
    episode = prototype.generate(0, SETTINGS[0], demos=2, queries=1)
    episode["train"][0]["output"][0][0] ^= 8
    with pytest.raises(ValueError, match="label"):
        prototype.teaching_check(episode)


@pytest.mark.parametrize("name,bad", [
    ("seed", -1), ("seed", 2**63), ("seed", True), ("seed", 0.0), ("seed", "0"),
    ("demos", 1), ("demos", 7), ("demos", True), ("demos", 2.0), ("demos", None),
    ("queries", 0), ("queries", 5), ("queries", False), ("queries", 1.0), ("queries", "1"),
])
def test_invalid_controls_are_rejected_before_sampling(prototype, name, bad):
    arguments = {"seed": 0, "settings": SETTINGS[0], "demos": 2, "queries": 1}
    arguments[name] = bad
    with pytest.raises(ValueError):
        prototype.generate(**arguments)


@pytest.mark.parametrize("settings", [None, {}, {"orientation": "dihedral"},
    {"orientation": "fixed", "extra": 0}, {"orientation": True}, {"orientation": 0}, ("fixed",)])
def test_only_exact_declared_settings_are_accepted(prototype, settings):
    with pytest.raises(ValueError):
        prototype.generate(0, settings, demos=2, queries=1)
    with pytest.raises(ValueError):
        prototype.program(settings)
    with pytest.raises(ValueError):
        prototype.rule_mirror(_orientation_scene(), settings)


@pytest.mark.parametrize("bad", [True, 4.0, None, -1, 10])
def test_solver_rejects_non_integer_or_out_of_range_grid_cells(prototype, bad):
    grid = _orientation_scene()
    grid[0][-1] = bad
    with pytest.raises(ValueError):
        prototype.rule_mirror(grid, SETTINGS[0])


def test_determinism_fresh_returns_and_global_rng_purity(prototype):
    state = random.getstate()
    try:
        random.seed(90210)
        before = random.getstate()
        episode = prototype.generate(2**63 - 1, SETTINGS[0], demos=2, queries=1)
        assert random.getstate() == before
        original = deepcopy(episode)
        repeated = prototype.generate(2**63 - 1, SETTINGS[0], demos=2, queries=1)
        assert repeated == original
        episode["train"][0]["input"][0][0] ^= 1
        episode["test"][0]["output"][0][0] ^= 8
        episode["settings"]["orientation"] = "rotations"
        assert repeated == original
        assert prototype.generate(2**63 - 1, SETTINGS[0], demos=2, queries=1) == original
    finally:
        random.setstate(state)


def test_public_projection_excludes_labels_settings_and_metadata(prototype):
    episode = prototype.generate(0, SETTINGS[1], demos=2, queries=4)
    for index in (0, 3):
        public = prototype.public_challenge(episode, index)
        expected = {"train": episode["train"], "test": [{"input": episode["test"][index]["input"]}]}
        assert public == expected
        altered = deepcopy(episode)
        altered["seed"] = "private-seed-must-not-affect-public"
        altered["settings"] = {"private": "unread"}
        altered["program_solution"] = "private program"
        altered["test"][index]["output"] = object()
        assert prototype.public_challenge(altered, index) == expected
    public["train"][0]["input"][0][0] ^= 1
    assert public != prototype.public_challenge(episode, 3)


@pytest.mark.parametrize("index", [-1, 4, True, 0.0, "0"])
def test_public_query_index_is_a_bounded_literal_integer(prototype, index):
    episode = prototype.generate(0, SETTINGS[0], demos=2, queries=4)
    with pytest.raises(ValueError):
        prototype.public_challenge(episode, index)


def test_export_ids_hash_exact_public_bytes_and_private_banks_are_separate(prototype, tmp_path):
    episodes = [prototype.generate(0, settings, demos=2, queries=4) for settings in SETTINGS]
    before = deepcopy(episodes)
    destination = tmp_path / "export"
    receipt = prototype.export_batch(episodes, destination)
    assert receipt["episodes"] == 2
    assert receipt["training_admitted"] is False
    public_paths = sorted((destination / "public").glob("*.json"))
    private_paths = sorted((destination / "private").glob("*.json"))
    assert len(public_paths) == len(private_paths) == 2
    assert {p.name for p in public_paths} == {p.name for p in private_paths}
    recovered = []
    for path in public_paths:
        content = path.read_bytes()
        assert path.stem == hashlib.sha256(content).hexdigest()
        public = json.loads(content)
        private = json.loads((destination / "private" / path.name).read_bytes())
        assert public == {"train": private["train"], "test": [{"input": private["test"][0]["input"]}]}
        assert len(private["test"]) == 4
        assert private["program_solution"] == prototype.program(private["settings"])
        recovered.append(private)
    assert sorted(recovered, key=lambda e: e["settings"]["orientation"]) == episodes
    assert episodes == before


def test_private_metadata_does_not_change_public_export_identity(prototype, tmp_path):
    episode = prototype.generate(0, SETTINGS[0], demos=2, queries=1)
    changed = deepcopy(episode)
    changed["private_note"] = {"review": "separate provenance"}
    for name, value in (("base", episode), ("changed", changed)):
        prototype.export_batch([value], tmp_path / name)
    base = list((tmp_path / "base" / "public").glob("*.json"))
    altered = list((tmp_path / "changed" / "public").glob("*.json"))
    assert len(base) == len(altered) == 1
    assert base[0].name == altered[0].name
    assert base[0].read_bytes() == altered[0].read_bytes()


def test_duplicate_visible_challenges_are_rejected_before_destination_creation(prototype, tmp_path):
    episode = prototype.generate(0, SETTINGS[0], demos=2, queries=4)
    hidden_difference = deepcopy(episode)
    hidden_difference["seed"] = 123
    hidden_difference["test"][-1]["output"][0][0] ^= 8
    destination = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate visible"):
        prototype.export_batch([episode, hidden_difference], destination)
    assert not destination.exists()


@pytest.mark.parametrize("bad", [object(), float("nan"), float("inf")])
def test_private_serialization_failure_publishes_no_partial_batch(prototype, tmp_path, bad):
    first = prototype.generate(0, SETTINGS[0], demos=2, queries=1)
    later = prototype.generate(1, SETTINGS[1], demos=2, queries=1)
    later["private_metadata"] = bad
    destination = tmp_path / "serialization"
    with pytest.raises((ValueError, TypeError)):
        prototype.export_batch([first, later], destination)
    assert not destination.exists()


def test_wrong_later_query_label_publishes_no_partial_batch(prototype, tmp_path):
    first = prototype.generate(0, SETTINGS[0], demos=2, queries=4)
    later = prototype.generate(1, SETTINGS[1], demos=2, queries=4)
    later["test"][-1]["output"][0][0] ^= 8
    destination = tmp_path / "bad-label"
    with pytest.raises(ValueError, match="label"):
        prototype.export_batch([first, later], destination)
    assert not destination.exists()


def test_existing_export_directory_is_preserved(prototype, tmp_path):
    episode = prototype.generate(0, SETTINGS[0], demos=2, queries=1)
    destination = tmp_path / "existing"
    destination.mkdir()
    sentinel = destination / "user-file.txt"
    sentinel.write_text("keep this exact content")
    with pytest.raises(FileExistsError):
        prototype.export_batch([episode], destination)
    assert sentinel.read_text() == "keep this exact content"
    assert list(destination.iterdir()) == [sentinel]
