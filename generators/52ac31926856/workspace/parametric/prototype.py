"""Proposed episode-level floor-acceptance extension for 52ac31926856.

The selected production generator and canonical Racket authority remain
unchanged.  This task-local prototype chooses one of two exact Racket programs
once per episode, labels every demonstration and query in Racket, and checks
all four queries against the other declared setting using only the labeled
demonstrations.
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


TASK_ID = "52ac31926856"
CANONICAL_SHA256 = "155890c61ab00ef4a460914d2de683ae25a4b20761bb7adfae92fb324688857d"
FLOOR_ACCEPTANCE_VALUES = ("whole_section", "under_drop")
DEFAULT_FLOOR_ACCEPTANCE = "whole_section"
FLOOR_ACCEPTANCE_DESCRIPTION = {
    "whole_section": "accept the first candidate section only when every floor cell is red",
    "under_drop": "accept the first candidate section when the floor cell under the drop is red",
}
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
_PUBLIC_NAME_RE = re.compile(r"challenge-[0-9a-f]{64}\.json\Z")
_COUNT_LIMIT = 12
_ALTERNATIVE_FLOOR_CLAUSE = "(floor-solid (= (at g frame-r1 bc) 2))"


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


def _validate_setting(floor_acceptance: str) -> None:
    if type(floor_acceptance) is not str:
        raise TypeError("floor_acceptance must be a string")
    if floor_acceptance not in FLOOR_ACCEPTANCE_VALUES:
        raise ValueError(
            f"floor_acceptance must be one of {FLOOR_ACCEPTANCE_VALUES}"
        )


def canonical_rule(*, root: Path | str | None = None) -> str:
    """Return the unique canonical program, byte-for-byte and hash-pinned."""
    selected_root = ROOT if root is None else Path(root).resolve()
    matches: list[str] = []
    with canonical_path(selected_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if isinstance(source, str):
                    matches.append(source)
    if len(matches) != 1:
        raise ValueError(
            f"prototype requires exactly one canonical rule for {TASK_ID}, got {len(matches)}"
        )
    source = matches[0]
    actual = sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket hash changed: expected {CANONICAL_SHA256}, got {actual}"
        )
    _canonical_floor_clause(source)
    return source


def _balanced_form(source: str, start: int) -> str:
    """Return the balanced parenthesized form beginning at ``start``."""
    if start < 0 or start >= len(source) or source[start] != "(":
        raise ValueError("balanced form must start at an opening parenthesis")
    depth = 0
    for index in range(start, len(source)):
        char = source[index]
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
            if depth < 0:
                break
    raise ValueError("unbalanced Racket form")


def _canonical_floor_clause(source: str) -> str:
    marker = "(floor-solid (for/and"
    if source.count(marker) != 1:
        raise ValueError("canonical source does not contain one whole-floor predicate")
    clause = _balanced_form(source, source.index(marker))
    if "frame-r1" not in clause or "sec-c0" not in clause or "sec-c1" not in clause:
        raise ValueError("canonical floor predicate has an unexpected structure")
    if clause.count("(at g") != 1 or clause.count(" 2") < 1:
        raise ValueError("canonical floor predicate has an unexpected comparison")
    return clause


def instantiate_rule(
    floor_acceptance: str = DEFAULT_FLOOR_ACCEPTANCE,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize the exact canonical or proposed alternative Racket program."""
    _validate_setting(floor_acceptance)
    source = canonical_rule(root=root)
    if floor_acceptance == DEFAULT_FLOOR_ACCEPTANCE:
        return source
    canonical_clause = _canonical_floor_clause(source)
    alternative = source.replace(canonical_clause, _ALTERNATIVE_FLOOR_CLAUSE, 1)
    if alternative == source or alternative.count(_ALTERNATIVE_FLOOR_CLAUSE) != 1:
        raise ValueError("alternative floor-acceptance rule did not materialize exactly once")
    return alternative


def restore_canonical(program: str, *, root: Path | str | None = None) -> str:
    """Prove that a generated program differs only at the declared predicate."""
    if type(program) is not str:
        raise TypeError("program must be Racket source text")
    canonical = canonical_rule(root=root)
    if program == canonical:
        return canonical
    if program.count(_ALTERNATIVE_FLOOR_CLAUSE) != 1:
        raise ValueError("program is not a declared floor-acceptance variant")
    restored = program.replace(
        _ALTERNATIVE_FLOOR_CLAUSE,
        _canonical_floor_clause(canonical),
        1,
    )
    if restored != canonical or sha256(restored) != CANONICAL_SHA256:
        raise ValueError("program changes more than the declared floor predicate")
    return restored


def evaluate(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Execute one exact rule through the packet's Racket authority."""
    restore_canonical(program)
    normalized = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("expected the selected task's native Racket lambda")
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def choose_floor_acceptance(seed: int) -> str:
    """Choose one hidden rule setting for the whole episode."""
    _validate_seed(seed)
    return FLOOR_ACCEPTANCE_VALUES[seed % len(FLOOR_ACCEPTANCE_VALUES)]


def generate_inputs(
    seed: int,
    *,
    demo_count: int = 3,
    query_count: int = 4,
) -> list[list[list[int]]]:
    """Generate distinct lawful off-column-gap witnesses independent of setting."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    total = demo_count + query_count
    dimension_cycle = ((10, 10), (12, 12), (14, 15), (16, 18), (18, 20))
    generation_seed = 520_319 + seed * 10_007
    result: list[list[list[int]]] = []
    seen: set[str] = set()
    candidate_index = 0
    max_attempts = max(80, total * 20)
    while len(result) < total and candidate_index < max_attempts:
        height, width = dimension_cycle[candidate_index % len(dimension_cycle)]
        landing = ("second", "bottom")[candidate_index % 2]
        target_width = 2 + candidate_index % 4
        overrides = {
            "grid_h": height,
            "grid_w": width,
            "landing": landing,
            "target_width": target_width,
        }
        grid = GEN.generate(
            generation_seed,
            candidate_index,
            difficulty="medium",
            **overrides,
        )
        errors = GEN.self_check(grid, meta={"overrides": overrides})
        if errors:
            raise RuntimeError(
                "selected generator returned an unlawful input: " + "; ".join(errors)
            )
        analysis = GEN._analyze(grid)
        witness = any(
            item["candidate"]
            and not item["floor_solid"]
            and item["blue_floor_solid"]
            and item["off_column_gap"]
            for item in analysis["containers"]
        )
        if not witness:
            candidate_index += 1
            continue
        key = json.dumps(grid, separators=(",", ":"))
        if key not in seen:
            seen.add(key)
            result.append(grid)
        candidate_index += 1
    if len(result) != total:
        raise RuntimeError(
            f"could not obtain {total} distinct lawful witnesses in {max_attempts} attempts"
        )
    return result


def make_episode(
    bridge: RacketBridge,
    seed: int,
    *,
    floor_acceptance: str | None = None,
    demo_count: int = 3,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one complete private episode; every label comes from Racket."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    chosen = (
        choose_floor_acceptance(seed)
        if floor_acceptance is None
        else floor_acceptance
    )
    _validate_setting(chosen)
    program = instantiate_rule(chosen)
    inputs = generate_inputs(seed, demo_count=demo_count, query_count=query_count)
    return {
        "schema": "52ac31926856-floor-acceptance-episode-v1",
        "task_id": TASK_ID,
        "prototype_status": "proposed_unapproved",
        "seed": seed,
        "parameters": {"floor_acceptance": chosen},
        "parameter_choice": (
            "seed_modulo_two"
            if floor_acceptance is None
            else "explicit_once_per_episode"
        ),
        "acceptance_description": FLOOR_ACCEPTANCE_DESCRIPTION[chosen],
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
    if not isinstance(episode, dict):
        raise TypeError("episode must be a mapping")
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


def _normalize_public(value: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("public challenge source must be a mapping")
    challenge = public_challenge(value) if "pairs" in value else deepcopy(value)
    # The shared helper validates exact keys, grids, and public-only projection.
    return json.loads(public_challenge_bytes(challenge))


def public_bytes(value: dict[str, Any]) -> bytes:
    """Return canonical visible bytes, independent of all private fields."""
    return public_challenge_bytes(_normalize_public(value))


def public_filename(value: dict[str, Any]) -> str:
    """Derive an opaque name solely from visible public challenge bytes."""
    challenge = _normalize_public(value)
    return f"challenge-{public_challenge_id(challenge)}.json"


def analyze_episode(bridge: RacketBridge, episode: dict[str, Any]) -> dict[str, Any]:
    """Check each query against the other setting using demonstrations only."""
    chosen = episode["parameters"]["floor_acceptance"]
    _validate_setting(chosen)
    demo_count = episode["demo_count"]
    query_count = episode["query_count"]
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    pairs = episode["pairs"]
    if len(pairs) != demo_count + query_count:
        raise ValueError("episode pair count does not match declared counts")

    chosen_program = instantiate_rule(chosen)
    for index, pair in enumerate(pairs):
        if evaluate(bridge, chosen_program, pair["input"]) != pair["output"]:
            raise ValueError(f"pair {index} is not labeled by its declared setting")

    alternatives: dict[str, list[list[list[int]]]] = {}
    for setting in FLOOR_ACCEPTANCE_VALUES:
        if setting == chosen:
            continue
        program = instantiate_rule(setting)
        alternatives[setting] = [
            evaluate(bridge, program, pair["input"]) for pair in pairs
        ]

    demonstration_indices = list(range(demo_count))
    query_rows = []
    for pair_index in range(demo_count, len(pairs)):
        rivals = []
        for setting, outputs in alternatives.items():
            refutations = [
                index
                for index in demonstration_indices
                if outputs[index] != pairs[index]["output"]
            ]
            rivals.append(
                {
                    "name": f"floor_acceptance={setting}",
                    "parameters": {"floor_acceptance": setting},
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
    """Write bounded, replayable evidence for both declared settings."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    report: dict[str, Any] = {
        "schema": "52ac31926856-floor-acceptance-evidence-v1",
        "status": "incomplete",
        "scope": (
            "proposed task-local prototype; not a canonical rule change, "
            "production API, approval, or training admission"
        ),
        "parameter_spec": {
            "floor_acceptance": {
                "allowed": list(FLOOR_ACCEPTANCE_VALUES),
                "original_default": DEFAULT_FLOOR_ACCEPTANCE,
                "meaning": FLOOR_ACCEPTANCE_DESCRIPTION,
            }
        },
        "choice_policy": (
            "One setting per complete episode: whole_section for even seeds and "
            "under_drop for odd seeds. Input generation is setting-independent."
        ),
        "input_constraints": (
            "Inputs are lawful selected-generator scenes with landing second or bottom, "
            "target width at least two, and a decisive off-column floor gap while the "
            "floor cell under the blue drop remains red."
        ),
        "lesson_policy": (
            f"{demo_count} labeled demonstrations followed by {query_count} distinct "
            "queries; each query is checked against the other setting using only "
            "the demonstrations."
        ),
        "limitations": (
            "Evidence covers two consecutive seeds and the one declared rival per "
            "episode. It does not prove uniqueness against undeclared rules or "
            "authorize production/catalog integration."
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

            for setting in FLOOR_ACCEPTANCE_VALUES:
                rule_path = out / "private" / "rules" / f"floor-acceptance-{setting}.rkt"
                rule_path.parent.mkdir(parents=True, exist_ok=True)
                rule_path.write_text(instantiate_rule(setting), encoding="utf-8")

            canonical_program = instantiate_rule(DEFAULT_FLOOR_ACCEPTANCE)
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

            batch = []
            for source_episode_index in range(2):
                episode = make_episode(
                    active,
                    seed + source_episode_index,
                    demo_count=demo_count,
                    query_count=query_count,
                )
                analysis = analyze_episode(active, episode)
                challenge = public_challenge(episode)
                batch.append(
                    {
                        "source_episode_index": source_episode_index,
                        "episode": episode,
                        "analysis": analysis,
                        "challenge": challenge,
                        "public_name": public_filename(challenge),
                    }
                )

            public_names = [item["public_name"] for item in batch]
            duplicates = sorted(
                name for name in set(public_names) if public_names.count(name) > 1
            )
            if duplicates:
                raise ValueError(
                    "duplicate visible public challenge: " + ", ".join(duplicates)
                )

            for episode_index, item in enumerate(
                sorted(batch, key=lambda row: row["public_name"])
            ):
                episode = item["episode"]
                analysis = item["analysis"]
                challenge = item["challenge"]
                public_path = Path("public") / item["public_name"]
                private_path = Path("private") / f"episode-{episode_index + 1:03d}.json"
                (out / public_path).parent.mkdir(parents=True, exist_ok=True)
                (out / public_path).write_bytes(public_challenge_bytes(challenge))
                write_json(out / private_path, {**episode, "analysis": analysis})
                report["episodes"].append(
                    {
                        "episode_index": episode_index,
                        "source_episode_index": item["source_episode_index"],
                        "seed": episode["seed"],
                        "parameters": episode["parameters"],
                        "acceptance_description": episode["acceptance_description"],
                        "racket_sha256": episode["racket_sha256"],
                        "demo_count": demo_count,
                        "query_count": query_count,
                        "public_path": str(public_path),
                        "private_path": str(private_path),
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
                    for setting in FLOOR_ACCEPTANCE_VALUES
                },
                "racket_hashes": {
                    setting: sha256(instantiate_rule(setting))
                    for setting in FLOOR_ACCEPTANCE_VALUES
                },
            }

            canonical_passed = sum(row["passed"] for row in report["canonical_checks"])
            query_ambiguities = sum(
                row["status"] == "ambiguous"
                for episode in report["episodes"]
                for row in episode["analysis"]["queries"]
            )
            settings_seen_set = {
                episode["parameters"]["floor_acceptance"]
                for episode in report["episodes"]
            }
            settings_seen = [
                setting
                for setting in FLOOR_ACCEPTANCE_VALUES
                if setting in settings_seen_set
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
                "episode_labels": len(report["episodes"]) * (demo_count + query_count),
                "counterfactual_labels": len(report["episodes"]) * (demo_count + query_count),
                "query_ambiguities": query_ambiguities,
                "settings_seen": settings_seen,
            }
            report["status"] = (
                "no_ambiguity_found"
                if canonical_passed == len(report["canonical_checks"])
                and settings_seen_set == set(FLOOR_ACCEPTANCE_VALUES)
                and len(witness_outputs) == 2
                and witness_outputs[0] != witness_outputs[1]
                and query_ambiguities == 0
                and all_queries_differ
                and all_rivals_refuted
                else "failed"
            )
            report["files"] = _relative_file_receipts(out)
    except Exception as exc:
        report["status"] = "error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        write_json(out / "report.json", report)
        raise
    write_json(out / "report.json", report)
    return report


def verify_tree(out: Path | str, *, root: Path | str | None = None) -> dict[str, Any]:
    """Replay source bindings, Racket labels, rival analysis, and public views."""
    out = Path(out).resolve()
    selected_root = ROOT if root is None else Path(root).resolve()
    report_path = out / "report.json"
    if not report_path.is_file():
        raise FileNotFoundError(report_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if report.get("status") != "no_ambiguity_found":
        errors.append(f"materialized report status is {report.get('status')!r}")

    expected_source_hashes = {
        "prototype.py": sha256(Path(__file__).read_bytes()),
        "generator.py": GENERATOR_SHA256,
        "canonical_racket": sha256(canonical_rule(root=selected_root)),
    }
    if report.get("source_hashes") != expected_source_hashes:
        errors.append("source hashes do not match the current selected sources")

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
        default_path = (
            out
            / "private"
            / "rules"
            / f"floor-acceptance-{DEFAULT_FLOOR_ACCEPTANCE}.rkt"
        )
        if default_path.read_text(encoding="utf-8") != canonical:
            errors.append("default rule is not byte-for-byte canonical")
        for setting in FLOOR_ACCEPTANCE_VALUES:
            path = out / "private" / "rules" / f"floor-acceptance-{setting}.rkt"
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
    with RacketBridge() as bridge:
        canonical_rows = canonical_pairs(TASK_ID, root=selected_root, labeled_only=True)
        try:
            canonical_program = instantiate_rule(
                DEFAULT_FLOOR_ACCEPTANCE, root=selected_root
            )
            for pair in canonical_rows:
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
                chosen = private["parameters"]["floor_acceptance"]
                settings_seen.add(chosen)
                expected_program = instantiate_rule(chosen, root=selected_root)
                if private["racket_program"] != expected_program:
                    errors.append(f"private episode program mismatch: {private_path.name}")
                if private["racket_sha256"] != sha256(expected_program):
                    errors.append(f"private episode Racket hash mismatch: {private_path.name}")
                inputs_seen: set[str] = set()
                for pair_index, pair in enumerate(private["pairs"]):
                    episode_labels_checked += 1
                    key = json.dumps(pair["input"], separators=(",", ":"))
                    if key in inputs_seen:
                        errors.append(f"duplicate episode input: {private_path.name} pair {pair_index}")
                    inputs_seen.add(key)
                    actual = evaluate(bridge, expected_program, pair["input"])
                    if actual != pair["output"]:
                        errors.append(
                            f"private label mismatch: {private_path.name} pair {pair_index}"
                        )
                replayed_analysis = analyze_episode(bridge, private)
                if replayed_analysis != private.get("analysis"):
                    errors.append(f"rival analysis mismatch: {private_path.name}")
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
                if any(set(pair) != {"input"} for pair in challenge["test"]):
                    errors.append(f"query answer leaked into {public_path.name}")
                public_files_checked += 1
            except Exception as exc:
                errors.append(f"episode replay failed: {type(exc).__name__}: {exc}")

    if settings_seen != set(FLOOR_ACCEPTANCE_VALUES):
        errors.append(
            f"settings seen {sorted(settings_seen)} do not cover declared settings"
        )
    if canonical_checked != len(canonical_rows):
        errors.append(
            f"expected {len(canonical_rows)} canonical labels, checked {canonical_checked}"
        )
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
                setting
                for setting in FLOOR_ACCEPTANCE_VALUES
                if setting in settings_seen
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
