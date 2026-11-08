#!/usr/bin/env python3
"""Task-local scan-order parameter prototype for ARC family 09d287bbfa0b.

This prototype is authoring evidence only. It neither changes the production
rule authority nor treats the reverse-order setting as canonically approved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from contextlib import nullcontext
from pathlib import Path
import random
import sys

from arc_repl.racket_bridge import RacketBridge
from reviewer_support import (
    canonical_pairs,
    canonical_path,
    find_root,
    load_selected_generator,
    normalize_grid,
)


TASK_ID = "09d287bbfa0b"
VERSION = "proposed-scan-order-v1"
SCAN_ORDERS = ("row_major", "reverse_row_major")
DEFAULT_SCAN_ORDER = "row_major"
CANONICAL_PROGRAM_SHA256 = "5ba270db6110a201c0a50caddb0bc3215680ace8e936c2fca3b67d31c1877fcd"
ROW_MAJOR_SCAN = "(d2 (for* ((r (range 0 hh)) (c (range 0 ww)))"
REVERSE_SCAN = "(d2 (for* ((r (range (- hh 1) -1 -1)) (c (range (- ww 1) -1 -1)))"


def sha256(value: str | bytes) -> str:
    """Return a lowercase SHA-256 digest for text or bytes."""
    payload = value.encode("utf-8") if isinstance(value, str) else value
    return hashlib.sha256(payload).hexdigest()


def _check_canonical_source(source: str) -> str:
    if not isinstance(source, str) or sha256(source) != CANONICAL_PROGRAM_SHA256:
        raise ValueError("canonical source SHA256 does not match the pinned program")
    if source.count(ROW_MAJOR_SCAN) != 1 or REVERSE_SCAN in source:
        raise ValueError("canonical program must have one unambiguous row-major scan site")
    return source


def canonical_source(*, root: str | Path | None = None) -> str:
    """Load and pin the unique canonical Racket program for this family."""
    resolved_root = find_root(__file__) if root is None else Path(root)
    sources: set[str] = set()
    with canonical_path(resolved_root).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID and isinstance(row.get("program_solution"), str):
                sources.add(row["program_solution"])
    if len(sources) != 1:
        raise ValueError(f"expected exactly one canonical program for {TASK_ID}")
    return _check_canonical_source(sources.pop())


def _validate_scan_order(scan_order: object) -> str:
    if type(scan_order) is not str or scan_order not in SCAN_ORDERS:
        raise ValueError("scan_order must be 'row_major' or 'reverse_row_major'")
    return scan_order


def materialize_rule(
    scan_order: str = DEFAULT_SCAN_ORDER,
    *,
    root: str | Path | None = None,
    source: str | None = None,
) -> str:
    """Return exact canonical bytes by default; change only source scan order otherwise."""
    order = _validate_scan_order(scan_order)
    canonical = canonical_source(root=root) if source is None else _check_canonical_source(source)
    if order == DEFAULT_SCAN_ORDER:
        return canonical
    return canonical.replace(ROW_MAJOR_SCAN, REVERSE_SCAN, 1)



def grid_sha256(grid: object) -> str:
    """Hash a normalized grid using stable compact JSON."""
    return sha256(json.dumps(normalize_grid(grid), separators=(",", ":")))


def execute_rule(source: str, grid: object, *, bridge: RacketBridge | None = None) -> list[list[int]]:
    """Execute a materialized rule with the protected Racket runtime."""
    if not isinstance(source, str):
        raise ValueError("canonical or materialized Racket source must be text")
    if source.count(REVERSE_SCAN) == 1 and ROW_MAJOR_SCAN not in source:
        canonicalized = source.replace(REVERSE_SCAN, ROW_MAJOR_SCAN, 1)
    elif source.count(ROW_MAJOR_SCAN) == 1 and REVERSE_SCAN not in source:
        canonicalized = source
    else:
        raise ValueError("rule must contain exactly one supported scan-order fragment")
    _check_canonical_source(canonicalized)
    if not source.startswith("(rule! ") or not source.endswith(")"):
        raise ValueError("unexpected canonical rule wrapper")
    body = source[len("(rule! ") : -1]
    normalized = normalize_grid(grid)
    literal = "'(" + " ".join(
        "(" + " ".join(map(str, row)) + ")" for row in normalized
    ) + ")"
    manager = RacketBridge() if bridge is None else nullcontext(bridge)
    with manager as live:
        return normalize_grid(live.eval_text(f"({body} {literal})"))


def choose_scan_order(seed: object) -> str:
    """Choose one hidden setting once per episode without touching global RNG state."""
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be an integer in 0..2**63-1")
    return random.Random(seed).choice(SCAN_ORDERS)


def generate_episode(
    seed: int,
    *,
    root: str | Path | None = None,
    difficulty: str = "medium",
    start: int = 0,
    bridge: RacketBridge | None = None,
) -> dict[str, object]:
    """Build one public challenge and separate private authoring evidence.

    Every input uses the production generator's ``multi_quadrant`` texture with eight
    sources. That constraint is independent of the hidden scan order and gives
    a fully visible, distinct-color same-orbit collision, making both settings observable.
    """
    scan_order = choose_scan_order(seed)
    if type(start) is not int or start < 0:
        raise ValueError("start must be a nonnegative integer")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    resolved_root = find_root(__file__) if root is None else Path(root)
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=resolved_root
    )
    train_count = generator.EXAMPLES_NEEDED
    if type(train_count) is not int or train_count < 1:
        raise ValueError("selected generator must declare a positive EXAMPLES_NEEDED")
    if sha256(Path(generator_path).read_bytes()) != generator_sha256:
        raise RuntimeError("selected generator changed while binding episode sources")

    canonical = canonical_source(root=resolved_root)
    rules = {
        order: materialize_rule(order, source=canonical)
        for order in SCAN_ORDERS
    }
    inputs: list[list[list[int]]] = []
    accepted: list[dict[str, object]] = []
    for position, sample_index in enumerate(range(start, start + train_count + 1)):
        grid = normalize_grid(
            generator.generate(
                seed,
                sample_index,
                difficulty=difficulty,
                texture="multi_quadrant",
                n_pixels=8,
            )
        )
        errors = generator.self_check(grid, difficulty=difficulty)
        if errors:
            raise ValueError(f"unlawful selected-generator input at {sample_index}: {errors}")
        observed = generator.observe_overrides(grid)
        if observed.get("texture") != "multi_quadrant" or observed.get("n_pixels") != 8:
            raise RuntimeError("episode input did not preserve the forced identifying controls")
        inputs.append(grid)
        accepted.append(
            {
                "split": "train" if position < train_count else "test",
                "pair_position": position if position < train_count else 0,
                "sample_index": sample_index,
                "input_sha256": grid_sha256(grid),
                "observed_texture": observed["texture"],
                "observed_n_pixels": observed["n_pixels"],
            }
        )

    manager = RacketBridge() if bridge is None else nullcontext(bridge)
    with manager as live:
        predictions = {
            order: [execute_rule(rule, grid, bridge=live) for grid in inputs]
            for order, rule in rules.items()
        }
    outputs = predictions[scan_order]
    challenge = {
        "train": [
            {"input": grid, "output": output}
            for grid, output in zip(inputs[:train_count], outputs[:train_count])
        ],
        "test": [{"input": inputs[-1]}],
    }

    rivals: dict[str, dict[str, object]] = {}
    for order in SCAN_ORDERS:
        demo_disagreements = [
            index
            for index in range(train_count)
            if predictions[order][index] != outputs[index]
        ]
        query_disagreements = [0] if predictions[order][-1] != outputs[-1] else []
        rivals[order] = {
            "status": (
                "selected"
                if order == scan_order
                else (
                    "eliminated_by_demonstrations"
                    if demo_disagreements
                    else ("ambiguous_query" if query_disagreements else "survived_all")
                )
            ),
            "demo_disagreements": demo_disagreements,
            "query_disagreements": query_disagreements,
            "rule_sha256": sha256(rules[order]),
            "train_predictions": predictions[order][:train_count],
            "query_predictions": predictions[order][train_count:],
        }
    identifiable = all(
        rivals[order]["demo_disagreements"]
        for order in SCAN_ORDERS
        if order != scan_order
    )
    test_path = (
        resolved_root
        / "generators"
        / TASK_ID
        / "tests"
        / "test_parametric_scan_order.py"
    )
    private = {
        "schema": "09d287bbfa0b-scan-order-episode-v1",
        "status": "proposed_prototype",
        "task_id": TASK_ID,
        "version": VERSION,
        "seed": seed,
        "parameters": {"scan_order": scan_order},
        "sampling": {
            "difficulty": difficulty,
            "start": start,
            "train_count": train_count,
            "query_count": 1,
            "forced_controls": {"texture": "multi_quadrant", "n_pixels": 8},
            "accepted_pairs": accepted,
        },
        "bindings": {
            "generator_sha256": generator_sha256,
            "prototype_sha256": sha256(Path(__file__).read_bytes()),
            "test_sha256": sha256(test_path.read_bytes()),
            "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
        },
        "reference_rule": {
            "racket": rules[scan_order],
            "sha256": sha256(rules[scan_order]),
        },
        "query_answers": [{"output": outputs[-1]}],
        "parameter_rivals": rivals,
        "identifiable_against_parameter_rivals": identifiable,
    }
    return {"challenge": challenge, "private": private}



def _source_files(root: Path, generator_path: Path) -> dict[str, bytes]:
    paths = {
        "prototype.py": Path(__file__),
        "generator.py": Path(generator_path),
        "test_parametric_scan_order.py": (
            root / "generators" / TASK_ID / "tests" / "test_parametric_scan_order.py"
        ),
        "README.md": Path(__file__).with_name("README.md"),
    }
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing prototype source files: {missing}")
    return {name: path.read_bytes() for name, path in paths.items()}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def retain_evidence(
    seeds: list[int] | tuple[int, ...],
    out: str | Path,
    *,
    root: str | Path | None = None,
    difficulty: str = "medium",
    start: int = 0,
) -> dict[str, object]:
    """Execute and retain canonical replay, witnesses, and complete episodes."""
    if not isinstance(seeds, (list, tuple)) or not seeds:
        raise ValueError("seeds must be a nonempty list or tuple")
    for seed in seeds:
        choose_scan_order(seed)
    if type(start) is not int or start < 0:
        raise ValueError("start must be a nonnegative integer")
    if difficulty not in ("easy", "medium", "hard"):
        raise ValueError("difficulty must be easy, medium, or hard")
    out = Path(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("out must be new or empty, so retained runs cannot mix")

    resolved_root = find_root(__file__) if root is None else Path(root)
    generator, generator_path, generator_sha256 = load_selected_generator(
        TASK_ID, root=resolved_root
    )
    sources = _source_files(resolved_root, generator_path)
    if sha256(sources["generator.py"]) != generator_sha256:
        raise RuntimeError("selected generator changed while binding evidence sources")
    rules = {
        order: materialize_rule(order, root=resolved_root)
        for order in SCAN_ORDERS
    }
    private_dir = out / "private"
    for name, body in sources.items():
        path = private_dir / "source_snapshot" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    for order, rule in rules.items():
        path = private_dir / "rules" / f"scan-{order}.rkt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rule, encoding="utf-8")

    with RacketBridge() as bridge:
        replay_rows: list[dict[str, object]] = []
        for pair in canonical_pairs(TASK_ID, root=resolved_root, labeled_only=True):
            actual = execute_rule(rules[DEFAULT_SCAN_ORDER], pair["input"], bridge=bridge)
            replay_rows.append(
                {
                    **pair,
                    "input_sha256": grid_sha256(pair["input"]),
                    "expected_output_sha256": grid_sha256(pair["output"]),
                    "actual_output": actual,
                    "actual_output_sha256": grid_sha256(actual),
                    "matches": actual == pair["output"],
                }
            )
        replay = {
            "pairs": len(replay_rows),
            "failed": sum(not row["matches"] for row in replay_rows),
            "unique_labelled_pairs": len(
                {
                    json.dumps([row["input"], row["output"]], separators=(",", ":"))
                    for row in replay_rows
                }
            ),
            "rule_sha256": sha256(rules[DEFAULT_SCAN_ORDER]),
            "results": replay_rows,
        }
        _write_json(private_dir / "canonical_replay.json", replay)

        episodes: list[dict[str, object]] = []
        for index, seed in enumerate(seeds):
            episode = generate_episode(
                seed,
                root=resolved_root,
                difficulty=difficulty,
                start=start,
                bridge=bridge,
            )
            private = episode["private"]
            if private["bindings"]["generator_sha256"] != generator_sha256:
                raise RuntimeError("selected generator changed during evidence run")
            public_path = out / "public" / f"episode-{index:03d}.json"
            private_path = private_dir / f"episode-{index:03d}.json"
            _write_json(public_path, episode["challenge"])
            private["public_file"] = public_path.relative_to(out).as_posix()
            private["public_file_sha256"] = sha256(public_path.read_bytes())
            _write_json(private_path, private)
            episodes.append(
                {
                    "seed": seed,
                    "scan_order": private["parameters"]["scan_order"],
                    "public_file": public_path.relative_to(out).as_posix(),
                    "private_file": private_path.relative_to(out).as_posix(),
                    "train_count": private["sampling"]["train_count"],
                    "identifiable_against_parameter_rivals": private[
                        "identifiable_against_parameter_rivals"
                    ],
                    "reference_rule_sha256": private["reference_rule"]["sha256"],
                }
            )

        witness_input = normalize_grid(
            generator.generate(
                seeds[0],
                start,
                difficulty=difficulty,
                texture="multi_quadrant",
                n_pixels=8,
            )
        )
        witness_outputs = {
            order: execute_rule(rule, witness_input, bridge=bridge)
            for order, rule in rules.items()
        }
        witness = {
            "seed": seeds[0],
            "sample_index": start,
            "difficulty": difficulty,
            "forced_controls": {"texture": "multi_quadrant", "n_pixels": 8},
            "input": witness_input,
            "input_sha256": grid_sha256(witness_input),
            "input_constraint_errors": generator.self_check(
                witness_input, difficulty=difficulty
            ),
            "outputs": witness_outputs,
            "output_sha256": {
                order: grid_sha256(output)
                for order, output in witness_outputs.items()
            },
            "outputs_differ": (
                witness_outputs["row_major"]
                != witness_outputs["reverse_row_major"]
            ),
        }
        _write_json(private_dir / "distinguishing_witness.json", witness)
        runtime_identity = bridge.runtime_identity

    settings_observed = sorted({episode["scan_order"] for episode in episodes})
    passed = (
        bool(replay_rows)
        and replay["failed"] == 0
        and witness["outputs_differ"]
        and not witness["input_constraint_errors"]
        and all(
            episode["identifiable_against_parameter_rivals"]
            for episode in episodes
        )
        and settings_observed == sorted(SCAN_ORDERS)
    )
    report = {
        "schema": "09d287bbfa0b-scan-order-evidence-v1",
        "status": "bounded_checks_passed" if passed else "bounded_checks_failed",
        "admission": "proposed prototype; no production or canonical approval",
        "parameter": {
            "name": "scan_order",
            "allowed": list(SCAN_ORDERS),
            "default": DEFAULT_SCAN_ORDER,
            "input_constraints": {
                "common_to_all_settings": {
                    "texture": "multi_quadrant",
                    "n_pixels": 8,
                },
                "reason": (
                    "a fully visible distinct-color same-orbit collision makes "
                    "source traversal order observable"
                ),
            },
        },
        "settings_observed": settings_observed,
        "commands": {
            "payload_argv": [sys.executable, *sys.argv],
            "cwd": str(Path.cwd()),
        },
        "source_files": {name: sha256(body) for name, body in sources.items()},
        "generator_sha256": generator_sha256,
        "canonical_program_sha256": CANONICAL_PROGRAM_SHA256,
        "rules": {
            order: {
                "path": f"private/rules/scan-{order}.rkt",
                "sha256": sha256(rule),
                "is_canonical_default": order == DEFAULT_SCAN_ORDER,
            }
            for order, rule in rules.items()
        },
        "canonical_replay": {
            key: value for key, value in replay.items() if key != "results"
        },
        "distinguishing_witness": {
            "path": "private/distinguishing_witness.json",
            "outputs_differ": witness["outputs_differ"],
            "input_sha256": witness["input_sha256"],
        },
        "episodes": episodes,
        "runtime_identity": runtime_identity,
        "limitations": [
            "Only the requested seeds, difficulty, and start were executed.",
            "Identifiability is checked against the declared row-major/reverse-row-major parameter rival, not every possible ARC rule.",
            "The alternative changes source traversal only; all other canonical roles and operations are held fixed.",
            "Canonical repair and production admission remain separate from this authoring prototype.",
        ],
    }
    _write_json(private_dir / "report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    parser.add_argument(
        "--difficulty", choices=("easy", "medium", "hard"), default="medium"
    )
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = retain_evidence(
            args.seeds,
            args.out,
            difficulty=args.difficulty,
            start=args.start,
        )
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        parser.exit(2, f"prototype error: {exc}\n")
    print(
        json.dumps(
            {
                "status": report["status"],
                "episodes": len(report["episodes"]),
                "settings_observed": report["settings_observed"],
                "canonical_pairs": report["canonical_replay"]["pairs"],
                "report": str(args.out / "private/report.json"),
            },
            sort_keys=True,
        )
    )
    return 0 if report["status"] == "bounded_checks_passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
