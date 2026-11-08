#!/usr/bin/env python3
"""Proposed, unapproved episode-level scale-factor extension for 2dacb90452ce.

The production generator and canonical Racket authority remain unchanged.  This
prototype materializes the canonical 2x nearest-neighbor upscale or a proposed
3x alternative from one hash-pinned source site.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
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


TASK_ID = "2dacb90452ce"
VERSION = "proposed-scale-factor-v1"
SCALE_FACTORS = (2, 3)
DEFAULT_SCALE_FACTOR = 2
CANONICAL_SHA256 = "511f58f5d47190acd7307da0e87d1e6d84d787e18b14ce8c3c14de0471730050"
CANONICAL_SITE = "(upscale g 2)"
ALTERNATIVE_SITE = "(upscale g 3)"
ROOT = find_root(__file__)
GEN, GENERATOR_PATH, GENERATOR_SHA256 = load_selected_generator(TASK_ID, root=ROOT)
COUNT_LIMIT = 12


def sha256(value: str | bytes) -> str:
    raw = value if isinstance(value, bytes) else value.encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _validate_scale_factor(scale_factor: int) -> int:
    if type(scale_factor) is not int or scale_factor not in SCALE_FACTORS:
        raise ValueError(f"scale_factor must be one of {SCALE_FACTORS}")
    return scale_factor


def _check_canonical_source(source: str) -> str:
    if type(source) is not str or sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical Racket SHA-256 does not match the pinned rule")
    if source.count(CANONICAL_SITE) != 1 or ALTERNATIVE_SITE in source:
        raise ValueError("canonical Racket source changed at the guarded upscale site")
    return source


def canonical_rule(*, root=None) -> str:
    """Return the unique canonical Racket rule, byte-for-byte and hash-pinned."""
    selected_root = ROOT if root is None else Path(root).resolve()
    sources: list[str] = []
    with canonical_path(selected_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                source = row.get("program_solution")
                if isinstance(source, str):
                    sources.append(source)
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical rule for {TASK_ID}")
    return _check_canonical_source(sources[0])


def instantiate_rule(
    scale_factor: int = DEFAULT_SCALE_FACTOR, *, root=None, source: str | None = None
) -> str:
    """Materialize the exact canonical rule or the one-site 3x alternative."""
    factor = _validate_scale_factor(scale_factor)
    canonical = canonical_rule(root=root) if source is None else _check_canonical_source(source)
    if factor == DEFAULT_SCALE_FACTOR:
        return canonical
    alternative = canonical.replace(CANONICAL_SITE, ALTERNATIVE_SITE, 1)
    if alternative == canonical:
        raise ValueError("alternative scale factor did not change the Racket program")
    return alternative


def restore_canonical(program: str, *, root=None) -> str:
    """Prove that a materialized rule differs only at the declared factor site."""
    if type(program) is not str:
        raise TypeError("program must be Racket source text")
    canonical = canonical_rule(root=root)
    if program == canonical:
        return canonical
    if program.count(ALTERNATIVE_SITE) != 1 or CANONICAL_SITE in program:
        raise ValueError("program is not the declared scale-factor alternative")
    restored = program.replace(ALTERNATIVE_SITE, CANONICAL_SITE, 1)
    if restored != canonical or sha256(restored) != CANONICAL_SHA256:
        raise ValueError("program differs from canonical outside the scale-factor site")
    return restored


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be a plain Python integer")
    if seed < 0:
        raise ValueError("seed must be nonnegative")
    return seed


def _validate_count(name: str, value: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be a plain Python integer")
    if not 1 <= value <= COUNT_LIMIT:
        raise ValueError(f"{name} must be between 1 and {COUNT_LIMIT}")
    return value


def choose_scale_factor(seed: int) -> int:
    """Choose one hidden factor for the entire episode."""
    value = _validate_seed(seed)
    return SCALE_FACTORS[value % len(SCALE_FACTORS)]


def generate_inputs(
    seed: int, *, demo_count: int = 2, query_count: int = 4
) -> list[list[list[int]]]:
    """Return distinct lawful canonical-manifold inputs, independent of factor."""
    value = _validate_seed(seed)
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    total = demos + queries
    generation_seed = 2_026_102_300_001 + value * 10_007
    bands = ("easy", "medium", "hard", "medium")
    grids: list[list[list[int]]] = []
    seen: set[str] = set()
    candidate_index = 0
    max_attempts = max(64, total * 16)
    while len(grids) < total and candidate_index < max_attempts:
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
        if key not in seen:
            seen.add(key)
            grids.append([list(row) for row in grid])
        candidate_index += 1
    if len(grids) != total:
        raise RuntimeError(
            f"could not obtain {total} distinct lawful inputs in {max_attempts} attempts"
        )
    return grids


def evaluate(bridge: RacketBridge, program: str, grid) -> list[list[int]]:
    """Execute one exact materialized rule through the packet's Racket authority."""
    restore_canonical(program)
    normalized = normalize_grid(grid)
    function = strip_rule_wrapper(program)
    if not function.startswith("(lambda (g)"):
        raise ValueError("expected the selected task's native Racket lambda")
    datum = "(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    return normalize_grid(bridge.eval_text(f"({function} '{datum})"))


def _grid_sha256(grid) -> str:
    normalized = normalize_grid(grid)
    raw = json.dumps(normalized, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(raw)


def make_episode(
    bridge: RacketBridge,
    seed: int,
    *,
    scale_factor: int | None = None,
    demo_count: int = 2,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one private episode with a single factor and Racket-derived labels."""
    value = _validate_seed(seed)
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    factor = choose_scale_factor(value) if scale_factor is None else _validate_scale_factor(scale_factor)
    program = instantiate_rule(factor)
    inputs = generate_inputs(value, demo_count=demos, query_count=queries)
    pairs = []
    for grid in inputs:
        output = evaluate(bridge, program, grid)
        pairs.append(
            {
                "input": grid,
                "output": output,
                "input_sha256": _grid_sha256(grid),
                "output_sha256": _grid_sha256(output),
            }
        )
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": value,
        "parameters": {"scale_factor": factor},
        "parameter_choice": (
            "seed_modulo_two" if scale_factor is None else "explicit_once_per_episode"
        ),
        "demo_count": demos,
        "query_count": queries,
        "generator_path": str(GENERATOR_PATH.relative_to(ROOT)),
        "generator_sha256": GENERATOR_SHA256,
        "canonical_rule_sha256": CANONICAL_SHA256,
        "racket_program": program,
        "racket_sha256": sha256(program),
        "pairs": pairs,
    }


def analyze_episode(bridge: RacketBridge, episode: dict[str, Any]) -> dict[str, Any]:
    """Check each query against every other factor using demonstrations only."""
    if not isinstance(episode, dict):
        raise TypeError("episode must be a mapping")
    factor = _validate_scale_factor(episode.get("parameters", {}).get("scale_factor"))
    demos = _validate_count("demo_count", episode.get("demo_count"))
    queries = _validate_count("query_count", episode.get("query_count"))
    pairs = episode.get("pairs")
    if type(pairs) is not list or len(pairs) != demos + queries:
        raise ValueError("episode pair count does not match demo_count + query_count")

    chosen_program = instantiate_rule(factor)
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            raise ValueError(f"pair {index} must contain private input and output")
        actual = evaluate(bridge, chosen_program, pair["input"])
        if actual != normalize_grid(pair["output"]):
            raise ValueError(f"pair {index} output does not match the selected Racket rule")

    rival_cache: dict[int, dict[str, Any]] = {}
    for rival_factor in SCALE_FACTORS:
        if rival_factor == factor:
            continue
        rival_program = instantiate_rule(rival_factor)
        predictions = [evaluate(bridge, rival_program, pair["input"]) for pair in pairs]
        refuting = [
            index
            for index in range(demos)
            if predictions[index] != normalize_grid(pairs[index]["output"])
        ]
        rival_cache[rival_factor] = {
            "program": rival_program,
            "racket_sha256": sha256(rival_program),
            "predictions": predictions,
            "refuting_demonstration_indices": refuting,
        }

    query_rows = []
    for query_offset in range(queries):
        pair_index = demos + query_offset
        rival_rows = []
        for rival_factor, cached in rival_cache.items():
            query_differs = (
                cached["predictions"][pair_index]
                != normalize_grid(pairs[pair_index]["output"])
            )
            refuting = list(cached["refuting_demonstration_indices"])
            rival_rows.append(
                {
                    "scale_factor": rival_factor,
                    "racket_sha256": cached["racket_sha256"],
                    "refuting_demonstration_indices": refuting,
                    "query_differs": query_differs,
                    "status": (
                        "refuted_by_demonstrations"
                        if refuting
                        else "ambiguous_on_query" if query_differs else "answer_equivalent"
                    ),
                }
            )
        query_rows.append(
            {
                "query_index": query_offset,
                "pair_index": pair_index,
                "status": (
                    "no_ambiguity_found"
                    if all(row["refuting_demonstration_indices"] for row in rival_rows)
                    else "ambiguous_parameter"
                ),
                "rivals": rival_rows,
            }
        )

    return {
        "schema": "arcpuzzles-parametric-rival-analysis-v1",
        "task_id": TASK_ID,
        "selected_scale_factor": factor,
        "demonstrations_used": list(range(demos)),
        "queries": query_rows,
        "status": (
            "no_ambiguity_found"
            if all(row["status"] == "no_ambiguity_found" for row in query_rows)
            else "ambiguity_found"
        ),
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project a private episode to visible demos and unlabeled query inputs."""
    if not isinstance(episode, dict):
        raise TypeError("episode must be a mapping")
    demos = _validate_count("demo_count", episode.get("demo_count"))
    queries = _validate_count("query_count", episode.get("query_count"))
    pairs = episode.get("pairs")
    if type(pairs) is not list or len(pairs) != demos + queries:
        raise ValueError("episode pair count does not match demo_count + query_count")
    challenge = {
        "train": [
            {
                "input": deepcopy(normalize_grid(pair["input"])),
                "output": deepcopy(normalize_grid(pair["output"])),
            }
            for pair in pairs[:demos]
        ],
        "test": [
            {"input": deepcopy(normalize_grid(pair["input"]))}
            for pair in pairs[demos:]
        ],
    }
    public_challenge_bytes(challenge)
    return challenge


def public_filename(value: dict[str, Any]) -> str:
    """Name a public challenge from visible bytes only."""
    challenge = public_challenge(value) if "pairs" in value else value
    return f"challenge-{public_challenge_id(challenge)}.json"


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _file_rows(out: Path) -> list[dict[str, str]]:
    rows = []
    for path in sorted(candidate for candidate in out.rglob("*") if candidate.is_file()):
        if path.name == "report.json":
            continue
        rows.append(
            {
                "path": path.relative_to(out).as_posix(),
                "sha256": sha256(path.read_bytes()),
            }
        )
    return rows


def materialize(
    out: Path | str,
    *,
    seed: int = 0,
    demo_count: int = 2,
    query_count: int = 4,
    root=None,
) -> dict[str, Any]:
    """Write two source-bound episodes, one for each factor, plus compact evidence."""
    base_seed = _validate_seed(seed)
    demos = _validate_count("demo_count", demo_count)
    queries = _validate_count("query_count", query_count)
    destination = Path(out)
    if destination.exists():
        raise FileExistsError(destination)
    destination.mkdir(parents=True)
    selected_root = ROOT if root is None else Path(root).resolve()

    canonical = canonical_rule(root=selected_root)
    rule_paths: dict[int, str] = {}
    for factor in SCALE_FACTORS:
        program = instantiate_rule(factor, root=selected_root, source=canonical)
        relative = f"private/rules/scale-factor-{factor}.rkt"
        path = destination / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(program, encoding="utf-8")
        rule_paths[factor] = relative

    canonical_rows = []
    episode_rows = []
    public_payloads: list[tuple[str, str, bytes]] = []
    public_ids: set[str] = set()
    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=selected_root, labeled_only=True):
            actual = evaluate(bridge, canonical, pair["input"])
            if actual != pair["output"]:
                raise AssertionError(
                    f"canonical pair {pair['split']}:{pair['pair_index']} disagrees with Racket"
                )
            canonical_rows.append(
                {
                    "split": pair["split"],
                    "pair_index": pair["pair_index"],
                    "input_sha256": _grid_sha256(pair["input"]),
                    "output_sha256": _grid_sha256(actual),
                }
            )

        for episode_seed in (base_seed, base_seed + 1):
            episode = make_episode(
                bridge,
                episode_seed,
                demo_count=demos,
                query_count=queries,
            )
            replay = make_episode(
                bridge,
                episode_seed,
                demo_count=demos,
                query_count=queries,
            )
            if replay != episode:
                raise AssertionError(f"episode seed {episode_seed} did not replay exactly")
            analysis = analyze_episode(bridge, episode)
            if analysis["status"] != "no_ambiguity_found":
                raise AssertionError(f"episode seed {episode_seed} remains ambiguous")
            visible = public_challenge(episode)
            public_id = public_challenge_id(visible)
            if public_id in public_ids:
                raise ValueError("duplicate visible challenge payload")
            public_ids.add(public_id)
            public_path = f"public/challenge-{public_id}.json"
            private_path = f"private/episodes/episode-{public_id}.json"
            analysis_path = f"private/analysis/analysis-{public_id}.json"
            public_payloads.append(
                (public_id, public_path, public_challenge_bytes(visible))
            )
            _write_json(destination / private_path, episode)
            _write_json(destination / analysis_path, analysis)
            episode_rows.append(
                {
                    "seed": episode_seed,
                    "scale_factor": episode["parameters"]["scale_factor"],
                    "public_id": public_id,
                    "public_path": public_path,
                    "private_path": private_path,
                    "analysis_path": analysis_path,
                    "rule_path": rule_paths[episode["parameters"]["scale_factor"]],
                    "racket_sha256": episode["racket_sha256"],
                    "status": analysis["status"],
                }
            )

        # Public artifact creation order must be derived exclusively from visible
        # challenge bytes, never from the private seed/setting enumeration above.
        for _, public_path, payload in sorted(public_payloads):
            path = destination / public_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)

        settings_seen = sorted(row["scale_factor"] for row in episode_rows)
        if settings_seen != list(SCALE_FACTORS):
            raise AssertionError(f"expected both factors, got {settings_seen}")
        witness_input = episode_rows and json.loads(
            (destination / episode_rows[0]["private_path"]).read_text(encoding="utf-8")
        )["pairs"][0]["input"]
        witness_outputs = {
            str(factor): evaluate(bridge, instantiate_rule(factor, root=selected_root), witness_input)
            for factor in SCALE_FACTORS
        }
        if witness_outputs["2"] == witness_outputs["3"]:
            raise AssertionError("distinguishing witness does not separate scale factors")
        witness = {
            "input": witness_input,
            "outputs_by_scale_factor": witness_outputs,
            "rule_sha256_by_scale_factor": {
                str(factor): sha256(instantiate_rule(factor, root=selected_root))
                for factor in SCALE_FACTORS
            },
        }
        _write_json(destination / "private/distinguishing-witness.json", witness)

    prototype_path = Path(__file__).resolve()
    test_path = ROOT / "generators/2dacb90452ce/tests/test_parametric_scale_factor.py"
    report: dict[str, Any] = {
        "schema": "arcpuzzles-parametric-evidence-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "no_ambiguity_found",
        "approval_status": "proposed_unapproved",
        "parameter_contract": {
            "name": "scale_factor",
            "allowed_values": list(SCALE_FACTORS),
            "canonical_default": DEFAULT_SCALE_FACTOR,
            "selection": "one value chosen once per episode from seed parity",
            "input_constraints": "unchanged canonical-scale 2..5 square inputs",
        },
        "source_hashes": {
            "canonical_rule_sha256": CANONICAL_SHA256,
            "generator_sha256": GENERATOR_SHA256,
            "prototype_sha256": sha256(prototype_path.read_bytes()),
            "test_sha256": sha256(test_path.read_bytes()) if test_path.is_file() else None,
        },
        "runtime": racket_runtime_status(),
        "canonical_checks": canonical_rows,
        "episodes": episode_rows,
        "witness_path": "private/distinguishing-witness.json",
        "counts": {
            "episodes": len(episode_rows),
            "canonical_labels_passed": len(canonical_rows),
            "demonstrations": len(episode_rows) * demos,
            "queries": len(episode_rows) * queries,
            "query_ambiguities": sum(
                row["status"] != "no_ambiguity_found" for row in episode_rows
            ),
            "settings_seen": sorted({row["scale_factor"] for row in episode_rows}),
        },
        "limits": [
            "Only scale factors 2 and 3 and two retained episode seeds are covered.",
            "Rival analysis covers the declared alternative factor, not every possible rule.",
            "This prototype does not change production generation, approval, or training admission.",
        ],
        "invocation": {"argv": list(sys.argv), "cwd": str(Path.cwd())},
    }
    report["files"] = _file_rows(destination)
    _write_json(destination / "report.json", report)
    return report


def verify_tree(out: Path | str, *, root=None) -> dict[str, Any]:
    """Replay hashes, public projections, exact rules, labels, and rival analyses."""
    destination = Path(out)
    report = json.loads((destination / "report.json").read_text(encoding="utf-8"))
    selected_root = ROOT if root is None else Path(root).resolve()
    source_hashes = report.get("source_hashes", {})
    if source_hashes.get("generator_sha256") != GENERATOR_SHA256:
        raise ValueError("report generator hash does not match this prototype")
    episode_rows = report.get("episodes")
    if (
        type(episode_rows) is not list
        or len(episode_rows) != len(SCALE_FACTORS)
        or sorted(row.get("scale_factor") for row in episode_rows if isinstance(row, dict))
        != list(SCALE_FACTORS)
    ):
        raise ValueError("report episode rows must cover each declared scale factor exactly once")
    files = report.get("files")
    if type(files) is not list:
        raise ValueError("report is missing its file manifest")
    for row in files:
        path = destination / row["path"]
        if not path.is_file() or sha256(path.read_bytes()) != row["sha256"]:
            raise ValueError(f"evidence file hash mismatch: {row['path']}")

    if report.get("source_hashes", {}).get("canonical_rule_sha256") != CANONICAL_SHA256:
        raise ValueError("report canonical rule hash does not match this prototype")
    if report.get("source_hashes", {}).get("prototype_sha256") != sha256(Path(__file__).read_bytes()):
        raise ValueError("prototype source hash differs from the retained report")

    canonical = canonical_rule(root=selected_root)
    episodes_verified = 0
    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=selected_root, labeled_only=True):
            if evaluate(bridge, canonical, pair["input"]) != pair["output"]:
                raise ValueError("canonical Racket replay failed")
        for row in report.get("episodes", []):
            public_path = destination / row["public_path"]
            private_path = destination / row["private_path"]
            analysis_path = destination / row["analysis_path"]
            public = json.loads(public_path.read_text(encoding="utf-8"))
            private = json.loads(private_path.read_text(encoding="utf-8"))
            retained_analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
            if public_path.name != public_filename(public):
                raise ValueError("public filename does not match visible challenge bytes")
            if public_path.read_bytes() != public_challenge_bytes(public):
                raise ValueError("public file is not in canonical visible-byte form")
            if public != public_challenge(private):
                raise ValueError("public challenge does not match its private episode")
            factor = private["parameters"]["scale_factor"]
            expected_rule = instantiate_rule(factor, root=selected_root)
            if (destination / row["rule_path"]).read_text(encoding="utf-8") != expected_rule:
                raise ValueError("retained Racket rule differs from the declared setting")
            for index, pair in enumerate(private["pairs"]):
                if evaluate(bridge, expected_rule, pair["input"]) != pair["output"]:
                    raise ValueError(f"episode label {index} failed Racket replay")
            fresh_analysis = analyze_episode(bridge, private)
            if fresh_analysis != retained_analysis:
                raise ValueError("retained rival analysis does not replay exactly")
            episodes_verified += 1

        witness = json.loads(
            (destination / report["witness_path"]).read_text(encoding="utf-8")
        )
        for factor in SCALE_FACTORS:
            actual = evaluate(
                bridge, instantiate_rule(factor, root=selected_root), witness["input"]
            )
            if actual != witness["outputs_by_scale_factor"][str(factor)]:
                raise ValueError("distinguishing witness failed Racket replay")

    return {
        "status": "pass",
        "files_verified": len(files),
        "episodes_verified": episodes_verified,
        "canonical_labels_verified": len(report.get("canonical_checks", [])),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("materialize", help="write new evidence")
    build.add_argument("--out", type=Path, required=True)
    build.add_argument("--seed", type=int, default=0)
    build.add_argument("--demo-count", type=int, default=2)
    build.add_argument("--query-count", type=int, default=4)
    verify = subparsers.add_parser("verify", help="replay an evidence tree")
    verify.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "materialize":
        result = materialize(
            args.out,
            seed=args.seed,
            demo_count=args.demo_count,
            query_count=args.query_count,
        )
        summary = {"status": result["status"], "counts": result["counts"]}
    else:
        summary = verify_tree(args.out)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
