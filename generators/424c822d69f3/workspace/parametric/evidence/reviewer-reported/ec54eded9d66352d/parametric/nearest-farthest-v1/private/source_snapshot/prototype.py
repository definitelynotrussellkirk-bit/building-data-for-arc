#!/usr/bin/env python3
"""Proposed, unapproved nearest/farthest marker prototype for 424c822d69f3."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "424c822d69f3"
VERSION = "proposed-nearest-farthest-v1"
ALLOWED_SELECTION_MODES = ("nearest", "farthest")
DEFAULT_SELECTION_MODE = "nearest"
CANONICAL_SOURCE_SHA256 = "1379212df45efd44f4bb6d4cafca92b9588442bfc83807ed5d926d3048ccade5"
NEAREST_SELECTOR = "(marker (argmin (lambda (m)"
FARTHEST_SELECTOR = "(marker (argmax (lambda (m)"


def _sha256(value: str | bytes) -> str:
    payload = value.encode() if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(NEAREST_SELECTOR) != 1 or FARTHEST_SELECTOR in source:
        raise ValueError("canonical source does not contain the unique guarded nearest selector")
    return source


def canonical_source(*, root=None) -> str:
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources = {
        row["program_solution"]
        for line in canonical_path(root).read_text(encoding="utf-8").splitlines()
        if line.strip()
        if (row := json.loads(line)).get("task_id") == TASK_ID
        and isinstance(row.get("program_solution"), str)
    }
    if len(sources) != 1:
        raise ValueError(f"expected one distinct canonical source for {TASK_ID}, got {len(sources)}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    selection_mode=DEFAULT_SELECTION_MODE,
    *,
    root=None,
    source: str | None = None,
) -> str:
    if type(selection_mode) is not str or selection_mode not in ALLOWED_SELECTION_MODES:
        raise ValueError(f"selection_mode must be one of {ALLOWED_SELECTION_MODES!r}")
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if selection_mode == DEFAULT_SELECTION_MODE:
        return canonical
    return canonical.replace(NEAREST_SELECTOR, FARTHEST_SELECTOR, 1)


def restore_canonical(source: str) -> str:
    if not isinstance(source, str):
        raise ValueError("source must be a Racket source string")
    if source.count(FARTHEST_SELECTOR) != 1 or NEAREST_SELECTOR in source:
        raise ValueError("source is not the unique guarded farthest variant")
    return _check_canonical_source(source.replace(FARTHEST_SELECTOR, NEAREST_SELECTOR, 1))


def _selection_mode(source: str) -> str:
    if _sha256(source) == CANONICAL_SOURCE_SHA256:
        _check_canonical_source(source)
        return "nearest"
    restore_canonical(source)
    return "farthest"


def rule_callable(source: str) -> str:
    _selection_mode(source)
    if not source.startswith("(rule!") or not source.endswith(")"):
        raise ValueError("source must be exactly one (rule! expression)")
    body = source[len("(rule!"):-1].strip()
    body = "\n".join(
        line for line in body.splitlines() if not line.lstrip().startswith(";;")
    ).strip()
    if not body.startswith("(lambda (g)"):
        raise ValueError("pinned source must contain a lambda over g")
    return body


def execute_rule(source: str, grid, *, bridge: RacketBridge | None = None):
    """Execute one exact materialized Racket rule; no Python answer mirror is used."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))

MAX_EPISODE_COUNT = 8
MAX_INPUT_ATTEMPTS = 512


def _validate_seed(seed) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("episode seed must be a literal integer in 0..2**63-1")
    return seed


def _validate_count(name: str, value) -> int:
    if type(value) is not int or not 1 <= value <= MAX_EPISODE_COUNT:
        raise ValueError(f"{name} must be a literal integer in 1..{MAX_EPISODE_COUNT}")
    return value


def parameters_for_seed(seed) -> dict[str, str]:
    """Choose exactly one rule setting for the complete episode."""
    _validate_seed(seed)
    return {"selection_mode": ALLOWED_SELECTION_MODES[seed % len(ALLOWED_SELECTION_MODES)]}


def _grid_sha256(grid) -> str:
    normalized = normalize_grid(grid)
    payload = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return _sha256(payload)


def _components(grid, color=5):
    unseen = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }
    result = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        todo = [start]
        cells = []
        while todo:
            row, col = todo.pop()
            cells.append((row, col))
            for point in (
                (row - 1, col),
                (row + 1, col),
                (row, col - 1),
                (row, col + 1),
            ):
                if point in unseen:
                    unseen.remove(point)
                    todo.append(point)
        result.append(tuple(sorted(cells)))
    return sorted(result, key=lambda cells: (min(col for _, col in cells), min(row for row, _ in cells)))


def extremum_facts(grid) -> list[dict]:
    """Describe unique nearest/farthest marker choices without producing labels."""
    normalized = normalize_grid(grid)
    markers = [
        (col, value)
        for col, value in enumerate(normalized[0])
        if value not in (0, 5)
    ]
    if len(markers) < 2:
        raise ValueError("at least two markers are required")
    facts = []
    for index, cells in enumerate(_components(normalized, 5)):
        rows = [row for row, _ in cells]
        cols = [col for _, col in cells]
        bbox = (min(rows), min(cols), max(rows), max(cols))
        center = (bbox[1] + bbox[3]) // 2
        distances = [abs(col - center) for col, _ in markers]
        nearest_distance = min(distances)
        farthest_distance = max(distances)
        nearest = [i for i, distance in enumerate(distances) if distance == nearest_distance]
        farthest = [i for i, distance in enumerate(distances) if distance == farthest_distance]
        if len(nearest) != 1:
            raise ValueError(f"object {index} has a nearest-marker tie")
        if len(farthest) != 1:
            raise ValueError(f"object {index} has a farthest-marker tie")
        nearest_col, nearest_color = markers[nearest[0]]
        farthest_col, farthest_color = markers[farthest[0]]
        facts.append({
            "object_index": index,
            "bbox": list(bbox),
            "center_column": center,
            "nearest": {
                "column": nearest_col,
                "color": nearest_color,
                "distance": nearest_distance,
            },
            "farthest": {
                "column": farthest_col,
                "color": farthest_color,
                "distance": farthest_distance,
            },
        })
    if not facts:
        raise ValueError("at least one color-5 rectangle is required")
    return facts


def _candidate_seed(input_seed: int, attempt: int) -> int:
    digest = hashlib.sha256(
        f"{VERSION}:input:{input_seed}:{attempt}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:8], "big") & (2**63 - 1)


def _collect_inputs(
    generator,
    *,
    input_seed: int,
    count: int,
    max_attempts: int = MAX_INPUT_ATTEMPTS,
):
    """Collect distinct production inputs with unique extrema for both settings."""
    rows = []
    seen = set()
    for attempt in range(max_attempts):
        generator_seed = _candidate_seed(input_seed, attempt)
        grid = normalize_grid(generator.generate(generator_seed, attempt))
        errors = generator.self_check(grid)
        if errors:
            raise RuntimeError(
                f"selected generator emitted an invalid candidate at attempt {attempt}: {errors}"
            )
        try:
            facts = extremum_facts(grid)
        except ValueError:
            continue
        digest = _grid_sha256(grid)
        if digest in seen:
            continue
        seen.add(digest)
        rows.append({
            "input": grid,
            "provenance": {
                "candidate_index": attempt,
                "generator_seed": generator_seed,
                "sample_index": attempt,
                "input_sha256": digest,
                "nearest_unique": True,
                "farthest_unique": True,
                "objects": facts,
            },
        })
        if len(rows) == count:
            return rows
    raise RuntimeError(
        f"unable to collect {count} distinct unique-extrema inputs after {max_attempts} candidates"
    )


def make_episode(
    seed,
    *,
    demo_count: int = 3,
    query_count: int = 4,
    root=None,
    bridge: RacketBridge | None = None,
) -> dict:
    seed = _validate_seed(seed)
    demo_count = _validate_count("demo_count", demo_count)
    query_count = _validate_count("query_count", query_count)
    root = find_root(__file__) if root is None else Path(root).resolve()

    from reviewer_support import load_selected_generator

    generator, generator_path, generator_sha256 = load_selected_generator(TASK_ID, root=root)
    input_seed = seed // len(ALLOWED_SELECTION_MODES)
    inputs = _collect_inputs(
        generator,
        input_seed=input_seed,
        count=demo_count + query_count,
    )
    parameters = parameters_for_seed(seed)
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(
                seed,
                input_seed,
                parameters,
                inputs,
                demo_count,
                query_count,
                root,
                generator_path,
                generator_sha256,
                owned,
            )
    return _make_episode(
        seed,
        input_seed,
        parameters,
        inputs,
        demo_count,
        query_count,
        root,
        generator_path,
        generator_sha256,
        bridge,
    )


def _make_episode(
    seed,
    input_seed,
    parameters,
    inputs,
    demo_count,
    query_count,
    root,
    generator_path,
    generator_sha256,
    bridge,
):
    canonical = canonical_source(root=root)
    rules = {
        mode: materialize_rule(mode, source=canonical)
        for mode in ALLOWED_SELECTION_MODES
    }
    outputs = {
        mode: [execute_rule(source, row["input"], bridge=bridge) for row in inputs]
        for mode, source in rules.items()
    }
    for index in range(len(inputs)):
        if outputs["nearest"][index] == outputs["farthest"][index]:
            raise RuntimeError(f"parameter settings do not change candidate input {index}")

    selected_mode = parameters["selection_mode"]
    selected_outputs = outputs[selected_mode]
    train = [
        {"input": inputs[index]["input"], "output": selected_outputs[index]}
        for index in range(demo_count)
    ]
    test = [
        {"input": inputs[index]["input"], "output": selected_outputs[index]}
        for index in range(demo_count, demo_count + query_count)
    ]

    rivals = []
    ambiguities = []
    for mode in ALLOWED_SELECTION_MODES:
        candidate = outputs[mode]
        demo_mismatches = [
            index
            for index in range(demo_count)
            if candidate[index] != selected_outputs[index]
        ]
        query_mismatches = [
            index - demo_count
            for index in range(demo_count, demo_count + query_count)
            if candidate[index] != selected_outputs[index]
        ]
        if not demo_mismatches and not query_mismatches:
            status = "matches_episode"
        elif demo_mismatches:
            status = "refuted_by_demonstrations"
        else:
            status = "fits_demonstrations_changes_query"
            ambiguities.append({
                "selection_mode": mode,
                "query_mismatch_indices": query_mismatches,
            })
        rivals.append({
            "selection_mode": mode,
            "status": status,
            "demonstration_mismatch_indices": demo_mismatches,
            "query_mismatch_indices": query_mismatches,
        })

    return {
        "schema": "424c822d69f3-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "seed": seed,
        "input_seed": input_seed,
        "parameters": parameters,
        "counts": {
            "demonstrations": demo_count,
            "queries": query_count,
        },
        "train": train,
        "test": test,
        "input_provenance": [row["provenance"] for row in inputs],
        "parameter_rivals": rivals,
        "ambiguities": ambiguities,
        "source_bindings": {
            "generator_path": str(Path(generator_path).relative_to(root)),
            "generator_sha256": generator_sha256,
            "canonical_rule_sha256": _sha256(canonical),
            "rules": {
                mode: _sha256(source)
                for mode, source in rules.items()
            },
        },
    }


def public_bytes(episode: dict) -> bytes:
    """Return the exact bytes that may be exposed to a solver."""
    return public_challenge_bytes(episode)


def public_id(episode: dict) -> str:
    """Content ID of exactly the visible challenge bytes."""
    return public_challenge_id(episode)


def public_challenge(episode: dict) -> dict:
    """Return a detached JSON value containing only public fields."""
    return json.loads(public_bytes(episode))


def _public_records(episodes) -> list[dict]:
    records = []
    seen = set()
    for episode in episodes:
        payload = public_bytes(episode)
        challenge_id = _sha256(payload)
        if challenge_id in seen:
            raise ValueError(f"duplicate visible challenge: {challenge_id}")
        seen.add(challenge_id)
        records.append({
            "public_id": challenge_id,
            "public_bytes": payload,
            "episode": episode,
        })
    return sorted(records, key=lambda row: row["public_id"])


def _write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _file_rows(root: Path, *, exclude=()) -> list[dict[str, str]]:
    excluded = {Path(value).as_posix() for value in exclude}
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        rows.append({"path": relative, "sha256": _sha256(path.read_bytes())})
    return rows


def _validated_seed_set(seeds) -> tuple[int, ...]:
    try:
        values = tuple(seeds)
    except TypeError as error:
        raise ValueError("seeds must be a nonempty iterable of episode seeds") from error
    if not values:
        raise ValueError("at least one episode seed is required")
    for seed in values:
        _validate_seed(seed)
    if len(set(values)) != len(values):
        raise ValueError("episode seeds must be distinct")
    return values


def write_evidence(
    seeds,
    *,
    out,
    demo_count: int = 3,
    query_count: int = 4,
    root=None,
) -> dict:
    """Materialize public challenges plus private, hash-bound verification evidence."""
    seed_values = _validated_seed_set(seeds)
    demo_count = _validate_count("demo_count", demo_count)
    query_count = _validate_count("query_count", query_count)
    root = find_root(__file__) if root is None else Path(root).resolve()
    out = Path(out).resolve()
    if out.exists():
        raise FileExistsError(f"evidence output already exists: {out}")
    out.mkdir(parents=True)

    try:
        with RacketBridge() as bridge:
            episodes = [
                make_episode(
                    seed,
                    demo_count=demo_count,
                    query_count=query_count,
                    root=root,
                    bridge=bridge,
                )
                for seed in seed_values
            ]
            records = _public_records(episodes)

            canonical = canonical_source(root=root)
            rules = {
                mode: materialize_rule(mode, source=canonical)
                for mode in ALLOWED_SELECTION_MODES
            }
            rule_rows = []
            for mode, source in rules.items():
                relative = Path("private/rules") / f"selection-mode-{mode}.rkt"
                destination = out / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(source, encoding="utf-8")
                rule_rows.append({
                    "selection_mode": mode,
                    "path": relative.as_posix(),
                    "sha256": _sha256(source),
                    "canonical_default": mode == DEFAULT_SELECTION_MODE,
                })

            episode_rows = []
            for record in records:
                challenge_id = record["public_id"]
                episode = record["episode"]
                public_relative = Path("public") / f"{challenge_id}.json"
                private_relative = Path("private/episodes") / f"{challenge_id}.json"
                public_path = out / public_relative
                public_path.parent.mkdir(parents=True, exist_ok=True)
                public_path.write_bytes(record["public_bytes"])
                _write_json(out / private_relative, episode)
                episode_rows.append({
                    "public_id": challenge_id,
                    "public_path": public_relative.as_posix(),
                    "private_path": private_relative.as_posix(),
                    "seed": episode["seed"],
                    "input_seed": episode["input_seed"],
                    "selection_mode": episode["parameters"]["selection_mode"],
                })

            source_snapshot = out / "private/source_snapshot"
            source_snapshot.mkdir(parents=True, exist_ok=True)
            prototype_path = Path(__file__).resolve()
            verifier_path = prototype_path.with_name("verify_evidence.py")
            test_path = prototype_path.parents[2] / "tests/test_parametric_prototype.py"
            generator_relative = Path(episodes[0]["source_bindings"]["generator_path"])
            generator_path = root / generator_relative
            for source_path, name in (
                (prototype_path, "prototype.py"),
                (verifier_path, "verify_evidence.py"),
                (test_path, "test_parametric_prototype.py"),
                (generator_path, "generator.py"),
            ):
                (source_snapshot / name).write_bytes(source_path.read_bytes())

            canonical_checks = []
            canonical_mismatches = 0
            for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
                actual = execute_rule(canonical, pair["input"], bridge=bridge)
                matches = actual == pair["output"]
                canonical_mismatches += int(not matches)
                canonical_checks.append({
                    "variant": pair["variant"],
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": _grid_sha256(pair["input"]),
                    "expected_sha256": _grid_sha256(pair["output"]),
                    "actual_sha256": _grid_sha256(actual),
                    "matches": matches,
                })
            _write_json(out / "private/checks/canonical-default.json", {
                "task_id": TASK_ID,
                "rule_sha256": _sha256(canonical),
                "checks": canonical_checks,
                "mismatch_count": canonical_mismatches,
            })

            witness_input = records[0]["episode"]["train"][0]["input"]
            _write_json(out / "private/checks/distinguishing-witness.json", {
                "input": witness_input,
                "outputs": {
                    mode: execute_rule(source, witness_input, bridge=bridge)
                    for mode, source in rules.items()
                },
            })

        ambiguity_count = sum(len(episode["ambiguities"]) for episode in episodes)
        report = {
            "schema": "424c822d69f3-parametric-evidence-v1",
            "task_id": TASK_ID,
            "prototype_version": VERSION,
            "status": "proposed_unapproved",
            "counts": {
                "episodes": len(episodes),
                "settings_exercised": len({
                    episode["parameters"]["selection_mode"] for episode in episodes
                }),
                "demonstrations_per_episode": demo_count,
                "queries_per_episode": query_count,
                "ambiguous_parameter_rivals": ambiguity_count,
                "canonical_pairs_checked": len(canonical_checks),
                "canonical_pair_mismatches": canonical_mismatches,
            },
            "episodes": episode_rows,
            "rules": rule_rows,
            "files": _file_rows(out),
        }
        _write_json(out / "report.json", report)
        manifest = {
            "schema": "424c822d69f3-parametric-manifest-v1",
            "prototype_version": VERSION,
            "files": _file_rows(out, exclude=("manifest.json",)),
        }
        _write_json(out / "manifest.json", manifest)
        return report
    except BaseException as error:
        failure = {
            "status": "failed",
            "error_type": type(error).__name__,
            "error": str(error),
        }
        try:
            _write_json(out / "failure.json", failure)
        except BaseException:
            pass
        raise


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1])
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = _parse_args(argv)
    report = write_evidence(
        args.seeds,
        out=args.out,
        demo_count=args.demo_count,
        query_count=args.query_count,
    )
    print(json.dumps({
        "status": report["status"],
        "episodes": report["counts"]["episodes"],
        "output": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
