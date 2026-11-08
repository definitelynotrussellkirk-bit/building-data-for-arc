"""Native parametric-family regressions for 4de2bae05c7d."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_path, find_root


TASK = "4de2bae05c7d"
ROOT = find_root(__file__)
HOME = Path(__file__).resolve().parents[1]
PROTO = HOME / "workspace/parametric"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAMILY = _load("parametric_family_4de2bae05c7d", PROTO / "family.py")
ADAPTER = _load("parametric_adapter_4de2bae05c7d", PROTO / "adapter.py")
PROBE = _load("parametric_probe_4de2bae05c7d", PROTO / "adversarial_probe.py")


def _canonical_program() -> str:
    rows = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    assert len(rows) == 1
    return rows[0]["program_solution"]


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def test_contract_and_default_program_preserve_exact_canonical_bytes():
    contract = json.loads((PROTO / "promotion.json").read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {
        "postprocess": ["canonical", "largest", "smallest"]
    }
    assert contract["default"] == {"postprocess": "canonical"}
    assert contract["limits"] == {"demos": [3, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3
    assert ADAPTER.program({"postprocess": "canonical"}) == _canonical_program()
    assert (PROTO / "canonical.rkt").read_text() == _canonical_program()


@pytest.mark.parametrize("demos", [3, 4, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_counts_are_independent_inputs_are_distinct_and_settings_are_matched(demos, queries):
    episodes = {
        mode: ADAPTER.generate(37, {"postprocess": mode}, demos, queries)
        for mode in FAMILY.MODES
    }
    reference_inputs = _inputs(episodes["canonical"])
    assert len(reference_inputs) == demos + queries
    assert len({FAMILY.grid_key(grid) for grid in reference_inputs}) == demos + queries
    for mode, episode in episodes.items():
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        assert episode["program_solution"] == ADAPTER.program({"postprocess": mode})
        assert _inputs(episode) == reference_inputs
        for pair in episode["train"] + episode["test"]:
            assert FAMILY.validate_scene(pair["input"]) == []
            assert pair["output"] == FAMILY.apply_mode(pair["input"], mode)


def test_minimum_lesson_covers_all_target_orientations_and_refutes_declared_rivals():
    for seed in range(12):
        episode = ADAPTER.generate(seed, {"postprocess": "largest"}, 3, 4)
        demos = episode["train"]
        orientations = set().union(
            *(set(FAMILY.scene_facts(pair["input"])["target_orientations"]) for pair in demos)
        )
        assert orientations == set(FAMILY.L_ORIENTATIONS)
        for name, rival in FAMILY.RIVALS["largest"].items():
            assert any(rival(pair["input"]) != pair["output"] for pair in demos), name
        for query in episode["test"]:
            assert FAMILY.lesson_identifiable(demos, query["input"], "largest") == []


@pytest.mark.parametrize("mode", ["largest", "smallest"])
def test_minimum_lessons_refute_fixed_position_component_shortcuts(mode):
    positional = {
        "select topmost post-step blue component",
        "select bottommost post-step blue component",
        "select leftmost post-step blue component",
        "select rightmost post-step blue component",
    }
    assert positional <= set(FAMILY.RIVALS[mode])
    for seed in range(24):
        episode = ADAPTER.generate(seed, {"postprocess": mode}, 3, 4)
        for name in positional:
            rival = FAMILY.RIVALS[mode][name]
            assert any(
                rival(pair["input"]) != pair["output"]
                for pair in episode["train"]
            ), (mode, seed, name)


def test_post_recolor_ranks_flip_relative_to_original_and_require_full_component_scope():
    for seed in range(16):
        episode = ADAPTER.generate(seed, {"postprocess": "largest"}, 3, 4)
        for pair in episode["train"] + episode["test"]:
            grid = pair["input"]
            facts = FAMILY.scene_facts(grid)
            assert facts["original_largest_blue"] != facts["post_largest_blue"]
            assert facts["original_smallest_blue"] != facts["post_smallest_blue"]
            assert facts["post_largest_blue"] != facts["post_largest_bbox_blue"]
            assert facts["post_largest_blue"] != facts["post_largest_blue_8"]
            assert FAMILY.rank_original_then_recolor(grid, "largest") != FAMILY.apply_mode(
                grid, "largest"
            )
            assert FAMILY.rank_original_then_recolor(grid, "smallest") != FAMILY.apply_mode(
                grid, "smallest"
            )
            assert FAMILY.recolor_only_new_targets(grid, "largest") != FAMILY.apply_mode(
                grid, "largest"
            )


def test_standard_profile_is_observably_interior():
    for seed in range(24):
        grid = FAMILY._generate_scene(seed, "standard", 0, "demo")
        facts = FAMILY.scene_facts(grid)
        assert facts["profile"] == "standard"
        assert not facts["touches_boundary"]


def test_boundary_thin_and_substantive_30x30_queries_are_present_but_privately_shuffled():
    first_roles = set()
    for seed in range(20):
        episode = ADAPTER.generate(seed, {"postprocess": "smallest"}, 3, 4)
        query_inputs = [pair["input"] for pair in episode["test"]]
        facts = [FAMILY.scene_facts(grid) for grid in query_inputs]
        assert any(row["height"] == row["width"] == 30 for row in facts)
        assert any(row["height"] != row["width"] for row in facts)
        assert any(row["touches_boundary"] for row in facts)
        dense = next(row for row in facts if row["height"] == row["width"] == 30)
        assert dense["nonzero"] >= 70
        assert dense["row_span"] >= 24 and dense["col_span"] >= 24
        first_roles.add(facts[0]["profile"])
    assert len(first_roles) >= 3


def test_determinism_fresh_returns_and_global_rng_purity():
    before = random.getstate()
    first = ADAPTER.generate(987654, {"postprocess": "smallest"}, 5, 4)
    assert random.getstate() == before
    second = ADAPTER.generate(987654, {"postprocess": "smallest"}, 5, 4)
    assert first == second
    assert first is not second
    assert first["train"][0]["input"] is not second["train"][0]["input"]
    first["train"][0]["input"][0][0] = 9
    assert ADAPTER.generate(987654, {"postprocess": "smallest"}, 5, 4) == second


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({}, 3, 4),
        ({"postprocess": "other"}, 3, 4),
        ({"postprocess": True}, 3, 4),
        ({"postprocess": "canonical", "extra": 1}, 3, 4),
        ({"postprocess": "canonical"}, 2, 4),
        ({"postprocess": "canonical"}, 7, 4),
        ({"postprocess": "canonical"}, 3, 0),
        ({"postprocess": "canonical"}, 3, 5),
    ],
)
def test_adapter_rejects_invalid_settings_and_counts(settings, demos, queries):
    with pytest.raises(ValueError):
        ADAPTER.generate(0, settings, demos, queries)


def test_dimension_probe_counts_setting_matched_inputs_once():
    values = {}
    examples = {}
    for _ in FAMILY.MODES:
        PROBE.record_dimension_observation(
            values, examples, "standard:21x20", "same-grid", 15
        )
    assert values == {"standard:21x20": {15}}
    assert examples == {"standard:21x20": {"same-grid"}}


def test_dimension_crossing_ignores_sparse_coincidences_but_rejects_frequent_confounding():
    sparse = {"boundary:18x18": {15}}
    assert PROBE.validate_dimension_crossing(sparse, {"boundary:18x18": 3}) == []

    with pytest.raises(AssertionError, match="boundary:18x18"):
        PROBE.validate_dimension_crossing(sparse, {"boundary:18x18": 12})


def test_seed12_canonical_lesson_refutes_yellow_size_three_shortcut():
    episode = ADAPTER.generate(12, {"postprocess": "canonical"}, 3, 4)
    rival = FAMILY.RIVALS["canonical"]["recolor every yellow size-three component"]
    assert any(
        rival(pair["input"]) != pair["output"]
        for pair in episode["train"]
    )


def test_minimum_lessons_refute_every_declared_rival_for_every_setting():
    for mode in FAMILY.MODES:
        for seed in range(12):
            episode = ADAPTER.generate(seed, {"postprocess": mode}, 3, 4)
            for name, rival in FAMILY.RIVALS[mode].items():
                assert any(
                    rival(pair["input"]) != pair["output"]
                    for pair in episode["train"]
                ), (mode, seed, name)


def test_lesson_certificate_rejects_duplicates_forged_outputs_and_bad_numeric_types():
    episode = ADAPTER.generate(123, {"postprocess": "largest"}, 3, 4)
    demos = episode["train"]
    query = episode["test"][0]["input"]

    duplicate_demo = [demos[0], demos[0], demos[2]]
    assert any("duplicate" in reason for reason in FAMILY.lesson_identifiable(
        duplicate_demo, query, "largest"
    ))

    duplicate_query = demos[0]["input"]
    assert any("duplicate" in reason for reason in FAMILY.lesson_identifiable(
        demos, duplicate_query, "largest"
    ))

    forged = json.loads(json.dumps(demos))
    forged[0]["output"][0][0] = (forged[0]["output"][0][0] + 1) % 10
    assert any("mislabeled" in reason for reason in FAMILY.lesson_identifiable(
        forged, query, "largest"
    ))

    malformed = json.loads(json.dumps(query))
    malformed[0][0] = True
    assert any("invalid" in reason for reason in FAMILY.lesson_identifiable(
        demos, malformed, "largest"
    ))
