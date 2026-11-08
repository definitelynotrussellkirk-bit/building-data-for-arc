"""Behavioral contract for the separate blue-object ranking prototype."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def prototype():
    path = HOME / "workspace/parametric/prototype.py"
    spec = importlib.util.spec_from_file_location("rank_metric_test_subject", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def witness():
    # L3: size 3 / bbox 4; T4: size 4 / bbox 6; line5: size 5 / bbox 5.
    grid = [[0] * 10 for _ in range(10)]
    groups = [([(0, 8), (1, 8), (1, 9)], 2, 2),
              ([(5, 1), (5, 2), (5, 3), (6, 2)], 3, 8),
              ([(3, c) for c in range(5)], 8, 3)]
    for cells, _, _ in groups:
        for r, c in cells:
            grid[r][c] = 1
    grid[9][9] = 7
    return grid, groups


def test_default_program_is_exact_canonical_bytes(prototype):
    from reviewer_support import canonical_path, find_root
    root = find_root(__file__)
    rows = [json.loads(line) for line in canonical_path(root).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows
                if row.get("task_id") == "8118155d8959"}
    assert programs == {prototype.materialize_program(metric="cells")}
    assert prototype.materialize_program(metric="bbox_area") not in programs


def test_literal_rank_witness_and_preserved_distractor(prototype):
    grid, groups = witness()
    before = copy.deepcopy(grid)
    for metric, slot in (("cells", 1), ("bbox_area", 2)):
        expected = copy.deepcopy(grid)
        for group in groups:
            for r, c in group[0]:
                expected[r][c] = group[slot]
        assert prototype.transform(grid, metric=metric) == expected
    assert grid == before


@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("metric", ["cells", "bbox_area"])
def test_counts_unique_queries_and_demo_only_teaching(prototype, demos, metric):
    episode = prototype.sample_episode(17, metric=metric, n_demo=demos, n_query=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(p["input"]) for p in pairs}) == len(pairs)
    certificate = prototype.lesson_certificate(episode)
    assert certificate["survivors"] == [metric]
    assert certificate["identifiable"] is True
    # A certificate must never obtain its conclusion from hidden query labels.
    changed = copy.deepcopy(episode)
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert prototype.lesson_certificate(changed) == certificate


def test_matched_settings_and_query_prefix_across_counts(prototype):
    a = prototype.sample_episode(83, metric="cells", n_demo=3, n_query=4)
    b = prototype.sample_episode(83, metric="bbox_area", n_demo=3, n_query=4)
    for split in ("train", "test"):
        assert [p["input"] for p in a[split]] == [p["input"] for p in b[split]]
    one = prototype.sample_episode(83, metric="cells", n_demo=3, n_query=1)
    assert prototype.first_turn(a) == prototype.first_turn(one)
    assert a["test"][:1] == one["test"]
    more_demos = prototype.sample_episode(83, metric="cells", n_demo=6, n_query=4)
    assert a["train"] == more_demos["train"][:3]
    assert a["test"] == more_demos["test"]


@pytest.mark.parametrize("field,value", [
    ("n_demo", 1), ("n_demo", 7), ("n_demo", True), ("n_demo", 3.0),
    ("n_query", 0), ("n_query", 5), ("n_query", False), ("n_query", 4.0),
    ("seed", -1), ("seed", True), ("metric", "width"), ("metric", 1),
])
def test_invalid_requests_reject_before_sampling(prototype, field, value):
    kwargs = {"seed": 0, "metric": "cells", "n_demo": 3, "n_query": 4}
    kwargs[field] = value
    with pytest.raises(ValueError):
        prototype.sample_episode(**kwargs)


@pytest.mark.parametrize("height,width", [(10, 10), (10, 30), (30, 10), (30, 30)])
def test_substantive_size_boundaries(prototype, height, width):
    grid = prototype.sample_input(51, index=9, height=height, width=width)
    assert (len(grid), len(grid[0])) == (height, width)
    objects = prototype.blue_objects(grid)
    assert len(objects) == 3
    assert sum(len(o) for o in objects) >= height * width // 8
    assert len({len(o) for o in objects}) == 3
    occupied = [(r, c) for r, row in enumerate(grid) for c, x in enumerate(row) if x]
    assert max(r for r, _ in occupied) - min(r for r, _ in occupied) >= height - 3
    assert max(c for _, c in occupied) - min(c for _, c in occupied) >= width - 3


def test_public_identity_and_first_turn_use_visible_bytes_only(prototype):
    from reviewer_support import public_challenge_bytes, public_challenge_id
    episode = prototype.sample_episode(91, n_demo=2, n_query=4)
    changed = copy.deepcopy(episode)
    changed.update(seed=999, parameters={"metric": "secret"}, program="secret")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert public_challenge_id(episode) == public_challenge_id(changed)
    assert public_challenge_bytes(episode) == public_challenge_bytes(changed)
    public = json.loads(public_challenge_bytes(episode))
    assert set(public) == {"train", "test"}
    assert all(set(p) == {"input"} for p in public["test"])
    assert len(prototype.first_turn(episode)["test"]) == 1


def test_racket_labels_export_replay_and_tamper_rejection(prototype, tmp_path):
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=15) as bridge:
        episodes = [prototype.generate_episode(17, metric=metric, n_demo=2,
                    n_query=4, bridge=bridge) for metric in ("cells", "bbox_area")]
        output = tmp_path / "batch"
        index = prototype.write_batch(episodes, output)
        result = prototype.verify_batch(output, bridge=bridge)
        assert result["episodes"] == 2
        assert result["labeled_pairs"] == 12
        assert result["queries"] == 8
        private = output / "private" / (index["public_ids"][0] + ".json")
        original = private.read_bytes()
        value = json.loads(original)
        value["test"][0]["output"][0][0] = False
        private.write_text(json.dumps(value))
        with pytest.raises(ValueError, match="integer"):
            prototype.verify_batch(output, bridge=bridge)
        private.write_bytes(original)
        value = json.loads(original)
        value["test"][0]["output"][0][0] = (value["test"][0]["output"][0][0] + 1) % 10
        private.write_text(json.dumps(value))
        with pytest.raises(ValueError, match="label"):
            prototype.verify_batch(output, bridge=bridge)


def test_export_duplicate_refusal_is_atomic(prototype, tmp_path):
    episode = prototype.sample_episode(7)
    output = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate"):
        prototype.write_batch([episode, episode], output)
    assert not output.exists()


@pytest.mark.parametrize("metric", ["cells", "bbox_area"])
def test_first_two_demos_teach_bbox_ties_and_change_t4_rank(prototype, metric):
    episode = prototype.sample_episode(2, metric=metric, n_demo=2, n_query=4)
    tie_keys = {
        "cells": lambda obj: (len(obj), *prototype.bbox(obj)[:2]),
        "descending_cells": lambda obj: (-len(obj), *prototype.bbox(obj)[:2]),
        "column_first": lambda obj: (prototype.bbox(obj)[1], prototype.bbox(obj)[0]),
        "reverse_row": lambda obj: (-prototype.bbox(obj)[0], prototype.bbox(obj)[1]),
        "reverse_column": lambda obj: (prototype.bbox(obj)[0], -prototype.bbox(obj)[1]),
    }
    for name, tie_key in tie_keys.items():
        def rival(grid):
            out = copy.deepcopy(grid)
            groups = sorted(prototype.blue_objects(grid),
                            key=lambda obj: (prototype.score(obj, "bbox_area"), *tie_key(obj)))
            for group, color in zip(groups, (2, 3, 8)):
                for r, c in group:
                    out[r][c] = color
            return out
        assert any(rival(p["input"]) != p["output"] for p in episode["train"]), name
    colors = []
    for pair in episode["train"]:
        t4 = next(obj for obj in prototype.blue_objects(pair["input"]) if len(obj) == 4)
        assert prototype.score(t4, "bbox_area") == 6
        colors.append(pair["output"][t4[0][0]][t4[0][1]])
    assert len(set(colors)) == 2


@pytest.mark.parametrize("mutation", ["empty_directory", "false_runtime"])
def test_verifier_rejects_private_path_and_runtime_tampering(prototype, tmp_path, mutation):
    from arc_repl.racket_bridge import RacketBridge
    with RacketBridge(timeout=15) as bridge:
        episode = prototype.generate_episode(17, n_demo=2, n_query=1, bridge=bridge)
        out = tmp_path / "tampered"
        index = prototype.write_batch([episode], out)
        if mutation == "empty_directory":
            (out / "public" / "metric=cells").mkdir()
        else:
            path = out / "private" / (index["public_ids"][0] + ".json")
            row = json.loads(path.read_bytes())
            row["racket"] = {"backend": "python", "protected": False}
            path.write_text(json.dumps(row))
        with pytest.raises(ValueError):
            prototype.verify_batch(out, bridge=bridge)


def test_ambiguous_demos_cannot_borrow_query_answer(prototype):
    demos = []
    for offset in (0, 2):
        grid = [[0] * 12 for _ in range(12)]
        groups = [[(offset, 0), (offset, 1)], [(4, c) for c in range(3)],
                  [(8, 7), (8, 8), (8, 9), (9, 8)]]
        for group in groups:
            for r, c in group:
                grid[r][c] = 1
        grid[11][11] = 7
        demos.append({"input": grid, "output": prototype.transform(grid)})
    query, _ = witness()
    challenge = {"train": demos, "test": [{"input": query, "output": prototype.transform(query)}]}
    certificate = prototype.lesson_certificate(challenge)
    assert {"cells", "bbox_area"} <= set(certificate["survivors"])
    assert certificate["identifiable"] is False
    assert certificate["query_agreement"] == [False]
