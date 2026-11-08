"""Focused contract tests for a separate public-task-inspired prototype."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest


TASK = Path(__file__).resolve().parents[1]
REPO = TASK.parents[1]
SOURCE = TASK / "workspace/parametric/inspired_template_expansion.py"


@pytest.fixture(scope="module")
def prototype():
    assert SOURCE.is_file(), "separate inspired prototype API is not implemented"
    spec = importlib.util.spec_from_file_location("inspired_template_expansion", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def bridge():
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=15) as runtime:
        yield runtime


@pytest.fixture(scope="module")
def parent_task():
    path = REPO / "shared/data/raw/arc-agi_evaluation_challenges.json"
    return json.loads(path.read_text())["65b59efc"]


def test_identity_reproduces_every_labeled_parent_demonstration(prototype, bridge, parent_task):
    # Catches skipping color lookup, template geometry, or the aligned swatch.
    for pair in parent_task["train"]:
        assert prototype.execute(bridge, pair["input"], "identity") == pair["output"]


def test_transpose_moves_whole_tiles_without_transposing_their_pixels(prototype, bridge, parent_task):
    # Hand-derived from the second parent demonstration's coarse arrangement.
    expected = [list(map(int, row)) for row in [
        "303303999", "333333909", "030030999",
        "000000999", "000000909", "000000999",
        "070070000", "777777000", "070070000",
    ]]
    assert prototype.execute(bridge, parent_task["train"][1]["input"], "transpose") == expected


def test_public_queries_support_four_templates_padding_and_even_swatches(prototype, bridge, parent_task):
    # These are structural checks; the public file contains no official query labels.
    assert [len(prototype.execute(bridge, pair["input"], "identity"))
            for pair in parent_task["test"]] == [25, 16]


def test_parent_source_binding_hashes_the_selected_challenge_not_the_whole_file(prototype, bridge):
    # The assignment pins the compact, sorted JSON object for the selected task.
    report = prototype.check_parent(bridge)
    assert report["challenge_sha256"] == "ee576437bcd000a274eb9a3ab26c827d293736f23a2940e227f575b1423ee067"
    assert len([p for p in report["pairs"] if p.get("exact_match")]) == 3
    assert all(not p["official_label_available"] for p in report["pairs"] if p["split"] == "test")


def test_paired_settings_share_inputs_and_have_four_distinct_supported_queries(prototype, bridge):
    episodes = [prototype.make_episode(bridge, input_seed=137, setting=setting,
                                      n_demos=3, n_queries=4)
                for setting in ("identity", "transpose")]
    inputs = [[p["input"] for p in e["train"] + e["test"]] for e in episodes]
    assert inputs[0] == inputs[1]
    assert len({json.dumps(grid) for grid in inputs[0]}) == 7
    assert episodes[0]["train"][0]["output"] != episodes[1]["train"][0]["output"]
    for setting, episode in zip(("identity", "transpose"), episodes):
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4
        certificate = episode["certificate"]
        assert certificate["surviving_rivals"] == [setting]
        assert all(q["supported"] for q in certificate["queries"])
        # Removing all private query labels cannot change the certificate.
        assert prototype.certify(episode["train"],
                                 [p["input"] for p in episode["test"]],
                                 setting) == certificate


def test_export_names_and_bytes_ignore_query_answers_and_private_metadata(prototype, bridge, tmp_path):
    first = prototype.make_episode(bridge, input_seed=91, setting="identity", n_demos=1, n_queries=4)
    changed = deepcopy(first)
    changed["metadata"]["input_seed"] = 999
    changed["metadata"]["parameters"] = {"coarse_placement": "arbitrary private annotation"}
    for pair in changed["test"]:
        pair["output"] = [[9]]
    one, two = tmp_path / "one", tmp_path / "two"
    prototype.write_bundle(one, [first])
    prototype.write_bundle(two, [changed])
    files1 = {p.name: p.read_bytes() for p in (one / "public").glob("*.json")}
    files2 = {p.name: p.read_bytes() for p in (two / "public").glob("*.json")}
    assert files1 == files2
    assert len(files1) == 1
    name, raw = next(iter(files1.items()))
    assert name == prototype.public_challenge_id(first) + ".json"
    assert raw == prototype.public_challenge_bytes(first)
    visible = json.loads(raw)
    assert set(visible) == {"train", "test"}
    assert all(set(pair) == {"input"} for pair in visible["test"])


@pytest.mark.parametrize("numeric_kind", ["float", "bool"])
def test_certificate_rejects_inexact_demo_labels_before_comparing_rivals(prototype, parent_task, numeric_kind):
    pair = deepcopy(parent_task["train"][0])
    if numeric_kind == "float":
        pair["output"] = [[float(v) for v in row] for row in pair["output"]]
    else:
        pair["output"][1][1] = False  # Numerically equal to the real background 0.
    with pytest.raises(ValueError):
        prototype.certify([pair], [parent_task["test"][0]["input"]], "identity")


@pytest.mark.parametrize("bad_output", [[[False]], [[1.0]], [], [[0], [0, 1]], [[10]], [[0]] * 31])
def test_export_rejects_malformed_private_query_labels(prototype, parent_task, tmp_path, bad_output):
    episode = dict(train=[deepcopy(parent_task["train"][0])],
                   test=[dict(input=parent_task["test"][0]["input"], output=bad_output)])
    destination = tmp_path / "invalid"
    with pytest.raises(ValueError):
        prototype.write_bundle(destination, [episode])
    assert not destination.exists()


@pytest.mark.parametrize("kwargs", [
    {"n_demos": 0}, {"n_demos": True}, {"n_demos": 1.0}, {"n_demos": 13},
    {"n_queries": 0}, {"n_queries": False}, {"n_queries": 4.0}, {"n_queries": 9},
    {"input_seed": True}, {"input_seed": -1}, {"setting": "rotate"},
])
def test_invalid_episode_requests_are_rejected_before_labeling(prototype, bridge, kwargs):
    request = dict(input_seed=7, setting="identity", n_demos=2, n_queries=4)
    request.update(kwargs)
    with pytest.raises(ValueError):
        prototype.make_episode(bridge, **request)


def test_input_validation_rejects_boolean_colors_and_overlapping_masks(prototype, bridge, parent_task):
    invalid = deepcopy(parent_task["train"][0]["input"])
    invalid[0][0] = True
    with pytest.raises(ValueError):
        prototype.execute(bridge, invalid, "identity")
    invalid = deepcopy(parent_task["train"][0]["input"])
    invalid[6][4] = 4  # Red at coarse (2,0) already occupies this location.
    with pytest.raises(ValueError):
        prototype.execute(bridge, invalid, "identity")


@pytest.mark.parametrize("size,templates", [(3, 3), (3, 4), (5, 3), (5, 4)])
def test_sampler_dimension_boundaries_execute_in_both_settings(prototype, bridge, size, templates):
    grid = prototype.sample_input(410, 0, size=size, templates=templates)
    assert max(len(grid), len(grid[0])) <= 30
    for setting in ("identity", "transpose"):
        output = prototype.execute(bridge, grid, setting)
        assert len(output) == size * size
        assert all(len(row) == size * size for row in output)
        assert output == prototype.predict(grid, setting)
