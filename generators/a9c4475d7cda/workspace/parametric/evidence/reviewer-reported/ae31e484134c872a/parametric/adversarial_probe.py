#!/usr/bin/env python3
"""Bounded adversarial probe for the task-local panel-threshold prototype."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import find_root, load_selected_generator

HERE = Path(__file__).resolve()
ROOT = find_root(HERE)
PROTOTYPE_PATH = (
    ROOT
    / "generators"
    / "a9c4475d7cda"
    / "workspace"
    / "parametric"
    / "prototype.py"
)


def load_prototype():
    spec = importlib.util.spec_from_file_location("panel_threshold_adversarial", PROTOTYPE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load prototype")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def expect_error(fn, error_types=(TypeError, ValueError)):
    try:
        fn()
    except error_types:
        return
    raise AssertionError("expected validation error")


def main() -> int:
    prototype = load_prototype()
    generator, _, generator_sha256 = load_selected_generator(prototype.TASK_ID, root=ROOT)
    seed_cases = []
    total_pairs = 0

    for seed in range(32):
        demos = 1 + (seed % 8)
        queries = 1 + ((seed * 3) % 8)
        episode = prototype.build_claimed_episode(
            seed,
            demos=demos,
            queries=queries,
            root=ROOT,
        )
        threshold = 2 + (seed % 2)
        assert episode["parameters"] == {"min_panel_count": threshold}
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == queries
        pairs = episode["train"] + episode["test"]
        keys = {
            json.dumps(pair["input"], sort_keys=True, separators=(",", ":"))
            for pair in pairs
        }
        assert len(keys) == len(pairs)
        for pair in pairs:
            assert generator.self_check(pair["input"]) == []
            counts = {count for row in prototype.panel_counts(pair["input"]) for count in row}
            assert {2, 3} <= counts
            assert pair["output"] == prototype.apply_python(pair["input"], threshold)
            assert pair["output"] != prototype.apply_python(pair["input"], 5 - threshold)
        total_pairs += len(pairs)
        seed_cases.append({"seed": seed, "demos": demos, "queries": queries})

    public_episode = prototype.build_claimed_episode(
        51,
        min_panel_count=3,
        demos=8,
        queries=8,
        root=ROOT,
    )
    public_bytes = prototype.public_bytes(public_episode)
    public_id = prototype.public_id(public_episode)
    assert public_id == hashlib.sha256(public_bytes).hexdigest()

    private_mutation = deepcopy(public_episode)
    private_mutation["seed"] = 10**9
    private_mutation["parameters"]["min_panel_count"] = 2
    private_mutation["program_solution"] = "not visible"
    for pair in private_mutation["test"]:
        pair["output"] = [[9, 9, 9], [9, 9, 9], [9, 9, 9]]
    assert prototype.public_bytes(private_mutation) == public_bytes
    assert prototype.public_id(private_mutation) == public_id

    visible_mutation = deepcopy(public_episode)
    visible_mutation["train"][0]["output"][0][0] ^= 1
    assert prototype.public_bytes(visible_mutation) != public_bytes
    assert prototype.public_id(visible_mutation) != public_id

    malformed_grids = [
        [],
        [[0], [0, 0]],
        [[True]],
        [[0, 0], [0, 0]],
        [
            [8, 8, 8, 8, 8],
            [8, 8, 8, 8, 8],
            [8, 8, 8, 8, 8],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ],
    ]
    for grid in malformed_grids:
        expect_error(lambda grid=grid: prototype.panel_counts(grid), (ValueError,))

    canonical = prototype.canonical_program(ROOT)
    tampered = canonical.replace(
        prototype.CANONICAL_THRESHOLD_FORM,
        prototype.CANONICAL_THRESHOLD_FORM.replace("                                 2)", "                                 4)"),
        1,
    )
    expect_error(lambda: prototype.render_program(tampered, 2), (ValueError,))

    with tempfile.TemporaryDirectory() as temporary:
        occupied = Path(temporary) / "occupied"
        occupied.mkdir()
        (occupied / "sentinel").write_text("do not overwrite", encoding="utf-8")
        expect_error(
            lambda: prototype.materialize(
                occupied,
                seed=9,
                demos=1,
                queries=1,
                root=ROOT,
            ),
            (ValueError,),
        )
        assert (occupied / "sentinel").read_text(encoding="utf-8") == "do not overwrite"

    programs = {
        threshold: prototype.render_program(canonical, threshold)
        for threshold in prototype.ALLOWED_MIN_PANEL_COUNTS
    }
    racket_cases = []
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        for seed, threshold, demos, queries in ((901, 2, 1, 8), (902, 3, 8, 1)):
            episode = prototype.build_claimed_episode(
                seed,
                min_panel_count=threshold,
                demos=demos,
                queries=queries,
                root=ROOT,
            )
            rival = 5 - threshold
            for pair in episode["train"] + episode["test"]:
                selected = prototype.execute(bridge, programs[threshold], pair["input"])
                other = prototype.execute(bridge, programs[rival], pair["input"])
                assert selected == pair["output"]
                assert other != pair["output"]
            racket_cases.append(
                {
                    "seed": seed,
                    "threshold": threshold,
                    "demos": demos,
                    "queries": queries,
                }
            )
        runtime_identity = bridge.runtime_identity

    result = {
        "schema": "a9c4475d7cda-parametric-adversarial-probe-v1",
        "status": "pass",
        "generator_sha256": generator_sha256,
        "seed_sweep": {
            "cases": len(seed_cases),
            "pairs": total_pairs,
            "demos_range": [1, 8],
            "queries_range": [1, 8],
            "seeds": seed_cases,
        },
        "checks": {
            "lawful_distinct_inputs": True,
            "both_thresholds_distinguished_on_every_pair": True,
            "private_fields_and_query_answers_do_not_change_public_id": True,
            "visible_demo_change_changes_public_id": True,
            "public_id_is_sha256_of_exact_visible_bytes": True,
            "malformed_grids_rejected": len(malformed_grids),
            "tampered_canonical_anchor_rejected": True,
            "nonempty_output_refused_without_overwrite": True,
            "racket_boundary_cases_match_python_and_refute_rival": True,
        },
        "racket_cases": racket_cases,
        "racket_runtime": runtime_identity,
        "findings": [],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
