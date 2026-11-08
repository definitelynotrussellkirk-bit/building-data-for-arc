"""Racket-backed prototype for an episode-level output bar color.

This is a proposed task-local extension, not a canonical rule change.  The
canonical default remains color 8 byte-for-byte; color 3 changes only the paint
role while preserving the row-wise count/rank reasoning pattern.
"""
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
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "587396c0817d"
BAR_COLORS = (8, 3)
DEFAULT_BAR_COLOR = 8
SCHEMA = "587396c0817d-bar-color-prototype-v1"
_PAINT_SITE = "(if (and (>= c bar-start) (<= c bar-end)) 8 7)"


def sha256(value):
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@lru_cache(maxsize=8)
def canonical_rule(*, root=None):
    """Read the one exact selected canonical Racket source."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                sources.append(str(row["program_solution"]))
    unique = list(dict.fromkeys(sources))
    if len(unique) != 1:
        raise ValueError(
            f"bar_color requires one exact canonical source; found {len(unique)}"
        )
    return unique[0]


def _validate_bar_color(bar_color):
    if type(bar_color) is not int or bar_color not in BAR_COLORS:
        raise ValueError(f"bar_color must be exactly one of {BAR_COLORS}")
    return bar_color


def instantiate_rule(bar_color=DEFAULT_BAR_COLOR, *, root=None):
    """Change only the canonical bar-paint literal; default is byte-identical."""
    color = _validate_bar_color(bar_color)
    source = canonical_rule(root=root)
    if color == DEFAULT_BAR_COLOR:
        return source
    if source.count(_PAINT_SITE) != 1:
        raise ValueError(
            "Canonical bar-paint site changed; manually reassess this prototype"
        )
    replacement = _PAINT_SITE.replace(" 8 7)", f" {color} 7)")
    changed = source.replace(_PAINT_SITE, replacement, 1)
    if changed == source:
        raise ValueError("alternative bar_color did not change the authority")
    return changed


def choose_bar_color(seed):
    """Choose one rule value for the entire episode."""
    if type(seed) is not int:
        raise ValueError("seed must be a Python int")
    return BAR_COLORS[seed % len(BAR_COLORS)]


def _racket_datum(grid):
    return "(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def evaluate(bridge, program, grid):
    """Execute one grid through the real Racket bridge."""
    grid = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("Expected the selected task's native Racket lambda")
    return normalize_grid(bridge.eval_text(f"({function} '{_racket_datum(grid)})"))


def generate_inputs(seed, *, root=None):
    """Generate four deterministic, lawful, pairwise-distinct task inputs."""
    choose_bar_color(seed)
    root = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    bands = ("easy", "medium", "hard", "medium")
    inputs = []
    for index, band in enumerate(bands):
        grid = generator.generate(
            100_000 + seed * 97 + index,
            seed * 4 + index,
            difficulty=band,
        )
        errors = generator.self_check(grid, difficulty=band)
        if errors:
            raise RuntimeError(f"generated invalid input {index}: {errors}")
        inputs.append(normalize_grid(grid))
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in inputs}
    if len(fingerprints) != len(inputs):
        raise RuntimeError("parametric input sampler produced duplicate grids")
    return inputs


def make_episode(bridge, seed, *, bar_color=None, root=None):
    """Bind one color, then Racket-label all four episode examples."""
    chosen = choose_bar_color(seed) if bar_color is None else _validate_bar_color(bar_color)
    program = instantiate_rule(chosen, root=root)
    inputs = generate_inputs(seed, root=root)
    return {
        "seed": seed,
        "parameters": {"bar_color": chosen},
        "parameter_choice": (
            "seed_modulo_two" if bar_color is None else "explicit_once_per_episode"
        ),
        "racket_program": program,
        "racket_sha256": sha256(program),
        "pairs": [
            {"input": grid, "output": evaluate(bridge, program, grid)}
            for grid in inputs
        ],
    }


def public_challenge(episode):
    """Expose three labeled demonstrations and one unlabeled query."""
    return deepcopy(
        {
            "train": episode["pairs"][:3],
            "test": [{"input": episode["pairs"][3]["input"]}],
        }
    )


def analyze_episode(bridge, episode, *, root=None):
    """Check the other color setting against production and all rotations."""
    pairs = episode["pairs"]
    if len(pairs) != 4:
        raise ValueError("episode must contain exactly four pairs")
    chosen = _validate_bar_color(episode["parameters"]["bar_color"])
    rival_color = next(color for color in BAR_COLORS if color != chosen)
    rival_program = instantiate_rule(rival_color, root=root)
    rival_outputs = [
        evaluate(bridge, rival_program, pair["input"]) for pair in pairs
    ]

    def score(query_index):
        demonstrations = [index for index in range(4) if index != query_index]
        refutations = [
            index
            for index in demonstrations
            if rival_outputs[index] != pairs[index]["output"]
        ]
        rival = {
            "name": f"bar_color={rival_color}",
            "parameters": {"bar_color": rival_color},
            "racket_sha256": sha256(rival_program),
            "refuting_demonstration_indices": refutations,
            "fits_demonstrations": not refutations,
            "query_differs": rival_outputs[query_index] != pairs[query_index]["output"],
        }
        ambiguous = rival["fits_demonstrations"] and rival["query_differs"]
        return {
            "query_index": query_index,
            "demonstration_indices": demonstrations,
            "rival": rival,
            "status": "ambiguous" if ambiguous else "no_ambiguity_found",
        }

    return {
        "production": score(3),
        "rotations": [score(index) for index in range(4)],
        "counterfactual_color": rival_color,
        "counterfactual_outputs": rival_outputs,
    }


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _inventory(out):
    return {
        path.relative_to(out).as_posix(): {
            "sha256": sha256(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(out.rglob("*"))
        if path.is_file() and path.name != "report.json"
    }


def materialize(out, *, seed=0, bridge=None):
    """Create immutable public/private Racket-backed prototype evidence."""
    choose_bar_color(seed)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    _, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    report = {
        "schema": SCHEMA,
        "status": "incomplete",
        "scope": (
            "Proposed task-local extension only; not a canonical rule change, "
            "training approval, or production generator axis."
        ),
        "parameter_spec": {
            "bar_color": {
                "allowed": list(BAR_COLORS),
                "original_default": DEFAULT_BAR_COLOR,
                "meaning": "Output color used for every reconstructed row bar.",
            }
        },
        "choice_policy": (
            "Exactly one value per episode: [8,3][seed % 2]. Two consecutive "
            "seeds cover both settings."
        ),
        "lesson_policy": (
            "Three demonstrations followed by one query; all four single-query "
            "rotations are checked against the other parameter value."
        ),
        "input_domain": (
            "Four deterministic strict-valid inputs from the selected generator "
            "across easy/medium/hard/medium; every input contains an active row."
        ),
        "limitations": (
            "Only two output-color settings are studied. The parameter preserves "
            "geometry and rank reasoning but does not test anchor-color changes or "
            "prove identifiability against undeclared rule families."
        ),
        "source_hashes": {
            "prototype.py": sha256(Path(__file__).read_bytes()),
            "generator.py": generator_sha,
            "generator_path": str(generator_path),
            "canonical_racket": sha256(canonical_rule(root=root)),
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
                "bridge_sha256": sha256(
                    Path(sys.modules[RacketBridge.__module__].__file__).read_bytes()
                ),
                "prelude_sha256": sha256(Path(active.prelude_path).read_bytes()),
            }
            for color in BAR_COLORS:
                rule_path = out / "private" / "rules" / f"bar-color-{color}.rkt"
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(instantiate_rule(color, root=root), encoding="utf-8")

            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = evaluate(
                    active,
                    instantiate_rule(DEFAULT_BAR_COLOR, root=root),
                    pair["input"],
                )
                report["canonical_checks"].append(
                    {
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "expected": pair["output"],
                        "actual": actual,
                        "passed": actual == pair["output"],
                    }
                )

            all_inputs = set()
            for index in range(2):
                episode = make_episode(active, seed + index, root=root)
                scores = analyze_episode(active, episode, root=root)
                public_path = f"public/episode-{index + 1:03d}.json"
                private_path = f"private/episode-{index + 1:03d}.json"
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
                all_inputs.update(
                    json.dumps(pair["input"], separators=(",", ":"))
                    for pair in episode["pairs"]
                )

            canonical_passed = sum(row["passed"] for row in report["canonical_checks"])
            production_ambiguities = sum(
                row["production"]["status"] == "ambiguous"
                for row in report["episodes"]
            )
            rotation_ambiguities = sum(
                rotation["status"] == "ambiguous"
                for row in report["episodes"]
                for rotation in row["rotations"]
            )
            report["counts"] = {
                "canonical_labels_checked": len(report["canonical_checks"]),
                "canonical_labels_passed": canonical_passed,
                "episodes": 2,
                "demonstrations": 6,
                "queries": 2,
                "episode_labels": 8,
                "counterfactual_labels": 8,
                "production_ambiguities": production_ambiguities,
                "rotation_ambiguities": rotation_ambiguities,
                "query_rotations": 8,
                "unique_episode_inputs": len(all_inputs),
            }
            report["status"] = (
                "no_ambiguity_found"
                if canonical_passed == len(report["canonical_checks"])
                and not production_ambiguities
                and not rotation_ambiguities
                else "failed"
            )
            report["files"] = _inventory(out)
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        write_json(out / "report.json", report)
        raise

    write_json(out / "report.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = materialize(args.out, seed=args.seed)
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
    return int(report["status"] != "no_ambiguity_found")


if __name__ == "__main__":
    raise SystemExit(main())
