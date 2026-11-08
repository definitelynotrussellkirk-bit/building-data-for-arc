"""Racket-backed tests for the isolated inset-depth prototype."""
from __future__ import annotations

import importlib.util
import json
import random
from copy import deepcopy
from functools import lru_cache

import pytest

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "dbecc530afd0"


@lru_cache(maxsize=1)
def prototype():
    root = find_root(__file__)
    load_selected_generator(TASK_ID, root=root)
    path = root / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
    assert path.is_file(), "The proposed inset-depth prototype must be runnable."
    spec = importlib.util.spec_from_file_location("dbecc_inset_depth_prototype", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, root


@pytest.fixture(scope="module")
def bridge():
    with RacketBridge() as instance:
        yield instance


# One 7x8 corner rectangle inside a 9x10 canvas. These expected outputs are
# hand-derived: depth 1 paints rows 2..6 / cols 2..7, while depth 2 paints
# rows 3..5 / cols 3..6.
SHARED_INPUT = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 4, 0, 0, 0, 0, 0, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 4, 0, 0, 0, 0, 0, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]
DEPTH_1_OUTPUT = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 4, 0, 0, 0, 0, 0, 0, 4, 0],
    [0, 0, 2, 2, 2, 2, 2, 2, 0, 0],
    [0, 0, 2, 2, 2, 2, 2, 2, 0, 0],
    [0, 0, 2, 2, 2, 2, 2, 2, 0, 0],
    [0, 0, 2, 2, 2, 2, 2, 2, 0, 0],
    [0, 0, 2, 2, 2, 2, 2, 2, 0, 0],
    [0, 4, 0, 0, 0, 0, 0, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]
DEPTH_2_OUTPUT = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 4, 0, 0, 0, 0, 0, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 2, 2, 2, 2, 0, 0, 0],
    [0, 0, 0, 2, 2, 2, 2, 0, 0, 0],
    [0, 0, 0, 2, 2, 2, 2, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 4, 0, 0, 0, 0, 0, 0, 4, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
]


@pytest.mark.parametrize("value", [True, False, 0, 3, 1.0, 2.0, "1", None])
def test_invalid_inset_depth_values_are_rejected(value):
    """Mutation caught: coercing or widening the two-value parameter domain."""
    module, _ = prototype()
    with pytest.raises(ValueError, match="inset_depth"):
        module.validate_setting(value)
    with pytest.raises(ValueError, match="inset_depth"):
        module.program_for_depth(value)


@pytest.mark.parametrize("seed", [True, -1, 1.0, "1", None])
def test_invalid_episode_seeds_are_rejected(seed):
    """Mutation caught: sharing permissive Python indexing/coercion with seed choice."""
    module, _ = prototype()
    with pytest.raises(ValueError, match="seed"):
        module.choose_inset_depth(seed)


@pytest.mark.parametrize(
    ("demo_count", "query_count"),
    [
        (True, 4),
        (3, False),
        (0, 4),
        (3, 0),
        (100, 1),
        (1, 100),
        (8, 8),
    ],
)
def test_invalid_episode_counts_are_rejected(demo_count, query_count):
    """Mutation caught: coercing counts or silently exceeding bounded support."""
    module, _ = prototype()
    with pytest.raises(ValueError, match="count"):
        module.validate_counts(demo_count, query_count)


def test_default_program_is_byte_for_byte_canonical():
    """Mutation caught: reformatting or rewriting the authority at the default setting."""
    module, root = prototype()
    assert module.DEFAULT_INSET_DEPTH == 1
    assert module.program_for_depth(1, root=root) == module.canonical_rule(root=root)


def test_depth_one_reproduces_every_selected_canonical_label(bridge):
    """Mutation caught: changing canonical semantics while introducing the parameter."""
    module, root = prototype()
    pairs = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    assert len(pairs) == 8
    source = module.program_for_depth(1, root=root)
    for pair in pairs:
        assert module.evaluate(bridge, source, pair["input"]) == pair["output"]


def test_both_exact_programs_execute_and_match_hand_checked_shared_witness(bridge):
    """Mutation caught: offsetting the wrong boundary or implementing depth in Python."""
    module, _ = prototype()
    depth_1 = module.evaluate(bridge, module.program_for_depth(1), SHARED_INPUT)
    depth_2 = module.evaluate(bridge, module.program_for_depth(2), SHARED_INPUT)
    assert depth_1 == DEPTH_1_OUTPUT
    assert depth_2 == DEPTH_2_OUTPUT
    assert depth_1 != depth_2


def test_seed_chooses_one_setting_and_all_labels_come_from_that_racket_program(bridge):
    """Mutation caught: varying the setting per pair or retaining a Python label path."""
    module, _ = prototype()
    for seed, expected_depth in ((0, 1), (1, 2)):
        episode = module.generate_episode(
            bridge,
            seed,
            demo_count=3,
            query_count=4,
        )
        assert episode["parameters"] == {"inset_depth": expected_depth}
        assert episode["counts"] == {"demonstrations": 3, "queries": 4}
        assert len(episode["pairs"]) == 7
        program = module.program_for_depth(expected_depth)
        for pair in episode["pairs"]:
            assert pair["output"] == module.evaluate(bridge, program, pair["input"])


def test_episode_inputs_are_repeatable_setting_independent_and_do_not_touch_global_rng(bridge):
    """Mutation caught: coupling input draws to setting choice or global random state."""
    module, _ = prototype()
    random.seed(987654321)
    before = random.getstate()
    depth_1 = module.generate_episode(bridge, 71, inset_depth=1)
    after = random.getstate()
    replay = module.generate_episode(bridge, 71, inset_depth=1)
    depth_2 = module.generate_episode(bridge, 71, inset_depth=2)
    assert before == after
    assert depth_1 == replay
    assert [p["input"] for p in depth_1["pairs"]] == [p["input"] for p in depth_2["pairs"]]
    assert all(a["output"] != b["output"] for a, b in zip(depth_1["pairs"], depth_2["pairs"]))


def test_generated_inputs_stay_in_the_shared_production_domain(bridge):
    """Mutation caught: proving distinction only on malformed or too-small scenes."""
    module, root = prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    for seed in range(6):
        episode = module.generate_episode(bridge, seed)
        for pair in episode["pairs"]:
            grid = pair["input"]
            assert generator.self_check(grid) == []
            assert 8 <= len(grid) <= 18
            assert 8 <= len(grid[0]) <= 18


def test_shared_demonstrations_identify_four_distinct_queries_without_query_answers(bridge):
    """Mutation caught: using rotations instead of four simultaneous query labels."""
    module, _ = prototype()
    for seed in (0, 1, 19):
        episode = module.generate_episode(
            bridge,
            seed,
            demo_count=2,
            query_count=4,
        )
        inputs = [json.dumps(pair["input"], separators=(",", ":")) for pair in episode["pairs"]]
        assert len(inputs) == len(set(inputs)) == 6

        scores = module.analyze_episode(bridge, episode)
        assert scores["status"] == "no_ambiguity_found"
        assert scores["demonstration_indices"] == [0, 1]
        assert scores["query_indices"] == [2, 3, 4, 5]
        assert [row["query_index"] for row in scores["query_checks"]] == [2, 3, 4, 5]
        for score in scores["query_checks"]:
            assert score["status"] == "no_ambiguity_found"
            assert len(score["rivals"]) == 1
            rival = score["rivals"][0]
            assert not rival["fits_demonstrations"]
            assert rival["query_differs"]
            assert rival["refuting_demonstration_indices"] == [0, 1]


def test_public_projection_contains_only_demonstrations_and_query_input(bridge):
    """Mutation caught: leaking hidden parameter/program/answer metadata publicly."""
    module, _ = prototype()
    episode = module.generate_episode(bridge, 0, demo_count=3, query_count=4)
    public = module.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert len(public["train"]) == 3
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    serialized = json.dumps(public, sort_keys=True)
    for forbidden in ("seed", "inset_depth", "racket", "sha256", "parameters", "rival"):
        assert forbidden not in serialized
    public["test"][0]["input"][0][0] = 9
    assert episode["pairs"][3]["input"][0][0] != 9


def test_public_identifier_depends_only_on_visible_bytes(bridge):
    """Mutation caught: deriving public identity from seed, setting, or query answers."""
    module, _ = prototype()
    episode = module.generate_episode(bridge, 0, demo_count=3, query_count=4)
    expected = public_challenge_id(module.public_challenge(episode))

    private_only = deepcopy(episode)
    private_only["seed"] = 999
    private_only["parameters"] = {"inset_depth": 2}
    private_only["racket_program"] = "private replacement"
    for pair in private_only["pairs"][3:]:
        pair["output"] = [[9]]
    assert public_challenge_id(module.public_challenge(private_only)) == expected

    visible_change = deepcopy(episode)
    old = visible_change["pairs"][3]["input"][0][0]
    visible_change["pairs"][3]["input"][0][0] = (old + 1) % 10
    assert public_challenge_id(module.public_challenge(visible_change)) != expected


def test_evidence_build_records_both_settings_and_separates_public_private_data(bridge, tmp_path):
    """Mutation caught: retaining only one setting or leaking private episode state."""
    module, _ = prototype()
    out = tmp_path / "evidence"
    report = module.build_evidence(
        out,
        seed=0,
        demo_count=3,
        query_count=4,
        bridge=bridge,
    )
    assert report["status"] == "no_ambiguity_found"
    assert report["counts"] == {
        "canonical_labels_checked": 8,
        "canonical_labels_passed": 8,
        "episodes": 2,
        "demonstrations": 6,
        "queries": 8,
        "episode_labels": 14,
        "counterfactual_labels": 14,
        "query_checks": 8,
        "query_ambiguities": 0,
        "unique_episode_inputs": 14,
        "unique_public_challenges": 2,
    }
    assert {row["parameters"]["inset_depth"] for row in report["episodes"]} == {1, 2}
    assert [row["public_id"] for row in report["episodes"]] == sorted(
        row["public_id"] for row in report["episodes"]
    )
    assert (out / "private/rules/inset-depth-1.rkt").read_text() == module.program_for_depth(1)
    assert (out / "private/rules/inset-depth-2.rkt").read_text() == module.program_for_depth(2)
    for row in report["episodes"]:
        public_path = out / row["public_path"]
        public = json.loads(public_path.read_bytes())
        private = json.loads((out / row["private_path"]).read_text())
        assert public_path.name == f"challenge-{row['public_id']}.json"
        assert "episode-" not in row["public_path"]
        assert public_path.read_bytes() == public_challenge_bytes(public)
        assert set(public) == {"train", "test"}
        assert len(public["train"]) == 3
        assert len(public["test"]) == 4
        assert all(set(pair) == {"input"} for pair in public["test"])
        assert "parameters" not in public
        assert private["parameters"] == row["parameters"]
        assert private["counts"] == {"demonstrations": 3, "queries": 4}
        assert all("output" in pair for pair in private["pairs"][3:])
        assert len(row["query_checks"]) == 4
        assert all(check["status"] == "no_ambiguity_found" for check in row["query_checks"])
    assert report["setting_witness"]["outputs"]["1"] != report["setting_witness"]["outputs"]["2"]


def test_evidence_build_refuses_to_overwrite_existing_directory(bridge, tmp_path):
    """Mutation caught: silently replacing retained review evidence."""
    module, _ = prototype()
    with pytest.raises(FileExistsError):
        module.build_evidence(tmp_path, seed=0, bridge=bridge)


def test_evidence_build_rejects_duplicate_visible_challenges(bridge, tmp_path, monkeypatch):
    """Mutation caught: overwriting two episodes that have identical public bytes."""
    module, _ = prototype()
    duplicate = module.generate_episode(
        bridge,
        0,
        demo_count=3,
        query_count=4,
    )

    def repeated_episode(*args, **kwargs):
        return deepcopy(duplicate)

    monkeypatch.setattr(module, "generate_episode", repeated_episode)
    with pytest.raises(RuntimeError, match="duplicate public challenge"):
        module.build_evidence(
            tmp_path / "duplicate-evidence",
            seed=0,
            demo_count=3,
            query_count=4,
            bridge=bridge,
        )
