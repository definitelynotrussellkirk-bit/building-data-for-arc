#!/usr/bin/env python3
"""Proposed axis-policy parameterization for ARC task 90082143f2ec.

This is deliberately task-local and non-production.  The canonical setting is
byte-for-byte the canonical Racket program.  The alternate setting changes
only which already-computed axis is selected.  Every answer is produced by an
actual Racket execution and checked against a Python component oracle derived from the unchanged selected generator's
semantic observables. This cross-check shares production observables; it is not
an independent implementation.
"""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

HERE = Path(__file__).resolve().parent
ROOT = find_root(__file__)
TASK_ID = "90082143f2ec"
AXIS_POLICIES = ("more_coherent", "less_coherent")
DEFAULT_AXIS_POLICY = "more_coherent"
RULE_VARIANTS = (
    "more_coherent",
    "less_coherent",
    "always_rows",
    "always_columns",
)
MIN_DEMOS = 3
MAX_DEMOS = 8
MIN_QUERIES = 1
MAX_QUERIES = 8
CANONICAL_RULE_HASH = "a86d1f36d1d2"
CANONICAL_SOURCE_SHA256 = "fce27c64e390c476ffe769e59766ad1fd179890f28233bf99a5c8176623b83e5"
_CANONICAL_CONDITION = "(if (> col-coherence row-coherence)"
_VARIANT_CONDITIONS = {
    "more_coherent": _CANONICAL_CONDITION,
    "less_coherent": "(if (< col-coherence row-coherence)",
    "always_rows": "(if #f",
    "always_columns": "(if #t",
}
# The canonical helper's tie order is an implementation detail of Racket hash
# iteration.  The canonical path never depends on it because every selected
# dominant slice has a strict mode.  Alternate/fixed-axis variants can select
# non-dominant slices, so they lexically shadow mode-list with the generator's
# explicit highest-count/lowest-color tie rule before changing the final branch.
_DETERMINISTIC_MODE = """(lambda (vals)
  (let* ((colors (remove-duplicates vals))
         (ranked (sort colors
                       (lambda (a b)
                         (let ((ca (count-if (lambda (v) (= v a)) vals))
                               (cb (count-if (lambda (v) (= v b)) vals)))
                           (or (> ca cb) (and (= ca cb) (< a b))))))))
    (first ranked)))"""


def _integer(name: str, value: Any, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a literal integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")
    return value


def _policy(value: Any) -> str:
    if not isinstance(value, str) or value not in AXIS_POLICIES:
        raise ValueError("axis_policy must be more_coherent or less_coherent")
    return value


def _variant(value: Any) -> str:
    if not isinstance(value, str) or value not in RULE_VARIANTS:
        raise ValueError("unknown rule variant")
    return value


def _text_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _value_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _copy_grid(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in grid]


@lru_cache(maxsize=1)
def generator():
    module, _path, _sha = load_selected_generator(TASK_ID, root=ROOT)
    return module


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs: list[str] = []
    with canonical_path(ROOT).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    if not programs or len(set(programs)) != 1:
        raise ValueError("exactly one canonical Racket authority is required")
    source = programs[0]
    if _text_sha256(source) != CANONICAL_SOURCE_SHA256:
        raise ValueError("exact canonical source SHA256 changed; review this prototype")
    normalized_hash = _text_sha256(" ".join(source.split()))[:12]
    if normalized_hash != CANONICAL_RULE_HASH:
        raise ValueError("canonical Racket authority changed; review this prototype")
    if source.count(_CANONICAL_CONDITION) != 1:
        raise ValueError("canonical coherence condition must occur exactly once")
    return source


@lru_cache(maxsize=len(RULE_VARIANTS))
def _program_for_variant(variant: str) -> str:
    variant = _variant(variant)
    source = canonical_program()
    if variant == DEFAULT_AXIS_POLICY:
        return source
    replacement = _VARIANT_CONDITIONS[variant]
    body = strip_rule_wrapper(source).replace(_CANONICAL_CONDITION, replacement, 1)
    return f"(rule! (let ((mode-list {_DETERMINISTIC_MODE}))\n  {body}))"


def program_for(axis_policy: str) -> str:
    """Return the exact program for one declared episode setting."""
    return _program_for_variant(_policy(axis_policy))


def choose_setting(seed: int) -> str:
    """Choose one fixed setting for the whole episode; paired seeds share inputs."""
    _integer("seed", seed, 0, 2**63 - 1)
    return AXIS_POLICIES[seed % len(AXIS_POLICIES)]


def _validate_counts(demos: int, queries: int) -> tuple[int, int]:
    return (
        _integer("demos", demos, MIN_DEMOS, MAX_DEMOS),
        _integer("queries", queries, MIN_QUERIES, MAX_QUERIES),
    )


def _sample_inputs(
    seed: int,
    *,
    demos: int,
    queries: int,
    difficulty: str | None,
) -> tuple[list[list[list[int]]], list[int]]:
    _integer("seed", seed, 0, 2**63 - 1)
    demos, queries = _validate_counts(demos, queries)
    if difficulty not in (None, "easy", "medium", "hard"):
        raise ValueError(f"unknown difficulty: {difficulty!r}")

    # Adjacent seeds are an A/B pair: setting parity changes, while the input
    # block stays identical.  The selected generator's declared schedule makes
    # every three consecutive slots contain both row- and column-dominant scenes.
    block_seed = seed // 2
    count = demos + queries
    grids: list[list[list[int]]] = []
    indices: list[int] = []
    seen: set[str] = set()
    candidate = 0
    max_attempts = count * 16
    while len(grids) < count and candidate < max_attempts:
        grid = generator().generate(
            block_seed,
            candidate,
            difficulty=difficulty,
        )
        errors = generator().self_check(grid, difficulty=difficulty)
        key = _value_sha256(grid)
        if not errors and key not in seen:
            facts = generator().semantic_observables(grid)
            if not facts.get("axis_answers_differ"):
                raise AssertionError("selected generator admitted an axis-degenerate scene")
            grids.append(_copy_grid(grid))
            indices.append(candidate)
            seen.add(key)
        candidate += 1
    if len(grids) != count:
        raise RuntimeError(
            f"sampling budget exhausted: accepted {len(grids)}/{count} distinct inputs"
        )
    demo_orientations = {
        generator().semantic_observables(grid)["orientation"] for grid in grids[:demos]
    }
    if demo_orientations != {"vertical", "horizontal"}:
        raise RuntimeError("demonstrations do not cover both coherence orientations")
    return grids, indices


def episode_inputs(
    seed: int,
    *,
    demos: int = 3,
    queries: int = 4,
    difficulty: str | None = "medium",
) -> list[list[list[int]]]:
    """Return only the deterministic lawful inputs for an episode."""
    grids, _indices = _sample_inputs(
        seed, demos=demos, queries=queries, difficulty=difficulty
    )
    return grids


def _python_variant_output(grid: list[list[int]], variant: str) -> list[list[int]]:
    """Component cross-check using the generator's exposed observables."""
    variant = _variant(variant)
    facts = generator().semantic_observables(grid)
    errors = facts.get("errors", [])
    if errors:
        raise ValueError("malformed input: " + "; ".join(errors))
    orientation = facts["orientation"]
    if variant == "more_coherent":
        output = facts["clean"]
    elif variant == "less_coherent":
        output = facts["alternate"]
    elif variant == "always_rows":
        output = facts["clean"] if orientation == "horizontal" else facts["alternate"]
    else:  # always_columns
        output = facts["clean"] if orientation == "vertical" else facts["alternate"]
    return copy.deepcopy(output)


def _racket_literal(grid: list[list[int]]) -> str:
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
    return "'(" + rows + ")"


def _validate_output(
    value: Any, *, expected_rows: int, expected_cols: int
) -> list[list[int]]:
    if type(value) is not list or len(value) != expected_rows:
        raise ValueError("Racket returned an output with the wrong row count")
    if any(type(row) is not list or len(row) != expected_cols for row in value):
        raise ValueError("Racket returned a nonrectangular or wrong-width output")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in value for cell in row):
        raise ValueError("Racket returned a non-ARC cell")
    return _copy_grid(value)


class RuleEngine:
    """Own one protected Racket bridge and retain content-bound execution records."""

    def __init__(self) -> None:
        self.bridge = RacketBridge(timeout=10.0, startup_timeout=30.0)
        self.executions: list[dict[str, Any]] = []
        self._closed = False

    def __enter__(self) -> "RuleEngine":
        return self

    def __exit__(self, *_error: object) -> bool:
        self.close()
        return False

    def close(self) -> None:
        if not self._closed:
            self.bridge.close()
            self._closed = True

    def apply(self, grid: list[list[int]], variant: str) -> list[list[int]]:
        if self._closed:
            raise RuntimeError("RuleEngine is closed")
        variant = _variant(variant)
        errors = generator().self_check(grid)
        if errors:
            raise ValueError("input outside prototype domain: " + "; ".join(errors))
        source = _program_for_variant(variant)
        callable_source = strip_rule_wrapper(strip_line_comments(source))
        if not callable_source.lstrip().startswith(("(lambda", "(let")):
            raise ValueError("prototype only supports its exact callable rules")
        raw = self.bridge.eval_text(f"({callable_source} {_racket_literal(grid)})")
        output = _validate_output(
            raw, expected_rows=len(grid), expected_cols=len(grid[0])
        )
        mirror = _python_variant_output(grid, variant)
        if output != mirror:
            raise ValueError(f"Racket and generator-derived component oracle disagree for {variant}")
        self.executions.append(
            {
                "call_index": len(self.executions),
                "variant": variant,
                "input_sha256": _value_sha256(grid),
                "output_sha256": _value_sha256(output),
                "program_sha256": _text_sha256(source),
                "generator_component_oracle_match": True,
            }
        )
        return output


def _source_identity() -> dict[str, str]:
    paths = [
        ROOT / "generators" / TASK_ID / "generator.py",
        canonical_path(ROOT),
        HERE / "prototype.py",
        HERE / "adapter.py",
        HERE / "promotion.json",
        HERE / "README.md",
        ROOT / "generators" / TASK_ID / "tests" / "test_parametric_axis_policy.py",
    ]
    return {
        str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }


def _make_episode(
    *,
    seed: int,
    selected: str,
    demos: int,
    queries: int,
    difficulty: str | None,
    inputs: list[list[list[int]]],
    indices: list[int],
    engine: RuleEngine,
) -> dict[str, Any]:
    outputs: dict[str, list[list[list[int]]]] = {}
    records: dict[str, list[dict[str, Any]]] = {}
    for variant in RULE_VARIANTS:
        variant_outputs: list[list[list[int]]] = []
        variant_records: list[dict[str, Any]] = []
        for grid in inputs:
            variant_outputs.append(engine.apply(grid, variant))
            variant_records.append(copy.deepcopy(engine.executions[-1]))
        outputs[variant] = variant_outputs
        records[variant] = variant_records

    selected_outputs = outputs[selected]
    train = [
        {"input": _copy_grid(inputs[index]), "output": _copy_grid(selected_outputs[index])}
        for index in range(demos)
    ]
    test = [
        {
            "input": _copy_grid(inputs[demos + index]),
            "output": _copy_grid(selected_outputs[demos + index]),
        }
        for index in range(queries)
    ]

    # This certificate fits every declared rival to demonstrations first.  Query
    # outputs are inspected only after the fit set is closed.
    rivals: list[dict[str, Any]] = []
    consistent: list[str] = []
    for variant in RULE_VARIANTS:
        mismatches = [
            index
            for index in range(demos)
            if outputs[variant][index] != selected_outputs[index]
        ]
        fits = not mismatches
        if fits:
            consistent.append(variant)
        rivals.append(
            {
                "variant": variant,
                "fits_demonstrations": fits,
                "mismatching_demo_indices": mismatches,
            }
        )

    reports: list[dict[str, Any]] = []
    for query_index in range(queries):
        absolute = demos + query_index
        query_predictions = {
            variant: _value_sha256(outputs[variant][absolute])
            for variant in RULE_VARIANTS
        }
        reports.append(
            {
                "query_index": query_index,
                "query_input_sha256": _value_sha256(inputs[absolute]),
                "consistent_variants": list(consistent),
                "status": (
                    "identified_within_declared_rivals"
                    if consistent == [selected]
                    else "ambiguous_within_declared_rivals"
                ),
                "determined_output_sha256": (
                    query_predictions[selected] if consistent == [selected] else None
                ),
                "query_answer_used_for_demo_fit": False,
                "rivals": [
                    dict(
                        rival,
                        query_prediction_sha256=query_predictions[rival["variant"]],
                    )
                    for rival in rivals
                ],
            }
        )
    if any(report["status"] != "identified_within_declared_rivals" for report in reports):
        raise RuntimeError("demonstrations do not uniquely identify the fixed episode setting")

    return {
        "schema": "axis-policy-parametric-prototype-v1",
        "status": "proposed",
        "approved": False,
        "training_admitted": False,
        "task_id": TASK_ID,
        "seed": seed,
        "input_pair_block": seed // 2,
        "axis_policy": selected,
        "difficulty": difficulty,
        "demo_count": demos,
        "query_count": queries,
        "accepted_sample_indices": indices,
        "train": train,
        "test": test,
        "program_solution": program_for(selected),
        "program_sha256": _text_sha256(program_for(selected)),
        "canonical_normalized_rule_hash": CANONICAL_RULE_HASH,
        "source_sha256": _source_identity(),
        "query_identification": reports,
        "variant_executions": records,
    }


def generate_episode(
    seed: int,
    *,
    axis_policy: str | None = None,
    demos: int = 3,
    queries: int = 4,
    difficulty: str | None = "medium",
    engine: RuleEngine | None = None,
) -> dict[str, Any]:
    _integer("seed", seed, 0, 2**63 - 1)
    demos, queries = _validate_counts(demos, queries)
    selected = choose_setting(seed) if axis_policy is None else _policy(axis_policy)
    inputs, indices = _sample_inputs(
        seed, demos=demos, queries=queries, difficulty=difficulty
    )
    if engine is None:
        with RuleEngine() as active:
            return _make_episode(
                seed=seed,
                selected=selected,
                demos=demos,
                queries=queries,
                difficulty=difficulty,
                inputs=inputs,
                indices=indices,
                engine=active,
            )
    return _make_episode(
        seed=seed,
        selected=selected,
        demos=demos,
        queries=queries,
        difficulty=difficulty,
        inputs=inputs,
        indices=indices,
        engine=engine,
    )


def public_payload(episode: dict[str, Any]) -> dict[str, Any]:
    """Project exactly the visible challenge; private answers never participate."""
    return {
        "train": [
            {
                "input": copy.deepcopy(pair["input"]),
                "output": copy.deepcopy(pair["output"]),
            }
            for pair in episode["train"]
        ],
        "test": [
            {"input": copy.deepcopy(pair["input"])} for pair in episode["test"]
        ],
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    return public_challenge_bytes(public_payload(episode))


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(public_payload(episode))


def _validate_episode(episode: dict[str, Any], engine: RuleEngine) -> None:
    selected = _policy(episode["axis_policy"])
    if episode.get("task_id") != TASK_ID:
        raise ValueError("episode task_id mismatch")
    if episode.get("source_sha256") != _source_identity():
        raise ValueError("source identity changed; regenerate the episode")
    expected_program = program_for(selected)
    if (
        episode.get("program_solution") != expected_program
        or episode.get("program_sha256") != _text_sha256(expected_program)
    ):
        raise ValueError("episode rule provenance disagrees with its materialized rule")
    seed = _integer("seed", episode["seed"], 0, 2**63 - 1)
    demos, queries = _validate_counts(episode["demo_count"], episode["query_count"])
    if len(episode["train"]) != demos or len(episode["test"]) != queries:
        raise ValueError("episode counts disagree with serialized pairs")
    inputs, indices = _sample_inputs(
        seed, demos=demos, queries=queries, difficulty=episode["difficulty"],
    )
    if ([pair["input"] for pair in episode["train"] + episode["test"]] != inputs
            or episode.get("accepted_sample_indices") != indices):
        raise ValueError("episode inputs disagree with deterministic sampling provenance")
    expected = _make_episode(
        seed=seed, selected=selected, demos=demos, queries=queries,
        difficulty=episode["difficulty"], inputs=inputs, indices=indices, engine=engine,
    )
    for split in ("train", "test"):
        for index, pair in enumerate(episode[split]):
            if pair["output"] != expected[split][index]["output"]:
                raise ValueError(f"label mismatch at {split}[{index}]")
    if episode.get("query_identification") != expected["query_identification"]:
        raise ValueError("episode identification certificate disagrees with Racket replay")



def _write_one(destination: Path, episode: dict[str, Any]) -> dict[str, str]:
    identifier = public_id(episode)
    payload = public_bytes(episode)
    public_path = destination / "public" / f"{identifier}.json"
    private_path = destination / "private" / "episodes" / f"{identifier}.json"
    rule_hash = _text_sha256(episode["program_solution"])
    rule_path = destination / "private" / "rules" / f"{rule_hash}.rkt"
    for path in (public_path, private_path, rule_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    if public_path.exists() and public_path.read_bytes() != payload:
        raise ValueError("visible-content hash collision or existing file corruption")
    public_path.write_bytes(payload)
    private_path.write_text(
        json.dumps(episode, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    rule_path.write_text(episode["program_solution"], encoding="utf-8")
    return {
        "public_id": identifier,
        "public_path": str(public_path),
        "private_path": str(private_path),
        "rule_path": str(rule_path),
    }


def write_episodes(
    destination: Path | str,
    episodes: Iterable[dict[str, Any]],
    *,
    engine: RuleEngine | None = None,
) -> list[dict[str, str]]:
    """Reject duplicate visible payloads, validate all labels, then write in a second phase."""
    destination = Path(destination)
    projected: list[tuple[str, bytes, dict[str, Any]]] = []
    seen: dict[str, bytes] = {}
    for episode in episodes:
        payload = public_bytes(episode)
        identifier = hashlib.sha256(payload).hexdigest()
        previous = seen.get(identifier)
        if previous is not None:
            if previous == payload:
                raise ValueError("duplicate visible payload in episode batch")
            raise ValueError("visible-content hash collision in episode batch")
        seen[identifier] = payload
        projected.append((identifier, payload, episode))
    if not projected:
        raise ValueError("empty episode batch")
    projected.sort(key=lambda row: row[0])
    if destination.exists():
        raise FileExistsError(destination)
    if engine is None:
        with RuleEngine() as active:
            return write_episodes(
                destination, [row[2] for row in projected], engine=active
            )
    for _identifier, _payload, episode in projected:
        _validate_episode(episode, engine)
    return [_write_one(destination, episode) for _, _, episode in projected]


def retain_evidence(
    destination: Path | str,
    *,
    pair_seed: int = 0,
    demos: int = 3,
    queries: int = 4,
    difficulty: str | None = "medium",
) -> dict[str, Any]:
    """Generate a paired A/B batch and retain public/private artifacts plus proof."""
    _integer("pair_seed", pair_seed, 0, 2**62 - 1)
    destination = Path(destination)
    first_seed = pair_seed * 2
    second_seed = first_seed + 1
    with RuleEngine() as engine:
        episodes = [
            generate_episode(
                first_seed,
                axis_policy="more_coherent",
                demos=demos,
                queries=queries,
                difficulty=difficulty,
                engine=engine,
            ),
            generate_episode(
                second_seed,
                axis_policy="less_coherent",
                demos=demos,
                queries=queries,
                difficulty=difficulty,
                engine=engine,
            ),
        ]
        written = write_episodes(destination, episodes, engine=engine)
        by_id = {row["public_id"]: row for row in written}
        report = {
            "schema": "axis-policy-parametric-evidence-v1",
            "status": "proposed",
            "approved": False,
            "training_admitted": False,
            "task_id": TASK_ID,
            "parameter": {
                "name": "axis_policy",
                "values": list(AXIS_POLICIES),
                "canonical_default": DEFAULT_AXIS_POLICY,
                "episode_choice": "seed parity; adjacent seeds share one input block",
            },
            "pair_seed": pair_seed,
            "demo_count": demos,
            "query_count": queries,
            "difficulty": difficulty,
            "canonical_normalized_rule_hash": CANONICAL_RULE_HASH,
            "program_sha256": {
                policy: _text_sha256(program_for(policy)) for policy in AXIS_POLICIES
            },
            "source_sha256": _source_identity(),
            "episodes": [
                {
                    "seed": episode["seed"],
                    "axis_policy": episode["axis_policy"],
                    "public_id": public_id(episode),
                    "accepted_sample_indices": episode["accepted_sample_indices"],
                    "query_identification": episode["query_identification"],
                    "paths": {
                        key: str(Path(value).relative_to(destination))
                        for key, value in by_id[public_id(episode)].items()
                        if key != "public_id"
                    },
                }
                for episode in episodes
            ],
            "paired_inputs_identical": [
                pair["input"]
                for pair in episodes[0]["train"] + episodes[0]["test"]
            ]
            == [
                pair["input"]
                for pair in episodes[1]["train"] + episodes[1]["test"]
            ],
            "all_selected_outputs_differ": all(
                left["output"] != right["output"]
                for left, right in zip(
                    episodes[0]["train"] + episodes[0]["test"],
                    episodes[1]["train"] + episodes[1]["test"],
                    strict=True,
                )
            ),
            "racket_execution_count": len(engine.executions),
            "limits": [
                "Proposed task-local extension; no production generator, canonical ledger, approval, or training-admission change.",
                "Identification is certified only against the four declared variants: both policies and two fixed-axis shortcuts.",
                "Inputs stay inside the unchanged selected generator's current lawful domain and finite schedule.",
                "The evidence covers the retained paired episodes, not every possible episode.",
            ],
        }
        if not report["paired_inputs_identical"] or not report["all_selected_outputs_differ"]:
            raise RuntimeError("paired parameter witness did not cleanly isolate axis_policy")
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "summary.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        private = destination / "private"
        private.mkdir(parents=True, exist_ok=True)
        (private / "racket-executions.json").write_text(
            json.dumps(engine.executions, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair-seed", type=int, default=0)
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--difficulty", choices=("easy", "medium", "hard"), default="medium")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = retain_evidence(
        args.out,
        pair_seed=args.pair_seed,
        demos=args.demos,
        queries=args.queries,
        difficulty=args.difficulty,
    )
    print(json.dumps({
        "status": report["status"],
        "episodes": [row["public_id"] for row in report["episodes"]],
        "racket_execution_count": report["racket_execution_count"],
        "out": str(args.out),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
