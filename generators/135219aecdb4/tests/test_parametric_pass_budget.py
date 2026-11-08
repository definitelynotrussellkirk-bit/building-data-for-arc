"""Contract tests for the task-local synchronous-pass budget prototype."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import sys

import pytest
from reviewer_support import canonical_path, find_root, load_selected_generator

TASK_ID = "135219aecdb4"
ROOT = find_root(__file__)
PROTOTYPE = (
    ROOT / "generators" / TASK_ID / "workspace" / "parametric" / "prototype.py"
)

THREE_PASS_INPUT = [
    [2, 1, 0, 3],
    [0, 0, 1, 2],
    [1, 3, 2, 4],
    [0, 2, 0, 1],
]
EXPECTED_BY_PASS = {
    1: [
        [2, 1, 4, 3],
        [0, 4, 1, 2],
        [1, 3, 2, 4],
        [0, 2, 0, 1],
    ],
    2: [
        [2, 1, 4, 3],
        [3, 4, 1, 2],
        [1, 3, 2, 4],
        [0, 2, 3, 1],
    ],
    3: [
        [2, 1, 4, 3],
        [3, 4, 1, 2],
        [1, 3, 2, 4],
        [4, 2, 3, 1],
    ],
}


def _load_prototype():
    assert PROTOTYPE.is_file(), "parametric pass-budget prototype is missing"
    spec = importlib.util.spec_from_file_location(
        "parametric_pass_budget_135219aecdb4", PROTOTYPE
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_record():
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"missing canonical row {TASK_ID}")


def _all_pairs(episode):
    return [*episode["train"], *episode["test"]]


def test_prototype_declares_bounded_episode_level_pass_count():
    proto = _load_prototype()
    assert proto.TASK_ID == TASK_ID
    assert proto.PARAMETERS == {
        "pass_count": {
            "allowed": (1, 2, 3),
            "default": 3,
            "selected_once_per_episode": True,
        }
    }


def test_default_program_is_exact_canonical_and_variants_change_only_fill_depth():
    proto = _load_prototype()
    canonical = _canonical_record()["program_solution"]
    tail = "(fill (fill (fill g)))"
    assert canonical.count(tail) == 1
    assert proto.racket_program(3, root=ROOT) == canonical
    assert proto.racket_program(2, root=ROOT) == canonical.replace(
        tail, "(fill (fill g))", 1
    )
    assert proto.racket_program(1, root=ROOT) == canonical.replace(tail, "(fill g)", 1)


@pytest.mark.parametrize("pass_count", (1, 2, 3))
def test_python_mirror_matches_hand_derived_three_stage_witness(pass_count):
    proto = _load_prototype()
    assert proto.apply_python(THREE_PASS_INPUT, pass_count) == EXPECTED_BY_PASS[pass_count]


@pytest.mark.parametrize("invalid", [None, True, False, 0, 4, 1.0, "3"])
def test_pass_count_rejects_values_outside_exact_bounded_integers(invalid):
    proto = _load_prototype()
    with pytest.raises(ValueError, match="pass_count"):
        proto.racket_program(invalid, root=ROOT)
    with pytest.raises(ValueError, match="pass_count"):
        proto.apply_python(THREE_PASS_INPUT, invalid)


@pytest.mark.parametrize("field", ["demo_count", "query_count"])
@pytest.mark.parametrize("invalid", [True, 0, 65, 1.5, "4"])
def test_episode_counts_are_strict_independent_authoring_bounds(field, invalid):
    proto = _load_prototype()
    kwargs = {"demo_count": 2, "query_count": 4, field: invalid}
    with pytest.raises(ValueError, match=field):
        proto.generate_episode(17, pass_count=3, root=ROOT, **kwargs)


@pytest.mark.parametrize("pass_count", (1, 2, 3))
def test_each_setting_builds_two_demo_four_unique_query_identifiable_episode(pass_count):
    proto = _load_prototype()
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    episode = proto.generate_episode(
        17,
        pass_count=pass_count,
        demo_count=2,
        query_count=4,
        root=ROOT,
    )
    assert episode["parameter_draw_count"] == 1
    assert episode["parameter"] == {"pass_count": pass_count}
    assert len(episode["train"]) == 2
    assert len(episode["test"]) == 4
    assert episode["program"] == proto.racket_program(pass_count, root=ROOT)

    pairs = _all_pairs(episode)
    encoded_inputs = {
        json.dumps(pair["input"], separators=(",", ":")) for pair in pairs
    }
    assert len(encoded_inputs) == 6
    for pair in pairs:
        assert generator.self_check(pair["input"]) == []
        assert generator.semantic_observables(pair["input"])["passes_to_complete"] == 3
        assert pair["output"] == proto.apply_python(pair["input"], pass_count)

    for alternative in {1, 2, 3} - {pass_count}:
        assert all(
            proto.apply_python(pair["input"], alternative) != pair["output"]
            for pair in episode["train"]
        )
        assert all(
            proto.apply_python(pair["input"], alternative) != pair["output"]
            for pair in episode["test"]
        )



def test_candidate_stream_bounds_actual_generator_draws(monkeypatch):
    """Catch retry ceilings that count only accepted candidates."""
    proto = _load_prototype()

    class NeverThreePass:
        def __init__(self):
            self.draws = 0

        def generate(self, seed, sample_index, **overrides):
            self.draws += 1
            return [[0, 0, 0, 0] for _ in range(4)]

        @staticmethod
        def semantic_observables(grid):
            return {"errors": [], "passes_to_complete": 2}

    fake = NeverThreePass()
    monkeypatch.setattr(
        proto,
        "load_selected_generator",
        lambda task_id, root: (fake, Path("generator.py"), "fake-sha"),
    )

    assert list(proto._candidate_stream(7, root=ROOT, max_draws=5)) == []
    assert fake.draws == 5

def test_seed_selects_one_setting_once_and_replay_is_deterministic():
    proto = _load_prototype()
    first = proto.generate_episode(8, demo_count=3, query_count=4, root=ROOT)
    second = proto.generate_episode(8, demo_count=3, query_count=4, root=ROOT)
    assert first == second
    assert first["parameter_draw_count"] == 1
    assert first["parameter"]["pass_count"] == proto.select_pass_count(8)
    assert all(
        pair["output"]
        == proto.apply_python(pair["input"], first["parameter"]["pass_count"])
        for pair in _all_pairs(first)
    )


def test_public_projection_masks_private_fields_and_ids_ignore_query_answers():
    proto = _load_prototype()
    episode = proto.generate_episode(
        23, pass_count=2, demo_count=2, query_count=4, root=ROOT
    )
    public = proto.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    encoded = json.dumps(public, sort_keys=True)
    for hidden in ("pass_count", "program", "seed", "generator_seed", "sample_index"):
        assert hidden not in encoded

    name = proto.public_filename(episode)
    assert re.fullmatch(r"challenge-[0-9a-f]{64}\.json", name)
    changed_private = deepcopy(episode)
    changed_private["seed"] = 999
    changed_private["parameter"] = {"pass_count": 1}
    changed_private["test"][0]["output"] = [[9]]
    assert proto.public_filename(changed_private) == name

    changed_visible = deepcopy(episode)
    changed_visible["test"][0]["input"][0][0] = (
        changed_visible["test"][0]["input"][0][0] + 1
    ) % 5
    assert proto.public_filename(changed_visible) != name
