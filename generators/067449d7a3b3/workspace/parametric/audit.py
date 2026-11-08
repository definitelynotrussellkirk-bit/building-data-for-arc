"""Replayable finite audit for the proposed 067449d7a3b3 parametric family."""
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
    "_arc_067449d7a3b3_parametric_audit_prototype", _PROTOTYPE_PATH
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
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8") + b"\n"


def _sha(value: object) -> str:
    return hashlib.sha256(_raw(value)).hexdigest()


def build_report(
    *,
    seeds: Iterable[int] = (0, 17),
    demo_counts: Iterable[int] = (2, 6),
) -> dict[str, object]:
    """Replay finite teaching/sampling invariants without claiming Racket parity."""
    normalized_seeds = _integer_list(list(seeds), 0, 2**63 - 1, "seeds")
    normalized_counts = _integer_list(list(demo_counts), 2, 6, "demo_counts")
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
                cases.append(
                    {
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
                    }
                )

    return {
        "schema": SCHEMA,
        "task_id": _FAMILY.TASK_ID,
        "scope": {
            "seeds": normalized_seeds,
            "demo_counts": normalized_counts,
            "queries": 4,
            "settings": settings,
            "shortcut_names": [
                "identity",
                "maroon_only",
                "solid_rectangles_only",
                "ignore_singletons",
            ],
            "claim": "finite Python audit; protected Racket qualification is separate",
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
        },
    }


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
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    report = build_report(
        seeds=args.seeds if args.seeds is not None else (0, 17),
        demo_counts=args.demo_counts if args.demo_counts is not None else (2, 6),
    )
    write_report(args.out, report)
    print(json.dumps(report["summary"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
