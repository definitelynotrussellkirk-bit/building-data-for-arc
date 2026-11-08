"""Bounded repeatable audit for the 64bd7bc767bb parametric family.

This is intentionally task-local: it checks matched inputs, deterministic labels,
teaching identifiability against the declared finite rival set, query diversity,
and the 30x30 stress case.  It does not claim proof beyond the supplied seeds or
replace protected-Racket qualification.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Iterable, Any


HERE = Path(__file__).resolve().parent
TASK_ID = "64bd7bc767bb"


def _load_family():
    source = HERE / "family.py"
    name = "_audit_family_64bd7bc767bb_" + hashlib.sha256(str(source).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, source)
    if spec is None or spec.loader is None:  # pragma: no cover - import guard
        raise ImportError(f"cannot load adjacent family: {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _freeze_grid(grid: list[list[int]]) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(row) for row in grid)


def run_audit(seeds: Iterable[int]) -> dict[str, Any]:
    family = _load_family()
    seed_list = list(seeds)
    failures: list[dict[str, Any]] = []
    winner_colors: set[int] = set()
    winner_orientations: set[str] = set()
    selected_alignments: set[str] = set()
    query_shapes: set[tuple[int, int]] = set()
    unique_inputs: set[tuple[tuple[int, ...], ...]] = set()
    stress_nonzero = 0
    setting_episodes = 0
    generated_pairs = 0

    for seed in seed_list:
        episodes: dict[str, dict[str, Any]] = {}
        for rule in ("bottom", "winner_bbox"):
            setting_episodes += 1
            settings = {"alignment_rule": rule}
            try:
                episode = family.generate(seed, settings, 2, 4)
                episodes[rule] = episode
                check = family.teaching_check(episode, settings)
                if check["survivors"] != [settings] or check["surviving_rivals"]:
                    failures.append({"seed": seed, "rule": rule, "kind": "teaching", "detail": check})
                local_inputs: set[tuple[tuple[int, ...], ...]] = set()
                for split in ("train", "test"):
                    for pair in episode[split]:
                        generated_pairs += 1
                        frozen = _freeze_grid(pair["input"])
                        local_inputs.add(frozen)
                        unique_inputs.add(frozen)
                        if pair["output"] != family.transform(pair["input"], settings):
                            failures.append({"seed": seed, "rule": rule, "kind": "python_label_mismatch"})
                        facts = family.analyze(pair["input"])
                        winner_colors.add(facts["winner_color"])
                        winner_orientations.add(facts["winner_orientation"])
                        selected_alignments.add(
                            "top" if rule == "winner_bbox" and facts["winner_orientation"] == "horizontal" else "bottom"
                        )
                        if split == "test":
                            shape = (len(pair["input"]), len(pair["input"][0]))
                            query_shapes.add(shape)
                            if shape == (30, 30):
                                stress_nonzero = max(
                                    stress_nonzero,
                                    sum(value != 0 for row in pair["input"] for value in row),
                                )
                if len(local_inputs) != 6:
                    failures.append({"seed": seed, "rule": rule, "kind": "duplicate_input", "count": len(local_inputs)})
            except Exception as exc:  # bounded audit records, rather than hides, a bad seed
                failures.append({"seed": seed, "rule": rule, "kind": "exception", "detail": f"{type(exc).__name__}: {exc}"})

        if set(episodes) == {"bottom", "winner_bbox"}:
            for split in ("train", "test"):
                left = [pair["input"] for pair in episodes["bottom"][split]]
                right = [pair["input"] for pair in episodes["winner_bbox"][split]]
                if left != right:
                    failures.append({"seed": seed, "kind": "unmatched_inputs", "split": split})
            if not any(
                a["output"] != b["output"]
                for a, b in zip(episodes["bottom"]["train"], episodes["winner_bbox"]["train"])
            ):
                failures.append({"seed": seed, "kind": "settings_not_taught"})

    return {
        "schema": "arc-review-parametric-self-audit-v1",
        "task_id": TASK_ID,
        "scope": "Finite Python mirror/rival audit; protected-Racket qualification remains separate.",
        "seeds": seed_list,
        "seed_count": len(seed_list),
        "setting_episodes": setting_episodes,
        "generated_pairs": generated_pairs,
        "unique_input_count": len(unique_inputs),
        "query_shapes": [list(shape) for shape in sorted(query_shapes)],
        "winner_colors": sorted(winner_colors),
        "winner_orientations": sorted(winner_orientations),
        "selected_alignments": sorted(selected_alignments),
        "stress_nonzero": stress_nonzero,
        "program_sha256": {
            rule: hashlib.sha256(family.program({"alignment_rule": rule}).encode()).hexdigest()
            for rule in ("bottom", "winner_bbox")
        },
        "failure_count": len(failures),
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, default=40, help="audit seeds 0..N-1")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    report = run_audit(range(args.seeds))
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 1 if report["failure_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
