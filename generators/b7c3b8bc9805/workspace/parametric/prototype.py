#!/usr/bin/env python3
"""Proposed, unapproved phase-relation variant for ARC task b7c3b8bc9805.

The canonical ``same`` setting paints interior quadrants whose parity matches
that of the row-major first marker with that marker's color.  The sole
alternative ``opposite`` setting swaps the two marker colors inside the frame.
Production ``generate`` and canonical authority remain unchanged.  This
prototype materializes and executes exact Racket and writes finite public /
private evidence without exposing the hidden episode parameter.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import random
import sys
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "b7c3b8bc9805"
VERSION = "proposed-phase-relation-v1"
ALLOWED_PHASE_RELATIONS = ("same", "opposite")
DEFAULT_PHASE_RELATION = "same"
CANONICAL_RULE_HASH = "a17b11ed3aa1"
CANONICAL_SHA256 = "23db22e68dd6cb8001f6e8f60bdd1fce403c99210586506b3e717ddb33e3bb90"
SAME_PHASE_SITE = "(color (if (= p m1p) (third m1) (third m2)))"
OPPOSITE_PHASE_SITE = "(color (if (= p m1p) (third m2) (third m1)))"

# Five shared, lawful inputs: four demonstrations followed by one query.
# Input construction is independent of the hidden phase relation.
_FIXTURE_SCHEDULE = (
    ("demo_ul_opposite_markers", 7100, 0, "easy"),
    ("demo_ur_same_markers", 7101, 1, "easy"),
    ("demo_ll_same_markers", 7102, 2, "medium"),
    ("demo_lr_same_markers", 7103, 3, "hard"),
    ("query_ul_opposite_markers", 7104, 4, "medium"),
)


def _sha256(value: str | bytes) -> str:
    payload = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _stable_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def grid_sha256(grid) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _validate_seed(seed) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(SAME_PHASE_SITE) != 1:
        raise ValueError("canonical source must contain exactly one guarded phase site")
    if OPPOSITE_PHASE_SITE in source:
        raise ValueError("canonical source unexpectedly contains the alternative phase site")
    return source


def canonical_source(*, root=None) -> str:
    root = find_root(__file__) if root is None else Path(root)
    sources: set[str] = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if isinstance(source, str):
                    sources.add(source)
    if len(sources) != 1:
        raise ValueError(
            f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}"
        )
    return _check_canonical_source(sources.pop())


def materialize_rule(
    phase_relation: str = DEFAULT_PHASE_RELATION,
    *,
    root=None,
    source: str | None = None,
) -> str:
    if type(phase_relation) is not str or phase_relation not in ALLOWED_PHASE_RELATIONS:
        raise ValueError("phase_relation must be the string 'same' or 'opposite'")
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if phase_relation == "same":
        return canonical
    return canonical.replace(SAME_PHASE_SITE, OPPOSITE_PHASE_SITE, 1)


def _variant_phase_relation(source: str) -> str:
    if not isinstance(source, str):
        raise ValueError("variant source must be Racket text")
    if _sha256(source) == CANONICAL_SHA256:
        _check_canonical_source(source)
        return "same"
    if source.count(OPPOSITE_PHASE_SITE) == 1 and SAME_PHASE_SITE not in source:
        restored = source.replace(OPPOSITE_PHASE_SITE, SAME_PHASE_SITE, 1)
        _check_canonical_source(restored)
        return "opposite"
    raise ValueError(
        "source is neither the pinned canonical rule nor its guarded opposite-phase variant"
    )


def rule_callable(source: str) -> str:
    """Return the exact callable inside one guarded ``(rule! ...)`` wrapper."""
    _variant_phase_relation(source)
    prefix = "(rule! "
    if not source.startswith(prefix) or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len(prefix):-1]
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def execute_rule(source: str, grid, *, bridge: RacketBridge | None = None):
    """Execute the actual Racket variant; no Python answer mirror is used."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def fixtures(*, root=None) -> list[dict]:
    """Return five shared lawful inputs from the repaired generator schedule."""
    root = find_root(__file__) if root is None else Path(root)
    generator, source_path, source_sha256 = load_selected_generator(TASK_ID, root=root)
    result = []
    for fixture_id, seed, sample_index, difficulty in _FIXTURE_SCHEDULE:
        grid = generator.generate(seed, sample_index, difficulty=difficulty)
        reasons = generator.self_check(copy.deepcopy(grid))
        if reasons:
            raise ValueError(f"fixture {fixture_id} is outside the rule domain: {reasons}")
        result.append(
            {
                "fixture_id": fixture_id,
                "input": normalize_grid(grid),
                "input_sha256": grid_sha256(grid),
                "generator_seed": seed,
                "generator_sample_index": sample_index,
                "generator_difficulty": difficulty,
                "schedule_profile": generator.schedule_profile(
                    seed, sample_index, difficulty
                ),
                "semantic_signature": json.loads(
                    json.dumps(generator.semantic_signature(grid), sort_keys=True)
                ),
                "generator_source_path": str(source_path.relative_to(root)),
                "generator_source_sha256": source_sha256,
            }
        )
    if len({row["input_sha256"] for row in result}) != len(result):
        raise ValueError("fixture schedule produced duplicate inputs")
    return result


def parameters_for_seed(seed) -> dict[str, str]:
    _validate_seed(seed)
    # Exactly one hidden-rule draw per episode, before any pair is evaluated.
    return {
        "phase_relation": random.Random(seed).choice(ALLOWED_PHASE_RELATIONS)
    }


def make_episode(seed, *, root=None, bridge: RacketBridge | None = None) -> dict:
    parameters = parameters_for_seed(seed)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(seed, parameters, root=root, bridge=owned)
    return _make_episode(seed, parameters, root=root, bridge=bridge)


def _make_episode(seed, parameters, *, root, bridge: RacketBridge) -> dict:
    canonical = canonical_source(root=root)
    rules = {
        relation: materialize_rule(relation, source=canonical)
        for relation in ALLOWED_PHASE_RELATIONS
    }
    inputs = fixtures(root=root)
    predictions = {
        relation: [
            execute_rule(source, fixture["input"], bridge=bridge)
            for fixture in inputs
        ]
        for relation, source in rules.items()
    }
    selected_relation = parameters["phase_relation"]
    selected_outputs = predictions[selected_relation]
    pairs = []
    for fixture, output in zip(inputs, selected_outputs, strict=True):
        pairs.append(
            {
                **fixture,
                "output": output,
                "output_sha256": grid_sha256(output),
            }
        )

    rival_rows = []
    ambiguities = []
    for relation in ALLOWED_PHASE_RELATIONS:
        demonstration_mismatches = [
            index for index in range(4)
            if predictions[relation][index] != selected_outputs[index]
        ]
        query_mismatches = [0] if predictions[relation][4] != selected_outputs[4] else []
        status = (
            "refuted_by_demonstrations"
            if demonstration_mismatches
            else "ambiguous_query"
            if query_mismatches
            else "matches_episode"
        )
        row = {
            "phase_relation": relation,
            "racket_sha256": _sha256(rules[relation]),
            "status": status,
            "demonstration_mismatch_indices": demonstration_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_predictions": predictions[relation][:4],
            "query_predictions": predictions[relation][4:],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    selected_source = rules[selected_relation]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "parameters": parameters,
        "parameter_selection": (
            "one random.Random(seed).choice(('same','opposite')) draw before any pair"
        ),
        "input_schedule": [row["fixture_id"] for row in inputs],
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "racket_source": selected_source,
        "racket_sha256": _sha256(selected_source),
        "racket_callable": rule_callable(selected_source),
        "racket_callable_sha256": _sha256(rule_callable(selected_source)),
        "racket_path": f"private/rules/phase-{selected_relation}.rkt",
        "train": pairs[:4],
        "test": pairs[4:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": 10,
    }


def public_challenge(episode: dict) -> dict:
    """Return the explicit model-visible allowlist with hidden data removed."""
    return copy.deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in episode["train"]
            ],
            "test": [{"input": pair["input"]} for pair in episode["test"]],
        }
    )


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_evidence(seeds, *, out, root=None) -> dict:
    """Write finite, hash-bound executable evidence to a new directory."""
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    out = Path(out)
    if out.exists():
        raise FileExistsError(out)
    out.mkdir(parents=True)
    root = find_root(__file__) if root is None else Path(root)

    canonical = canonical_source(root=root)
    rules = {
        relation: materialize_rule(relation, source=canonical)
        for relation in ALLOWED_PHASE_RELATIONS
    }
    rule_rows = []
    for relation, source in rules.items():
        path = out / f"private/rules/phase-{relation}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")
        rule_rows.append(
            {
                "phase_relation": relation,
                "path": str(path.relative_to(out)),
                "sha256": _sha256(source),
                "source_identical_to_canonical": source == canonical,
            }
        )

    canonical_rows = canonical_pairs(TASK_ID, root=root, labeled_only=True)
    canonical_checks = []
    episode_rows = []
    with RacketBridge() as bridge:
        for pair in canonical_rows:
            actual = execute_rule(rules["same"], pair["input"], bridge=bridge)
            if actual != pair["output"]:
                raise AssertionError(
                    f"canonical Racket mismatch at variant={pair['variant']} "
                    f"split={pair['split']} pair={pair['pair_index']}"
                )
            canonical_checks.append(
                {
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": grid_sha256(pair["input"]),
                    "output_sha256": grid_sha256(actual),
                }
            )

        fixture_rows = fixtures(root=root)
        witness = fixture_rows[0]["input"]
        same_witness = execute_rule(rules["same"], witness, bridge=bridge)
        opposite_witness = execute_rule(rules["opposite"], witness, bridge=bridge)
        if same_witness == opposite_witness:
            raise AssertionError("phase settings did not differ on the distinguishing witness")

        for seed in seeds:
            episode = make_episode(seed, root=root, bridge=bridge)
            replay = make_episode(seed, root=root, bridge=bridge)
            if episode != replay:
                raise AssertionError(f"episode seed {seed} is not deterministic")
            if episode["ambiguities"]:
                raise AssertionError(f"episode seed {seed} leaves a parameter rival ambiguous")

            private_path = out / f"private/episodes/seed-{seed}.json"
            public = public_challenge(episode)
            public_path = out / f"public/episodes/{public_challenge_id(public)}.json"
            if public_path.exists():
                raise ValueError("duplicate visible episode; choose distinct demonstrated settings")
            _write_json(private_path, episode)
            public_path.parent.mkdir(parents=True, exist_ok=True)
            public_path.write_bytes(public_challenge_bytes(public))
            episode_rows.append(
                {
                    "seed": seed,
                    "parameters": episode["parameters"],
                    "public_path": str(public_path.relative_to(out)),
                    "private_path": str(private_path.relative_to(out)),
                    "public_sha256": _sha256(public_path.read_bytes()),
                    "private_sha256": _sha256(private_path.read_bytes()),
                    "parameter_rivals": [
                        {
                            key: row[key]
                            for key in (
                                "phase_relation",
                                "status",
                                "demonstration_mismatch_indices",
                                "query_mismatch_indices",
                            )
                        }
                        for row in episode["parameter_rivals"]
                    ],
                }
            )

    episode_rows.sort(key=lambda row: row["public_path"])
    _write_json(out / "private/canonical-checks.json", canonical_checks)
    _write_json(
        out / "private/distinguishing-witness.json",
        {
            "fixture": fixture_rows[0],
            "same_output": same_witness,
            "opposite_output": opposite_witness,
            "same_output_sha256": grid_sha256(same_witness),
            "opposite_output_sha256": grid_sha256(opposite_witness),
        },
    )

    files = [
        {"path": str(path.relative_to(out)), "sha256": _sha256(path.read_bytes())}
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    ambiguous_count = sum(
        row["status"] == "ambiguous_query"
        for episode in episode_rows
        for row in episode["parameter_rivals"]
    )
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "parameter": {
            "name": "phase_relation",
            "allowed_values": list(ALLOWED_PHASE_RELATIONS),
            "original_default": DEFAULT_PHASE_RELATION,
            "input_constraints_depend_on_parameter": False,
        },
        "invariant_reasoning": (
            "detect the gray frame and row-major marker pair, split the frame interior "
            "into quadrant parity classes, and vary only whether the first marker color "
            "occupies matching or opposite parity"
        ),
        "input_scope": (
            "five shared lawful inputs from the generator's four-slot curriculum; "
            "four demonstrations and one query"
        ),
        "runtime": racket_runtime_status(),
        "rules": rule_rows,
        "episodes": episode_rows,
        "files": files,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "counts": {
            "episodes": len(seeds),
            "train_pairs": 4 * len(seeds),
            "query_pairs": len(seeds),
            "distinct_input_grids": len(fixture_rows),
            "settings_exercised": len(ALLOWED_PHASE_RELATIONS),
            "episode_settings_exercised": len(
                {row["parameters"]["phase_relation"] for row in episode_rows}
            ),
            "canonical_pairs_checked": len(canonical_rows),
            "parameter_rival_episode_checks": (
                len(ALLOWED_PHASE_RELATIONS) * len(seeds)
            ),
            "ambiguous_parameter_rivals": ambiguous_count,
        },
        "limitations": [
            "Proposed prototype only; no variant approval or production API change.",
            "Evidence covers two settings, two seeds, and five generated inputs, not every lawful input.",
            "Rival checks cover only phase_relation in {'same','opposite'}, not every conceivable rule.",
            "The same setting is source-identical to the pinned canonical Racket rule and is checked on every labeled canonical pair.",
        ],
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--out", type=Path, required=True, help="new evidence directory")
    args = parser.parse_args(argv)
    report = write_evidence(args.seeds, out=args.out)
    print(
        json.dumps(
            {
                "status": report["status"],
                "counts": report["counts"],
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
