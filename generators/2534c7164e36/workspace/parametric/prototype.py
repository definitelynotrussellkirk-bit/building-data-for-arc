"""Proposed episode-level panel-priority extension for 2534c7164e36.

The selected production generator and canonical Racket authority remain
unchanged. This task-local prototype chooses one of two exact Racket programs
once per episode, generates inputs independently of that hidden setting, labels
every demonstration and query in Racket, and checks all four queries against
the other declared setting using only the labeled demonstrations.
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


TASK_ID = "2534c7164e36"
CANONICAL_SHA256 = (
    "3d9402d2c7a5a95e4e76a0cac9b607451694f4f32a7a501664be99032ab453e1"
)
PRIORITY_ORDERS = ("q1_q2_q3", "q1_q3_q2")
DEFAULT_PRIORITY_ORDER = "q1_q2_q3"
ORDER_DESCRIPTION = {
    "q1_q2_q3": "panel priority Q1 > Q2 > Q3 (canonical left-to-right)",
    "q1_q3_q2": "panel priority Q1 > Q3 > Q2 (proposed lower-priority swap)",
}
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)

_CANONICAL_PRIORITY_CLAUSES = (
    "(cond ((!= q1 0) q1) ((!= q2 0) q2) (else q3))"
)
_ALTERNATIVE_PRIORITY_CLAUSES = (
    "(cond ((!= q1 0) q1) ((!= q3 0) q3) (else q2))"
)
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


def _validate_setting(priority_order: str) -> None:
    if type(priority_order) is not str or priority_order not in PRIORITY_ORDERS:
        raise ValueError(f"priority_order must be one of {PRIORITY_ORDERS}")


def canonical_rule(*, root=None) -> str:
    """Return the selected canonical program, byte-for-byte and hash-pinned."""
    selected_root = ROOT if root is None else Path(root).resolve()
    programs: list[str] = []
    with canonical_path(selected_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    if not programs:
        raise ValueError("prototype requires at least one selected canonical row")
    if len(set(programs)) != 1:
        raise ValueError("selected canonical rows disagree on the Racket authority")
    source = programs[0]
    actual = sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket hash changed: expected {CANONICAL_SHA256}, got {actual}"
        )
    if source.count(_CANONICAL_PRIORITY_CLAUSES) != 1:
        raise ValueError("canonical priority clauses changed; reassess the prototype")
    return source


def instantiate_rule(
    priority_order: str = DEFAULT_PRIORITY_ORDER, *, root=None
) -> str:
    """Materialize the exact canonical or proposed alternative Racket program."""
    _validate_setting(priority_order)
    source = canonical_rule(root=root)
    if priority_order == DEFAULT_PRIORITY_ORDER:
        return source
    alternative = source.replace(
        _CANONICAL_PRIORITY_CLAUSES, _ALTERNATIVE_PRIORITY_CLAUSES, 1
    )
    if alternative == source:
        raise ValueError("alternative panel ordering did not change the program")
    return alternative


def restore_canonical(program: str, *, root=None) -> str:
    """Prove a generated program differs only at the declared parameter site."""
    if type(program) is not str:
        raise TypeError("program must be Racket source text")
    canonical = canonical_rule(root=root)
    if program == canonical:
        return canonical
    if program.count(_ALTERNATIVE_PRIORITY_CLAUSES) != 1:
        raise ValueError("program is not a declared priority-order variant")
    restored = program.replace(
        _ALTERNATIVE_PRIORITY_CLAUSES, _CANONICAL_PRIORITY_CLAUSES, 1
    )
    if restored != canonical or sha256(restored) != CANONICAL_SHA256:
        raise ValueError("program is not a declared priority-order variant")
    return restored


def evaluate(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Execute one exact rule through the packet's Racket authority."""
    normalized = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)") and not function.startswith("(build-grid"):
        raise ValueError("expected the selected task's native Racket rule body")
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    # strip_rule_wrapper may expose the build-grid expression whose free `g`
    # needs binding, or a lambda in other task-local variants.
    expression = (
        f"({function} '{datum})"
        if function.startswith("(lambda (g)")
        else f"((lambda (g) {function}) '{datum})"
    )
    return normalize_grid(bridge.eval_text(expression))


def choose_priority_order(seed: int) -> str:
    """Choose one hidden rule setting for the whole episode."""
    _validate_seed(seed)
    return PRIORITY_ORDERS[seed % len(PRIORITY_ORDERS)]


def generate_inputs(
    seed: int, *, demo_count: int = 2, query_count: int = 4
) -> list[list[list[int]]]:
    """Generate distinct lawful inputs independently of the hidden setting."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    total = demo_count + query_count
    bands = ("easy", "medium", "hard", "medium")
    generation_seed = 253_400_001 + seed * 10_007
    result: list[list[list[int]]] = []
    seen: set[bytes] = set()
    candidate_index = 0
    max_attempts = max(64, total * 16)
    while len(result) < total and candidate_index < max_attempts:
        grid = GEN.generate(
            generation_seed,
            candidate_index,
            difficulty=bands[candidate_index % len(bands)],
            scene_family="generalized",
        )
        errors = GEN.self_check(grid)
        if errors:
            raise RuntimeError(
                "selected generator returned an unlawful input: " + "; ".join(errors)
            )
        if GEN.canonical_profile_signature(grid) != "generalized":
            raise RuntimeError("prototype requires a generalized overlap witness")
        facts = GEN._analyze(grid)["facts"]
        if (False, True, True) not in facts["states"]:
            raise RuntimeError("generated input does not distinguish Q2 from Q3 priority")
        normalized = normalize_grid(grid)
        key = json.dumps(normalized, separators=(",", ":")).encode("utf-8")
        if key not in seen:
            seen.add(key)
            result.append(normalized)
        candidate_index += 1
    if len(result) != total:
        raise RuntimeError(
            f"could not obtain {total} distinct lawful inputs in {max_attempts} attempts"
        )
    return result


def make_episode(
    bridge: RacketBridge,
    seed: int,
    *,
    priority_order: str | None = None,
    demo_count: int = 2,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one private episode; all labels come from matching exact Racket."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    chosen = choose_priority_order(seed) if priority_order is None else priority_order
    _validate_setting(chosen)
    program = instantiate_rule(chosen)
    inputs = generate_inputs(seed, demo_count=demo_count, query_count=query_count)
    return {
        "schema": "2534c7164e36-priority-order-episode-v1",
        "seed": seed,
        "parameters": {"priority_order": chosen},
        "parameter_choice": (
            "seed_modulo_two" if priority_order is None else "explicit_once_per_episode"
        ),
        "priority_description": ORDER_DESCRIPTION[chosen],
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
    """Project private evidence to visible demonstrations and unlabeled queries."""
    demo_count = episode.get("demo_count")
    query_count = episode.get("query_count")
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    pairs = episode.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != demo_count + query_count:
        raise ValueError("episode pair count does not match demo_count + query_count")
    return deepcopy(
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


def _normalize_public_challenge(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("public challenge source must be a mapping")
    challenge = public_challenge(value) if "pairs" in value else deepcopy(value)
    # The shared helper validates exact visible shape and emits a normalized view.
    return json.loads(public_challenge_bytes(challenge).decode("utf-8"))


def public_filename(value: dict[str, Any]) -> str:
    """Derive an opaque filename from the exact visible bytes only."""
    challenge = _normalize_public_challenge(value)
    return f"challenge-{public_challenge_id(challenge)}.json"


def analyze_episode(bridge: RacketBridge, episode: dict[str, Any]) -> dict[str, Any]:
    """Check each query against all declared rivals using demonstrations only."""
    chosen = episode["parameters"]["priority_order"]
    _validate_setting(chosen)
    demo_count = episode["demo_count"]
    query_count = episode["query_count"]
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    pairs = episode["pairs"]
    if len(pairs) != demo_count + query_count:
        raise ValueError("episode pair count does not match declared counts")

    alternatives: dict[str, list[list[list[int]]]] = {}
    for setting in PRIORITY_ORDERS:
        if setting == chosen:
            continue
        program = instantiate_rule(setting)
        alternatives[setting] = [
            evaluate(bridge, program, pair["input"]) for pair in pairs
        ]

    demonstration_indices = list(range(demo_count))
    query_rows = []
    for query_index in range(demo_count, len(pairs)):
        rivals = []
        for setting, outputs in alternatives.items():
            refutations = [
                index
                for index in demonstration_indices
                if outputs[index] != pairs[index]["output"]
            ]
            rivals.append(
                {
                    "name": f"priority_order={setting}",
                    "parameters": {"priority_order": setting},
                    "refuting_demonstration_indices": refutations,
                    "fits_demonstrations": not refutations,
                    "query_differs": outputs[query_index]
                    != pairs[query_index]["output"],
                    "query_output": outputs[query_index],
                }
            )
        ambiguous = any(
            rival["fits_demonstrations"] and rival["query_differs"]
            for rival in rivals
        )
        query_rows.append(
            {
                "query_index": query_index - demo_count,
                "pair_index": query_index,
                "demonstration_indices": demonstration_indices,
                "rivals": rivals,
                "status": "ambiguous" if ambiguous else "no_ambiguity_found",
            }
        )

    ambiguities = sum(row["status"] == "ambiguous" for row in query_rows)
    return {
        "status": "no_ambiguity_found" if ambiguities == 0 else "ambiguous",
        "chosen_parameters": deepcopy(episode["parameters"]),
        "demonstration_indices": demonstration_indices,
        "queries": query_rows,
        "counterfactual_outputs": alternatives,
        "counts": {
            "demonstrations": demo_count,
            "queries": query_count,
            "declared_rivals": len(alternatives),
            "query_ambiguities": ambiguities,
        },
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_public(path: Path, challenge: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(public_challenge_bytes(_normalize_public_challenge(challenge)))


def _prepare_public_batch(
    episodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Plan a stable public batch and reject duplicate visible payloads."""
    prepared: list[dict[str, Any]] = []
    payload_by_id: dict[str, bytes] = {}
    for episode_index, episode in enumerate(episodes):
        challenge = _normalize_public_challenge(episode)
        payload = public_challenge_bytes(challenge)
        identifier = public_challenge_id(challenge)
        previous = payload_by_id.get(identifier)
        if previous is not None:
            if previous == payload:
                raise ValueError(
                    f"duplicate public challenge payload: {identifier}"
                )
            raise ValueError(f"public challenge ID collision: {identifier}")
        payload_by_id[identifier] = payload
        prepared.append(
            {
                "episode_index": episode_index,
                "public_id": identifier,
                "public_name": f"challenge-{identifier}.json",
                "payload": payload,
            }
        )
    return sorted(prepared, key=lambda row: row["public_id"])


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
    demo_count: int = 2,
    query_count: int = 4,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write bounded, replayable evidence covering both declared settings."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError(out)
    output_created = False
    report: dict[str, Any] = {
        "schema": "2534c7164e36-priority-order-evidence-v1",
        "status": "incomplete",
        "scope": (
            "proposed task-local prototype; not a canonical rule change, "
            "production API, approval, or training admission"
        ),
        "parameter_spec": {
            "priority_order": {
                "allowed": list(PRIORITY_ORDERS),
                "original_default": DEFAULT_PRIORITY_ORDER,
                "effective_priority": ORDER_DESCRIPTION,
            }
        },
        "choice_policy": (
            "One setting per complete episode: canonical for even seeds and the "
            "Q2/Q3 swap for odd seeds. Input generation is setting-independent."
        ),
        "input_constraints": (
            "Inputs remain lawful 4x14 three-panel generalized scenes from the "
            "selected generator. Every scene includes all eight occupancy states, "
            "including Q2/Q3 overlap with Q1 absent, so the settings differ without "
            "changing the input manifold."
        ),
        "lesson_policy": (
            f"{demo_count} labeled demonstrations followed by {query_count} distinct "
            "queries; every query is checked against the other declared setting using "
            "only those demonstrations."
        ),
        "limitations": (
            "Evidence covers two consecutive seeds and one declared rival per episode. "
            "It does not prove uniqueness against undeclared rules or authorize shared "
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
    episode_records: list[dict[str, Any]] = []
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

            canonical_program = instantiate_rule(DEFAULT_PRIORITY_ORDER)
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

            for episode_index in range(2):
                episode = make_episode(
                    active,
                    seed + episode_index,
                    demo_count=demo_count,
                    query_count=query_count,
                )
                analysis = analyze_episode(active, episode)
                episode_records.append(
                    {
                        "episode_index": episode_index,
                        "episode": episode,
                        "analysis": analysis,
                        "private_path": Path("private")
                        / f"episode-{episode_index + 1:03d}.json",
                    }
                )

            public_batch = _prepare_public_batch(
                [row["episode"] for row in episode_records]
            )
            public_by_episode = {
                row["episode_index"]: row for row in public_batch
            }
            report["public_write_order"] = [
                str(Path("public") / row["public_name"]) for row in public_batch
            ]
            for row in episode_records:
                episode_index = row["episode_index"]
                episode = row["episode"]
                analysis = row["analysis"]
                public_row = public_by_episode[episode_index]
                public_path = Path("public") / public_row["public_name"]
                report["episodes"].append(
                    {
                        "episode_index": episode_index,
                        "seed": episode["seed"],
                        "parameters": episode["parameters"],
                        "priority_description": episode["priority_description"],
                        "racket_sha256": episode["racket_sha256"],
                        "demo_count": demo_count,
                        "query_count": query_count,
                        "public_path": str(public_path),
                        "private_path": str(row["private_path"]),
                        "analysis": analysis,
                    }
                )

            witness_input = generate_inputs(
                seed, demo_count=demo_count, query_count=query_count
            )[0]
            report["setting_witness"] = {
                "input": witness_input,
                "outputs": {
                    setting: evaluate(active, instantiate_rule(setting), witness_input)
                    for setting in PRIORITY_ORDERS
                },
                "racket_hashes": {
                    setting: sha256(instantiate_rule(setting))
                    for setting in PRIORITY_ORDERS
                },
            }

            canonical_passed = sum(
                row["passed"] for row in report["canonical_checks"]
            )
            query_ambiguities = sum(
                query["status"] == "ambiguous"
                for episode in report["episodes"]
                for query in episode["analysis"]["queries"]
            )
            settings_seen_set = {
                episode["parameters"]["priority_order"]
                for episode in report["episodes"]
            }
            settings_seen = [
                setting for setting in PRIORITY_ORDERS if setting in settings_seen_set
            ]
            witness_outputs = list(report["setting_witness"]["outputs"].values())
            all_queries_differ = all(
                rival["query_differs"]
                for episode in report["episodes"]
                for query in episode["analysis"]["queries"]
                for rival in query["rivals"]
            )
            all_rivals_refuted = all(
                rival["refuting_demonstration_indices"]
                for episode in report["episodes"]
                for query in episode["analysis"]["queries"]
                for rival in query["rivals"]
            )
            report["counts"] = {
                "canonical_labels_checked": len(report["canonical_checks"]),
                "canonical_labels_passed": canonical_passed,
                "episodes": len(report["episodes"]),
                "demonstrations": len(report["episodes"]) * demo_count,
                "queries": len(report["episodes"]) * query_count,
                "episode_labels": len(report["episodes"])
                * (demo_count + query_count),
                "counterfactual_labels": len(report["episodes"])
                * (demo_count + query_count),
                "query_ambiguities": query_ambiguities,
                "settings_seen": settings_seen,
            }
            report["status"] = (
                "no_ambiguity_found"
                if canonical_passed == len(report["canonical_checks"])
                and settings_seen_set == set(PRIORITY_ORDERS)
                and len(witness_outputs) == 2
                and witness_outputs[0] != witness_outputs[1]
                and query_ambiguities == 0
                and all_queries_differ
                and all_rivals_refuted
                else "failed"
            )

            out.mkdir(parents=True, exist_ok=False)
            output_created = True
            for setting in PRIORITY_ORDERS:
                rule_path = out / "private" / "rules" / f"priority-order-{setting}.rkt"
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(instantiate_rule(setting), encoding="utf-8")
            for public_row in public_batch:
                public_path = out / "public" / public_row["public_name"]
                public_path.parent.mkdir(parents=True, exist_ok=True)
                public_path.write_bytes(public_row["payload"])
            for row in episode_records:
                write_json(
                    out / row["private_path"],
                    {**row["episode"], "analysis": row["analysis"]},
                )
            report["files"] = _relative_file_receipts(out)
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        if output_created:
            write_json(out / "report.json", report)
        raise
    write_json(out / "report.json", report)
    return report


def verify_tree(out: Path | str, *, root=None) -> dict[str, Any]:
    """Replay an evidence tree, including labels, rivals, and public bytes."""
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
        default_rule_path = (
            out
            / "private"
            / "rules"
            / f"priority-order-{DEFAULT_PRIORITY_ORDER}.rkt"
        )
        if default_rule_path.read_text(encoding="utf-8") != canonical:
            errors.append("default rule is not byte-for-byte canonical")
        for setting in PRIORITY_ORDERS:
            path = out / "private" / "rules" / f"priority-order-{setting}.rkt"
            source = path.read_text(encoding="utf-8")
            expected = instantiate_rule(setting, root=selected_root)
            if source != expected:
                errors.append(f"retained rule does not match setting {setting}")
            try:
                restore_canonical(source, root=selected_root)
            except (TypeError, ValueError) as exc:
                errors.append(f"retained rule {setting} cannot restore canonical: {exc}")
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"rule verification failed: {type(exc).__name__}: {exc}")

    canonical_checked = 0
    episode_labels_checked = 0
    public_files_checked = 0
    settings_seen: set[str] = set()
    expected_public_paths: set[Path] = set()
    with RacketBridge() as bridge:
        try:
            canonical_program = instantiate_rule(
                DEFAULT_PRIORITY_ORDER, root=selected_root
            )
            selected_pairs = canonical_pairs(
                TASK_ID, root=selected_root, labeled_only=True
            )
            for pair in selected_pairs:
                canonical_checked += 1
                actual = evaluate(bridge, canonical_program, pair["input"])
                if actual != pair["output"]:
                    errors.append(
                        "canonical Racket mismatch at "
                        f"variant {pair['variant']} {pair['split']}[{pair['pair_index']}]"
                    )
        except Exception as exc:
            errors.append(f"canonical replay failed: {type(exc).__name__}: {exc}")

        for episode_row in report.get("episodes", []):
            try:
                private_path = (out / episode_row["private_path"]).resolve()
                public_path = (out / episode_row["public_path"]).resolve()
                expected_public_paths.add(public_path)
                if not private_path.is_relative_to(out) or not public_path.is_relative_to(out):
                    raise ValueError("episode path escapes evidence tree")
                private = json.loads(private_path.read_text(encoding="utf-8"))
                chosen = private["parameters"]["priority_order"]
                _validate_setting(chosen)
                settings_seen.add(chosen)
                expected_program = instantiate_rule(chosen, root=selected_root)
                if private["racket_program"] != expected_program:
                    errors.append(f"private episode program mismatch: {private_path.name}")
                if private["racket_sha256"] != sha256(expected_program):
                    errors.append(
                        f"private episode Racket hash mismatch: {private_path.name}"
                    )
                expected_inputs = generate_inputs(
                    private["seed"],
                    demo_count=private["demo_count"],
                    query_count=private["query_count"],
                )
                retained_inputs = [pair["input"] for pair in private["pairs"]]
                if retained_inputs != expected_inputs:
                    errors.append(f"episode input schedule mismatch: {private_path.name}")
                for pair_index, pair in enumerate(private["pairs"]):
                    episode_labels_checked += 1
                    actual = evaluate(bridge, expected_program, pair["input"])
                    if actual != pair["output"]:
                        errors.append(
                            f"private label mismatch: {private_path.name} pair {pair_index}"
                        )
                replayed_analysis = analyze_episode(bridge, private)
                retained_analysis = private.get("analysis")
                if replayed_analysis != retained_analysis:
                    errors.append(f"rival analysis mismatch: {private_path.name}")
                challenge = json.loads(public_path.read_text(encoding="utf-8"))
                expected_challenge = public_challenge(private)
                if challenge != expected_challenge:
                    errors.append(f"public projection mismatch: {public_path.name}")
                expected_bytes = public_challenge_bytes(expected_challenge)
                if public_path.read_bytes() != expected_bytes:
                    errors.append(f"public bytes are not canonical: {public_path.name}")
                if public_path.name != public_filename(challenge):
                    errors.append(f"public opaque filename mismatch: {public_path.name}")
                if not _PUBLIC_NAME_RE.fullmatch(public_path.name):
                    errors.append(f"public filename is not opaque: {public_path.name}")
                if sha256(public_path.read_bytes()) != public_path.stem.removeprefix(
                    "challenge-"
                ):
                    errors.append(f"public filename does not hash exact bytes: {public_path.name}")
                serialized = json.dumps(challenge)
                if any(
                    forbidden in serialized
                    for forbidden in (
                        "priority_order",
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
                errors.append(f"episode replay failed: {type(exc).__name__}: {exc}")

    actual_public_paths = {path.resolve() for path in (out / "public").glob("*.json")}
    if actual_public_paths != expected_public_paths:
        errors.append("public directory does not exactly match reported episode files")
    if settings_seen != set(PRIORITY_ORDERS):
        errors.append(
            f"settings seen {sorted(settings_seen)} do not cover declared settings"
        )
    expected_canonical = report.get("counts", {}).get("canonical_labels_checked")
    if expected_canonical != canonical_checked:
        errors.append(
            f"expected {expected_canonical} canonical labels, checked {canonical_checked}"
        )
    expected_episode_labels = report.get("counts", {}).get("episode_labels")
    if expected_episode_labels != episode_labels_checked:
        errors.append(
            f"expected {expected_episode_labels} episode labels, "
            f"checked {episode_labels_checked}"
        )
    if public_files_checked != len(report.get("episodes", [])):
        errors.append(
            f"expected {len(report.get('episodes', []))} public challenges, "
            f"checked {public_files_checked}"
        )

    return {
        "status": "pass" if not errors else "fail",
        "errors": errors,
        "counts": {
            "canonical_labels_checked": canonical_checked,
            "episode_labels_checked": episode_labels_checked,
            "public_files_checked": public_files_checked,
            "settings_seen": [
                setting for setting in PRIORITY_ORDERS if setting in settings_seen
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
    materialize_parser.add_argument("--demo-count", type=int, default=2)
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
