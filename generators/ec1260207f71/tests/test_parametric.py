"""Focused contracts for the separate aligned/reversed row-transfer family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def load(name):
    path = HOME / (name + ".py")
    if not path.is_file():
        pytest.fail(f"The requested executable parametric component is missing: {path.name}")
    spec = importlib.util.spec_from_file_location("ec1260_test_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixture():
    """Hand-built 14x7 scene: upper-left offset 0 maps to row 10 or 13."""
    grid = [[0] * 7 for _ in range(14)]
    for offset in range(4):
        grid[offset][0] = 2
        grid[10 + offset][6] = 2
    grid[0][3] = 8
    return grid


def test_native_adapter_produces_requested_four_query_episode():
    adapter = load("adapter")
    episode = adapter.generate(17, {"transfer_order": "aligned"}, 3, 4)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == adapter.program({"transfer_order": "aligned"})


@pytest.mark.parametrize("order,filled_row", [("aligned", 10), ("reversed", 13)])
def test_literal_row_transfer_preserves_join_and_reverses_only_destination(order, filled_row):
    module = load("prototype")
    grid = fixture()
    expected = copy.deepcopy(grid)
    expected[0] = [2, 8, 8, 4, 0, 0, 0]
    expected[filled_row] = [8, 8, 8, 8, 8, 8, 2]
    assert module.transform(grid, {"transfer_order": order}) == expected
    assert grid == fixture()


def test_default_is_exact_canonical_program_and_all_public_labels_agree():
    from reviewer_support import canonical_pairs, find_root
    module = load("prototype")
    root = find_root(__file__)
    ledger = root / "shared/data/canonical/puzzles.jsonl"
    canonical = next(json.loads(line)["program_solution"] for line in ledger.read_text().splitlines()
                     if json.loads(line).get("task_id") == "ec1260207f71")
    assert module.program({"transfer_order": "aligned"}) == canonical
    for pair in canonical_pairs("ec1260207f71", root=root, labeled_only=True):
        assert module.transform(pair["input"], {"transfer_order": "aligned"}) == pair["output"]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_four_novel_queries_and_branch_witnesses(demos):
    module = load("prototype")
    for seed in [0, 17, 239]:
        episodes = [module.generate(seed, {"transfer_order": order}, demos, 4)
                    for order in ["aligned", "reversed"]]
        assert [[p["input"] for p in e["train"] + e["test"]] for e in episodes][0] == [
            [p["input"] for p in e["train"] + e["test"]] for e in episodes][1]
        for episode in episodes:
            inputs = [p["input"] for p in episode["train"] + episode["test"]]
            assert len({json.dumps(g) for g in inputs}) == demos + 4
            certificate = module.teaching_certificate(episode["train"],
                [p["input"] for p in episode["test"]], episode["settings"])
            assert certificate["identified"] is True
            assert certificate["survivors"] == [episode["settings"]["transfer_order"]]
            assert all(certificate["query_identifiable"])
            assert set(certificate["rejected"]) >= {
                "upper_only", "lower_only", "left_only", "right_only",
                "join_only", "transfer_only", "keep_markers"}
            assert [(len(p["input"]), len(p["input"][0])) for p in episode["test"]] == [
                (14, 7), (19, 17), (26, 24), (30, 30)]


def test_dense_30_by_30_case_has_real_content_and_reaches_boundaries():
    module = load("prototype")
    episode = module.generate(17, {"transfer_order": "reversed"}, 2, 4)
    grid = episode["test"][-1]["input"]
    output = episode["test"][-1]["output"]
    assert sum(v == 2 for row in grid for v in row) == 28
    assert sum(v == 8 for row in grid for v in row) == 12
    assert sum(v == 8 for row in output for v in row) >= 12 * 29
    assert 2 in grid[0] and 2 in grid[-1]
    dot_columns = {c for row in grid for c, value in enumerate(row) if value == 8}
    assert {1, 28} <= dot_columns


def test_public_projection_is_private_invariant_and_one_query_prefix_is_exact():
    from reviewer_support import public_challenge_bytes, public_challenge_id
    module = load("prototype")
    one = module.generate(17, {"transfer_order": "reversed"}, 3, 1)
    four = module.generate(17, {"transfer_order": "reversed"}, 3, 4)
    assert public_challenge_bytes(one) == module.visible_turn(four, 0)
    altered = copy.deepcopy(four)
    altered.update(seed=999, settings={"private": "changed"}, program_solution="hidden")
    altered["test"][0]["output"][0][0] = 9
    assert public_challenge_bytes(four) == public_challenge_bytes(altered)
    assert public_challenge_id(four) == public_challenge_id(altered)
    for index in range(4):
        visible = json.loads(module.visible_turn(four, index))
        assert set(visible) == {"train", "test"}
        assert visible["test"] == [{"input": four["test"][index]["input"]}]
        assert b"settings" not in module.visible_turn(four, index)


def test_certificate_uses_demonstrations_and_rejects_known_upper_only_gap():
    module = load("prototype")
    episode = module.generate(17, {"transfer_order": "aligned"}, 2, 4)
    upper = fixture()
    lower = upper[::-1]
    lesson = [{"input": upper, "output": module.transform(upper, episode["settings"])}]
    certificate = module.teaching_certificate(lesson, [lower], episode["settings"])
    assert "upper_only" in certificate["survivors"]
    assert certificate["identified"] is False
    assert certificate["query_identifiable"] == [False]


def test_episode_verification_rejects_tampered_query_label_program_and_counts():
    module = load("prototype")
    episode = module.generate(0, {"transfer_order": "aligned"}, 2, 4)
    for kind in ["label", "program", "duplicate", "boolean"]:
        bad = copy.deepcopy(episode)
        if kind == "label":
            bad["test"][0]["output"][0][0] = 9
        elif kind == "program":
            bad["program_solution"] = module.program({"transfer_order": "reversed"})
        elif kind == "duplicate":
            bad["test"][0] = copy.deepcopy(bad["train"][0])
        else:
            bad["train"][0]["input"][0][1] = False
        with pytest.raises(ValueError):
            module.verify_episode(bad)


@pytest.mark.parametrize("args", [
    (True, {"transfer_order": "aligned"}, 3, 4),
    (-1, {"transfer_order": "aligned"}, 3, 4),
    (0, {"transfer_order": "aligned"}, 1, 4),
    (0, {"transfer_order": "aligned"}, 7, 4),
    (0, {"transfer_order": "aligned"}, 3, 0),
    (0, {"transfer_order": "aligned"}, 3, 5),
    (0, {"transfer_order": "aligned"}, 3.0, 4),
    (0, {"transfer_order": True}, 3, 4),
    (0, {"transfer_order": "unknown"}, 3, 4),
    (0, {"transfer_order": "aligned", "extra": 1}, 3, 4),
])
def test_unsupported_requests_fail_explicitly(args):
    with pytest.raises(ValueError):
        load("prototype").generate(*args)


def test_export_is_hash_named_sorted_masked_and_refuses_duplicates(tmp_path):
    from reviewer_support import public_challenge_bytes
    module = load("prototype")
    episodes = [module.generate(17, {"transfer_order": order}, 3, 4)
                for order in ["reversed", "aligned"]]
    result = module.write_export(episodes, tmp_path / "export")
    ids = result["public_ids"]
    assert ids == sorted(ids)
    for path in sorted((tmp_path / "export/public").glob("*.json")):
        data = path.read_bytes()
        assert path.stem == hashlib.sha256(data).hexdigest()
        obj = json.loads(data)
        assert data == public_challenge_bytes(obj)
        assert all(set(p) == {"input"} for p in obj["test"])
    with pytest.raises(ValueError):
        module.write_export([episodes[0], episodes[0]], tmp_path / "duplicate")
    assert not (tmp_path / "duplicate").exists()
    with pytest.raises(FileExistsError):
        module.write_export(episodes, tmp_path / "export")
