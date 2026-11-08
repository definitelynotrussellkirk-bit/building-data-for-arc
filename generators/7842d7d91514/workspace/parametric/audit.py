"""Replayable finite teaching audit for parametric family 7842d7d91514.

By default this executes declared programs and nine nearby shortcut programs in
the protected Racket runtime.  ``--python-only`` is a fast source/test preflight;
it is deliberately marked as not Racket checked.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from typing import Iterable

_PROTOTYPE_PATH = Path(__file__).with_name("prototype.py")
_SPEC = importlib.util.spec_from_file_location(
    "_arc_7842d7d91514_parametric_audit_prototype", _PROTOTYPE_PATH
)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"cannot load native prototype at {_PROTOTYPE_PATH}")
_FAMILY = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_FAMILY)

SCHEMA = "arcpuzzles-parametric-prototype-audit-v1"


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


def _literal(grid: list[list[int]]) -> str:
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


def _shape_prefix() -> str:
    return """  (define (shape-grid obj)
    (recolor
      (crop-to-content
        (subgrid (keep-only grid (obj-color obj))
                 (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj)))
      (obj-color obj) 1))
  (define (rotate-n g turns)
    (if (= turns 0) g (rotate-n (rotate-cw g) (- turns 1))))
"""


def _target_program(turn_expression: str, *, selector: bool = False) -> str:
    selector_lines = ""
    if selector:
        selector_lines = """         (selector (first (filter (lambda (obj) (= (obj-color obj) 8)) objects-list)))
         (selector-count (length (obj-cells selector)))
"""
    return (
        "(rule! (lambda (grid)\n"
        + _shape_prefix()
        + "  (let* ((objects-list (objects grid 0))\n"
        + "         (template (first (filter (lambda (obj) (= (obj-color obj) 5)) objects-list)))\n"
        + selector_lines
        + f"         (quarter-turns {turn_expression})\n"
        + "         (template-shape (rotate-n (shape-grid template) quarter-turns)))\n"
        + "    (reduce (lambda (acc obj)\n"
        + "      (if (= (obj-color obj) 2)\n"
        + "          (recolor-cells acc (obj-cells obj)\n"
        + "            (if (= (shape-grid obj) template-shape) 4 1))\n"
        + "          acc))\n"
        + "      grid objects-list))))"
    )


def _constant_program(color: int) -> str:
    return f"""(rule! (lambda (grid)
  (reduce (lambda (acc obj)
    (if (= (obj-color obj) 2)
        (recolor-cells acc (obj-cells obj) {color})
        acc))
    grid (objects grid 0))))"""


def _same_cell_count_program() -> str:
    return """(rule! (lambda (grid)
  (let* ((objects-list (objects grid 0))
         (template (first (filter (lambda (obj) (= (obj-color obj) 5)) objects-list)))
         (template-count (length (obj-cells template))))
    (reduce (lambda (acc obj)
      (if (= (obj-color obj) 2)
          (recolor-cells acc (obj-cells obj)
            (if (= (length (obj-cells obj)) template-count) 4 1))
          acc))
      grid objects-list))))"""


def _dihedral_program() -> str:
    return """(rule! (lambda (grid)
  (define (shape-grid obj)
    (recolor
      (crop-to-content
        (subgrid (keep-only grid (obj-color obj))
                 (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj)))
      (obj-color obj) 1))
  (let* ((objects-list (objects grid 0))
         (template (first (filter (lambda (obj) (= (obj-color obj) 5)) objects-list)))
         (t0 (shape-grid template))
         (t1 (rotate-cw t0))
         (t2 (rotate-cw t1))
         (t3 (rotate-cw t2))
         (f0 (flip-lr t0))
         (f1 (rotate-cw f0))
         (f2 (rotate-cw f1))
         (f3 (rotate-cw f2)))
    (reduce (lambda (acc obj)
      (if (= (obj-color obj) 2)
          (let ((shape (shape-grid obj)))
            (recolor-cells acc (obj-cells obj)
              (if (or (= shape t0) (= shape t1) (= shape t2) (= shape t3)
                      (= shape f0) (= shape f1) (= shape f2) (= shape f3))
                  4 1)))
          acc))
      grid objects-list))))"""


def racket_rival_programs() -> dict[str, str]:
    """Standalone executable rivals; topmost-only remains in the Python audit."""
    return {
        "identity": "(rule! (lambda (grid) grid))",
        "all_candidates_yellow": _constant_program(4),
        "all_candidates_blue": _constant_program(1),
        "same_cell_count": _same_cell_count_program(),
        "dihedral_match": _dihedral_program(),
        "fixed_clockwise": _target_program("1"),
        "fixed_counterclockwise": _target_program("3"),
        "fixed_half_turn": _target_program("2"),
        "reversed_selector_mapping": _target_program(
            "(if (= selector-count 2) 3 1)", selector=True
        ),
    }


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

    def apply(self, source: str, grid: list[list[int]]) -> list[list[int]]:
        if source not in self._wrapped:
            self._wrapped[source] = self._wrap_rule(source)
        self.evaluations += 1
        return self._bridge.eval_text(f"({self._wrapped[source]} {_literal(grid)})")

    def close(self) -> None:
        self._bridge.close()


def build_report(
    *,
    seeds: Iterable[int] = (0, 17),
    demo_counts: Iterable[int] = (2,),
    run_racket: bool = True,
) -> dict[str, object]:
    normalized_seeds = _integer_list(list(seeds), 0, 2**63 - 1, "seeds")
    normalized_counts = _integer_list(list(demo_counts), 2, 6, "demo_counts")
    if type(run_racket) is not bool:
        raise ValueError("run_racket must be boolean")

    settings = _FAMILY.settings_space()
    programs = [
        {
            "settings": setting,
            "sha256": hashlib.sha256(_FAMILY.program(setting).encode("utf-8")).hexdigest(),
        }
        for setting in settings
    ]
    cases: list[dict[str, object]] = []
    all_inputs_setting_independent = True
    all_lessons_unique = True
    all_shortcuts_rejected = True
    query_outputs_consulted = False
    racket_labels_match: bool | None = None
    racket_declared_unique: bool | None = None
    racket_rivals_rejected: bool | None = None
    evaluator = _RacketEvaluator() if run_racket else None
    rivals = racket_rival_programs()
    if evaluator is not None:
        racket_labels_match = True
        racket_declared_unique = True
        racket_rivals_rejected = True

    try:
        for seed in normalized_seeds:
            for demos in normalized_counts:
                baseline_inputs: str | None = None
                for setting in settings:
                    episode = _FAMILY.generate_episode(
                        seed=seed,
                        settings=setting,
                        demos=demos,
                        queries=4,
                    )
                    inputs = {
                        "train": [pair["input"] for pair in episode["train"]],
                        "test": [pair["input"] for pair in episode["test"]],
                    }
                    input_sha = _sha(inputs)
                    if baseline_inputs is None:
                        baseline_inputs = input_sha
                    else:
                        all_inputs_setting_independent &= input_sha == baseline_inputs
                    certificate = episode["certificate"]
                    unique = certificate["surviving_settings"] == [setting]
                    shortcuts_rejected = certificate["surviving_shortcuts"] == []
                    all_lessons_unique &= unique
                    all_shortcuts_rejected &= shortcuts_rejected
                    query_outputs_consulted |= bool(certificate["query_outputs_consulted"])

                    racket_case: dict[str, object] | None = None
                    if evaluator is not None:
                        intended_source = _FAMILY.program(setting)
                        labels_ok = all(
                            evaluator.apply(intended_source, pair["input"]) == pair["output"]
                            for split in ("train", "test")
                            for pair in episode[split]
                        )
                        declared_survivors = [
                            candidate
                            for candidate in settings
                            if all(
                                evaluator.apply(_FAMILY.program(candidate), pair["input"])
                                == pair["output"]
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
                        declared_unique = declared_survivors == [setting]
                        rivals_rejected = rival_survivors == []
                        racket_labels_match = bool(racket_labels_match and labels_ok)
                        racket_declared_unique = bool(racket_declared_unique and declared_unique)
                        racket_rivals_rejected = bool(racket_rivals_rejected and rivals_rejected)
                        racket_case = {
                            "labels_match": labels_ok,
                            "declared_survivors": declared_survivors,
                            "rival_survivors": rival_survivors,
                        }

                    row: dict[str, object] = {
                        "seed": seed,
                        "demos": demos,
                        "queries": 4,
                        "settings": setting,
                        "input_sha256": input_sha,
                        "output_sha256": _sha(
                            {
                                "train": [pair["output"] for pair in episode["train"]],
                                "test": [pair["output"] for pair in episode["test"]],
                            }
                        ),
                        "program_sha256": hashlib.sha256(
                            episode["program_solution"].encode("utf-8")
                        ).hexdigest(),
                        "unique_declared_survivor": unique,
                        "shortcut_survivors": certificate["surviving_shortcuts"],
                        "query_outputs_consulted": certificate["query_outputs_consulted"],
                        "query_shapes": [
                            [len(pair["input"]), len(pair["input"][0])]
                            for pair in episode["test"]
                        ],
                        "selector_counts": [
                            _FAMILY.causal_trace(pair["input"])["selector_cells"]
                            for pair in episode["train"]
                        ],
                    }
                    if racket_case is not None:
                        row["racket"] = racket_case
                    cases.append(row)
    finally:
        if evaluator is not None:
            evaluator.close()

    report: dict[str, object] = {
        "schema": SCHEMA,
        "task_id": _FAMILY.TASK_ID,
        "scope": {
            "seeds": normalized_seeds,
            "demo_counts": normalized_counts,
            "queries": 4,
            "settings": settings,
            "shortcut_names": sorted(
                _FAMILY.shortcut_outputs(
                    _FAMILY.sample_inputs(normalized_seeds[0], 2, 4)["train"][0],
                    settings[0],
                )
            ),
            "racket_rival_names": sorted(rivals),
            "claim": (
                "finite protected-Racket teaching audit"
                if run_racket
                else "finite Python preflight; protected-Racket audit is separate"
            ),
        },
        "programs": programs,
        "cases": cases,
        "summary": {
            "cases": len(cases),
            "programs": len(programs),
            "all_programs_distinct": len({row["sha256"] for row in programs}) == len(programs),
            "all_lessons_unique": all_lessons_unique,
            "all_shortcuts_rejected": all_shortcuts_rejected,
            "all_inputs_setting_independent": all_inputs_setting_independent,
            "query_outputs_consulted": query_outputs_consulted,
            "racket_checked": run_racket,
            "racket_labels_match": racket_labels_match,
            "racket_declared_unique": racket_declared_unique,
            "racket_rivals_rejected": racket_rivals_rejected,
        },
    }
    if evaluator is not None:
        report["racket"] = {
            **evaluator.identity,
            "evaluations": evaluator.evaluations,
        }
    return report


def write_report(path: Path | str, report: dict[str, object]) -> None:
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
        demo_counts=args.demo_counts if args.demo_counts is not None else (2,),
        run_racket=not args.python_only,
    )
    write_report(args.out, report)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
