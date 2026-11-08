"""Proposed episode-level shape-equivalence extension for ``ae0a295c2271``.

This prototype does not modify production generation or canonical authority.
It binds one rule setting for a complete episode:

``shape_equivalence = exact`` (canonical/default)
    Compare translation-normalized object shapes only.

``shape_equivalence = d4`` (proposed alternative)
    Compare shapes modulo rotation and reflection.

Every saved label is produced by the included Racket runtime.  The Python
mirror is an independent parity check, never the label authority.
"""
from __future__ import annotations

import argparse
from contextlib import nullcontext
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_rule_wrapper
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)

TASK_ID = "ae0a295c2271"
PARAMETER_NAME = "shape_equivalence"
ALLOWED_VALUES = ("exact", "d4")
DEFAULT_VALUE = "exact"
PROTOTYPE_SEEDS = {"exact": 1701, "d4": 1702}
SCHEMA = "ae0a295c2271-shape-equivalence-prototype-v1"

_EXACT_SITE = "(same-shape? o other)"
_D4_SITE = "(match-transform (obj-cells o) (obj-cells other))"
_SAMPLE_INDICES = (1, 5, 9, 13)  # all canonical_two_pairs_d4; parity alternates
_BANDS = ("easy", "medium", "hard", "medium")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


@lru_cache(maxsize=8)
def canonical_program(*, root: Path | str | None = None) -> str:
    """Load the selected canonical Racket program exactly."""
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    found: list[str] = []
    with canonical_path(root_path).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                found.append(row["program_solution"])
    unique = list(dict.fromkeys(found))
    if len(unique) != 1:
        raise ValueError(f"expected one canonical program for {TASK_ID}; found {len(unique)}")
    return unique[0]


def _validate_setting(value: Any) -> str:
    if type(value) is not str or value not in ALLOWED_VALUES:
        raise ValueError(
            "shape_equivalence must be exactly 'exact' or 'd4' as a Python str"
        )
    return value


def program_for(
    shape_equivalence: str = DEFAULT_VALUE,
    *,
    root: Path | str | None = None,
) -> str:
    """Materialize one exact Racket program without changing the default text."""
    setting = _validate_setting(shape_equivalence)
    source = canonical_program(root=root)
    if setting == DEFAULT_VALUE:
        return source
    if source.count(_EXACT_SITE) != 1:
        raise ValueError(
            "canonical comparison site changed; manually reassess the prototype"
        )
    changed = source.replace(_EXACT_SITE, _D4_SITE, 1)
    if changed == source:
        raise ValueError("d4 setting did not change the executed authority")
    return changed


def _racket_datum(grid: list[list[int]]) -> str:
    return "(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


def evaluate(bridge: RacketBridge, program: str, grid: Any) -> list[list[int]]:
    """Execute one grid through the supplied Racket bridge."""
    normalized = normalize_grid(grid)
    wrapper_start = program.find("(rule!")
    if wrapper_start < 0:
        raise ValueError("program does not contain a rule! wrapper")
    function = strip_rule_wrapper(program[wrapper_start:])
    if not function.startswith("(lambda (g)"):
        raise ValueError("expected the selected task's native Racket lambda")
    value = bridge.eval_text(f"({function} '{_racket_datum(normalized)})")
    return normalize_grid(value)


def choose_setting(seed: Any) -> str:
    """Choose one hidden setting once per episode."""
    if type(seed) is not int:
        raise ValueError("seed must be a Python int")
    return ALLOWED_VALUES[seed % len(ALLOWED_VALUES)]


def generate_inputs(
    seed: Any,
    *,
    root: Path | str | None = None,
) -> list[list[list[int]]]:
    """Generate four deterministic D4-discriminating task inputs."""
    choose_setting(seed)  # validates exact scalar type
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    generator, _, _ = load_selected_generator(TASK_ID, root=root_path)
    inputs: list[list[list[int]]] = []
    for offset, (sample_index, band) in enumerate(zip(_SAMPLE_INDICES, _BANDS)):
        grid = generator.generate(
            700_001 + seed * 101 + offset,
            sample_index,
            difficulty=band,
        )
        errors = generator.self_check(grid, difficulty=band)
        if errors:
            raise RuntimeError(
                f"invalid prototype input at offset {offset}: {'; '.join(errors)}"
            )
        if generator.schedule_profile(0, sample_index, band) != "canonical_two_pairs_d4":
            raise RuntimeError("prototype input schedule no longer selects the D4 witness")
        inputs.append(normalize_grid(grid))
    fingerprints = {json.dumps(grid, separators=(",", ":")) for grid in inputs}
    if len(fingerprints) != len(inputs):
        raise RuntimeError("prototype sampler produced duplicate inputs")
    return inputs


def _components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    components: list[list[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        stack = [start]
        unseen.remove(start)
        cells: list[tuple[int, int]] = []
        while stack:
            r, c = stack.pop()
            cells.append((r, c))
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if (nr, nc) in unseen and grid[nr][nc] == color:
                    unseen.remove((nr, nc))
                    stack.append((nr, nc))
        components.append(sorted(cells))
    return components


def _normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    r0 = min(r for r, _ in points)
    c0 = min(c for _, c in points)
    return tuple(sorted((r - r0, c - c0) for r, c in points))


def _d4_key(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    base = _normalize(cells)
    variants: list[tuple[tuple[int, int], ...]] = []
    for reflected in (False, True):
        transformed = tuple((r, -c if reflected else c) for r, c in base)
        for turns in range(4):
            rotated = transformed
            for _ in range(turns):
                rotated = tuple((c, -r) for r, c in rotated)
            variants.append(_normalize(rotated))
    return min(variants)


def python_apply(
    grid: Any,
    shape_equivalence: str,
    *,
    root: Path | str | None = None,
) -> list[list[int]]:
    """Independent Python parity oracle for the two bounded settings."""
    del root
    setting = _validate_setting(shape_equivalence)
    normalized = normalize_grid(grid)
    components = _components(normalized)
    key_fn = _normalize if setting == "exact" else _d4_key
    keys = [key_fn(component) for component in components]
    counts = {key: keys.count(key) for key in set(keys)}
    output = deepcopy(normalized)
    for component, key in zip(components, keys):
        color = 2 if counts[key] == 1 else 1
        for r, c in component:
            output[r][c] = color
    return output


def make_episode(
    bridge: RacketBridge,
    seed: Any,
    *,
    shape_equivalence: str | None = None,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Bind one setting once, then Racket-label all four episode examples."""
    chosen = choose_setting(seed) if shape_equivalence is None else _validate_setting(shape_equivalence)
    program = program_for(chosen, root=root)
    inputs = generate_inputs(seed, root=root)
    pairs = [
        {"input": grid, "output": evaluate(bridge, program, grid)}
        for grid in inputs
    ]
    return {
        "schema": SCHEMA,
        "task_id": TASK_ID,
        "prototype": True,
        "seed": seed,
        "parameters": {PARAMETER_NAME: chosen},
        "parameter_choice": "seed_modulo_two" if shape_equivalence is None else "explicit",
        "program": program,
        "program_sha256": sha256_text(program),
        "label_authority": "executed_racket",
        "pairs": pairs,
    }


def public_challenge(episode: dict[str, Any]) -> dict[str, Any]:
    """Hide parameter, source program, and query output from the public view."""
    pairs = episode["pairs"]
    return {
        "train": deepcopy(pairs[:3]),
        "test": [{"input": deepcopy(pairs[3]["input"])}],
    }


def _assessment_row(
    actual_pairs: list[dict[str, Any]],
    rival_outputs: list[list[list[int]]],
    query_index: int,
) -> dict[str, Any]:
    demonstration_indices = [i for i in range(len(actual_pairs)) if i != query_index]
    refuting = [
        i
        for i in demonstration_indices
        if rival_outputs[i] != actual_pairs[i]["output"]
    ]
    rival_query_differs = rival_outputs[query_index] != actual_pairs[query_index]["output"]
    return {
        "query_index": query_index,
        "demonstration_indices": demonstration_indices,
        "refuting_demonstration_indices": refuting,
        "rival_fits_demonstrations": not refuting,
        "rival_query_differs": rival_query_differs,
        "status": (
            "refuted_by_demonstrations"
            if refuting
            else "ambiguous"
            if rival_query_differs
            else "same_behavior"
        ),
    }


def assess_episode(
    bridge: RacketBridge,
    episode: dict[str, Any],
    *,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Check the other parameter setting against production and all rotations."""
    actual = _validate_setting(episode["parameters"][PARAMETER_NAME])
    rival = next(value for value in ALLOWED_VALUES if value != actual)
    pairs = episode["pairs"]
    rival_program = program_for(rival, root=root)
    rival_outputs = [
        evaluate(bridge, rival_program, pair["input"])
        for pair in pairs
    ]
    production = _assessment_row(pairs, rival_outputs, len(pairs) - 1)
    rotations = [
        _assessment_row(pairs, rival_outputs, query_index)
        for query_index in range(len(pairs))
    ]
    return {
        "actual_setting": actual,
        "rival_setting": rival,
        "production": production,
        "rotations": rotations,
    }


def materialize(
    out_dir: Path | str,
    *,
    bridge: RacketBridge | None = None,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Write exact rules, private episodes, public challenges, and a receipt."""
    out = Path(out_dir)
    if out.exists():
        raise FileExistsError(out)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    out.mkdir(parents=True)
    (out / "rules").mkdir()
    (out / "private").mkdir()
    (out / "public").mkdir()

    context = nullcontext(bridge) if bridge is not None else RacketBridge(max_calls_before_restart=128)
    with context as active_bridge:
        if active_bridge is None:
            raise RuntimeError("Racket bridge was not created")
        canonical = canonical_pairs(TASK_ID, root=root_path, labeled_only=True)
        exact_program = program_for("exact", root=root_path)
        canonical_passed = sum(
            evaluate(active_bridge, exact_program, pair["input"]) == pair["output"]
            for pair in canonical
        )
        if canonical_passed != len(canonical):
            raise AssertionError("canonical default failed a retained label")

        settings: list[dict[str, Any]] = []
        production_ambiguities = 0
        rotation_ambiguities = 0
        for setting in ALLOWED_VALUES:
            program = program_for(setting, root=root_path)
            episode = make_episode(
                active_bridge,
                PROTOTYPE_SEEDS[setting],
                shape_equivalence=setting,
                root=root_path,
            )
            analysis = assess_episode(active_bridge, episode, root=root_path)
            if analysis["production"]["status"] != "refuted_by_demonstrations":
                production_ambiguities += 1
            rotation_ambiguities += sum(
                row["status"] != "refuted_by_demonstrations"
                for row in analysis["rotations"]
            )
            private_value = {**episode, "parameter_rival_assessment": analysis}
            public_value = public_challenge(episode)

            rule_rel = Path("rules") / f"shape-equivalence-{setting}.rkt"
            private_rel = Path("private") / f"episode-{setting}.json"
            public_rel = Path("public") / f"challenge-{setting}.json"
            rule_bytes = (program + "\n").encode("utf-8")
            private_bytes = _json_bytes(private_value)
            public_bytes = _json_bytes(public_value)
            (out / rule_rel).write_bytes(rule_bytes)
            (out / private_rel).write_bytes(private_bytes)
            (out / public_rel).write_bytes(public_bytes)
            settings.append(
                {
                    "setting": setting,
                    "seed": PROTOTYPE_SEEDS[setting],
                    "rule_path": rule_rel.as_posix(),
                    "rule_sha256": sha256_bytes(rule_bytes),
                    "program_sha256_without_trailing_newline": sha256_text(program),
                    "private_path": private_rel.as_posix(),
                    "private_sha256": sha256_bytes(private_bytes),
                    "public_path": public_rel.as_posix(),
                    "public_sha256": sha256_bytes(public_bytes),
                    "production_status": analysis["production"]["status"],
                    "rotation_statuses": [row["status"] for row in analysis["rotations"]],
                    "demo_cell_disagreements_vs_rival": [
                        sum(
                            a != b
                            for row_a, row_b in zip(
                                pair["output"],
                                evaluate(
                                    active_bridge,
                                    program_for(
                                        next(v for v in ALLOWED_VALUES if v != setting),
                                        root=root_path,
                                    ),
                                    pair["input"],
                                ),
                            )
                            for a, b in zip(row_a, row_b)
                        )
                        for pair in episode["pairs"][:3]
                    ],
                }
            )

    report = {
        "schema": SCHEMA,
        "status": "proposed_prototype",
        "production_integration": False,
        "task_id": TASK_ID,
        "parameter": {
            "name": PARAMETER_NAME,
            "allowed_values": list(ALLOWED_VALUES),
            "default": DEFAULT_VALUE,
            "chosen_once_per_episode": True,
            "input_constraints": [
                "four 10x10 lawful inputs from canonical_two_pairs_d4",
                "two exact repeated classes and two exact singleton classes",
                "all four exact classes share one D4 orbit",
                "three demonstrations each distinguish exact from D4 equivalence",
            ],
        },
        "prototype_source": Path(__file__).resolve().relative_to(root_path).as_posix(),
        "prototype_source_sha256": sha256_bytes(Path(__file__).read_bytes()),
        "settings": settings,
        "counts": {
            "canonical_labels_checked": len(canonical),
            "canonical_labels_passed": canonical_passed,
            "settings": len(ALLOWED_VALUES),
            "episodes": len(ALLOWED_VALUES),
            "episode_labels": 4 * len(ALLOWED_VALUES),
            "production_ambiguities": production_ambiguities,
            "rotation_ambiguities": rotation_ambiguities,
            "query_rotations": 4 * len(ALLOWED_VALUES),
        },
        "limitations": [
            "prototype only; not wired into the selected generator or catalog",
            "bounded evidence covers two fixed episodes and focused tests, not all seeds",
            "inputs intentionally use one D4-orbit witness family",
            "the exact setting remains the only canonical and approved authority",
        ],
    }
    (out / "evidence.json").write_bytes(_json_bytes(report))
    return report


def verify_tree(
    out_dir: Path | str,
    *,
    bridge: RacketBridge | None = None,
    root: Path | str | None = None,
) -> dict[str, Any]:
    """Rehash and re-execute an existing materialized prototype tree."""
    out = Path(out_dir)
    root_path = find_root(__file__) if root is None else Path(root).resolve()
    failures: list[str] = []
    try:
        report = json.loads((out / "evidence.json").read_text(encoding="utf-8"))
    except Exception as exc:  # malformed evidence must become an explicit failure
        return {"status": "fail", "failures": [f"evidence read failed: {exc}"]}

    context = nullcontext(bridge) if bridge is not None else RacketBridge(max_calls_before_restart=128)
    with context as active_bridge:
        if active_bridge is None:
            return {"status": "fail", "failures": ["Racket bridge was not created"]}
        for record in report.get("settings", []):
            setting = record.get("setting")
            for key, hash_key in (
                ("rule_path", "rule_sha256"),
                ("private_path", "private_sha256"),
                ("public_path", "public_sha256"),
            ):
                path = out / record[key]
                if not path.is_file():
                    failures.append(f"missing {record[key]}")
                elif sha256_bytes(path.read_bytes()) != record[hash_key]:
                    failures.append(f"hash mismatch {record[key]}")
            if failures:
                continue
            rule_text = (out / record["rule_path"]).read_text(encoding="utf-8").rstrip("\n")
            if rule_text != program_for(setting, root=root_path):
                failures.append(f"rule text mismatch for {setting}")
            private = json.loads((out / record["private_path"]).read_text(encoding="utf-8"))
            public = json.loads((out / record["public_path"]).read_text(encoding="utf-8"))
            if public != public_challenge(private):
                failures.append(f"public projection mismatch for {setting}")
            for index, pair in enumerate(private.get("pairs", [])):
                if evaluate(active_bridge, rule_text, pair["input"]) != pair["output"]:
                    failures.append(f"Racket label mismatch for {setting} pair {index}")
                if python_apply(pair["input"], setting, root=root_path) != pair["output"]:
                    failures.append(f"Python parity mismatch for {setting} pair {index}")
            fresh = assess_episode(active_bridge, private, root=root_path)
            if fresh != private.get("parameter_rival_assessment"):
                failures.append(f"rival assessment mismatch for {setting}")

        canonical = canonical_pairs(TASK_ID, root=root_path, labeled_only=True)
        exact_program = program_for("exact", root=root_path)
        for index, pair in enumerate(canonical):
            if evaluate(active_bridge, exact_program, pair["input"]) != pair["output"]:
                failures.append(f"canonical label mismatch {index}")

    return {"status": "pass" if not failures else "fail", "failures": failures}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    materialize_parser = sub.add_parser("materialize")
    materialize_parser.add_argument("--out", type=Path, required=True)
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.command == "materialize":
        value = materialize(args.out)
    else:
        value = verify_tree(args.out)
    print(json.dumps(value, indent=2, sort_keys=True))
    return 0 if value.get("status") in {"proposed_prototype", "pass"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
