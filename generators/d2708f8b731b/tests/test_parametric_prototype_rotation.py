"""Native contract regressions for the prototype-rotation legend proposal."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "d2708f8b731b"
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing {path.name}"
    spec = importlib.util.spec_from_file_location(f"prototype_rotation_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    root = find_root(__file__)
    ledger = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    return next(
        json.loads(line)["program_solution"]
        for line in ledger.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def test_native_adapter_and_promotion_contract_exist():
    adapter = load("adapter")
    episode = adapter.generate(17, {"prototype_transform": "identity"}, 3, 4)
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program(
        {"prototype_transform": "identity"}
    )
    promotion = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["default"] == {"prototype_transform": "identity"}
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}


def test_default_program_is_exact_canonical_and_python_matches_canonical_pairs():
    module = load("prototype")
    assert module.program({"prototype_transform": "identity"}) == canonical_program()
    root = find_root(__file__)
    for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
        assert module.transform(
            pair["input"], {"prototype_transform": "identity"}
        ) == pair["output"]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_all_orientations_and_demo_only_identification(demos):
    module = load("prototype")
    settings = ("identity", "quarter_turn")
    expected_rivals = {
        "identity",
        "quarter_turn",
        "constant_first",
        "constant_last",
        "target_order",
    }
    for seed in (0, 17, 239):
        episodes = [
            module.generate(seed, {"prototype_transform": setting}, demos, 4)
            for setting in settings
        ]
        batches = [
            [pair["input"] for pair in episode["train"] + episode["test"]]
            for episode in episodes
        ]
        assert batches[0] == batches[1]
        for episode in episodes:
            inputs = [pair["input"] for pair in episode["train"] + episode["test"]]
            assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs}) == demos + 4
            certificate = episode["certificate"]
            chosen = episode["settings"]["prototype_transform"]
            assert certificate["identified"] is True
            assert certificate["survivors"] == [chosen]
            assert set(certificate["rejected"]) >= expected_rivals - {chosen}
            assert all(certificate["query_identifiable"])
            for pair in episode["train"] + episode["test"]:
                facts = module.features(pair["input"])
                assert set(facts["prototype_shapes"]) == set(module.ORBIT)
                assert set(facts["target_shapes"]) == set(module.ORBIT)
                assert facts["n_prototypes"] == 4
                assert facts["n_targets"] >= 8
        for left, right in zip(
            episodes[0]["train"] + episodes[0]["test"],
            episodes[1]["train"] + episodes[1]["test"],
        ):
            assert left["output"] != right["output"]


def test_demo_and_query_count_prefixes_are_independent():
    module = load("prototype")
    settings = {"prototype_transform": "quarter_turn"}
    two = module.generate(17, settings, 2, 4)
    six = module.generate(17, settings, 6, 4)
    one = module.generate(17, settings, 3, 1)
    four = module.generate(17, settings, 3, 4)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert module.visible_turn(one, 0) == module.visible_turn(four, 0)


def test_30_by_30_query_is_dense_repeated_and_touches_every_boundary():
    module = load("prototype")
    episode = module.generate(17, {"prototype_transform": "quarter_turn"}, 2, 4)
    grid = episode["test"][-1]["input"]
    facts = module.features(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert facts["n_prototypes"] == 4
    assert facts["n_targets"] >= 60
    counts = Counter(facts["target_shapes"])
    assert set(counts) == set(module.ORBIT)
    assert min(counts.values()) >= 12
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    neutral = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 1}
    assert len(neutral) >= 190
    assert any(r == 0 for r, _ in nonzero) and any(r == 29 for r, _ in nonzero)
    assert any(c == 0 for _, c in nonzero) and any(c == 29 for _, c in nonzero)


def test_public_projection_is_private_invariant_and_prefix_stable():
    module = load("prototype")
    one = module.generate(17, {"prototype_transform": "quarter_turn"}, 3, 1)
    four = module.generate(17, {"prototype_transform": "quarter_turn"}, 3, 4)
    assert public_challenge_bytes(one) == module.visible_turn(four, 0)
    assert public_challenge_id(one) == hashlib.sha256(public_challenge_bytes(one)).hexdigest()
    changed = copy.deepcopy(four)
    changed["settings"] = {"prototype_transform": "private"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"][0][0] = 9
    assert public_challenge_bytes(four) == public_challenge_bytes(changed)
    for index in range(4):
        visible = json.loads(module.visible_turn(four, index))
        assert visible["test"] == [{"input": four["test"][index]["input"]}]
        assert set(visible) == {"train", "test"}


def test_verifier_rejects_tampered_label_program_duplicate_and_boolean():
    module = load("prototype")
    episode = module.generate(0, {"prototype_transform": "identity"}, 2, 4)
    for kind in ("label", "program", "duplicate", "boolean"):
        bad = copy.deepcopy(episode)
        if kind == "label":
            bad["test"][0]["output"][0][0] = 9
        elif kind == "program":
            bad["program_solution"] = module.program(
                {"prototype_transform": "quarter_turn"}
            )
        elif kind == "duplicate":
            bad["test"][0] = copy.deepcopy(bad["train"][0])
        else:
            bad["train"][0]["input"][0][0] = False
        with pytest.raises(ValueError):
            module.verify_episode(bad)


@pytest.mark.parametrize(
    "args",
    [
        (True, {"prototype_transform": "identity"}, 3, 4),
        (-1, {"prototype_transform": "identity"}, 3, 4),
        (0, {"prototype_transform": "identity"}, 1, 4),
        (0, {"prototype_transform": "identity"}, 7, 4),
        (0, {"prototype_transform": "identity"}, 3, 0),
        (0, {"prototype_transform": "identity"}, 3, 5),
        (0, {"prototype_transform": "mirror"}, 3, 4),
        (0, {"prototype_transform": "identity", "extra": 1}, 3, 4),
    ],
)
def test_unsupported_requests_fail_explicitly(args):
    with pytest.raises(ValueError):
        load("prototype").generate(*args)
