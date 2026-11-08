"""Native contract regressions for the center/away ray-tail proposal."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "02a33ab58da6"
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing {path.name}"
    spec = importlib.util.spec_from_file_location(f"ray_turn_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    root = find_root(__file__)
    ledger = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    return next(json.loads(line)["program_solution"] for line in ledger.read_text().splitlines()
                if json.loads(line).get("task_id") == TASK_ID)


def test_native_adapter_and_promotion_contract_exist():
    adapter = load("adapter")
    episode = adapter.generate(17, {"turn_policy": "toward_center"}, 3, 4)
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program({"turn_policy": "toward_center"})
    promotion = json.loads((HOME / "promotion.json").read_text())
    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["default"] == {"turn_policy": "toward_center"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}


def test_default_program_is_exact_canonical_and_python_matches_canonical_pairs():
    module = load("prototype")
    assert module.program({"turn_policy": "toward_center"}) == canonical_program()
    root = find_root(__file__)
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        assert module.transform(pair["input"], {"turn_policy": "toward_center"}) == pair["output"]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_four_queries_and_demonstration_only_identification(demos):
    module = load("prototype")
    policies = ("toward_center", "away_from_center")
    for seed in (0, 17, 239):
        episodes = [module.generate(seed, {"turn_policy": policy}, demos, 4) for policy in policies]
        batches = [[pair["input"] for pair in e["train"] + e["test"]] for e in episodes]
        assert batches[0] == batches[1]
        for episode in episodes:
            inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
            assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
            certificate = episode["certificate"]
            assert certificate["identified"] is True
            assert certificate["survivors"] == [episode["settings"]["turn_policy"]]
            assert set(certificate["rejected"]) >= {
                "toward_center", "away_from_center", "clockwise", "counterclockwise", "no_move"
            } - {episode["settings"]["turn_policy"]}
            assert all(certificate["query_identifiable"])
            for pair in episode["train"]:
                senses = {move["toward_sense"] for move in module.features(pair["input"])["moves"]}
                assert senses == {"clockwise", "counterclockwise"}


def test_30_by_30_query_has_eight_spread_motifs_and_boundary_contacts():
    module = load("prototype")
    episode = module.generate(17, {"turn_policy": "away_from_center"}, 2, 4)
    grid = episode["test"][-1]["input"]
    facts = module.features(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert len(facts["moves"]) == 8
    nonfield = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 7}
    assert len(nonfield) >= 70
    assert any(r == 0 for r, _ in nonfield) and any(r == 29 for r, _ in nonfield)
    assert any(c == 0 for _, c in nonfield) and any(c == 29 for _, c in nonfield)
    assert {move["direction"] for move in facts["moves"]} == set(module.DIRECTIONS)
    assert sum(move["tail_len"] for move in facts["moves"]) >= 24


def test_public_projection_is_private_invariant_and_prefix_stable():
    module = load("prototype")
    one = module.generate(17, {"turn_policy": "away_from_center"}, 3, 1)
    four = module.generate(17, {"turn_policy": "away_from_center"}, 3, 4)
    assert public_challenge_bytes(one) == module.visible_turn(four, 0)
    assert public_challenge_id(one) == hashlib.sha256(public_challenge_bytes(one)).hexdigest()
    changed = copy.deepcopy(four)
    changed["settings"] = {"turn_policy": "private"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"][0][0] = 9
    assert public_challenge_bytes(four) == public_challenge_bytes(changed)
    for index in range(4):
        visible = json.loads(module.visible_turn(four, index))
        assert visible["test"] == [{"input": four["test"][index]["input"]}]
        assert set(visible) == {"train", "test"}


def test_verifier_rejects_tampered_label_program_duplicate_and_boolean():
    module = load("prototype")
    episode = module.generate(0, {"turn_policy": "toward_center"}, 2, 4)
    for kind in ("label", "program", "duplicate", "boolean"):
        bad = copy.deepcopy(episode)
        if kind == "label":
            bad["test"][0]["output"][0][0] = 9
        elif kind == "program":
            bad["program_solution"] = module.program({"turn_policy": "away_from_center"})
        elif kind == "duplicate":
            bad["test"][0] = copy.deepcopy(bad["train"][0])
        else:
            bad["train"][0]["input"][0][0] = False
        with pytest.raises(ValueError):
            module.verify_episode(bad)


@pytest.mark.parametrize("args", [
    (True, {"turn_policy": "toward_center"}, 3, 4),
    (-1, {"turn_policy": "toward_center"}, 3, 4),
    (0, {"turn_policy": "toward_center"}, 1, 4),
    (0, {"turn_policy": "toward_center"}, 7, 4),
    (0, {"turn_policy": "toward_center"}, 3, 0),
    (0, {"turn_policy": "toward_center"}, 3, 5),
    (0, {"turn_policy": "sideways"}, 3, 4),
    (0, {"turn_policy": "toward_center", "extra": 1}, 3, 4),
])
def test_unsupported_requests_fail_explicitly(args):
    with pytest.raises(ValueError):
        load("prototype").generate(*args)
