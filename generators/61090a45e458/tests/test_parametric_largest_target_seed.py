"""Native parametric contract for the largest-target seed relay."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles import Catalog
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "61090a45e458"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str, filename: str):
    path = PARAMETRIC / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


FAMILY = _load("_arc_61090a45e458_parametric_test", "prototype.py")
ADAPTER = _load("_arc_61090a45e458_adapter_test", "adapter.py")


def _frozen(grid):
    return tuple(tuple(row) for row in grid)


def test_exact_canonical_default_and_distinct_alternative():
    programs = {
        row["program_solution"]
        for row in Catalog(ROOT).get(TASK_ID)["variants"]
        if isinstance(row.get("program_solution"), str)
    }
    assert programs == {FAMILY.program({"recolor_policy": "local_seed"})}
    assert ADAPTER.program({"recolor_policy": "local_seed"}) in programs
    assert FAMILY.program({"recolor_policy": "largest_target_seed"}) not in programs
    assert FAMILY.program({"recolor_policy": "largest_target_seed"}) == ADAPTER.program(
        {"recolor_policy": "largest_target_seed"}
    )


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"recolor_policy": "bad"}, {"recolor_policy": 1},
     {"recolor_policy": "local_seed", "extra": 1}],
)
def test_rejects_invalid_settings(settings):
    with pytest.raises(ValueError):
        FAMILY.program(settings)


@pytest.mark.parametrize("seed", [True, -1, 2**63, 1.0, "1"])
def test_rejects_invalid_seed(seed):
    with pytest.raises(ValueError):
        FAMILY.generate(seed, {"recolor_policy": "local_seed"})


@pytest.mark.parametrize(
    "demos,queries",
    [(1, 4), (7, 4), (3, 0), (3, 5), (True, 1), (3.0, 1), (3, False)],
)
def test_rejects_invalid_counts(demos, queries):
    with pytest.raises(ValueError):
        FAMILY.generate(0, {"recolor_policy": "local_seed"}, demos=demos, queries=queries)


def test_matched_inputs_prefix_stability_determinism_and_copy_isolation():
    local = FAMILY.generate(17, {"recolor_policy": "local_seed"}, demos=6, queries=4)
    short = FAMILY.generate(17, {"recolor_policy": "local_seed"}, demos=2, queries=1)
    global_rule = FAMILY.generate(
        17, {"recolor_policy": "largest_target_seed"}, demos=6, queries=4
    )
    assert short["train"] == local["train"][:2]
    assert short["test"] == local["test"][:1]
    for split in ("train", "test"):
        assert [pair["input"] for pair in local[split]] == [
            pair["input"] for pair in global_rule[split]
        ]
    assert local == FAMILY.generate(17, {"recolor_policy": "local_seed"}, demos=6, queries=4)
    short["train"][0]["input"][0][0] = 99
    assert FAMILY.generate(17, {"recolor_policy": "local_seed"}, demos=2, queries=1) != short


def test_two_demo_prefix_uniquely_teaches_each_setting_against_declared_rivals():
    for seed in range(12):
        for policy in FAMILY.RECOLOR_POLICIES:
            episode = FAMILY.generate(seed, {"recolor_policy": policy}, demos=2, queries=4)
            proof = FAMILY.teaching_certificate(
                episode["train"], [pair["input"] for pair in episode["test"]]
            )
            assert proof["survivors"] == [policy]
            assert proof["scope"].startswith("Finite declared rivals")


def test_every_scene_has_three_frames_unique_largest_target_and_valid_outputs():
    for seed in range(10):
        episode = FAMILY.generate(
            seed, {"recolor_policy": "largest_target_seed"}, demos=6, queries=4
        )
        all_inputs = []
        for split in ("train", "test"):
            for pair in episode[split]:
                analysis = FAMILY.analyze(pair["input"])
                assert len(analysis["frames"]) == 3
                sizes = [frame["target_size"] for frame in analysis["frames"]]
                assert sizes.count(max(sizes)) == 1
                assert pair["output"] == FAMILY.predict(pair["input"], "largest_target_seed")
                assert all(type(cell) is int and 0 <= cell <= 9 for row in pair["output"] for cell in row)
                all_inputs.append(_frozen(pair["input"]))
        assert len(all_inputs) == len(set(all_inputs)) == 10


def test_global_rule_consumes_the_selected_frame_intermediate():
    episode = FAMILY.generate(
        0, {"recolor_policy": "largest_target_seed"}, demos=3, queries=4
    )
    for pair in episode["test"]:
        intermediate = FAMILY.largest_target_intermediate(pair["input"])
        assert intermediate["target_size"] == max(
            frame["target_size"] for frame in FAMILY.analyze(pair["input"])["frames"]
        )
        correct = FAMILY.predict(pair["input"], "largest_target_seed")
        wrong = FAMILY.predict(pair["input"], "smallest_target_seed")
        assert correct != wrong
        assert sum(a != b for ra, rb in zip(correct, wrong) for a, b in zip(ra, rb)) > 0


def test_fourth_query_is_substantive_30x30_boundary_stress():
    episode = FAMILY.generate(
        5, {"recolor_policy": "largest_target_seed"}, demos=3, queries=4
    )
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    colored = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(colored) >= 240
    assert len({r for r, _ in colored}) >= 24
    assert len({c for _, c in colored}) >= 24
    assert any(r in {0, 29} or c in {0, 29} for r, c in colored)


def test_public_turn_hashes_only_visible_current_query():
    episode = FAMILY.generate(
        11, {"recolor_policy": "largest_target_seed"}, demos=3, queries=4
    )
    challenge = FAMILY.public_turn(episode, 0)
    assert set(challenge) == {"train", "test"}
    assert len(challenge["test"]) == 1 and set(challenge["test"][0]) == {"input"}
    assert b"program_solution" not in public_challenge_bytes(challenge)
    assert len(public_challenge_id(challenge)) == 64

    changed_private = deepcopy(episode)
    changed_private["program_solution"] = "private replacement"
    assert FAMILY.public_turn(changed_private, 0) == challenge
    assert public_challenge_id(FAMILY.public_turn(changed_private, 0)) == public_challenge_id(challenge)


def test_adapter_returns_only_native_contract_fields():
    episode = ADAPTER.generate(
        17, {"recolor_policy": "largest_target_seed"}, demos=3, queries=4
    )
    assert set(episode) == {"train", "test", "program_solution"}
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == ADAPTER.program(
        {"recolor_policy": "largest_target_seed"}
    )


def test_program_files_have_stable_nonempty_hashes():
    hashes = {
        name: hashlib.sha256((PARAMETRIC / name).read_bytes()).hexdigest()
        for name in (
            "canonical.rkt",
            "largest_target_seed.rkt",
            "smallest_target_seed_counterfactual.rkt",
        )
    }
    assert len(set(hashes.values())) == 3
    assert all(len(value) == 64 for value in hashes.values())


def test_protected_racket_programs_match_claimed_labels():
    from arcpuzzles.parametric_worker import _local_imports, _real_evaluator

    runtime = ROOT / "shared" / "runtime"
    with _local_imports(runtime, PARAMETRIC):
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            assert identity["backend"] == "racket" and identity["protected"] is True
            for policy in FAMILY.RECOLOR_POLICIES:
                episode = FAMILY.generate(0, {"recolor_policy": policy}, demos=3, queries=4)
                for pair in (
                    episode["train"][0],
                    episode["train"][1],
                    episode["test"][0],
                    episode["test"][3],
                ):
                    assert apply(episode["program_solution"], pair["input"]) == pair["output"]
            counterfactual = (PARAMETRIC / "smallest_target_seed_counterfactual.rkt").read_text()
            pair = FAMILY.generate(
                0, {"recolor_policy": "largest_target_seed"}, demos=3, queries=4
            )["test"][0]
            assert apply(counterfactual, pair["input"]) == FAMILY.predict(
                pair["input"], "smallest_target_seed"
            )
        finally:
            bridge.close()
