"""Task-local survivor-role parameter prototype for ead22faa41ef.

The production generator keeps its canonical default unchanged.  This opt-in
prototype chooses exactly one survivor role per episode, generates inputs
without consulting that hidden setting, labels every demonstration and query
with the corresponding exact Racket program, and checks four queries against
both the other parameter setting and the historical global-replacement
shortcut using demonstrations only.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "ead22faa41ef"
CANONICAL_SHA256 = "fc2471b9a0fe8f3bf1318728a845cb54408e2d80744b6da6deca664a681cdbaa"
SURVIVOR_ROLES = ("green3", "red2")
DEFAULT_SURVIVOR_ROLE = "green3"
ROLE_DESCRIPTION = {
    "green3": "paired green 3 survives as cyan 8; paired red 2 is erased to 0",
    "red2": "paired red 2 survives as cyan 8; paired green 3 is erased to 0",
}
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

_CANONICAL_GREEN_SITE = "(and (< c (- w 1)) (= 2 (at g r (+ c 1)))))) 8)"
_ALTERNATIVE_GREEN_SITE = "(and (< c (- w 1)) (= 2 (at g r (+ c 1)))))) 0)"
_CANONICAL_RED_SITE = "(and (< c (- w 1)) (= 3 (at g r (+ c 1)))))) 0)"
_ALTERNATIVE_RED_SITE = "(and (< c (- w 1)) (= 3 (at g r (+ c 1)))))) 8)"
_PUBLIC_NAME_RE = re.compile(r"challenge-[0-9a-f]{64}\.json\Z")
_COUNT_LIMIT = 12


def sha256(value: str | bytes) -> str:
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_seed(seed: int) -> None:
    if type(seed) is not int:
        raise TypeError("seed must be a plain Python integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")


def _validate_count(name: str, value: int) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be a plain Python integer")
    if not 1 <= value <= _COUNT_LIMIT:
        raise ValueError(f"{name} must be between 1 and {_COUNT_LIMIT}")


def _validate_setting(survivor_role: str) -> None:
    if type(survivor_role) is not str or survivor_role not in SURVIVOR_ROLES:
        raise ValueError(f"survivor_role must be one of {SURVIVOR_ROLES}")


def canonical_rule(*, root=None) -> str:
    """Return the selected canonical Racket rule, byte-for-byte and hash-pinned."""
    selected_root = ROOT if root is None else Path(root).resolve()
    matches: list[str] = []
    with canonical_path(selected_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                matches.append(row["program_solution"])
    if len(matches) != 1:
        raise ValueError("prototype requires exactly one selected canonical rule")
    source = matches[0]
    actual = sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket hash changed: expected {CANONICAL_SHA256}, got {actual}"
        )
    for site in (_CANONICAL_GREEN_SITE, _CANONICAL_RED_SITE):
        if source.count(site) != 1:
            raise ValueError("canonical survivor output site changed; reassess prototype")
    return source


def instantiate_rule(
    survivor_role: str = DEFAULT_SURVIVOR_ROLE, *, root=None
) -> str:
    """Materialize the exact canonical rule or the declared role-swapped rule."""
    _validate_setting(survivor_role)
    source = canonical_rule(root=root)
    if survivor_role == DEFAULT_SURVIVOR_ROLE:
        return source
    alternative = source.replace(
        _CANONICAL_GREEN_SITE, _ALTERNATIVE_GREEN_SITE, 1
    ).replace(_CANONICAL_RED_SITE, _ALTERNATIVE_RED_SITE, 1)
    if alternative == source:
        raise ValueError("alternative survivor role did not change the program")
    return alternative


def restore_canonical(program: str, *, root=None) -> str:
    """Prove that a generated rule differs only at the declared output sites."""
    if type(program) is not str:
        raise TypeError("program must be Racket source text")
    canonical = canonical_rule(root=root)
    if program == canonical:
        return canonical
    restored = program.replace(
        _ALTERNATIVE_GREEN_SITE, _CANONICAL_GREEN_SITE, 1
    ).replace(_ALTERNATIVE_RED_SITE, _CANONICAL_RED_SITE, 1)
    if restored != canonical or sha256(restored) != CANONICAL_SHA256:
        raise ValueError("program is not a declared survivor-role variant")
    return restored


def evaluate(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Execute one exact rule through the packet's Racket authority."""
    normalized = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("expected the selected task's native Racket lambda")
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def choose_survivor_role(seed: int) -> str:
    """Choose exactly one hidden setting for a complete episode."""
    _validate_seed(seed)
    return SURVIVOR_ROLES[seed % len(SURVIVOR_ROLES)]


def _has_required_witnesses(grid) -> bool:
    features = GEN._scene_features(grid)
    paired3 = len(features["paired3"])
    paired2 = len(features["paired2"])
    return (
        paired3 >= 1
        and features["counts"][3] - paired3 >= 1
        and features["counts"][2] - paired2 >= 1
    )


def generate_inputs(
    seed: int, *, demo_count: int = 3, query_count: int = 4
) -> list[list[list[int]]]:
    """Generate distinct lawful inputs independently of the hidden role setting."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    total = demo_count + query_count
    bands = ("easy", "medium", "hard", "medium")
    generation_seed = 910_003 + seed * 10_019
    result: list[list[list[int]]] = []
    seen: set[str] = set()
    candidate_index = 0
    max_attempts = max(256, total * 32)
    while len(result) < total and candidate_index < max_attempts:
        grid = GEN.generate(
            generation_seed,
            candidate_index,
            difficulty=bands[candidate_index % len(bands)],
        )
        errors = GEN.self_check(grid)
        if errors:
            raise RuntimeError(
                "selected generator returned an unlawful input: " + "; ".join(errors)
            )
        key = json.dumps(grid, separators=(",", ":"))
        if key not in seen and _has_required_witnesses(grid):
            seen.add(key)
            result.append(deepcopy(grid))
        candidate_index += 1
    if len(result) != total:
        raise RuntimeError(
            f"could not obtain {total} distinct witness-bearing inputs "
            f"in {max_attempts} attempts"
        )
    return result


def make_episode(
    bridge: RacketBridge,
    seed: int,
    *,
    survivor_role: str | None = None,
    demo_count: int = 3,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one private episode; every label comes from its matching Racket rule."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    chosen = choose_survivor_role(seed) if survivor_role is None else survivor_role
    _validate_setting(chosen)
    program = instantiate_rule(chosen)
    inputs = generate_inputs(seed, demo_count=demo_count, query_count=query_count)
    return {
        "schema": "ead22faa41ef-survivor-role-episode-v1",
        "seed": seed,
        "parameters": {"survivor_role": chosen},
        "parameter_choice": (
            "seed_modulo_two" if survivor_role is None else "explicit_once_per_episode"
        ),
        "role_description": ROLE_DESCRIPTION[chosen],
        "demo_count": demo_count,
        "query_count": query_count,
        "racket_program": program,
        "racket_sha256": sha256(program),
        "generator_sha256": GENERATOR_SHA256,
        "pairs": [
            {"input": grid, "output": evaluate(bridge, program, grid)}
            for grid in inputs
        ],
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project private evidence to visible demonstrations and hidden queries."""
    demo_count = episode.get("demo_count")
    query_count = episode.get("query_count")
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    pairs = episode.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != demo_count + query_count:
        raise ValueError("episode pair count does not match demo_count + query_count")
    challenge = deepcopy(
        {
            "train": [
                {"input": pair["input"], "output": pair["output"]}
                for pair in pairs[:demo_count]
            ],
            "test": [
                {"input": pair["input"]}
                for pair in pairs[demo_count:]
            ],
        }
    )
    public_challenge_bytes(challenge)
    return challenge


def public_filename(challenge: dict[str, Any]) -> str:
    """Return a visible-content-only opaque filename."""
    return f"challenge-{public_challenge_id(challenge)}.json"


def _global_replacement(grid, survivor_role: str) -> list[list[int]]:
    _validate_setting(survivor_role)
    green, red = ((8, 0) if survivor_role == "green3" else (0, 8))
    source = normalize_grid(grid)
    return [
        [green if value == 3 else red if value == 2 else value for value in row]
        for row in source
    ]


def analyze_episode(
    bridge: RacketBridge, episode: dict[str, Any]
) -> dict[str, Any]:
    """Check declared rivals using labeled demonstrations only."""
    parameters = episode.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("episode is missing parameters")
    chosen = parameters.get("survivor_role")
    _validate_setting(chosen)
    demo_count = episode.get("demo_count")
    query_count = episode.get("query_count")
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    pairs = episode.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != demo_count + query_count:
        raise ValueError("episode pair count does not match declared counts")

    alternate = next(role for role in SURVIVOR_ROLES if role != chosen)
    alternate_outputs = [
        evaluate(bridge, instantiate_rule(alternate), pair["input"])
        for pair in pairs
    ]
    global_outputs = [
        _global_replacement(pair["input"], chosen) for pair in pairs
    ]
    rival_specs = (
        (
            "alternate_parameter",
            f"survivor_role={alternate}",
            {"survivor_role": alternate},
            alternate_outputs,
        ),
        (
            "global_replacement",
            f"global_replacement_for={chosen}",
            {"survivor_role": chosen, "adjacency_required": False},
            global_outputs,
        ),
    )

    demonstration_indices = list(range(demo_count))
    query_rows: list[dict[str, Any]] = []
    for pair_index in range(demo_count, len(pairs)):
        rivals: list[dict[str, Any]] = []
        for kind, name, rival_parameters, outputs in rival_specs:
            refutations = [
                index
                for index in demonstration_indices
                if outputs[index] != pairs[index]["output"]
            ]
            rivals.append(
                {
                    "kind": kind,
                    "name": name,
                    "parameters": rival_parameters,
                    "refuting_demonstration_indices": refutations,
                    "fits_demonstrations": not refutations,
                    "query_differs": outputs[pair_index] != pairs[pair_index]["output"],
                    "query_output": outputs[pair_index],
                }
            )
        ambiguous = any(
            rival["fits_demonstrations"] and rival["query_differs"]
            for rival in rivals
        )
        query_rows.append(
            {
                "query_index": pair_index - demo_count,
                "pair_index": pair_index,
                "demonstration_indices": demonstration_indices,
                "rivals": rivals,
                "status": "ambiguous" if ambiguous else "no_ambiguity_found",
            }
        )

    ambiguities = sum(row["status"] == "ambiguous" for row in query_rows)
    return {
        "status": "no_ambiguity_found" if ambiguities == 0 else "ambiguous",
        "chosen_parameters": deepcopy(parameters),
        "demonstration_indices": demonstration_indices,
        "queries": query_rows,
        "counts": {
            "demonstrations": demo_count,
            "queries": query_count,
            "declared_rivals_per_query": len(rival_specs),
            "query_ambiguities": ambiguities,
        },
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _relative_file_receipts(out: Path) -> dict[str, dict[str, Any]]:
    return {
        str(path.relative_to(out)): {
            "sha256": sha256(path.read_bytes()),
            "bytes": path.stat().st_size,
        }
        for path in sorted(out.rglob("*"))
        if path.is_file() and path.name != "report.json"
    }


def materialize(
    out: Path | str,
    *,
    seed: int = 0,
    demo_count: int = 3,
    query_count: int = 4,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write bounded, replayable evidence for both survivor-role settings."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    out = Path(out).resolve()
    if out.exists() or out.is_symlink():
        raise FileExistsError(out)
    report: dict[str, Any] = {
        "schema": "ead22faa41ef-survivor-role-evidence-v1",
        "status": "incomplete",
        "scope": (
            "proposed task-local prototype; not a canonical rule change, "
            "shared production API, approval, or training admission"
        ),
        "parameter_spec": {
            "survivor_role": {
                "allowed": list(SURVIVOR_ROLES),
                "original_default": DEFAULT_SURVIVOR_ROLE,
                "meaning": ROLE_DESCRIPTION,
            }
        },
        "choice_policy": (
            "One role per complete episode. Evidence explicitly covers both settings; "
            "input generation is independent of the hidden setting."
        ),
        "lesson_policy": (
            f"{demo_count} labeled demonstrations followed by {query_count} distinct "
            "queries. Every input contains a pair plus preserved lone 3 and lone 2 "
            "witnesses. Each query is checked against the alternate parameter and "
            "global-replacement rival using demonstrations only."
        ),
        "limitations": (
            "Evidence covers two episodes and two declared rival families. It does not "
            "prove uniqueness against every imaginable rule or authorize shared "
            "runtime/catalog integration."
        ),
        "source_hashes": {
            "prototype.py": sha256(Path(__file__).read_bytes()),
            "generator.py": GENERATOR_SHA256,
            "canonical_racket": sha256(canonical_rule()),
        },
        "generator_path": str(GENERATOR_PATH),
        "invocation": {"cwd": str(Path.cwd()), "argv": [sys.executable, *sys.argv]},
        "canonical_checks": [],
        "episodes": [],
    }
    planned_episodes: list[dict[str, Any]] = []
    try:
        manager = nullcontext(bridge) if bridge is not None else RacketBridge()
        with manager as active:
            assert active is not None
            bridge_module = Path(sys.modules[RacketBridge.__module__].__file__).resolve()
            report["runtime"] = {
                "python": sys.version,
                "racket_version": active.eval_text("(version)"),
                "bridge_path": str(bridge_module),
                "bridge_sha256": sha256(bridge_module.read_bytes()),
                "prelude_path": str(active.prelude_path),
                "prelude_sha256": sha256(Path(active.prelude_path).read_bytes()),
            }

            canonical_program = instantiate_rule(DEFAULT_SURVIVOR_ROLE)
            for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
                actual = evaluate(active, canonical_program, pair["input"])
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

            for episode_index, role in enumerate(SURVIVOR_ROLES):
                episode = make_episode(
                    active,
                    seed + episode_index,
                    survivor_role=role,
                    demo_count=demo_count,
                    query_count=query_count,
                )
                analysis = analyze_episode(active, episode)
                challenge = public_challenge(episode)
                public_name = public_filename(challenge)
                public_path = Path("public") / public_name
                private_path = Path("private") / f"episode-{episode_index + 1:03d}.json"
                planned_episodes.append(
                    {
                        "public_name": public_name,
                        "public_path": public_path,
                        "public_payload": public_challenge_bytes(challenge),
                        "private_path": private_path,
                        "private_payload": {**episode, "analysis": analysis},
                    }
                )
                report["episodes"].append(
                    {
                        "episode_index": episode_index,
                        "seed": episode["seed"],
                        "parameters": episode["parameters"],
                        "racket_sha256": episode["racket_sha256"],
                        "demo_count": demo_count,
                        "query_count": query_count,
                        "public_path": str(public_path),
                        "private_path": str(private_path),
                        "analysis": analysis,
                    }
                )

            public_names = [row["public_name"] for row in planned_episodes]
            if len(set(public_names)) != len(public_names):
                raise ValueError("duplicate visible challenge in materialized batch")

            out.mkdir(parents=True, exist_ok=False)
            for role in SURVIVOR_ROLES:
                rule_path = out / "private" / "rules" / f"survivor-role-{role}.rkt"
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(instantiate_rule(role), encoding="utf-8")
            for planned in sorted(
                planned_episodes, key=lambda row: row["public_name"]
            ):
                public_path = out / planned["public_path"]
                public_path.parent.mkdir(parents=True, exist_ok=True)
                public_path.write_bytes(planned["public_payload"])
            for planned in planned_episodes:
                write_json(
                    out / planned["private_path"], planned["private_payload"]
                )

            witness_input = generate_inputs(
                seed, demo_count=demo_count, query_count=query_count
            )[0]
            report["setting_witness"] = {
                "input": witness_input,
                "outputs": {
                    role: evaluate(active, instantiate_rule(role), witness_input)
                    for role in SURVIVOR_ROLES
                },
                "racket_hashes": {
                    role: sha256(instantiate_rule(role)) for role in SURVIVOR_ROLES
                },
            }

            canonical_passed = sum(
                row["passed"] for row in report["canonical_checks"]
            )
            query_ambiguities = sum(
                row["status"] == "ambiguous"
                for episode in report["episodes"]
                for row in episode["analysis"]["queries"]
            )
            settings_seen_set = {
                episode["parameters"]["survivor_role"]
                for episode in report["episodes"]
            }
            settings_seen = [
                role for role in SURVIVOR_ROLES if role in settings_seen_set
            ]
            all_rivals_refuted = all(
                not rival["fits_demonstrations"]
                for episode in report["episodes"]
                for row in episode["analysis"]["queries"]
                for rival in row["rivals"]
            )
            all_queries_differ = all(
                rival["query_differs"]
                for episode in report["episodes"]
                for row in episode["analysis"]["queries"]
                for rival in row["rivals"]
            )
            witness_outputs = list(report["setting_witness"]["outputs"].values())
            report["counts"] = {
                "canonical_labels": len(report["canonical_checks"]),
                "canonical_labels_passed": canonical_passed,
                "episodes": len(report["episodes"]),
                "demonstrations": len(report["episodes"]) * demo_count,
                "queries": len(report["episodes"]) * query_count,
                "episode_labels": len(report["episodes"]) * (demo_count + query_count),
                "query_ambiguities": query_ambiguities,
                "settings_seen": settings_seen,
            }
            report["status"] = (
                "no_ambiguity_found"
                if len(report["canonical_checks"]) == 4
                and canonical_passed == 4
                and settings_seen_set == set(SURVIVOR_ROLES)
                and len(witness_outputs) == 2
                and witness_outputs[0] != witness_outputs[1]
                and query_ambiguities == 0
                and all_rivals_refuted
                and all_queries_differ
                else "failed"
            )
            report["files"] = _relative_file_receipts(out)
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        if out.exists():
            write_json(out / "report.json", report)
        raise
    write_json(out / "report.json", report)
    return report


def verify_tree(out: Path | str, *, root=None) -> dict[str, Any]:
    """Replay a materialized tree, including all private labels and public views."""
    out = Path(out).resolve()
    selected_root = ROOT if root is None else Path(root).resolve()
    report_path = out / "report.json"
    if not report_path.is_file():
        raise FileNotFoundError(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if report.get("status") != "no_ambiguity_found":
        errors.append(f"materialized report status is {report.get('status')!r}")

    for relative, receipt in report.get("files", {}).items():
        path = (out / relative).resolve()
        if not path.is_relative_to(out):
            errors.append(f"unsafe receipt path: {relative}")
            continue
        if not path.is_file():
            errors.append(f"missing retained file: {relative}")
            continue
        if sha256(path.read_bytes()) != receipt.get("sha256"):
            errors.append(f"sha256 mismatch: {relative}")
        if path.stat().st_size != receipt.get("bytes"):
            errors.append(f"byte-count mismatch: {relative}")

    try:
        canonical = canonical_rule(root=selected_root)
        default_rule_path = out / "private" / "rules" / "survivor-role-green3.rkt"
        if default_rule_path.read_text(encoding="utf-8") != canonical:
            errors.append("default rule is not byte-for-byte canonical")
        for role in SURVIVOR_ROLES:
            path = out / "private" / "rules" / f"survivor-role-{role}.rkt"
            source = path.read_text(encoding="utf-8")
            if source != instantiate_rule(role, root=selected_root):
                errors.append(f"retained rule does not match setting {role}")
            try:
                restore_canonical(source, root=selected_root)
            except (TypeError, ValueError) as exc:
                errors.append(f"retained rule {role} cannot restore canonical: {exc}")
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"rule verification failed: {type(exc).__name__}: {exc}")

    canonical_checked = 0
    episode_labels_checked = 0
    public_files_checked = 0
    settings_seen: set[str] = set()
    with RacketBridge() as bridge:
        try:
            canonical_program = instantiate_rule(
                DEFAULT_SURVIVOR_ROLE, root=selected_root
            )
            for pair in canonical_pairs(
                TASK_ID, root=selected_root, labeled_only=True
            ):
                canonical_checked += 1
                actual = evaluate(bridge, canonical_program, pair["input"])
                if actual != pair["output"]:
                    errors.append(
                        f"canonical Racket mismatch at {pair['split']}[{pair['pair_index']}]"
                    )
        except Exception as exc:
            errors.append(f"canonical replay failed: {type(exc).__name__}: {exc}")

        for episode_row in report.get("episodes", []):
            try:
                private_path = (out / episode_row["private_path"]).resolve()
                public_path = (out / episode_row["public_path"]).resolve()
                if not private_path.is_relative_to(out) or not public_path.is_relative_to(out):
                    raise ValueError("episode path escapes evidence tree")
                private = json.loads(private_path.read_text(encoding="utf-8"))
                chosen = private["parameters"]["survivor_role"]
                _validate_setting(chosen)
                settings_seen.add(chosen)
                expected_program = instantiate_rule(chosen, root=selected_root)
                if private["racket_program"] != expected_program:
                    errors.append(f"private episode program mismatch: {private_path.name}")
                if private["racket_sha256"] != sha256(expected_program):
                    errors.append(f"private Racket hash mismatch: {private_path.name}")
                for pair_index, pair in enumerate(private["pairs"]):
                    episode_labels_checked += 1
                    actual = evaluate(bridge, expected_program, pair["input"])
                    if actual != pair["output"]:
                        errors.append(
                            f"private label mismatch: {private_path.name} pair {pair_index}"
                        )
                replayed_analysis = analyze_episode(bridge, private)
                if replayed_analysis != private.get("analysis"):
                    errors.append(f"rival analysis mismatch: {private_path.name}")
                if replayed_analysis.get("status") != "no_ambiguity_found":
                    errors.append(f"retained ambiguity: {private_path.name}")

                challenge = json.loads(public_path.read_text(encoding="utf-8"))
                expected_challenge = public_challenge(private)
                if challenge != expected_challenge:
                    errors.append(f"public projection mismatch: {public_path.name}")
                if public_path.read_bytes() != public_challenge_bytes(challenge):
                    errors.append(f"public bytes are not canonical: {public_path.name}")
                if public_path.name != public_filename(challenge):
                    errors.append(f"public opaque filename mismatch: {public_path.name}")
                if not _PUBLIC_NAME_RE.fullmatch(public_path.name):
                    errors.append(f"public filename is not opaque: {public_path.name}")
                serialized = json.dumps(challenge)
                if any(
                    forbidden in serialized
                    for forbidden in (
                        "survivor_role",
                        "racket",
                        "parameters",
                        "seed",
                        "query_output",
                    )
                ):
                    errors.append(f"private state leaked into {public_path.name}")
                if any(set(pair) != {"input"} for pair in challenge["test"]):
                    errors.append(f"query answer leaked into {public_path.name}")
                public_files_checked += 1
            except Exception as exc:
                errors.append(
                    f"episode replay failed: {type(exc).__name__}: {exc}"
                )

    if settings_seen != set(SURVIVOR_ROLES):
        errors.append(f"settings seen {sorted(settings_seen)} do not cover declared settings")
    if canonical_checked != 4:
        errors.append(f"expected 4 canonical labels, checked {canonical_checked}")
    expected_episode_labels = report.get("counts", {}).get("episode_labels")
    if expected_episode_labels != episode_labels_checked:
        errors.append(
            f"expected {expected_episode_labels} episode labels, checked {episode_labels_checked}"
        )
    if public_files_checked != 2:
        errors.append(f"expected 2 public challenges, checked {public_files_checked}")

    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "counts": {
            "canonical_labels_checked": canonical_checked,
            "episode_labels_checked": episode_labels_checked,
            "public_files_checked": public_files_checked,
            "settings_seen": [
                role for role in SURVIVOR_ROLES if role in settings_seen
            ],
        },
        "report": str(report_path),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    materialize_parser = subparsers.add_parser(
        "materialize", help="write a new two-setting evidence tree"
    )
    materialize_parser.add_argument("--seed", type=int, default=0)
    materialize_parser.add_argument("--demo-count", type=int, default=3)
    materialize_parser.add_argument("--query-count", type=int, default=4)
    materialize_parser.add_argument("--out", type=Path, required=True)

    verify_parser = subparsers.add_parser(
        "verify", help="replay and verify an existing evidence tree"
    )
    verify_parser.add_argument("--out", type=Path, required=True)

    args = parser.parse_args(argv)
    if args.command == "materialize":
        report = materialize(
            args.out,
            seed=args.seed,
            demo_count=args.demo_count,
            query_count=args.query_count,
        )
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

    result = verify_tree(args.out)
    print(json.dumps(result, indent=2, sort_keys=True))
    return int(result["status"] != "pass")


if __name__ == "__main__":
    raise SystemExit(main())
