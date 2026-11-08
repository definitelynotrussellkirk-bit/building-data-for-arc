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

from reviewer_support import public_challenge_bytes, public_challenge_id


TASK_ID = "b6ba2d176fe8"
FAMILY = "training:03560426"
VERSION = "0.2.0"
SCHEMA = "arc-task-parametric-sort-order-v2"
DEFAULT_DEMOS = 3
DEFAULT_QUERIES = 4
DEMO_LIMITS = (3, 8)
QUERY_LIMITS = (1, 8)
MAX_SAMPLE_ATTEMPTS = 512
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
ADAPTER_PATH = Path(__file__).with_name("adapter.py")
PROMOTION_PATH = Path(__file__).with_name("promotion.json")
_SORT_FRAGMENT = "(sorted (sort-by objs (lambda (o) (second (obj-bbox o)))))"
_REVERSE_SORT_FRAGMENT = (
    "(sorted (reverse (sort-by objs (lambda (o) (second (obj-bbox o))))))"
)
LIMITATIONS = [
    "Proposed task-local prototype only; it does not change production generation, selected authority, approval, or training admission.",
    "Evidence checks the two declared sort-order settings and recorded seeds, not every plausible rule or every lawful input.",
    "Inputs come from the repaired production generator, so prototype evidence is source-bound to that generator implementation.",
    "Supported requests are 3..8 demonstrations and 1..8 queries; bounded sampling rejects rather than silently reducing counts.",
    "Public challenges hide settings, seeds, programs, and query labels; identifiers hash only exact visible bytes.",
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


def _validate_count(name: str, value, limits: tuple[int, int]) -> int:
    lower, upper = limits
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f"{name} must be a literal integer in {lower}..{upper}")
    return value


def _validate_total_count(value) -> int:
    maximum = DEMO_LIMITS[1] + QUERY_LIMITS[1]
    if type(value) is not int or not 1 <= value <= maximum:
        raise ValueError(f"count must be a literal integer in 1..{maximum}")
    return value


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
    """Independent Python parity model; never used to manufacture retained labels."""
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


def _sample_input_records(
    seed: int,
    *,
    count: int,
    max_attempts: int = MAX_SAMPLE_ATTEMPTS,
) -> list[dict]:
    """Return a deterministic bounded set of distinct lawful inputs."""
    seed = _validate_seed(seed)
    count = _validate_total_count(count)
    if type(max_attempts) is not int or not 1 <= max_attempts <= 10_000:
        raise ValueError("max_attempts must be a literal integer in 1..10000")
    generator = _load_generator()
    profiles = (
        ("easy", 3, "bottom", "compact"),
        ("medium", 4, "mixed", "irregular"),
        ("hard", 5, "scattered", "spread"),
        ("hard", 6, "mixed", "irregular"),
    )
    records: list[dict] = []
    seen: set[str] = set()
    for attempt in range(max_attempts):
        difficulty, n_objects, row_layout, column_layout = profiles[attempt % len(profiles)]
        sample_index = 10_007 + attempt * 997
        try:
            grid = generator.generate(
                seed,
                sample_index,
                difficulty=difficulty,
                canonical_prior=False,
                n_objects=n_objects,
                row_layout=row_layout,
                column_layout=column_layout,
            )
            grid = validate_grid(grid)
        except (RuntimeError, ValueError):
            continue
        input_sha256 = digest(grid)
        if input_sha256 in seen:
            continue
        seen.add(input_sha256)
        records.append(
            {
                "input": grid,
                "input_sha256": input_sha256,
                "sample_index": sample_index,
                "profile": {
                    "difficulty": difficulty,
                    "n_objects": n_objects,
                    "row_layout": row_layout,
                    "column_layout": column_layout,
                },
            }
        )
        if len(records) == count:
            return records
    raise RuntimeError(
        f"sampling budget exhausted: accepted {len(records)} distinct inputs "
        f"of {count} requested after {max_attempts} attempts"
    )


def sample_inputs(
    seed: int,
    *,
    count: int = DEFAULT_DEMOS + DEFAULT_QUERIES,
    max_attempts: int = MAX_SAMPLE_ATTEMPTS,
) -> list[list[list[int]]]:
    return [
        copy.deepcopy(record["input"])
        for record in _sample_input_records(seed, count=count, max_attempts=max_attempts)
    ]


def build_claimed_episode(
    seed: int,
    settings: Settings = DEFAULT,
    *,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
) -> dict:
    """Build a fixed-setting Python claim for the independent promotion worker."""
    if not isinstance(settings, Settings):
        raise ValueError("settings must be a Settings instance")
    demos = _validate_count("demos", demos, DEMO_LIMITS)
    queries = _validate_count("queries", queries, QUERY_LIMITS)
    records = _sample_input_records(seed, count=demos + queries)
    pairs = [
        {
            "input": copy.deepcopy(record["input"]),
            "output": transform(record["input"], settings),
        }
        for record in records
    ]
    return {
        "train": pairs[:demos],
        "test": pairs[demos:],
        "program_solution": program(settings),
    }


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
        ADAPTER_PATH,
        PROMOTION_PATH,
        GENERATOR_PATH,
        CANONICAL_PATH,
        SELECTED_PATH,
    )
    missing = [path for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"prototype source binding is incomplete: {missing}")
    return {path.relative_to(REPO).as_posix(): file_digest(path) for path in paths}


def public_episode(episode: dict) -> dict:
    pairs = episode.get("pairs")
    if type(pairs) is not list:
        raise ValueError("episode pairs must be a list")
    train = [
        {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
        for pair in pairs
        if pair.get("split") == "train"
    ]
    test = [
        {"input": copy.deepcopy(pair["input"])}
        for pair in pairs
        if pair.get("split") == "test"
    ]
    return {"train": train, "test": test}


def public_identity(episode: dict) -> str:
    """Hash only exact model-visible demonstrations and query inputs."""
    return public_challenge_id(public_episode(episode))


def _episode(
    seed: int,
    settings: Settings,
    labels: RacketLabels,
    *,
    demos: int,
    queries: int,
    input_records: list[dict],
) -> dict:
    pairs = []
    for index, record in enumerate(input_records):
        grid = record["input"]
        output = labels.output(grid, settings)
        pairs.append(
            {
                "index": index,
                "split": "train" if index < demos else "test",
                "sample_index": record["sample_index"],
                "profile": record["profile"],
                "input": copy.deepcopy(grid),
                "input_sha256": record["input_sha256"],
                "output": output,
                "output_sha256": digest(output),
            }
        )

    rivals = []
    for alternate in ALL_SETTINGS:
        if alternate == settings:
            continue
        predictions = [labels.output(record["input"], alternate) for record in input_records]
        matches = [
            prediction == pair["output"]
            for prediction, pair in zip(predictions, pairs, strict=True)
        ]
        demo_matches = matches[:demos]
        query_matches = matches[demos:]
        if all(demo_matches):
            status = "survived_all" if all(query_matches) else "ambiguous_query"
        else:
            status = "refuted_by_demonstrations"
        rivals.append(
            {
                "parameters": alternate.as_dict(),
                "program_sha256": text_digest(program(alternate)),
                "predictions": predictions,
                "prediction_sha256": [digest(value) for value in predictions],
                "demo_matches": demo_matches,
                "query_matches": query_matches,
                "status": status,
                "first_refuting_demo": next(
                    (i for i, match in enumerate(demo_matches) if not match), None
                ),
            }
        )

    episode = {
        "seed": seed,
        "parameters": settings.as_dict(),
        "program": program(settings),
        "program_sha256": text_digest(program(settings)),
        "demo_count": demos,
        "query_count": queries,
        "pairs": pairs,
        "rivals": rivals,
    }
    identifier = public_identity(episode)
    episode["public_id"] = identifier
    episode["public_path"] = f"public/{identifier}.json"
    return episode


def _semantic_metadata(demos: int, queries: int) -> dict:
    demos = _validate_count("demos", demos, DEMO_LIMITS)
    queries = _validate_count("queries", queries, QUERY_LIMITS)
    return {
        "schema": SCHEMA,
        "prototype_version": VERSION,
        "task_id": TASK_ID,
        "family": FAMILY,
        "classification": "proposed unapproved task-local prototype",
        "parameter_space": {"sort_order": ["left_to_right", "right_to_left"]},
        "default": DEFAULT.as_dict(),
        "count_limits": {
            "demonstrations": list(DEMO_LIMITS),
            "queries": list(QUERY_LIMITS),
        },
        "input_constraints_by_setting": {
            "left_to_right": "canonical generator grammar",
            "right_to_left": "same grammar; total staircase extent is order-invariant",
        },
        "episode_policy": {
            "setting_draws": 1,
            "demonstrations": demos,
            "queries": queries,
            "same_inputs_across_settings_for_evidence": True,
            "all_inputs_distinct": True,
            "rival_gate": (
                "fail when an alternate fits all demonstrations, regardless of query labels"
            ),
        },
        "public_identity": "sha256(reviewer_support.public_challenge_bytes(visible challenge))",
        "limitations": LIMITATIONS,
    }


def build_evidence(
    seed: int,
    settings: Iterable[Settings],
    *,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
) -> dict:
    seed = _validate_seed(seed)
    demos = _validate_count("demos", demos, DEMO_LIMITS)
    queries = _validate_count("queries", queries, QUERY_LIMITS)
    settings = tuple(settings)
    if not settings or any(not isinstance(value, Settings) for value in settings):
        raise ValueError("settings must be a nonempty iterable of Settings")
    if len(set(settings)) != len(settings):
        raise ValueError("settings must be unique")

    authority = authority_identity()
    if not authority["selected_exact_match"]:
        raise ValueError("selected target_code is not exact canonical program_solution")
    input_records = _sample_input_records(seed, count=demos + queries)

    with RacketLabels() as labels:
        episodes = [
            _episode(
                seed,
                setting,
                labels,
                demos=demos,
                queries=queries,
                input_records=input_records,
            )
            for setting in settings
        ]
        witness_input = input_records[0]["input"]
        witness_outputs = {
            setting.sort_order: labels.output(witness_input, setting)
            for setting in ALL_SETTINGS
        }
        runtime_identity = labels.runtime_identity
        racket_requests = labels.requests

    public_ids = [episode["public_id"] for episode in episodes]
    if len(public_ids) != len(set(public_ids)):
        raise ValueError("duplicate visible payload across requested settings")
    episodes.sort(key=lambda episode: episode["public_id"])

    distinct = len({digest(value) for value in witness_outputs.values()}) == len(
        ALL_SETTINGS
    )
    rivals_pass = all(
        rival["status"] == "refuted_by_demonstrations"
        for episode in episodes
        for rival in episode["rivals"]
    )
    evidence = {
        **_semantic_metadata(demos, queries),
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
            "demonstrations_per_episode": demos,
            "queries_per_episode": queries,
            "rival_checks": sum(len(episode["rivals"]) for episode in episodes),
            "racket_requests": racket_requests,
            "unique_program_input_executions": len(ALL_SETTINGS) * len(input_records),
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


def emit_bundle(
    seed: int,
    settings: Iterable[Settings],
    output,
    *,
    demos: int = DEFAULT_DEMOS,
    queries: int = DEFAULT_QUERIES,
) -> dict:
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    try:
        evidence = build_evidence(seed, settings, demos=demos, queries=queries)
        (output / "public").mkdir()
        (output / "private/rules").mkdir(parents=True)
        for rule in evidence["rules"]:
            path = _safe_relative(output, rule["path"])
            path.write_text(rule["program"])
        for episode in evidence["episodes"]:
            visible = public_episode(episode)
            payload = public_challenge_bytes(visible)
            identifier = public_challenge_id(visible)
            if identifier != episode["public_id"]:
                raise ValueError("private public_id differs from exact visible bytes")
            path = _safe_relative(output, episode["public_path"])
            if path.name != identifier + ".json":
                raise ValueError("public filename is not its exact visible-content ID")
            path.write_bytes(payload)
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
            "demonstrations_per_episode": demos,
            "queries_per_episode": queries,
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
    policy = evidence.get("episode_policy", {})
    demos = _validate_count("demos", policy.get("demonstrations"), DEMO_LIMITS)
    queries = _validate_count("queries", policy.get("queries"), QUERY_LIMITS)
    for key, value in _semantic_metadata(demos, queries).items():
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
        visible = public_episode(episode)
        identifier = public_challenge_id(visible)
        expected_path = f"public/{identifier}.json"
        if episode.get("public_id") != identifier or episode.get("public_path") != expected_path:
            raise ValueError("private public identity is not derived from exact visible bytes")
        path = _safe_relative(output, expected_path)
        if path.read_bytes() != public_challenge_bytes(visible):
            raise ValueError("public challenge bytes changed or are not canonical")
        public = json.loads(path.read_text())
        if public != visible:
            raise ValueError("public challenge changed")
        if set(public) != {"train", "test"}:
            raise ValueError("public challenge exposes unexpected top-level metadata")
        if len(public["train"]) != demos or len(public["test"]) != queries:
            raise ValueError("public challenge counts differ from the private request")
        if any(set(query) != {"input"} for query in public["test"]):
            raise ValueError("public query exposes more than its input")

    fresh = build_evidence(evidence["seed"], settings, demos=demos, queries=queries)
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
    emit.add_argument("--demos", type=int, default=DEFAULT_DEMOS)
    emit.add_argument("--queries", type=int, default=DEFAULT_QUERIES)
    emit.add_argument("--out", required=True)

    verify = subparsers.add_parser("verify", help="reexecute and verify a saved bundle")
    verify.add_argument("bundle")
    verify.add_argument("--out")

    args = parser.parse_args(argv)
    if args.command == "emit":
        settings = ALL_SETTINGS if args.all_settings else (
            select_settings(args.seed, sort_order=args.sort_order),
        )
        result = emit_bundle(
            args.seed,
            settings,
            args.out,
            demos=args.demos,
            queries=args.queries,
        )
    else:
        result = verify_bundle(args.bundle)
        if args.out:
            _write_json_exclusive(args.out, result)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
