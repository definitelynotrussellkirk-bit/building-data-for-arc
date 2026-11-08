#!/usr/bin/env python3
"""Task-local prototype for an episode-fixed quarter-turn rule parameter."""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from reviewer_support import (
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "88b8e6aaa49d"
PROTOTYPE_VERSION = "quarter-turns-prototype-v1"
ALLOWED_QUARTER_TURNS = (1, 2, 3)
DEFAULT_QUARTER_TURNS = 2
MAX_DEMOS = 16
MAX_QUERIES = 16
DEFAULT_MAX_ATTEMPTS = 256
CANONICAL_RULE_HASH = "d4b6baaa86e7"

_RULES = {
    1: "(rule! (lambda (g) (rotate-cw g)))",
    2: "(rule! (lambda (g) (flip-ud (flip-lr g))))",
    3: "(rule! (lambda (g) (rotate-ccw g)))",
}


def stable_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def digest(value: Any) -> str:
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_quarter_turns(value: Any) -> int:
    if type(value) is not int or value not in ALLOWED_QUARTER_TURNS:
        raise ValueError(
            f"quarter_turns must be one of {ALLOWED_QUARTER_TURNS}, got {value!r}"
        )
    return value


@lru_cache(maxsize=1)
def canonical_rule_source() -> str:
    """Load and content-bind the approved default from the canonical ledger."""
    ledger = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    matches: list[dict[str, Any]] = []
    with ledger.open(encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.strip():
                continue
            row = json.loads(raw)
            if row.get("task_id") == TASK_ID:
                row["_line_number"] = line_number
                matches.append(row)
    if len(matches) != 1:
        raise RuntimeError(
            f"expected exactly one canonical row for {TASK_ID}, found {len(matches)}"
        )
    source = matches[0].get("program_solution")
    if not isinstance(source, str) or not source:
        raise RuntimeError("canonical row has no program_solution")
    if text_digest(source)[: len(CANONICAL_RULE_HASH)] != CANONICAL_RULE_HASH:
        raise RuntimeError("canonical rule hash changed; review the parameter family")
    if source != _RULES[DEFAULT_QUARTER_TURNS]:
        raise RuntimeError("declared default is not byte-identical to the canonical rule")
    return source


def rule_source(quarter_turns: Any) -> str:
    """Return the exact Racket rule for one fixed episode setting."""
    turns = _validate_quarter_turns(quarter_turns)
    if turns == DEFAULT_QUARTER_TURNS:
        return canonical_rule_source()
    return _RULES[turns]


def _validate_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a non-empty list of non-empty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(cell) is not int or not 0 <= cell <= 9 for row in grid for cell in row):
        raise ValueError("grid cells must be literal ARC colors 0..9")
    return len(grid), width


def python_mirror(grid: list[list[int]], quarter_turns: Any) -> list[list[int]]:
    """Independent Python mirror used to cross-check executed Racket labels."""
    turns = _validate_quarter_turns(quarter_turns)
    _validate_grid(grid)
    if turns == 1:
        return [list(row) for row in zip(*reversed(grid))]
    if turns == 2:
        return [list(reversed(row)) for row in reversed(grid)]
    return [list(row) for row in reversed(list(zip(*grid)))]


class RuleEngine:
    """Execute materialized rules through the protected persistent Racket bridge."""

    backend = "racket"

    def __init__(self, *, timeout: float = 10.0):
        from arc_repl.racket_bridge import RacketBridge

        self.bridge = RacketBridge(timeout=timeout, max_calls_before_restart=128)
        self.runtime_identity = self.bridge.runtime_identity
        self.executions: list[dict[str, Any]] = []
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def close(self) -> None:
        if not self._closed:
            self.bridge.shutdown()
            self._closed = True

    def apply(self, grid: list[list[int]], quarter_turns: Any) -> list[list[int]]:
        from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper

        turns = _validate_quarter_turns(quarter_turns)
        _validate_grid(grid)
        domain_reasons = list(generator().self_check(grid))
        if domain_reasons:
            raise ValueError(f"input is outside the canonical generator domain: {domain_reasons}")
        source = rule_source(turns)
        callable_source = strip_rule_wrapper(strip_line_comments(source))
        self.bridge.define_grid("__parametric_input", grid)
        output = self.bridge.eval_text(f"({callable_source} __parametric_input)")
        _validate_grid(output)
        output = [list(row) for row in output]
        self.executions.append(
            {
                "call_index": len(self.executions),
                "backend": self.backend,
                "quarter_turns": turns,
                "input_sha256": digest(grid),
                "output_sha256": digest(output),
                "program_sha256": text_digest(source),
                "runtime_identity_sha256": digest(self.runtime_identity),
            }
        )
        return output


@lru_cache(maxsize=1)
def _selected_generator():
    return load_selected_generator(TASK_ID, root=ROOT)


def generator():
    """Load the selected canonical input generator from this exact source tree."""
    return _selected_generator()[0]


def generator_source_sha256() -> str:
    return _selected_generator()[2]


def _integer(name: str, value: Any, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a literal integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")
    return value


def choose_setting(seed: Any) -> int:
    """Choose the hidden rotation once, independently of pair counts and inputs."""
    seed = _integer("seed", seed, 0, 2**63 - 1)
    key = f"{PROTOTYPE_VERSION}:rule:{seed}".encode("utf-8")
    return ALLOWED_QUARTER_TURNS[hashlib.sha256(key).digest()[0] % len(ALLOWED_QUARTER_TURNS)]


def _sample_inputs(seed: int, count: int, max_attempts: int):
    selected = generator()
    accepted: list[list[list[int]]] = []
    accepted_indices: list[int] = []
    rejected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for sample_index in range(max_attempts):
        grid = selected.generate(seed, sample_index)
        reasons = list(selected.self_check(grid))
        key = digest(grid)
        if key in seen:
            reasons.append("duplicate input")
        outputs = [python_mirror(grid, turns) for turns in ALLOWED_QUARTER_TURNS]
        if len({digest(output) for output in outputs}) != len(ALLOWED_QUARTER_TURNS):
            reasons.append("input does not distinguish all quarter-turn settings")
        if reasons:
            rejected.append({"sample_index": sample_index, "reasons": reasons})
            continue
        seen.add(key)
        accepted.append(deepcopy(grid))
        accepted_indices.append(sample_index)
        if len(accepted) == count:
            return accepted, accepted_indices, rejected
    raise RuntimeError(
        f"sampling budget exhausted: accepted {len(accepted)} distinct inputs of {count} "
        f"requested after {max_attempts} attempts"
    )


def identify_query(demonstrations, query_input, *, engine) -> dict[str, Any]:
    """Fit declared settings on demonstrations only, then compare query predictions."""
    if not isinstance(demonstrations, (list, tuple)):
        raise TypeError("demonstrations must be a list or tuple")
    if generator().self_check(query_input):
        raise ValueError("query input is outside the prototype domain")

    rivals: list[dict[str, Any]] = []
    consistent: list[int] = []
    for turns in ALLOWED_QUARTER_TURNS:
        mismatches: list[int] = []
        for index, pair in enumerate(demonstrations):
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                raise ValueError(f"demonstration {index} must contain input and output")
            if engine.apply(pair["input"], turns) != pair["output"]:
                mismatches.append(index)
        if not mismatches:
            consistent.append(turns)
        rivals.append(
            {
                "quarter_turns": turns,
                "fits_demonstrations": not mismatches,
                "mismatching_demo_indices": mismatches,
            }
        )

    predictions: dict[int, str] = {}
    for row in rivals:
        turns = row["quarter_turns"]
        prediction_hash = digest(engine.apply(query_input, turns))
        predictions[turns] = prediction_hash
        row["query_prediction_sha256"] = prediction_hash

    identified = len(consistent) == 1
    return {
        "status": (
            "identified_within_declared_rivals"
            if identified
            else "ambiguous_within_declared_rivals"
        ),
        "query_input_sha256": digest(query_input),
        "consistent_settings": consistent,
        "determined_output_sha256": predictions[consistent[0]] if identified else None,
        "query_answer_used_for_demo_fit": False,
        "rivals": rivals,
    }


def _checked_label(engine, grid, quarter_turns: int, split: str, index: int):
    output = engine.apply(grid, quarter_turns)
    mirror = python_mirror(grid, quarter_turns)
    if output != mirror:
        raise ValueError(f"Racket/Python mirror disagreement at {split}[{index}]")
    evidence = {
        "split": split,
        "index": index,
        "quarter_turns": quarter_turns,
        "input_sha256": digest(grid),
        "output_sha256": digest(output),
        "program_sha256": text_digest(rule_source(quarter_turns)),
        "backend": getattr(engine, "backend", "test-mirror"),
        "python_mirror_match": True,
    }
    return {"input": deepcopy(grid), "output": output}, evidence


def generate_episode(
    seed,
    *,
    quarter_turns=None,
    demos: int = 3,
    queries: int = 4,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    engine=None,
) -> dict[str, Any]:
    """Build one proposed episode with a single fixed hidden rotation setting."""
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 1, MAX_DEMOS)
    queries = _integer("queries", queries, 1, MAX_QUERIES)
    max_attempts = _integer("max_attempts", max_attempts, 1, 10_000)
    selected = choose_setting(seed) if quarter_turns is None else _validate_quarter_turns(quarter_turns)
    if engine is None:
        with RuleEngine() as owned_engine:
            return generate_episode(
                seed,
                quarter_turns=selected,
                demos=demos,
                queries=queries,
                max_attempts=max_attempts,
                engine=owned_engine,
            )

    inputs, indices, rejected = _sample_inputs(seed, demos + queries, max_attempts)
    train: list[dict[str, Any]] = []
    test: list[dict[str, Any]] = []
    label_checks: list[dict[str, Any]] = []
    query_reports: list[dict[str, Any]] = []

    for index, grid in enumerate(inputs[:demos]):
        pair, check = _checked_label(engine, grid, selected, "train", index)
        train.append(pair)
        label_checks.append(check)

    for index, grid in enumerate(inputs[demos:]):
        report = identify_query(train, grid, engine=engine)
        if report["consistent_settings"] != [selected]:
            raise RuntimeError("demonstrations do not identify the fixed episode setting")
        pair, check = _checked_label(engine, grid, selected, "test", index)
        if report["determined_output_sha256"] != digest(pair["output"]):
            raise ValueError("demonstration-derived prediction disagrees with executed label")
        test.append(pair)
        label_checks.append(check)
        query_reports.append({**report, "query_index": index})

    source = rule_source(selected)
    return {
        "schema": "arc-rotation-parametric-prototype-v1",
        "status": "proposed",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "quarter_turns": selected,
        "demo_count": demos,
        "query_count": queries,
        "max_attempts": max_attempts,
        "accepted_sample_indices": indices,
        "rejected_draws": rejected,
        "train": train,
        "test": test,
        "program_solution": source,
        "program_sha256": text_digest(source),
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "generator_source_sha256": generator_source_sha256(),
        "label_checks": label_checks,
        "query_identification": query_reports,
    }


def public_bytes(episode: dict[str, Any]) -> bytes:
    """Return the exact visible bytes used for both public files and IDs."""
    return public_challenge_bytes(episode)


def public_id(episode: dict[str, Any]) -> str:
    return public_challenge_id(episode)


def _validate_episode(episode: dict[str, Any], *, engine) -> None:
    if not isinstance(episode, dict):
        raise TypeError("episode must be a dictionary")
    if episode.get("task_id") != TASK_ID:
        raise ValueError("episode task identity mismatch")
    turns = _validate_quarter_turns(episode.get("quarter_turns"))
    if episode.get("program_solution") != rule_source(turns):
        raise ValueError("episode program does not match its quarter-turn setting")
    if episode.get("program_sha256") != text_digest(rule_source(turns)):
        raise ValueError("episode program hash mismatch")
    if episode.get("generator_source_sha256") != generator_source_sha256():
        raise ValueError("selected generator source changed; regenerate the episode")

    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode train/test must be lists")
    if episode.get("demo_count") != len(train) or episode.get("query_count") != len(test):
        raise ValueError("episode count metadata does not match its pairs")
    if not train or not test:
        raise ValueError("episode requires at least one demonstration and query")

    all_inputs = [pair.get("input") for pair in train + test if isinstance(pair, dict)]
    if len(all_inputs) != len(train) + len(test):
        raise ValueError("every pair must be a dictionary with an input")
    if len({digest(grid) for grid in all_inputs}) != len(all_inputs):
        raise ValueError("episode inputs must be distinct")

    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            if "output" not in pair:
                raise ValueError(f"missing private label at {split_name}[{index}]")
            actual = engine.apply(pair["input"], turns)
            if actual != pair["output"] or actual != python_mirror(pair["input"], turns):
                raise ValueError(f"label mismatch at {split_name}[{index}]")

    for index, pair in enumerate(test):
        report = identify_query(train, pair["input"], engine=engine)
        if report["consistent_settings"] != [turns]:
            raise ValueError(f"demonstrations do not identify setting for test[{index}]")
        if report["determined_output_sha256"] != digest(pair["output"]):
            raise ValueError(f"demonstration-derived label mismatch at test[{index}]")


def write_episodes(destination, episodes, *, engine=None) -> list[dict[str, str]]:
    """Validate a batch, reject visible duplicates, then export in public-ID order."""
    if not isinstance(episodes, (list, tuple)) or not episodes:
        raise ValueError("episodes must be a nonempty list or tuple")
    if engine is None:
        with RuleEngine() as owned_engine:
            return write_episodes(destination, episodes, engine=owned_engine)

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

    projected.sort(key=lambda row: row[0])
    for _, _, episode in projected:
        _validate_episode(episode, engine=engine)

    destination = Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError(f"output directory is not empty: {destination}")

    records: list[dict[str, str]] = []
    for identifier, payload, episode in projected:
        public_path = destination / "public" / f"{identifier}.json"
        private_path = destination / "private" / "episodes" / f"{identifier}.json"
        rule_path = destination / "private" / "rules" / f"{episode['program_sha256']}.rkt"
        public_path.parent.mkdir(parents=True, exist_ok=True)
        private_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        public_path.write_bytes(payload)
        private_path.write_text(
            json.dumps(episode, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        if rule_path.exists() and rule_path.read_text(encoding="utf-8") != episode["program_solution"]:
            raise ValueError("rule hash collision or existing rule corruption")
        rule_path.write_text(episode["program_solution"], encoding="utf-8")
        records.append(
            {
                "public_id": identifier,
                "public_path": str(public_path),
                "private_path": str(private_path),
                "rule_path": str(rule_path),
            }
        )
    return records


def _file_receipt(path: Path) -> dict[str, Any]:
    payload = path.read_bytes()
    return {"sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def source_identity() -> dict[str, str]:
    """Return exact source identities needed to reproduce this prototype."""
    paths = {
        "prototype_sha256": HERE / "prototype.py",
        "adapter_sha256": HERE / "adapter.py",
        "promotion_sha256": HERE / "promotion.json",
    }
    identities = {
        name: hashlib.sha256(path.read_bytes()).hexdigest()
        for name, path in paths.items()
    }
    identities.update(
        {
            "generator_source_sha256": generator_source_sha256(),
            "canonical_program_sha256": text_digest(canonical_rule_source()),
        }
    )
    return identities


def build_evidence(
    destination,
    *,
    seed: int = 17,
    demos: int = 3,
    queries: int = 4,
    settings=ALLOWED_QUARTER_TURNS,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    engine=None,
) -> dict[str, Any]:
    """Generate paired settings and retain public/private reproducibility evidence."""
    seed = _integer("seed", seed, 0, 2**63 - 1)
    demos = _integer("demos", demos, 1, MAX_DEMOS)
    queries = _integer("queries", queries, 1, MAX_QUERIES)
    max_attempts = _integer("max_attempts", max_attempts, 1, 10_000)
    if not isinstance(settings, (list, tuple)) or not settings:
        raise ValueError("settings must be a nonempty list or tuple")
    selected_settings = tuple(_validate_quarter_turns(value) for value in settings)
    if len(set(selected_settings)) != len(selected_settings):
        raise ValueError("settings must not contain duplicates")
    if engine is None:
        with RuleEngine() as owned_engine:
            return build_evidence(
                destination,
                seed=seed,
                demos=demos,
                queries=queries,
                settings=selected_settings,
                max_attempts=max_attempts,
                engine=owned_engine,
            )

    episodes = [
        generate_episode(
            seed,
            quarter_turns=turns,
            demos=demos,
            queries=queries,
            max_attempts=max_attempts,
            engine=engine,
        )
        for turns in selected_settings
    ]
    destination = Path(destination)
    records = write_episodes(destination, episodes, engine=engine)
    records_by_id = {row["public_id"]: row for row in records}

    episode_rows: list[dict[str, Any]] = []
    input_sequences: list[list[str]] = []
    for episode in episodes:
        identifier = public_id(episode)
        source_record = records_by_id[identifier]
        input_hashes = [
            digest(pair["input"]) for pair in episode["train"] + episode["test"]
        ]
        input_sequences.append(input_hashes)
        backends = sorted({check["backend"] for check in episode["label_checks"]})
        episode_rows.append(
            {
                "quarter_turns": episode["quarter_turns"],
                "program_sha256": episode["program_sha256"],
                "public_id": identifier,
                "public_path": str(Path(source_record["public_path"]).relative_to(destination)),
                "private_path": str(Path(source_record["private_path"]).relative_to(destination)),
                "rule_path": str(Path(source_record["rule_path"]).relative_to(destination)),
                "demo_count": episode["demo_count"],
                "query_count": episode["query_count"],
                "accepted_sample_indices": episode["accepted_sample_indices"],
                "input_sha256s": input_hashes,
                "label_backend": backends[0] if len(backends) == 1 else backends,
                "all_queries_identified": all(
                    report["consistent_settings"] == [episode["quarter_turns"]]
                    and report["query_answer_used_for_demo_fit"] is False
                    for report in episode["query_identification"]
                ),
            }
        )

    first_outputs = {
        str(episode["quarter_turns"]): digest(episode["train"][0]["output"])
        for episode in episodes
    }
    execution_rows = []
    for row in getattr(engine, "executions", []):
        execution_rows.append(row if isinstance(row, dict) else {"test_double_record": repr(row)})
    private_execution_path = destination / "private" / "engine-executions.json"
    private_execution_path.parent.mkdir(parents=True, exist_ok=True)
    private_execution_path.write_text(
        json.dumps(execution_rows, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    report = {
        "schema": "arc-rotation-parametric-evidence-v1",
        "status": "proposed_unapproved",
        "task_id": TASK_ID,
        "prototype_version": PROTOTYPE_VERSION,
        "seed": seed,
        "settings": list(selected_settings),
        "default_quarter_turns": DEFAULT_QUARTER_TURNS,
        "demo_count": demos,
        "query_count": queries,
        "canonical_default_exact": rule_source(DEFAULT_QUARTER_TURNS)
        == canonical_rule_source(),
        "shared_input_sequence": len({tuple(row) for row in input_sequences}) == 1,
        "all_queries_identified": all(row["all_queries_identified"] for row in episode_rows),
        "distinct_public_ids": len({row["public_id"] for row in episode_rows})
        == len(episode_rows),
        "cross_setting_first_output_sha256": first_outputs,
        "cross_setting_first_output_distinct": len(set(first_outputs.values()))
        == len(first_outputs),
        "source_identity": source_identity(),
        "engine_backend": getattr(engine, "backend", "test-mirror"),
        "engine_execution_count": len(execution_rows),
        "runtime_identity": getattr(engine, "runtime_identity", None),
        "episodes": sorted(episode_rows, key=lambda row: row["quarter_turns"]),
        "limits": {
            "declared_rivals_only": list(ALLOWED_QUARTER_TURNS),
            "max_demos": MAX_DEMOS,
            "max_queries": MAX_QUERIES,
            "training_admission": False,
            "canonical_approval_changed": False,
        },
    }
    report_path = destination / "report.json"
    report_path.write_text(
        json.dumps(report, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    manifest_files = {
        str(path.relative_to(destination)): _file_receipt(path)
        for path in sorted(destination.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
    manifest = {
        "schema": "arc-rotation-parametric-manifest-v1",
        "task_id": TASK_ID,
        "files": manifest_files,
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--quarter-turns", choices=("all", "1", "2", "3"), default="all")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    settings = ALLOWED_QUARTER_TURNS if args.quarter_turns == "all" else (int(args.quarter_turns),)
    report = build_evidence(
        args.out,
        seed=args.seed,
        demos=args.demos,
        queries=args.queries,
        settings=settings,
        max_attempts=args.max_attempts,
    )
    print(
        json.dumps(
            {
                "status": report["status"],
                "output": str(Path(args.out).resolve()),
                "settings": report["settings"],
                "public_ids": [row["public_id"] for row in report["episodes"]],
                "engine_execution_count": report["engine_execution_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
