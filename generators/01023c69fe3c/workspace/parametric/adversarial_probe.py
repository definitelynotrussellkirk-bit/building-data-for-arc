#!/usr/bin/env python3
"""Bounded adversarial audit for the 01023c69fe3c parametric family."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

from reviewer_support import public_challenge_bytes, public_challenge_id

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "prototype.py"
FINDINGS_AND_REPAIRS = (
    {
        "finding": "A global cue/ring color swap preserved selected payload positions and was not a causal crossed control.",
        "repair": "Swap only the true interior cue cell and ring decoy cell while holding remote payload positions and counts fixed.",
        "regression": "test_crossed_controls_change_only_the_intended_semantic_factor",
    },
    {
        "finding": "The minimum lesson could otherwise admit a seed-dependent fixed-color shortcut.",
        "repair": "First two demonstrations use different cue colors and jointly cover all six decor colors in crossed semantic roles.",
        "regression": "test_two_demo_lesson_refutes_relevant_bypasses_across_fresh_seeds",
    },
    {
        "finding": "A payload could occupy an expanded-selector corner before the intended ring decoy and make the wrong intermediate recover the true cue.",
        "repair": "Reserve the complete one-cell-expanded selector zone from payload placement.",
        "regression": "test_expanded_selector_zone_contains_no_early_payload_before_ring_decoy",
    },
    {
        "finding": "A cue-colored crosshair nuisance could appear inside the expanded selector before the ring decoy.",
        "repair": "Keep every crosshair nuisance outside the complete one-cell-expanded selector zone.",
        "regression": "test_crosshair_nuisance_stays_outside_wrong_expanded_selector_zone",
    },
)


def _load():
    spec = importlib.util.spec_from_file_location("_audit_01023c69fe3c", SOURCE)
    if spec is None or spec.loader is None:
        raise ImportError(SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expect_reject(call, contains: str) -> None:
    try:
        call()
    except ValueError as error:
        if contains not in str(error):
            raise AssertionError(f"wrong rejection: {error}") from error
    else:
        raise AssertionError(f"expected rejection containing {contains!r}")


def audit(seeds: int, racket_seeds: int) -> dict[str, Any]:
    p = _load()
    if type(seeds) is not int or not 1 <= seeds <= 512:
        raise ValueError("seeds must be in 1..512")
    if type(racket_seeds) is not int or not 1 <= racket_seeds <= min(seeds, 32):
        raise ValueError("racket-seeds must be in 1..min(seeds,32)")

    episodes_checked = 0
    pairs_checked = 0
    certificate_checks = 0
    crossed_controls = 0
    privacy_mutations = 0
    corruption_rejections = 0
    setting_comparisons = 0
    wrong_intermediate_checks = 0
    query_prefix_checks = 0
    stress_30x30 = 0
    public_ids: set[str] = set()

    for seed in range(seeds):
        by_request: dict[tuple[str, int, int], dict[str, Any]] = {}
        for demos, queries in ((2, 1), (2, 4), (6, 1), (6, 4)):
            for mode in p.MODES:
                episode = p.generate_episode(seed, mode, demos=demos, queries=queries)
                p.verify_episode(episode)
                assert episode["certificate"]["all_rivals_refuted"]
                assert episode["certificate"]["survivors"] == [{"mode": mode}]
                episodes_checked += 1
                pairs_checked += demos + queries
                certificate_checks += len(episode["certificate"]["rival_checks"])
                by_request[(mode, demos, queries)] = episode

            canonical = by_request[("canonical", demos, queries)]
            alternate = by_request[("interior_cue", demos, queries)]
            assert [pair["input"] for pair in canonical["train"] + canonical["test"]] == [
                pair["input"] for pair in alternate["train"] + alternate["test"]
            ]
            assert all(
                left["output"] != right["output"]
                for left, right in zip(canonical["train"], alternate["train"])
            )
            setting_comparisons += demos + queries

        # Demo count and query count are independent; query presentation is a
        # prefix of the same privately shuffled four-query bank.
        assert by_request[("canonical", 2, 1)]["test"] == by_request[("canonical", 6, 4)]["test"][:1]
        assert by_request[("interior_cue", 2, 4)]["test"] == by_request[("interior_cue", 6, 4)]["test"]
        query_prefix_checks += 2

        lesson = by_request[("interior_cue", 2, 4)]
        demo_profiles = [p.scene_profile(pair["input"]) for pair in lesson["train"]]
        assert len({profile["cue_color"] for profile in demo_profiles}) == 2
        assert set().union(*(set(profile["decor_counts"]) for profile in demo_profiles)) == set(p._DECOR_COLORS)

        for pair in lesson["train"] + lesson["test"]:
            grid = pair["input"]
            profile = p.scene_profile(grid)
            assert len(profile["cue_candidates"]) == 1
            assert len(profile["ring_decoys"]) == 1
            assert profile["cue_color"] != profile["ring_decoy_color"]
            assert p.wrong_intermediate_transform(grid) != p.transform(grid, "interior_cue")
            wrong_intermediate_checks += 1

        control = lesson["train"][0]["input"]
        intended = p.transform(control, "interior_cue")
        changed = p.swap_cue_and_ring_colors(control)
        nuisance = p.swap_nuisance_colors(control)
        assert p.scene_profile(changed)["anchors"] == p.scene_profile(control)["anchors"]
        assert p.transform(changed, "interior_cue") != intended
        assert p.transform(nuisance, "interior_cue") == intended
        crossed_controls += 2

        stress = next(
            pair["input"] for pair in lesson["test"]
            if (len(pair["input"]), len(pair["input"][0])) == (30, 30)
        )
        stress_profile = p.scene_profile(stress)
        assert stress_profile["anchor_span_rows"] >= 20
        assert stress_profile["anchor_span_cols"] >= 20
        assert stress_profile["nonzero_count"] >= 30
        stress_30x30 += 1

        first = p.public_turn(lesson, 0)
        before = public_challenge_bytes(first)
        public_ids.add(public_challenge_id(first))
        mutated = copy.deepcopy(lesson)
        mutated["settings"] = {"mode": "canonical"}
        mutated["program_solution"] = "private mutation"
        mutated["program_sha256"] = "0" * 64
        mutated["certificate"] = {"private": True}
        mutated["test"][0]["output"] = [[9]]
        mutated["test"][1:] = [{"input": [[9]], "output": [[8]], "future": True}]
        assert public_challenge_bytes(p.public_turn(mutated, 0)) == before
        privacy_mutations += 6

        corrupt = copy.deepcopy(lesson)
        corrupt["train"][0]["output"] = [[0]]
        _expect_reject(lambda: p.verify_episode(corrupt), "label")
        duplicate = copy.deepcopy(lesson)
        duplicate["test"][0]["input"] = copy.deepcopy(duplicate["train"][0]["input"])
        _expect_reject(lambda: p.verify_episode(duplicate), "distinct")
        malformed = copy.deepcopy(lesson)
        malformed["test"][0]["input"][0][0] = True
        _expect_reject(lambda: p.verify_episode(malformed), "grid")
        corruption_rejections += 3

    # Protected-Racket replay on bounded fresh episodes, including 30x30 and
    # the deliberately wrong intermediate.
    from arc_repl.racket_bridge import RacketBridge

    racket_evaluations = 0
    with RacketBridge(max_calls_before_restart=256) as bridge:
        identity = bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            raise ValueError("audit requires protected Racket")
        for seed in range(racket_seeds):
            for mode in p.MODES:
                episode = p.generate_episode(10_000 + seed, mode, demos=2, queries=4)
                for pair in episode["train"] + episode["test"]:
                    assert p.execute(bridge, episode["program_solution"], pair["input"]) == pair["output"]
                    racket_evaluations += 1
            grid = p.sample_scene(10_000 + seed, "query", 3)
            right = p.execute(bridge, p.program_for("interior_cue"), grid)
            wrong = p.execute(bridge, p.wrong_intermediate_program(), grid)
            assert right == p.transform(grid, "interior_cue")
            assert wrong == p.wrong_intermediate_transform(grid)
            assert wrong != right
            racket_evaluations += 2

    return {
        "schema": "01023c69fe3c-adversarial-audit-v1",
        "status": "passed",
        "task_id": p.TASK_ID,
        "source": {"path": str(SOURCE.relative_to(p.ROOT)), "sha256": _sha(SOURCE)},
        "bounds": {"python_seeds": seeds, "racket_seeds": racket_seeds},
        "checks": {
            "episodes_checked": episodes_checked,
            "labelled_pairs_checked": pairs_checked,
            "finite_rival_checks": certificate_checks,
            "matched_setting_comparisons": setting_comparisons,
            "wrong_intermediate_cases": wrong_intermediate_checks,
            "crossed_controls": crossed_controls,
            "query_prefix_checks": query_prefix_checks,
            "substantive_30x30_cases": stress_30x30,
            "first_turn_private_mutations": privacy_mutations,
            "distinct_first_turn_public_ids": len(public_ids),
            "corruption_rejections": corruption_rejections,
            "protected_racket_evaluations": racket_evaluations,
        },
        "racket": {
            key: identity[key]
            for key in (
                "schema", "backend", "protected", "binary_sha256", "prelude_sha256",
                "bridge_sha256", "boot_script_sha256", "candidate_symbol_policy_sha256",
            )
            if key in identity
        },
        "findings_and_repairs": [dict(row) for row in FINDINGS_AND_REPAIRS],
        "limits": (
            "Finite bounded attacks do not prove universal uniqueness. Owner source review, native "
            "qualification/acceptance, and training admission remain separate."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--racket-seeds", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists() or args.out.is_symlink():
        raise FileExistsError(args.out)
    report = audit(args.seeds, args.racket_seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], **report["checks"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
