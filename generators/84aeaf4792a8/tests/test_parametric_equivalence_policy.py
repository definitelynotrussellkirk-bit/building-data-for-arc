"""Focused checks for the native rotation-vs-dihedral relation-matrix family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "84aeaf4792a8"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"


def load(filename: str):
    path = PARAMETRIC / filename
    assert path.is_file(), f"missing required parametric source: {path}"
    name = f"_{TASK_ID}_{filename.replace('.', '_')}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task row not found")


def all_pairs(episode: dict) -> list[dict]:
    return episode["train"] + episode["test"]


def all_inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for pair in all_pairs(episode)]


def test_contract_and_programs_preserve_the_exact_canonical_default():
    prototype = load("prototype.py")
    adapter = load("adapter.py")
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    expected = {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"equivalence_policy": ["rotation", "dihedral"]},
        "default": {"equivalence_policy": "rotation"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/dihedral.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rivals.py",
            f"generators/{TASK_ID}/workspace/parametric/audit.py",
            f"generators/{TASK_ID}/workspace/parametric/counterfactual_bbox.rkt",
        ],
    }
    assert contract == expected
    canonical = canonical_program()
    assert prototype.program({"equivalence_policy": "rotation"}) == canonical
    assert adapter.program({"equivalence_policy": "rotation"}) == canonical
    alternate = prototype.program({"equivalence_policy": "dihedral"})
    assert alternate == adapter.program({"equivalence_policy": "dihedral"})
    assert alternate != canonical
    assert hashlib.sha256((PARAMETRIC / "canonical.rkt").read_bytes()).hexdigest() == hashlib.sha256(canonical.encode()).hexdigest()


@pytest.mark.parametrize("seed", [0, 1, 17, 2**31 - 1])
@pytest.mark.parametrize("demos", range(2, 7))
def test_setting_neutral_inputs_are_distinct_and_demonstrations_identify_the_policy(seed, demos):
    prototype = load("prototype.py")
    adapter = load("adapter.py")
    settings = [
        {"equivalence_policy": "rotation"},
        {"equivalence_policy": "dihedral"},
    ]
    episodes = [adapter.generate(seed, setting, demos, 4) for setting in settings]
    assert all_inputs(episodes[0]) == all_inputs(episodes[1])
    assert len(episodes[0]["train"]) == demos
    assert len(episodes[0]["test"]) == 4
    serialized = [json.dumps(grid, separators=(",", ":")) for grid in all_inputs(episodes[0])]
    assert len(serialized) == len(set(serialized))
    assert any(a["output"] != b["output"] for a, b in zip(episodes[0]["train"], episodes[1]["train"]))
    for setting, episode in zip(settings, episodes):
        assert episode["settings"] == setting
        assert episode["program_solution"] == prototype.program(setting)
        assert all(pair["output"] == prototype.solve(pair["input"], setting["equivalence_policy"])
                   for pair in all_pairs(episode))
        certificate = prototype.lesson_certificate(episode)
        assert certificate["declared_survivors"] == [setting["equivalence_policy"]]
        assert certificate["harmful_rival_survivors"] == []


def test_query_profiles_include_real_30x30_boundary_and_quadrant_stress():
    prototype = load("prototype.py")
    episode = prototype.generate(23, {"equivalence_policy": "rotation"}, 6, 4)
    assert [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]] == [
        (14, 16), (18, 20), (24, 27), (30, 30)
    ]
    large = episode["test"][-1]["input"]
    cells = [(r, c, value) for r, row in enumerate(large) for c, value in enumerate(row) if value]
    assert len(cells) >= 36
    assert {(r >= 15, c >= 15) for r, c, _ in cells} == {
        (False, False), (False, True), (True, False), (True, True)
    }
    assert {r for r, _, _ in cells} & {0, 29}
    assert {c for _, c, _ in cells} & {0, 29}
    assert len(prototype.extract_components(large)) == 6
    assert prototype.solve(large, "rotation") != prototype.solve(large, "dihedral")


def test_public_turns_reveal_one_query_and_ignore_all_private_fields():
    prototype = load("prototype.py")
    episode = prototype.generate(7, {"equivalence_policy": "dihedral"}, 3, 4)
    turns = prototype.public_query_turns(episode)
    assert len(turns) == 4
    for index, turn in enumerate(turns):
        assert set(turn) == {"train", "test"}
        assert len(turn["train"]) == 3 and len(turn["test"]) == 1
        assert all(set(pair) == {"input", "output"} for pair in turn["train"])
        assert set(turn["test"][0]) == {"input"}
        assert turn["test"][0]["input"] == episode["test"][index]["input"]
        assert public_challenge_id(turn) == hashlib.sha256(public_challenge_bytes(turn)).hexdigest()

    changed = copy.deepcopy(episode)
    changed["settings"] = {"equivalence_policy": "private-change"}
    changed["seed"] = 999
    changed["program_solution"] = "private-change"
    for pair in changed["test"]:
        pair["output"][0][0] = (pair["output"][0][0] + 1) % 10
    assert [public_challenge_bytes(turn) for turn in prototype.public_query_turns(changed)] == [
        public_challenge_bytes(turn) for turn in turns
    ]


def test_component_orbit_intermediate_is_needed_before_matrix_rendering():
    prototype = load("prototype.py")
    episode = prototype.generate(13, {"equivalence_policy": "rotation"}, 2, 4)
    grid = episode["test"][-1]["input"]
    analysis = prototype.analyze(grid, "rotation")
    assert len(analysis["components"]) == 6
    assert len(analysis["orbit_keys"]) == 6
    assert analysis["matrix"] == prototype.solve(grid, "rotation")
    wrong = prototype.solve_bbox_only(grid)
    assert wrong != analysis["matrix"]
    assert prototype.counterfactual_bbox_program() == (PARAMETRIC / "counterfactual_bbox.rkt").read_text(encoding="utf-8")


@pytest.mark.parametrize("bad", [
    {},
    {"equivalence_policy": "rotation", "extra": 1},
    {"equivalence_policy": "reflection"},
    {"equivalence_policy": True},
    None,
])
def test_setting_validation_is_exact(bad):
    prototype = load("prototype.py")
    with pytest.raises(ValueError):
        prototype.program(bad)


@pytest.mark.parametrize("args", [
    (True, {"equivalence_policy": "rotation"}, 3, 4),
    (-1, {"equivalence_policy": "rotation"}, 3, 4),
    (2**63, {"equivalence_policy": "rotation"}, 3, 4),
    (0, {"equivalence_policy": "rotation"}, 1, 4),
    (0, {"equivalence_policy": "rotation"}, 7, 4),
    (0, {"equivalence_policy": "rotation"}, 3, 3),
    (0, {"equivalence_policy": "rotation"}, 3, True),
])
def test_request_validation_is_exact(args):
    prototype = load("prototype.py")
    with pytest.raises(ValueError):
        prototype.generate(*args)


def test_generation_is_deterministic_fresh_and_bounded_sampler_audit_is_clean():
    prototype = load("prototype.py")
    first = prototype.generate(91, {"equivalence_policy": "dihedral"}, 6, 4)
    second = prototype.generate(91, {"equivalence_policy": "dihedral"}, 6, 4)
    assert first == second and first is not second
    first["train"][0]["input"][0][0] = 9
    assert first != second
    assert prototype.generate(91, {"equivalence_policy": "dihedral"}, 6, 4) == second

    for seed in range(24):
        for policy in prototype.POLICIES:
            episode = prototype.generate(seed, {"equivalence_policy": policy}, 6, 4)
            assert prototype.lesson_certificate(episode)["harmful_rival_survivors"] == []
            assert len({json.dumps(grid, separators=(",", ":")) for grid in all_inputs(episode)}) == 10
            assert all(1 <= len(pair["output"]) <= 6 for pair in all_pairs(episode))
