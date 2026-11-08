#!/usr/bin/env python3
"""Replayable bounded self-audit for e3f1bc75d654's native parametric family.

The audit checks the finite teaching claim without reading query answers, sweeps
supported count boundaries, validates public/private projection and sequential
query reveal, executes both setting programs and all declared rival programs in
protected Racket, and emits one source-bound causal case for native witness
construction.  It is deliberately a bounded audit, not a uniqueness proof.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any, Iterable


_HERE = Path(__file__).resolve().parent
_FAMILY_PATH = _HERE / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_arc_e3f1bc75d654_parametric_audit_family", _FAMILY_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load adjacent prototype: {_FAMILY_PATH}")
family = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = family
_SPEC.loader.exec_module(family)


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _grid_key(grid: list[list[int]]) -> str:
    return json.dumps(grid, separators=(",", ":"))


def _all_inputs(episode: dict[str, Any]) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _canonical_program() -> str:
    from reviewer_support import canonical_path, find_root

    root = find_root(__file__)
    programs: list[str] = []
    for line in canonical_path(root).read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("task_id") == family.TASK_ID:
            programs.append(row["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise RuntimeError("canonical program missing or inconsistent")
    return programs[0]


def _public_projection_invariant(episode: dict[str, Any]) -> bool:
    from reviewer_support import public_challenge_bytes

    private = {
        **copy.deepcopy(episode),
        "settings": {family.PARAMETER_NAME: "pattern_bbox"},
        "program_solution": episode["program_solution"],
        "seed": 123,
        "private_note": "original",
    }
    visible = public_challenge_bytes(private)
    changed = copy.deepcopy(private)
    changed["settings"] = {family.PARAMETER_NAME: "template_interior"}
    changed["program_solution"] = "private replacement"
    changed["seed"] = 999
    changed["private_note"] = "changed"
    for pair in changed["test"]:
        pair["output"] = [[9 for _ in row] for row in pair["output"]]
    return public_challenge_bytes(changed) == visible == family.public_bytes(private)


def _sequential_projection_invariant(episode: dict[str, Any]) -> bool:
    from reviewer_support import public_challenge_bytes, public_challenge_id

    turns = family.sequential_public_turns(episode)
    if len(turns) != len(episode["test"]):
        return False
    for index, turn in enumerate(turns):
        expected = {
            "train": episode["train"],
            "test": [episode["test"][index]],
        }
        expected_public = family.public_challenge(expected)
        if set(turn) != {"turn", "challenge_id", "challenge"}:
            return False
        if turn["turn"] != index + 1 or turn["challenge"] != expected_public:
            return False
        if turn["challenge_id"] != public_challenge_id(expected_public):
            return False
        if public_challenge_bytes(turn["challenge"]) != family.public_bytes(expected):
            return False
        if len(turn["challenge"]["test"]) != 1:
            return False
    return True


def _stress_features(grid: list[list[int]]) -> dict[str, Any]:
    facts = family.analyze_scene(grid)
    if facts["errors"]:
        raise AssertionError("stress scene invalid: " + "; ".join(facts["errors"]))
    height, width = len(grid), len(grid[0])
    boxes = [frame["bbox"] for frame in facts["frames"]]
    occupied = [
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value
    ]
    quadrants = {
        (row < height // 2, col < width // 2) for row, col in occupied
    }
    return {
        "shape": [height, width],
        "frame_count": len(facts["frames"]),
        "colors": sorted({value for row in grid for value in row if value}),
        "nonzero_cells": len(occupied),
        "all_boundaries_touched": bool(
            any(r0 == 0 for r0, _c0, _r1, _c1 in boxes)
            and any(r1 == height - 1 for _r0, _c0, r1, _c1 in boxes)
            and any(c0 == 0 for _r0, c0, _r1, _c1 in boxes)
            and any(c1 == width - 1 for _r0, _c0, _r1, c1 in boxes)
        ),
        "all_quadrants_occupied": len(quadrants) == 4,
    }


def _write_public_examples(
    public_dir: Path | None,
    *,
    seed_first: int,
    seed_second: int,
) -> list[dict[str, Any]]:
    from reviewer_support import public_challenge_bytes, public_challenge_id

    if public_dir is None:
        return []
    if public_dir.exists() and any(public_dir.iterdir()):
        raise ValueError(f"public export directory is not empty: {public_dir}")
    public_dir.mkdir(parents=True, exist_ok=True)
    requests = (
        (seed_first, {family.PARAMETER_NAME: "template_interior"}),
        (seed_second, {family.PARAMETER_NAME: "pattern_bbox"}),
    )
    rows: list[dict[str, Any]] = []
    for seed, settings in requests:
        episode = family.generate(seed, settings, demos=3, queries=4)
        public = family.public_challenge(episode)
        visible_id = public_challenge_id(public)
        body = public_challenge_bytes(public)
        path = public_dir / f"{visible_id}.json"
        path.write_bytes(body)
        rows.append(
            {
                "seed": seed,
                "settings": settings,
                "public_id": visible_id,
                "path": str(path),
                "bytes": len(body),
                "sha256": _sha256_bytes(body),
            }
        )
    if len({row["public_id"] for row in rows}) != len(rows):
        raise AssertionError("public examples unexpectedly collide")
    return rows


def _racket_apply(program: str, grid: list[list[int]], bridge: Any) -> list[list[int]]:
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def _runtime_summary(identity: dict[str, Any]) -> dict[str, Any]:
    keep = (
        "schema",
        "backend",
        "protected",
        "binary_sha256",
        "prelude_sha256",
        "racket_version",
    )
    return {key: identity[key] for key in keep if key in identity}


def _racket_audit() -> dict[str, Any]:
    from arc_repl.racket_bridge import RacketBridge

    selected_checks: list[dict[str, Any]] = []
    rival_checks: list[dict[str, Any]] = []
    settings_space = [
        {family.PARAMETER_NAME: "template_interior"},
        {family.PARAMETER_NAME: "pattern_bbox"},
    ]
    total_evaluations = 0
    with RacketBridge(timeout=30, max_calls_before_restart=128) as bridge:
        identity = _runtime_summary(bridge.runtime_identity)
        for seed in (0, 17):
            for settings in settings_space:
                episode = family.generate(seed, settings, demos=3, queries=4)
                source = family.program(settings)
                for split in ("train", "test"):
                    for pair_index, pair in enumerate(episode[split]):
                        actual = _racket_apply(source, pair["input"], bridge)
                        total_evaluations += 1
                        matches = actual == pair["output"]
                        selected_checks.append(
                            {
                                "seed": seed,
                                "settings": settings,
                                "split": split,
                                "pair_index": pair_index,
                                "shape": [len(pair["input"]), len(pair["input"][0])],
                                "matches_claim": matches,
                            }
                        )
                        if not matches:
                            raise AssertionError(
                                f"selected Racket mismatch: {settings} {seed} {split}[{pair_index}]"
                            )

        rival_episode = family.generate(
            0, {family.PARAMETER_NAME: "pattern_bbox"}, demos=2, queries=4
        )
        selected_demo_outputs = [pair["output"] for pair in rival_episode["train"]]
        for name, source in family.rival_programs().items():
            demo_disagreements: list[int] = []
            for split in ("train", "test"):
                for pair_index, pair in enumerate(rival_episode[split]):
                    actual = _racket_apply(source, pair["input"], bridge)
                    total_evaluations += 1
                    expected = family.shortcut_output(pair["input"], name)
                    if actual != expected:
                        raise AssertionError(
                            f"rival Racket/Python mismatch: {name} {split}[{pair_index}]"
                        )
                    disagrees = actual != pair["output"]
                    if split == "train" and disagrees:
                        demo_disagreements.append(pair_index)
                    rival_checks.append(
                        {
                            "rival": name,
                            "split": split,
                            "pair_index": pair_index,
                            "matches_independent_prediction": True,
                            "disagrees_with_selected_label": disagrees,
                        }
                    )
            if not demo_disagreements:
                raise AssertionError(f"rival fits every visible demonstration: {name}")

        witness_episode = family.generate(
            0, {family.PARAMETER_NAME: "pattern_bbox"}, demos=3, queries=4
        )
        witness_pair = witness_episode["test"][3]
        correct_program = family.program({family.PARAMETER_NAME: "pattern_bbox"})
        wrong_program = family.counterfactual_program("template_extent")
        correct_output = _racket_apply(correct_program, witness_pair["input"], bridge)
        wrong_output = _racket_apply(wrong_program, witness_pair["input"], bridge)
        total_evaluations += 2
        if correct_output != witness_pair["output"]:
            raise AssertionError("causal witness selected program missed its native label")
        if correct_output == wrong_output:
            raise AssertionError("causal counterfactual did not change final output")
        intermediate = family.pattern_bbox_intermediate(witness_pair["input"])
        causal_case = {
            "settings": {family.PARAMETER_NAME: "pattern_bbox"},
            "program": correct_program,
            "input": witness_pair["input"],
            "output": correct_output,
            "intermediate_value": intermediate,
            "counterfactual_program": wrong_program,
            "counterfactual_output": wrong_output,
            "ablation": "wrong_intermediate",
            "changes_final_output": True,
            "case_source": {
                "seed": 0,
                "split": "test",
                "pair_index": 3,
                "shape": [30, 30],
            },
        }

    return {
        "runtime": identity,
        "selected_jobs": 4,
        "selected_labels": len(selected_checks),
        "selected_checks": selected_checks,
        "rival_programs": len(family.rival_programs()),
        "rival_labels": len(rival_checks),
        "rival_checks": rival_checks,
        "all_selected_labels_match": all(row["matches_claim"] for row in selected_checks),
        "all_rivals_match_independent_predictions": all(
            row["matches_independent_prediction"] for row in rival_checks
        ),
        "all_rivals_rejected_by_demonstrations": all(
            any(
                row["rival"] == name
                and row["split"] == "train"
                and row["disagrees_with_selected_label"]
                for row in rival_checks
            )
            for name in family.SHORTCUTS
        ),
        "total_evaluations": total_evaluations,
        "causal_case": causal_case,
    }


def build_report(
    *,
    seeds: Iterable[int] = (0, 17, 2718),
    demo_counts: Iterable[int] = (2, 3, 6),
    stress_seeds: int = 50,
    include_racket: bool = True,
    public_dir: Path | None = None,
) -> dict[str, Any]:
    seeds = tuple(seeds)
    demo_counts = tuple(demo_counts)
    if not seeds or not demo_counts or type(stress_seeds) is not int or stress_seeds < 1:
        raise ValueError("seeds, demo_counts, and a positive exact stress_seeds are required")

    canonical = _canonical_program()
    default_exact = family.program(family.DEFAULT_SETTINGS) == canonical
    if not default_exact:
        raise AssertionError("default materialized program is not exact canonical authority")

    settings_space = [
        {family.PARAMETER_NAME: "template_interior"},
        {family.PARAMETER_NAME: "pattern_bbox"},
    ]
    lesson_cases: list[dict[str, Any]] = []
    all_inputs_setting_independent = True
    for seed in seeds:
        for demos in demo_counts:
            episodes = {
                setting[family.PARAMETER_NAME]: family.generate(
                    seed, setting, demos=demos, queries=4
                )
                for setting in settings_space
            }
            first_inputs = _all_inputs(episodes["template_interior"])
            matched = first_inputs == _all_inputs(episodes["pattern_bbox"])
            all_inputs_setting_independent &= matched
            for settings in settings_space:
                episode = episodes[settings[family.PARAMETER_NAME]]
                query_inputs = [pair["input"] for pair in episode["test"]]
                certificate = family.lesson_certificate(episode["train"], query_inputs)
                lesson_cases.append(
                    {
                        "seed": seed,
                        "demonstrations": demos,
                        "settings": settings,
                        "surviving_settings": certificate["surviving_settings"],
                        "surviving_shortcuts": certificate["surviving_shortcuts"],
                        "query_disagreements": certificate["query_disagreements"],
                        "query_outputs_consulted": certificate["query_outputs_consulted"],
                        "inputs_setting_independent": matched,
                        "public_projection_private_invariant": _public_projection_invariant(
                            episode
                        ),
                        "sequential_projection_valid": _sequential_projection_invariant(
                            episode
                        ),
                    }
                )

    stress_episodes = 0
    stress_pairs = 0
    matched_input_comparisons = 0
    sequential_turns = 0
    stress_rows: list[dict[str, Any]] = []
    for seed in range(stress_seeds):
        for demos in (2, 3, 6):
            episodes = {
                setting[family.PARAMETER_NAME]: family.generate(
                    seed, setting, demos=demos, queries=4
                )
                for setting in settings_space
            }
            matched = _all_inputs(episodes["template_interior"]) == _all_inputs(
                episodes["pattern_bbox"]
            )
            matched_input_comparisons += 1
            if not matched:
                raise AssertionError(f"setting-dependent inputs at seed={seed}, demos={demos}")
            for settings in settings_space:
                episode = episodes[settings[family.PARAMETER_NAME]]
                inputs = _all_inputs(episode)
                if len(inputs) != len({_grid_key(grid) for grid in inputs}):
                    raise AssertionError(
                        f"duplicate input at seed={seed}, demos={demos}, settings={settings}"
                    )
                for pair in [*episode["train"], *episode["test"]]:
                    if family.analyze_scene(pair["input"])["errors"]:
                        raise AssertionError("sampler emitted an invalid scene")
                    if pair["output"] != family.transform(pair["input"], settings):
                        raise AssertionError("sampler label disagrees with selected Python claim")
                turns = family.sequential_public_turns(episode)
                if not _sequential_projection_invariant(episode):
                    raise AssertionError("sequential public projection changed or leaked")
                features = _stress_features(episode["test"][3]["input"])
                if (
                    features["shape"] != [30, 30]
                    or not features["all_boundaries_touched"]
                    or not features["all_quadrants_occupied"]
                ):
                    raise AssertionError("fourth query lost substantive 30x30 coverage")
                stress_rows.append(
                    {
                        "seed": seed,
                        "demonstrations": demos,
                        "settings": settings,
                        "pairs": len(episode["train"]) + len(episode["test"]),
                        "sequential_turns": len(turns),
                        "stress_query": features,
                    }
                )
                stress_episodes += 1
                stress_pairs += len(episode["train"]) + len(episode["test"])
                sequential_turns += len(turns)

            # Requested counts are independent prefixes, not one coupled total.
            full = episodes["pattern_bbox"]
            short_demos = family.generate(
                seed, {family.PARAMETER_NAME: "pattern_bbox"}, demos=2, queries=4
            )
            short_queries = family.generate(
                seed, {family.PARAMETER_NAME: "pattern_bbox"}, demos=demos, queries=1
            )
            if [pair["input"] for pair in short_demos["train"]] != [
                pair["input"] for pair in full["train"][:2]
            ]:
                raise AssertionError("demonstration prefix changed with requested count")
            if [pair["input"] for pair in short_queries["test"]] != [
                full["test"][0]["input"]
            ]:
                raise AssertionError("query prefix changed with requested count")

    public_exports = _write_public_examples(
        public_dir,
        seed_first=seeds[0],
        seed_second=seeds[-1],
    )
    racket = _racket_audit() if include_racket else None

    all_lessons_unique = all(
        case["surviving_settings"] == [case["settings"]] for case in lesson_cases
    )
    all_shortcuts_rejected = all(
        case["surviving_shortcuts"] == [] for case in lesson_cases
    )
    all_query_disagreements = all(
        case["query_disagreements"]
        and all(case["query_disagreements"].values())
        for case in lesson_cases
    )
    all_public_invariant = all(
        case["public_projection_private_invariant"] for case in lesson_cases
    )
    all_sequential_valid = all(
        case["sequential_projection_valid"] for case in lesson_cases
    )
    query_outputs_consulted = any(
        case["query_outputs_consulted"] for case in lesson_cases
    )
    racket_passed = racket is None or (
        racket["all_selected_labels_match"]
        and racket["all_rivals_match_independent_predictions"]
        and racket["all_rivals_rejected_by_demonstrations"]
        and racket["causal_case"]["changes_final_output"]
    )
    passed = bool(
        default_exact
        and all_lessons_unique
        and all_shortcuts_rejected
        and all_query_disagreements
        and all_inputs_setting_independent
        and all_public_invariant
        and all_sequential_valid
        and not query_outputs_consulted
        and stress_episodes == stress_seeds * 3 * len(settings_space)
        and racket_passed
        and (public_dir is None or len(public_exports) == 2)
    )

    summary = {
        "lesson_cases": len(lesson_cases),
        "all_lessons_unique": all_lessons_unique,
        "all_shortcuts_rejected": all_shortcuts_rejected,
        "all_rejected_rules_disagree_on_a_query": all_query_disagreements,
        "all_inputs_setting_independent": all_inputs_setting_independent,
        "all_public_projections_private_invariant": all_public_invariant,
        "all_sequential_projections_valid": all_sequential_valid,
        "query_outputs_consulted": query_outputs_consulted,
        "stress_episodes": stress_episodes,
        "stress_visible_pairs": stress_pairs,
        "matched_input_comparisons": matched_input_comparisons,
        "sequential_public_turns": sequential_turns,
        "public_exports": len(public_exports),
        "racket_evaluations": None if racket is None else racket["total_evaluations"],
    }
    return {
        "schema": "e3f1bc75d654-parametric-self-audit-v2",
        "task_id": family.TASK_ID,
        "status": "passed" if passed else "failed",
        "parameter": {
            "name": family.PARAMETER_NAME,
            "values": list(family.TARGET_BASES),
            "default": family.DEFAULT_SETTINGS,
        },
        "sequential_dependency": {
            "step_a": "locate the sole patterned template and derive the pattern's minimal bounding box plus normalized crop",
            "intermediate": "pattern bounding-box coordinates, crop dimensions, normalized pattern cells, and the frame(s) selected by those dimensions",
            "step_b": "select the unique empty frame whose interior equals the derived crop dimensions and stamp the normalized crop in that frame's color",
            "why_b_depends_on_a": "the target dimensions and therefore the target frame are unavailable until Step A derives the input-dependent pattern bounding box",
        },
        "source": {
            "default_exact_canonical": default_exact,
            "canonical_program_sha256": _sha256_bytes(canonical.encode("utf-8")),
            "alternate_program_sha256": _sha256_bytes(
                family.PATTERN_BBOX_PROGRAM.encode("utf-8")
            ),
            "prototype_sha256": _sha256_bytes(_FAMILY_PATH.read_bytes()),
            "audit_sha256": _sha256_bytes(Path(__file__).read_bytes()),
        },
        "summary": summary,
        "lesson_cases": lesson_cases,
        "stress": {
            "seed_count": stress_seeds,
            "demo_counts": [2, 3, 6],
            "rows": stress_rows,
        },
        "public_exports": public_exports,
        "racket": racket,
        "limitations": [
            "This is a finite audit of two settings and six authored rivals, not a proof of universal rule uniqueness.",
            "The stress sweep checks deterministic admitted scenes and Python claim construction; protected Racket replay is bounded to the recorded jobs and rivals.",
            "Reviewer readiness does not grant owner acceptance or training admission.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--public-dir")
    parser.add_argument("--case-out")
    parser.add_argument("--stress-seeds", type=int, default=50)
    parser.add_argument("--no-racket", action="store_true")
    options = parser.parse_args(argv)

    report = build_report(
        stress_seeds=options.stress_seeds,
        include_racket=not options.no_racket,
        public_dir=Path(options.public_dir) if options.public_dir else None,
    )
    destination = Path(options.out)
    _write_json(destination, report)
    if options.case_out:
        if report["racket"] is None:
            raise ValueError("--case-out requires protected Racket execution")
        _write_json(Path(options.case_out), report["racket"]["causal_case"])
    print(
        json.dumps(
            {
                "status": report["status"],
                "summary": report["summary"],
                "out": str(destination),
                "case_out": options.case_out,
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
