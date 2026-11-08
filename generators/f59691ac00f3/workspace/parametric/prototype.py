#!/usr/bin/env python3
"""Proposed episode-level parent-choice extension for ARC task f59691ac00f3.

The canonical cellular automaton writes the opposite color when both diagonal
parents agree and copies the right parent when they differ.  This prototype
keeps the gate and equal-parent branch fixed while making the different-parent
choice episode-fixed: copy the canonical right parent or the alternative left
parent.  It never changes the production generator or canonical rule authority.
"""
from __future__ import annotations

import argparse
import copy
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "f59691ac00f3"
PROTOTYPE_VERSION = "1.1.0"
SCHEMA = "arcpuzzles-parent-choice-prototype-v1"
DIFFERENT_PARENT_POLICIES = ("right", "left")
DEFAULT_DIFFERENT_PARENT = "right"
DEFAULT_DEMO_COUNT = 2
DEFAULT_QUERY_COUNT = 4
CANONICAL_SHA256 = "2e50ecc613be187d84268664bd1c2c33cf187efe48d02ecf8330366abd929a63"
CANONICAL_BRANCH = """(if (= lp rp)
                                               (set-cell g2 r c (opp lp))
                                               (set-cell g2 r c rp))"""
ALTERNATIVE_BRANCH = """(if (= lp rp)
                                               (set-cell g2 r c (opp lp))
                                               (set-cell g2 r c lp))"""


def _sha256(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _grid_sha256(grid: Any) -> str:
    return _sha256(_stable_json(normalize_grid(grid)))


def _validate_seed(seed: Any) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a nonnegative plain integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_count(value: Any, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a positive plain integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def _validate_policy(value: Any) -> str:
    if type(value) is not str:
        raise TypeError("different_parent must be a string")
    if value not in DIFFERENT_PARENT_POLICIES:
        raise ValueError(
            "different_parent must be one of "
            f"{DIFFERENT_PARENT_POLICIES}, got {value!r}"
        )
    return value


def choose_setting(seed: Any) -> str:
    """Choose one episode-fixed policy deterministically from a valid seed."""
    return DIFFERENT_PARENT_POLICIES[
        _validate_seed(seed) % len(DIFFERENT_PARENT_POLICIES)
    ]


def _check_canonical_source(source: Any) -> str:
    if not isinstance(source, str):
        raise ValueError("canonical Racket source must be text")
    actual = _sha256(source)
    if actual != CANONICAL_SHA256:
        raise ValueError(
            f"canonical Racket source hash mismatch: {actual} != {CANONICAL_SHA256}"
        )
    if source.count(CANONICAL_BRANCH) != 1:
        raise ValueError("canonical source does not contain the unique parent branch")
    if ALTERNATIVE_BRANCH in source:
        raise ValueError("canonical source unexpectedly contains the alternative branch")
    return source


def canonical_source(*, root: Path | str | None = None) -> str:
    """Load and pin the exact canonical Racket authority for this task."""
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    sources: set[str] = set()
    with canonical_path(resolved_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(
                row.get("program_solution"), str
            ):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(
            f"expected exactly one canonical source for {TASK_ID}, got {len(sources)}"
        )
    return _check_canonical_source(sources.pop())


def materialize_rule(
    different_parent: str = DEFAULT_DIFFERENT_PARENT,
    *,
    root: Path | str | None = None,
    source: str | None = None,
) -> str:
    """Instantiate one declared setting while preserving exact default bytes."""
    selected = _validate_policy(different_parent)
    canonical = (
        canonical_source(root=root)
        if source is None
        else _check_canonical_source(source)
    )
    if selected == DEFAULT_DIFFERENT_PARENT:
        return canonical
    alternative = canonical.replace(CANONICAL_BRANCH, ALTERNATIVE_BRANCH, 1)
    if alternative.count(ALTERNATIVE_BRANCH) != 1:
        raise AssertionError("failed to materialize left-parent policy")
    return alternative


def restore_canonical(source: Any) -> str:
    """Restore either declared materialization to the exact canonical source."""
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    if source.count(ALTERNATIVE_BRANCH) == 1 and CANONICAL_BRANCH not in source:
        restored = source.replace(ALTERNATIVE_BRANCH, CANONICAL_BRANCH, 1)
    elif source.count(CANONICAL_BRANCH) == 1 and ALTERNATIVE_BRANCH not in source:
        restored = source
    else:
        raise ValueError("Racket source must contain exactly one declared parent branch")
    return _check_canonical_source(restored)


def rule_callable(source: str) -> str:
    """Strip only the outer ``rule!`` wrapper from a declared rule source."""
    restore_canonical(source)
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    callable_source = source[len("(rule!") : -1].strip()
    if not callable_source.startswith("(lambda (g)"):
        raise ValueError("expected a wrapped grid lambda")
    return callable_source


def _racket_grid_literal(grid: Any) -> str:
    normalized = normalize_grid(grid)
    return "(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")"
        for row in normalized
    ) + ")"


def execute_rule_many(
    source: str,
    grids: Iterable[Any],
    *,
    bridge: RacketBridge | None = None,
) -> list[list[list[int]]]:
    """Execute one exact Racket materialization over several grids at once."""
    normalized = [normalize_grid(grid) for grid in grids]
    if not normalized:
        return []
    literal = "'(" + " ".join(_racket_grid_literal(grid) for grid in normalized) + ")"
    expression = f"(map {rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            result = owned.eval_text(expression)
    else:
        result = bridge.eval_text(expression)
    return [normalize_grid(grid) for grid in result]


def execute_rule(
    source: str,
    grid: Any,
    *,
    bridge: RacketBridge | None = None,
) -> list[list[int]]:
    """Execute one exact Racket materialization over one grid."""
    return execute_rule_many(source, [grid], bridge=bridge)[0]


def parent_pair_set(grid: Any) -> set[str]:
    """Return active top-row diagonal-parent witnesses such as ``25``."""
    normalized = normalize_grid(grid)
    top = normalized[0]
    return {
        f"{top[column]}{top[column + 2]}"
        for column in range(len(top) - 2)
        if top[column] in (2, 5) and top[column + 2] in (2, 5)
    }


def _input_rows(
    seed: int,
    count: int,
    *,
    root: Path,
) -> tuple[list[dict[str, Any]], str, str]:
    """Generate distinct mixed-parent inputs from the selected production source."""
    _validate_seed(seed)
    _validate_count(count, "input_count")
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=root
    )
    placements = tuple(generator.PLACEMENTS)
    supports = tuple(generator.SUPPORT_MODES)
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    max_attempts = max(200, count * 80)
    for attempt in range(max_attempts):
        support = supports[(seed + attempt) % len(supports)]
        placement = placements[(seed // 2 + attempt) % len(placements)]
        chain_length = 5 + ((seed + attempt // 2) % 3)
        grid_height = 3 + ((seed * 3 + attempt) % 6)
        difficulty = ("easy", "medium", "hard")[(seed + attempt) % 3]
        try:
            grid = generator.generate(
                seed * 1_000_003 + attempt * 97 + 17,
                seed * 65_537 + attempt * 193 + 29,
                difficulty=difficulty,
                grid_h=grid_height,
                grid_w=16,
                chain_length=chain_length,
                seed_profile="mixed",
                support_mode=support,
                placement=placement,
            )
        except ValueError:
            # Some exact placement/support/length triples are intentionally
            # incompatible; the bounded schedule moves to the next lawful one.
            continue
        errors = generator.self_check(grid)
        if errors:
            raise AssertionError(f"selected generator returned an unlawful input: {errors}")
        witnesses = parent_pair_set(grid)
        if witnesses != {"22", "25", "52", "55"}:
            raise AssertionError(f"mixed profile lost a parent witness: {witnesses}")
        input_sha256 = _grid_sha256(grid)
        if input_sha256 in seen:
            continue
        seen.add(input_sha256)
        rows.append(
            {
                "fixture_id": f"input-{input_sha256[:16]}",
                "input": grid,
                "input_sha256": input_sha256,
                "parent_pairs": sorted(witnesses),
                "generator_request": {
                    "seed": seed * 1_000_003 + attempt * 97 + 17,
                    "sample_index": seed * 65_537 + attempt * 193 + 29,
                    "difficulty": difficulty,
                    "grid_h": grid_height,
                    "grid_w": 16,
                    "chain_length": chain_length,
                    "seed_profile": "mixed",
                    "support_mode": support,
                    "placement": placement,
                },
            }
        )
        if len(rows) == count:
            break
    if len(rows) != count:
        raise RuntimeError(
            f"could only generate {len(rows)} distinct mixed inputs out of {count}"
        )
    return rows, generator_path.relative_to(root).as_posix(), generator_sha256


def make_episode(
    seed: Any,
    *,
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one complete fixed-setting episode with separate query count."""
    validated_seed = _validate_seed(seed)
    demos = _validate_count(demo_count, "demo_count")
    queries = _validate_count(query_count, "query_count")
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    selected = choose_setting(validated_seed)
    canonical = canonical_source(root=resolved_root)
    rules = {
        policy: materialize_rule(policy, source=canonical)
        for policy in DIFFERENT_PARENT_POLICIES
    }
    input_rows, generator_path, generator_sha256 = _input_rows(
        validated_seed, demos + queries, root=resolved_root
    )
    inputs = [row["input"] for row in input_rows]
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        outputs = {
            policy: execute_rule_many(source, inputs, bridge=active)
            for policy, source in rules.items()
        }
    for index, row in enumerate(input_rows):
        if outputs["right"][index] == outputs["left"][index]:
            raise AssertionError(
                f"fixture {row['fixture_id']} does not distinguish parent policies"
            )

    pairs: list[dict[str, Any]] = []
    for index, row in enumerate(input_rows):
        output = outputs[selected][index]
        pairs.append(
            {
                **copy.deepcopy(row),
                "different_parent": selected,
                "output": output,
                "output_sha256": _grid_sha256(output),
            }
        )
    episode = {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": validated_seed,
        "parameters": {"different_parent": selected},
        "parameter_contract": {
            "different_parent": {
                "allowed": list(DIFFERENT_PARENT_POLICIES),
                "default": DEFAULT_DIFFERENT_PARENT,
                "input_constraints_depend_on_parameter": False,
            }
        },
        "counts": {"demonstrations": demos, "queries": queries},
        "generator_source": {
            "path": generator_path,
            "sha256": generator_sha256,
        },
        "rules": {
            policy: {"sha256": _sha256(source), "source": source}
            for policy, source in rules.items()
        },
        "train": copy.deepcopy(pairs[:demos]),
        "test": copy.deepcopy(pairs[demos:]),
        "pairs": copy.deepcopy(pairs),
    }
    public = public_challenge(episode)
    episode["public_id"] = public_challenge_id(public)
    return episode


def analyze_episode(
    episode: dict[str, Any],
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Check labels and the sole declared rival using demonstrations first."""
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    if not isinstance(episode, dict):
        raise TypeError("episode must be a mapping")
    selected = _validate_policy(episode.get("parameters", {}).get("different_parent"))
    rival = next(
        policy for policy in DIFFERENT_PARENT_POLICIES if policy != selected
    )
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not train:
        raise ValueError("episode must contain demonstrations")
    if not isinstance(test, list) or not test:
        raise ValueError("episode must contain queries")
    canonical = canonical_source(root=resolved_root)
    rules = {
        policy: materialize_rule(policy, source=canonical)
        for policy in DIFFERENT_PARENT_POLICIES
    }
    all_pairs = [*train, *test]
    inputs = [normalize_grid(pair.get("input")) for pair in all_pairs]
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        outputs = {
            policy: execute_rule_many(source, inputs, bridge=active)
            for policy, source in rules.items()
        }

    selected_outputs = outputs[selected]
    rival_outputs = outputs[rival]
    demonstration_rows = []
    selected_labels_match = True
    rival_fits = True
    for index, pair in enumerate(train):
        label = normalize_grid(pair.get("output"))
        selected_match = selected_outputs[index] == label
        rival_match = rival_outputs[index] == label
        selected_labels_match &= selected_match
        rival_fits &= rival_match
        demonstration_rows.append(
            {
                "input_sha256": _grid_sha256(pair["input"]),
                "selected_label_matches": selected_match,
                "rival_label_matches": rival_match,
            }
        )

    query_rows = []
    query_labels_match = True
    offset = len(train)
    for query_index, pair in enumerate(test):
        index = offset + query_index
        label = normalize_grid(pair.get("output"))
        selected_match = selected_outputs[index] == label
        query_labels_match &= selected_match
        query_rows.append(
            {
                "query_index": query_index,
                "input_sha256": _grid_sha256(pair["input"]),
                "selected_output_sha256": _grid_sha256(selected_outputs[index]),
                "rival_output_sha256": _grid_sha256(rival_outputs[index]),
                "selected_label_matches": selected_match,
                "rival_query_differs": selected_outputs[index] != rival_outputs[index],
            }
        )
    status = (
        "no_ambiguity_found"
        if selected_labels_match
        and query_labels_match
        and not rival_fits
        and all(row["rival_query_differs"] for row in query_rows)
        else "ambiguous_or_invalid"
    )
    return {
        "status": status,
        "selected": selected,
        "rival": rival,
        "selected_labels_match": selected_labels_match and query_labels_match,
        "rival_fits_demonstrations": rival_fits,
        "demonstrations": demonstration_rows,
        "queries": query_rows,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project an episode to visible demonstrations and unlabeled queries."""
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not train or not isinstance(test, list) or not test:
        raise ValueError("episode must contain nonempty train and test lists")
    return {
        "train": [
            {
                "input": normalize_grid(pair.get("input")),
                "output": normalize_grid(pair.get("output")),
            }
            for pair in train
        ],
        "test": [{"input": normalize_grid(pair.get("input"))} for pair in test],
    }


def public_filename(challenge: dict[str, Any]) -> str:
    """Return a visible-content-only opaque filename."""
    return f"challenge-{public_challenge_id(challenge)}.json"


def _sorted_unique_episode_rows(rows: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted((copy.deepcopy(row) for row in rows), key=lambda row: row["public_id"])
    ids = [row["public_id"] for row in ordered]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate visible public challenge ID")
    return ordered


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _file_record(path: Path) -> dict[str, Any]:
    body = path.read_bytes()
    return {"bytes": len(body), "sha256": _sha256(body)}


def _safe_relative(base: Path, relative: str) -> Path:
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError(f"unsafe evidence path: {relative}")
    path = (base / rel).resolve()
    if not path.is_relative_to(base.resolve()):
        raise ValueError(f"evidence path escapes tree: {relative}")
    return path


def materialize(
    out: Path | str,
    *,
    seeds: Iterable[Any] = (0, 1),
    demo_count: Any = DEFAULT_DEMO_COUNT,
    query_count: Any = DEFAULT_QUERY_COUNT,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Write a fail-closed, self-verifying evidence tree for fixed episodes."""
    demos = _validate_count(demo_count, "demo_count")
    queries = _validate_count(query_count, "query_count")
    validated_seeds = tuple(_validate_seed(seed) for seed in seeds)
    if not validated_seeds:
        raise ValueError("seeds must contain at least one seed")
    if len(validated_seeds) != len(set(validated_seeds)):
        raise ValueError("seeds must be distinct")
    destination = Path(out).resolve()
    if destination.exists():
        raise FileExistsError(f"output directory already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(destination.name + ".tmp")
    if staging.exists():
        raise FileExistsError(f"staging directory already exists: {staging}")
    staging.mkdir()

    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    prototype_path = Path(__file__).resolve()
    canonical = canonical_source(root=resolved_root)
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=resolved_root
    )
    del generator
    rules = {
        policy: materialize_rule(policy, source=canonical)
        for policy in DIFFERENT_PARENT_POLICIES
    }
    try:
        manager = nullcontext(bridge) if bridge is not None else RacketBridge()
        with manager as active:
            episodes = [
                make_episode(
                    seed,
                    demo_count=demos,
                    query_count=queries,
                    root=resolved_root,
                    bridge=active,
                )
                for seed in validated_seeds
            ]
            analyses = [
                analyze_episode(episode, root=resolved_root, bridge=active)
                for episode in episodes
            ]

            rows = []
            prepared_public = {}
            prepared_private = {}
            for episode, analysis in zip(episodes, analyses, strict=True):
                if analysis["status"] != "no_ambiguity_found":
                    raise RuntimeError(
                        f"episode {episode['seed']} failed lesson analysis: {analysis}"
                    )
                public = public_challenge(episode)
                public_id = public_challenge_id(public)
                if public_id != episode["public_id"]:
                    raise AssertionError("episode public ID drifted after construction")
                public_path = f"public/{public_filename(public)}"
                private_path = f"private/episode-{public_id}.json"
                # Prepare the whole batch before publishing any visible bytes.
                # Private seed order and duplicate attempts must not determine
                # public filesystem creation order.
                prepared_public[public_id] = public_challenge_bytes(public)
                prepared_private[public_id] = episode
                rows.append(
                    {
                        "public_id": public_id,
                        "seed": episode["seed"],
                        "parameters": episode["parameters"],
                        "public_path": public_path,
                        "private_path": private_path,
                        "analysis": analysis,
                    }
                )
            rows = _sorted_unique_episode_rows(rows)
            for row in rows:
                public_id = row["public_id"]
                public_path = _safe_relative(staging, row["public_path"])
                public_path.parent.mkdir(parents=True, exist_ok=True)
                public_path.write_bytes(prepared_public[public_id])
                _write_json(
                    _safe_relative(staging, row["private_path"]),
                    prepared_private[public_id],
                )

            rule_rows = {}
            for policy, source in rules.items():
                digest = _sha256(source)
                relative = f"rules/rule-{digest}.rkt"
                path = _safe_relative(staging, relative)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(source, encoding="utf-8")
                rule_rows[policy] = {"path": relative, "sha256": digest}

            status = (
                "no_ambiguity_found"
                if all(row["analysis"]["status"] == "no_ambiguity_found" for row in rows)
                else "ambiguous_or_invalid"
            )
            report = {
                "schema": SCHEMA,
                "task_id": TASK_ID,
                "prototype_version": PROTOTYPE_VERSION,
                "status": status,
                "approved": False,
                "scope": "proposed task-local prototype only",
                "parameters": {
                    "different_parent": {
                        "allowed": list(DIFFERENT_PARENT_POLICIES),
                        "default": DEFAULT_DIFFERENT_PARENT,
                        "input_constraints_depend_on_parameter": False,
                    }
                },
                "counts": {
                    "episodes": len(rows),
                    "demonstrations": len(rows) * demos,
                    "queries": len(rows) * queries,
                },
                "canonical_sha256": _sha256(canonical),
                "prototype_source": prototype_path.relative_to(resolved_root).as_posix(),
                "prototype_source_sha256": _sha256(prototype_path.read_bytes()),
                "generator_source": {
                    "path": generator_path.relative_to(resolved_root).as_posix(),
                    "sha256": generator_sha256,
                },
                "rules": rule_rows,
                "episodes": rows,
                "limits": [
                    "finite evidence covers only the recorded seeds and declared rival",
                    "prototype does not change production generation, catalog state, approval, or training admission",
                ],
            }
            _write_json(staging / "report.json", report)
            manifest_files = {}
            for path in sorted(staging.rglob("*")):
                if path.is_file() and path.name != "manifest.json":
                    manifest_files[path.relative_to(staging).as_posix()] = _file_record(path)
            manifest = {
                "schema": "arcpuzzles-parent-choice-evidence-manifest-v1",
                "files": manifest_files,
            }
            _write_json(staging / "manifest.json", manifest)
            verification = verify_tree(staging, root=resolved_root, bridge=active)
            _write_json(staging / "verification.json", verification)
            if verification["status"] != "pass":
                raise RuntimeError(f"evidence verification failed: {verification['errors']}")
        staging.replace(destination)
        return report
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def verify_tree(
    tree: Path | str,
    *,
    root: Path | str | None = None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Verify source bindings, public/private separation, labels, and rivals."""
    base = Path(tree).resolve()
    resolved_root = find_root(__file__) if root is None else Path(root).resolve()
    errors: list[str] = []
    checked = {"manifest_files": 0, "episodes": 0, "queries": 0}

    try:
        report = json.loads((base / "report.json").read_text(encoding="utf-8"))
    except Exception as error:
        return {"status": "fail", "errors": [f"report unreadable: {error}"], "checked": checked}
    try:
        manifest = json.loads((base / "manifest.json").read_text(encoding="utf-8"))
    except Exception as error:
        return {"status": "fail", "errors": [f"manifest unreadable: {error}"], "checked": checked}

    files = manifest.get("files")
    if not isinstance(files, dict):
        errors.append("manifest files must be a mapping")
        files = {}
    for relative, expected in files.items():
        try:
            path = _safe_relative(base, relative)
            actual = _file_record(path)
            if actual != expected:
                errors.append(f"manifest mismatch for {relative}: {actual} != {expected}")
            checked["manifest_files"] += 1
        except Exception as error:
            errors.append(f"manifest entry {relative} failed: {error}")

    prototype_path = Path(__file__).resolve()
    actual_prototype_sha256 = _sha256(prototype_path.read_bytes())
    if report.get("prototype_source_sha256") != actual_prototype_sha256:
        errors.append(
            "prototype source binding mismatch: "
            f"{report.get('prototype_source_sha256')} != {actual_prototype_sha256}"
        )
    try:
        expected_path = prototype_path.relative_to(resolved_root).as_posix()
        if report.get("prototype_source") != expected_path:
            errors.append("prototype source path binding mismatch")
    except ValueError:
        errors.append("prototype source is outside selected root")

    try:
        canonical = canonical_source(root=resolved_root)
        if report.get("canonical_sha256") != _sha256(canonical):
            errors.append("canonical source binding mismatch")
        _, generator_path, generator_sha256 = load_selected_generator(
            TASK_ID, root=resolved_root
        )
        expected_generator = {
            "path": generator_path.relative_to(resolved_root).as_posix(),
            "sha256": generator_sha256,
        }
        if report.get("generator_source") != expected_generator:
            errors.append("generator source binding mismatch")
    except Exception as error:
        errors.append(f"source binding check failed: {error}")
        canonical = None

    if canonical is not None:
        for policy in DIFFERENT_PARENT_POLICIES:
            try:
                expected_source = materialize_rule(policy, source=canonical)
                row = report.get("rules", {}).get(policy, {})
                path = _safe_relative(base, row.get("path", ""))
                actual_source = path.read_text(encoding="utf-8")
                if actual_source != expected_source:
                    errors.append(f"rule text mismatch for {policy}")
                if row.get("sha256") != _sha256(expected_source):
                    errors.append(f"rule hash mismatch for {policy}")
            except Exception as error:
                errors.append(f"rule check for {policy} failed: {error}")

    episode_rows = report.get("episodes")
    if not isinstance(episode_rows, list) or not episode_rows:
        errors.append("report must contain episode rows")
        episode_rows = []
    public_ids = []
    manager = nullcontext(bridge) if bridge is not None else RacketBridge()
    with manager as active:
        for row in episode_rows:
            try:
                public_id = row["public_id"]
                public_ids.append(public_id)
                public_path = _safe_relative(base, row["public_path"])
                private_path = _safe_relative(base, row["private_path"])
                public = json.loads(public_path.read_text(encoding="utf-8"))
                episode = json.loads(private_path.read_text(encoding="utf-8"))
                if public_filename(public) != public_path.name:
                    errors.append(f"public filename mismatch for {public_id}")
                if public_challenge_id(public) != public_id:
                    errors.append(f"public content ID mismatch for {public_id}")
                if public_challenge(episode) != public:
                    errors.append(f"public/private projection mismatch for {public_id}")
                if episode.get("public_id") != public_id:
                    errors.append(f"private public ID mismatch for {public_id}")
                selected = episode.get("parameters", {}).get("different_parent")
                if any(pair.get("different_parent") != selected for pair in episode.get("pairs", [])):
                    errors.append(f"episode setting is not fixed for {public_id}")
                analysis = analyze_episode(episode, root=resolved_root, bridge=active)
                if analysis != row.get("analysis"):
                    errors.append(f"analysis replay mismatch for {public_id}")
                if analysis["status"] != "no_ambiguity_found":
                    errors.append(f"episode remains ambiguous for {public_id}")
                checked["episodes"] += 1
                checked["queries"] += len(analysis["queries"])
            except Exception as error:
                errors.append(f"episode verification failed: {error}")

    if public_ids != sorted(public_ids):
        errors.append("episode rows are not sorted by public ID")
    if len(public_ids) != len(set(public_ids)):
        errors.append("duplicate visible public challenge ID")
    counts = report.get("counts", {})
    expected_counts = {
        "episodes": checked["episodes"],
        "demonstrations": sum(
            len(json.loads(_safe_relative(base, row["private_path"]).read_text()).get("train", []))
            for row in episode_rows
            if isinstance(row, dict) and "private_path" in row
        ),
        "queries": checked["queries"],
    }
    if counts != expected_counts:
        errors.append(f"count mismatch: {counts} != {expected_counts}")
    return {"status": "pass" if not errors else "fail", "errors": errors, "checked": checked}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--demo-count", type=int, default=DEFAULT_DEMO_COUNT)
    parser.add_argument("--query-count", type=int, default=DEFAULT_QUERY_COUNT)
    parser.add_argument("--out", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    report = materialize(
        args.out,
        seeds=args.seeds,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
