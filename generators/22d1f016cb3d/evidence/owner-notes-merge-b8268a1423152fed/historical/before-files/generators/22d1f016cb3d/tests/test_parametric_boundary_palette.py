"""Prototype-only tests for a fixed-per-episode boundary palette.

The selected production generator and canonical Racket authority stay fixed to
``ends1_edges4``. This file exercises only the isolated prototype under
``workspace/parametric``.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root


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
