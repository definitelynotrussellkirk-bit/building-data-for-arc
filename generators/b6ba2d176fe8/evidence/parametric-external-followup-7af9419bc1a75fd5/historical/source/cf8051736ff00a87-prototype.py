#!/usr/bin/env python3
"""Proposed episode-level sort-order variant for ARC task b6ba2d176fe8.

This task-local prototype does not alter production generation or selected rule
authority.  It chooses one ordering rule for an entire episode, executes exact
Racket for every label, and checks the alternate setting against all demos.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
from typing import Iterable


TASK_ID = "b6ba2d176fe8"
FAMILY = "training:03560426"
VERSION = "0.1.0"
SCHEMA = "arc-task-parametric-sort-order-v1"
TASK_HOME = Path(__file__).resolve().parents[2]
REPO = TASK_HOME.parents[1]
CANONICAL_PATH = REPO / "shared/data/canonical/puzzles.jsonl"
SELECTED_PATH = (
    REPO
    / "shared/data/base/solutions/training/03560426__b6ba2d176fe8.json"
)
GENERATOR_PATH = TASK_HOME / "generator.py"
TEST_PATH = TASK_HOME / "tests/test_parametric_sort_order.py"
README_PATH = Path(__file__).with_name("README.md")
_SORT_FRAGMENT = "(sorted (sort-by objs (lambda (o) (second (obj-bbox o)))))"
_REVERSE_SORT_FRAGMENT = (
    "(sorted (reverse (sort-by objs (lambda (o) (second (obj-bbox o))))))"
)
LIMITATIONS = [
    "Proposed task-local prototype only; it does not change production generation, selected authority, approval, or training admission.",
    "Evidence checks the two declared sort-order settings and recorded seeds, not every plausible rule or every lawful input.",
    "Inputs come from the repaired production generator, so prototype evidence is source-bound to that generator implementation.",
    "Public challenges hide the setting and query label; private evidence contains exact programs, labels, rivals, and hashes.",
]


class Settings:
    """One immutable episode-level rule setting."""

    __slots__ = ("sort_order",)

    def __init__(self, sort_order: str = "left_to_right"):
        if type(sort_order) is not str or sort_order not in (
            "left_to_right",
            "right_to_left",
        ):
            raise ValueError("sort_order must be left_to_right or right_to_left")
        object.__setattr__(self, "sort_order", sort_order)

    def __setattr__(self, name, value):  # pragma: no cover - defensive immutability
        raise AttributeError("Settings is immutable")

    def __repr__(self):
        return f"Settings(sort_order={self.sort_order!r})"

    def __eq__(self, other):
        return isinstance(other, Settings) and self.sort_order == other.sort_order

    def __hash__(self):
        return hash(self.sort_order)

    def as_dict(self):
        return {"sort_order": self.sort_order}


DEFAULT = Settings()
ALL_SETTINGS = (Settings("left_to_right"), Settings("right_to_left"))
_GENERATOR = None
_CANONICAL_PROGRAM = None


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def digest(value) -> str:
    return text_digest(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    )


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_seed(seed: int) -> int:
    if type(seed) is not int or not 0 <= seed < 2**63:
        raise ValueError("seed must be a literal integer in 0..2**63-1")
    return seed


def _load_generator():
    global _GENERATOR
    if _GENERATOR is None:
        spec = importlib.util.spec_from_file_location(
            "b6ba2d176fe8_parametric_generator", GENERATOR_PATH
        )
        if spec is None or spec.loader is None:
            raise RuntimeError(f"cannot load generator from {GENERATOR_PATH}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _GENERATOR = module
    return _GENERATOR


def _canonical_record() -> dict:
    for line in CANONICAL_PATH.read_text().splitlines():
        record = json.loads(line)
        if record.get("task_id") == TASK_ID:
            return record
    raise ValueError(f"canonical task {TASK_ID} not found")


def canonical_program() -> str:
    global _CANONICAL_PROGRAM
    if _CANONICAL_PROGRAM is None:
        source = _canonical_record().get("program_solution")
        if not isinstance(source, str) or not source.strip():
            raise ValueError("canonical program_solution is missing")
        if source.count(_SORT_FRAGMENT) != 1:
            raise ValueError("canonical sort fragment is not unique")
        _CANONICAL_PROGRAM = source
    return _CANONICAL_PROGRAM


def selected_target_program() -> str:
    record = json.loads(SELECTED_PATH.read_text())
    source = record.get("racket_target", {}).get("target_code")
    if not isinstance(source, str) or not source.strip():
        raise ValueError("selected target_code is missing")
    return source


def authority_identity() -> dict:
    canonical = canonical_program()
    selected = selected_target_program()
    return {
        "canonical_path": CANONICAL_PATH.relative_to(REPO).as_posix(),
        "selected_path": SELECTED_PATH.relative_to(REPO).as_posix(),
        "canonical_program_sha256": text_digest(canonical),
        "selected_program_sha256": text_digest(selected),
        "canonical_rule_hash_12": text_digest(" ".join(canonical.split()))[:12],
        "selected_exact_match": selected == canonical,
        "canonical_file_sha256": file_digest(CANONICAL_PATH),
        "selected_file_sha256": file_digest(SELECTED_PATH),
    }


def program(settings: Settings = DEFAULT) -> str:
    if not isinstance(settings, Settings):
        raise ValueError("settings must be a Settings instance")
    source = canonical_program()
    if settings.sort_order == "left_to_right":
        return source
    transformed = source.replace(_SORT_FRAGMENT, _REVERSE_SORT_FRAGMENT)
    if transformed == source or transformed.count(_REVERSE_SORT_FRAGMENT) != 1:
        raise ValueError("failed to materialize right_to_left Racket program")
    return transformed


def select_settings(seed: int, *, sort_order: str = "left_to_right") -> Settings:
    """Choose the hidden rule once; callers reuse the returned value per episode."""
    rng = random.Random(f"{TASK_ID}:{VERSION}:setting:{_validate_seed(seed)}")
    if sort_order == "sample":
        sort_order = rng.choice(("left_to_right", "right_to_left"))
    return Settings(sort_order)


def validate_grid(grid) -> list[list[int]]:
    generator = _load_generator()
    errors = generator.self_check(grid)
    if errors:
        raise ValueError("input is outside the canonical generator grammar: " + "; ".join(errors))
    return [list(row) for row in grid]


def transform(grid, settings: Settings = DEFAULT):
    """Independent Python parity model; never used to manufacture labels."""
    if not isinstance(settings, Settings):
        raise ValueError("settings must be a Settings instance")
    source = validate_grid(grid)
    generator = _load_generator()
    rectangles = generator._ordered_rectangles(source)
    if not rectangles:
        raise ValueError("no rectangular objects found")
    if settings.sort_order == "right_to_left":
        rectangles = list(reversed(rectangles))

    output = [[0 for _ in row] for row in source]
    row = column = 0
    for rectangle in rectangles:
        top, left, bottom, right = rectangle["bbox"]
        height = bottom - top + 1
        width = right - left + 1
        for rr in range(row, row + height):
            for cc in range(column, column + width):
                output[rr][cc] = rectangle["color"]
        row += height - 1
        column += width - 1
    return output


def sample_inputs(seed: int) -> list[list[list[int]]]:
    """Four deterministic lawful inputs shared by every setting in an episode."""
    seed = _validate_seed(seed)
    generator = _load_generator()
    profiles = (
        ("easy", 3, "bottom", "compact"),
        ("medium", 4, "mixed", "irregular"),
        ("hard", 5, "scattered", "spread"),
        ("hard", 6, "mixed", "irregular"),
    )
    inputs = []
    for index, (difficulty, n_objects, row_layout, column_layout) in enumerate(profiles):
        grid = generator.generate(
            seed,
            10_007 + index * 997,
            difficulty=difficulty,
            canonical_prior=False,
            n_objects=n_objects,
            row_layout=row_layout,
            column_layout=column_layout,
        )
        inputs.append([row[:] for row in grid])
    return inputs


def _grid_literal(grid) -> str:
    validate_grid(grid)
    return "'(" + " ".join(
        "(" + " ".join(str(value) for value in row) + ")" for row in grid
    ) + ")"


class RacketLabels:
    """Outputs cached only after successful protected-Racket execution."""

    def __enter__(self):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(timeout=20.0, startup_timeout=45.0)
        self.runtime_identity = dict(self.bridge.runtime_identity)
        if not self.runtime_identity.get("protected"):
            self.bridge.shutdown()
            raise RuntimeError("protected Racket runtime required")
        self.cache = {}
        self.requests = 0
        return self

    def __exit__(self, *exc):
        self.bridge.shutdown()

    def output(self, grid, settings: Settings):
        validate_grid(grid)
        source = program(settings)
        key = (text_digest(source), digest(grid))
        self.requests += 1
        if key not in self.cache:
            expression = (
                f"(let ((rule! (lambda (f) f))) "
                f"({source} {_grid_literal(grid)}))"
            )
            output = self.bridge.eval_text(expression)
            expected = transform(grid, settings)
            if output != expected:
                raise ValueError(
                    f"Racket/Python parity mismatch for {settings.sort_order} "
                    f"on input {digest(grid)}"
                )
            self.cache[key] = output
        return copy.deepcopy(self.cache[key])


def _source_hashes() -> dict[str, str]:
    paths = (
        Path(__file__).resolve(),
        README_PATH,
        TEST_PATH,
        GENERATOR_PATH,
        CANONICAL_PATH,
        SELECTED_PATH,
    )
    return {path.relative_to(REPO).as_posix(): file_digest(path) for path in paths}


def _public_episode(episode: dict) -> dict:
    return {
        "train": [
            {"input": pair["input"], "output": pair["output"]}
            for pair in episode["pairs"][:3]
        ],
        "test": [{"input": episode["pairs"][3]["input"]}],
    }


def _episode(seed: int, settings: Settings, labels: RacketLabels) -> dict:
    inputs = sample_inputs(seed)
    pairs = []
    for index, grid in enumerate(inputs):
        output = labels.output(grid, settings)
        pairs.append(
            {
                "index": index,
                "split": "train" if index < 3 else "test",
                "input": grid,
                "input_sha256": digest(grid),
                "output": output,
                "output_sha256": digest(output),
            }
        )

    rivals = []
    for alternate in ALL_SETTINGS:
        if alternate == settings:
            continue
        predictions = [labels.output(grid, alternate) for grid in inputs]
        matches = [
            prediction == pair["output"]
            for prediction, pair in zip(predictions, pairs, strict=True)
        ]
        if all(matches[:3]):
            status = "survived_all" if matches[3] else "ambiguous_query"
        else:
            status = "refuted_by_demonstrations"
        rivals.append(
            {
                "parameters": alternate.as_dict(),
                "program_sha256": text_digest(program(alternate)),
                "predictions": predictions,
                "prediction_sha256": [digest(value) for value in predictions],
                "demo_matches": matches[:3],
                "query_matches": matches[3:],
                "status": status,
                "first_refuting_demo": next(
                    (i for i, match in enumerate(matches[:3]) if not match), None
                ),
            }
        )

    opaque = text_digest(
        f"{TASK_ID}:{VERSION}:public:{seed}:{settings.sort_order}"
    )[:16]
    return {
        "seed": seed,
        "parameters": settings.as_dict(),
        "program": program(settings),
        "program_sha256": text_digest(program(settings)),
        "pairs": pairs,
        "rivals": rivals,
        "public_path": f"public/episode-{opaque}.json",
    }


def _semantic_metadata() -> dict:
    return {
        "schema": SCHEMA,
        "prototype_version": VERSION,
        "task_id": TASK_ID,
        "family": FAMILY,
        "classification": "proposed unapproved task-local prototype",
        "parameter_space": {"sort_order": ["left_to_right", "right_to_left"]},
        "default": DEFAULT.as_dict(),
        "input_constraints_by_setting": {
            "left_to_right": "canonical generator grammar",
            "right_to_left": "same grammar; total staircase extent is order-invariant",
        },
        "episode_policy": {
            "setting_draws": 1,
            "demonstrations": 3,
            "queries": 1,
            "same_inputs_across_settings_for_evidence": True,
            "rival_gate": (
                "fail when an alternate fits all demonstrations and changes the query"
            ),
        },
        "limitations": LIMITATIONS,
    }


def build_evidence(seed: int, settings: Iterable[Settings]) -> dict:
    seed = _validate_seed(seed)
    settings = tuple(settings)
    if not settings or any(not isinstance(value, Settings) for value in settings):
        raise ValueError("settings must be a nonempty iterable of Settings")
    if len(set(settings)) != len(settings):
        raise ValueError("settings must be unique")

    authority = authority_identity()
    if not authority["selected_exact_match"]:
        raise ValueError("selected target_code is not exact canonical program_solution")

    with RacketLabels() as labels:
        episodes = [_episode(seed, setting, labels) for setting in settings]
        witness_input = sample_inputs(seed)[0]
        witness_outputs = {
            setting.sort_order: labels.output(witness_input, setting)
            for setting in ALL_SETTINGS
        }
        runtime_identity = labels.runtime_identity
        racket_requests = labels.requests

    distinct = len({digest(value) for value in witness_outputs.values()}) == len(
        ALL_SETTINGS
    )
    rivals_pass = all(
        rival["status"] == "refuted_by_demonstrations"
        for episode in episodes
        for rival in episode["rivals"]
    )
    evidence = {
        **_semantic_metadata(),
        "status": "pass" if distinct and rivals_pass else "fail",
        "seed": seed,
        "authority": authority,
        "source_hashes": _source_hashes(),
        "runtime_identity": runtime_identity,
        "rules": [
            {
                "parameters": setting.as_dict(),
                "program": program(setting),
                "program_sha256": text_digest(program(setting)),
                "path": f"private/rules/{setting.sort_order}.rkt",
            }
            for setting in ALL_SETTINGS
        ],
        "episodes": episodes,
        "distinct_setting_witness": {
            "input": witness_input,
            "input_sha256": digest(witness_input),
            "outputs": witness_outputs,
            "output_sha256": {
                name: digest(output) for name, output in witness_outputs.items()
            },
            "all_distinct": distinct,
        },
        "counts": {
            "episodes": len(episodes),
            "pairs": sum(len(episode["pairs"]) for episode in episodes),
            "rival_checks": sum(len(episode["rivals"]) for episode in episodes),
            "racket_requests": racket_requests,
            "unique_program_input_executions": len(ALL_SETTINGS)
            * len(sample_inputs(seed)),
        },
    }
    return evidence


def _safe_relative(root: Path, relative: str) -> Path:
    path = root / relative
    resolved_root = root.resolve()
    resolved = path.resolve()
    if resolved_root not in (resolved, *resolved.parents):
        raise ValueError(f"path escapes bundle: {relative!r}")
    return path


def emit_bundle(seed: int, settings: Iterable[Settings], output) -> dict:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    try:
        evidence = build_evidence(seed, settings)
        (output / "public").mkdir()
        (output / "private/rules").mkdir(parents=True)
        for rule in evidence["rules"]:
            path = _safe_relative(output, rule["path"])
            path.write_text(rule["program"])
        for episode in evidence["episodes"]:
            path = _safe_relative(output, episode["public_path"])
            path.write_text(json.dumps(_public_episode(episode), indent=2) + "\n")
        evidence_path = output / "private/evidence.json"
        evidence_path.write_text(json.dumps(evidence, indent=2) + "\n")
        return {
            "schema": SCHEMA,
            "status": evidence["status"],
            "bundle": str(output),
            "evidence": str(evidence_path),
            "evidence_sha256": file_digest(evidence_path),
            "episodes": len(evidence["episodes"]),
            "public_files": len(evidence["episodes"]),
        }
    except Exception as exc:
        failure = output / "private/failure.json"
        failure.parent.mkdir(parents=True, exist_ok=True)
        failure.write_text(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "status": "failed",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                indent=2,
            )
            + "\n"
        )
        raise


def verify_bundle(output) -> dict:
    output = Path(output)
    evidence_path = output / "private/evidence.json"
    evidence = json.loads(evidence_path.read_text())
    if evidence.get("schema") != SCHEMA or evidence.get("status") != "pass":
        raise ValueError("bundle is not a completed passing prototype")
    for key, value in _semantic_metadata().items():
        if evidence.get(key) != value:
            raise ValueError(f"semantic metadata changed: {key}")
    if evidence.get("source_hashes") != _source_hashes():
        raise ValueError("prototype source binding changed; emit fresh evidence")

    settings = tuple(Settings(**episode["parameters"]) for episode in evidence["episodes"])
    if len(settings) != len(set(settings)):
        raise ValueError("duplicate episode settings")

    expected_public_paths = {episode["public_path"] for episode in evidence["episodes"]}
    public_root = output / "public"
    actual_public_paths = {
        path.relative_to(output).as_posix()
        for path in public_root.rglob("*")
        if path.is_file()
    }
    if actual_public_paths != expected_public_paths:
        raise ValueError("public file inventory differs from private evidence")
    if public_root.is_symlink() or any(path.is_symlink() for path in public_root.rglob("*")):
        raise ValueError("public bundle contains symlinks")

    for rule in evidence["rules"]:
        setting = Settings(**rule["parameters"])
        exact = program(setting)
        path = _safe_relative(output, rule["path"])
        if rule["program"] != exact or rule["program_sha256"] != text_digest(exact):
            raise ValueError("private rule metadata differs from current exact program")
        if path.read_text() != exact:
            raise ValueError("saved private rule differs from exact program")

    for episode in evidence["episodes"]:
        public = json.loads(_safe_relative(output, episode["public_path"]).read_text())
        if public != _public_episode(episode):
            raise ValueError("public challenge changed")
        if set(public) != {"train", "test"}:
            raise ValueError("public challenge exposes unexpected top-level metadata")
        if any(set(query) != {"input"} for query in public["test"]):
            raise ValueError("public query exposes more than its input")

    fresh = build_evidence(evidence["seed"], settings)
    for key in (
        "authority",
        "source_hashes",
        "rules",
        "episodes",
        "distinct_setting_witness",
        "counts",
        "status",
    ):
        if digest(evidence[key]) != digest(fresh[key]):
            raise ValueError(f"reexecuted {key} differs from saved evidence")
    return {
        "schema": SCHEMA,
        "status": "pass",
        "bundle": str(output),
        "evidence_sha256": file_digest(evidence_path),
        "episodes_reexecuted": len(fresh["episodes"]),
        "pairs_reexecuted": fresh["counts"]["pairs"],
        "current_runtime_identity": fresh["runtime_identity"],
        "authority": fresh["authority"],
    }


def _write_json_exclusive(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as handle:
        json.dump(value, handle, indent=2)
        handle.write("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    emit = subparsers.add_parser("emit", help="materialize executable prototype evidence")
    emit.add_argument("--seed", type=int, default=20261023)
    emit.add_argument(
        "--sort-order",
        choices=("left_to_right", "right_to_left", "sample"),
        default="left_to_right",
    )
    emit.add_argument("--all-settings", action="store_true")
    emit.add_argument("--out", required=True)

    verify = subparsers.add_parser("verify", help="reexecute and verify a saved bundle")
    verify.add_argument("bundle")
    verify.add_argument("--out")

    args = parser.parse_args(argv)
    if args.command == "emit":
        settings = ALL_SETTINGS if args.all_settings else (
            select_settings(args.seed, sort_order=args.sort_order),
        )
        result = emit_bundle(args.seed, settings, args.out)
    else:
        result = verify_bundle(args.bundle)
        if args.out:
            _write_json_exclusive(args.out, result)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
