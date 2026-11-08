"""Replay exact role-conditioned shortcut witnesses without redrawing inputs."""
from __future__ import annotations

import copy
from itertools import groupby
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, load_selected_generator


ROOT = find_root(__file__)
GEN, _, _ = load_selected_generator("8e6c44aee812", root=ROOT)
FIXTURE_PATH = Path(__file__).resolve().parents[1] / "counterexamples/role_conditioned_first_run.json"
CAPTURE_SHA256 = "168ea9c084ecedf7f5dd8302251b370ce3c816e7b06512f7f27a09160985d869"


@pytest.fixture(scope="module")
def capture():
    data = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert data["task_id"] == "8e6c44aee812"
    assert data["provenance"]["capture_evidence_sha256"] == CAPTURE_SHA256
    assert GEN.RULE_HASH == data["provenance"]["executed_rule_hash"]
    return data


@pytest.fixture(scope="module")
def current_canonical():
    return {(pair["variant"], pair["split"], pair["pair_index"]): pair
            for pair in canonical_pairs("8e6c44aee812", root=ROOT, labeled_only=True)}


def _first_color_exempt_first_run(grid):
    """Independent wrong rule: repeat first color freely, deduplicate later runs."""
    active = [grid[i][i] for i in range(len(grid))]
    while active and active[-1] == 0:
        active.pop()
    seen, kept = set(), []
    first_color = active[0]
    for color, run in groupby(active):
        if color == first_color or color not in seen:
            kept.extend(run)
        seen.add(color)
    return [[kept[max(row, col) % len(kept)] for col in range(2 * len(grid[0]))]
            for row in range(2 * len(grid))]


@pytest.mark.parametrize("pair_id", ("canonical/0", "canonical/1", "canonical/2", "canonical/3"))
def test_role_conditioned_rival_fits_retained_canonical_labels(pair_id, capture, current_canonical):
    pair = capture["pairs"][pair_id]
    request = pair["request"]
    canonical = current_canonical[(request["variant"], request["split"], request["pair_index"])]
    assert pair["input"] == canonical["input"]
    assert pair["output"] == canonical["output"]
    assert GEN.self_check(copy.deepcopy(pair["input"])) == []
    assert _first_color_exempt_first_run(pair["input"]) == pair["rival_output"] == pair["output"]


@pytest.mark.parametrize("lesson_name", ("production", "rotation"))
def test_retained_ambiguous_lesson_explicitly_rejects_role_conditioned_rival(lesson_name, capture):
    lesson = next(row for row in capture["lessons"] if row["name"] == lesson_name)
    assert len(lesson["demo_ids"]) == 5
    assert lesson["captured_hook_reasons"] == []
    predictions = {}
    for pair_id in [*lesson["demo_ids"], lesson["query_id"]]:
        pair = capture["pairs"][pair_id]
        assert pair["captured_self_check"] == [], pair_id
        assert GEN.self_check(copy.deepcopy(pair["input"])) == [], pair_id
        predictions[pair_id] = _first_color_exempt_first_run(pair["input"])
        assert predictions[pair_id] == pair["rival_output"], pair_id
    for pair_id in lesson["demo_ids"]:
        assert predictions[pair_id] == capture["pairs"][pair_id]["output"], pair_id

    query = capture["pairs"][lesson["query_id"]]
    rival_output = predictions[lesson["query_id"]]
    different = [[row, col] for row, values in enumerate(query["output"])
                 for col, value in enumerate(values) if value != rival_output[row][col]]
    assert different == lesson["different_coordinates"]
    expected_differences, expected_cells = {"production": (128, 144), "rotation": (148, 196)}[lesson_name]
    assert len(different) == lesson["different_cells"] == expected_differences
    assert sum(map(len, query["output"])) == lesson["query_cells"] == expected_cells

    demos = [{key: copy.deepcopy(capture["pairs"][pair_id][key]) for key in ("input", "output")}
             for pair_id in lesson["demo_ids"]]
    query_pair = {key: copy.deepcopy(query[key]) for key in ("input", "output")}
    reasons = GEN.lesson_identifiable(demos, query_pair)
    assert any(capture["rival_name"] in reason for reason in reasons), reasons
