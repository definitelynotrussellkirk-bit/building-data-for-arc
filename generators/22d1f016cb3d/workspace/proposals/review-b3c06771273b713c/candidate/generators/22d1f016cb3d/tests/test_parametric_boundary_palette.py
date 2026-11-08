"""Prototype-only tests for a fixed-per-episode boundary palette.

The selected production generator and canonical Racket authority stay fixed to
``ends1_edges4``. This file exercises only the isolated prototype under
``workspace/parametric``.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_path,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "22d1f016cb3d"
PROTOTYPE_PATH = (
    Path(__file__).resolve().parents[1] / "workspace" / "parametric" / "prototype.py"
)
ROOT = find_root(__file__)


def _load():
    assert PROTOTYPE_PATH.exists(), "boundary-palette prototype has not been implemented"
    spec = importlib.util.spec_from_file_location(
        "boundary_palette_prototype", PROTOTYPE_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_source() -> str:
    for line in canonical_path(ROOT).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("selected canonical source not found")


def _block_witness() -> list[list[int]]:
    grid = [[0] * 7 for _ in range(7)]
    for row in range(1, 6):
        for col in range(1, 6):
            grid[row][col] = 5
    return grid


def test_parameter_contract_and_default_preserve_canonical_setting():
    prototype = _load()
    assert prototype.ALLOWED_BOUNDARY_PALETTES == (
        "ends1_edges4",
        "ends4_edges1",
    )
    assert prototype.DEFAULT_BOUNDARY_PALETTE == "ends1_edges4"
    assert prototype.choose_boundary_palette(18) == "ends1_edges4"
    assert prototype.choose_boundary_palette(19) == "ends4_edges1"
    assert prototype.choose_boundary_palette(20) == "ends1_edges4"
    for bad_seed in (True, False, 1.0, 1.75, "1"):
        with pytest.raises(TypeError, match="seed"):
            prototype.choose_boundary_palette(bad_seed)


def test_default_racket_is_byte_exact_canonical_and_hash_pinned():
    prototype = _load()
    source = prototype.racket_source("ends1_edges4", root=ROOT)
    assert source == _canonical_source()
    assert prototype.normalized_hash(source) == "2219db85ca5f"


def test_swapped_racket_and_python_exchange_only_end_and_edge_colors():
    prototype = _load()
    canonical_source = prototype.racket_source("ends1_edges4", root=ROOT)
    swapped_source = prototype.racket_source("ends4_edges1", root=ROOT)
    assert swapped_source != canonical_source
    assert prototype.normalized_hash(swapped_source) != prototype.normalized_hash(
        canonical_source
    )

    grid = _block_witness()
    canonical = prototype.python_transform(grid, "ends1_edges4")
    swapped = prototype.python_transform(grid, "ends4_edges1")
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            if grid[row][col] != 5:
                assert canonical[row][col] == swapped[row][col] == grid[row][col]
            elif canonical[row][col] == 2:
                assert swapped[row][col] == 2
            elif canonical[row][col] == 1:
                assert swapped[row][col] == 4
            else:
                assert canonical[row][col] == 4
                assert swapped[row][col] == 1


def test_episode_uses_one_palette_and_every_pair_refutes_alternative():
    prototype = _load()
    for mode, seed in {"ends1_edges4": 18, "ends4_edges1": 19}.items():
        episode = prototype.build_episode(root=ROOT, seed=seed)
        assert episode["parameter"] == {"boundary_palette": mode}
        assert len(episode["train"]) == 4
        assert len(episode["test"]) == 1
        alternative = (
            "ends4_edges1" if mode == "ends1_edges4" else "ends1_edges4"
        )
        for pair in [*episode["train"], *episode["test"]]:
            assert pair["output"] == prototype.python_transform(pair["input"], mode)
            assert pair["output"] != prototype.python_transform(
                pair["input"], alternative
            )


def test_public_challenge_hides_parameter_rule_source_and_query_answer():
    prototype = _load()
    public = prototype.public_challenge(prototype.build_episode(root=ROOT, seed=19))
    payload = json.dumps(public, sort_keys=True)
    assert "parameter" not in public
    assert "boundary_palette" not in payload
    assert "racket" not in payload.lower()
    assert all("output" in pair for pair in public["train"])
    assert public["test"] and all("output" not in pair for pair in public["test"])


def test_retained_racket_files_equal_materialized_sources():
    prototype = _load()
    for mode in prototype.ALLOWED_BOUNDARY_PALETTES:
        path = prototype.rule_path(mode)
        assert path.read_text(encoding="utf-8") == prototype.racket_source(
            mode, root=ROOT
        )



def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def test_episode_accepts_independent_counts_and_four_distinct_queries():
    """Catch fixed 4+1 slicing or query cloning when counts become configurable."""
    prototype = _load()
    for mode, seed in {"ends1_edges4": 18, "ends4_edges1": 19}.items():
        episode = prototype.build_episode(
            root=ROOT,
            seed=seed,
            demo_count=3,
            query_count=4,
        )
        assert episode["parameter"] == {"boundary_palette": mode}
        assert episode["demo_count"] == 3
        assert episode["query_count"] == 4
        assert len(episode["train"]) == 3
        assert len(episode["test"]) == 4

        pairs = [*episode["train"], *episode["test"]]
        assert len({_grid_key(pair["input"]) for pair in pairs}) == 7
        alternative = (
            "ends4_edges1" if mode == "ends1_edges4" else "ends1_edges4"
        )
        for pair in pairs:
            assert pair["output"] == prototype.python_transform(pair["input"], mode)
            assert pair["output"] != prototype.python_transform(
                pair["input"], alternative
            )


@pytest.mark.parametrize("field,bad", [("demo_count", True), ("demo_count", 1.0), ("demo_count", "1"), ("query_count", False), ("query_count", 2.5), ("query_count", "2")])
def test_episode_rejects_non_literal_integer_counts(field, bad):
    """Catch bool/float/string aliases entering the deterministic pair schedule."""
    prototype = _load()
    kwargs = {"demo_count": 3, "query_count": 4, field: bad}
    with pytest.raises(TypeError, match=field):
        prototype.build_episode(root=ROOT, seed=18, **kwargs)


@pytest.mark.parametrize("field,bad", [("demo_count", 0), ("demo_count", -1), ("query_count", 0), ("query_count", -2)])
def test_episode_rejects_nonpositive_counts(field, bad):
    """Catch empty demonstration/query splits that cannot form a public episode."""
    prototype = _load()
    kwargs = {"demo_count": 3, "query_count": 4, field: bad}
    with pytest.raises(ValueError, match=field):
        prototype.build_episode(root=ROOT, seed=18, **kwargs)


def test_episode_rejects_requests_beyond_distinct_schedule_capacity():
    """Catch silent truncation or pair reuse when a request exceeds support."""
    prototype = _load()
    with pytest.raises(ValueError, match="available|capacity|schedule"):
        prototype.build_episode(root=ROOT, seed=18, demo_count=100, query_count=1)


def test_public_projection_id_ignores_private_fields_and_query_answers():
    """Catch public IDs that encode setting, seed, program, or hidden labels."""
    prototype = _load()
    episode = prototype.build_episode(
        root=ROOT,
        seed=18,
        demo_count=3,
        query_count=4,
    )
    expected_public = prototype.public_challenge(episode)
    expected_bytes = public_challenge_bytes(expected_public)
    expected_id = public_challenge_id(expected_public)

    changed = deepcopy(episode)
    changed["seed"] = 999
    changed["parameter"] = {"boundary_palette": "private-mutated-value"}
    changed["racket_text"] = "private program"
    for pair in changed["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]

    changed_public = prototype.public_challenge(changed)
    assert public_challenge_bytes(changed_public) == expected_bytes
    assert public_challenge_id(changed_public) == expected_id


@pytest.mark.parametrize(
    "split,pair_index,field",
    [("train", 0, "input"), ("train", 0, "output"), ("test", 0, "input")],
)
def test_each_visible_public_channel_changes_planned_id(split, pair_index, field):
    """Catch a writer ID that omits any model-visible challenge channel."""
    prototype = _load()
    episode = prototype.build_episode(
        root=ROOT,
        seed=18,
        demo_count=3,
        query_count=4,
    )
    public = prototype.public_challenge(episode)
    baseline = prototype.plan_public_exports({"private-a": public})[0]

    changed = deepcopy(public)
    changed[split][pair_index][field][0][0] = (
        changed[split][pair_index][field][0][0] + 1
    ) % 10
    mutated = prototype.plan_public_exports({"private-a": changed})[0]
    assert mutated["public_id"] != baseline["public_id"]
    assert mutated["filename"] != baseline["filename"]


def test_public_export_plan_is_sorted_order_independent_and_duplicate_safe(tmp_path):
    """Catch hidden-setting enumeration leaks and duplicate public payload writes."""
    prototype = _load()
    canonical = prototype.public_challenge(
        prototype.build_episode(
            root=ROOT,
            seed=18,
            demo_count=3,
            query_count=4,
        )
    )
    swapped = prototype.public_challenge(
        prototype.build_episode(
            root=ROOT,
            seed=19,
            demo_count=3,
            query_count=4,
        )
    )

    forward = prototype.plan_public_exports(
        {"ends1_edges4": canonical, "ends4_edges1": swapped}
    )
    reverse = prototype.plan_public_exports(
        {"ends4_edges1": swapped, "ends1_edges4": canonical}
    )
    assert forward == reverse
    assert [row["public_id"] for row in forward] == sorted(
        row["public_id"] for row in forward
    )
    for row in forward:
        assert row["filename"] == f"challenge-{row['public_id']}.json"
        assert "ends" not in row["filename"]
        assert row["payload"] == public_challenge_bytes(
            {"ends1_edges4": canonical, "ends4_edges1": swapped}[
                row["private_key"]
            ]
        )

    written = prototype.write_public_exports(
        tmp_path,
        {"ends4_edges1": swapped, "ends1_edges4": canonical},
    )
    assert written == forward
    assert sorted(path.name for path in tmp_path.iterdir()) == [
        row["filename"] for row in forward
    ]
    assert all((tmp_path / row["filename"]).read_bytes() == row["payload"] for row in forward)

    duplicate_dir = tmp_path / "duplicates"
    with pytest.raises(ValueError, match="duplicate"):
        prototype.write_public_exports(
            duplicate_dir,
            {"private-a": canonical, "private-b": deepcopy(canonical)},
        )
    assert not duplicate_dir.exists() or not list(duplicate_dir.iterdir())
