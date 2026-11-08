"""Native contract regressions for the four-corner crop proposal."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "d2b3402dde86"
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing {path.name}"
    spec = importlib.util.spec_from_file_location(f"d2_corner_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    root = find_root(__file__)
    ledger = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    for line in ledger.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical row missing")


def test_native_adapter_and_promotion_contract_exist():
    adapter = load("adapter")
    episode = adapter.generate(17, {"corner": "upper_left"}, 3, 4)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program({"corner": "upper_left"})
    promotion = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["default"] == {"corner": "upper_left"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}


def test_default_program_is_exact_canonical_and_matches_canonical_pairs():
    module = load("prototype")
    assert module.program({"corner": "upper_left"}) == canonical_program()
    root = find_root(__file__)
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        assert module.transform(pair["input"], {"corner": "upper_left"}) == pair["output"]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_four_distinct_queries_and_teaching(demos):
    module = load("prototype")
    settings = [
        {"corner": "upper_left"},
        {"corner": "upper_right"},
        {"corner": "lower_left"},
        {"corner": "lower_right"},
    ]
    for seed in (0, 17, 239):
        episodes = [module.generate(seed, setting, demos, 4) for setting in settings]
        batches = [[pair["input"] for pair in episode["train"] + episode["test"]]
                   for episode in episodes]
        assert all(batch == batches[0] for batch in batches[1:])
        for episode in episodes:
            inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
            assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
            certificate = episode["certificate"]
            assert certificate["identified"] is True
            assert certificate["survivors"] == [episode["settings"]["corner"]]
            assert all(certificate["query_identifiable"])
            for pair in episode["train"] + episode["test"]:
                outputs = {
                    corner: module.transform(pair["input"], {"corner": corner})
                    for corner in module.ALLOWED_SETTINGS
                }
                assert len({json.dumps(value) for value in outputs.values()}) == 4


def test_substantive_30_by_30_query_reaches_boundaries_and_has_distinct_corners():
    module = load("prototype")
    episode = module.generate(17, {"corner": "lower_right"}, 2, 4)
    grid = episode["test"][-1]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    nonzero = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 500
    assert {r for r, _ in nonzero} >= {0, 29}
    assert {c for _, c in nonzero} >= {0, 29}
    outputs = [module.transform(grid, {"corner": corner}) for corner in module.ALLOWED_SETTINGS]
    assert len({json.dumps(value) for value in outputs}) == 4
    assert all((len(value), len(value[0])) == (15, 15) for value in outputs)


def test_public_projection_is_private_invariant_and_prefix_stable():
    module = load("prototype")
    one = module.generate(17, {"corner": "upper_right"}, 3, 1)
    four = module.generate(17, {"corner": "upper_right"}, 3, 4)
    assert public_challenge_bytes(one) == module.visible_turn(four, 0)
    assert public_challenge_id(one) == hashlib.sha256(public_challenge_bytes(one)).hexdigest()
    changed = copy.deepcopy(four)
    changed["settings"] = {"corner": "private-change"}
    changed["program_solution"] = "private program"
    changed["test"][0]["output"][0][0] = 9
    assert public_challenge_bytes(four) == public_challenge_bytes(changed)
    for index in range(4):
        visible = json.loads(module.visible_turn(four, index))
        assert set(visible) == {"train", "test"}
        assert visible["test"] == [{"input": four["test"][index]["input"]}]
        raw = module.visible_turn(four, index)
        assert b"settings" not in raw and b"program" not in raw and b"output" not in json.dumps(visible["test"]).encode()


def test_verifier_rejects_tampered_label_program_duplicate_and_boolean():
    module = load("prototype")
    episode = module.generate(0, {"corner": "lower_left"}, 2, 4)
    for kind in ("label", "program", "duplicate", "boolean"):
        bad = copy.deepcopy(episode)
        if kind == "label":
            bad["test"][0]["output"][0][0] = 9
        elif kind == "program":
            bad["program_solution"] = module.program({"corner": "upper_left"})
        elif kind == "duplicate":
            bad["test"][0] = copy.deepcopy(bad["train"][0])
        else:
            bad["train"][0]["input"][0][0] = False
        with pytest.raises(ValueError):
            module.verify_episode(bad)


@pytest.mark.parametrize("args", [
    (True, {"corner": "upper_left"}, 3, 4),
    (-1, {"corner": "upper_left"}, 3, 4),
    (0, {"corner": "upper_left"}, 1, 4),
    (0, {"corner": "upper_left"}, 7, 4),
    (0, {"corner": "upper_left"}, 3, 0),
    (0, {"corner": "upper_left"}, 3, 5),
    (0, {"corner": "upper_left", "extra": 1}, 3, 4),
    (0, {"corner": "center"}, 3, 4),
])
def test_unsupported_requests_fail_explicitly(args):
    with pytest.raises(ValueError):
        load("prototype").generate(*args)
