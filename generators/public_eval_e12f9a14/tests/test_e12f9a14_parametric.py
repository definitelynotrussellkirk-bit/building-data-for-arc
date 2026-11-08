"""Native episode, privacy, and bounded-teaching contracts for e12f9a14."""
from __future__ import annotations

from pathlib import Path
import copy
import importlib.util
import json
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]


def load_adapter():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.exists(), "native adapter has not been authored"
    spec = importlib.util.spec_from_file_location("_public_eval_e12f9a14_adapter", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_default_program_exact_and_stop_changes_labels_on_identical_inputs():
    a = load_adapter()
    assert a.program({"collision_rule": "vector_sum"}) == (HOME / "reference.rkt").read_text()
    merged = a.generate(17, {"collision_rule": "vector_sum"}, 2, 4)
    stopped = a.generate(17, {"collision_rule": "stop"}, 2, 4)
    assert [p["input"] for split in ("train", "test") for p in merged[split]] == [
        p["input"] for split in ("train", "test") for p in stopped[split]
    ]
    assert all(p["output"] != q["output"] for p, q in zip(merged["train"], stopped["train"]))


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_distinct_determinism_query_independence_and_large_stress(demos):
    a = load_adapter()
    episode = a.generate(43, {"collision_rule": "vector_sum"}, demos, 4)
    assert episode == a.generate(43, {"collision_rule": "vector_sum"}, demos, 4)
    assert len(episode["train"]) == demos and len(episode["test"]) == 4
    inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({json.dumps(grid) for grid in inputs}) == demos + 4
    assert episode["test"] == a.generate(43, {"collision_rule": "vector_sum"}, 2, 4)["test"]
    assert len(episode["test"][3]["input"]) == 30
    assert len(episode["test"][3]["input"][0]) == 30
    assert len(a.impl.trace(episode["test"][3]["input"])["events"]) >= 1


def test_seed_28_train_query_bank_is_structurally_distinct():
    a = load_adapter()
    episode = a.generate(28, {"collision_rule": "vector_sum"}, 2, 4)
    inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == 6


@pytest.mark.parametrize(
    "seed,demos,queries,settings",
    [
        (True, 2, 4, {"collision_rule": "vector_sum"}),
        (-1, 2, 4, {"collision_rule": "vector_sum"}),
        (1, 1, 4, {"collision_rule": "vector_sum"}),
        (1, 7, 4, {"collision_rule": "vector_sum"}),
        (1, True, 4, {"collision_rule": "vector_sum"}),
        (1, 2, 3, {"collision_rule": "vector_sum"}),
        (1, 2, 5, {"collision_rule": "vector_sum"}),
        (1, 2, 4, {"collision_rule": "bad"}),
        (1, 2, 4, {}),
        (1, 2, 4, {"collision_rule": "vector_sum", "extra": 1}),
    ],
)
def test_rejects_invalid_episode_requests(seed, demos, queries, settings):
    a = load_adapter()
    with pytest.raises(ValueError):
        a.generate(seed, settings, demos, queries)


def test_public_turns_reveal_one_query_and_ignore_private_fields():
    a = load_adapter()
    episode = a.generate(17, {"collision_rule": "vector_sum"}, 3, 4)
    public = a.impl.public_turns(episode, 918)
    assert len(public) == 4
    assert all(set(view) == {"train", "test"} and len(view["test"]) == 1 for view in public)
    assert all(set(view["test"][0]) == {"input"} for view in public)
    changed = copy.deepcopy(episode)
    changed["settings"] = {"secret": True}
    changed["program_solution"] = "SECRET"
    changed["seed"] = 999
    changed["train"][0]["private"] = "SECRET"
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert public == a.impl.public_turns(changed, 918)
    assert public[:1] == a.impl.public_turns(episode, 918, stop_after=1)
    assert len({json.dumps(a.impl.public_turns(episode, seed)[0]["test"]) for seed in range(16)}) > 1


def test_two_demo_lessons_reject_declared_harmful_rivals():
    a = load_adapter()
    for seed in range(24):
        for rule in a.impl.COLLISION_RULES:
            episode = a.generate(seed, {"collision_rule": rule}, 2, 4)
            other = "stop" if rule == "vector_sum" else "vector_sum"
            assert any(a.impl.solve(pair["input"], other) != pair["output"] for pair in episode["train"])
            for rival in ("no_merge", "destination_only"):
                fits = all(a.impl.solve(pair["input"], rule, rival) == pair["output"] for pair in episode["train"])
                assert not fits or all(
                    a.impl.solve(pair["input"], rule, rival) == pair["output"] for pair in episode["test"]
                ), (seed, rule, rival)


def test_bounded_audit_tool_is_importable_and_source_bound():
    path = HOME / "workspace/parametric/audit.py"
    assert path.exists()
    spec = importlib.util.spec_from_file_location("_public_eval_e12f9a14_audit", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    assert module.TASK == "public_eval_e12f9a14"
    assert any(row["path"].endswith("workspace/parametric/audit.py") for row in module.source_files())
