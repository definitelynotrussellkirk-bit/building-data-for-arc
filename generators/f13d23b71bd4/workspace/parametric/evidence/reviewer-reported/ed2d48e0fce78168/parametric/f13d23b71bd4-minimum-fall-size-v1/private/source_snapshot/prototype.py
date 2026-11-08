#!/usr/bin/env python3
"""Proposed episode-level minimum-fall-size extension for f13d23b71bd4.

The selected production generator and canonical threshold-4 rule remain
unchanged.  This task-local prototype chooses one hidden threshold per complete
episode, generates boundary-rich inputs from the selected generator's existing
``mixed_sizes_1_to_6`` profile, and obtains every selected and rival label from
the included Racket runtime.
"""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

from arc_repl.racket_bridge import RacketBridge, racket_runtime_status
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
    public_challenge_bytes,
    public_challenge_id,
)


TASK_ID = "f13d23b71bd4"
VERSION = "proposed-minimum-fall-size-v1"
ALLOWED_MINIMUM_FALL_SIZES = (3, 4, 5)
DEFAULT_MINIMUM_FALL_SIZE = 4
CANONICAL_SHA256 = "71a162d2019efc9e1dad31b9b6f99b2a6f80089126ad749ee444696b61efbf45"
CANONICAL_RULE_HASH = "71a162d2019e"
BASE_GENERATOR_SHA256 = "5b2f9dfdf528813ad9d342a086943138201231be812b77fcf135c510c57b2b32"
THRESHOLD_SITE = "(>= (obj-size obj) 4)"
MAX_PAIRS_PER_EPISODE = 16
INPUT_PROFILE = "mixed_sizes_1_to_6"


def _sha256(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def grid_sha256(grid) -> str:
    return _sha256(_json(normalize_grid(grid)))


def _validate_seed(seed: int) -> None:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")


def _validate_count(name: str, value: int) -> None:
    if type(value) is not int or not 1 <= value <= MAX_PAIRS_PER_EPISODE:
        raise ValueError(f"{name} must be an integer in 1..{MAX_PAIRS_PER_EPISODE}")


def _validate_difficulty(difficulty: str) -> None:
    if difficulty not in {"easy", "medium", "hard"}:
        raise ValueError("difficulty must be 'easy', 'medium', or 'hard'")


def _validate_minimum_fall_size(minimum_fall_size: int) -> None:
    if (type(minimum_fall_size) is not int
            or minimum_fall_size not in ALLOWED_MINIMUM_FALL_SIZES):
        raise ValueError(
            "minimum_fall_size must be one of the exact integers "
            f"{ALLOWED_MINIMUM_FALL_SIZES}"
        )


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or _sha256(source) != CANONICAL_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned rule")
    if source.count(THRESHOLD_SITE) != 1:
        raise ValueError("canonical source must contain exactly one guarded threshold site")
    return source


def canonical_source(*, root=None) -> str:
    root = find_root(__file__) if root is None else Path(root).resolve()
    sources = set()
    with canonical_path(root).open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    sources.add(row.get("program_solution"))
    if len(sources) != 1:
        raise ValueError(f"expected exactly one distinct canonical source for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def materialize_rule(
    minimum_fall_size: int = DEFAULT_MINIMUM_FALL_SIZE,
    *,
    root=None,
    source: str | None = None,
) -> str:
    """Return exact Racket for one proposed hidden threshold setting."""
    _validate_minimum_fall_size(minimum_fall_size)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if minimum_fall_size == DEFAULT_MINIMUM_FALL_SIZE:
        return canonical
    return canonical.replace(
        THRESHOLD_SITE,
        f"(>= (obj-size obj) {minimum_fall_size})",
        1,
    )


def _canonicalize_materialized_source(source: str) -> str:
    if not isinstance(source, str):
        raise ValueError("Racket source must be text")
    matches = [
        value for value in ALLOWED_MINIMUM_FALL_SIZES
        if source.count(f"(>= (obj-size obj) {value})") == 1
    ]
    if len(matches) != 1:
        raise ValueError("Racket source must contain exactly one allowed threshold site")
    value = matches[0]
    canonicalized = source.replace(
        f"(>= (obj-size obj) {value})", THRESHOLD_SITE, 1
    )
    _check_canonical_source(canonicalized)
    return canonicalized


def rule_callable(source: str) -> str:
    """Wrap a source-bound materialized rule for the bare Racket bridge."""
    _canonicalize_materialized_source(source)
    return wrap_rule(source)


def execute_rule(source: str, grid, *, bridge: RacketBridge | None = None):
    """Apply the actual Racket rule; this prototype has no Python answer mirror."""
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    expression = f"({rule_callable(source)} {literal})"
    if bridge is None:
        with RacketBridge() as owned:
            return normalize_grid(owned.eval_text(expression))
    return normalize_grid(bridge.eval_text(expression))


def _resolve_root(root=None) -> Path:
    return find_root(__file__) if root is None else Path(root).resolve()


@lru_cache(maxsize=4)
def _selected_generator(root_text: str):
    root = Path(root_text)
    module, source_path, digest = load_selected_generator(TASK_ID, root=root)
    if digest != BASE_GENERATOR_SHA256:
        raise ValueError(
            "selected generator SHA256 changed from the prototype's pinned source"
        )
    return module, source_path, digest


def _derived_coordinates(seed: int, index: int, attempt: int) -> tuple[int, int]:
    payload = f"{TASK_ID}:{VERSION}:input:{seed}:{index}:{attempt}".encode()
    digest = hashlib.sha256(payload).digest()
    input_seed = int.from_bytes(digest[:8], "big") % (2**63)
    sample_index = int.from_bytes(digest[8:16], "big") % (2**31)
    return input_seed, sample_index


def _sample_inputs(
    seed: int,
    count: int,
    *,
    difficulty: str,
    root: Path,
) -> list[dict[str, Any]]:
    module, _, _ = _selected_generator(str(root))
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index in range(count):
        for attempt in range(32):
            input_seed, sample_index = _derived_coordinates(seed, index, attempt)
            grid = module.generate(
                input_seed,
                sample_index,
                difficulty=difficulty,
                scene_profile=INPUT_PROFILE,
            )
            if module.self_check(grid):
                raise AssertionError("selected generator rejected its own parametric input")
            if module.observe_overrides(grid) != {"scene_profile": INPUT_PROFILE}:
                raise AssertionError("selected generator profile drifted")
            analysis = module._analysis(grid)
            sizes = sorted(obj["size"] for obj in analysis["facts"]["objects"])
            if sizes != [1, 2, 3, 4, 5, 6]:
                raise AssertionError(f"boundary profile lost sizes 1..6: {sizes}")
            digest = grid_sha256(grid)
            if digest in seen:
                continue
            seen.add(digest)
            result.append({
                "input": grid,
                "input_sha256": digest,
                "input_seed": input_seed,
                "sample_index": sample_index,
                "attempt": attempt,
                "object_sizes": sizes,
            })
            break
        else:
            raise RuntimeError(f"could not sample distinct input {index} after 32 attempts")
    return result


def parameters_for_seed(seed: int) -> dict[str, int]:
    """Choose exactly one setting per episode without touching global RNG state."""
    _validate_seed(seed)
    return {
        "minimum_fall_size": ALLOWED_MINIMUM_FALL_SIZES[
            seed % len(ALLOWED_MINIMUM_FALL_SIZES)
        ]
    }


def make_episode(
    seed: int,
    *,
    minimum_fall_size: int | None = None,
    demo_count: int = 3,
    query_count: int = 4,
    difficulty: str = "medium",
    root=None,
    bridge: RacketBridge | None = None,
) -> dict[str, Any]:
    """Build one complete fixed-setting episode with independently sized splits."""
    _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    _validate_difficulty(difficulty)
    selected = (
        parameters_for_seed(seed)["minimum_fall_size"]
        if minimum_fall_size is None
        else minimum_fall_size
    )
    _validate_minimum_fall_size(selected)
    resolved_root = _resolve_root(root)
    inputs = _sample_inputs(
        seed,
        demo_count + query_count,
        difficulty=difficulty,
        root=resolved_root,
    )
    if bridge is None:
        with RacketBridge() as owned:
            return _make_episode(
                seed,
                selected,
                demo_count,
                query_count,
                difficulty,
                inputs,
                root=resolved_root,
                bridge=owned,
            )
    return _make_episode(
        seed,
        selected,
        demo_count,
        query_count,
        difficulty,
        inputs,
        root=resolved_root,
        bridge=bridge,
    )


def _make_episode(
    seed: int,
    selected: int,
    demo_count: int,
    query_count: int,
    difficulty: str,
    inputs: list[dict[str, Any]],
    *,
    root: Path,
    bridge: RacketBridge,
) -> dict[str, Any]:
    canonical = canonical_source(root=root)
    rules = {
        value: materialize_rule(value, source=canonical)
        for value in ALLOWED_MINIMUM_FALL_SIZES
    }
    outputs = {
        value: [execute_rule(rule, row["input"], bridge=bridge) for row in inputs]
        for value, rule in rules.items()
    }
    for index in range(len(inputs)):
        hashes = {grid_sha256(outputs[value][index]) for value in ALLOWED_MINIMUM_FALL_SIZES}
        if len(hashes) != len(ALLOWED_MINIMUM_FALL_SIZES):
            raise AssertionError(
                f"pair {index} failed to distinguish all threshold settings"
            )

    pairs = []
    for row, output in zip(inputs, outputs[selected], strict=True):
        pairs.append({
            "input": copy.deepcopy(row["input"]),
            "output": output,
            "input_sha256": row["input_sha256"],
            "output_sha256": grid_sha256(output),
            "minimum_fall_size": selected,
            "input_provenance": {
                "input_seed": row["input_seed"],
                "sample_index": row["sample_index"],
                "attempt": row["attempt"],
                "scene_profile": INPUT_PROFILE,
                "object_sizes": row["object_sizes"],
            },
        })

    rival_rows = []
    ambiguities = []
    for value in ALLOWED_MINIMUM_FALL_SIZES:
        train_mismatches = [
            index for index in range(demo_count)
            if outputs[value][index] != outputs[selected][index]
        ]
        query_mismatches = [
            index for index in range(query_count)
            if outputs[value][demo_count + index] != outputs[selected][demo_count + index]
        ]
        status = (
            "refuted_by_demonstrations" if train_mismatches
            else "ambiguous_query" if query_mismatches
            else "matches_episode"
        )
        row = {
            "minimum_fall_size": value,
            "racket_sha256": _sha256(rules[value]),
            "status": status,
            "demonstration_mismatch_indices": train_mismatches,
            "query_mismatch_indices": query_mismatches,
            "train_output_sha256": [grid_sha256(grid) for grid in outputs[value][:demo_count]],
            "query_output_sha256": [grid_sha256(grid) for grid in outputs[value][demo_count:]],
        }
        rival_rows.append(row)
        if status == "ambiguous_query":
            ambiguities.append(row)

    source = rules[selected]
    return {
        "schema": "arcpuzzles-proposed-parametric-episode-v1",
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "status": "proposed_unapproved",
        "approved": False,
        "seed": seed,
        "difficulty": difficulty,
        "parameters": {"minimum_fall_size": selected},
        "parameter_selection": (
            "one seed-modulo-three selection before any pair unless explicitly overridden"
        ),
        "selection_scope": "once_per_episode",
        "allowed_minimum_fall_sizes": list(ALLOWED_MINIMUM_FALL_SIZES),
        "canonical_default": DEFAULT_MINIMUM_FALL_SIZE,
        "demo_count": demo_count,
        "query_count": query_count,
        "input_constraint": (
            "every input is the selected generator's mixed_sizes_1_to_6 profile; "
            "sizes 3 and 4 visibly distinguish thresholds 3, 4, and 5"
        ),
        "prototype_sha256": _sha256(Path(__file__).read_bytes()),
        "base_generator_sha256": BASE_GENERATOR_SHA256,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "racket_source": source,
        "racket_sha256": _sha256(source),
        "racket_callable_sha256": _sha256(rule_callable(source)),
        "racket_path": f"private/rules/minimum-fall-size-{selected}.rkt",
        "train": pairs[:demo_count],
        "test": pairs[demo_count:],
        "parameter_rivals": rival_rows,
        "ambiguities": ambiguities,
        "racket_evaluations": len(inputs) * len(ALLOWED_MINIMUM_FALL_SIZES),
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Explicit allowlist view: demos plus query inputs, never hidden answers."""
    return copy.deepcopy({
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["train"]
        ],
        "test": [{"input": pair["input"]} for pair in episode["test"]],
    })


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_evidence(
    seeds,
    *,
    out,
    root=None,
    demo_count: int = 3,
    query_count: int = 4,
    difficulty: str = "medium",
) -> dict[str, Any]:
    """Retain finite source-bound evidence in a new directory."""
    seeds = tuple(seeds)
    if not seeds or len(set(seeds)) != len(seeds):
        raise ValueError("provide at least one distinct episode seed")
    for seed in seeds:
        _validate_seed(seed)
    _validate_count("demo_count", demo_count)
    _validate_count("query_count", query_count)
    _validate_difficulty(difficulty)
    resolved_root = _resolve_root(root)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    try:
        return _write_evidence(
            seeds,
            out=out,
            root=resolved_root,
            demo_count=demo_count,
            query_count=query_count,
            difficulty=difficulty,
        )
    except Exception as exc:
        _write_json(out / "failure.json", {
            "status": "error",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "seeds": list(seeds),
        })
        raise


def _write_evidence(
    seeds: tuple[int, ...],
    *,
    out: Path,
    root: Path,
    demo_count: int,
    query_count: int,
    difficulty: str,
) -> dict[str, Any]:
    source_path = Path(__file__).resolve()
    task_dir = root / f"generators/{TASK_ID}"
    test_path = task_dir / "tests/test_parametric_minimum_fall_size.py"
    readme_path = task_dir / "workspace/parametric/README.md"
    snapshot = out / "private/source_snapshot"
    snapshot.mkdir(parents=True)
    sources = []
    for path in (source_path, test_path, readme_path):
        if path.is_file():
            target = snapshot / path.name
            target.write_bytes(path.read_bytes())
            sources.append({
                "path": str(path.relative_to(root)),
                "sha256": _sha256(path.read_bytes()),
                "snapshot": str(target.relative_to(out)),
            })

    runtime_files = []
    for name in (
        "reviewer_support.py",
        "puzzle_generators/rule_wrap.py",
        "arc_repl/racket_bridge.py",
        "arc_repl/racket_prelude/arc-prelude.rkt",
    ):
        path = root / "shared/runtime" / name
        runtime_files.append({
            "path": str(path.relative_to(root)),
            "sha256": _sha256(path.read_bytes()),
        })

    canonical = canonical_source(root=root)
    rule_dir = out / "private/rules"
    rule_dir.mkdir(parents=True)
    rule_rows = []
    for value in ALLOWED_MINIMUM_FALL_SIZES:
        source = materialize_rule(value, source=canonical)
        rule_path = rule_dir / f"minimum-fall-size-{value}.rkt"
        rule_path.write_text(source, encoding="utf-8")
        rule_rows.append({
            "minimum_fall_size": value,
            "path": str(rule_path.relative_to(out)),
            "sha256": _sha256(source),
            "callable_sha256": _sha256(rule_callable(source)),
        })

    canonical_rows = []
    episode_rows = []
    distinct_inputs: set[str] = set()
    public_ids: set[str] = set()
    with RacketBridge() as bridge:
        for pair in canonical_pairs(TASK_ID, root=root, labeled_only=True):
            actual = execute_rule(canonical, pair["input"], bridge=bridge)
            canonical_rows.append({
                **pair,
                "actual": actual,
                "matches": actual == pair["output"],
                "input_sha256": grid_sha256(pair["input"]),
                "output_sha256": grid_sha256(actual),
            })
        _write_json(out / "private/canonical-original-check.json", canonical_rows)
        if not canonical_rows or not all(row["matches"] for row in canonical_rows):
            raise AssertionError("default threshold did not reproduce every canonical label")

        witness_input = _sample_inputs(0, 1, difficulty=difficulty, root=root)[0]["input"]
        witness_outputs = {
            str(value): execute_rule(
                materialize_rule(value, source=canonical), witness_input, bridge=bridge
            )
            for value in ALLOWED_MINIMUM_FALL_SIZES
        }
        if len({_json(grid) for grid in witness_outputs.values()}) != 3:
            raise AssertionError("threshold settings failed to change the witness output")
        _write_json(out / "private/distinguishing-witness.json", {
            "input": witness_input,
            "input_sha256": grid_sha256(witness_input),
            "outputs_by_minimum_fall_size": witness_outputs,
            "rules": rule_rows,
        })

        for index, seed in enumerate(seeds):
            episode = make_episode(
                seed,
                demo_count=demo_count,
                query_count=query_count,
                difficulty=difficulty,
                root=root,
                bridge=bridge,
            )
            public = public_challenge(episode)
            visible_id = public_challenge_id(public)
            if visible_id in public_ids:
                raise AssertionError("distinct episode seeds produced the same public challenge")
            public_ids.add(visible_id)
            public_path = f"public/challenge-{visible_id}.json"
            private_path = f"private/episode-{index:03d}.json"
            (out / public_path).parent.mkdir(parents=True, exist_ok=True)
            (out / public_path).write_bytes(public_challenge_bytes(public))
            _write_json(out / private_path, episode)
            distinct_inputs.update(
                pair["input_sha256"] for pair in episode["train"] + episode["test"]
            )
            replay_inputs = _sample_inputs(
                seed,
                demo_count + query_count,
                difficulty=difficulty,
                root=root,
            )
            deterministic_inputs = [row["input_sha256"] for row in replay_inputs] == [
                pair["input_sha256"] for pair in episode["train"] + episode["test"]
            ]
            if not deterministic_inputs:
                raise AssertionError("same-seed input replay changed")
            episode_rows.append({
                "seed": seed,
                "parameters": episode["parameters"],
                "public_id": visible_id,
                "public_path": public_path,
                "private_path": private_path,
                "deterministic_input_replay": True,
                "episode_sha256": _sha256(_json(episode)),
                "parameter_rivals": [
                    {
                        key: row[key]
                        for key in (
                            "minimum_fall_size",
                            "status",
                            "demonstration_mismatch_indices",
                            "query_mismatch_indices",
                        )
                    }
                    for row in episode["parameter_rivals"]
                ],
            })

    episode_rows.sort(key=lambda row: row["public_id"])

    retained_files = [
        {
            "path": str(path.relative_to(out)),
            "sha256": _sha256(path.read_bytes()),
        }
        for path in sorted(out.rglob("*"))
        if path.is_file()
    ]
    report = {
        "schema": "arcpuzzles-proposed-parametric-evidence-v1",
        "status": "proposed_unapproved",
        "approved": False,
        "task_id": TASK_ID,
        "prototype_version": VERSION,
        "parameter": {
            "name": "minimum_fall_size",
            "allowed_values": list(ALLOWED_MINIMUM_FALL_SIZES),
            "original_default": DEFAULT_MINIMUM_FALL_SIZE,
            "selection_scope": "once_per_episode",
            "input_constraints_depend_on_parameter": False,
        },
        "input_scope": (
            "selected generator mixed_sizes_1_to_6 scenes; each input contains "
            "one object of every size 1 through 6"
        ),
        "sources": sources,
        "runtime_files": runtime_files,
        "runtime": racket_runtime_status(),
        "rules": rule_rows,
        "episodes": episode_rows,
        "files": retained_files,
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "canonical_source_sha256": CANONICAL_SHA256,
        "base_generator_sha256": BASE_GENERATOR_SHA256,
        "counts": {
            "episodes": len(seeds),
            "train_pairs": demo_count * len(seeds),
            "query_pairs": query_count * len(seeds),
            "distinct_input_grids": len(distinct_inputs),
            "settings_exercised": len({
                row["parameters"]["minimum_fall_size"] for row in episode_rows
            }),
            "canonical_pairs_checked": len(canonical_rows),
            "parameter_rival_episode_checks": (
                len(ALLOWED_MINIMUM_FALL_SIZES) * len(seeds)
            ),
            "ambiguous_parameter_rivals": sum(
                row["status"] == "ambiguous_query"
                for episode in episode_rows
                for row in episode["parameter_rivals"]
            ),
        },
        "limitations": [
            "Proposed task-local prototype only; no production, variant, or training approval.",
            "Evidence covers the listed seeds and thresholds 3, 4, and 5, not every possible threshold or seed.",
            "Inputs intentionally contain sizes 1 through 6; this is a teaching distribution, not a replacement for the canonical distribution.",
            "Rival checks cover only the declared threshold family, not every conceivable gravity rule.",
            "Public challenge names are hashes of visible demonstrations and query inputs; private settings and query answers do not affect them.",
        ],
        "process_argv": list(sys.argv),
        "effective_cwd": str(Path.cwd()),
    }
    _write_json(out / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", nargs="+", type=int, default=[0, 1, 2])
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--demo-count", type=int, default=3)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    args = parser.parse_args(argv)
    report = write_evidence(
        args.seeds,
        out=args.out,
        demo_count=args.demo_count,
        query_count=args.query_count,
        difficulty=args.difficulty,
    )
    print(json.dumps({
        "status": report["status"],
        "counts": report["counts"],
        "report": str(args.out / "report.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
