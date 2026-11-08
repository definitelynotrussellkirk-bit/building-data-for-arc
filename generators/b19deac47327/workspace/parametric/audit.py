"""Finite protected-Racket teaching audit for ``b19deac47327``.

The audit never consults query outputs while deciding whether a lesson is
identifiable.  It checks the two declared settings and a deliberately small
set of nearby shortcut programs against demonstrations only, while separately
replaying every saved label in the protected Racket runtime.  The report also
contains a concrete skip-stage-A causal case for the owner witness builder.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable, Iterable


HOME = Path(__file__).resolve().parent
_PROTOTYPE_PATH = HOME / "prototype.py"
_SPEC = importlib.util.spec_from_file_location(
    "_arc_b19deac47327_parametric_audit_prototype", _PROTOTYPE_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load native prototype at {_PROTOTYPE_PATH}")
_FAMILY = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _FAMILY
_SPEC.loader.exec_module(_FAMILY)

SCHEMA = "arcpuzzles-parametric-prototype-audit-v1"
Grid = list[list[int]]


def _raw(value: object) -> bytes:
    return (
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


def _sha(value: object) -> str:
    return hashlib.sha256(_raw(value)).hexdigest()


def _literal(grid: Grid) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _integer_list(values: object, low: int, high: int, name: str) -> list[int]:
    if type(values) not in (list, tuple) or not values:
        raise ValueError(f"{name} must be a nonempty list")
    result: list[int] = []
    for value in values:
        if type(value) is not int or not low <= value <= high:
            raise ValueError(f"{name} entries must be exact integers in {low}..{high}")
        result.append(value)
    if len(set(result)) != len(result):
        raise ValueError(f"{name} entries must be distinct")
    return result


def _replace_once(source: str, old: str, new: str, label: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"cannot derive {label}: expected one source anchor")
    return source.replace(old, new)


_CORRECT_COMPARATOR = """  (define (better-record? a b)
    (cond
      ((> (first a) (first b)) #t)
      ((< (first a) (first b)) #f)
      ((> (second a) (second b)) #t)
      ((< (second a) (second b)) #f)
      ((< (third a) (third b)) #t)
      ((> (third a) (third b)) #f)
      (else (< (list-ref a 6) (list-ref b 6)))))"""

_WIDEST_COMPARATOR = """  (define (better-record? a b)
    (cond
      ((> (second a) (second b)) #t)
      ((< (second a) (second b)) #f)
      ((> (first a) (first b)) #t)
      ((< (first a) (first b)) #f)
      (else (< (third a) (third b)))))"""

_FEWEST_COMPARATOR = """  (define (better-record? a b)
    (cond
      ((< (first a) (first b)) #t)
      ((> (first a) (first b)) #f)
      ((> (second a) (second b)) #t)
      ((< (second a) (second b)) #f)
      (else (< (third a) (third b)))))"""

_NARROWEST_COMPARATOR = """  (define (better-record? a b)
    (cond
      ((< (second a) (second b)) #t)
      ((> (second a) (second b)) #f)
      ((> (first a) (first b)) #t)
      ((< (first a) (first b)) #f)
      (else (< (third a) (third b)))))"""

_TOP_LEFT_COMPARATOR = """  (define (better-record? a b)
    (cond
      ((< (third a) (third b)) #t)
      ((> (third a) (third b)) #f)
      ((< (list-ref a 6) (list-ref b 6)) #t)
      (else #f)))"""

_RECORD_FILTER = """             (filter
               (lambda (record) (not (empty? record)))
               (apply append"""

_ALL_GROUPS_BLOCK = """      (if (empty? records)
          projected
          (let* ((winner (first (sort records better-record?)))
                 (line (third winner))
                 (color (list-ref winner 3))
                 (lo (list-ref winner 4))
                 (hi (list-ref winner 5)))
            (for/fold ((out projected)) ((lane (range lo (+ hi 1))))
              (if horizontal?
                  (set-cell out line lane color)
                  (set-cell out lane line color)))))))"""

_ALL_GROUPS_REPLACEMENT = """      (if (empty? records)
          projected
          (for/fold ((out projected)) ((winner records))
            (let* ((line (third winner))
                   (color (list-ref winner 3))
                   (lo (list-ref winner 4))
                   (hi (list-ref winner 5)))
              (for/fold ((inner out)) ((lane (range lo (+ hi 1))))
                (if horizontal?
                    (set-cell inner line lane color)
                    (set-cell inner lane line color))))))))"""


def racket_rival_programs() -> dict[str, str]:
    """Return executable shortcut programs derived from the reviewed source."""
    base = (HOME / "bridge_longest.rkt").read_text(encoding="utf-8")
    rivals: dict[str, str] = {
        "skip_projection": (HOME / "skip_projection.rkt").read_text(encoding="utf-8"),
        "widest_span": _replace_once(base, _CORRECT_COMPARATOR, _WIDEST_COMPARATOR, "widest_span"),
        "fewest_seeds": _replace_once(base, _CORRECT_COMPARATOR, _FEWEST_COMPARATOR, "fewest_seeds"),
        "narrowest_span": _replace_once(base, _CORRECT_COMPARATOR, _NARROWEST_COMPARATOR, "narrowest_span"),
        "top_or_leftmost": _replace_once(base, _CORRECT_COMPARATOR, _TOP_LEFT_COMPARATOR, "top_or_leftmost"),
        "first_found": _replace_once(
            base,
            "(first (sort records better-record?))",
            "(first records)",
            "first_found",
        ),
        "first_border_only": _replace_once(
            base,
            _RECORD_FILTER,
            """             (filter
               (lambda (record)
                 (and (not (empty? record)) (= (list-ref record 6) 0)))
               (apply append""",
            "first_border_only",
        ),
        "second_border_only": _replace_once(
            base,
            _RECORD_FILTER,
            """             (filter
               (lambda (record)
                 (and (not (empty? record)) (= (list-ref record 6) 1)))
               (apply append""",
            "second_border_only",
        ),
        "bridge_every_group": _replace_once(
            base,
            _ALL_GROUPS_BLOCK,
            _ALL_GROUPS_REPLACEMENT,
            "bridge_every_group",
        ),
    }
    if len(set(rivals.values())) != len(rivals):
        raise ValueError("rival programs must be source-distinct")
    return rivals


class _RacketEvaluator:
    def __init__(self) -> None:
        from arc_repl.racket_bridge import RacketBridge
        from puzzle_generators.rule_wrap import wrap_rule

        self._wrap_rule = wrap_rule
        self._bridge = RacketBridge()
        identity = self._bridge.runtime_identity
        if identity.get("backend") != "racket" or identity.get("protected") is not True:
            self._bridge.close()
            raise ValueError("audit requires the protected Racket runtime")
        self.identity = {
            key: identity[key]
            for key in (
                "schema",
                "backend",
                "protected",
                "binary_sha256",
                "prelude_sha256",
                "bridge_sha256",
                "boot_script_sha256",
                "candidate_symbol_policy_sha256",
            )
            if key in identity
        }
        self._wrapped: dict[str, str] = {}
        self.evaluations = 0

    def apply(self, source: str, grid: Grid) -> Grid:
        if source not in self._wrapped:
            self._wrapped[source] = self._wrap_rule(source)
        self.evaluations += 1
        return self._bridge.eval_text(f"({self._wrapped[source]} {_literal(grid)})")

    def close(self) -> None:
        self._bridge.close()


def _fill_record(original: Grid, intermediate: Grid, record: dict[str, Any]) -> Grid:
    facts = _FAMILY._facts(original)
    output = copy.deepcopy(intermediate)
    for lane in range(record["lo"], record["hi"] + 1):
        row, col = _FAMILY._cell_from_axis_lane(facts, record["line"], lane)
        output[row][col] = record["color"]
    return output


def _python_rival_outputs(grid: Grid) -> dict[str, Grid]:
    projected = _FAMILY.project(grid)
    records = _FAMILY._records(grid, projected)
    if not records:
        return {name: copy.deepcopy(projected) for name in racket_rival_programs()}

    def selected(key: Callable[[dict[str, Any]], Any], *, reverse: bool = True) -> Grid:
        return _fill_record(grid, projected, sorted(records, key=key, reverse=reverse)[0])

    all_groups = copy.deepcopy(projected)
    for record in records:
        all_groups = _fill_record(grid, all_groups, record)
    first = [record for record in records if record["side"] == "first"]
    second = [record for record in records if record["side"] == "second"]
    correct_key = _FAMILY._record_score
    return {
        "skip_projection": copy.deepcopy(grid),
        "widest_span": selected(lambda record: (record["span"], record["count"], -record["line"])),
        "fewest_seeds": selected(lambda record: (record["count"], -record["span"], record["line"]), reverse=False),
        "narrowest_span": selected(lambda record: (record["span"], -record["count"], record["line"]), reverse=False),
        "top_or_leftmost": selected(lambda record: (record["line"], record["side"] == "second"), reverse=False),
        "first_found": _fill_record(grid, projected, records[0]),
        "first_border_only": _fill_record(grid, projected, max(first, key=correct_key)) if first else projected,
        "second_border_only": _fill_record(grid, projected, max(second, key=correct_key)) if second else projected,
        "bridge_every_group": all_groups,
    }


def _python_apply_rival(name: str, grid: Grid) -> Grid:
    outputs = _python_rival_outputs(grid)
    if name not in outputs:
        raise ValueError(f"unknown rival {name}")
    return outputs[name]


def _case_for(
    seed: int,
    demos: int,
    settings: dict[str, str],
    rivals: dict[str, str],
    evaluator: _RacketEvaluator | None,
) -> dict[str, Any]:
    episode = _FAMILY.generate(seed, settings, demos, 4)
    intended = _FAMILY.program(settings)
    if evaluator is None:
        labels_match = all(
            _FAMILY.solve(pair["input"], settings) == pair["output"]
            for split in ("train", "test")
            for pair in episode[split]
        )
        declared_survivors = [
            candidate
            for candidate in _FAMILY.SETTINGS
            if all(
                _FAMILY.solve(pair["input"], candidate) == pair["output"]
                for pair in episode["train"]
            )
        ]
        rival_survivors = [
            name
            for name in rivals
            if all(
                _python_apply_rival(name, pair["input"]) == pair["output"]
                for pair in episode["train"]
            )
        ]
    else:
        labels_match = all(
            evaluator.apply(intended, pair["input"]) == pair["output"]
            for split in ("train", "test")
            for pair in episode[split]
        )
        declared_survivors = [
            candidate
            for candidate in _FAMILY.SETTINGS
            if all(
                evaluator.apply(_FAMILY.program(candidate), pair["input"]) == pair["output"]
                for pair in episode["train"]
            )
        ]
        rival_survivors = [
            name
            for name, source in rivals.items()
            if all(
                evaluator.apply(source, pair["input"]) == pair["output"]
                for pair in episode["train"]
            )
        ]

    return {
        "seed": seed,
        "demos": demos,
        "queries": 4,
        "settings": settings,
        "input_sha256": _sha({
            "train": [pair["input"] for pair in episode["train"]],
            "test": [pair["input"] for pair in episode["test"]],
        }),
        "output_sha256": _sha({
            "train": [pair["output"] for pair in episode["train"]],
            "test": [pair["output"] for pair in episode["test"]],
        }),
        "program_sha256": hashlib.sha256(intended.encode("utf-8")).hexdigest(),
        "labels_match": labels_match,
        "declared_survivors": declared_survivors,
        "rival_survivors": rival_survivors,
        "query_outputs_consulted": False,
        "query_shapes": [
            [len(pair["input"]), len(pair["input"][0])]
            for pair in episode["test"]
        ],
    }


def build_report(
    *,
    seeds: Iterable[int] = (0, 17),
    demo_counts: Iterable[int] = (2, 3, 6),
    run_racket: bool = True,
) -> dict[str, Any]:
    normalized_seeds = _integer_list(list(seeds), 0, 2**63 - 1, "seeds")
    normalized_counts = _integer_list(list(demo_counts), 2, 6, "demo_counts")
    if type(run_racket) is not bool:
        raise ValueError("run_racket must be boolean")

    rivals = racket_rival_programs()
    evaluator = _RacketEvaluator() if run_racket else None
    cases: list[dict[str, Any]] = []
    try:
        for seed in normalized_seeds:
            for demos in normalized_counts:
                baseline_input_sha: str | None = None
                for settings in _FAMILY.SETTINGS:
                    case = _case_for(seed, demos, settings, rivals, evaluator)
                    if baseline_input_sha is None:
                        baseline_input_sha = case["input_sha256"]
                    case["inputs_match_other_settings"] = case["input_sha256"] == baseline_input_sha
                    cases.append(case)

        causal_input = _FAMILY.sample_input(17, "query", 3)
        intended_source = _FAMILY.program(_FAMILY.SETTINGS[1])
        counterfactual_source = rivals["skip_projection"]
        if evaluator is None:
            expected_output = _FAMILY.solve(causal_input, _FAMILY.SETTINGS[1])
            counterfactual_output = _python_apply_rival("skip_projection", causal_input)
        else:
            expected_output = evaluator.apply(intended_source, causal_input)
            counterfactual_output = evaluator.apply(counterfactual_source, causal_input)
        if expected_output == counterfactual_output:
            raise ValueError("causal skip-projection case did not change the final output")
        analysis = _FAMILY.analyze(causal_input)
        causal_case = {
            "task_id": _FAMILY.TASK_ID,
            "seed": 17,
            "split": "query",
            "index": 3,
            "settings": _FAMILY.SETTINGS[1],
            "ablation": "skip_projection",
            "input": causal_input,
            "expected_output": expected_output,
            "counterfactual_output": counterfactual_output,
            "intended_program_sha256": hashlib.sha256(intended_source.encode()).hexdigest(),
            "counterfactual_program_sha256": hashlib.sha256(counterfactual_source.encode()).hexdigest(),
            "intermediate": {
                "orientation": analysis["orientation"],
                "winner": analysis["winner"],
                "records": analysis["records"],
                "bridge_added_cells": analysis["bridge_added_cells"],
            },
        }
    finally:
        if evaluator is not None:
            evaluator.close()

    report: dict[str, Any] = {
        "schema": SCHEMA,
        "task_id": _FAMILY.TASK_ID,
        "scope": {
            "seeds": normalized_seeds,
            "demo_counts": normalized_counts,
            "queries": 4,
            "settings": list(_FAMILY.SETTINGS),
            "rival_names": sorted(rivals),
            "claim": (
                "finite protected-Racket teaching audit"
                if run_racket
                else "finite Python preflight; protected-Racket audit is separate"
            ),
        },
        "programs": [
            {
                "settings": settings,
                "sha256": hashlib.sha256(_FAMILY.program(settings).encode()).hexdigest(),
            }
            for settings in _FAMILY.SETTINGS
        ],
        "rivals": {
            name: hashlib.sha256(source.encode()).hexdigest()
            for name, source in sorted(rivals.items())
        },
        "cases": cases,
        "causal_case": causal_case,
        "summary": {
            "cases": len(cases),
            "all_inputs_setting_independent": all(
                case["inputs_match_other_settings"] for case in cases
            ),
            "all_labels_match": all(case["labels_match"] for case in cases),
            "all_declared_unique": all(
                case["declared_survivors"] == [case["settings"]] for case in cases
            ),
            "all_rivals_rejected": all(not case["rival_survivors"] for case in cases),
            "query_outputs_consulted": any(case["query_outputs_consulted"] for case in cases),
            "racket_checked": run_racket,
        },
    }
    if evaluator is not None:
        report["racket"] = {**evaluator.identity, "evaluations": evaluator.evaluations}
    return report


def write_report(path: Path | str, report: dict[str, Any]) -> None:
    target = Path(path)
    if target.is_symlink():
        raise ValueError("audit output cannot be a symlink")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        report,
        sort_keys=True,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8") + b"\n"
    temporary = target.with_name(target.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, action="append", dest="seeds")
    parser.add_argument("--demos", type=int, action="append", dest="demo_counts")
    parser.add_argument("--python-only", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_report(
        seeds=args.seeds if args.seeds is not None else (0, 17),
        demo_counts=args.demo_counts if args.demo_counts is not None else (2, 3, 6),
        run_racket=not args.python_only,
    )
    write_report(args.out, report)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
