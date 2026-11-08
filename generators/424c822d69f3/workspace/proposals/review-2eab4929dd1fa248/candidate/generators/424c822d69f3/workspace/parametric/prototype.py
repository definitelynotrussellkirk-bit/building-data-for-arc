#!/usr/bin/env python3
"""Proposed rectangle-anchor parameterization for ARC task 424c822d69f3.

The approved generator and canonical authority stay unchanged.  This task-local
prototype varies only which horizontal point of each color-5 rectangle is used
when selecting the uniquely nearest row-0 marker.
"""
from __future__ import annotations

import argparse
import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TASK_ID = "424c822d69f3"
SOURCE_PARENT = "training:ddf7fa4f"
ANCHORS = ("midpoint", "left_edge", "right_edge")
DEFAULT_ANCHOR = "midpoint"
MAX_DEMOS = 16
MAX_QUERIES = 16
DEFAULT_MAX_ATTEMPTS = 512
CANONICAL_RULE_HASH = "5abbdbb61293"
CANONICAL_CENTER = "(center (/ (+ (second bb) (fourth bb)) 2))"
CENTER_EXPRESSIONS = {
    "midpoint": CANONICAL_CENTER,
    "left_edge": "(center (second bb))",
    "right_edge": "(center (fourth bb))",
}


def _module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


oracle = _module("rectangle_anchor_oracle", HERE / "oracle.py")


def stable_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")


def digest(value) -> str:
    return hashlib.sha256(stable_bytes(value)).hexdigest()


def text_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _integer(name: str, value, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a literal integer")
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")
    return value


def _anchor(value) -> str:
    return oracle.validate_anchor(value)


@lru_cache(maxsize=1)
def canonical_rows() -> tuple[dict, ...]:
    path = ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        return tuple(row for line in handle if (row := json.loads(line)).get("task_id") == TASK_ID)


@lru_cache(maxsize=1)
def canonical_program() -> str:
    programs = {row["program_solution"] for row in canonical_rows()}
    if len(programs) != 1:
        raise ValueError("exactly one canonical rule authority is required")
    program = next(iter(programs))
    short_hash = text_digest(" ".join(program.split()))[:12]
    if short_hash != CANONICAL_RULE_HASH:
        raise ValueError("canonical rule authority changed; review the prototype")
    if program.count(CANONICAL_CENTER) != 1:
        raise ValueError("canonical center binding must occur exactly once")
    return program


@lru_cache(maxsize=3)
def rule_text(anchor: str) -> str:
    anchor = _anchor(anchor)
    expected = canonical_program().replace(CANONICAL_CENTER, CENTER_EXPRESSIONS[anchor])
    materialized = (HERE / "rules" / f"{anchor}.rkt").read_text(encoding="utf-8")
    if materialized != expected:
        raise ValueError(f"materialized {anchor} rule differs from its declared canonical derivation")
    return materialized


@lru_cache(maxsize=1)
def generator():
    return _module("rectangle_anchor_canonical_generator", ROOT / "generators" / TASK_ID / "generator.py")


def prototype_domain_errors(grid) -> list[str]:
    """Return canonical-domain errors plus ties under any declared anchor."""
    errors = [f"canonical domain: {reason}" for reason in generator().self_check(grid)]
    if errors:
        return errors
    legend = oracle.markers(grid)
    marker_cols = [col for col, _ in legend]
    for index, cells in enumerate(oracle.components(grid)):
        _r0, c0, _r1, c1 = oracle.bbox(cells)
        for anchor in ANCHORS:
            point = oracle.anchor_column(c0, c1, anchor)
            if oracle.nearest_marker_index(marker_cols, point) is None:
                errors.append(f"rectangle {index} has an exact nearest-marker tie under {anchor}")
    return errors


def choose_setting(seed: int) -> str:
    _integer("seed", seed, 0, 2**63 - 1)
    index = hashlib.sha256(f"rectangle-anchor-v1:{seed}".encode("utf-8")).digest()[0] % len(ANCHORS)
    return ANCHORS[index]


def source_identity() -> dict[str, str]:
    relative_paths = [
        f"generators/{TASK_ID}/generator.py",
        f"generators/{TASK_ID}/tests/test_parametric_anchor.py",
        f"generators/{TASK_ID}/workspace/parametric/prototype.py",
        f"generators/{TASK_ID}/workspace/parametric/oracle.py",
        f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        f"generators/{TASK_ID}/workspace/parametric/promotion.json",
        f"generators/{TASK_ID}/workspace/parametric/rules/midpoint.rkt",
        f"generators/{TASK_ID}/workspace/parametric/rules/left_edge.rkt",
        f"generators/{TASK_ID}/workspace/parametric/rules/right_edge.rkt",
        "shared/data/canonical/puzzles.jsonl",
    ]
    readme = f"generators/{TASK_ID}/workspace/parametric/README.md"
    if (ROOT / readme).is_file():
        relative_paths.append(readme)
    return {
        relative: hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        for relative in relative_paths
    }


def _prediction_record(grid) -> dict:
    outputs = {anchor: oracle.independent_output(grid, anchor) for anchor in ANCHORS}
    midpoint, left, right = (outputs[name] for name in ANCHORS)
    if midpoint == right and left != midpoint:
        kind = "left_edge_witness"
    elif midpoint == left and right != midpoint:
        kind = "right_edge_witness"
    elif midpoint == left == right:
        kind = "neutral"
    else:
        kind = "complex_witness"
    return {
        "witness_kind": kind,
        "prediction_sha256": {anchor: digest(outputs[anchor]) for anchor in ANCHORS},
    }


def _copy_candidate(row: dict) -> dict:
    return {
        "sample_index": row["sample_index"],
        "witness_kind": row["witness_kind"],
        "prediction_sha256": dict(row["prediction_sha256"]),
        "input": copy.deepcopy(row["input"]),
    }


@lru_cache(maxsize=64)
def _select_inputs_cached(seed: int, demos: int, queries: int, max_attempts: int) -> dict:
    accepted: list[dict] = []
    rejected: list[dict] = []
    seen: set[str] = set()
    for sample_index in range(max_attempts):
        try:
            grid = generator().generate(seed, sample_index)
        except Exception as exc:  # a bounded diagnostic, never silently accepted
            rejected.append({
                "sample_index": sample_index,
                "reasons": [f"generator raised {type(exc).__name__}: {exc}"],
            })
            continue
        reasons = prototype_domain_errors(grid)
        identifier = digest(grid)
        if identifier in seen:
            reasons = [*reasons, "duplicate input"]
        if reasons:
            rejected.append({"sample_index": sample_index, "reasons": reasons})
            continue
        seen.add(identifier)
        prediction = _prediction_record(grid)
        accepted.append({"sample_index": sample_index, "input": grid, **prediction})

    left = [row for row in accepted if row["witness_kind"] == "left_edge_witness"]
    right = [row for row in accepted if row["witness_kind"] == "right_edge_witness"]
    if not left or not right:
        raise RuntimeError(
            "sampling budget exhausted: demonstrations require both left-edge and right-edge witnesses; "
            f"found left={len(left)}, right={len(right)} after {max_attempts} attempts"
        )

    demos_selected = [left[0], right[0]]
    selected_indices = {row["sample_index"] for row in demos_selected}
    # Preserve scarce query witnesses by preferring neutral filler demonstrations.
    filler_order = [row for row in accepted if row["witness_kind"] == "neutral"] + [
        row for row in accepted if row["witness_kind"] != "neutral"
    ]
    for row in filler_order:
        if len(demos_selected) == demos:
            break
        if row["sample_index"] in selected_indices:
            continue
        demos_selected.append(row)
        selected_indices.add(row["sample_index"])
        if len(demos_selected) == demos:
            break
    if len(demos_selected) != demos:
        raise RuntimeError(
            f"sampling budget exhausted: accepted {len(demos_selected)} demonstrations of {demos} requested "
            f"after {max_attempts} attempts"
        )

    remaining_witnesses = [
        row for row in accepted
        if row["sample_index"] not in selected_indices
        and row["witness_kind"] in {"left_edge_witness", "right_edge_witness"}
    ]
    queries_selected: list[dict] = []
    if queries >= 2:
        for kind in ("left_edge_witness", "right_edge_witness"):
            match = next((row for row in remaining_witnesses if row["witness_kind"] == kind), None)
            if match is None:
                raise RuntimeError(
                    "sampling budget exhausted: query set requires both witness types when queries >= 2; "
                    f"after {max_attempts} attempts"
                )
            queries_selected.append(match)
            selected_indices.add(match["sample_index"])
    for row in remaining_witnesses:
        if row["sample_index"] in selected_indices:
            continue
        queries_selected.append(row)
        selected_indices.add(row["sample_index"])
        if len(queries_selected) == queries:
            break
    if len(queries_selected) != queries:
        raise RuntimeError(
            f"sampling budget exhausted: accepted {len(queries_selected)} parameter-sensitive queries of "
            f"{queries} requested after {max_attempts} attempts"
        )

    demos_selected.sort(key=lambda row: row["sample_index"])
    queries_selected.sort(key=lambda row: row["sample_index"])
    return {
        "train": tuple(_copy_candidate(row) for row in demos_selected),
        "test": tuple(_copy_candidate(row) for row in queries_selected),
        "rejected_draws": tuple(copy.deepcopy(rejected)),
        "attempts_examined": max_attempts,
        "accepted_candidates": len(accepted),
    }


def select_inputs(seed: int, *, demos: int = 3, queries: int = 4,
                  max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, MAX_DEMOS)
    _integer("queries", queries, 1, MAX_QUERIES)
    _integer("max_attempts", max_attempts, 1, 10000)
    cached = _select_inputs_cached(seed, demos, queries, max_attempts)
    return {
        "train": [_copy_candidate(row) for row in cached["train"]],
        "test": [_copy_candidate(row) for row in cached["test"]],
        "rejected_draws": copy.deepcopy(list(cached["rejected_draws"])),
        "attempts_examined": cached["attempts_examined"],
        "accepted_candidates": cached["accepted_candidates"],
    }


class RuleEngine:
    """Own one actual Racket bridge and cache exact rule/input executions."""

    def __init__(self):
        self.bridge = RacketBridge(timeout=15.0)
        self.executions: list[dict] = []
        self._cache: dict[tuple[str, str], list[list[int]]] = {}
        self._records: dict[tuple[str, str], dict] = {}

    def __enter__(self):
        return self

    def __exit__(self, *error):
        self.bridge.shutdown()
        return False

    def apply(self, grid, anchor: str):
        anchor = _anchor(anchor)
        errors = prototype_domain_errors(grid)
        if errors:
            raise ValueError("input outside prototype domain: " + "; ".join(errors))
        input_hash = digest(grid)
        key = (input_hash, anchor)
        if key in self._cache:
            return copy.deepcopy(self._cache[key])
        source = rule_text(anchor)
        callable_source = strip_rule_wrapper(strip_line_comments(source))
        if not callable_source.lstrip().startswith("(lambda"):
            raise ValueError("prototype only supports its exact lambda rules")
        literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
        output = self.bridge.eval_text(f"({callable_source} {literal})")
        if (
            not isinstance(output, list)
            or len(output) != len(grid)
            or any(not isinstance(row, list) or len(row) != len(grid[0]) for row in output)
            or any(isinstance(cell, bool) or not isinstance(cell, int) or not 0 <= cell <= 9
                   for row in output for cell in row)
        ):
            raise ValueError("Racket returned an invalid output grid")
        record = {
            "call_index": len(self.executions),
            "anchor": anchor,
            "input_sha256": input_hash,
            "output_sha256": digest(output),
            "program_sha256": text_digest(source),
            "racket_executed": True,
        }
        self.executions.append(record)
        self._cache[key] = copy.deepcopy(output)
        self._records[key] = dict(record)
        return copy.deepcopy(output)

    def execution_record(self, grid, anchor: str) -> dict:
        key = (digest(grid), _anchor(anchor))
        if key not in self._records:
            self.apply(grid, anchor)
        return dict(self._records[key])


def identify_query(demonstrations, query_input, *, engine: RuleEngine) -> dict:
    """Fit all declared anchors using demonstrations only, then predict the query."""
    rivals = []
    consistent = []
    predictions = {}
    for anchor in ANCHORS:
        mismatches = [
            index
            for index, pair in enumerate(demonstrations)
            if engine.apply(pair["input"], anchor) != pair["output"]
        ]
        if not mismatches:
            consistent.append(anchor)
        rivals.append({
            "anchor": anchor,
            "fits_demonstrations": not mismatches,
            "mismatching_demo_indices": mismatches,
        })
    for rival in rivals:
        output = engine.apply(query_input, rival["anchor"])
        output_hash = digest(output)
        predictions[rival["anchor"]] = output_hash
        rival["query_prediction_sha256"] = output_hash
    identified = len(consistent) == 1
    return {
        "status": "identified_within_declared_anchors" if identified else "ambiguous_within_declared_anchors",
        "query_input_sha256": digest(query_input),
        "consistent_anchors": consistent,
        "determined_output_sha256": predictions[consistent[0]] if identified else None,
        "query_answer_used_for_demo_fit": False,
        "rivals": rivals,
    }


def _checked_label(engine: RuleEngine, grid, anchor: str, split: str, index: int):
    output = engine.apply(grid, anchor)
    independent = oracle.independent_output(grid, anchor)
    if output != independent:
        raise ValueError(f"independent oracle disagrees at {split}[{index}]")
    evidence = engine.execution_record(grid, anchor)
    evidence.update({
        "split": split,
        "index": index,
        "independent_oracle_match": True,
        "racket_executed": True,
    })
    evidence.pop("call_index", None)
    return {"input": copy.deepcopy(grid), "output": output}, evidence


def generate_episode(seed: int, *, anchor: str | None = None, demos: int = 3,
                     queries: int = 4, max_attempts: int = DEFAULT_MAX_ATTEMPTS,
                     engine: RuleEngine | None = None) -> dict:
    _integer("seed", seed, 0, 2**63 - 1)
    _integer("demos", demos, 2, MAX_DEMOS)
    _integer("queries", queries, 1, MAX_QUERIES)
    _integer("max_attempts", max_attempts, 1, 10000)
    selected = choose_setting(seed) if anchor is None else _anchor(anchor)
    selection = select_inputs(seed, demos=demos, queries=queries, max_attempts=max_attempts)
    if engine is None:
        with RuleEngine() as active:
            return generate_episode(
                seed, anchor=selected, demos=demos, queries=queries,
                max_attempts=max_attempts, engine=active,
            )

    train = []
    test = []
    checks = []
    reports = []
    for index, row in enumerate(selection["train"]):
        pair, evidence = _checked_label(engine, row["input"], selected, "train", index)
        train.append(pair)
        checks.append(evidence)
    for index, row in enumerate(selection["test"]):
        report = identify_query(train, row["input"], engine=engine)
        if report["consistent_anchors"] != [selected]:
            raise RuntimeError("demonstrations do not identify the fixed episode anchor")
        pair, evidence = _checked_label(engine, row["input"], selected, "test", index)
        if report["determined_output_sha256"] != digest(pair["output"]):
            raise ValueError("demonstration-derived prediction disagrees with the Racket label")
        reports.append({**report, "query_index": index})
        test.append(pair)
        checks.append(evidence)

    program = rule_text(selected)
    selection_summary = {
        split: [
            {
                "sample_index": row["sample_index"],
                "witness_kind": row["witness_kind"],
                "prediction_sha256": row["prediction_sha256"],
                "input_sha256": digest(row["input"]),
            }
            for row in selection[split]
        ]
        for split in ("train", "test")
    }
    return {
        "schema": "rectangle-anchor-parametric-prototype-v1",
        "status": "proposed",
        "task_id": TASK_ID,
        "source_parent": SOURCE_PARENT,
        "seed": seed,
        "anchor": selected,
        "demo_count": demos,
        "query_count": queries,
        "max_attempts": max_attempts,
        "attempts_examined": selection["attempts_examined"],
        "accepted_candidate_count": selection["accepted_candidates"],
        "accepted_sample_indices": [row["sample_index"] for row in selection["train"] + selection["test"]],
        "selection": selection_summary,
        "rejected_draws": selection["rejected_draws"],
        "train": train,
        "test": test,
        "program_solution": program,
        "program_sha256": text_digest(program),
        "canonical_rule_hash": CANONICAL_RULE_HASH,
        "source_sha256": source_identity(),
        "label_checks": checks,
        "query_identification": reports,
    }


def public_payload(episode: dict) -> dict:
    return {
        "train": [
            {"input": copy.deepcopy(pair["input"]), "output": copy.deepcopy(pair["output"])}
            for pair in episode["train"]
        ],
        "test": [{"input": copy.deepcopy(pair["input"])} for pair in episode["test"]],
    }


def public_id(episode: dict) -> str:
    return digest(public_payload(episode))


def _validate_episode(episode: dict, *, engine: RuleEngine) -> None:
    anchor = _anchor(episode.get("anchor"))
    if episode.get("source_sha256") != source_identity():
        raise ValueError("source identity changed; regenerate the episode")
    expected_program = rule_text(anchor)
    if episode.get("program_solution") != expected_program or episode.get("program_sha256") != text_digest(expected_program):
        raise ValueError("episode rule provenance disagrees with materialized Racket")
    train = episode.get("train")
    test = episode.get("test")
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("episode must contain train and test lists")
    if len(train) != episode.get("demo_count") or len(test) != episode.get("query_count"):
        raise ValueError("episode counts disagree with serialized pairs")
    all_inputs = [pair.get("input") for pair in train + test]
    if len({digest(grid) for grid in all_inputs}) != len(all_inputs):
        raise ValueError("episode inputs must be distinct")
    demo_kinds = {_prediction_record(pair["input"])["witness_kind"] for pair in train}
    if not {"left_edge_witness", "right_edge_witness"}.issubset(demo_kinds):
        raise ValueError("demonstrations no longer identify all declared anchors")
    for split_name, pairs in (("train", train), ("test", test)):
        for index, pair in enumerate(pairs):
            actual = engine.apply(pair["input"], anchor)
            independent = oracle.independent_output(pair["input"], anchor)
            if actual != pair.get("output") or actual != independent:
                raise ValueError(f"label mismatch at {split_name}[{index}]")
    for index, pair in enumerate(test):
        report = identify_query(train, pair["input"], engine=engine)
        if report["consistent_anchors"] != [anchor]:
            raise ValueError(f"demonstrations do not identify query {index}")
        if report["determined_output_sha256"] != digest(pair["output"]):
            raise ValueError(f"identified prediction mismatch at test[{index}]")


def _write_manifest(destination: Path) -> Path:
    rows = []
    for path in sorted(destination.rglob("*")):
        if not path.is_file() or path.name == "manifest.json":
            continue
        rows.append({
            "path": str(path.relative_to(destination)),
            "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    manifest = {
        "schema": "rectangle-anchor-parametric-export-v1",
        "task_id": TASK_ID,
        "files": rows,
    }
    path = destination / "manifest.json"
    path.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return path


def write_episodes(destination, episodes, *, engine: RuleEngine | None = None) -> list[dict]:
    destination = Path(destination)
    projected = []
    seen = {}
    for episode in episodes:
        payload = stable_bytes(public_payload(episode))
        identifier = hashlib.sha256(payload).hexdigest()
        if identifier in seen:
            if seen[identifier] == payload:
                raise ValueError("duplicate visible payload in episode batch")
            raise ValueError("visible-content hash collision in episode batch")
        seen[identifier] = payload
        projected.append((identifier, payload, episode))
    projected.sort(key=lambda row: row[0])
    if engine is None:
        with RuleEngine() as active:
            return write_episodes(destination, [row[2] for row in projected], engine=active)
    for _identifier, _payload, episode in projected:
        _validate_episode(episode, engine=engine)
    if destination.exists() and any(destination.iterdir()):
        raise ValueError(f"destination is not empty: {destination}")
    destination.mkdir(parents=True, exist_ok=True)
    written = []
    for identifier, payload, episode in projected:
        public_path = destination / "public" / f"{identifier}.json"
        private_path = destination / "private" / "episodes" / f"{identifier}.json"
        rule_path = destination / "private" / "rules" / f"{episode['program_sha256']}.rkt"
        public_path.parent.mkdir(parents=True, exist_ok=True)
        private_path.parent.mkdir(parents=True, exist_ok=True)
        rule_path.parent.mkdir(parents=True, exist_ok=True)
        public_path.write_bytes(payload)
        private_path.write_text(json.dumps(episode, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        if rule_path.exists() and rule_path.read_text(encoding="utf-8") != episode["program_solution"]:
            raise ValueError("program hash collision or existing rule corruption")
        rule_path.write_text(episode["program_solution"], encoding="utf-8")
        written.append({
            "public_id": identifier,
            "public_path": str(public_path),
            "private_path": str(private_path),
            "rule_path": str(rule_path),
        })
    _write_manifest(destination)
    return written


def retain_evidence(destination, *, seed: int, anchors, demos: int, queries: int,
                    max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> dict:
    destination = Path(destination)
    with RuleEngine() as engine:
        episodes = [
            generate_episode(
                seed, anchor=anchor, demos=demos, queries=queries,
                max_attempts=max_attempts, engine=engine,
            )
            for anchor in anchors
        ]
        written = write_episodes(destination, episodes, engine=engine)
        executions = copy.deepcopy(engine.executions)
    execution_path = destination / "private" / "racket-executions.json"
    execution_path.parent.mkdir(parents=True, exist_ok=True)
    execution_path.write_text(json.dumps(executions, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    witness_rows = []
    first = episodes[0]
    for split in ("train", "test"):
        for index, pair in enumerate(first[split]):
            witness_rows.append({
                "split": split,
                "index": index,
                "input_sha256": digest(pair["input"]),
                "witness_kind": _prediction_record(pair["input"])["witness_kind"],
                "output_sha256": {
                    episode["anchor"]: digest(episode[split][index]["output"])
                    for episode in episodes
                },
            })
    summary = {
        "schema": "rectangle-anchor-parametric-evidence-v1",
        "status": "proposed",
        "task_id": TASK_ID,
        "source_parent": SOURCE_PARENT,
        "seed": seed,
        "anchors": list(anchors),
        "demos": demos,
        "queries": queries,
        "max_attempts": max_attempts,
        "public_ids": [row["public_id"] for row in written],
        "racket_execution_count": len(executions),
        "all_labels_independent_oracle_matched": all(
            check["independent_oracle_match"]
            for episode in episodes for check in episode["label_checks"]
        ),
        "all_queries_identified_from_demonstrations_only": all(
            report["status"] == "identified_within_declared_anchors"
            and report["query_answer_used_for_demo_fit"] is False
            for episode in episodes for report in episode["query_identification"]
        ),
        "shared_input_witnesses": witness_rows,
        "source_sha256": source_identity(),
    }
    summary_path = destination / "summary.json"
    summary_path.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    _write_manifest(destination)
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("--anchor", choices=("auto", "all", *ANCHORS), default="all")
    parser.add_argument("--demos", type=int, default=3)
    parser.add_argument("--queries", type=int, default=4)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.anchor == "all":
        anchors = ANCHORS
    elif args.anchor == "auto":
        anchors = (choose_setting(args.seed),)
    else:
        anchors = (args.anchor,)
    summary = retain_evidence(
        args.out,
        seed=args.seed,
        anchors=anchors,
        demos=args.demos,
        queries=args.queries,
        max_attempts=args.max_attempts,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
