"""Focused contract and adversarial tests for c181f41a09f0's parametric family."""
from __future__ import annotations

from copy import deepcopy
from functools import cache
import importlib.util
from pathlib import Path

import pytest

from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "c181f41a09f0"
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
    return _load(HOME / "prototype.py", "_c181f41a09f0_parametric")


@cache
def adapter():
    return _load(HOME / "adapter.py", "_c181f41a09f0_adapter")


@cache
def audit_tool():
    return _load(HOME / "adversarial_audit.py", "_c181f41a09f0_audit")


def _all_inputs(public):
    return [pair["input"] for pair in public["train"] + public["test"]]


def _destinations(rows):
    return {tuple(row["bbox"]): row["destination_start"] for row in rows if row["marked"]}


def test_default_program_is_exact_canonical_and_count_steps_match_protected_racket():
    p = prototype()
    canonical = p.canonical_record(root=ROOT)["program_solution"]
    assert p.program_for("opposite_end", root=ROOT) == canonical
    assert p.program_for("marker_count_steps", root=ROOT) != canonical

    grids = [row["input"] for row in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)]
    grids += [p.sample_input(73, index, root=ROOT) for index in range(4)]
    causal = p.sample_input(
        73,
        1003,
        size=(30, 30),
        cap_sizes=(1, 2, 3),
        decoy_count=6,
        root=ROOT,
    )
    grids.append(causal)

    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=256) as bridge:
        for grid in grids:
            for rule in p.TRAVEL_RULES:
                assert p.execute(bridge, p.program_for(rule, root=ROOT), grid) == p.transform(
                    grid, rule
                )
        actual = p.execute(bridge, p.program_for("marker_count_steps", root=ROOT), causal)
        wrong = p.execute(bridge, p.counterfactual_program(root=ROOT), causal)
    assert actual != wrong


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("rule", ["opposite_end", "marker_count_steps"])
def test_episode_supports_counts_distinct_queries_and_demo_only_identification(demos, rule):
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=256) as bridge:
        public, private = p.generate_episode(
            300 + demos,
            bridge,
            travel_rule=rule,
            demos=demos,
            queries=4,
            root=ROOT,
        )
    assert len(public["train"]) == demos
    assert len(public["test"]) == 4
    assert private["parameter"] == {"travel_rule": rule}
    assert private["surviving_settings"] == [{"travel_rule": rule}]
    assert len(private["query_answers"]) == 4
    assert all(set(pair) == {"input"} for pair in public["test"])
    assert len({p.grid_digest(grid) for grid in _all_inputs(public)}) == demos + 4
    p.verify_episode(public, private, root=ROOT)


def test_query_bank_is_count_independent_shuffled_and_covers_stress_roles():
    p = prototype()
    demos2, queries1 = p.episode_inputs(41, 2, 1, root=ROOT)
    demos6, queries4 = p.episode_inputs(41, 6, 4, root=ROOT)
    assert demos2 == demos6[:2]
    assert queries1 == queries4[:1]

    profiles = [p.input_profile(grid) for grid in queries4]
    assert sorted((row["grid_h"], row["grid_w"]) for row in profiles) == sorted(p.QUERY_SIZES)
    assert {row["orientation"] for row in profiles} == {"horizontal", "vertical"}
    assert {row["source_side"] for row in profiles} == {"low", "high"}
    largest = next(row for row in profiles if (row["grid_h"], row["grid_w"]) == (30, 30))
    assert largest["strip_count"] == 4
    assert largest["marked_count"] == 3
    assert largest["decoy_count"] == 6

    # The source schedule is shuffled by seed rather than leaking a fixed query position.
    _, other_queries = p.episode_inputs(42, 2, 4, root=ROOT)
    assert [(len(g), len(g[0])) for g in queries4] != [(len(g), len(g[0])) for g in other_queries]


def test_two_demo_minimum_crosses_marker_count_against_the_same_strip_ranks():
    p = prototype()
    for seed in range(32):
        demos, _ = p.episode_inputs(seed, 2, 1, root=ROOT)
        rows = [p.strip_intermediates(grid, "marker_count_steps") for grid in demos]
        masks = [[row["marked"] for row in scene] for scene in rows]
        counts = [[row["marker_count"] for row in scene if row["marked"]] for scene in rows]
        assert masks[0] == masks[1]
        assert set(counts[0]) == set(counts[1]) == {1, 2, 3}
        assert counts[0] != counts[1]
        assert {
            (row["orientation"], row["source_side"])
            for scene in rows
            for row in scene
        } == {("horizontal", "low")}

        # At least one two-cell cap is deliberately non-contiguous, so its span
        # cannot substitute for counting marker cells.
        records = p._strip_records(demos[0])
        count_two = next(record for record in records if record["marker_count"] == 2)
        offsets = sorted(c - count_two["bbox"][1] for _, c in count_two["marker_cells"])
        assert offsets == [0, 2]


def test_marker_count_is_a_real_crossed_intermediate_not_a_position_or_color_shortcut():
    p = prototype()
    base_kwargs = dict(seed=911, index=3, size=(30, 30), root=ROOT)
    counts_a = p.sample_input(**base_kwargs, cap_sizes=(1, 2, 3), cap_color=2, decoy_count=2)
    counts_b = p.sample_input(**base_kwargs, cap_sizes=(2, 1, 3), cap_color=2, decoy_count=2)
    nuisance = p.sample_input(**base_kwargs, cap_sizes=(1, 2, 3), cap_color=8, decoy_count=6)

    rows_a = p.strip_intermediates(counts_a, "marker_count_steps")
    rows_b = p.strip_intermediates(counts_b, "marker_count_steps")
    rows_nuisance = p.strip_intermediates(nuisance, "marker_count_steps")

    assert [row["bbox"] for row in rows_a] == [row["bbox"] for row in rows_b]
    assert [row["source_side"] for row in rows_a] == [row["source_side"] for row in rows_b]
    assert _destinations(rows_a) != _destinations(rows_b)
    assert _destinations(rows_a) == _destinations(rows_nuisance)
    assert p.transform(counts_a, "marker_count_steps") != p.transform(
        counts_a, "opposite_end"
    )


def test_sequential_projection_and_strict_verifier_reject_corruption_and_forgery():
    p = prototype()
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge() as bridge:
        public, private = p.generate_episode(59, bridge, demos=3, queries=4, root=ROOT)

    views = p.sequential_views(public, presentation_seed=17)
    assert len(views) == 4
    assert all(set(view) == {"train", "test"} and len(view["test"]) == 1 for view in views)
    assert {public_challenge_id(view) for view in views} == {
        public_challenge_id({"train": public["train"], "test": [pair]})
        for pair in public["test"]
    }
    assert p.sequential_views(public, presentation_seed=17)[0] == views[0]

    corrupted = deepcopy(private)
    corrupted["query_answers"][0][0][0] = (corrupted["query_answers"][0][0][0] + 1) % 10
    with pytest.raises(ValueError, match="query answer"):
        p.verify_episode(public, corrupted, root=ROOT)

    forged = deepcopy(private)
    forged["program_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="program hash"):
        p.verify_episode(public, forged, root=ROOT)

    duplicate = deepcopy(public)
    duplicate["test"][0]["input"] = deepcopy(duplicate["train"][0]["input"])
    with pytest.raises(ValueError, match="duplicate"):
        p.verify_episode(duplicate, private, root=ROOT)

    leaked = {"train": public["train"], "test": [dict(public["test"][0], output=[[7]])]}
    with pytest.raises(ValueError, match="public query"):
        p.validate_public(leaked)

    non_exact = deepcopy(public)
    non_exact["test"][0]["input"][0][0] = True
    with pytest.raises(ValueError, match="exact ARC colors"):
        p.validate_public(non_exact)


@pytest.mark.parametrize("demos,queries", [(1, 4), (7, 4), (3, 0), (3, 5), (True, 4)])
def test_invalid_counts_reject(demos, queries):
    with pytest.raises(ValueError):
        prototype().validate_counts(demos, queries)


def test_promotion_adapter_matches_prototype():
    p = prototype()
    a = adapter()
    settings = {"travel_rule": "marker_count_steps"}
    assert a.program(settings) == p.program_for("marker_count_steps", root=ROOT)
    episode = a.generate(13, settings, demos=3, queries=4)
    assert len(episode["train"]) == 3 and len(episode["test"]) == 4
    assert all(
        pair["output"] == p.transform(pair["input"], "marker_count_steps")
        for pair in episode["train"] + episode["test"]
    )


def test_reusable_adversarial_audit_finds_no_shortcut_or_boundary_failures():
    report = audit_tool().run_python_audit(seed_count=8)
    assert report["shortcut_cases"] > 0
    assert report["boundary_cases"] > 0
    assert report["failures"] == []


def test_public_writer_uses_exact_canonical_bytes(tmp_path):
    p = prototype()
    public = {
        "train": [{"input": [[0]], "output": [[7]]}],
        "test": [{"input": [[1]]}],
    }
    path = tmp_path / "challenge.json"
    p._write_public(path, public)
    assert path.read_bytes() == public_challenge_bytes(public)
    assert p.digest(path.read_bytes()) == public_challenge_id(public)
