"""Racket-backed prototype for an episode-level reflected-copy color role.

This is evidence for a proposed task-local extension, not a canonical rule
change.  Every emitted label is evaluated by the selected Racket authority.
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

TASK_ID = "6d33e42a400d"
COPY_COLOR_ROLES = ("paint", "source")
DEFAULT_COPY_COLOR_ROLE = "paint"
SCHEMA = "6d33e42a400d-copy-color-role-prototype-v1"

_HORIZONTAL_PAINT = "(set-cell acc nr c paint-color)"
_HORIZONTAL_SOURCE = "(set-cell acc nr c source-color)"
_VERTICAL_PAINT = "(set-cell acc r nc paint-color)"
_VERTICAL_SOURCE = "(set-cell acc r nc source-color)"


def sha256(value):
    """Return a lowercase SHA-256 hex digest for bytes or text."""
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@lru_cache(maxsize=8)
def canonical_rule(*, root=None):
    """Load the one exact canonical rule text shared by all task variants."""
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.append(row["program_solution"])
    unique = list(dict.fromkeys(sources))
    if len(unique) != 1:
        raise ValueError(
            "copy_color_role requires one exact canonical rule across variants; "
            f"found {len(unique)} distinct sources"
        )
    return unique[0]


def _validate_copy_color_role(copy_color_role):
    if type(copy_color_role) is not str or copy_color_role not in COPY_COLOR_ROLES:
        raise ValueError(
            "copy_color_role must be exactly 'paint' or 'source' as a Python str"
        )
    return copy_color_role


def instantiate_rule(copy_color_role=DEFAULT_COPY_COLOR_ROLE, *, root=None):
    """Instantiate only the two reflected-copy paint sites in the authority."""
    role = _validate_copy_color_role(copy_color_role)
    source = canonical_rule(root=root)
    if role == "paint":
        return source

    if source.count(_HORIZONTAL_PAINT) != 1 or source.count(_VERTICAL_PAINT) != 1:
        raise ValueError(
            "Canonical copy-color sites changed; manually reassess this prototype."
        )
    changed = source.replace(_HORIZONTAL_PAINT, _HORIZONTAL_SOURCE, 1)
    changed = changed.replace(_VERTICAL_PAINT, _VERTICAL_SOURCE, 1)
    if changed == source:
        raise ValueError("copy_color_role='source' did not change the authority")
    return changed


def _racket_datum(grid):
    return "(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def evaluate(bridge, program, grid):
    """Execute one grid through the supplied Racket bridge."""
    grid = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("Expected the selected task's native Racket lambda")
    return normalize_grid(bridge.eval_text(f"({function} '{_racket_datum(grid)})"))


def choose_copy_color_role(seed):
    """Choose one role for a whole episode without sharing the input RNG."""
    if type(seed) is not int:
        raise ValueError("seed must be a Python int")
    return COPY_COLOR_ROLES[seed % len(COPY_COLOR_ROLES)]


def generate_inputs(seed, *, root=None):
    """Generate four deterministic, lawful, pairwise-distinct task inputs."""
    choose_copy_color_role(seed)  # exact scalar validation
    root = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root)
    bands = ("easy", "medium", "hard", "medium")
    profiles = tuple(generator.SCENE_PROFILES[:4])
    inputs = []
    for index, (band, profile) in enumerate(zip(bands, profiles)):
        grid = generator.generate(
            100_000 + seed * 97 + index,
            index,
            difficulty=band,
            scene_profile=profile,
            orientation=(seed + index) % 4,
        )
        if generator.self_check(grid, difficulty=band):
            raise RuntimeError(f"generated invalid parametric input at index {index}")
        inputs.append(normalize_grid(grid))
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in inputs}
    if len(fingerprints) != len(inputs):
        raise RuntimeError("parametric input sampler produced a duplicate grid")
    return inputs


def make_episode(bridge, seed, *, copy_color_role=None, root=None):
    """Bind one parameter value, then Racket-label all four episode examples."""
    chosen = (
        choose_copy_color_role(seed)
        if copy_color_role is None
        else _validate_copy_color_role(copy_color_role)
    )
    program = instantiate_rule(chosen, root=root)
    inputs = generate_inputs(seed, root=root)
    return {
        "seed": seed,
        "parameters": {"copy_color_role": chosen},
        "parameter_choice": (
            "seed_modulo_two"
            if copy_color_role is None
            else "explicit_once_per_episode"
        ),
        "racket_program": program,
        "racket_sha256": sha256(program),
        "pairs": [
            {"input": grid, "output": evaluate(bridge, program, grid)}
            for grid in inputs
        ],
    }


def public_challenge(episode):
    """Project an episode to three labeled demos and one unlabeled query."""
    return deepcopy(
        {
            "train": episode["pairs"][:3],
            "test": [{"input": episode["pairs"][3]["input"]}],
        }
    )


def analyze_episode(bridge, episode, *, root=None):
    """Check the one declared counterfactual against every query rotation."""
    pairs = episode["pairs"]
    if len(pairs) != 4:
        raise ValueError("episode must contain exactly four input/output pairs")
    chosen = _validate_copy_color_role(episode["parameters"]["copy_color_role"])
    rival_role = next(role for role in COPY_COLOR_ROLES if role != chosen)
    rival_program = instantiate_rule(rival_role, root=root)
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
            "name": f"copy_color_role={rival_role}",
            "parameters": {"copy_color_role": rival_role},
            "racket_sha256": sha256(rival_program),
            "refuting_demonstration_indices": refutations,
            "fits_demonstrations": not refutations,
            "query_differs": (
                rival_outputs[query_index] != pairs[query_index]["output"]
            ),
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
        "counterfactual_role": rival_role,
        "counterfactual_outputs": rival_outputs,
    }


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _file_inventory(out, *, exclude=()):
    excluded = {Path(item).as_posix() for item in exclude}
    return {
        path.relative_to(out).as_posix(): {
            "sha256": sha256(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(out.rglob("*"))
        if path.is_file() and path.relative_to(out).as_posix() not in excluded
    }


def materialize(out, *, seed=0, bridge=None):
    """Create a new, immutable public/private evidence tree."""
    choose_copy_color_role(seed)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = find_root(__file__)
    _, generator_path, generator_sha = load_selected_generator(TASK_ID, root=root)
    report = {
        "schema": SCHEMA,
        "status": "incomplete",
        "scope": (
            "Proposed task-local parametric extension only; not a canonical "
            "rule change, production approval, or generator-axis approval."
        ),
        "parameter_spec": {
            "copy_color_role": {
                "allowed": list(COPY_COLOR_ROLES),
                "original_default": DEFAULT_COPY_COLOR_ROLE,
                "meaning": (
                    "Color used for reflected terrain: marker/paint role or "
                    "source/terrain role."
                ),
            }
        },
        "choice_policy": (
            "Exactly one value per episode: ['paint','source'][seed % 2]. "
            "Two consecutive seeds cover both settings."
        ),
        "lesson_policy": (
            "Three demonstrations followed by one query; also test all four "
            "single-query rotations against the other parameter value."
        ),
        "input_domain": (
            "Four deterministic strict-valid scenes from the selected generator: "
            "three public-profile geometries and one shallow extrapolation, with "
            "fixed difficulty/profile/orientation controls and independently "
            "drawn role palettes."
        ),
        "limitations": (
            "Two consecutive seeds and one declared rival per episode only. "
            "The prototype proves executable labels and local identifiability "
            "on this bounded sample; it does not prove broad curriculum value."
        ),
        "source_hashes": {
            "prototype.py": sha256(Path(__file__).read_bytes()),
            "selected_generator": generator_sha,
            "selected_generator_path": str(generator_path.relative_to(root)),
            "canonical_racket": sha256(canonical_rule(root=root)),
        },
        "invocation": {
            "cwd": str(Path.cwd()),
            "argv": [sys.executable, *sys.argv],
            "seed": seed,
        },
        "canonical_checks": [],
        "episodes": [],
    }

    try:
        manager = nullcontext(bridge) if bridge is not None else RacketBridge()
        with manager as active:
            report["runtime"] = {
                "python": sys.version,
                "racket_version": active.eval_text("(version)"),
                "bridge_sha256": sha256(
                    Path(sys.modules[RacketBridge.__module__].__file__).read_bytes()
                ),
                "prelude_sha256": sha256(Path(active.prelude_path).read_bytes()),
            }

            rules = {
                role: instantiate_rule(role, root=root) for role in COPY_COLOR_ROLES
            }
            for role, program in rules.items():
                path = out / "private" / "rules" / f"copy-{role}.rkt"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(program, encoding="utf-8")

            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = evaluate(active, rules[DEFAULT_COPY_COLOR_ROLE], pair["input"])
                report["canonical_checks"].append(
                    {
                        "variant": pair["variant"],
                        "split": pair["split"],
                        "pair_index": pair["pair_index"],
                        "input": pair["input"],
                        "expected": pair["output"],
                        "actual": actual,
                        "passed": actual == pair["output"],
                    }
                )

            all_inputs = set()
            for index in range(2):
                episode = make_episode(active, seed + index, root=root)
                analysis = analyze_episode(active, episode, root=root)
                public_path = f"public/episode-{index + 1:03d}.json"
                private_path = f"private/episode-{index + 1:03d}.json"
                write_json(out / public_path, public_challenge(episode))
                write_json(
                    out / private_path,
                    {**episode, "rival_checks": analysis},
                )
                report["episodes"].append(
                    {
                        "seed": episode["seed"],
                        "parameters": episode["parameters"],
                        "racket_sha256": episode["racket_sha256"],
                        "public_path": public_path,
                        "private_path": private_path,
                        "production": analysis["production"],
                        "rotations": analysis["rotations"],
                    }
                )
                all_inputs.update(
                    json.dumps(pair["input"], separators=(",", ":"))
                    for pair in episode["pairs"]
                )
                if episode["parameters"]["copy_color_role"] == "paint":
                    report["setting_witness"] = {
                        "input": episode["pairs"][0]["input"],
                        "outputs": {
                            "paint": episode["pairs"][0]["output"],
                            "source": analysis["counterfactual_outputs"][0],
                        },
                        "racket_hashes": {
                            role: sha256(program) for role, program in rules.items()
                        },
                    }

            production_ambiguities = sum(
                episode["production"]["status"] == "ambiguous"
                for episode in report["episodes"]
            )
            rotation_ambiguities = sum(
                score["status"] == "ambiguous"
                for episode in report["episodes"]
                for score in episode["rotations"]
            )
            canonical_passed = sum(
                row["passed"] for row in report["canonical_checks"]
            )
            roles_seen = {
                row["parameters"]["copy_color_role"] for row in report["episodes"]
            }
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
                and roles_seen == set(COPY_COLOR_ROLES)
                and len(all_inputs) == 8
                else "failed"
            )
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        write_json(out / "report.json", report)
        raise

    write_json(out / "report.json", report)
    manifest = {
        "schema": f"{SCHEMA}-manifest-v1",
        "files": _file_inventory(out),
    }
    write_json(out / "manifest.json", manifest)
    verification = verify_tree(out, bridge=bridge)
    write_json(out / "verification.json", verification)
    if verification["status"] != "pass":
        raise RuntimeError(
            "materialized evidence failed self-verification: "
            + "; ".join(verification["failures"])
        )
    return report


def verify_tree(out, *, bridge=None):
    """Rehash and Racket-reexecute a materialized evidence tree."""
    out = Path(out).resolve()
    failures = []
    checked_files = 0
    checked_labels = 0
    try:
        report = json.loads((out / "report.json").read_text(encoding="utf-8"))
        manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "status": "fail",
            "failures": [f"cannot load report/manifest: {type(exc).__name__}: {exc}"],
            "checked_files": 0,
            "checked_labels": 0,
        }

    for relative, expected in manifest.get("files", {}).items():
        path = out / relative
        if not path.is_file():
            failures.append(f"missing manifest file: {relative}")
            continue
        checked_files += 1
        if path.stat().st_size != expected.get("bytes"):
            failures.append(f"size mismatch: {relative}")
        if sha256(path.read_bytes()) != expected.get("sha256"):
            failures.append(f"sha256 mismatch: {relative}")

    root = find_root(__file__)
    for role in COPY_COLOR_ROLES:
        path = out / "private" / "rules" / f"copy-{role}.rkt"
        try:
            actual = path.read_text(encoding="utf-8")
            if actual != instantiate_rule(role, root=root):
                failures.append(f"rule mismatch: {role}")
        except Exception as exc:
            failures.append(f"cannot read rule {role}: {type(exc).__name__}: {exc}")

    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    try:
        with manager as active:
            for row in report.get("canonical_checks", []):
                actual = evaluate(
                    active,
                    instantiate_rule(DEFAULT_COPY_COLOR_ROLE, root=root),
                    row["input"],
                )
                checked_labels += 1
                if actual != row["expected"] or actual != row["actual"]:
                    failures.append(
                        "canonical label mismatch: "
                        f"variant={row.get('variant')} split={row.get('split')} "
                        f"pair={row.get('pair_index')}"
                    )

            for summary in report.get("episodes", []):
                public_path = out / summary["public_path"]
                private_path = out / summary["private_path"]
                try:
                    public = json.loads(public_path.read_text(encoding="utf-8"))
                    private = json.loads(private_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    failures.append(
                        f"cannot load episode {summary.get('seed')}: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    continue
                expected_public = public_challenge(private)
                if public != expected_public:
                    failures.append(f"public/private projection mismatch: seed={summary['seed']}")
                if set(public) != {"train", "test"}:
                    failures.append(f"public schema leak: seed={summary['seed']}")
                elif len(public.get("test", [])) != 1 or set(public["test"][0]) != {"input"}:
                    failures.append(f"public query label leak: seed={summary['seed']}")

                role = private.get("parameters", {}).get("copy_color_role")
                try:
                    program = instantiate_rule(role, root=root)
                except Exception as exc:
                    failures.append(
                        f"invalid episode parameter seed={summary['seed']}: {exc}"
                    )
                    continue
                if private.get("racket_program") != program:
                    failures.append(f"episode program mismatch: seed={summary['seed']}")
                if private.get("racket_sha256") != sha256(program):
                    failures.append(f"episode program hash mismatch: seed={summary['seed']}")
                for pair_index, pair in enumerate(private.get("pairs", [])):
                    actual = evaluate(active, program, pair["input"])
                    checked_labels += 1
                    if actual != pair["output"]:
                        failures.append(
                            f"episode label mismatch: seed={summary['seed']} "
                            f"pair={pair_index}"
                        )
                analysis = analyze_episode(active, private, root=root)
                saved = private.get("rival_checks")
                if saved != analysis:
                    failures.append(f"rival analysis mismatch: seed={summary['seed']}")
                checked_labels += len(private.get("pairs", []))
    except Exception as exc:
        failures.append(f"Racket verification error: {type(exc).__name__}: {exc}")

    expected_status = "no_ambiguity_found"
    if report.get("status") != expected_status:
        failures.append(
            f"report status is {report.get('status')!r}, expected {expected_status!r}"
        )
    return {
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "checked_files": checked_files,
        "checked_labels": checked_labels,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    materialize_parser = subparsers.add_parser("materialize")
    materialize_parser.add_argument("--seed", type=int, default=0)
    materialize_parser.add_argument("--out", type=Path, required=True)
    verify_parser = subparsers.add_parser("verify")
    verify_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "materialize":
        result = materialize(args.out, seed=args.seed)
        payload = {
            "status": result["status"],
            "counts": result["counts"],
            "report": str(args.out / "report.json"),
        }
        code = int(result["status"] != "no_ambiguity_found")
    else:
        result = verify_tree(args.out)
        payload = result
        code = int(result["status"] != "pass")
    print(json.dumps(payload, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
