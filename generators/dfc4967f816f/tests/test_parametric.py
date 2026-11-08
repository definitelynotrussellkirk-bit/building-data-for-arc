"""Focused contract tests for the proposed output-color parametric family."""
from __future__ import annotations

from functools import cache
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import (
    canonical_pairs,
    find_root,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "dfc4967f816f"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID / "workspace" / "parametric"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@cache
def prototype():
    return _load(HOME / "prototype.py", "_dfc4967f816f_parametric")


@cache
def adapter():
    return _load(HOME / "adapter.py", "_dfc4967f816f_adapter")


def _inputs(public):
    return [pair["input"] for pair in public["train"] + public["test"]]


def test_default_program_is_exact_canonical_and_alternate_is_racket_backed():
    p = prototype()
    canonical = p.canonical_record(root=ROOT)["program_solution"]
    assert p.program_for(8, root=ROOT) == canonical
    assert p.program_for(4, root=ROOT) != canonical

    from arc_repl.racket_bridge import RacketBridge

    grids = [row["input"] for row in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)]
    grids += [p.sample_input(91, index, root=ROOT) for index in range(4)]
    with RacketBridge() as bridge:
        for grid in grids:
            for color in p.OUTPUT_COLORS:
                assert p.execute(bridge, p.program_for(color, root=ROOT), grid) == p.transform(
                    grid, color
                )


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("color", [8, 4])
def test_episode_supports_independent_counts_and_demo_only_identification(demos, color):
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=256) as bridge:
        public, private = p.generate_episode(
            700 + demos + color,
            bridge,
            output_color=color,
            demos=demos,
            queries=4,
            root=ROOT,
        )
    assert len(public["train"]) == demos
    assert len(public["test"]) == 4
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert len(private["query_answers"]) == 4
    assert private["parameter"] == {"output_color": color}
    assert private["surviving_settings"] == [{"output_color": color}]
    keys = {p.grid_digest(grid) for grid in _inputs(public)}
    assert len(keys) == demos + 4
    p.verify_episode(public, private, root=ROOT)


def test_four_queries_cover_supported_widths_and_sequential_projection():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        public, private = p.generate_episode(17, bridge, demos=3, queries=4, root=ROOT)
    counts = [p.tile_count(pair["input"]) for pair in public["test"]]
    assert counts == [3, 4, 5, 6]
    assert [len(pair["input"][0]) for pair in public["test"]] == [11, 15, 19, 23]
    assert private["size_limit"] == "3x23; the 3x3-tile grammar cannot form an exact 30x30 grid"

    views = p.sequential_views(public)
    assert len(views) == 4
    assert all(set(view) == {"train", "test"} for view in views)
    assert all(view["train"] == public["train"] for view in views)
    assert [view["test"][0] for view in views] == public["test"]
    first = {"train": public["train"], "test": [public["test"][0]]}
    assert public_challenge_bytes(views[0]) == public_challenge_bytes(first)
    assert public_challenge_id(views[0]) == public_challenge_id(first)


def test_adversarial_corruption_and_invalid_requests_fail_closed():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        public, private = p.generate_episode(23, bridge, demos=3, queries=4, root=ROOT)
    corrupted = dict(private)
    corrupted["query_answers"] = [[row[:] for row in grid] for grid in private["query_answers"]]
    corrupted["query_answers"][0][0][0] = 9
    with pytest.raises(ValueError, match="query answer"):
        p.verify_episode(public, corrupted, root=ROOT)

    leaked = {"train": public["train"], "test": [dict(public["test"][0], output=[[0]])]}
    with pytest.raises(ValueError, match="public query"):
        p.validate_public(leaked)
    for bad in (1, 7, True, 3.0):
        with pytest.raises(ValueError, match="demos"):
            p.validate_counts(bad, 4)
    for bad in (0, 9, True, 4.0):
        with pytest.raises(ValueError, match="queries"):
            p.validate_counts(3, bad)


def test_promotion_adapter_reuses_prototype_and_honors_counts():
    p = prototype()
    a = adapter()
    settings = {"output_color": 4}
    assert a.program(settings) == p.program_for(4, root=ROOT)
    episode = a.generate(31, settings, demos=3, queries=4)
    assert len(episode["train"]) == 3
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == a.program(settings)
    assert all(pair["output"] == p.transform(pair["input"], 4) for pair in episode["train"])
    assert all(pair["output"] == p.transform(pair["input"], 4) for pair in episode["test"])


def test_public_writer_uses_exact_canonical_bytes(tmp_path):
    p = prototype()
    public = {
        "train": [{"input": [[0]], "output": [[8]]}],
        "test": [{"input": [[1]]}],
    }
    path = tmp_path / "challenge.json"
    p._write_public(path, public)
    assert path.read_bytes() == public_challenge_bytes(public)
    assert p.digest(path.read_bytes()) == public_challenge_id(public)
