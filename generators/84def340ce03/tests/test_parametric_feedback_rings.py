"""Focused regressions for the proposed feedback-routed ring family."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

from arcpuzzles.catalog import Catalog
from reviewer_support import find_root


TASK_ID = "84def340ce03"
REPO = find_root(__file__)
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
PROTOTYPE_PATH = HOME / "prototype.py"


def _load_prototype():
    assert PROTOTYPE_PATH.is_file(), "prototype.py must exist"
    spec = importlib.util.spec_from_file_location("feedback_ring_prototype", PROTOTYPE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    catalog = Catalog(REPO)
    row = catalog.describe(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in catalog._variants()[row["rule_task_id"]]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def test_direct_program_matches_selected_canonical_bytes():
    prototype = _load_prototype()
    assert prototype.program_for("direct") == _canonical_program()


def test_feedback_min_uses_rendered_prior_ring_to_route_next_tile():
    prototype = _load_prototype()
    grid = [
        [3, 0, 4, 5, 1, 2],
        [2, 1, 6, 0, 3, 4],
    ]
    assert prototype.feedback_trace(grid) == [1, 2]
    assert prototype.render(grid, "feedback_min") == [
        [4, 4, 4, 3, 3, 3],
        [4, 6, 6, 4, 4, 3],
        [4, 6, 3, 0, 4, 3],
        [2, 0, 2, 1, 5, 1],
        [2, 0, 0, 5, 5, 1],
        [2, 2, 2, 1, 1, 1],
    ]
    assert prototype.render(grid, "direct") != prototype.render(grid, "feedback_min")


def _inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_episode_inputs_are_setting_neutral_and_query_prefix_is_demo_count_independent():
    prototype = _load_prototype()
    direct_two = prototype.generate_episode(17, "direct", demos=2, queries=4)
    feedback_two = prototype.generate_episode(17, "feedback_min", demos=2, queries=4)
    direct_six = prototype.generate_episode(17, "direct", demos=6, queries=4)

    assert [pair["input"] for pair in direct_two["train"]] == [
        pair["input"] for pair in feedback_two["train"]
    ]
    assert [pair["input"] for pair in direct_two["test"]] == [
        pair["input"] for pair in feedback_two["test"]
    ]
    assert [pair["input"] for pair in direct_two["train"]] == [
        pair["input"] for pair in direct_six["train"][:2]
    ]
    assert [pair["input"] for pair in direct_two["test"]] == [
        pair["input"] for pair in direct_six["test"]
    ]
    assert len(direct_two["train"]) == 2
    assert len(direct_six["train"]) == 6
    assert len(direct_two["test"]) == 4
    assert len({repr(grid) for grid in _inputs(direct_six)}) == 10


def test_four_queries_are_distinct_substantive_30_by_30_stress_cases():
    prototype = _load_prototype()
    episode = prototype.generate_episode(23, "feedback_min", demos=3, queries=4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(6, 10), (10, 6), (2, 30), (30, 2)]
    for pair in episode["test"]:
        assert len(pair["output"]) == 30
        assert len(pair["output"][0]) == 30
        assert len({cell for row in pair["input"] for cell in row}) == 10
        assert len({cell for row in pair["output"] for cell in row}) == 10
        tiles = prototype._tiles(pair["input"])
        assert any(len(set(tile)) == 1 for tile in tiles), "stress input needs a uniform distractor tile"
        assert len(set(tiles)) < len(tiles), "stress input needs a repeated heterogeneous tile"
        assert pair["output"] == prototype.render(pair["input"], "feedback_min")


@pytest.mark.parametrize("seed", [0, 17, 23])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_visible_demos_isolate_setting_and_eliminate_plausible_feedback_shortcuts(seed, demos):
    prototype = _load_prototype()
    candidates = {
        "direct": lambda grid: prototype.render(grid, "direct"),
        "feedback_min": lambda grid: prototype.render(grid, "feedback_min"),
        **prototype.RIVALS,
    }
    for routing in ("direct", "feedback_min"):
        episode = prototype.generate_episode(seed, routing, demos=demos, queries=4)
        survivors = [
            name
            for name, candidate in candidates.items()
            if all(candidate(pair["input"]) == pair["output"] for pair in episode["train"])
        ]
        assert survivors == [routing]
        assert any(
            candidate(pair["input"]) != pair["output"]
            for candidate in candidates.values()
            for pair in episode["test"]
        )


@pytest.mark.parametrize(
    "grid",
    [
        [],
        [[1]],
        [[1, 2], [3]],
        [[1, 2, 3], [4, 5, 6]],
        [[1, 2], [3, True]],
        [[0] * 8 for _ in range(8)],
    ],
)
def test_render_rejects_inputs_outside_the_canonical_bounded_grammar(grid):
    prototype = _load_prototype()
    with pytest.raises(ValueError, match="grid"):
        prototype.render(grid, "feedback_min")


def _load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "adapter.py must exist"
    spec = importlib.util.spec_from_file_location("feedback_ring_adapter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_adapter_enforces_exact_setting_and_episode_count_contract():
    adapter = _load_adapter()
    prototype = _load_prototype()

    assert adapter.program({"routing": "direct"}) == _canonical_program()
    assert adapter.program({"routing": "feedback_min"}) == prototype.program_for("feedback_min")
    for invalid in (None, {}, {"routing": "unknown"}, {"routing": True},
                    {"routing": "direct", "extra": 0}):
        with pytest.raises(ValueError, match="settings|routing"):
            adapter.program(invalid)

    for demos in (2, 6):
        episode = adapter.generate(17, {"routing": "feedback_min"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        assert episode["program_solution"] == adapter.program({"routing": "feedback_min"})
    for demos, queries in ((1, 4), (7, 4), (True, 4), (3, 3), (3, 5), (3, False)):
        with pytest.raises(ValueError, match="demos|queries"):
            adapter.generate(17, {"routing": "direct"}, demos, queries)


def test_promotion_contract_declares_finite_two_setting_family_and_resources():
    import json

    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"routing": ["direct", "feedback_min"]},
        "default": {"routing": "direct"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/rules/direct.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/feedback_min.rkt",
        ],
    }


def test_public_projection_hides_settings_program_and_query_answers_and_reveals_one_query_at_a_time():
    import copy
    import json
    from reviewer_support import public_challenge_bytes

    adapter = _load_adapter()
    episode = adapter.generate(23, {"routing": "feedback_min"}, 3, 4)
    episode["settings"] = {"routing": "feedback_min"}
    baseline = public_challenge_bytes(episode)

    mutated = copy.deepcopy(episode)
    mutated["settings"] = {"routing": "direct"}
    mutated["program_solution"] = "PRIVATE PROGRAM CHANGED"
    for pair in mutated["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(mutated) == baseline

    public = json.loads(baseline)
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert len(public["test"]) == 4

    first_turn = {
        "train": episode["train"],
        "test": [episode["test"][0]],
        "settings": episode["settings"],
        "program_solution": episode["program_solution"],
    }
    first_public = json.loads(public_challenge_bytes(first_turn))
    assert first_public["train"] == public["train"]
    assert first_public["test"] == public["test"][:1]


def _load_audit():
    path = HOME / "audit.py"
    assert path.is_file(), "audit.py must exist"
    spec = importlib.util.spec_from_file_location("feedback_ring_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_protected_audit_replays_declared_settings_and_eliminates_named_shortcuts():
    audit = _load_audit()
    report = audit.build_report(seeds=(0,), demo_counts=(2,))

    assert report["schema"] == "arcpuzzles-parametric-self-audit-v1"
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert len(report["checks"]) == 2
    for check in report["checks"]:
        routing = check["settings"]["routing"]
        assert check["declared_survivors"] == [routing]
        assert check["bounded_survivors"] == [routing]
        assert check["python_selected_matches_racket"] is True
        assert check["racket_label_count"] == 6
        assert set(check["eliminated_candidates"]) == {
            "direct", "feedback_min", "source_min_not_rendered",
            "global_first_offset", "one_step_then_direct", "current_tile_offset",
        } - {routing}
        assert all(row["first_demo_disagreement"] in (0, 1)
                   for row in check["eliminated_candidates"].values())
        assert all(row["first_query_disagreement"] in (0, 1, 2, 3)
                   for row in check["eliminated_candidates"].values())
    assert report["minimal_counterexample"]["selected"] == "feedback_min"
    assert report["minimal_counterexample"]["rival"] == "source_min_not_rendered"
    assert report["minimal_counterexample"]["expected_racket"] != report["minimal_counterexample"]["rival_output"]


def _load_witness_builder():
    path = HOME / "build_witness.py"
    assert path.is_file(), "build_witness.py must exist"
    spec = importlib.util.spec_from_file_location("feedback_ring_witness_builder", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_witness_builder_binds_qualified_feedback_program_and_survives_owner_replay():
    import hashlib
    import json
    from arcpuzzles.review_sequential_replay import replay_witness

    prototype = _load_prototype()
    builder = _load_witness_builder()
    feedback_program = prototype.program_for("feedback_min")
    key = json.dumps({"routing": "feedback_min"}, sort_keys=True, separators=(",", ":"))
    qualification = {
        "schema": "arcpuzzles-parametric-qualification-v1",
        "status": "qualified",
        "task_id": TASK_ID,
        "source_binding": {
            "task_id": TASK_ID,
            "files": [{"path": "fixture", "sha256": "0" * 64}],
        },
        "programs": {key: hashlib.sha256(feedback_program.encode()).hexdigest()},
    }

    witness = builder.build_witness(qualification, seed=17, query_index=0)
    assert witness["schema"] == "arcpuzzles-sequential-dependency-witness-v1"
    assert witness["source_binding"] == qualification["source_binding"]
    assert witness["racket"] == {"backend": "racket", "protected": True}
    assert len(witness["cases"]) == 1
    case = witness["cases"][0]
    assert case["settings"] == {"routing": "feedback_min"}
    assert case["ablation"] == "skip_a"
    assert hashlib.sha256(case["program"].encode()).hexdigest() == qualification["programs"][key]
    assert case["output"] != case["counterfactual_output"]
    assert case["intermediate_value"] == {
        "prior_ring_minimum_quadrant_indices": prototype.feedback_trace(case["input"])
    }

    replay = replay_witness(REPO, witness)
    assert replay["status"] == "owner_replayed"
    assert replay["evaluations"] == 2
