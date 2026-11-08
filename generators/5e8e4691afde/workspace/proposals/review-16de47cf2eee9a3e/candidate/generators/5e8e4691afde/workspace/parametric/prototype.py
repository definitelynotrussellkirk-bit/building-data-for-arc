#!/usr/bin/env python3
"""Racket-backed episode-level diagonal-mode prototype for 5e8e4691afde.

The selected production generator and canonical authority remain unchanged by
this module.  It varies one episode-fixed output-rule parameter: draw both full
diagonals through the relocated frame center (canonical/default), only the
falling ``\\`` diagonal, or only the rising ``/`` diagonal.  Input generation,
path-vector relocation, frame geometry, fill color, and center preservation are
identical across settings.  Every retained label and declared-rival prediction
is executed by the exact materialized Racket program.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
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

TASK_ID = "5e8e4691afde"
PROTOTYPE_VERSION = "1.0.0"
ALLOWED_DIAGONAL_MODES = ("both", "falling", "rising")
DEFAULT_DIAGONAL_MODE = "both"
PARAMETERS = {
    "diagonal_mode": {
        "allowed": ALLOWED_DIAGONAL_MODES,
        "default": DEFAULT_DIAGONAL_MODE,
        "meaning": (
            "Which complete diagonal families are drawn through the relocated "
            "frame center: both, falling (\\), or rising (/)."
        ),
        "input_constraint": (
            "The canonical framed-center and path-vector input contract is unchanged; "
            "retained inputs must make all three outputs pairwise distinct."
        ),
    }
}
ROOT = find_root(__file__)
HERE = Path(__file__).resolve().parent
_DIAGONAL_MARKER = "(or (= (- r c) (- nr nc)) (= (+ r c) (+ nr nc)))"
_MODE_PREDICATES = {
    "falling": "(= (- r c) (- nr nc))",
    "rising": "(= (+ r c) (+ nr nc))",
}
_INPUT_PROFILES = (
    "straight_down",
    "straight_left",
    "diagonal_down_right",
    "diagonal_up_left",
    "long_down_right",
    "long_up_right",
    "straight_right",
    "diagonal_down_left",
    "long_down_left",
    "straight_up",
    "diagonal_up_right",
)
_DIFFICULTIES = ("easy", "medium", "hard")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def _grid_sha256(grid: list[list[int]]) -> str:
    payload = json.dumps(grid, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256_bytes(payload)


def _validate_mode(diagonal_mode: str) -> str:
    if type(diagonal_mode) is not str:
        raise TypeError("diagonal_mode must be a string")
    if diagonal_mode not in ALLOWED_DIAGONAL_MODES:
        raise ValueError(
            f"diagonal_mode must be one of {ALLOWED_DIAGONAL_MODES}, got {diagonal_mode!r}"
        )
    return diagonal_mode


def _validate_seed(seed: int) -> int:
    if type(seed) is not int:
        raise TypeError("seed must be an integer (not bool)")
    return seed


def _validate_count(name: str, value: int) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} count must be an integer (not bool)")
    if not 1 <= value <= 16:
        raise ValueError(f"{name} count must be in 1..16")
    return value


def choose_diagonal_mode(seed: int) -> str:
    """Choose one deterministic hidden setting for a complete episode."""
    _validate_seed(seed)
    digest = hashlib.sha256(f"{TASK_ID}|diagonal_mode|{seed}".encode()).digest()
    return ALLOWED_DIAGONAL_MODES[digest[0] % len(ALLOWED_DIAGONAL_MODES)]


@lru_cache(maxsize=1)
def _canonical_program() -> str:
    programs: list[str] = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and row.get("program_solution"):
                programs.append(str(row["program_solution"]))
    unique = list(dict.fromkeys(programs))
    if len(unique) != 1:
        raise RuntimeError(
            f"expected one exact canonical program for {TASK_ID}, found {len(unique)}"
        )
    return unique[0]


def racket_program(diagonal_mode: str = DEFAULT_DIAGONAL_MODE) -> str:
    """Materialize the exact Racket program for one bounded setting."""
    mode = _validate_mode(diagonal_mode)
    canonical = _canonical_program()
    if canonical.count(_DIAGONAL_MARKER) != 1:
        raise RuntimeError(
            "canonical diagonal predicate changed; manually reassess this prototype"
        )
    if mode == DEFAULT_DIAGONAL_MODE:
        return canonical
    changed = canonical.replace(_DIAGONAL_MARKER, _MODE_PREDICATES[mode])
    if changed == canonical or changed.count(_MODE_PREDICATES[mode]) < 1:
        raise RuntimeError("diagonal-mode program materialization failed")
    return changed


def racket_sha256(diagonal_mode: str) -> str:
    return _sha256_text(racket_program(diagonal_mode))


def _racket_literal(value: Any) -> str:
    if isinstance(value, (list, tuple)):
        return "(" + " ".join(_racket_literal(item) for item in value) + ")"
    if type(value) is int:
        return str(value)
    raise TypeError(f"cannot encode Racket literal: {value!r}")


def run_racket(
    bridge: RacketBridge,
    diagonal_mode: str,
    grid: list[list[int]],
) -> list[list[int]]:
    """Execute one grid through the exact instantiated Racket authority."""
    if not isinstance(bridge, RacketBridge):
        raise TypeError("bridge must be a live RacketBridge")
    mode = _validate_mode(diagonal_mode)
    normalized = normalize_grid(grid)
    callable_source = strip_rule_wrapper(racket_program(mode))
    literal = "'" + _racket_literal(normalized)
    result = bridge.eval_text(f"({callable_source} {literal})")
    return normalize_grid(result)


@lru_cache(maxsize=1)
def _generator():
    module, source_path, source_sha256 = load_selected_generator(TASK_ID, root=ROOT)
    return module, source_path, source_sha256


def _python_output(grid: list[list[int]], diagonal_mode: str) -> list[list[int]]:
    """Sampling guard only; retained labels still come from Racket."""
    mode = _validate_mode(diagonal_mode)
    module, _, _ = _generator()
    info = module._analysis(grid)
    if info["errors"]:
        raise ValueError("; ".join(info["errors"]))
    height, width = info["height"], info["width"]
    color = info["color"]
    nr, nc = info["new_center"]
    output: list[list[int]] = []
    for row in range(height):
        values: list[int] = []
        for column in range(width):
            if (row, column) == (nr, nc):
                value = color
            elif abs(row - nr) <= 1 and abs(column - nc) <= 1:
                value = 4
            elif mode in ("both", "falling") and row - column == nr - nc:
                value = 4
            elif mode in ("both", "rising") and row + column == nr + nc:
                value = 4
            else:
                value = color
            values.append(value)
        output.append(values)
    return output


def _production_seed(seed: int) -> int:
    digest = hashlib.sha256(f"{TASK_ID}|parametric-inputs|{seed}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _episode_inputs(seed: int, count: int) -> list[list[list[int]]]:
    """Select distinct production-lawful inputs that separate all three modes."""
    _validate_seed(seed)
    count = _validate_count("total", count)
    module, _, _ = _generator()
    production_seed = _production_seed(seed)
    start = int.from_bytes(
        hashlib.sha256(f"{TASK_ID}|start|{seed}".encode()).digest()[:4], "big"
    )
    selected: list[list[list[int]]] = []
    seen: set[tuple[tuple[int, ...], ...]] = set()
    for offset in range(4096):
        profile = _INPUT_PROFILES[offset % len(_INPUT_PROFILES)]
        difficulty = _DIFFICULTIES[offset % len(_DIFFICULTIES)]
        grid = module.generate(
            production_seed,
            start + offset,
            difficulty=difficulty,
            scene_profile=profile,
        )
        key = tuple(map(tuple, grid))
        if key in seen or module.self_check(grid):
            continue
        outputs = [_python_output(grid, mode) for mode in ALLOWED_DIAGONAL_MODES]
        if len({_grid_sha256(output) for output in outputs}) != len(ALLOWED_DIAGONAL_MODES):
            continue
        selected.append(deepcopy(grid))
        seen.add(key)
        if len(selected) == count:
            return selected
    raise RuntimeError(f"found only {len(selected)} distinguishing inputs; needed {count}")


def build_episode(
    bridge: RacketBridge,
    seed: int,
    *,
    diagonal_mode: str | None = None,
    demo_count: int = 2,
    query_count: int = 4,
) -> dict[str, Any]:
    """Build one private fully labeled episode with one fixed rule setting."""
    seed = _validate_seed(seed)
    demos = _validate_count("demo", demo_count)
    queries = _validate_count("query", query_count)
    if demos + queries > 16:
        raise ValueError("demo count + query count must not exceed 16")
    mode = choose_diagonal_mode(seed) if diagonal_mode is None else _validate_mode(diagonal_mode)
    inputs = _episode_inputs(seed, demos + queries)
    outputs = {
        candidate: [run_racket(bridge, candidate, grid) for grid in inputs]
        for candidate in ALLOWED_DIAGONAL_MODES
    }
    selected = outputs[mode]
    train = [
        {"input": deepcopy(inputs[index]), "output": deepcopy(selected[index])}
        for index in range(demos)
    ]
    test = [
        {
            "input": deepcopy(inputs[demos + index]),
            "output": deepcopy(selected[demos + index]),
        }
        for index in range(queries)
    ]

    rivals: dict[str, Any] = {}
    for rival_mode in ALLOWED_DIAGONAL_MODES:
        if rival_mode == mode:
            continue
        rival_outputs = outputs[rival_mode]
        refuting = [
            index
            for index in range(demos)
            if selected[index] != rival_outputs[index]
        ]
        query_differences = [
            selected[demos + index] != rival_outputs[demos + index]
            for index in range(queries)
        ]
        distinguished = bool(refuting) and all(query_differences)
        rivals[rival_mode] = {
            "diagonal_mode": rival_mode,
            "racket_sha256": racket_sha256(rival_mode),
            "refuting_demonstration_indices": refuting,
            "query_differences": query_differences,
            "train_output_sha256": [
                _grid_sha256(rival_outputs[index]) for index in range(demos)
            ],
            "test_output_sha256": [
                _grid_sha256(rival_outputs[demos + index]) for index in range(queries)
            ],
            "status": "distinguished" if distinguished else "ambiguous",
        }

    all_inputs_distinct = len({tuple(map(tuple, grid)) for grid in inputs}) == len(inputs)
    demos_distinguish = all(
        row["refuting_demonstration_indices"] for row in rivals.values()
    )
    queries_differ = all(
        all(row["query_differences"]) for row in rivals.values()
    )
    query_checks = []
    for index in range(queries):
        differing = [
            rival_mode
            for rival_mode, row in rivals.items()
            if row["query_differences"][index]
        ]
        query_checks.append(
            {
                "query_index": index,
                "input_sha256": _grid_sha256(inputs[demos + index]),
                "output_sha256": _grid_sha256(selected[demos + index]),
                "differing_rivals": differing,
                "all_declared_rivals_refuted_by_demonstrations": demos_distinguish,
            }
        )
    no_ambiguity = all_inputs_distinct and demos_distinguish and queries_differ
    return {
        "schema": "arcpuzzles-parametric-diagonal-mode-private-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "parameter": {"diagonal_mode": mode},
        "parameter_draw_count": 1,
        "parameter_selection": (
            "deterministic_seed_draw" if diagonal_mode is None else "explicit_setting_coverage"
        ),
        "demo_count": demos,
        "query_count": queries,
        "racket_sha256": racket_sha256(mode),
        "train": train,
        "test": test,
        "rivals": rivals,
        "analysis": {
            "all_inputs_distinct": all_inputs_distinct,
            "demonstrations_distinguish_all_rivals": demos_distinguish,
            "every_query_differs_from_all_rivals": queries_differ,
            "queries": query_checks,
            "status": "no_ambiguity_found" if no_ambiguity else "ambiguity_found",
        },
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Project a private episode to visible demonstrations and query inputs."""
    return {
        "train": [
            {"input": deepcopy(pair["input"]), "output": deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [
            {"input": deepcopy(pair["input"])}
            for pair in episode["test"]
        ],
    }


def public_identifier(episode: dict[str, Any]) -> str:
    """Hash exactly the visible bytes; hidden metadata and query labels are absent."""
    return public_challenge_id(public_challenge(episode))


def _canonical_default_check(bridge: RacketBridge) -> dict[str, Any]:
    rows = canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)
    results = []
    for row in rows:
        actual = run_racket(bridge, DEFAULT_DIAGONAL_MODE, row["input"])
        passed = actual == row["output"]
        results.append(
            {
                "variant": row["variant"],
                "split": row["split"],
                "pair_index": row["pair_index"],
                "input_sha256": _grid_sha256(row["input"]),
                "expected_output_sha256": _grid_sha256(row["output"]),
                "actual_output_sha256": _grid_sha256(actual),
                "passed": passed,
            }
        )
    passed = sum(1 for row in results if row["passed"])
    return {
        "checked": len(results),
        "passed": passed,
        "all_passed": passed == len(results),
        "pairs": results,
    }


def _distinguishing_witness(
    bridge: RacketBridge,
    grid: list[list[int]],
) -> dict[str, Any]:
    outputs = {
        mode: run_racket(bridge, mode, grid)
        for mode in ALLOWED_DIAGONAL_MODES
    }
    hashes = {mode: _grid_sha256(output) for mode, output in outputs.items()}
    return {
        "input": deepcopy(grid),
        "input_sha256": _grid_sha256(grid),
        "outputs": outputs,
        "output_sha256": hashes,
        "all_outputs_pairwise_distinct": len(set(hashes.values())) == len(hashes),
    }


def build_evidence(
    bridge: RacketBridge,
    *,
    seed: int = 20261023,
    demo_count: int = 2,
    query_count: int = 4,
) -> dict[str, Any]:
    """Execute all settings and return source-bound private evidence."""
    seed = _validate_seed(seed)
    demos = _validate_count("demo", demo_count)
    queries = _validate_count("query", query_count)
    if demos + queries > 16:
        raise ValueError("demo count + query count must not exceed 16")
    module, source_path, source_sha256 = _generator()
    settings: dict[str, Any] = {}
    for mode in ALLOWED_DIAGONAL_MODES:
        episode = build_episode(
            bridge,
            seed,
            diagonal_mode=mode,
            demo_count=demos,
            query_count=queries,
        )
        public = public_challenge(episode)
        identifier = public_challenge_id(public)
        settings[mode] = {
            "racket_text": racket_program(mode),
            "racket_sha256": racket_sha256(mode),
            "episode": episode,
            "public_id": identifier,
            "public_bytes_sha256": _sha256_bytes(public_challenge_bytes(public)),
        }

    witness_input = settings[DEFAULT_DIAGONAL_MODE]["episode"]["train"][0]["input"]
    test_path = ROOT / f"generators/{TASK_ID}/tests/test_parametric_diagonal_mode.py"
    source_rel = source_path.resolve().relative_to(ROOT).as_posix()
    return {
        "schema": "arcpuzzles-parametric-diagonal-mode-evidence-v1",
        "status": "prototype",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "request": {"demo_count": demos, "query_count": queries},
        "parameter": {
            "name": "diagonal_mode",
            "allowed_values": list(ALLOWED_DIAGONAL_MODES),
            "default": DEFAULT_DIAGONAL_MODE,
            "dependent_input_constraints": [
                "the path vector keeps the relocated 3x3 frame inside the canvas",
                "the canvas extends beyond the frame on both diagonal families",
            ],
        },
        "source": {
            "generator_path": source_rel,
            "generator_sha256": source_sha256,
            "generator_version": module.VERSION,
            "prototype_path": HERE.relative_to(ROOT).joinpath("prototype.py").as_posix(),
            "prototype_sha256": _sha256_bytes(Path(__file__).read_bytes()),
            "test_path": test_path.relative_to(ROOT).as_posix(),
            "test_sha256": _sha256_bytes(test_path.read_bytes()),
        },
        "canonical_default": _canonical_default_check(bridge),
        "distinguishing_witness": _distinguishing_witness(bridge, witness_input),
        "settings": settings,
        "all_labels_and_rivals_executed_in_racket": True,
        "limits": [
            "bounded three-setting prototype; not selected production behavior",
            "identifiability is checked only against the two declared diagonal-mode rivals",
            "finite retained episodes do not establish unique induction against every program",
            "no training admission or generator approval follows from this evidence",
        ],
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def materialize(out: Path, evidence: dict[str, Any]) -> dict[str, Any]:
    """Write private evidence and exact visible-byte public challenges."""
    out = Path(out).resolve()
    if out.exists() and any(out.iterdir()):
        raise FileExistsError(f"output directory is not empty: {out}")
    out.mkdir(parents=True, exist_ok=True)

    records = []
    for mode, record in evidence["settings"].items():
        episode = record["episode"]
        identifier = public_identifier(episode)
        if identifier != record["public_id"]:
            raise ValueError(f"stale public identifier for {mode}")
        records.append((identifier, mode, record))
    records.sort(key=lambda row: row[0])
    identifiers = [row[0] for row in records]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate visible public challenge identifiers")

    for mode in ALLOWED_DIAGONAL_MODES:
        rule_path = out / "private" / "rules" / f"{mode}.rkt"
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.write_text(racket_program(mode), encoding="utf-8")

    setting_rows = []
    for identifier, mode, record in records:
        episode = record["episode"]
        challenge = public_challenge(episode)
        body = public_challenge_bytes(challenge)
        if _sha256_bytes(body) != identifier:
            raise ValueError("public bytes do not match their identifier")
        public_path = out / "public" / f"{identifier}.json"
        public_path.parent.mkdir(parents=True, exist_ok=True)
        public_path.write_bytes(body)
        _write_json(out / "private" / "episodes" / f"{identifier}.json", episode)
        setting_rows.append(
            {
                "public_id": identifier,
                "diagonal_mode": mode,
                "seed": episode["seed"],
                "demo_count": episode["demo_count"],
                "query_count": episode["query_count"],
                "racket_sha256": record["racket_sha256"],
                "private_episode": f"private/episodes/{identifier}.json",
                "public_challenge": f"public/{identifier}.json",
            }
        )

    _write_json(
        out / "private" / "setting-map.json",
        {
            "schema": "arcpuzzles-parametric-diagonal-mode-setting-map-v1",
            "task_id": TASK_ID,
            "episodes": setting_rows,
        },
    )
    _write_json(out / "private" / "distinguishing-witness.json", evidence["distinguishing_witness"])
    _write_json(out / "report.json", evidence)

    manifest = {
        "schema": "arcpuzzles-parametric-diagonal-mode-manifest-v1",
        "task_id": TASK_ID,
        "files": [],
    }
    for path in sorted(
        item for item in out.rglob("*") if item.is_file() and item.name != "manifest.json"
    ):
        manifest["files"].append(
            {
                "path": path.relative_to(out).as_posix(),
                "sha256": _sha256_bytes(path.read_bytes()),
                "bytes": path.stat().st_size,
            }
        )
    _write_json(out / "manifest.json", manifest)
    return {
        "status": evidence["status"],
        "out": str(out),
        "public_file_count": len(records),
        "private_episode_count": len(records),
        "demo_count": evidence["request"]["demo_count"],
        "query_count": evidence["request"]["query_count"],
        "canonical_pairs_passed": evidence["canonical_default"]["passed"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=20261023)
    parser.add_argument("--demo-count", type=int, default=2)
    parser.add_argument("--query-count", type=int, default=4)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with RacketBridge(timeout=30, startup_timeout=60, max_calls_before_restart=96) as bridge:
        evidence = build_evidence(
            bridge,
            seed=args.seed,
            demo_count=args.demo_count,
            query_count=args.query_count,
        )
    summary = materialize(args.out, evidence)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
