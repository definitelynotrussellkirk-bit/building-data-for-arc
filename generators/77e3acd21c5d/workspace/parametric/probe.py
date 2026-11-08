#!/usr/bin/env python3
"""Runnable bounded evidence and episode export for the proposed tie variants."""
from __future__ import annotations

import argparse
import hashlib
from itertools import combinations
import json
from pathlib import Path
import shlex
import sys

from prototype import (
    ALL_PARAMETERS, DEFAULT, HERE, ROOT, TASK_HOME, TASK_ID, VALUES, Parameters,
    RacketRules, canonical_program, choose_parameters, generate_episode,
    generator, materialize_rule, object_sha256, source_hashes, text_sha256,
)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def check_public(challenge: dict) -> None:
    if set(challenge) != {"train", "test"}:
        raise AssertionError("public challenge contains metadata")
    for split, keys in (("train", {"input", "output"}), ("test", {"input"})):
        for pair in challenge[split]:
            if set(pair) != keys:
                raise AssertionError(f"public {split} pair contains hidden data")
            for grid in pair.values():
                if any(type(cell) is not int for row in grid for cell in row):
                    raise AssertionError("public grid contains non-integer data")


def export_episode(args) -> dict:
    selected = None
    if args.row_ties is not None or args.column_ties is not None:
        seeded = choose_parameters(args.seed)
        selected = Parameters(args.row_ties or seeded.row_ties, args.column_ties or seeded.column_ties)
    episode = generate_episode(args.seed, parameters=selected)
    check_public(episode["public"])
    args.out.mkdir(parents=True, exist_ok=False)
    write_json(args.out / "challenge.json", episode["public"])
    write_json(args.out / "private.json", episode["private"])
    (args.out / "rule.rkt").write_text(episode["private"]["program"], encoding="utf-8")
    return {"status": "prototype_episode_written", "public": str(args.out / "challenge.json"),
            "public_sha256": episode["private"]["public_sha256"],
            "private_sha256": object_sha256(episode["private"])}


def evidence(args) -> dict:
    sources = source_hashes()
    first_seeds = {}
    for seed in range(args.seed_start, args.seed_start + args.max_seeds):
        parameters = choose_parameters(seed)
        first_seeds.setdefault(parameters.key, seed)
        if len(first_seeds) == len(ALL_PARAMETERS):
            break
    if len(first_seeds) != len(ALL_PARAMETERS):
        raise ValueError(f"seed search did not cover all settings; found {sorted(first_seeds)}")
    last_examined = seed
    args.out.mkdir(parents=True, exist_ok=False)
    for parameters in ALL_PARAMETERS:
        path = args.out / "rules" / f"{parameters.key}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(materialize_rule(parameters), encoding="utf-8")
    episodes = []
    with RacketRules() as rules:
        for index, parameters in enumerate(ALL_PARAMETERS):
            seed = first_seeds[parameters.key]
            episode = generate_episode(seed, rules=rules)
            replay = generate_episode(seed, rules=rules)
            if episode != replay:
                raise AssertionError(f"episode replay changed for seed {seed}")
            if episode["private"]["parameters"] != parameters.as_dict():
                raise AssertionError("seed selection changed")
            check_public(episode["public"])
            name = f"episode-{index:03d}"
            write_json(args.out / "public" / f"{name}.json", episode["public"])
            write_json(args.out / "private" / f"{name}.json", episode["private"])
            eliminated = sum(row["status"] == "eliminated" for row in episode["private"]["rivals"].values())
            if eliminated != 8:
                raise AssertionError("episode demonstrations left a declared alternative alive")
            episodes.append({"episode": name, "seed": seed, "parameters": parameters.as_dict(),
                             "program_sha256": episode["private"]["program_sha256"],
                             "public_sha256": object_sha256(episode["public"]),
                             "private_sha256": object_sha256(episode["private"]),
                             "replay_equal": True, "eliminated_rivals": eliminated})

        # Retain one lawful same-input witness with nine distinct executed
        # outputs, which separates all 36 unordered pairs of parameter settings.
        sampler = generator()
        for witness_index in range(16):
            witness = sampler.generate(177, witness_index, difficulty="medium", profile="large6", marker_mode="both_tie")
            if sampler.self_check(witness):
                raise AssertionError("distinguishing witness failed canonical self_check")
            predictions = {key: values[0] for key, values in rules.matrix([witness]).items()}
            if len({object_sha256(output) for output in predictions.values()}) == 9:
                break
        else:
            raise AssertionError("no nine-way separating witness in 16 bounded candidates")
        separated = [list(pair) for pair in combinations(predictions, 2) if predictions[pair[0]] != predictions[pair[1]]]
        write_json(args.out / "witness.json", {
            "input": witness, "input_sha256": object_sha256(witness),
            "generator_seed": 177, "sample_index": witness_index,
            "profile": "large6", "marker_mode": "both_tie",
            "outputs": predictions, "separated_setting_pairs": separated,
            "output_sha256": {key: object_sha256(output) for key, output in predictions.items()},
        })

        from reviewer_support import canonical_pairs
        sys.path.insert(0, str(TASK_HOME / "workspace"))
        from reference_probe import geometry_output

        canonical = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
        canonical_outputs = rules.outputs(DEFAULT, [pair["input"] for pair in canonical])
        for pair, output in zip(canonical, canonical_outputs):
            if output != pair["output"]:
                raise AssertionError("canonical default disagrees with a canonical pair")
        canonical_rows = [{"variant": pair["variant"], "split": pair["split"], "pair_index": pair["pair_index"],
                           "input_sha256": object_sha256(pair["input"]), "output": output,
                           "expected_output_sha256": object_sha256(pair["output"]), "equal": True}
                          for pair, output in zip(canonical, canonical_outputs)]
        generated = []
        for profile in ("compact4", "stack3", "wide4", "large6"):
            for mode in ("corner", "row_tie", "col_tie", "both_tie", "clipped"):
                index = len(generated)
                grid = sampler.generate(955, index, difficulty="medium", profile=profile, marker_mode=mode)
                generated.append({"input": grid, "profile": profile, "marker_mode": mode, "sample_index": index})
        generated_outputs = rules.outputs(DEFAULT, [row["input"] for row in generated])
        for row, output in zip(generated, generated_outputs):
            expected = geometry_output(row["input"])
            if output != expected or sampler.self_check(row["input"]):
                raise AssertionError("canonical default or sampler failed generated geometry parity")
            row.update({"output": output, "input_sha256": object_sha256(row["input"]),
                        "expected_output_sha256": object_sha256(expected), "equal": True})
        write_json(args.out / "default-parity.json", {"canonical": canonical_rows, "generated": generated,
                    "canonical_count": len(canonical), "generated_count": len(generated),
                    "default_exact_canonical_bytes": materialize_rule(DEFAULT) == canonical_program()})
        runtime_identity = rules.runtime_identity
        applications = rules.calls
    if source_hashes() != sources:
        raise RuntimeError("source changed during evidence run; rerun in a new output directory")
    artifacts = {path.relative_to(args.out).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in sorted(args.out.rglob("*")) if path.is_file()}
    receipt = {
        "schema": "arc-parametric-prototype-evidence-v1", "task_id": TASK_ID,
        "status": "passed_declared_checks", "admission": "prototype_only_not_production_approval",
        "parameter_values": {"row_ties": list(VALUES), "column_ties": list(VALUES)},
        "canonical_default": DEFAULT.as_dict(), "canonical_program_sha256": text_sha256(canonical_program()),
        "source_sha256": sources, "runtime_identity": runtime_identity,
        "command": shlex.join([sys.executable, *sys.argv]), "payload_cwd": str(ROOT),
        "seed_search": {"start": args.seed_start, "bound": args.max_seeds, "last_examined": last_examined},
        "episodes": episodes, "episode_count": len(episodes), "demonstrations_per_episode": 5,
        "queries_per_episode": 1, "rival_checks": 81, "alternative_eliminations": 72,
        "ambiguous_episodes": 0, "exact_replays": 9, "unique_witness_outputs": 9,
        "separated_setting_pairs": len(separated), "canonical_pairs_passed": len(canonical),
        "generated_default_pairs_passed": len(generated), "racket_label_applications": applications,
        "artifacts_sha256": artifacts,
        "limitations": [
            "Only nine declared tie-policy settings are tested; undeclared hypotheses remain possible.",
            "Nine seeded episodes, one retained witness, and the listed parity inputs are bounded evidence, not universal identifiability.",
            "The input sampler retains the canonical generator's fixed slot templates; no arbitrary packing claim.",
            "The ordered five-demonstration curriculum is checked; arbitrary demonstration subsets or query rotations are not certified.",
            "This task-local prototype does not alter canonical authority, catalog approval, or the production generator API.",
        ],
    }
    write_json(args.out / "receipt.json", receipt)
    return {key: receipt[key] for key in ("status", "episode_count", "alternative_eliminations", "separated_setting_pairs",
                                          "canonical_pairs_passed", "generated_default_pairs_passed", "racket_label_applications")} | {
        "receipt": str(args.out / "receipt.json"), "receipt_sha256": hashlib.sha256((args.out / "receipt.json").read_bytes()).hexdigest()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    single = commands.add_parser("episode", help="export one public challenge and its separate private record")
    single.add_argument("--seed", type=int, required=True)
    single.add_argument("--row-ties", choices=VALUES)
    single.add_argument("--column-ties", choices=VALUES)
    single.add_argument("--out", type=Path, required=True, help="new directory; existing outputs are never overwritten")
    single.set_defaults(run=export_episode)
    audit = commands.add_parser("evidence", help="retain nine complete episodes, materialized programs, witnesses and parity")
    audit.add_argument("--seed-start", type=int, default=0)
    audit.add_argument("--max-seeds", type=int, default=256)
    audit.add_argument("--out", type=Path, required=True, help="new directory")
    audit.set_defaults(run=evidence)
    args = parser.parse_args()
    print(json.dumps(args.run(args), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
