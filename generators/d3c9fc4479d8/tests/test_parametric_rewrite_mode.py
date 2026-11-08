"""Prototype-only tests for one-step versus cascading legend rewrites."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

TASK_ID = "d3c9fc4479d8"
HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
SUPPORT = ROOT / "shared/runtime"
if str(SUPPORT) not in sys.path:
    sys.path.insert(0, str(SUPPORT))

from reviewer_support import canonical_path

PROTO_PATH = HOME / "workspace/parametric/prototype.py"
ADAPTER_PATH = HOME / "workspace/parametric/adapter.py"
PROMOTION_PATH = HOME / "workspace/parametric/promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing required prototype file: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def prototype():
    return _load(PROTO_PATH, "d3c9fc4479d8_rewrite_mode_prototype")


@pytest.fixture(scope="module")
def adapter():
    return _load(ADAPTER_PATH, "d3c9fc4479d8_rewrite_mode_adapter")


def canonical_source() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines() if line.strip()]
    sources = {row["program_solution"] for row in rows if row.get("task_id") == TASK_ID}
    assert len(sources) == 1
    return sources.pop()


def witness_grid() -> list[list[int]]:
    return [
        [1, 2, 2, 3, 0, 0],
        [1, 2, 3, 4, 0, 1],
        [0, 1, 4, 2, 3, 0],
    ]


def test_default_program_is_exact_canonical_and_cascade_changes_only_behavior(prototype):
    once = prototype.materialize_program(mode="once")
    cascade = prototype.materialize_program(mode="cascade")
    assert once == canonical_source()
    assert hashlib.sha256(once.encode()).hexdigest() == prototype.CANONICAL_SHA256
    assert cascade != once
    assert prototype.settings("once") == {"mode": "once"}
    assert prototype.settings("cascade") == {"mode": "cascade"}


def test_hand_derived_chain_witness_distinguishes_once_from_cascade(prototype):
    grid = witness_grid()
    before = copy.deepcopy(grid)
    assert prototype.transform(grid, mode="once") == [
        [2, 3, 3, 4, 0, 2],
        [0, 2, 4, 3, 3, 0],
    ]
    assert prototype.transform(grid, mode="cascade") == [
        [3, 3, 3, 4, 0, 3],
        [0, 3, 4, 3, 3, 0],
    ]
    assert grid == before


@pytest.mark.parametrize("mode", ["once", "cascade"])
@pytest.mark.parametrize("demos", range(2, 7))
def test_supported_counts_are_unique_and_demos_alone_identify_mode(prototype, mode, demos):
    episode = prototype.sample_episode(17, mode=mode, n_demo=demos, n_query=4)
    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    pairs = episode["train"] + episode["test"]
    assert len({json.dumps(pair["input"]) for pair in pairs}) == len(pairs)
    certificate = prototype.lesson_certificate(episode)
    assert certificate["survivors"] == [mode]
    assert certificate["identifiable"] is True
    changed = copy.deepcopy(episode)
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert prototype.lesson_certificate(changed) == certificate


def test_input_streams_and_split_prefixes_do_not_depend_on_hidden_mode_or_other_count(prototype):
    once = prototype.sample_episode(83, mode="once", n_demo=3, n_query=4)
    cascade = prototype.sample_episode(83, mode="cascade", n_demo=3, n_query=4)
    for split in ("train", "test"):
        assert [pair["input"] for pair in once[split]] == [pair["input"] for pair in cascade[split]]
    one_query = prototype.sample_episode(83, mode="once", n_demo=3, n_query=1)
    six_demo = prototype.sample_episode(83, mode="once", n_demo=6, n_query=4)
    assert once["test"][:1] == one_query["test"]
    assert once["train"] == six_demo["train"][:3]
    assert once["test"] == six_demo["test"]
    assert prototype.first_turn(once) == prototype.first_turn(one_query)
    assert len(prototype.first_turn(once)["test"]) == 1
    assert set(prototype.first_turn(once)["test"][0]) == {"input"}


@pytest.mark.parametrize(
    "field,value",
    [
        ("n_demo", 1), ("n_demo", 7), ("n_demo", True), ("n_demo", 3.0),
        ("n_query", 0), ("n_query", 5), ("n_query", False), ("n_query", 4.0),
        ("seed", -1), ("seed", 2**63), ("seed", True),
        ("mode", "repeat"), ("mode", 1),
    ],
)
def test_invalid_requests_fail_before_sampling(prototype, field, value):
    kwargs = {"seed": 0, "mode": "once", "n_demo": 3, "n_query": 4}
    kwargs[field] = value
    with pytest.raises(ValueError):
        prototype.sample_episode(**kwargs)


@pytest.mark.parametrize("height,width", [(8, 8), (8, 30), (30, 8), (30, 30)])
def test_exact_size_boundaries_have_substantive_body_content(prototype, height, width):
    grid = prototype.sample_input(51, index=9, height=height, width=width)
    assert (len(grid), len(grid[0])) == (height, width)
    legend_columns = [c for c, value in enumerate(grid[0]) if value != 0]
    assert legend_columns[0] in (0, 1)
    assert legend_columns == list(range(legend_columns[0], legend_columns[0] + 6))
    occupied = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value != 0]
    body_occupied = [(r, c) for r, c in occupied if r > 0]
    assert len(body_occupied) >= ((height - 1) * width) // 4
    assert max(r for r, _ in body_occupied) - min(r for r, _ in body_occupied) >= height - 3
    assert max(c for _, c in body_occupied) - min(c for _, c in body_occupied) >= width - 3
    assert prototype.transform(grid, mode="once") != prototype.transform(grid, mode="cascade")


def test_native_adapter_and_promotion_contract(prototype, adapter):
    promotion = json.loads(PROMOTION_PATH.read_text())
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/d3c9fc4479d8/workspace/parametric/adapter.py",
        "parameters": {"mode": ["once", "cascade"]},
        "default": {"mode": "once"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
    }
    assert adapter.program({"mode": "once"}) == prototype.materialize_program(mode="once")
    episode = adapter.generate(7, {"mode": "cascade"}, 2, 4)
    assert len(episode["train"]) == 2 and len(episode["test"]) == 4
    assert episode["program_solution"] == prototype.materialize_program(mode="cascade")


def test_racket_labels_export_replay_and_tamper_rejection(prototype, tmp_path):
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(timeout=20, startup_timeout=60) as bridge:
        episodes = [
            prototype.generate_episode(23, mode=mode, n_demo=2, n_query=4, bridge=bridge)
            for mode in ("once", "cascade")
        ]
        output = tmp_path / "batch"
        index = prototype.write_batch(episodes, output)
        result = prototype.verify_batch(output, bridge=bridge)
        assert result["episodes"] == 2
        assert result["labeled_pairs"] == 12
        assert result["queries"] == 8
        assert result["max_shape"] == [30, 30]

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


def test_duplicate_visible_challenges_are_rejected_atomically(prototype, tmp_path):
    episode = prototype.sample_episode(7, n_demo=2, n_query=1)
    output = tmp_path / "duplicate"
    with pytest.raises(ValueError, match="duplicate"):
        prototype.write_batch([episode, episode], output)
    assert not output.exists()
