"""Racket-backed episode prototype for bounded frame-chain replication.

This is proposed task-local evidence, not a canonical rule change.  The
canonical/default setting repeats every selected 4x4 frame to the marked edge.
The alternative performs the same selection, direction, color, and 4-cell
translation reasoning, but emits only the first translated copy per marker.
Every retained label is produced by the corresponding Racket program.
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
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    normalize_grid,
)


TASK_ID = "f4d4fb4404c6"
PARAMETER_NAME = "copy_limit"
COPY_LIMITS = ("to_edge", "one_copy")
DEFAULT_COPY_LIMIT = "to_edge"
SCHEMA = "f4d4fb4404c6-copy-limit-prototype-v1"

WORKSPACE = Path(__file__).resolve().parent.parent
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
from reference_probe import (  # noqa: E402
    intended_output,
    load_generator,
    rival_one_copy_only,
)


_LOOP_REPLACEMENTS = (
    (
        """(loop (- r 4)
                            (draw-frame acc (first f) (- r 4) (third f)
                                        (- r 1) (fifth f)))""",
        """(draw-frame acc (first f) (- r 4) (third f)
                                  (- r 1) (fifth f))""",
    ),
    (
        """(loop (+ r 4)
                            (draw-frame acc (first f) (+ r 1) (third f)
                                        (+ r 4) (fifth f)))""",
        """(draw-frame acc (first f) (+ r 1) (third f)
                                  (+ r 4) (fifth f))""",
    ),
    (
        """(loop (- c 4)
                            (draw-frame acc (first f) (second f) (- c 4)
                                        (fourth f) (- c 1)))""",
        """(draw-frame acc (first f) (second f) (- c 4)
                                  (fourth f) (- c 1))""",
    ),
    (
        """(loop (+ c 4)
                            (draw-frame acc (first f) (second f) (+ c 1)
                                        (fourth f) (+ c 4)))""",
        """(draw-frame acc (first f) (second f) (+ c 1)
                                  (fourth f) (+ c 4))""",
    ),
)


def sha256(value: str | bytes) -> str:
    payload = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _root(root=None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


@lru_cache(maxsize=8)
def _canonical_rule_for_root(root_text: str) -> str:
    root = Path(root_text)
    sources = []
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                sources.append(row["program_solution"])
    unique = list(dict.fromkeys(sources))
    if len(unique) != 1:
        raise ValueError(
            "copy_limit requires one exact canonical rule across variants; "
            f"found {len(unique)} distinct sources"
        )
    return unique[0]


def canonical_rule(*, root=None) -> str:
    """Return the exact selected canonical authority without normalization."""
    return _canonical_rule_for_root(str(_root(root)))


def _validate_copy_limit(copy_limit) -> str:
    if type(copy_limit) is not str or copy_limit not in COPY_LIMITS:
        raise ValueError("copy_limit must be exactly 'to_edge' or 'one_copy'")
    return copy_limit


def choose_parameters(episode_seed: int) -> dict[str, str]:
    """Choose exactly one transformation setting for an entire episode."""
    if type(episode_seed) is not int:
        raise TypeError("episode seed must be a Python int")
    return {PARAMETER_NAME: COPY_LIMITS[episode_seed % len(COPY_LIMITS)]}


def instantiate_rule(copy_limit=DEFAULT_COPY_LIMIT, *, root=None) -> str:
    """Materialize exact Racket for one bounded copy-limit setting."""
    setting = _validate_copy_limit(copy_limit)
    source = canonical_rule(root=root)
    if setting == DEFAULT_COPY_LIMIT:
        return source

    changed = source
    for old, new in _LOOP_REPLACEMENTS:
        count = changed.count(old)
        if count != 1:
            raise ValueError(
                "Canonical replication loop changed; expected one exact site, "
                f"found {count}. Manually reassess copy_limit."
            )
        changed = changed.replace(old, new, 1)
    if changed == source:
        raise ValueError("copy_limit='one_copy' did not change the authority")
    return changed


def _racket_datum(grid) -> str:
    return "(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def evaluate(bridge, program: str, grid):
    """Execute a grid using the supplied live Racket bridge."""
    normalized = normalize_grid(grid)
    body = strip_rule_wrapper(strip_line_comments(program)).strip()
    if not body.startswith("(lambda (g)"):
        raise ValueError("expected the selected task's exact Racket lambda")
    function = (
        "(lambda (g) (let* ((h (rows g)) (w (cols g))) "
        f"({body} g)))"
    )
    expression = f"({function} '{_racket_datum(normalized)})"
    return normalize_grid(bridge.eval_text(expression))


def python_reference(grid, *, copy_limit=DEFAULT_COPY_LIMIT):
    """Independent task-local oracle used only to cross-check Racket labels."""
    setting = _validate_copy_limit(copy_limit)
    if setting == "to_edge":
        return intended_output(grid)
    return rival_one_copy_only(grid)


def generate_inputs(episode_seed: int, *, root=None) -> list[list[list[int]]]:
    """Draw four lawful inputs whose outputs differ under both settings."""
    choose_parameters(episode_seed)
    root = _root(root)
    generator = load_generator(root / f"generators/{TASK_ID}/generator.py")
    profiles = tuple(generator.SCENE_PROFILES)
    if len(profiles) != 4:
        raise ValueError(f"expected four selected scene profiles, got {len(profiles)}")
    bands = ("easy", "medium", "hard", "medium")
    inputs = []
    for index, (profile, band) in enumerate(zip(profiles, bands)):
        grid = generator.generate(
            310_000 + episode_seed * 131 + index,
            index,
            difficulty=band,
            scene_profile=profile,
        )
        issues = generator.self_check(grid, difficulty=band)
        if issues:
            raise RuntimeError(
                f"generated invalid parametric input index={index}: {issues}"
            )
        normalized = normalize_grid(grid)
        if python_reference(normalized, copy_limit="to_edge") == python_reference(
            normalized, copy_limit="one_copy"
        ):
            raise RuntimeError(
                f"parametric input index={index} does not distinguish copy_limit"
            )
        inputs.append(normalized)
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in inputs}
    if len(fingerprints) != len(inputs):
        raise RuntimeError("parametric input sampler produced a duplicate grid")
    return inputs


def make_episode(
    bridge,
    episode_seed: int,
    *,
    copy_limit=None,
    root=None,
) -> dict:
    """Bind one parameter value and Racket-label all four episode pairs."""
    chosen = (
        choose_parameters(episode_seed)[PARAMETER_NAME]
        if copy_limit is None
        else _validate_copy_limit(copy_limit)
    )
    program = instantiate_rule(chosen, root=root)
    pairs = [
        {"input": grid, "output": evaluate(bridge, program, grid)}
        for grid in generate_inputs(episode_seed, root=root)
    ]
    return {
        "schema": f"{SCHEMA}-episode-v1",
        "seed": episode_seed,
        "parameters": {PARAMETER_NAME: chosen},
        "parameter_choice": (
            "seed_modulo_two_once_per_episode"
            if copy_limit is None
            else "explicit_once_per_episode"
        ),
        "racket_program": program,
        "racket_sha256": sha256(program),
        "pairs": pairs,
    }


def public_challenge(episode: dict) -> dict:
    """Redact parameter, code, and query label from a four-pair episode."""
    pairs = episode["pairs"]
    if len(pairs) != 4:
        raise ValueError("episode must contain exactly four pairs")
    return deepcopy(
        {
            "train": pairs[:3],
            "test": [{"input": pairs[3]["input"]}],
        }
    )


def analyze_episode(bridge, episode: dict, *, root=None) -> dict:
    """Test the other setting against production order and every query rotation."""
    pairs = episode["pairs"]
    if len(pairs) != 4:
        raise ValueError("episode must contain exactly four pairs")
    chosen = _validate_copy_limit(episode["parameters"][PARAMETER_NAME])
    rival_setting = next(value for value in COPY_LIMITS if value != chosen)
    rival_program = instantiate_rule(rival_setting, root=root)
    rival_outputs = [
        evaluate(bridge, rival_program, pair["input"]) for pair in pairs
    ]

    def score(query_index: int) -> dict:
        demonstrations = [index for index in range(4) if index != query_index]
        refutations = [
            index
            for index in demonstrations
            if rival_outputs[index] != pairs[index]["output"]
        ]
        query_differs = rival_outputs[query_index] != pairs[query_index]["output"]
        ambiguous = not refutations and query_differs
        return {
            "query_index": query_index,
            "demonstration_indices": demonstrations,
            "rival": {
                "name": f"copy_limit={rival_setting}",
                "parameters": {PARAMETER_NAME: rival_setting},
                "racket_sha256": sha256(rival_program),
                "refuting_demonstration_indices": refutations,
                "fits_demonstrations": not refutations,
                "query_differs": query_differs,
            },
            "status": "ambiguous" if ambiguous else "no_ambiguity_found",
        }

    return {
        "production": score(3),
        "rotations": [score(index) for index in range(4)],
        "counterfactual_setting": rival_setting,
        "counterfactual_outputs": rival_outputs,
    }


def write_json(path, value) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_inventory(out: Path, *, exclude=()) -> dict:
    excluded = {Path(item).as_posix() for item in exclude}
    return {
        path.relative_to(out).as_posix(): {
            "sha256": sha256(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(out.rglob("*"))
        if path.is_file() and path.relative_to(out).as_posix() not in excluded
    }


def materialize(out, *, seed=0, bridge=None) -> dict:
    """Write a new immutable public/private evidence tree and verify it."""
    choose_parameters(seed)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    root = _root()
    generator_path = root / f"generators/{TASK_ID}/generator.py"
    generator_sha = sha256(generator_path.read_bytes())
    prototype_path = Path(__file__).resolve()
    canonical_file = canonical_path(root)
    rules = {setting: instantiate_rule(setting, root=root) for setting in COPY_LIMITS}

    for setting, program in rules.items():
        name = setting.replace("_", "-")
        path = out / "private/rules" / f"copy-limit-{name}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program, encoding="utf-8")

    report = {
        "schema": SCHEMA,
        "status": "incomplete",
        "scope": (
            "Proposed task-local parametric extension only; it does not alter or "
            "approve the selected canonical rule or production generator."
        ),
        "parameter_spec": {
            PARAMETER_NAME: {
                "allowed": list(COPY_LIMITS),
                "original_default": DEFAULT_COPY_LIMIT,
                "meaning": (
                    "Number of translated frame copies emitted per edge marker: "
                    "repeat to the edge or stop after the first copy."
                ),
                "input_constraints": (
                    "Every marker must identify one frame and have room for one "
                    "full copy; retained episode inputs also have room for at least "
                    "two copies so the settings visibly disagree."
                ),
            }
        },
        "invariant_reasoning": [
            "find hollow 4x4 frames",
            "find blue edge markers and infer direction",
            "select the uniquely overlapping frame",
            "preserve that frame's color and move in 4-cell steps",
        ],
        "choice_policy": (
            "Choose one setting once per episode as COPY_LIMITS[seed % 2]; "
            "two consecutive seeds cover both settings."
        ),
        "lesson_policy": (
            "Three labeled demonstrations plus one unlabeled query; evaluate all "
            "four single-query rotations against the other setting."
        ),
        "source_bindings": {
            "generator_path": str(Path(generator_path).relative_to(root)),
            "generator_sha256": generator_sha,
            "prototype_path": str(prototype_path.relative_to(root)),
            "prototype_sha256": sha256(prototype_path.read_bytes()),
            "canonical_path": str(canonical_file.relative_to(root)),
            "canonical_file_sha256": sha256(canonical_file.read_bytes()),
            "canonical_program_sha256": sha256(rules[DEFAULT_COPY_LIMIT]),
            "setting_program_sha256": {
                setting: sha256(program) for setting, program in rules.items()
            },
        },
        "execution": {
            "cwd": str(Path.cwd()),
            "argv": list(sys.argv),
            "label_engine": "live RacketBridge execution",
        },
        "canonical_checks": [],
        "episodes": [],
        "limitations": [
            "Only two bounded settings are evaluated.",
            "Finite generated episodes refute only the declared parameter rival.",
            "The alternative is proposed evidence, not a production API or approval.",
            "Inputs intentionally avoid chain collisions, matching the selected domain.",
        ],
    }

    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    try:
        with manager as active:
            default_program = rules[DEFAULT_COPY_LIMIT]
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = evaluate(active, default_program, pair["input"])
                report["canonical_checks"].append(
                    {
                        "variant": pair.get("variant"),
                        "split": pair.get("split"),
                        "pair_index": pair.get("pair_index"),
                        "input": pair["input"],
                        "expected": pair["output"],
                        "actual": actual,
                        "passed": actual == pair["output"],
                    }
                )

            all_inputs = set()
            witness = None
            for episode_index in range(2):
                episode = make_episode(active, seed + episode_index, root=root)
                analysis = analyze_episode(active, episode, root=root)
                public_path = f"public/episode-{episode_index + 1:03d}.json"
                private_path = f"private/episode-{episode_index + 1:03d}.json"
                write_json(out / public_path, public_challenge(episode))
                write_json(out / private_path, {**episode, "rival_checks": analysis})
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
                if witness is None:
                    grid = episode["pairs"][0]["input"]
                    outputs = {
                        setting: evaluate(active, program, grid)
                        for setting, program in rules.items()
                    }
                    if len({json.dumps(value) for value in outputs.values()}) == 2:
                        witness = {
                            "input": grid,
                            "outputs": outputs,
                            "racket_sha256": {
                                setting: sha256(program)
                                for setting, program in rules.items()
                            },
                        }

            if witness is None:
                raise RuntimeError("no setting-difference witness was materialized")
            write_json(out / "private/setting-difference-witness.json", witness)

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
            settings_seen = {
                row["parameters"][PARAMETER_NAME] for row in report["episodes"]
            }
            report["counts"] = {
                "canonical_labels_checked": len(report["canonical_checks"]),
                "canonical_labels_passed": canonical_passed,
                "episodes": len(report["episodes"]),
                "demonstrations": 3 * len(report["episodes"]),
                "queries": len(report["episodes"]),
                "episode_labels": 4 * len(report["episodes"]),
                "counterfactual_labels": 4 * len(report["episodes"]),
                "query_rotations": 4 * len(report["episodes"]),
                "production_ambiguities": production_ambiguities,
                "rotation_ambiguities": rotation_ambiguities,
                "unique_episode_inputs": len(all_inputs),
            }
            report["status"] = (
                "no_ambiguity_found"
                if canonical_passed == len(report["canonical_checks"])
                and settings_seen == set(COPY_LIMITS)
                and len(all_inputs) == 8
                and production_ambiguities == 0
                and rotation_ambiguities == 0
                else "failed"
            )
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        write_json(out / "report.json", report)
        raise

    write_json(out / "report.json", report)
    write_json(
        out / "manifest.json",
        {"schema": f"{SCHEMA}-manifest-v1", "files": _file_inventory(out)},
    )
    verification = verify_tree(out, bridge=bridge)
    write_json(out / "verification.json", verification)
    if verification["status"] != "pass":
        raise RuntimeError(
            "materialized evidence failed self-verification: "
            + "; ".join(verification["failures"])
        )
    return report


def verify_tree(out, *, bridge=None) -> dict:
    """Rehash, redact-check, and Racket-reexecute a materialized tree."""
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

    root = _root()
    rules = {}
    for setting in COPY_LIMITS:
        path = out / "private/rules" / f"copy-limit-{setting.replace('_', '-')}.rkt"
        try:
            actual = path.read_text(encoding="utf-8")
            expected = instantiate_rule(setting, root=root)
            rules[setting] = expected
            if actual != expected:
                failures.append(f"rule mismatch: {setting}")
        except Exception as exc:
            failures.append(f"cannot read rule {setting}: {type(exc).__name__}: {exc}")

    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    try:
        with manager as active:
            for row in report.get("canonical_checks", []):
                actual = evaluate(active, rules[DEFAULT_COPY_LIMIT], row["input"])
                checked_labels += 1
                if actual != row["expected"] or actual != row["actual"]:
                    failures.append(
                        "canonical label mismatch: "
                        f"variant={row.get('variant')} split={row.get('split')} "
                        f"pair={row.get('pair_index')}"
                    )

            for summary in report.get("episodes", []):
                try:
                    public = json.loads(
                        (out / summary["public_path"]).read_text(encoding="utf-8")
                    )
                    private = json.loads(
                        (out / summary["private_path"]).read_text(encoding="utf-8")
                    )
                except Exception as exc:
                    failures.append(
                        f"cannot load episode seed={summary.get('seed')}: "
                        f"{type(exc).__name__}: {exc}"
                    )
                    continue
                if public != public_challenge(private):
                    failures.append(
                        f"public/private projection mismatch: seed={summary['seed']}"
                    )
                if set(public) != {"train", "test"}:
                    failures.append(f"public schema leak: seed={summary['seed']}")
                elif (
                    len(public.get("test", [])) != 1
                    or set(public["test"][0]) != {"input"}
                ):
                    failures.append(f"public query label leak: seed={summary['seed']}")
                serialized = json.dumps(public, sort_keys=True).lower()
                if "copy_limit" in serialized or "racket" in serialized:
                    failures.append(f"public hidden-state leak: seed={summary['seed']}")

                setting = private.get("parameters", {}).get(PARAMETER_NAME)
                try:
                    program = instantiate_rule(setting, root=root)
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
                            f"episode label mismatch: seed={summary['seed']} pair={pair_index}"
                        )
                    reference = python_reference(pair["input"], copy_limit=setting)
                    if actual != reference:
                        failures.append(
                            f"independent reference mismatch: seed={summary['seed']} "
                            f"pair={pair_index}"
                        )
                recomputed = analyze_episode(active, private, root=root)
                if recomputed != private.get("rival_checks"):
                    failures.append(f"rival analysis mismatch: seed={summary['seed']}")
    except Exception as exc:
        failures.append(f"Racket replay failed: {type(exc).__name__}: {exc}")

    return {
        "schema": f"{SCHEMA}-verification-v1",
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "checked_files": checked_files,
        "checked_labels": checked_labels,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("materialize", help="create and verify a fresh evidence tree")
    build.add_argument("--out", required=True)
    build.add_argument("--seed", type=int, default=0)
    verify = sub.add_parser("verify", help="rehash and Racket-replay an evidence tree")
    verify.add_argument("--out", required=True)
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "materialize":
        result = materialize(args.out, seed=args.seed)
        print(json.dumps({"status": result["status"], "counts": result["counts"]}, indent=2))
        return 0 if result["status"] == "no_ambiguity_found" else 1
    result = verify_tree(args.out)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
