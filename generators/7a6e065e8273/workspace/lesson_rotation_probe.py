"""Audit every pair in materialized lessons as the query.

The shared lesson census verifies the production query position.  This task-local
probe reuses the saved four-pair lessons and asks whether every plausible declared
rival is still refuted after *any* one pair is removed from the demonstrations.
It makes no Racket calls and is therefore cheap enough to run over all cyclic
query positions after each final census.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Callable

from reference_probe import canonical_pairs, load_generator

ROOT = Path(__file__).resolve().parents[3]
TASK = "7a6e065e8273"


def _declared_rivals(module: Any) -> list[tuple[str, Callable]]:
    rivals: list[tuple[str, Callable]] = []
    for group_name in (
        "SEMANTIC_RIVALS",
        "LESSON_COMPETITORS",
        "CANONICAL_SHORTCUTS",
    ):
        group = getattr(module, group_name, {})
        if not isinstance(group, dict):
            raise TypeError(f"{group_name} must be a dictionary")
        for name, rival in sorted(group.items()):
            if not callable(rival):
                raise TypeError(f"{group_name}:{name} is not callable")
            rivals.append((f"{group_name}:{name}", rival))
    if not rivals:
        raise ValueError("generator declares no semantic rivals")
    return rivals


def _pairs(instance: dict[str, Any]) -> list[dict[str, Any]]:
    train = instance.get("train", [])
    test = instance.get("test", [])
    if not isinstance(train, list) or not isinstance(test, list):
        raise ValueError("lesson train/test fields must be lists")
    pairs = train + test
    if len(pairs) < 2:
        raise ValueError("a rotation audit needs at least two lesson pairs")
    for index, pair in enumerate(pairs):
        if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
            raise ValueError(f"lesson pair {index} lacks input/output")
    return pairs


def analyze_instance(module: Any, instance: dict[str, Any]) -> dict[str, Any]:
    """Return rival survivors for each possible query position."""
    pairs = _pairs(instance)
    rivals = _declared_rivals(module)
    ambiguous: list[dict[str, Any]] = []
    rotations: list[dict[str, Any]] = []
    for query_index in range(len(pairs)):
        demos = [pair for index, pair in enumerate(pairs) if index != query_index]
        survivors = [
            name
            for name, rival in rivals
            if all(rival(pair["input"]) == pair["output"] for pair in demos)
        ]
        row = {
            "query_index": query_index,
            "demo_indices": [
                index for index in range(len(pairs)) if index != query_index
            ],
            "surviving_rivals": survivors,
            "identifiable": not survivors,
        }
        rotations.append(row)
        if survivors:
            ambiguous.append(row)
    return {
        "pair_count": len(pairs),
        "rotation_count": len(rotations),
        "ambiguous_rotation_count": len(ambiguous),
        "rotations": rotations,
        "ambiguous_rotations": ambiguous,
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit_censuses(
    module: Any,
    census_paths: list[Path],
    generator_path: Path,
) -> dict[str, Any]:
    generator_hash = _sha256(generator_path)
    canonical_shortcuts = getattr(module, "CANONICAL_SHORTCUTS", {})
    canonical_fit = {
        name: all(rival(pair["input"]) == pair["output"] for pair in canonical_pairs())
        for name, rival in sorted(canonical_shortcuts.items())
    }

    errors: list[str] = []
    ambiguity: list[dict[str, Any]] = []
    per_band: dict[str, dict[str, int]] = {}
    lesson_count = 0
    rotation_count = 0
    census_records = []

    for path in census_paths:
        document = json.loads(path.read_text())
        reported_hash = document.get("generator_sha256")
        if reported_hash != generator_hash:
            errors.append(
                f"{path}: generator hash {reported_hash!r} does not match {generator_hash}"
            )
        census_records.append(
            {
                "path": str(path),
                "sha256": _sha256(path),
                "generator_sha256": reported_hash,
                "status": document.get("status"),
            }
        )
        for lesson in document.get("lessons", []):
            band = str(lesson.get("band"))
            stats = per_band.setdefault(
                band,
                {"lessons": 0, "rotations": 0, "ambiguous_rotations": 0},
            )
            try:
                result = analyze_instance(module, lesson["instance"])
            except Exception as exc:  # preserve the lesson identity in the report
                errors.append(
                    f"{path}: lesson {lesson.get('index')} could not be audited: {exc}"
                )
                continue
            lesson_count += 1
            rotation_count += result["rotation_count"]
            stats["lessons"] += 1
            stats["rotations"] += result["rotation_count"]
            stats["ambiguous_rotations"] += result["ambiguous_rotation_count"]
            for row in result["ambiguous_rotations"]:
                ambiguity.append(
                    {
                        "census": str(path),
                        "band": band,
                        "lesson_index": lesson.get("index"),
                        "seed": lesson.get("seed"),
                        "sample_index": lesson.get("sample_index"),
                        **row,
                    }
                )

    status = "passed" if not errors and not ambiguity else "failed"
    return {
        "schema": f"{TASK}-cyclic-lesson-rotation-v1",
        "task_id": TASK,
        "status": status,
        "generator_sha256": generator_hash,
        "probe_sha256": _sha256(Path(__file__)),
        "censuses": census_records,
        "canonical_shortcut_fit": canonical_fit,
        "lesson_count": lesson_count,
        "rotation_count": rotation_count,
        "ambiguous_rotation_count": len(ambiguity),
        "per_band": per_band,
        "ambiguous_rotations": ambiguity,
        "errors": errors,
        "interpretation": (
            "Finite checks against declared rivals over every cyclic query position; "
            "not a proof of universal task induction."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--census", action="append", type=Path, required=True)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    generator_path = (
        args.generator
        or ROOT / f"generators/{TASK}/generator.py"
    ).resolve()
    module = load_generator(generator_path)
    report = audit_censuses(
        module,
        [path.resolve() for path in args.census],
        generator_path,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
