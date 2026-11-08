"""Native parametric-family tests for 22304ccc509c."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "22304ccc509c"
HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
ADAPTER = HERE.parent / "workspace" / "parametric" / "adapter.py"


def adapter():
    spec = importlib.util.spec_from_file_location("parametric_22304ccc509c", ADAPTER)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(ADAPTER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge(timeout=10) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True

        def apply(program, grid):
            bridge.define_grid("gravity-policy-test-grid", grid)
            return bridge.eval_text(
                "(" + wrap_rule(program) + " gravity-policy-test-grid)"
            )

        yield apply


def all_pairs(episode):
    return episode["train"] + episode["test"]


def all_inputs(episode):
    return [pair["input"] for pair in all_pairs(episode)]


def test_default_program_is_exact_canonical_authority():
    module = adapter()
    programs = {
        row["program_solution"]
        for line in canonical_path(ROOT).read_text().splitlines()
        if (row := json.loads(line))["task_id"] == TASK_ID
    }
    assert programs == {module.program({"gravity_policy": "down"})}
    assert module.program({"gravity_policy": "edge_directed"}) not in programs


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_inputs_are_setting_neutral_deterministic_distinct_and_rng_local(demos):
    module = adapter()
    random.seed(8675309)
    before = random.getstate()
    fixed = module.generate(17, {"gravity_policy": "down"}, demos, 4)
    directed = module.generate(
        17, {"gravity_policy": "edge_directed"}, demos, 4
    )
    assert all_inputs(fixed) == all_inputs(directed)
    assert fixed == module.generate(17, {"gravity_policy": "down"}, demos, 4)
    assert random.getstate() == before
    assert len(fixed["train"]) == demos
    assert len(fixed["test"]) == 4
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs(fixed)]
    assert len(serialized) == len(set(serialized)) == demos + 4


def test_minimum_demos_teach_policy_and_queries_cover_every_direction():
    module = adapter()
    fixed = module.generate(91, {"gravity_policy": "down"}, 2, 4)
    directed = module.generate(
        91, {"gravity_policy": "edge_directed"}, 2, 4
    )
    demo_directions = [module.observe(pair["input"])["anchor_direction"] for pair in fixed["train"]]
    query_directions = [module.observe(pair["input"])["anchor_direction"] for pair in fixed["test"]]
    assert demo_directions == ["up", "left"]
    assert query_directions == ["right", "down", "up", "left"]
    assert all(
        a["input"] == b["input"]
        for a, b in zip(all_pairs(fixed), all_pairs(directed), strict=True)
    )
    assert fixed["train"][0]["output"] != directed["train"][0]["output"]
    assert fixed["train"][1]["output"] != directed["train"][1]["output"]
    for policy, episode in (("down", fixed), ("edge_directed", directed)):
        for pair in all_pairs(episode):
            assert module.transform(pair["input"], policy) == pair["output"]


def test_last_query_is_substantive_30x30_with_all_boundary_contacts():
    module = adapter()
    episode = module.generate(7, {"gravity_policy": "edge_directed"}, 3, 4)
    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    occupied = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value != 0
    ]
    assert len(occupied) >= 80
    assert {min(row for row, _ in occupied), max(row for row, _ in occupied)} == {0, 29}
    assert {min(col for _, col in occupied), max(col for _, col in occupied)} == {0, 29}
    observed = module.observe(grid)
    assert observed["anchor_direction"] == "left"
    assert observed["anchor_color_count"] == 1
    assert observed["nonzero_count"] == len(occupied)


@pytest.mark.parametrize("policy", ["down", "edge_directed"])
def test_demonstrations_alone_eliminate_declared_shortcuts(policy):
    module = adapter()
    episode = module.generate(123, {"gravity_policy": policy}, 2, 4)
    certificate = module.certificate(
        episode["train"], [pair["input"] for pair in episode["test"]]
    )
    assert certificate["survivors"] == [policy]
    assert certificate["demos"] == 2
    assert certificate["queries"] == 4
    assert certificate["demo_anchor_directions"] == ["up", "left"]
    assert len(certificate["predicted_query_sha256"]) == 4
    assert "sort_then_edge_directed" in certificate["declared_hypotheses"]
    assert "remove_anchor_then_edge_directed" in certificate["declared_hypotheses"]


@pytest.mark.parametrize("policy", ["down", "edge_directed"])
def test_generated_labels_match_protected_racket(policy, racket):
    module = adapter()
    episode = module.generate(5, {"gravity_policy": policy}, 2, 4)
    program = module.program({"gravity_policy": policy})
    for pair in all_pairs(episode):
        assert racket(program, pair["input"]) == pair["output"]


def test_public_projection_hashes_only_visible_bytes_and_masks_queries():
    module = adapter()
    episode = module.generate(42, {"gravity_policy": "edge_directed"}, 2, 4)
    mutated_private = copy.deepcopy(episode)
    mutated_private["program_solution"] = "private-program-changed"
    mutated_private["private"] = {"gravity_policy": "changed", "seed": 999}
    for pair in mutated_private["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(episode) == public_challenge_bytes(mutated_private)
    assert public_challenge_id(episode) == public_challenge_id(mutated_private)
    visible = json.loads(public_challenge_bytes(episode))
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert all(set(pair) == {"input", "output"} for pair in visible["train"])


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"gravity_policy": "down"}, 2, 4),
        (-1, {"gravity_policy": "down"}, 2, 4),
        (0, {"gravity_policy": "wrong"}, 2, 4),
        (0, {"gravity_policy": "down", "extra": 1}, 2, 4),
        (0, {"gravity_policy": "down"}, 1, 4),
        (0, {"gravity_policy": "down"}, 7, 4),
        (0, {"gravity_policy": "down"}, 2, 3),
        (0, {"gravity_policy": "down"}, 2, 5),
        (0, {"gravity_policy": "down"}, 2, True),
    ],
)
def test_invalid_requests_fail_explicitly(seed, settings, demos, queries):
    with pytest.raises(ValueError):
        adapter().generate(seed, settings, demos, queries)


def test_observer_rejects_boolean_duplicate_corner_and_interior_anchors():
    module = adapter()
    grid = module.generate(13, {"gravity_policy": "down"}, 2, 4)["train"][0]["input"]

    boolean = [row[:] for row in grid]
    boolean[1][1] = False
    with pytest.raises(ValueError):
        module.observe(boolean)

    duplicate = [row[:] for row in grid]
    duplicate[1][1] = 1
    with pytest.raises(ValueError):
        module.observe(duplicate)

    corner = [row[:] for row in grid]
    anchor = module.observe(corner)["anchor"]
    corner[anchor[0]][anchor[1]] = 0
    corner[0][0] = 1
    with pytest.raises(ValueError):
        module.observe(corner)

    interior = [row[:] for row in grid]
    interior[0][module.observe(interior)["anchor"][1]] = 0
    interior[2][2] = 1
    with pytest.raises(ValueError):
        module.observe(interior)


def test_wrong_intermediate_changes_the_final_output():
    module = adapter()
    pair = module.generate(314, {"gravity_policy": "edge_directed"}, 2, 4)["test"][2]
    assert module.observe(pair["input"])["anchor_direction"] == "up"
    assert module.transform_with_direction(pair["input"], "up") == pair["output"]
    assert module.transform_with_direction(pair["input"], "down") != pair["output"]
