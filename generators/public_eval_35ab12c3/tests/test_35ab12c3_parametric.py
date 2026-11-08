"""Native episode, privacy, and bounded-teaching contracts for 35ab12c3."""
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
    spec = importlib.util.spec_from_file_location("_public_eval_35ab12c3_adapter", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_default_program_exact_and_alternate_changes_labels_on_identical_inputs():
    a = load_adapter()
    assert a.program({"edge_mode": "all_8"}) == (HOME / "reference.rkt").read_text()
    full = a.generate(17, {"edge_mode": "all_8"}, 2, 4)
    orth = a.generate(17, {"edge_mode": "orthogonal"}, 2, 4)
    assert [p["input"] for split in ("train", "test") for p in full[split]] == [
        p["input"] for split in ("train", "test") for p in orth[split]
    ]
    assert all(p["output"] != q["output"] for p, q in zip(full["train"], orth["train"]))


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_distinct_determinism_query_independence_and_large_stress(demos):
    a = load_adapter()
    episode = a.generate(43, {"edge_mode": "all_8"}, demos, 4)
    assert episode == a.generate(43, {"edge_mode": "all_8"}, demos, 4)
    assert len(episode["train"]) == demos and len(episode["test"]) == 4
    inputs = [pair["input"] for split in ("train", "test") for pair in episode[split]]
    assert len({json.dumps(grid) for grid in inputs}) == demos + 4
    assert episode["test"] == a.generate(43, {"edge_mode": "all_8"}, 2, 4)["test"]
    assert len(episode["test"][3]["input"]) == 30
    assert len(episode["test"][3]["input"][0]) == 30
    assert sum(value != a.impl.analyse(episode["test"][3]["input"])["background"] for row in episode["test"][3]["output"] for value in row) >= 100


@pytest.mark.parametrize(
    "seed,demos,queries,settings",
    [
        (True, 2, 4, {"edge_mode": "all_8"}),
        (-1, 2, 4, {"edge_mode": "all_8"}),
        (1, 1, 4, {"edge_mode": "all_8"}),
        (1, 7, 4, {"edge_mode": "all_8"}),
        (1, True, 4, {"edge_mode": "all_8"}),
        (1, 2, 3, {"edge_mode": "all_8"}),
        (1, 2, 5, {"edge_mode": "all_8"}),
        (1, 2, 4, {"edge_mode": "bad"}),
        (1, 2, 4, {}),
        (1, 2, 4, {"edge_mode": "all_8", "extra": 1}),
    ],
)
def test_rejects_invalid_episode_requests(seed, demos, queries, settings):
    a = load_adapter()
    with pytest.raises(ValueError):
        a.generate(seed, settings, demos, queries)


def test_public_turns_reveal_one_query_and_ignore_all_private_fields():
    a = load_adapter()
    episode = a.generate(17, {"edge_mode": "all_8"}, 3, 4)
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
    assert set(public[0]["train"][0]) == {"input", "output"}


def test_two_demo_lessons_reject_declared_harmful_rivals():
    a = load_adapter()
    rivals = ["all_pairs", "convex_hull", "row_order", "seed_shadow", "no_shadow", "overwrite_shadow"]
    for seed in range(32):
        for mode in a.impl.EDGE_MODES:
            episode = a.generate(seed, {"edge_mode": mode}, 2, 4)
            for rival in rivals:
                survives = all(a.impl.solve(pair["input"], mode, rival) == pair["output"] for pair in episode["train"])
                assert not survives or all(
                    a.impl.solve(pair["input"], mode, rival) == pair["output"] for pair in episode["test"]
                ), (seed, mode, rival)
