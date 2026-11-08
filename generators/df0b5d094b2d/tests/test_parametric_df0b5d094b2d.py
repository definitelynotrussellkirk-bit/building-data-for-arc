"""Focused contract tests for the proposed rectangle move-distance family."""
from __future__ import annotations

from functools import cache
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "df0b5d094b2d"
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
    return _load(HOME / "prototype.py", "_df0b5d094b2d_parametric")


@cache
def adapter():
    return _load(HOME / "adapter.py", "_df0b5d094b2d_adapter")


def _all_inputs(public):
    return [pair["input"] for pair in public["train"] + public["test"]]


def test_default_program_is_exact_canonical_and_both_distances_match_racket():
    p = prototype()
    canonical = p.canonical_record(root=ROOT)["program_solution"]
    assert p.program_for(1, root=ROOT) == canonical
    assert p.program_for(2, root=ROOT) != canonical

    from arc_repl.racket_bridge import RacketBridge

    grids = [row["input"] for row in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)]
    grids += [p.sample_input(61, index, root=ROOT) for index in range(4)]
    grids.append(p.sample_input(61, 1003, size=(30, 30), root=ROOT))
    with RacketBridge(max_calls_before_restart=256) as bridge:
        for grid in grids:
            # Canonical inputs are guaranteed for one step; custom inputs are safe for both.
            distances = (1,) if grid in grids[: len(canonical_pairs(TASK_ID, root=ROOT, labeled_only=True))] else p.MOVE_DISTANCES
            for distance in distances:
                assert p.execute(bridge, p.program_for(distance, root=ROOT), grid) == p.transform(
                    grid, distance
                )


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("distance", [1, 2])
def test_episode_supports_counts_distinct_queries_and_demo_only_identification(demos, distance):
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=256) as bridge:
        public, private = p.generate_episode(
            500 + demos,
            bridge,
            move_distance=distance,
            demos=demos,
            queries=4,
            root=ROOT,
        )
    assert len(public["train"]) == demos
    assert len(public["test"]) == 4
    assert private["parameter"] == {"move_distance": distance}
    assert private["surviving_settings"] == [{"move_distance": distance}]
    assert len(private["query_answers"]) == 4
    assert len({p.grid_digest(grid) for grid in _all_inputs(public)}) == demos + 4
    p.verify_episode(public, private, root=ROOT)


def test_query_schedule_has_substantive_large_cases_and_exact_30x30():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        public, _ = p.generate_episode(71, bridge, demos=3, queries=4, root=ROOT)
    profiles = [p.input_profile(pair["input"]) for pair in public["test"]]
    assert [(row["grid_h"], row["grid_w"]) for row in profiles] == [
        (10, 10),
        (16, 20),
        (24, 26),
        (30, 30),
    ]
    assert [row["shape_count"] for row in profiles] == [2, 3, 4, 4]
    assert profiles[-1]["occupied_cells"] >= 60
    assert profiles[-1]["span_rows"] >= 20
    assert profiles[-1]["span_cols"] >= 20


def test_sequential_projection_and_adversarial_corruption_fail_closed():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        public, private = p.generate_episode(79, bridge, demos=3, queries=4, root=ROOT)
    views = p.sequential_views(public)
    first = {"train": public["train"], "test": [public["test"][0]]}
    assert public_challenge_bytes(views[0]) == public_challenge_bytes(first)
    assert public_challenge_id(views[0]) == public_challenge_id(first)

    corrupted = dict(private)
    corrupted["query_answers"] = [[row[:] for row in grid] for grid in private["query_answers"]]
    corrupted["query_answers"][0][0][0] = (corrupted["query_answers"][0][0][0] + 1) % 10
    with pytest.raises(ValueError, match="query answer"):
        p.verify_episode(public, corrupted, root=ROOT)
    leaked = {"train": public["train"], "test": [dict(public["test"][0], output=[[7]])]}
    with pytest.raises(ValueError, match="public query"):
        p.validate_public(leaked)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (3, 0), (3, 9), (True, 4)])
def test_invalid_counts_reject(demos, queries):
    with pytest.raises(ValueError):
        prototype().validate_counts(demos, queries)


def test_promotion_adapter_matches_prototype():
    p = prototype()
    a = adapter()
    settings = {"move_distance": 2}
    assert a.program(settings) == p.program_for(2, root=ROOT)
    episode = a.generate(19, settings, demos=3, queries=4)
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4
    assert all(pair["output"] == p.transform(pair["input"], 2) for pair in episode["train"] + episode["test"])


def test_public_writer_uses_exact_canonical_bytes(tmp_path):
    p = prototype()
    public = {
        "train": [{"input": [[7]], "output": [[1]]}],
        "test": [{"input": [[8]]}],
    }
    path = tmp_path / "challenge.json"
    p._write_public(path, public)
    assert path.read_bytes() == public_challenge_bytes(public)
    assert p.digest(path.read_bytes()) == public_challenge_id(public)
