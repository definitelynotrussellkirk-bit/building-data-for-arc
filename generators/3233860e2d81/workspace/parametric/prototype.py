"""Proposed task-local top-k episodes for ARC family f8ff0b80.

This is authoring evidence only.  It does not alter the selected production
rule, generator API, approval state, or canonical labels.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import random
import re
import sys

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root, normalize_grid


TASK_ID = "3233860e2d81"
TOP_K_VALUES = (2, 3, 4)
DEFAULT_TOP_K = 3


def sha256(value):
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@lru_cache(maxsize=4)
def canonical_rule(*, root=None):
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if TASK_ID not in line:
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.append(row["program_solution"])
    if not sources:
        raise ValueError("No selected canonical rule found for the prototype")
    if len(set(sources)) != 1:
        raise ValueError("Canonical variants disagree in exact rule text")
    return sources[0]


def instantiate_rule(top_k=DEFAULT_TOP_K, *, root=None):
    if type(top_k) is not int:
        raise TypeError(f"top_k must be a Python int, not {type(top_k).__name__}")
    if top_k not in TOP_K_VALUES:
        raise ValueError(f"top_k must be one of {TOP_K_VALUES}, got {top_k}")
    source = canonical_rule(root=root)
    changed, count = re.subn(
        r"\(build-grid\s+3\s+1\s+\(r c\)",
        f"(build-grid {top_k} 1 (r c)",
        source,
    )
    if count != 1:
        raise ValueError(
            "Canonical top-k output site changed; reassess this prototype"
        )
    if top_k == DEFAULT_TOP_K and changed != source:
        raise AssertionError("Original top_k=3 must preserve exact canonical text")
    return changed


def evaluate(bridge, program, grid):
    grid = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("Expected the selected task's native Racket lambda")
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in grid
    ) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def choose_top_k(seed):
    if type(seed) is not int:
        raise TypeError(f"seed must be a Python int, not {type(seed).__name__}")
    return TOP_K_VALUES[seed % len(TOP_K_VALUES)]


def _row_snake(height, width):
    return [
        (row, column)
        for row in range(height)
        for column in (
            range(width) if row % 2 == 0 else range(width - 1, -1, -1)
        )
    ]


def generate_inputs(seed):
    """Create four rule-lawful count-ranking inputs with five colors each."""
    choose_top_k(seed)  # Validate without coupling rule and input selection.
    rng = random.Random(f"{TASK_ID}:top-k-inputs:{seed}")
    grids = []
    base_counts = (3, 5, 8, 12, 17)
    for index in range(4):
        height = 10 + rng.randrange(3)
        width = 11 + rng.randrange(3)
        palette = rng.sample(range(1, 10), 5)
        counts = list(base_counts)
        rng.shuffle(counts)
        color_counts = list(zip(palette, counts))
        rng.shuffle(color_counts)

        path = _row_snake(height, width)
        if rng.random() < 0.5:
            path.reverse()
        required = sum(counts) + len(counts) - 1
        slack = len(path) - required
        if slack < 0:
            raise RuntimeError("prototype input dimensions are unexpectedly too small")
        offset = rng.randrange(slack + 1)
        grid = [[0] * width for _ in range(height)]
        cursor = offset
        for segment_index, (color, count) in enumerate(color_counts):
            for row, column in path[cursor: cursor + count]:
                grid[row][column] = color
            cursor += count
            if segment_index < len(color_counts) - 1:
                cursor += 1
        grids.append(grid)
    return grids


def make_episode(bridge, seed, *, top_k=None):
    chosen = choose_top_k(seed) if top_k is None else top_k
    program = instantiate_rule(chosen)
    pairs = [
        {"input": grid, "output": evaluate(bridge, program, grid)}
        for grid in generate_inputs(seed)
    ]
    return {
        "seed": seed,
        "parameters": {"top_k": chosen},
        "parameter_choice": (
            "seed_modulo_three" if top_k is None else "explicit_once_per_episode"
        ),
        "racket_program": program,
        "racket_sha256": sha256(program),
        "pairs": pairs,
    }


def public_challenge(episode):
    return deepcopy(
        {
            "train": episode["pairs"][:3],
            "test": [{"input": episode["pairs"][3]["input"]}],
        }
    )


def analyze_episode(bridge, episode):
    pairs = episode["pairs"]
    chosen = episode["parameters"]["top_k"]
    alternatives = {}
    for top_k in TOP_K_VALUES:
        if top_k == chosen:
            continue
        program = instantiate_rule(top_k)
        alternatives[str(top_k)] = [
            evaluate(bridge, program, pair["input"]) for pair in pairs
        ]

    def score(query_index):
        demonstration_indices = [
            index for index in range(len(pairs)) if index != query_index
        ]
        rivals = []
        for raw_top_k, outputs in sorted(alternatives.items()):
            refutations = [
                index
                for index in demonstration_indices
                if outputs[index] != pairs[index]["output"]
            ]
            rivals.append(
                {
                    "name": f"top_k={raw_top_k}",
                    "parameters": {"top_k": int(raw_top_k)},
                    "refuting_demonstration_indices": refutations,
                    "fits_demonstrations": not refutations,
                    "query_differs": outputs[query_index]
                    != pairs[query_index]["output"],
                }
            )
        ambiguous = any(
            rival["fits_demonstrations"] and rival["query_differs"]
            for rival in rivals
        )
        return {
            "query_index": query_index,
            "demonstration_indices": demonstration_indices,
            "rivals": rivals,
            "status": "ambiguous" if ambiguous else "no_ambiguity_found",
        }

    return {
        "production": score(3),
        "rotations": [score(index) for index in range(4)],
        "counterfactual_outputs": alternatives,
    }


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def materialize(out, *, seed=0, bridge=None):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    report = {
        "schema": "3233860e2d81-top-k-prototype-v1",
        "status": "incomplete",
        "scope": (
            "proposed task-local extension; not a canonical rule change or "
            "production approval"
        ),
        "parameter_spec": {
            "top_k": {
                "allowed": list(TOP_K_VALUES),
                "original_default": DEFAULT_TOP_K,
            }
        },
        "choice_policy": (
            "One top_k per episode: (2,3,4)[seed % 3]; three consecutive "
            "seeds cover all settings."
        ),
        "lesson_policy": (
            "Three demonstrations and one query; all four single-query "
            "rotations are checked."
        ),
        "input_domain": (
            "10..12 rows by 11..13 columns, zero background, exactly five "
            "nonzero colors with distinct counts 3,5,8,12,17."
        ),
        "limitations": (
            "Three seeds and two declared parameter rivals per episode only. "
            "The sampler is a bounded count-ranking subset and is separate "
            "from the selected production generator."
        ),
        "source_hashes": {
            "prototype.py": sha256(Path(__file__).read_bytes()),
            "canonical_racket": sha256(canonical_rule(root=root)),
        },
        "invocation": {
            "cwd": str(Path.cwd()),
            "argv": [sys.executable, *sys.argv],
        },
        "canonical_checks": [],
        "episodes": [],
    }
    try:
        with (
            nullcontext(bridge)
            if bridge is not None
            else RacketBridge()
        ) as active:
            report["runtime"] = {
                "python": sys.version,
                "racket_version": active.eval_text("(version)"),
                "bridge_sha256": sha256(
                    Path(sys.modules[RacketBridge.__module__].__file__).read_bytes()
                ),
                "prelude_sha256": sha256(Path(active.prelude_path).read_bytes()),
            }
            for top_k in TOP_K_VALUES:
                rule_path = out / "private" / "rules" / f"top-k-{top_k}.rkt"
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(instantiate_rule(top_k), encoding="utf-8")

            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = evaluate(active, instantiate_rule(DEFAULT_TOP_K), pair["input"])
                report["canonical_checks"].append(
                    {
                        "variant": pair.get("variant"),
                        "split": pair.get("split"),
                        "row_index": pair.get("row_index"),
                        "pair_index": pair.get("pair_index"),
                        "passed": actual == pair["output"],
                    }
                )

            unique_inputs = set()
            for episode_index in range(3):
                episode = make_episode(active, seed + episode_index)
                scores = analyze_episode(active, episode)
                public_path = f"public/episode-{episode_index + 1:03d}.json"
                private_path = f"private/episode-{episode_index + 1:03d}.json"
                write_json(out / public_path, public_challenge(episode))
                write_json(out / private_path, {**episode, "rival_checks": scores})
                report["episodes"].append(
                    {
                        "seed": episode["seed"],
                        "parameters": episode["parameters"],
                        "racket_sha256": episode["racket_sha256"],
                        "public_path": public_path,
                        "private_path": private_path,
                        "production": scores["production"],
                        "rotations": scores["rotations"],
                    }
                )
                unique_inputs.update(
                    json.dumps(pair["input"], separators=(",", ":"))
                    for pair in episode["pairs"]
                )
                if episode["parameters"]["top_k"] == DEFAULT_TOP_K:
                    report["setting_witness"] = {
                        "input": episode["pairs"][0]["input"],
                        "outputs": {
                            "3": episode["pairs"][0]["output"],
                            **{
                                name: outputs[0]
                                for name, outputs in scores[
                                    "counterfactual_outputs"
                                ].items()
                            },
                        },
                        "racket_hashes": {
                            str(value): sha256(instantiate_rule(value))
                            for value in TOP_K_VALUES
                        },
                    }

            production_ambiguities = sum(
                episode["production"]["status"] == "ambiguous"
                for episode in report["episodes"]
            )
            rotation_ambiguities = sum(
                rotation["status"] == "ambiguous"
                for episode in report["episodes"]
                for rotation in episode["rotations"]
            )
            canonical_passes = sum(
                check["passed"] for check in report["canonical_checks"]
            )
            report["counts"] = {
                "canonical_labels_checked": len(report["canonical_checks"]),
                "canonical_labels_passed": canonical_passes,
                "episodes": 3,
                "demonstrations": 9,
                "queries": 3,
                "episode_labels": 12,
                "counterfactual_labels": 24,
                "production_ambiguities": production_ambiguities,
                "rotation_ambiguities": rotation_ambiguities,
                "query_rotations": 12,
                "unique_episode_inputs": len(unique_inputs),
            }
            report["status"] = (
                "no_ambiguity_found"
                if canonical_passes == len(report["canonical_checks"])
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
    parser.add_argument(
        "--seed", type=int, default=0, help="First of three consecutive seeds"
    )
    parser.add_argument(
        "--out", type=Path, required=True, help="New evidence directory"
    )
    args = parser.parse_args(argv)
    report = materialize(args.out, seed=args.seed)
    print(
        json.dumps(
            {
                "status": report["status"],
                "counts": report.get("counts"),
                "report": str(args.out / "report.json"),
            },
            sort_keys=True,
        )
    )
    return int(report["status"] != "no_ambiguity_found")


if __name__ == "__main__":
    raise SystemExit(main())
