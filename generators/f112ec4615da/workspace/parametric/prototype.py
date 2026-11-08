"""Proposed two-setting priority episodes, with every label executed in Racket."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid


TASK_ID = "f112ec4615da"
PRIORITY_SETTINGS = ("canonical", "reverse")
DEFAULT_PRIORITY = "canonical"
PRIORITY_DESCRIPTION = {
    "canonical": "TR > BL > BR > TL",
    "reverse": "TL > BR > BL > TR",
}
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

_CANONICAL_BINDINGS = """(let* ((v (at g r c))
                                (v (if (!= (at g (+ r hh) (+ c hw)) 0)
                                       (at g (+ r hh) (+ c hw))
                                       v))
                                (v (if (!= (at g (+ r hh) c) 0) (at g (+ r hh) c) v))
                                (v (if (!= (at g r (+ c hw)) 0) (at g r (+ c hw)) v)))"""
_REVERSE_BINDINGS = """(let* ((v (at g r (+ c hw)))
                                (v (if (!= (at g (+ r hh) c) 0) (at g (+ r hh) c) v))
                                (v (if (!= (at g (+ r hh) (+ c hw)) 0)
                                       (at g (+ r hh) (+ c hw))
                                       v))
                                (v (if (!= (at g r c) 0) (at g r c) v)))"""


def sha256(value) -> str:
    raw = value if isinstance(value, bytes) else value.encode()
    return hashlib.sha256(raw).hexdigest()


@lru_cache(maxsize=2)
def canonical_rule(*, root=None) -> str:
    selected_root = ROOT if root is None else Path(root)
    matches = []
    with canonical_path(selected_root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    if len(matches) != 1:
        raise ValueError("The prototype requires exactly one selected canonical rule.")
    return matches[0]


def instantiate_rule(priority_order=DEFAULT_PRIORITY, *, root=None) -> str:
    if type(priority_order) is not str or priority_order not in PRIORITY_SETTINGS:
        raise ValueError(f"priority_order must be one of {PRIORITY_SETTINGS}")
    source = canonical_rule(root=root)
    if priority_order == DEFAULT_PRIORITY:
        return source
    if source.count(_CANONICAL_BINDINGS) != 1:
        raise ValueError("Canonical priority binding sequence changed; reassess the prototype.")
    return source.replace(_CANONICAL_BINDINGS, _REVERSE_BINDINGS)


def evaluate(bridge, program, grid):
    grid = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("Expected the selected task's native Racket lambda.")
    datum = "(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def choose_priority(seed) -> str:
    if type(seed) is not int:
        raise TypeError("seed must be a Python integer")
    return PRIORITY_SETTINGS[seed % len(PRIORITY_SETTINGS)]


def generate_inputs(seed):
    choose_priority(seed)  # Validate without coupling inputs to the chosen setting.
    bands = ("easy", "medium", "hard", "medium")
    return [
        GEN.generate(91_003 + seed * 101, index, difficulty=band)
        for index, band in enumerate(bands)
    ]


def make_episode(bridge, seed, *, priority_order=None):
    chosen = choose_priority(seed) if priority_order is None else priority_order
    program = instantiate_rule(chosen)
    return {
        "seed": seed,
        "parameters": {"priority_order": chosen},
        "parameter_choice": "seed_modulo_two" if priority_order is None else "explicit_once_per_episode",
        "priority_description": PRIORITY_DESCRIPTION[chosen],
        "racket_program": program,
        "racket_sha256": sha256(program),
        "pairs": [
            {"input": grid, "output": evaluate(bridge, program, grid)}
            for grid in generate_inputs(seed)
        ],
    }


def public_challenge(episode):
    return deepcopy({
        "train": episode["pairs"][:3],
        "test": [{"input": episode["pairs"][3]["input"]}],
    })


def analyze_episode(bridge, episode):
    pairs = episode["pairs"]
    chosen = episode["parameters"]["priority_order"]
    alternatives = {}
    for setting in PRIORITY_SETTINGS:
        if setting != chosen:
            program = instantiate_rule(setting)
            alternatives[setting] = [evaluate(bridge, program, pair["input"]) for pair in pairs]

    def score(query_index):
        demonstrations = [index for index in range(len(pairs)) if index != query_index]
        rivals = []
        for setting, outputs in alternatives.items():
            refutations = [
                index for index in demonstrations
                if outputs[index] != pairs[index]["output"]
            ]
            rivals.append({
                "name": f"priority_order={setting}",
                "parameters": {"priority_order": setting},
                "refuting_demonstration_indices": refutations,
                "fits_demonstrations": not refutations,
                "query_differs": outputs[query_index] != pairs[query_index]["output"],
            })
        ambiguous = any(row["fits_demonstrations"] and row["query_differs"] for row in rivals)
        return {
            "query_index": query_index,
            "demonstration_indices": demonstrations,
            "rivals": rivals,
            "status": "ambiguous" if ambiguous else "no_ambiguity_found",
        }

    return {
        "production": score(3),
        "rotations": [score(index) for index in range(len(pairs))],
        "counterfactual_outputs": alternatives,
    }


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def materialize(out, *, seed=0, bridge=None):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {
        "schema": "f112ec4615da-priority-prototype-v1",
        "status": "incomplete",
        "scope": "proposed task-local extension; not a canonical rule change or production approval",
        "parameter_spec": {
            "priority_order": {
                "allowed": list(PRIORITY_SETTINGS),
                "original_default": DEFAULT_PRIORITY,
                "effective_precedence": PRIORITY_DESCRIPTION,
            }
        },
        "choice_policy": "One value per episode: canonical for even seeds and reverse for odd seeds.",
        "lesson_policy": "Three demonstrations followed by one query; all four single-query rotations are also checked.",
        "input_domain": "Four lawful inputs from the selected 3.1.0 sampler; every input contains an all-four overlap witness. Input generation is independent of the hidden priority setting.",
        "limitations": "Two consecutive seeds and one declared alternative per episode only. This does not approve a production parametric API or establish uniqueness against undeclared rules.",
        "source_hashes": {
            "prototype.py": sha256(Path(__file__).read_bytes()),
            "generator.py": GENERATOR_SHA256,
            "canonical_racket": sha256(canonical_rule()),
        },
        "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "canonical_checks": [],
        "episodes": [],
    }
    try:
        with (nullcontext(bridge) if bridge is not None else RacketBridge()) as active:
            report["runtime"] = {
                "python": sys.version,
                "racket_version": active.eval_text("(version)"),
                "bridge_sha256": sha256(Path(sys.modules[RacketBridge.__module__].__file__).read_bytes()),
                "prelude_sha256": sha256(Path(active.prelude_path).read_bytes()),
            }
            for setting in PRIORITY_SETTINGS:
                rule_path = out / "private" / "rules" / f"priority-{setting}.rkt"
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(instantiate_rule(setting), encoding="utf-8")

            canonical_program = instantiate_rule(DEFAULT_PRIORITY)
            for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
                actual = evaluate(active, canonical_program, pair["input"])
                report["canonical_checks"].append({
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "expected": pair["output"],
                    "actual": actual,
                    "passed": actual == pair["output"],
                })

            for episode_index in range(2):
                episode = make_episode(active, seed + episode_index)
                analysis = analyze_episode(active, episode)
                public_path = f"public/episode-{episode_index + 1:03d}.json"
                private_path = f"private/episode-{episode_index + 1:03d}.json"
                write_json(out / public_path, public_challenge(episode))
                write_json(out / private_path, {**episode, "rival_checks": analysis})
                report["episodes"].append({
                    "seed": episode["seed"],
                    "parameters": episode["parameters"],
                    "priority_description": episode["priority_description"],
                    "racket_sha256": episode["racket_sha256"],
                    "public_path": public_path,
                    "private_path": private_path,
                    "production": analysis["production"],
                    "rotations": analysis["rotations"],
                })

            witness_input = generate_inputs(seed)[0]
            report["setting_witness"] = {
                "input": witness_input,
                "outputs": {
                    setting: evaluate(active, instantiate_rule(setting), witness_input)
                    for setting in PRIORITY_SETTINGS
                },
                "racket_hashes": {
                    setting: sha256(instantiate_rule(setting))
                    for setting in PRIORITY_SETTINGS
                },
            }
            passed = sum(row["passed"] for row in report["canonical_checks"])
            production_ambiguities = sum(
                row["production"]["status"] == "ambiguous"
                for row in report["episodes"]
            )
            rotation_ambiguities = sum(
                rotation["status"] == "ambiguous"
                for row in report["episodes"]
                for rotation in row["rotations"]
            )
            settings_seen = {
                row["parameters"]["priority_order"] for row in report["episodes"]
            }
            report["counts"] = {
                "canonical_labels_checked": len(report["canonical_checks"]),
                "canonical_labels_passed": passed,
                "episodes": len(report["episodes"]),
                "demonstrations": 6,
                "queries": 2,
                "episode_labels": 8,
                "counterfactual_labels": 8,
                "production_ambiguities": production_ambiguities,
                "query_rotations": 8,
                "rotation_ambiguities": rotation_ambiguities,
                "settings_seen": sorted(settings_seen),
            }
            witness_outputs = list(report["setting_witness"]["outputs"].values())
            report["status"] = (
                "no_ambiguity_found"
                if passed == len(report["canonical_checks"])
                and settings_seen == set(PRIORITY_SETTINGS)
                and witness_outputs[0] != witness_outputs[1]
                and not production_ambiguities
                and not rotation_ambiguities
                else "failed"
            )
            report["files"] = {
                str(path.relative_to(out)): {
                    "sha256": sha256(path.read_bytes()),
                    "bytes": path.stat().st_size,
                }
                for path in sorted(out.rglob("*"))
                if path.is_file()
            }
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        write_json(out / "report.json", report)
        raise
    write_json(out / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0, help="First of two consecutive episode seeds")
    parser.add_argument("--out", type=Path, required=True, help="New evidence directory; never overwritten")
    args = parser.parse_args(argv)
    report = materialize(args.out, seed=args.seed)
    print(json.dumps({
        "status": report["status"],
        "counts": report["counts"],
        "report": str(args.out / "report.json"),
    }, sort_keys=True))
    return int(report["status"] != "no_ambiguity_found")


if __name__ == "__main__":
    raise SystemExit(main())
