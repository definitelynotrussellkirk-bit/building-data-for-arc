#!/usr/bin/env python3
"""Bounded learnability, projection, size, and protected-Racket audit."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

TASK_ID = "83e70bd8c0a1"
HERE = Path(__file__).resolve()
ROOT = HERE.parents[4]
SETTINGS = (
    {"rule": "full_reflection"},
    {"rule": "probe_relay"},
)
DEMO_COUNTS = (2, 3, 6)
QUERY_COUNT = 4


def _load_adjacent(filename: str, name: str):
    path = HERE.with_name(filename)
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PROTO = _load_adjacent("prototype.py", "audit_83e70bd8c0a1_prototype")


def _stable_bytes(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def _identity(grid):
    return copy.deepcopy(grid)


def _transpose(grid):
    return [list(row) for row in zip(*grid)]


def _rotate_180(grid):
    return [row[::-1] for row in grid[::-1]]


def _flip_lr(grid):
    return [row[::-1] for row in grid]


def _probe_only(grid):
    return PROTO._move_probe(grid)


def _skip_a_original_cue(grid):
    selected = PROTO._cue_color(grid, PROTO._probe_position(grid))
    return PROTO._transpose_color(PROTO._move_probe(grid), selected)


def _copy_probe(grid):
    copied = PROTO._move_probe(grid, keep_source=True)
    destination = PROTO._anti(PROTO._probe_position(grid), len(grid))
    selected = PROTO._cue_color(copied, destination)
    return PROTO._transpose_color(copied, selected)


def _fixed_color(color):
    return lambda grid: PROTO._transpose_color(PROTO._move_probe(grid), color)


def _recolor_selected(grid):
    moved = PROTO._move_probe(grid)
    selected = PROTO._cue_color(moved, PROTO._probe_position(moved))
    return [[9 if value == selected else value for value in row] for row in moved]


RIVALS = {
    "full_reflection": {
        "identity": _identity,
        "transpose": _transpose,
        "rotate_180": _rotate_180,
        "flip_lr": _flip_lr,
        "probe_relay": PROTO.relay_output,
    },
    "probe_relay": {
        "identity": _identity,
        "probe_only": _probe_only,
        "skip_a_original_cue": _skip_a_original_cue,
        "copy_probe": _copy_probe,
        "fixed_color_2": _fixed_color(2),
        "fixed_color_3": _fixed_color(3),
        "fixed_color_4": _fixed_color(4),
        "recolor_selected": _recolor_selected,
        "transpose_everything": _transpose,
        "full_reflection": PROTO.full_reflection,
    },
}


def _target_color(grid):
    moved = PROTO._move_probe(grid)
    return PROTO._cue_color(moved, PROTO._probe_position(moved))


def _write_public_examples(output: Path) -> list[dict]:
    from reviewer_support import public_challenge_bytes, public_challenge_id

    rows = []
    public = output / "public"
    public.mkdir(parents=True, exist_ok=True)
    for settings in SETTINGS:
        episode = PROTO.generate(0, settings, demos=3, queries=4)
        for query_index in range(4):
            view = PROTO.public_view(episode, query_index)
            payload = public_challenge_bytes(view)
            identifier = public_challenge_id(view)
            path = public / f"{identifier}.json"
            if path.exists() and path.read_bytes() != payload:
                raise ValueError("public content hash collision")
            path.write_bytes(payload)
            rows.append(
                {
                    "settings": settings,
                    "query_index": query_index,
                    "public_id": identifier,
                    "path": path.relative_to(output).as_posix(),
                    "bytes_sha256": hashlib.sha256(payload).hexdigest(),
                }
            )
    if len({row["public_id"] for row in rows}) != len(rows):
        raise ValueError("duplicate visible public examples")
    return rows


def build_report(seed_count: int = 64, execute_racket: bool = True) -> dict:
    if type(seed_count) is not int or not 1 <= seed_count <= 512:
        raise ValueError("seed_count must be an exact integer in 1..512")

    rival_failures = []
    projection_failures = []
    construction_failures = []
    targets = set()
    sizes = set()
    inputs = set()
    episodes = 0
    labeled_pairs = 0

    from reviewer_support import public_challenge_bytes

    for seed in range(seed_count):
        for demos in DEMO_COUNTS:
            by_setting = {
                setting["rule"]: PROTO.generate(
                    seed, setting, demos=demos, queries=QUERY_COUNT
                )
                for setting in SETTINGS
            }
            episodes += len(SETTINGS)
            labeled_pairs += len(SETTINGS) * (demos + QUERY_COUNT)

            left_inputs = [
                pair["input"]
                for split in ("train", "test")
                for pair in by_setting["full_reflection"][split]
            ]
            right_inputs = [
                pair["input"]
                for split in ("train", "test")
                for pair in by_setting["probe_relay"][split]
            ]
            if left_inputs != right_inputs:
                construction_failures.append(
                    {"seed": seed, "demos": demos, "kind": "settings_changed_inputs"}
                )
            if len({_stable_bytes(grid) for grid in left_inputs}) != demos + QUERY_COUNT:
                construction_failures.append(
                    {"seed": seed, "demos": demos, "kind": "duplicate_inputs"}
                )

            for grid in left_inputs:
                inputs.add(hashlib.sha256(_stable_bytes(grid)).hexdigest())
                sizes.add(len(grid))
                targets.add(_target_color(grid))

            for rule, episode in by_setting.items():
                demos_only = episode["train"]
                for rival_name, rival in RIVALS[rule].items():
                    if all(
                        rival(pair["input"]) == pair["output"]
                        for pair in demos_only
                    ):
                        rival_failures.append(
                            {
                                "seed": seed,
                                "demos": demos,
                                "rule": rule,
                                "rival": rival_name,
                            }
                        )

                one = PROTO.generate(seed, {"rule": rule}, demos=demos, queries=1)
                try:
                    first_many = public_challenge_bytes(PROTO.public_view(episode, 0))
                    first_one = public_challenge_bytes(PROTO.public_view(one, 0))
                    if first_many != first_one:
                        raise ValueError("first query changed with future query count")
                    query_payloads = [
                        public_challenge_bytes(PROTO.public_view(episode, index))
                        for index in range(QUERY_COUNT)
                    ]
                    if len(set(query_payloads)) != QUERY_COUNT:
                        raise ValueError("query projections are not distinct")
                    altered = copy.deepcopy(episode)
                    altered["settings"] = {"rule": "private-metadata-change"}
                    altered["program_solution"] = "private-metadata-change"
                    if public_challenge_bytes(PROTO.public_view(altered, 0)) != first_many:
                        raise ValueError("private metadata changed visible bytes")
                except Exception as exc:
                    projection_failures.append(
                        {
                            "seed": seed,
                            "demos": demos,
                            "rule": rule,
                            "error": f"{type(exc).__name__}: {exc}",
                        }
                    )

    racket = {"executed": False}
    if execute_racket:
        from arcpuzzles.parametric_worker import evaluate_contract

        contract = json.loads(HERE.with_name("promotion.json").read_text(encoding="utf-8"))
        jobs = [
            {"seed": seed, "settings": settings, "demos": demos, "queries": 4}
            for seed, demos in ((0, 2), (17, 6))
            for settings in SETTINGS
        ]
        result = evaluate_contract(ROOT, TASK_ID, contract, jobs)
        racket = {
            "executed": True,
            "identity": result["racket"],
            "evaluations": result["racket_evaluations"],
            "checks": result["checks"],
        }

    failures = construction_failures + rival_failures + projection_failures
    return {
        "schema": "arcpuzzles-probe-relay-audit-v1",
        "task_id": TASK_ID,
        "status": "PASS" if not failures else "FAIL",
        "seed_count": seed_count,
        "demo_counts": list(DEMO_COUNTS),
        "query_count": QUERY_COUNT,
        "episodes": episodes,
        "labeled_pairs": labeled_pairs,
        "unique_inputs": len(inputs),
        "sizes": sorted(sizes),
        "target_colors": sorted(targets),
        "construction_failures": construction_failures,
        "rival_failures": rival_failures,
        "projection_failures": projection_failures,
        "racket": racket,
        "limits": [
            "Finite declared-rival audit; it does not prove universal identifiability.",
            "The broad sweep uses Python claims; the recorded protected-Racket jobs check exact programs and labels.",
            "Owner acceptance and training admission remain separate downstream decisions.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=64)
    parser.add_argument("--no-racket", action="store_true")
    args = parser.parse_args()
    if args.out.exists():
        parser.error(f"output already exists: {args.out}")

    report = build_report(seed_count=args.seeds, execute_racket=not args.no_racket)
    args.out.mkdir(parents=True)
    report["public_examples"] = _write_public_examples(args.out)
    (args.out / "report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"{TASK_ID}: {report['status']} — {report['episodes']} episodes, "
        f"{report['labeled_pairs']} labeled pairs, {report['unique_inputs']} unique inputs"
    )
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
